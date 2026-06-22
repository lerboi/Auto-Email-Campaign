# Migration Plan: Postmark → Resend

**Status:** ✅ **Code implemented — Path C (Broadcasts + Segments).** Remaining work is provider-side setup only (see "Your remaining steps" below).
**Author:** Claude (researched against live Resend docs on 2026-06-21; every API fact below was adversarially re-verified against `resend.com/docs`).
**Scope:** Move the AniOne automated monthly email campaign off Postmark and onto Resend.

### What was implemented (2026-06-21)
- `deploy_new_year.py` rewritten to send a Resend **Broadcast** (`POST /broadcasts` with `send:true`) to a Segment, reading HTML/text/Subject from the local template folder. `CAMPAIGN_MAP` now keys each date to `{template_dir, segment}`.
- `sync_contacts.py` added — pushes the `email/` CSVs into the two Resend Segments (CSVs stay the source of truth). `--create` makes the segments and prints their IDs.
- `{{{ pm:unsubscribe }}}` → `{{{RESEND_UNSUBSCRIBE_URL}}}` across all 60 template + base-template files.
- `CLAUDE.md` and the `monthly-campaign-remake` skill updated for the Resend workflow.
- No new dependencies (`requests` + stdlib). `railway.json` unchanged.

### Your remaining steps (provider-side, only you can do these)
1. Create a Resend account + **Pro plan** ($20/50k covers ~31k/month).
2. **Verify `mail.anione.me`** in Resend (add the DKIM/SPF/MX DNS records; wait for `verified`).
3. Create an API key → set `RESEND_API_KEY` in Railway **and** local `.env`.
4. Run `python sync_contacts.py --create` once → set the printed `RESEND_SEGMENT_A` / `RESEND_SEGMENT_B` in the env.
5. Run `python sync_contacts.py` to load the lists, then test-send before the next live `CAMPAIGN_MAP` date.

---

## 1. TL;DR

- The codebase sends one **identical, non-personalized** HTML email to ~2,600 recipients per send-day via Postmark's **server-side templates** (`TemplateAlias`) and the **`batchWithTemplates`** endpoint, relying on Postmark **message streams** + the `{{{ pm:unsubscribe }}}` tag to handle unsubscribe/suppression automatically.
- Resend can do this, but **two things have no drop-in equivalent** and force a design decision:
  1. **Templates** — Postmark stores templates server-side and you send an *alias*. Resend's cleanest path is to **inline the HTML** in the API call (it also has a newer server-side template object, see §4).
  2. **Unsubscribe/suppression** — Postmark's `{{{ pm:unsubscribe }}}` + message stream **managed this for free**. Resend only manages it automatically inside **Broadcasts**. For raw transactional/batch sends, *you* must host an unsubscribe endpoint and maintain your own suppression list.
- **Recommended approach: migrate to Resend Broadcasts + Segments (Path C).** It is purpose-built for "blast one HTML email to a list," and it is the **only** path that preserves the automatic unsubscribe + suppression behavior we get from Postmark today — which matters because at this volume (>5,000/day to Gmail/Yahoo across the A/B pair) **one-click unsubscribe is mandatory** for inbox placement.
- A fallback (**Path A — inline-HTML batch send**) is fully specified in §8 for the case where you want to keep the current CSV-driven workflow and are willing to build a small unsubscribe service.

> **You must decide one thing before implementation: Path C (Broadcasts) vs Path A (batch send).** See §4 and §12.

---

## 2. Current State (what Postmark does for us today)

