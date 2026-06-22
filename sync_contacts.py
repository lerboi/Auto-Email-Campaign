"""
Sync the local CSV email lists into Resend Segments.

Resend Broadcasts send to a Segment (a managed contact list) rather than to an
inline list of addresses. This script keeps the CSV files in /email as the
SOURCE OF TRUTH and pushes their addresses into the two campaign segments. Run
it once per month after you update the lists — it replaces the old "upload the
templates to the Postmark dashboard" step.

Usage:
    python sync_contacts.py --create   # first time: create the two segments, print their IDs
    python sync_contacts.py            # sync the CSVs into the configured segments

Notes:
- Resend has NO bulk contact-import API, so contacts are created one at a time.
  Expect roughly (number_of_emails / 4) seconds — the API rate limit is
  5 requests/second per team and this script stays just under it.
- Existing contacts are left untouched, so anyone who has unsubscribed STAYS
  unsubscribed. This script never re-subscribes anyone.
- Membership is additive (it adds the CSV's addresses to the segment; it does not
  remove anyone). To retarget a segment from scratch, create a fresh one with
  --create and point RESEND_SEGMENT_A/B (and CAMPAIGN_MAP) at the new IDs.
"""
import csv
import os
import sys
import time
import requests

from deploy_new_year import (
    RESEND_API_KEY,
    API_BASE,
    GROUP_A_FILES,
    GROUP_B_FILES,
    SEGMENT_A,
    SEGMENT_B,
)

THROTTLE_SECONDS = 0.25   # ~4 req/s, comfortably under the 5 req/s team rate limit
MAX_SAMPLE_ERRORS = 5     # how many skipped/failed responses to print per segment


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


def sync_segment(label, files, segment_id):
    emails = load_emails(files)
    print(f"\n🔁 Syncing {label}: {len(emails)} unique emails → segment {segment_id}")

    created = skipped = failed = 0
    samples = []
    for i, email in enumerate(emails, 1):
        payload = {"email": email, "segments": [{"id": segment_id}]}
        try:
            resp = requests.post(f"{API_BASE}/contacts", headers=auth_headers(), json=payload)
            if 200 <= resp.status_code < 300:
                created += 1
            elif 400 <= resp.status_code < 500:
                # Most commonly the contact already exists (left untouched, so its
                # unsubscribe status is preserved). Record a few samples for review.
                skipped += 1
                if len(samples) < MAX_SAMPLE_ERRORS:
                    samples.append(f"{email}: {resp.status_code} {resp.text[:120]}")
            else:
                failed += 1
                if len(samples) < MAX_SAMPLE_ERRORS:
                    samples.append(f"{email}: {resp.status_code} {resp.text[:120]}")
        except Exception as e:
            failed += 1
            if len(samples) < MAX_SAMPLE_ERRORS:
                samples.append(f"{email}: {e}")

        if i % 200 == 0:
            print(f"   … {i}/{len(emails)} processed")
        time.sleep(THROTTLE_SECONDS)

    print(f"   ✅ Done {label}: {created} created, {skipped} skipped (already exist / invalid), {failed} failed.")
    if samples:
        print("   ℹ️ Sample non-success responses:")
        for s in samples:
            print(f"      - {s}")


def main():
    if not RESEND_API_KEY:
        print("❌ Error: RESEND_API_KEY missing in environment.")
        sys.exit(1)

    seg_a, seg_b = SEGMENT_A, SEGMENT_B

    if "--create" in sys.argv:
        print("🆕 Creating campaign segments...")
        seg_a = create_segment("AniOne Group A")
        seg_b = create_segment("AniOne Group B")
        print("\n👉 Add these to your environment (Railway + .env), then re-run without --create:")
        print(f"   RESEND_SEGMENT_A={seg_a}")
        print(f"   RESEND_SEGMENT_B={seg_b}")
        return

    if not seg_a or not seg_b:
        print("❌ Segment IDs not set. Run once with --create, then set RESEND_SEGMENT_A / RESEND_SEGMENT_B.")
        sys.exit(1)

    sync_segment("Group A", GROUP_A_FILES, seg_a)
    sync_segment("Group B", GROUP_B_FILES, seg_b)
    print("\n🎉 Sync complete. Run `python deploy_new_year.py` (or let the cron run) to send.")


if __name__ == "__main__":
    main()
