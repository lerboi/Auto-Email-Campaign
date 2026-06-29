"""
Sync the local CSV email lists into the five Resend Segments (A..E).

The CSV files in /email are the SOURCE OF TRUTH. Each unique email is created as
a Resend contact ONCE, carrying the FULL SET of segments it belongs to (e.g. a
paid user in GROUP_A_FILES and GROUP_E_FILES is created with segments [A, E]).
This matters because Resend only sets a contact's segments on CREATION — there
is no API to add an existing contact to another segment.

Usage:
    python sync_contacts.py --create        # first time: create all 5 segments, print IDs
    python sync_contacts.py                 # sync the CSVs into the configured segments
    python sync_contacts.py --fresh         # DELETE all contacts first, then sync (clean slate)
    python sync_contacts.py --allow-empty   # don't error when a configured segment has 0 emails

⚠️ IMPORTANT — run with --fresh whenever segment membership changes (e.g. moving
to this 5-segment layout, or any time a contact must land in a NEW segment).
Without it, contacts that ALREADY exist return "already exists" and are NOT added
to their new segments — the summary reports them as `exists` and prints a loud
warning so you can re-run with --fresh.

Notes:
- Resend has NO bulk import/delete, so contacts are created/deleted one at a time
  (~ emails / 4 seconds; the 5 req/s rate limit is respected with retries on 429).
- --fresh clears Resend-side unsubscribe state, so always sync from CSVs already
  filtered to opted-in users (newsletter = true) exported from the app DB.
"""
import csv
import os
import sys
import time
import requests

# Force UTF-8 stdout so the emoji status lines below don't crash on Windows
# consoles (which default to cp1252 and can't encode characters like 🔁).
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

from deploy_new_year import (
    RESEND_API_KEY,
    API_BASE,
    GROUP_A_FILES,
    GROUP_B_FILES,
    GROUP_C_FILES,
    GROUP_D_FILES,
    GROUP_E_FILES,
    SEGMENT_A,
    SEGMENT_B,
    SEGMENT_C,
    SEGMENT_D,
    SEGMENT_E,
)

THROTTLE_SECONDS = 0.25   # ~4 req/s, comfortably under the 5 req/s team rate limit
MAX_SAMPLE_ERRORS = 5     # how many skipped/failed responses to print per segment
MAX_RETRIES = 5           # retries for HTTP 429 (rate limited) / transient network errors


def auth_headers():
    return {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json",
    }