| Concern | Current implementation | File |
|---|---|---|
| Dispatcher | Daily Railway cron runs `deploy_new_year.py` at 03:00 UTC | `railway.json` |
| Date → campaign | `CAMPAIGN_MAP` maps `YYYY-MM-DD` → `{template alias, lists}` | `deploy_new_year.py:29-42` |
| Auth | Header `X-Postmark-Server-Token: <POSTMARK_SERVER_TOKEN>` | `deploy_new_year.py:10,65` |
| Endpoint | `POST https://api.postmarkapp.com/email/batchWithTemplates` | `deploy_new_year.py:61` |
| Payload (per msg) | `{From, To, TemplateAlias, TemplateModel: {}, MessageStream}` | `deploy_new_year.py:76-82` |
| Batching | 500 messages per call, wrapped as `{"Messages": [...]}` | `deploy_new_year.py:68,84` |
| Templates | Stored **server-side in Postmark** by alias (e.g. `jun-gift-day-1`); local `templates/{month}/day-N/` holds `metadata.txt` (Name/Subject/Alias), `template.html`, `template.txt`, **uploaded to the Postmark dashboard by hand** | `templates/`, skill Step 5 |
| Personalization | **None** — `TemplateModel` is always `{}` | `deploy_new_year.py:80` |
| Unsubscribe | `{{{ pm:unsubscribe }}}` tag in every `template.html` **and** `template.txt` footer; Postmark hosts the page + suppresses | all templates + base-templates |
| Segmentation | `MessageStream: "monthly-campaign"` (separate from legacy `christmas-campaign`) | `deploy_new_year.py:12` |
| List hygiene | CSV scrub/dedup pipeline (provider-agnostic, **no change needed**) | `clean_list.py`, `clean_tools/` |
| A/B split | `GROUP_A` / `GROUP_B` alternate on consecutive days (~2,600 each) | `deploy_new_year.py:23-24` |

**Campaign volume (corrected):** `CAMPAIGN_MAP` has 12 send-days, each to one group of ~2,600 → **~31,000 emails per campaign month** (not daily; only on mapped dates).

---

## 3. Postmark → Resend: core API differences (verified)

| Aspect | Postmark (current) | Resend (verified) |
|---|---|---|
| Base URL | `api.postmarkapp.com` | `api.resend.com` |
| Auth header | `X-Postmark-Server-Token: <token>` | `Authorization: Bearer re_xxxxxxxx` |
| Extra required header | — | **`User-Agent` is required** (missing → 403, code 1010). `requests`/SDK set it automatically — don't strip it. |
| Batch endpoint | `POST /email/batchWithTemplates` | `POST /emails/batch` |
| Batch body shape | `{"Messages": [ {...} ]}` | **raw top-level JSON array** `[ {...}, {...} ]` (no wrapper key) |
| **Batch size cap** | **500 / call** | **100 / call** ⚠️ must re-chunk |
| Field casing | PascalCase (`From`, `To`, `TemplateAlias`) | snake_case (`from`, `to`, `reply_to`, `html`, `text`, `headers`, `tags`, `template`) |
| `to` per message | single address | string or array, **max 50 addresses** |
| Rate limit | (generous) | **5 requests/sec per *team*** (shared across all API keys); 429 on exceed, honor `retry-after` |
| Templates | server-side alias, `TemplateModel` | inline `html`/`text`, **or** `template:{id|alias, variables}` (newer; mutually exclusive with `html`/`text`) |
| Message streams | `monthly-campaign` etc. | **none** — drop `MessageStream`; separate marketing via a dedicated verified subdomain / Broadcasts |
| Unsubscribe | `{{{ pm:unsubscribe }}}` tag, auto-managed | **No equivalent for raw sends.** Broadcasts: `{{{RESEND_UNSUBSCRIBE_URL}}}` (auto-managed). Transactional: `List-Unsubscribe` header + self-hosted endpoint + your own suppression |
| Success response | per-message `ErrorCode`/`Message` array | single: `{"id": "..."}`; batch: `{"data": [{"id": "..."}, ...]}` |
| Attachments / scheduling on batch | n/a | **not supported on `/emails/batch`** (single-send only). Irrelevant today (no attachments). |

---

## 4. The central decision — how templates get sent

There are three viable approaches. Pick one; the rest of the plan branches on it.

