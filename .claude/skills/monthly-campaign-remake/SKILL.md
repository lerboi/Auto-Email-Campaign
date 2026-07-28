---
name: monthly-campaign-remake
description: Recreates Anione's monthly Resend email campaign templates for a new month. Use this skill whenever the user says things like "new month campaign", "remake templates for April", "update campaign for next month", "create new monthly emails", "prepare next campaign", or any request about generating fresh email templates for a new campaign period. This is the primary skill for the monthly email marketing workflow.
---

# Monthly Campaign Remake

This skill handles the end-to-end process of remaking Anione's monthly Resend email campaign for a new month. A month is **11 unique templates** sent across ~26 days in **three phases** to **five Resend Segments (A–E)**. Templates are sent **inline** via Resend Broadcasts (read from disk at send time) — there is no template-upload-to-dashboard step.

> **`CLAUDE.md` ("Monthly Campaign Structure & Contact CSVs") is the source of truth for the campaign shape.** Read it first. This skill covers how to *generate the content* for that shape.

## The 11 templates (not 6)

| Group | Templates | Sent to | Phase |
|---|---|---|---|
| **Wave templates** | `day-1, day-3, day-5, day-7, day-9, day-10` | free lists via A/B then C/D | Waves 1 & 2 |
| **Paid drops** | `drop-1, drop-2, drop-3` | paid (Segment E) | mid Wave 2 (days 13/17/21) |
| **Paid finale** | `finale-1, finale-2` | paid (Segment E) | days 25–26 |

The **6 wave templates rotate twice**: A→B in Wave 1 (days 1–12), then the *same six* rotate C→D in Wave 2 (days 13–24). The 3 drops + 2 finale are paid-only, single-send. So it's 11 unique templates but ~26 send-days.

## Before You Start

