"""
Send a TEST copy of a campaign template before the real campaign runs.

TWO MODES:
  • transactional (default): sends via Resend's /emails endpoint straight to ONE
        inbox you pass on the command line. Fast render check (images, dark mode,
        fonts). Does NOT touch segments. The {{{RESEND_UNSUBSCRIBE_URL}}} footer
        shows as literal text here (it only resolves inside a real Broadcast).
  • --broadcast: exercises the REAL production send path. Sends a real Resend
        Broadcast of each template to the PERSISTENT test segment ("AniOne BROADCAST
        TEST"), reusing the exact send_broadcast() the daily cron uses, then polls
        each to its true terminal status. NO email argument — whoever you put in the
        "AniOne BROADCAST TEST" segment (manage it in the Resend dashboard) is who
        receives the test. This is the mode to use for testing managed unsubscribe.

WHY A PERSISTENT TEST SEGMENT: Resend sends broadcasts ASYNCHRONOUSLY (~30s). The
test segment is found-or-created by name and REUSED forever — never deleted —
because deleting it right after sending leaves the async send with no recipients,
which Resend marks 'failed'. You control its membership in the Resend dashboard.

Usage:
    python preview.py you@example.com                 # transactional, all templates
    python preview.py you@example.com day-1           # transactional, one template
    python preview.py --broadcast                     # REAL broadcast of all templates to the test segment
    python preview.py day-1 --broadcast               # REAL broadcast of day-1 to the test segment
"""
import sys
import time
import requests

# Force UTF-8 stdout so emoji status lines don't crash on Windows (cp1252) consoles.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

from deploy_new_year import (
    RESEND_API_KEY,
    API_BASE,
    FROM,
    load_template,
    send_broadcast,   # the EXACT function the daily cron uses — tested verbatim
)
from sync_contacts import create_segment

# The campaign templates for the CURRENT month — all 11 slots.
# ⚠️ RE-POINT THIS AT THE NEW MONTH EVERY ROLLOVER. It fails SILENTLY if you don't:
# _filter_dirs() matches only the last path segment, so `preview.py day-1` happily
# tests the previous month's day-1 and reports success. (It sat on templates/july/
# through the whole August campaign, so August was never actually preview-tested.)
CAMPAIGN_MONTH = "september"
TEMPLATE_DIRS = [f"templates/{CAMPAIGN_MONTH}/{slot}" for slot in (
    "day-1", "day-3", "day-5", "day-7", "day-9", "day-10",
    "drop-1", "drop-2", "drop-3",      # paid token drops — omitted before, now covered
    "finale-1", "finale-2",
)]

THROTTLE_SECONDS = 0.25  # stay under the 5 req/s team rate limit
TEST_SEGMENT_NAME = "AniOne BROADCAST TEST"  # persistent test segment, membership managed in Resend


def _auth():
    return {"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"}


def send_test(template_dir, to_email):
    """Sends one template to to_email via the transactional /emails endpoint."""
    html, text, subject, name = load_template(template_dir)
    if not subject:
        print(f"   ❌ No 'Subject:' in {template_dir}/metadata.txt — skipping.")
        return False

    payload = {"from": FROM, "to": [to_email], "subject": f"[TEST] {subject}", "html": html}
    if text:
        payload["text"] = text

    try:
        resp = requests.post(f"{API_BASE}/emails", headers=_auth(), json=payload, timeout=30)
    except requests.exceptions.RequestException as e:
        print(f"   ❌ {template_dir}: network error: {e}")
        return False

    if 200 <= resp.status_code < 300:
        print(f"   ✅ {template_dir.split('/')[-1]:<7} → {to_email}  (\"{subject}\")  id={resp.json().get('id')}")
        return True
    print(f"   ❌ {template_dir}: {resp.status_code} {resp.text[:200]}")
    return False


def _segment_contacts(seg_id):
    """Return the contacts currently in a segment (first page is plenty for a test)."""
    r = requests.get(f"{API_BASE}/segments/{seg_id}/contacts", headers=_auth(),
                     params={"limit": 100}, timeout=30)
    r.raise_for_status()
    return r.json().get("data", []) or []


def _find_or_create_test_segment():
    """Return the id of the PERSISTENT broadcast-test segment, creating it once if it
    doesn't exist yet. Reused (never deleted) across runs — see module docstring."""
    try:
        for s in requests.get(f"{API_BASE}/segments", headers=_auth(), timeout=30).json().get("data", []):
            if s.get("name") == TEST_SEGMENT_NAME:
                print(f"   ♻️  reusing test segment '{TEST_SEGMENT_NAME}' → {s['id']}")
                return s["id"]
    except requests.exceptions.RequestException:
        pass
    return create_segment(TEST_SEGMENT_NAME)  # prints "➕ Created segment ..."


def _broadcast_ids_for_segment(seg_id):
    """Set of broadcast ids currently targeting seg_id (to isolate THIS run's sends)."""
    try:
        return {b["id"] for b in requests.get(f"{API_BASE}/broadcasts", headers=_auth(), timeout=30).json().get("data", [])
                if (b.get("segment_id") or b.get("audience_id")) == seg_id}
    except requests.exceptions.RequestException:
        return set()