| | **Path A — Inline-HTML batch** | **Path B — Template-alias batch** | **Path C — Broadcasts + Segments (RECOMMENDED)** |
|---|---|---|---|
| Send mechanism | `POST /emails/batch`, read local `template.html`/`.txt`, inline into each message | `POST /emails/batch` with `template:{id: "<alias>"}` | `POST /broadcasts` (with `send: true`) targeting a Segment |
| Closest to current code? | Medium (keeps CSV loop) | **Highest** (keeps alias indirection) | Low (new send model) |
| Template upload step | **Removed** (HTML read from disk) | Re-add: upload/publish each template to Resend (dashboard or API) | **Removed** (HTML inlined in broadcast) |
| List source | Existing `email/*.csv` (unchanged) | Existing `email/*.csv` (unchanged) | **One-time import into 2 Segments** (then maintained in Resend) |
| Batch re-chunk to 100? | **Yes** | **Yes** | N/A (one call per group) |
| Rate-limit throttling needed? | Yes (~26 calls/send-day) | Yes (~26 calls/send-day) | No (a couple of calls/send-day) |
| **Unsubscribe** | ⚠️ **You build & host it** + maintain suppression + `List-Unsubscribe` headers | ⚠️ Same as A | ✅ **Automatic** via `{{{RESEND_UNSUBSCRIBE_URL}}}`; Resend hosts page + auto-suppresses |
| Gmail/Yahoo one-click compliance (>5k/day) | You implement RFC 8058 yourself | You implement it yourself | ✅ Handled by Resend |
| Net new infrastructure | Unsubscribe web service + suppression store | Same + template publish | None |
| Main downside | Compliance/suppression burden falls on you | Compliance burden **and** template publishing overhead | List management moves into Resend (re-import on monthly list changes) |

### Recommendation: **Path C (Broadcasts + Segments)**

Rationale:
1. The campaign is a **pure marketing blast with zero personalization** — exactly what Broadcasts exist for.
2. It is the **only path that preserves the "platform manages unsubscribe + suppression" guarantee** we currently get from Postmark's `{{{ pm:unsubscribe }}}` + message stream. Paths A/B require us to stand up an unsubscribe endpoint, persist opt-outs, filter every send, and implement RFC 8058 one-click ourselves — and Resend **explicitly does not suppress** for transactional sends ("Resend doesn't manage contact lists for transactional emails").
3. At ~2,600/day per group (~5,200 across the consecutive A/B days), we are at/over the **5,000/day Gmail+Yahoo bulk-sender threshold** that *requires* one-click unsubscribe. Broadcasts make this automatic.
4. The send code **shrinks** — no 500→100 re-chunking, no rate-limit throttling, no batch payload assembly.