def load_emails(filenames):
    """Loads and de-duplicates emails from a list of CSV files."""
    emails = set()
    for filename in filenames:
        if not os.path.exists(filename):
            print(f"⚠️ Warning: File '{filename}' not found. Skipping.")
            continue
        with open(filename, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            key = next((h for h in (reader.fieldnames or []) if h.lower() == "email"), None)
            if not key:
                print(f"⚠️ No 'email' column in {filename}. Headers: {reader.fieldnames}")
                continue
            for row in reader:
                email = (row.get(key) or "").strip()
                if email:
                    emails.add(email.lower())
    return sorted(emails)


def create_segment(name):
    """Creates a new Resend segment and returns its ID."""
    resp = requests.post(f"{API_BASE}/segments", headers=auth_headers(), json={"name": name})
    resp.raise_for_status()
    seg = resp.json()
    print(f"   ➕ Created segment '{name}' → {seg['id']}")
    return seg["id"]


def post_contact(email, segment_ids):
    """Create one contact in ALL of `segment_ids` at once, retrying on HTTP 429
    and transient network errors. Returns (status, detail) where status is one of
    'created' | 'skipped' | 'failed'.

    Creating with every segment in a single POST matters because Resend only sets
    a contact's segments on CREATION — a second POST for an existing email returns
    "already exists" and does NOT add it to another segment. So callers must pass
    the full set of segments an email belongs to (e.g. paid users -> [A, E]).

    A 429 is NOT treated as "skipped" — it means we were throttled, so we honor
    the Retry-After header (or exponential backoff) and try again, only giving up
    (status 'failed') after MAX_RETRIES so the contact is never silently dropped.
    """
    payload = {"email": email, "segments": [{"id": s} for s in segment_ids]}
    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = requests.post(
                f"{API_BASE}/contacts", headers=auth_headers(), json=payload, timeout=30
            )
        except requests.exceptions.RequestException as e:
            if attempt < MAX_RETRIES:
                time.sleep(THROTTLE_SECONDS * (2 ** attempt))
                continue
            return "failed", f"network error after {MAX_RETRIES} retries: {e}"

        if 200 <= resp.status_code < 300:
            return "created", None

        if resp.status_code == 429:
            retry_after = resp.headers.get("Retry-After")
            try:
                wait = float(retry_after) if retry_after else THROTTLE_SECONDS * (2 ** attempt)
            except (TypeError, ValueError):
                wait = THROTTLE_SECONDS * (2 ** attempt)
            wait = max(wait, THROTTLE_SECONDS)
            if attempt < MAX_RETRIES:
                time.sleep(wait)
                continue
            return "failed", f"429 rate-limited after {MAX_RETRIES} retries"

        if 400 <= resp.status_code < 500:
            # Distinguish "already exists" (contact present but NOT (re)segmented —
            # Resend ignores `segments` on an existing email, so this needs a
            # --fresh run) from a genuinely invalid/rejected address.
            if resp.status_code == 409 or "exist" in resp.text.lower():
                return "exists", f"{resp.status_code} {resp.text[:120]}"
            return "invalid", f"{resp.status_code} {resp.text[:120]}"

        return "failed", f"{resp.status_code} {resp.text[:120]}"

    return "failed", "exhausted retries"


def build_email_segments():
    """Map each unique email -> the SET of segment ids it belongs to, across all
    five groups. Groups whose segment id is unset are skipped. Returns
    (email_segments, per_group_counts)."""
    groups = [
        ("A", GROUP_A_FILES, SEGMENT_A),
        ("B", GROUP_B_FILES, SEGMENT_B),
        ("C", GROUP_C_FILES, SEGMENT_C),
        ("D", GROUP_D_FILES, SEGMENT_D),
        ("E", GROUP_E_FILES, SEGMENT_E),
    ]
    email_segments, counts = {}, {}
    for label, files, seg in groups:
        if not seg:
            counts[label] = None  # segment id not configured
            continue
        emails = load_emails(files)
        counts[label] = len(emails)
        for e in emails:
            email_segments.setdefault(e, set()).add(seg)
    return email_segments, counts


def sync_all(email_segments):
    """Create each unique contact ONCE, with the full set of segments it belongs
    to. Returns the count of contacts that ALREADY EXISTED (and were therefore
    NOT (re)segmented) so the caller can flag an incorrect sync."""
    total = len(email_segments)
    print(f"\n🔁 Syncing {total} unique contacts (each created with all its segments)...")

    created = exists = invalid = failed = 0
    samples = []
    for i, (email, segs) in enumerate(sorted(email_segments.items()), 1):
        try:
            status, detail = post_contact(email, sorted(segs))
        except Exception as e:  # safety net for anything unexpected
            status, detail = "failed", str(e)

        if status == "created":
            created += 1
        elif status == "exists":
            exists += 1
        elif status == "invalid":
            invalid += 1
            if detail and len(samples) < MAX_SAMPLE_ERRORS:
                samples.append(f"{email}: {detail}")
        else:
            failed += 1
            if detail and len(samples) < MAX_SAMPLE_ERRORS:
                samples.append(f"{email}: {detail}")

        if i % 200 == 0:
            print(f"   … {i}/{total} processed")
        time.sleep(THROTTLE_SECONDS)

    print(f"   ✅ Done: {created} created, {exists} already existed, {invalid} invalid, {failed} failed.")
    if exists:
        print(f"   ⚠️  {exists} contacts ALREADY EXISTED and were NOT added to their segments")
        print(f"       (Resend ignores `segments` for an existing email). Their broadcasts may")
        print(f"       under-deliver. Re-run with `--fresh` to clear and recreate cleanly.")
    if samples:
        print("   ℹ️ Sample invalid/failed responses:")
        for s in samples:
            print(f"      - {s}")
    return exists


def list_all_contacts():
    """Return every contact (dicts with id/email) in the account, via cursor pagination."""
    contacts, after = [], None
    while True:
        params = {"limit": 100}
        if after:
            params["after"] = after
        r = requests.get(f"{API_BASE}/contacts", headers=auth_headers(), params=params, timeout=30)
        r.raise_for_status()
        body = r.json()
        data = body.get("data", []) or []
        contacts.extend(data)
        if not body.get("has_more") or not data:
            break
        after = data[-1]["id"]
        time.sleep(THROTTLE_SECONDS)
    return contacts


def delete_all_contacts():
    """Delete EVERY contact in the account (clean slate for a --fresh sync)."""
    contacts = list_all_contacts()
    print(f"🗑️  --fresh: deleting ALL {len(contacts)} existing contacts...")
    deleted = failed = 0
    for i, c in enumerate(contacts, 1):
        ok = False
        for attempt in range(MAX_RETRIES + 1):
            try:
                r = requests.delete(f"{API_BASE}/contacts/{c['id']}", headers=auth_headers(), timeout=30)
            except requests.exceptions.RequestException:
                if attempt < MAX_RETRIES:
                    time.sleep(THROTTLE_SECONDS * (2 ** attempt))
                    continue
                break
            if 200 <= r.status_code < 300 or r.status_code == 404:
                ok = True
                break
            if r.status_code == 429 and attempt < MAX_RETRIES:
                time.sleep(THROTTLE_SECONDS * (2 ** attempt))
                continue
            break
        deleted += int(ok)
        failed += int(not ok)
        if i % 200 == 0:
            print(f"   … {i}/{len(contacts)} deleted")
        time.sleep(THROTTLE_SECONDS)
    print(f"   ✅ Cleared {deleted}, failed {failed}.")
    return failed == 0


def main():
    if not RESEND_API_KEY:
        print("❌ Error: RESEND_API_KEY missing in environment.")
        sys.exit(1)

    # Fresh setup: create all five segments at once and print their IDs.
    if "--create" in sys.argv:
        print("🆕 Creating campaign segments...")
        ids = {
            "A": create_segment("AniOne Group A"),
            "B": create_segment("AniOne Group B"),
            "C": create_segment("AniOne Group C"),
            "D": create_segment("AniOne Group D"),
            "E": create_segment("AniOne Group E (Paid)"),
        }
        print("\n👉 Add these to your environment (Railway + .env), then re-run without --create:")
        for k, v in ids.items():
            print(f"   RESEND_SEGMENT_{k}={v}")
        return

    email_segments, counts = build_email_segments()
    print("Per-group unique emails:")
    configured_empty = []
    for label in ["A", "B", "C", "D", "E"]:
        c = counts.get(label)
        print(f"   Group {label}: {'(segment id not set — skipped)' if c is None else c}")
        if c == 0:  # segment id IS set but its CSV(s) yielded 0 emails (missing file?)
            configured_empty.append(label)

    # A configured segment with 0 emails would silently ship an empty campaign wave.
    if configured_empty and "--allow-empty" not in sys.argv:
        print(f"\n❌ Segment(s) {configured_empty} are configured but resolved to 0 emails "
              f"(missing/empty CSV?).\n   Provide their CSVs, unset their RESEND_SEGMENT_* vars, "
              f"or pass --allow-empty to proceed anyway.")
        sys.exit(1)

    if not email_segments:
        print("❌ Nothing to sync. Set RESEND_SEGMENT_A..E and provide the CSVs, then re-run.")
        sys.exit(1)

    if "--fresh" in sys.argv:
        if not delete_all_contacts():
            print("⚠️  Some deletions failed — continuing to sync anyway.")

    existed = sync_all(email_segments)
    print("\n🎉 Sync complete. Run `python deploy_new_year.py` (or let the cron run) to send.")
    if existed and "--fresh" not in sys.argv:
        print("⚠️  Membership may be incomplete (see warning above) — re-run with --fresh.")
        sys.exit(1)


if __name__ == "__main__":
    main()