def _wait_for_broadcasts(seg_id, before_ids, expected, timeout=150):
    """Poll until THIS run's broadcasts (ids not in before_ids) reach a terminal
    status. Broadcasts send async (~30s), so a 2xx create is only 'accepted'."""
    deadline = time.time() + timeout
    statuses = {}
    while time.time() < deadline:
        try:
            rows = [b for b in requests.get(f"{API_BASE}/broadcasts", headers=_auth(), timeout=30).json().get("data", [])
                    if (b.get("segment_id") or b.get("audience_id")) == seg_id and b["id"] not in before_ids]
        except requests.exceptions.RequestException:
            rows = []
        statuses = {b["id"]: b.get("status") for b in rows}
        if len(statuses) >= expected and all(s in ("sent", "failed", "canceled") for s in statuses.values()):
            break
        time.sleep(5)
    return statuses


def run_broadcast_test(dirs, label="test"):
    """Fire REAL Resend Broadcast(s) of each template at the PERSISTENT test segment
    (whatever contacts you've put in it), reusing the production send_broadcast(), and
    poll each to its true terminal status (sent/failed). No email argument — the
    segment's membership (managed in the Resend dashboard) IS the recipient list."""
    print(f"📡 BROADCAST test — real Resend Broadcast(s) to segment '{TEST_SEGMENT_NAME}'\n")
    seg_id = _find_or_create_test_segment()

    members = _segment_contacts(seg_id)
    if not members:
        print(f"\n   ❌ Test segment '{TEST_SEGMENT_NAME}' has no contacts. Add your test address(es) to it\n"
              f"      in the Resend dashboard, then re-run. (Broadcasts send to a segment, not an address.)")
        return
    emails = [c.get("email") for c in members if c.get("email")]
    shown = ", ".join(emails[:5]) + (" …" if len(emails) > 5 else "")
    print(f"   recipients in segment: {len(members)} ({shown})")

    print(f"\n   firing broadcast(s):\n")
    before = _broadcast_ids_for_segment(seg_id)
    for d in dirs:
        print(f"   • {d.split('/')[-1]:<8}", end="")
        send_broadcast(d, seg_id, label)
        time.sleep(THROTTLE_SECONDS)

    print(f"\n   ⏳ Broadcasts send asynchronously — waiting for delivery status (~30-60s)...")
    statuses = _wait_for_broadcasts(seg_id, before, expected=len(dirs))
    sent = sum(1 for s in statuses.values() if s == "sent")
    for bid, s in statuses.items():
        print(f"   {'✅' if s == 'sent' else '❌'} broadcast {bid[:8]}… → {s}")
    print(f"\n🎉 {sent}/{len(dirs)} broadcast(s) actually SENT to the test segment "
          f"({len(members)} recipient(s)). {'Check the inbox.' if sent else 'See statuses above.'}")
    print(f"   (test segment '{TEST_SEGMENT_NAME}' left in place for reuse next time)")


def _filter_dirs(wanted):
    """Resolve template-name filters to dirs; exit with a helpful message if none match."""
    if not wanted:
        return TEMPLATE_DIRS
    dirs = [d for d in TEMPLATE_DIRS if d.split("/")[-1] in wanted]
    if not dirs:
        print(f"❌ None of {wanted} matched a known template. Options: "
              f"{[d.split('/')[-1] for d in TEMPLATE_DIRS]}")
        sys.exit(1)
    return dirs


def main():
    if not RESEND_API_KEY:
        print("❌ RESEND_API_KEY missing in environment.")
        sys.exit(1)

    raw = sys.argv[1:]
    broadcast = "--broadcast" in raw
    args = [a for a in raw if not a.startswith("--")]

    if broadcast:
        # No email needed — the test segment's membership is the recipient list.
        # Drop any email-looking arg passed out of habit; the rest are template filters.
        wanted = [a for a in args if "@" not in a]
        run_broadcast_test(_filter_dirs(wanted), label=time.strftime("%m%d-%H%M%S"))
        return

    # Transactional mode still needs the destination inbox.
    if not args:
        print("Usage:\n"
              "  python preview.py you@example.com [day-1 day-7 ...]   # transactional preview\n"
              "  python preview.py [day-1 ...] --broadcast             # real broadcast to the test segment")
        sys.exit(1)

    to_email = args[0]
    dirs = _filter_dirs(args[1:])
    print(f"📨 Sending {len(dirs)} test email(s) to {to_email} (transactional — segments untouched)...")
    sent = 0
    for d in dirs:
        if send_test(d, to_email):
            sent += 1
        time.sleep(THROTTLE_SECONDS)

    print(f"\n🎉 Done: {sent}/{len(dirs)} test emails sent to {to_email}.")
    if sent < len(dirs):
        print("⚠️ Some failed — see errors above (often a domain-not-verified or rate-limit issue).")


if __name__ == "__main__":
    main()