**The one real trade-off** to accept with Path C: recipient lists live in Resend **Segments** instead of CSVs. Monthly list changes (which the campaign does — see the skill's "verify user group CSVs" step) mean re-importing/syncing contacts into the two Segments. Mitigations in §6.4. The existing CSV scrub/dedup pipeline (`clean_list.py`) still runs **before** import, so list hygiene is unchanged.

> If you prefer to keep the CSV-driven flow and are willing to own a small unsubscribe service, use **Path A** (§8). Path B is not recommended — it carries Path A's compliance burden *plus* template-publishing overhead, with little upside.

---

## 5. Verified Resend facts the plan depends on

All confirmed by re-fetching the cited docs (June 2026). Contradictions found during verification are already reconciled here.

- **Auth:** `Authorization: Bearer re_xxx`; base `https://api.resend.com`; `User-Agent` header required. — `docs/api-reference/introduction`
- **Batch send:** `POST /emails/batch`, body is a **bare JSON array**, **max 100 messages/call**, `to` max 50/msg, response `{"data":[{"id":...}]}`. No attachments/`scheduled_at` on batch. — `docs/api-reference/emails/send-batch-emails`
- **Single send:** `POST /emails`; response `{"id":"..."}`; supports `attachments`, `scheduled_at`. — `docs/api-reference/emails/send-email`
- **Rate limit:** **5 req/s per team**, increasable on request; 429 returns `retry-after`. (An older "2 req/s" figure circulating in blogs is outdated.) — `docs/api-reference/rate-limit`
- **Server-side templates (optional):** `template:{id, variables}` where `id` accepts the template id **or a human-readable alias**; mutually exclusive with `html`/`text`/`react`; templates must be **published** before use; `{{{VAR}}}` syntax, up to 50 vars, no-fallback vars are required (422 if omitted). _Note: the by-alias capability is documented on the send-email API field and the Resend SDK reference; programmatic template create/publish is relatively new — treat dashboard upload as the safe route if you go Path B._ — `docs/api-reference/emails/send-email`, `docs/dashboard/templates/*`
- **Transactional unsubscribe:** set `headers: {"List-Unsubscribe": "<https://...>", "List-Unsubscribe-Post": "List-Unsubscribe=One-Click"}` (URL **must** be angle-bracket-wrapped) **and host your own endpoint** (GET = page, POST = blank 200/202, stop within 48h). **Resend does not suppress for you.** Reserved transactional template var is `UNSUBSCRIBE_URL`. — `docs/dashboard/emails/add-unsubscribe-to-transactional-emails`
- **Broadcasts:** `POST /broadcasts` requires `segment_id`, `from`, `subject`; optional `html`, `text`, `name`, `reply_to`, `topic_id`, `scheduled_at`, `send` (default false). `POST /broadcasts/{id}/send` to send; **create-and-send in one call via `send: true`**. **Only API-created broadcasts can be sent via the API** (dashboard-created ones can't). Auto-unsubscribe via `{{{RESEND_UNSUBSCRIBE_URL}}}` placeholder; Resend hosts the page and auto-suppresses opted-out contacts on the next broadcast. — `docs/api-reference/broadcasts/*`, `docs/dashboard/broadcasts/introduction`
- **Audiences → Segments:** "Audiences are now called Segments"; create-broadcast uses **`segment_id`**. Contacts are **global** (`POST /contacts`, required `email`, optional `first_name`/`last_name`/`unsubscribed`/`segments`/`topics`). **No bulk contact-import API** — programmatic import is one `POST /contacts` per contact; **dashboard CSV import** is the practical bulk path. — `docs/api-reference/contacts/*`, `docs/dashboard/audiences/contacts`
- **Domains:** verify the **`mail.anione.me` subdomain independently** of the apex — DKIM TXT + SPF TXT + MX (on the send subdomain) + optional DMARC; SPF on a subdomain does **not** inherit from apex; up to 72h to verify. — `docs/dashboard/domains/introduction`
- **Plans/limits:** Free = **100/day & 3,000/month** (cannot run even one campaign day). Paid: Pro **$20/mo = 50,000** emails, **$35/mo = 100,000**; no daily cap. **~31k/month → Pro $20 (50k) is sufficient**, Pro $35 (100k) for headroom. Dedicated IPs are Scale-plan only and need ~30k+/mo to stay warm (shared IPs are fine at this volume). — `resend.com/pricing`, `docs/knowledge-base/account-quotas-and-limits`

---

## 6. Pre-migration setup (provider side — no code; do these first for either path)

1. **Create a Resend account** and choose a plan: **Pro 50k ($20/mo)** covers ~31k/month with margin (upgrade to 100k if other mail shares the account).
2. **Verify the sending domain `mail.anione.me`** (separate from the apex):
   - Add the DKIM TXT, SPF TXT, and MX records Resend generates to the `mail.anione.me` DNS zone; optionally add DMARC.
   - Wait for status `verified` (up to 72h). **No send will succeed until this is done** (otherwise 403 / `invalid_from_address`).
   - Keep `from` as `AniOne <contact@mail.anione.me>` (Resend's `from` supports `Name <addr>`).
3. **Create an API key** → store as `RESEND_API_KEY` (see §7 env + the **.env-in-git security fix** in §9).
4. **Path C only — set up Segments & contacts:**
   - Create two Segments, e.g. `anione-group-a` and `anione-group-b`.
   - **Import contacts via the dashboard CSV importer** (no bulk API): map the lowercase `email` column; leave name fields blank (no personalization). Assign GROUP_A CSVs (`May2025_Free_CLEANED.csv`, `paidNoPackage_May.csv`) to Segment A and GROUP_B CSV (`May2026_freeUsers_CLEANED.csv`) to Segment B. Run `clean_list.py` first as today.
   - (Optional) Configure the **branded unsubscribe page** (logo/colors) under unsubscribe settings.
5. **Path A only — stand up the unsubscribe service** (see §8.4).

---

## 7. Environment & dependency changes (both paths)

**`.env`:**
```diff
- POSTMARK_SERVER_TOKEN=...
+ RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxxx
  SENDER_EMAIL=contact@mail.anione.me
```

**`requirements.txt`** — recommended to add the official SDK (cleaner than raw `requests` for both batch and broadcasts):
```diff
  requests
  python-dotenv
  email-validator
+ resend
```
(Raw `requests` also works against the REST API; the SDK is optional but matches the docs and handles auth/User-Agent for you.)

**`railway.json`** — **no change.** The cron still runs `python deploy_new_year.py` daily at 03:00 UTC.

---

## 8. Implementation by path

### 8.A — Path C: Broadcasts + Segments (recommended)

**`deploy_new_year.py` becomes much simpler.** Replace the batch loop with: read the day's local `template.html` + subject, then create-and-send a broadcast to the day's Segment.

Conceptual rewrite:
```python
import os, re, requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("RESEND_API_KEY")
SENDER  = os.getenv("SENDER_EMAIL", "contact@mail.anione.me")
FROM    = f"AniOne <{SENDER}>"

SEGMENT_A = os.getenv("RESEND_SEGMENT_A")   # uuid of anione-group-a
SEGMENT_B = os.getenv("RESEND_SEGMENT_B")   # uuid of anione-group-b

# date -> {template folder, segment}  (replaces the alias-based map)
CAMPAIGN_MAP = {
    "2026-06-01": {"path": "templates/june/day-1", "segment": SEGMENT_A},
    "2026-06-02": {"path": "templates/june/day-1", "segment": SEGMENT_B},
    # ... same dates as today, pointing at a folder + segment instead of an alias
}

def load_template(folder):
    with open(f"{folder}/template.html", encoding="utf-8") as f:
        html = f.read()
    with open(f"{folder}/metadata.txt", encoding="utf-8") as f:
        meta = f.read()
    subject = re.search(r"^Subject:\s*(.+)$", meta, re.M).group(1).strip()
    name    = re.search(r"^Name:\s*(.+)$",    meta, re.M).group(1).strip()
    return html, subject, name

def send_broadcast(cfg):
    html, subject, name = load_template(cfg["path"])
    resp = requests.post(
        "https://api.resend.com/broadcasts",
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={
            "segment_id": cfg["segment"],
            "from": FROM,
            "subject": subject,
            "name": name,
            "html": html,      # footer contains {{{RESEND_UNSUBSCRIBE_URL}}}
            "send": True,      # create AND send in one request
        },
    )
    resp.raise_for_status()
    print("✅ Broadcast created+sent:", resp.json())
```
SDK equivalent: `resend.Broadcasts.create({... , "send": True})`.

**Template change (all active `template.html` + `template.txt`):** replace the Postmark tag with Resend's broadcast placeholder:
```diff
- <a href="{{{ pm:unsubscribe }}}" ...>Unsubscribe</a>
+ <a href="{{{RESEND_UNSUBSCRIBE_URL}}}" ...>Unsubscribe</a>
```
```diff
- Unsubscribe: {{{ pm:unsubscribe }}}
+ Unsubscribe: {{{RESEND_UNSUBSCRIBE_URL}}}
```

**Per-month operations change:** instead of "upload templates to Postmark dashboard," the new monthly steps are (a) refresh the two Segments' contacts if the lists changed (dashboard CSV re-import, or a small `POST /contacts` sync script) and (b) update `CAMPAIGN_MAP` dates/paths. Template HTML is read from disk at send time — no upload.

**New env vars:** `RESEND_SEGMENT_A`, `RESEND_SEGMENT_B` (the Segment UUIDs).

---

### 8.B — Path A: Inline-HTML batch send (fallback; keeps CSV workflow)

Use this only if you want to keep CSV-driven sends and will host an unsubscribe service.

**8.B.1 `deploy_new_year.py` — `send_batch` rewrite:**
- Endpoint → `https://api.resend.com/emails/batch`; header → `Authorization: Bearer {RESEND_API_KEY}`.
- **Body is a bare array** (`json=messages`, *not* `{"Messages": messages}`).
- **Chunk size 500 → 100.**
- Read the day's `template.html`/`template.txt` + subject from `metadata.txt` and inline them.
- Add per-recipient `List-Unsubscribe` headers and **throttle** to respect 5 req/s.
- **Filter the recipient list against your suppression store before sending.**

```python
import time
RESEND_BATCH = "https://api.resend.com/emails/batch"

def send_batch(email_list, folder, suppression):
    html, text, subject = load_template(folder)                    # reads template.html/.txt + metadata Subject
    recipients = [e for e in email_list if e not in suppression]   # REQUIRED: self-managed suppression
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    sent = 0
    for i in range(0, len(recipients), 100):                       # 100, not 500
        chunk = recipients[i:i+100]
        messages = [{
            "from": FROM,
            "to": [email],
            "subject": subject,
            "html": html.replace("{{UNSUBSCRIBE_URL}}", unsub_url(email)),
            "text": text.replace("{{UNSUBSCRIBE_URL}}", unsub_url(email)),
            "headers": {
                "List-Unsubscribe": f"<{unsub_url(email)}>",       # angle brackets required
                "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
            },
        } for email in chunk]
        r = requests.post(RESEND_BATCH, headers=headers, json=messages)   # bare array
        if r.ok: sent += len(chunk); print(f"✅ {sent}")
        else:    print("❌", r.status_code, r.text)
        time.sleep(0.25)                                           # ~4 req/s, under the 5 req/s team cap
    return sent
```
SDK equivalent: `resend.Batch.send(messages)`.

**8.B.2 Template change:** Postmark's `{{{ pm:unsubscribe }}}` has **no platform equivalent** for raw sends. Replace it with a script-injected placeholder (e.g. `{{UNSUBSCRIBE_URL}}`) that the dispatcher fills per recipient, in **both** `template.html` and `template.txt`.

**8.B.3 Drop `MessageStream`** (no equivalent).

**8.B.4 New: unsubscribe service + suppression (the real cost of Path A):**
- A small HTTPS endpoint (could be a second Railway service) that:
  - `GET /unsub?t=<token>` → renders a confirmation page,
  - `POST /unsub?t=<token>` → records the opt-out and returns a **blank 200/202** (RFC 8058 one-click),
  - persists opt-outs (a CSV/DB/`suppression.txt`).
- `unsub_url(email)` produces a **signed** token so addresses can't be guessed.
- The dispatcher loads the suppression set and filters every send (shown above). Carry this store across monthly list swaps so unsubscribes persist.

---

## 9. Cross-cutting changes (both paths)

1. **Env var rename** `POSTMARK_SERVER_TOKEN` → `RESEND_API_KEY` (+ Path C's Segment IDs). Update the guard in `main()` (`deploy_new_year.py:99-101`).
2. **Security fix — `.env` is tracked in git** (CLAUDE.md flags this). During migration: add `.env` to `.gitignore`, `git rm --cached .env`, and **treat the new `RESEND_API_KEY` as secret** (set it in Railway's env vars, not in the committed file). Rotate/revoke the old Postmark token after cutover.
3. **`CLAUDE.md`** — update Project Overview, message-stream notes, batch-size (500→100 / N/A), sender/endpoint, and the unsubscribe mechanism. Remove Postmark-specific wording.
4. **`monthly-campaign-remake` skill** (`.claude/skills/monthly-campaign-remake/SKILL.md`):
   - Replace the `{{{ pm:unsubscribe }}}` references (≈ lines 220, 249, 346) with the chosen Resend mechanism.
   - Rewrite **Step 5 "Postmark Upload Reminder"** → Path C: "refresh Segments + update `CAMPAIGN_MAP`" (no upload); or Path A: "no upload — HTML is read from disk."
   - Update the `CAMPAIGN_MAP` example (Step 2) to the new shape (folder/segment instead of alias).
   - Update the "alias naming convention" + `metadata.txt` `Alias:` guidance (aliases are Postmark-specific; keep only if Path B).
5. **Base templates** (`.claude/skills/monthly-campaign-remake/base-templates/*/template.{html,txt}`) — replace the `{{{ pm:unsubscribe }}}` tag (12 files) so all future months are generated correctly.
6. **Existing template files** (`templates/{march,april,may,june}/day-*/template.{html,txt}`) — replace the unsubscribe tag. Only the **active/future** month must be correct for sending; past months are historical (update for consistency, optional).
7. **`metadata.txt` `Subject:`** is now read by the dispatcher at send time (Postmark stored it server-side) — already present in every folder; just ensure the parser reads it.

---

## 10. Testing & rollout

1. **Domain:** confirm `mail.anione.me` shows `verified` in Resend.
2. **Smoke test:** send one email (single `POST /emails`) to your own inbox; confirm DKIM/SPF pass (Gmail "show original") and the unsubscribe link/header render.
3. **Path C:** create a throwaway Segment with 2-3 internal addresses; run the dispatcher against a test date → confirm the broadcast sends, the footer link works, and unsubscribing flips `contact.unsubscribed` and excludes them on a resend.
   **Path A:** point at a tiny CSV; confirm 100-chunking, throttle, `List-Unsubscribe` header present, one-click POST returns blank 200, and the address lands in suppression.
4. **Dry-run a real template day** to internal addresses before a live date.
5. **Cutover:** schedule the first live `CAMPAIGN_MAP` date on Resend; keep Postmark credentials until one full campaign cycle succeeds, then revoke.
6. **Monitor:** Resend dashboard for bounces (<4%) and spam complaints (<0.08%) — exceeding these pauses sending.

---

## 11. Key risks & gotchas

- **Batch cap 100, not 500** (Path A/B) — the current 500-chunk loop *will be rejected* if not changed.
- **5 req/s per team is shared** across all API keys — concurrent jobs can collide into 429s (Path A/B). Throttle + honor `retry-after`.
- **No automatic suppression for transactional sends** (Path A/B) — if you don't build it, you'll keep emailing people who unsubscribed (CAN-SPAM/GDPR + deliverability risk). This is the single biggest reason to prefer Path C.
- **`{{{ pm:unsubscribe }}}` renders literally** in Resend — every template/base-template must be updated or recipients see raw tag text.
- **Token vs placeholder confusion:** Broadcasts use `{{{RESEND_UNSUBSCRIBE_URL}}}`; the transactional reserved template variable is `UNSUBSCRIBE_URL` (no `RESEND_` prefix). Don't mix them.
- **Domain not verified → all sends 403.** Verify first; allow up to 72h.
- **Path C list churn:** monthly list changes require re-importing/syncing Segments (no bulk contacts API — dashboard CSV import or a per-contact sync script). The CSV scrub pipeline still runs first.
- **Free tier (100/day) cannot run the campaign** — a paid plan is mandatory before go-live.
- **`.env` in git** — rotate and stop tracking the secret during migration.

---

## 12. Open decisions for you

1. **Path C (Broadcasts) vs Path A (batch send)?** — recommendation is C; A is the fallback if you want to keep CSV-driven sends and own a small unsubscribe service.
2. **Plan tier** — Pro 50k ($20/mo) is sufficient for ~31k/month; choose 100k ($35) if other mail shares the account.
3. **(Path C) Segment sync strategy** — manual dashboard CSV re-import each month, or a one-time `POST /contacts` sync script?
4. **(Path A) Where to host the unsubscribe endpoint** — a second Railway service? And what suppression store (flat file vs DB)?
5. **Adopt the Resend Python SDK** (`resend`) or keep raw `requests`?
6. **Keep the `monthly-campaign` vs `christmas-campaign` distinction?** — Resend has no message streams; if still needed, model via separate API keys/subdomains or Topics.

---

## 13. Rough effort estimate

| Work | Path C | Path A |
|---|---|---|
| Resend account + domain verify | 0.5–1 day (mostly DNS wait) | same |
| Dispatcher code changes | ~0.5 day (simpler) | ~1 day |
| Unsubscribe service + suppression | — | **~1–2 days** |
| One-time contact/Segment import | ~0.5 day | — (lists stay as CSV) |
| Template + base-template + skill + docs edits | ~0.5 day | ~0.5 day |
| Testing & staged cutover | ~0.5–1 day | ~0.5–1 day |
| **Total** | **~2.5–3.5 days** | **~3.5–5 days** |
