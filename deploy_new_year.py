import os
import re
import sys
import requests
from datetime import datetime
from dotenv import load_dotenv

# --- CONFIGURATION ---
load_dotenv()
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "contact@mail.anione.me")
SENDER_NAME = os.getenv("SENDER_NAME", "AniOne")
FROM = f"{SENDER_NAME} <{SENDER_EMAIL}>"

API_BASE = "https://api.resend.com"

# Folder where CSVs are stored. The CSVs remain the source of truth for the
# recipient lists; sync_contacts.py pushes them into the Resend segments below.
EMAIL_FOLDER = "email"

# Resend Segment IDs. Create them once with `python sync_contacts.py --create`,
# then set these in the environment (Railway + .env).
SEGMENT_A = os.getenv("RESEND_SEGMENT_A")
SEGMENT_B = os.getenv("RESEND_SEGMENT_B")

# Source CSVs for each segment (synced into Resend by sync_contacts.py).
GROUP_A_FILES = [
    os.path.join(EMAIL_FOLDER, "May2025_Free_CLEANED.csv"),
    os.path.join(EMAIL_FOLDER, "paidNoPackage_May.csv"),
]
GROUP_B_FILES = [
    os.path.join(EMAIL_FOLDER, "May2026_freeUsers_CLEANED.csv"),
]

# --- JULY CAMPAIGN MAPPING ---
# Map each send date to the local template folder + the Resend segment to send to.
# (Replaces Postmark's TemplateAlias + MessageStream. The HTML/subject are read
#  from disk and sent inline via a Resend Broadcast — no dashboard upload needed.)
CAMPAIGN_MAP = {
    "2026-07-01": {"template_dir": "templates/july/day-1",  "segment": SEGMENT_A},
    "2026-07-02": {"template_dir": "templates/july/day-1",  "segment": SEGMENT_B},
    "2026-07-03": {"template_dir": "templates/july/day-3",  "segment": SEGMENT_A},
    "2026-07-04": {"template_dir": "templates/july/day-3",  "segment": SEGMENT_B},
    "2026-07-05": {"template_dir": "templates/july/day-5",  "segment": SEGMENT_A},
    "2026-07-06": {"template_dir": "templates/july/day-5",  "segment": SEGMENT_B},
    "2026-07-07": {"template_dir": "templates/july/day-7",  "segment": SEGMENT_A},
    "2026-07-08": {"template_dir": "templates/july/day-7",  "segment": SEGMENT_B},
    "2026-07-09": {"template_dir": "templates/july/day-9",  "segment": SEGMENT_A},
    "2026-07-10": {"template_dir": "templates/july/day-9",  "segment": SEGMENT_B},
    "2026-07-11": {"template_dir": "templates/july/day-10", "segment": SEGMENT_A},
    "2026-07-12": {"template_dir": "templates/july/day-10", "segment": SEGMENT_B},
}


def load_template(template_dir):
    """Reads the local HTML body, plain-text body, Subject, and Name for a day."""
    html_path = os.path.join(template_dir, "template.html")
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    text = None
    text_path = os.path.join(template_dir, "template.txt")
    if os.path.exists(text_path):
        with open(text_path, "r", encoding="utf-8") as f:
            text = f.read()

    subject = name = None
    with open(os.path.join(template_dir, "metadata.txt"), "r", encoding="utf-8") as f:
        meta = f.read()
    m = re.search(r"^Subject:\s*(.+)$", meta, re.MULTILINE)
    if m:
        subject = m.group(1).strip()
    m = re.search(r"^Name:\s*(.+)$", meta, re.MULTILINE)
    if m:
        name = m.group(1).strip()

    return html, text, subject, name


def send_broadcast(template_dir, segment_id):
    """Creates and sends a Resend Broadcast to a segment using the local template."""
    html, text, subject, name = load_template(template_dir)

    if not subject:
        print(f"   ❌ No 'Subject:' found in {template_dir}/metadata.txt")
        return False

    payload = {
        "segment_id": segment_id,
        "from": FROM,
        "subject": subject,
        "name": name or template_dir,
        "html": html,          # footer contains {{{RESEND_UNSUBSCRIBE_URL}}}
        "send": True,          # create AND send in a single request
    }
    if text:
        payload["text"] = text

    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(f"{API_BASE}/broadcasts", headers=headers, json=payload)
        if 200 <= response.status_code < 300:
            print(f"   ✅ Broadcast created & sent. ID: {response.json().get('id')}")
            return True
        print(f"   ❌ API Error {response.status_code}: {response.text}")
        return False
    except Exception as e:
        print(f"   ❌ Network Error: {e}")
        return False


def main():
    if not RESEND_API_KEY:
        print("❌ Error: RESEND_API_KEY missing in environment.")
        sys.exit(1)

    # Use Today's Date (Format: YYYY-MM-DD)
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"📅 Current Date detected: {today}")

    config = CAMPAIGN_MAP.get(today)
    if not config:
        print("🛑 No campaign scheduled for today. Exiting.")
        return

    segment_id = config["segment"]
    if not segment_id:
        print("❌ Error: Segment ID for today's group is not set (RESEND_SEGMENT_A/B).")
        sys.exit(1)

    print(f"🚀 Launching Monthly Campaign Day: {today} | Template: {config['template_dir']}")
    print(f"📧 Sending broadcast to segment: {segment_id}")

    if send_broadcast(config["template_dir"], segment_id):
        print("✅ Mission Accomplished. Broadcast dispatched to Resend.")
    else:
        print("⚠️ Broadcast failed — see error above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