1. **Read the current month's templates** in `templates/{month}/` — all 11 folders (`day-*`, `drop-*`, `finale-*`) — to see what exists and avoid repeating last month's copy. Browse older months for reference.
2. **Read `deploy_new_year.py`** (`CAMPAIGN_MAP` + `GROUP_A_FILES`…`GROUP_E_FILES`) and **`create_codes.py`** (`CONFIG` block) to see the current dates, segments, lists, and codes.
3. **Ask the user** for (do not assume):
   - **Target month** (e.g., "August 2026") and **campaign start date** (day 1 of the month).
   - **Seasonal theme / vibe** (e.g., "Summer heat wave", "Back to school").
   - **Promo codes** — the user decides. A full month needs **8**:
     - Day-1 **gift code** (token grant, e.g. `AUG2026` → 10 image tokens)
     - Day-7 **sale voucher** (e.g. `AUG20` → 20% off subscription)
     - Day-9/10 **multiplier voucher** (e.g. `AUGSURGE` → 1.5× on token packs; day-10 reuses day-9's code)
     - Three **drop codes** (token grants, e.g. `AUGDROP1/2/3` → 20 image tokens each)
     - Finale **gift code** (token grant, e.g. `AUGVIP30` → 30 image tokens)
     - Finale **sale voucher** (e.g. `AUGFINAL20` → 20% off subscription)
   - **Day 3 & Day 5 feature topics** — the two flexible "feature showcase" slots. The user picks what to highlight (Custom Characters, Custom Scenarios, Voice Calls, Image Generation, New Characters, Streak Rewards, etc.). Ask for both; they may reuse last month's topics but the copy must be fresh.
   - **Any offer changes** (different discount %, token amounts, multiplier).
   - **Hero images** — reuse existing (default) or new URLs.
   - **Recipient lists** — are the **5 CSVs** (4 free + 1 paid) refreshed this month? (See Step 4.)

## Template Content Anatomy (What Goes In Each Day)

Each day's email has a distinct content recipe. Preserve these structural patterns when remaking — they're what make each email feel different while maintaining the funnel progression (free gift → features → sale → multiplier → urgency).

### Day 1 — Free Gift (Voucher Code Email)

**Content blocks:**
1. Hero image (character art, links to redemption page with code pre-filled)
2. Warm greeting + 2-3 paragraphs: "new month, new possibilities" seasonal opener → mention the gift → explain what it unlocks
3. Horizontal divider line
4. **Green dashed offer box** (bg `#f0fdf4`, border `#166534`):
   - Box title: "{MONTH} GIFT VOUCHER" (uppercase, bold, green)
   - Description: "Use this code to get **10 Image tokens** or explore our brand new characters for free"
   - Expiry notice: "Expires in 48 Hours" (red text, uppercase)
   - Code display: `{CODE}` in monospace on white bg with dashed green border
   - CTA button: "Redeem My Gift Now →" (red `#D42426`)
5. P.S. line teasing upcoming month updates (italic, gray, centered)

**CTA link pattern:** `https://www.anione.me/en/Profile?tab=redeem&code={CODE}`
**Unique to Day 1:** Only wave template with an expiry timer on a free gift. Simplest offer box (no bullet list). Horizontal divider before the box.

---

### Day 3 — Feature Showcase #1 (Variable Content)

> **This is a flexible slot.** The specific feature changes each month based on what the user wants to highlight. Ask the user what feature to showcase.

**Structural pattern (stays the same regardless of feature):**
1. Hero image (relevant to the featured topic)
2. Bold heading emphasizing the feature's core appeal
3. 1-2 paragraphs about what the feature lets you do
4. **Embedded GIF** showing the feature in action (captioned)
5. 1 paragraph going deeper on the experience + unrestricted environment
6. **Optional: Showcase image** (static screenshot, with subtle 1px border) — use when the feature is visual (characters, images) but skip for non-visual features (voice, chat)
7. **Blue dashed feature box** (bg `#eff6ff`, border `#3b82f6`):
   - Box title: descriptive toolkit name (uppercase, bold, blue `#1e40af`)
   - **3 bullet-point features** (each with bold label + description) — highlight the top 3 selling points of the chosen feature
   - CTA button: action-oriented text + " →" (blue `#3b82f6`)
8. Closing one-liner (bold, centered)

**CTA link pattern:** `https://www.anione.me/en` (or a more specific page if the feature has one)
**Key traits:** Most image-heavy template (hero + GIF + optional showcase = 2-3 visuals). 3-item bullet feature list. No promo code. Blue color scheme.

**Previous feature topics used:**
- March 2026: Custom Characters ("She's exactly who you want her to be")
- July/August 2026: New Characters ("meet the lineup")

---

### Day 5 — Feature Showcase #2 (Variable Content)

> **This is a flexible slot.** The specific feature changes each month. Must be different from whatever Day 3 covers. Ask the user.

**Structural pattern (stays the same regardless of feature):**
1. Hero image (relevant to featured topic, can differ from Day 3)
2. Bold heading emphasizing the feature's empowerment angle
3. 1-2 paragraphs about the feature — position the user as the one in control
4. **Embedded GIF** showing the feature in action (captioned)
5. 1 paragraph expanding on the experience and freedom
6. **Purple dashed feature box** (bg `#f5f3ff`, border `#8b5cf6`):
   - Box title: thematic/seasonal name rather than just descriptive (uppercase, bold, purple `#5b21b6`)
   - **5 bullet-point features** (each with bold label + description) — more comprehensive breakdown than Day 3
   - CTA button: action-oriented text + " →" (purple `#8b5cf6`)
7. Closing challenge line (bold, centered)

**CTA link pattern:** `https://www.anione.me/en` (or a more specific page, e.g. `/en/Wheel` for Streak Rewards)
**Key traits:** Longer feature list (5 bullets vs. Day 3's 3). Has GIF but typically no showcase image (2 visuals). No promo code. Purple color scheme. Box title is themed to the month, not just the feature name.

**Previous feature topics used:**
- March 2026: Custom Scenarios ("Your World. Your Story. Your Rules.")
- July/August 2026: Streak Rewards on the daily Wheel ("Spin daily, stack chests")

---

### Day 7 — Flash Sale (Subscription Discount)

**Content blocks:**
1. Hero image (different character art from Days 3/5)
2. Bold urgent heading with timer emoji (e.g., "⏳ 48-HOUR {MONTH} FLASH SALE")
3. Greeting + 2 paragraphs: seasonal transition opener → "For the next 48 hours, upgrade for **20% less**"
4. **Green dashed offer box** (bg `#f0fdf4`, border `#166534`):
   - Box title: "EXCLUSIVE: $7.99/mo DEAL" (bold, centered, green `#166534`)
   - Instruction text with code name bolded
   - **3 benefit bullets** (with special characters as bullet markers):
     - "∞ Unlimited Text & High-Intel Roleplay"
     - "200 AI Images per month"
     - "50 Tokens + 25% OFF Daily Wheel Spins"
   - Code display: `CODE: {CODE}` on white bg with dashed border
   - Fine print: "*Applicable on subscriptions only" (11px, gray, italic)
   - CTA button: "Upgrade My {Month} →" (red `#D42426`)
5. Closing urgency line (italic, centered)

**CTA link pattern:** `https://www.anione.me/en/Pricing?voucher={CODE}`
**Unique to Day 7:** Only template showing actual pricing ($X.XX/mo). Has fine print disclaimer. Benefit bullets use special characters (∞) not just text. Links to Pricing page, not homepage or Profile.

---

### Day 9 — Token Multiplier (1.5x Bonus)

**Content blocks:**
1. Hero image (different character art)
2. Bold exciting heading with lightning emoji (e.g., "⚡ 1.5x TOKEN MULTIPLIER ACTIVATED!")
3. Greeting + 2 paragraphs: "Why settle for standard when you can have **50% MORE?**" → explain the 1.5x multiplier on all token pack purchases for 48 hours
4. **Red/pink dashed offer box** (bg `#fdf2f2`, border `#D42426`):
   - Box title: "🚀 LIMITED TIME: 50% BONUS TOKENS" (bold, centered, red `#D42426`)
   - Simple instruction text: "Use the code below at checkout to receive 1.5x more tokens on any pack purchase"
   - Code display: `CODE: {CODE}` on white bg with dashed red border
   - CTA button: "Get My Bonus Tokens →" (red `#D42426`)
5. Closing confidence line (italic, centered)

**CTA link pattern:** `https://www.anione.me/en/Pricing?voucher={CODE}`
**Unique to Day 9:** Simpler box than Day 7 — no bullet list, just instructional text + code + CTA. Focuses on token packs, not subscriptions. Red/pink color scheme.

---

### Day 10 — Final Urgency (24-Hour Deadline)

**Content blocks:**
1. Hero image (can be different from Day 9 or platform homepage hero)
2. Bold urgent heading with timer emoji (e.g., "⏳ FINAL HOURS: Don't miss your bonus tokens!")
3. Greeting + 2 paragraphs: "This is a quick reminder" that the multiplier ends in <24 hours → "Once the timer hits zero, the 50% bonus tokens will disappear"
4. **Orange/warm dashed offer box** (bg `#fffaf0`, border `#D42426`):
   - Box title: "⚠️ ENDING SOON: 1.5x MULTIPLIER" (bold, centered, dark orange `#9a3412`)
   - Instruction text about using code before expiry
   - Code display: `CODE: {CODE}` — **larger font (20px)** than Day 9's code display for emphasis
   - CTA button: "Claim My Bonus Tokens →" (red `#D42426`)
5. Closing gratitude line: "Thank you for being a part of Anione. Happy {Month} creating!"

**CTA link pattern:** `https://www.anione.me/en/Pricing?voucher={CODE}`
**Unique to Day 10:** Uses the **same code as Day 9** (it's a reminder). Warning emoji (⚠️) instead of rocket. Orange-warm background. Larger code font for visual emphasis. Closing line shifts from confidence to gratitude. Simplest offer box overall.

---

### Quick Reference: Content Ingredients by Day

| Element | Day 1 | Day 3 | Day 5 | Day 7 | Day 9 | Day 10 |
|---------|-------|-------|-------|-------|-------|--------|
| **Hero image** | Yes | Yes | Yes | Yes | Yes | Yes |
| **Inline GIF** | No | Yes | Yes | No | No | No |
| **Showcase image** | No | Optional | No | No | No | No |
| **Box color** | Green | Blue | Purple | Green | Red/pink | Orange/warm |
| **Bullet list** | None | 3 items | 5 items | 3 items | None | None |
| **Content fixed?** | Yes | **No — variable** | **No — variable** | Yes | Yes | Yes |
| **Promo code** | Gift code | None | None | Sale voucher | Multiplier voucher | Same as Day 9 |
| **CTA links to** | Profile/Redeem | Homepage | Homepage/feature | Pricing | Pricing | Pricing |
| **Closing tone** | Anticipation | Confidence | Challenge | Urgency | Confidence | Gratitude |

### Paid Drops — `drop-1`, `drop-2`, `drop-3` (Segment E, days 13/17/21)

Three paid-only "care package" gift emails that fill the paid gap during Wave 2 (free users are getting Wave-2 emails; paid users get these instead). Each is a **separate token-grant code** (`{MON}DROP1/2/3` → 20 image tokens), redeemed on Profile.

**Content pattern (simple, warm, "no strings"):**
1. Hero image + short warm heading ("A token care package")
2. 1-2 short paragraphs: a thank-you-for-being-a-member gift, no purchase required
3. Green/gift dashed offer box with the `{CODE}` and a "Grab My Tokens →" CTA
4. Keep each of the three distinct (drop-1 "on us", drop-2 "more", drop-3 "last drop of the month")

**CTA link pattern:** `https://www.anione.me/en/Profile?tab=redeem&code={CODE}`
**No base skeleton exists** — generate these from the **previous month's `drop-*` templates** (copy structure, swap month/copy/code).

### Paid Finale — `finale-1`, `finale-2` (Segment E, days 25–26)

The paid month closes with two dedicated emails:
- **`finale-1` — Premium gift:** members-only token grant, larger than a drop (e.g. `{MON}VIP30` → **30 image tokens**). Structure like Day-1 gift but "exclusive / members only", Profile redeem CTA, 48-hour expiry copy.
- **`finale-2` — Final sale:** last-chance subscription discount voucher (e.g. `{MON}FINAL20` → 20% off), "ends tonight" urgency, Pricing CTA.

**No base skeleton exists** — generate from the **previous month's `finale-*` templates**.

## File Structure Per Template

Each template lives in `templates/{month}/{day-N|drop-N|finale-N}/` with exactly 3 files:

### `metadata.txt`
```
Name: {Month} {Day/Drop/Finale label} ({Short Description})
Subject: {emoji} {Subject Line}
Alias: {mon}-{purpose}-{slot}
```
With Resend, `Alias` is just an internal label (kept for readability). The dispatcher sends a Broadcast using the `Subject` and `Name` from `metadata.txt` and the inline `template.html`/`template.txt` — it does **not** look up a template by alias. `CAMPAIGN_MAP` keys each date to a `template_dir` + `segment`. (Drop/finale aliases may be left blank.)

### `template.html`
The 600px-wide table-layout HTML email: preheader div, Anione logo header, hero image, heading with emoji, 2-3 body paragraphs, the dashed feature/offer box (color-coded by type), CTA button, footer with copyright + the `{{{RESEND_UNSUBSCRIBE_URL}}}` Resend managed-unsubscribe placeholder. Full dark-mode (`@media (prefers-color-scheme: dark)` + Outlook `[data-ogsc]`) and mobile-responsive (`@media max-width: 600px`).

### `template.txt`
Plain-text fallback with the same key info, promo code, and links (including the `{{{RESEND_UNSUBSCRIBE_URL}}}` footer).

## Step-by-Step Remake Process

### Step 1: Generate all 11 templates

For each template, create the 3 files in `templates/{month}/{slot}/` (lowercase full month name). **The 6 wave templates** can start from `base-templates/` skeletons (replace `{{PLACEHOLDER}}` vars). **The 3 drops + 2 finale** have no skeletons — copy the **previous month's** `drop-*`/`finale-*` and refresh. Fastest reliable path for ALL 11: read the previous month's exact template, preserve the HTML/CSS/structure, and change only copy + code + subject.

**What changes per month:** month name & seasonal references, promo codes, subject lines (fresh, not recycled), preheader text, body copy (new angles — don't repeat last month's phrasing), seasonal emoji, alias prefix, copyright year (if it changes), image `alt`/`<title>` month references.
**What stays the same:** HTML structure & CSS, logo/branding, per-type color scheme, CTA link patterns, the `{{{RESEND_UNSUBSCRIBE_URL}}}` placeholder, 600px width, and the funnel progression.

**Verify after generating:** every file keeps `{{{RESEND_UNSUBSCRIBE_URL}}}` (html + txt), the new code appears in every CTA URL and code box, and **no previous-month references remain** (grep the month name and old codes across `templates/{month}/`, including image `alt` text and `<title>`).

### Step 2: Update `CAMPAIGN_MAP` in `deploy_new_year.py`

Map each date to `{template_dir, segment}`. A date may map to a **single dict OR a list of dicts** (drop days fire two sends). Segments are `SEGMENT_A`…`SEGMENT_E` (from `RESEND_SEGMENT_A`…`E`).

```python
CAMPAIGN_MAP = {
    # Wave 1 (1-12): free A/B + paid riding A, A->B alternating
    "{m}-01": {"template_dir": "templates/{mon}/day-1",  "segment": SEGMENT_A},
    "{m}-02": {"template_dir": "templates/{mon}/day-1",  "segment": SEGMENT_B},
    # ... day-3 (03/04), day-5 (05/06), day-7 (07/08), day-9 (09/10), day-10 (11/12) ...

    # Wave 2 (13-24): free C/D, C->D alternating; paid drops on 13/17/21 -> E
    "{m}-13": [{"template_dir": "templates/{mon}/day-1",  "segment": SEGMENT_C},
               {"template_dir": "templates/{mon}/drop-1", "segment": SEGMENT_E}],
    "{m}-14": {"template_dir": "templates/{mon}/day-1",  "segment": SEGMENT_D},
    # ... 15/16 day-3, 17 (day-5 C + drop-2 E), 18 day-5 D, 19/20 day-7, 21 (day-9 C + drop-3 E), 22 day-9 D, 23/24 day-10 ...

    # Paid finale (25-26): Segment E only
    "{m}-25": {"template_dir": "templates/{mon}/finale-1", "segment": SEGMENT_E},
    "{m}-26": {"template_dir": "templates/{mon}/finale-2", "segment": SEGMENT_E},
}
```
When adding a new month while the previous month's finale is still pending, **append** the new block and leave the pending dates intact (past dates never re-fire).

### Step 3: Create the campaign's codes & vouchers (`create_codes.py`)

Every code a template references must exist in the animechat-ai app, or the email links redeem nothing. Edit the `CONFIG` block (`CODES` + `VOUCHERS`), then `python create_codes.py` (dry run) → `--create` → `--verify`. See **CLAUDE.md "Campaign Codes & Vouchers"** for the full rules. The two that bite:
- **Codes** start a **day before** their first send; **all 8 expire end-of-month** so the Wave-2 reuse (≈12 days later) never hits an expired code.
- Codes are **case-sensitive** and must match the email URL exactly. Use fresh strings each month (can't collide with a prior month's still-valid code).

### Step 4: Verify / refresh the 5 recipient CSVs + segments

The month needs **5 CSVs** (4 free + 1 paid) in `email/`, wired into `GROUP_A_FILES`…`GROUP_E_FILES`:
- Free lists → A, B, C, D. Put the **smallest free list in A** (it also carries the paid ride-along) to keep the four wave sends even.
- Paid CSV → referenced in **both** `GROUP_A_FILES` and `GROUP_E_FILES` (created once, billed once).
- **Sizing rule:** `free1 + free2 + free3 + free4 + paid ≤ 10,000` (the plan's contact cap; paid counted once).

If the lists changed, run `python sync_contacts.py --fresh` to wipe + reload the segments. **Timing:** a `--fresh` sync **wipes all contacts including the previous month's paid finale audience** — run it only **after** the prior month's finale (day-26) has fired.

### Step 5: Present a summary for review

| Slot | Subject | Code | Segment / dates |
|---|---|---|---|
| day-1 … finale-2 | … | … | … |

Plus the updated `CAMPAIGN_MAP` dates.

### Step 6: Go-live checklist

1. `mail.anione.me` sending domain is `verified` in Resend (DKIM/SPF/MX).
2. `python create_codes.py --create` (then `--verify`) — codes exist in the app.
3. `python sync_contacts.py --fresh` — **after** the prior finale — loads the 5 CSVs into segments A–E. A clean run reports `N created, 0 existed, 0 failed`.
4. `python preview.py --broadcast` — real test send to the `AniOne BROADCAST TEST` segment. **Run it before the `--fresh` wipe** (which empties the test segment), and note `TEMPLATE_DIRS` covers `day-*`/`finale-*` but **not `drop-*`** — add the drop dirs there to test those too.
5. `RESEND_API_KEY` + `RESEND_SEGMENT_A`…`E` set in Railway **and** `.env`.
6. Every `template.html`/`template.txt` footer still has `{{{RESEND_UNSUBSCRIBE_URL}}}`.
7. The Railway cron runs `deploy_new_year.py` daily and sends each `CAMPAIGN_MAP` date automatically — no manual send.

## Writing Guidelines for Email Copy

- **Tone**: Conversational, slightly playful, not corporate. Address the reader as "you".
- **Length**: 2-3 short paragraphs max. People skim.
- **Urgency**: Time-limited language for sale/multiplier/finale days ("48 hours", "expires soon", "ends tonight").
- **Feature emails**: Focus on what the user can DO, not what the feature IS. Paint a picture.
- **Avoid**: Repeating phrases across emails, and repeating last month's copy. Each should feel fresh. Vary subject-line emojis rather than reusing one across all sends.
- **Deliverability**: keep copy inbox-safe — no explicit wording, no spammy ALL-CAPS/"FREE!!!"/"$$$" patterns.
- **Seasonal hooks**: Tie the month/season into the opening naturally — don't force it.
- **P.S. lines**: Use sparingly (Day 1 is good for teasing upcoming content).

## Base Templates

`base-templates/` holds ready-to-use HTML/text skeletons for the **6 wave templates** only:

```
base-templates/
├── gift-day-1/             # Day 1: Free gift voucher (green box, red CTA)
├── feature-showcase-day-3/ # Day 3: Feature spotlight #1 (blue box, 3 bullets, GIF)
├── feature-showcase-day-5/ # Day 5: Feature spotlight #2 (purple box, 5 bullets, GIF)
├── sale-day-7/             # Day 7: Flash sale (green box, pricing, 3 benefit bullets)
├── multiplier-day-9/       # Day 9: Token multiplier (red/pink box, code + CTA)
└── urgency-day-10/         # Day 10: Final urgency (orange/warm box, larger code font)
```

Replace all `{{PLACEHOLDER}}` vars (see `references/placeholder-variables.md`) and write to `templates/{month}/day-N/`. **There are no skeletons for `drop-*` or `finale-*`** — generate those from the previous month's actual templates.

**Best practices baked into the skeletons:** Outlook dark-mode fix (`[data-ogsc]`), 600px mobile breakpoint, preheader div, MSO table attributes, `role="presentation"`, image alt text, the `{{{RESEND_UNSUBSCRIBE_URL}}}` footer, and fully inline styles (no external CSS).

## References

- `references/anione-features.md` — Platform features, pricing, and messaging angles for writing copy.
- `references/placeholder-variables.md` — Variable reference for the 6 wave base templates.
- `CLAUDE.md` — "Monthly Campaign Structure & Contact CSVs" (the authoritative campaign shape) and "Campaign Codes & Vouchers" (code/voucher rules).
