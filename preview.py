"""
Send a one-off TEST copy of each campaign template to a single address, so you
can preview the real rendering (images, dark mode, fonts) in your own inbox —
the Resend equivalent of Postmark's live preview.

This uses Resend's transactional /emails endpoint (NOT Broadcasts), so it does
NOT touch your segments and sends nothing to real recipients.

Note: the {{{RESEND_UNSUBSCRIBE_URL}}} placeholder only resolves inside a real
Broadcast, so in these test emails the footer "Unsubscribe" link will appear as
literal text. That is expected and only affects the preview, not the real send.

Usage:
    python preview.py you@example.com                 # send all 6 templates
    python preview.py you@example.com day-1 day-7     # send only specific days
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
)

# The campaign templates (templates/july/): 6 wave templates + 2 paid-finale templates.
TEMPLATE_DIRS = [
    "templates/july/day-1",
    "templates/july/day-3",
    "templates/july/day-5",
    "templates/july/day-7",
    "templates/july/day-9",
    "templates/july/day-10",
    "templates/july/finale-1",
    "templates/july/finale-2",
]

THROTTLE_SECONDS = 0.25  # stay under the 5 req/s team rate limit


def send_test(template_dir, to_email):
    """Sends one template to to_email via the transactional /emails endpoint."""
    html, text, subject, name = load_template(template_dir)
    if not subject:
        print(f"   ❌ No 'Subject:' in {template_dir}/metadata.txt — skipping.")
        return False

    payload = {
        "from": FROM,
        "to": [to_email],
        "subject": f"[TEST] {subject}",
        "html": html,
    }
    if text:
        payload["text"] = text

    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(f"{API_BASE}/emails", headers=headers, json=payload, timeout=30)
    except requests.exceptions.RequestException as e:
        print(f"   ❌ {template_dir}: network error: {e}")
        return False

    if 200 <= resp.status_code < 300:
        print(f"   ✅ {template_dir.split('/')[-1]:<7} → {to_email}  (\"{subject}\")  id={resp.json().get('id')}")
        return True
    print(f"   ❌ {template_dir}: {resp.status_code} {resp.text[:200]}")
    return False


def main():
    if not RESEND_API_KEY:
        print("❌ RESEND_API_KEY missing in environment.")
        sys.exit(1)

    args = sys.argv[1:]
    if not args:
        print("Usage: python preview.py you@example.com [day-1 day-7 ...]")
        sys.exit(1)

    to_email = args[0]
    wanted = args[1:]
    dirs = TEMPLATE_DIRS
    if wanted:
        dirs = [d for d in TEMPLATE_DIRS if d.split("/")[-1] in wanted]
        if not dirs:
            print(f"❌ None of {wanted} matched a known template. Options: "
                  f"{[d.split('/')[-1] for d in TEMPLATE_DIRS]}")
            sys.exit(1)

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
