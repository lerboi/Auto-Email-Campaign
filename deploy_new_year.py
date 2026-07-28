import os
import re
import sys
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

# Force UTF-8 stdout so emoji status lines don't crash on Windows (cp1252) consoles.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

# --- CONFIGURATION ---
load_dotenv()
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "contact@mail.anione.me")
SENDER_NAME = os.getenv("SENDER_NAME", "Anione")
FROM = f"{SENDER_NAME} <{SENDER_EMAIL}>"

API_BASE = "https://api.resend.com"

# Folder where CSVs are stored. The CSVs remain the source of truth for the
# recipient lists; sync_contacts.py pushes them into the Resend segments below.
EMAIL_FOLDER = "email"

# Resend Segment IDs. Create them once with `python sync_contacts.py --create`,
# then set these in the environment (Railway + .env). On the $80/10k marketing
# tier ALL FIVE segments are loaded at once (~9k contacts) — no list rotation and
# no clearing between phases.
SEGMENT_A = os.getenv("RESEND_SEGMENT_A")  # Wave 1 free (A) + paid (ride-along)
SEGMENT_B = os.getenv("RESEND_SEGMENT_B")  # Wave 1 free (B)
SEGMENT_C = os.getenv("RESEND_SEGMENT_C")  # Wave 2 free (C)
SEGMENT_D = os.getenv("RESEND_SEGMENT_D")  # Wave 2 free (D)
SEGMENT_E = os.getenv("RESEND_SEGMENT_E")  # Paid finale (E)

# Source CSVs for each segment (synced into Resend by sync_contacts.py). All five
# are synced once up-front; the campaign just sends to the right segment per day.
# Provide each CSV (column `email`) exported filtered to opted-in users
# (newsletter = true). Paid users (E) appear in BOTH Segment A (Wave 1 main) and
# Segment E (finale) — that's one contact in two segments, billed once.
GROUP_A_FILES = [
    os.path.join(EMAIL_FOLDER, "July2025_Free_CLEANED.csv"),  # free A (~1878, smallest — paired with paid)
    os.path.join(EMAIL_FOLDER, "Paid_CLEANED.csv"),           # paid (E) rides Wave 1
]
GROUP_B_FILES = [
    os.path.join(EMAIL_FOLDER, "Feb2026_Free_CLEANED.csv"),  # free B (~2739)
]
GROUP_C_FILES = [
    os.path.join(EMAIL_FOLDER, "July2026_Free_CLEANED.csv"),  # free C (~2285, Wave 2)
]
GROUP_D_FILES = [
    os.path.join(EMAIL_FOLDER, "Sept2025_Free_CLEANED.csv"),  # free D (~2417, Wave 2)
]
GROUP_E_FILES = [
    os.path.join(EMAIL_FOLDER, "Paid_CLEANED.csv"),  # paid (finale + Wave 1 ride-along)
]

# --- JULY CAMPAIGN MAPPING ($80/10k tier: all segments pre-loaded, no resets) ---
# Map each send date to the local template folder + the Resend segment to send to.
# Two free waves (A/B then C/D, A->B alternating to spread volume) reach all four
# free lists, with paid users riding Wave 1 (Seg A) and getting a 2-day finale.
CAMPAIGN_MAP = {
    # ---- WAVE 1 (Jul 1-12): free A/B + paid, A->B alternating ----
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

    # ---- WAVE 2 (Jul 13-24): free C/D, C->D alternating ----
    # On Jul 13/17/21 a SECOND send goes out: a paid token-drop to Segment E (a
    # date can map to a LIST of sends; main() dispatches each).
    "2026-07-13": [{"template_dir": "templates/july/day-1",  "segment": SEGMENT_C},
                   {"template_dir": "templates/july/drop-1", "segment": SEGMENT_E}],  # + paid token drop (20 img)
    "2026-07-14": {"template_dir": "templates/july/day-1",  "segment": SEGMENT_D},
    "2026-07-15": {"template_dir": "templates/july/day-3",  "segment": SEGMENT_C},
    "2026-07-16": {"template_dir": "templates/july/day-3",  "segment": SEGMENT_D},
    "2026-07-17": [{"template_dir": "templates/july/day-5",  "segment": SEGMENT_C},
                   {"template_dir": "templates/july/drop-2", "segment": SEGMENT_E}],  # + paid token drop (20 img)
    "2026-07-18": {"template_dir": "templates/july/day-5",  "segment": SEGMENT_D},
    "2026-07-19": {"template_dir": "templates/july/day-7",  "segment": SEGMENT_C},
    "2026-07-20": {"template_dir": "templates/july/day-7",  "segment": SEGMENT_D},
    "2026-07-21": [{"template_dir": "templates/july/day-9",  "segment": SEGMENT_C},
                   {"template_dir": "templates/july/drop-3", "segment": SEGMENT_E}],  # + paid token drop (20 img)
    "2026-07-22": {"template_dir": "templates/july/day-9",  "segment": SEGMENT_D},
    "2026-07-23": {"template_dir": "templates/july/day-10", "segment": SEGMENT_C},
    "2026-07-24": {"template_dir": "templates/july/day-10", "segment": SEGMENT_D},

    # ---- PAID FINALE (Jul 25-26): Seg E only, dedicated finale templates ----
    "2026-07-25": {"template_dir": "templates/july/finale-1", "segment": SEGMENT_E},  # premium 30-token gift
    "2026-07-26": {"template_dir": "templates/july/finale-2", "segment": SEGMENT_E},  # final 20% off

    # ================= AUGUST CAMPAIGN (2026-08) =================
    # Same 5-segment design: two free waves (A/B then C/D) + paid drops (Aug 13/17/21)
    # + paid finale (Aug 25-26). Segments A-E are reused; re-sync the August contact
    # lists into them with `python sync_contacts.py --fresh` AFTER the Jul 25-26 finale
    # fires (a --fresh sync wipes all contacts, including the paid finale audience).
    # ---- WAVE 1 (Aug 1-12): free A/B + paid, A->B alternating ----
    "2026-08-01": {"template_dir": "templates/august/day-1",  "segment": SEGMENT_A},
    "2026-08-02": {"template_dir": "templates/august/day-1",  "segment": SEGMENT_B},
    "2026-08-03": {"template_dir": "templates/august/day-3",  "segment": SEGMENT_A},
    "2026-08-04": {"template_dir": "templates/august/day-3",  "segment": SEGMENT_B},
    "2026-08-05": {"template_dir": "templates/august/day-5",  "segment": SEGMENT_A},
    "2026-08-06": {"template_dir": "templates/august/day-5",  "segment": SEGMENT_B},
    "2026-08-07": {"template_dir": "templates/august/day-7",  "segment": SEGMENT_A},
    "2026-08-08": {"template_dir": "templates/august/day-7",  "segment": SEGMENT_B},
    "2026-08-09": {"template_dir": "templates/august/day-9",  "segment": SEGMENT_A},
    "2026-08-10": {"template_dir": "templates/august/day-9",  "segment": SEGMENT_B},
    "2026-08-11": {"template_dir": "templates/august/day-10", "segment": SEGMENT_A},
    "2026-08-12": {"template_dir": "templates/august/day-10", "segment": SEGMENT_B},

    # ---- WAVE 2 (Aug 13-24): free C/D, C->D alternating; paid drops on 13/17/21 to E ----
    "2026-08-13": [{"template_dir": "templates/august/day-1",  "segment": SEGMENT_C},
                   {"template_dir": "templates/august/drop-1", "segment": SEGMENT_E}],  # + paid token drop (20 img)
    "2026-08-14": {"template_dir": "templates/august/day-1",  "segment": SEGMENT_D},
    "2026-08-15": {"template_dir": "templates/august/day-3",  "segment": SEGMENT_C},
    "2026-08-16": {"template_dir": "templates/august/day-3",  "segment": SEGMENT_D},
    "2026-08-17": [{"template_dir": "templates/august/day-5",  "segment": SEGMENT_C},
                   {"template_dir": "templates/august/drop-2", "segment": SEGMENT_E}],  # + paid token drop (20 img)
    "2026-08-18": {"template_dir": "templates/august/day-5",  "segment": SEGMENT_D},
    "2026-08-19": {"template_dir": "templates/august/day-7",  "segment": SEGMENT_C},
    "2026-08-20": {"template_dir": "templates/august/day-7",  "segment": SEGMENT_D},
    "2026-08-21": [{"template_dir": "templates/august/day-9",  "segment": SEGMENT_C},
                   {"template_dir": "templates/august/drop-3", "segment": SEGMENT_E}],  # + paid token drop (20 img)
    "2026-08-22": {"template_dir": "templates/august/day-9",  "segment": SEGMENT_D},
    "2026-08-23": {"template_dir": "templates/august/day-10", "segment": SEGMENT_C},
    "2026-08-24": {"template_dir": "templates/august/day-10", "segment": SEGMENT_D},

    # ---- PAID FINALE (Aug 25-26): Seg E only, dedicated finale templates ----
    "2026-08-25": {"template_dir": "templates/august/finale-1", "segment": SEGMENT_E},  # premium 30-token gift
    "2026-08-26": {"template_dir": "templates/august/finale-2", "segment": SEGMENT_E},  # final 20% off
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


def send_broadcast(template_dir, segment_id, today=""):
    """Creates and sends a Resend Broadcast to a segment using the local template."""
    html_path = os.path.join(template_dir, "template.html")
    meta_path = os.path.join(template_dir, "metadata.txt")
    if not (os.path.exists(html_path) and os.path.exists(meta_path)):
        print(f"   ❌ Template files missing in {template_dir} (need template.html + metadata.txt)")
        return False

    html, text, subject, name = load_template(template_dir)

    if not subject:
        print(f"   ❌ No 'Subject:' found in {template_dir}/metadata.txt")
        return False

    # Unique, human-readable broadcast name (same template goes to two segments on
    # consecutive days, so include the date to keep them distinct in the dashboard).
    base_name = name or os.path.basename(template_dir)
    payload = {
        "segment_id": segment_id,
        "from": FROM,
        "subject": subject,
        "name": f"{base_name} [{today}]" if today else base_name,
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

    # Use today's date in UTC to match the Railway cron (03:00 UTC) and the
    # UTC-keyed CAMPAIGN_MAP — a local-timezone container could otherwise resolve
    # 03:00 UTC to the wrong calendar date and send the wrong day's broadcast.
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"📅 Current Date detected (UTC): {today}")

    config = CAMPAIGN_MAP.get(today)
    if not config:
        print("🛑 No campaign scheduled for today. Exiting.")
        return

    # A date maps to one send (dict) or several (list of dicts, e.g. a Wave 2 free
    # send plus a paid token-drop on the same day).
    sends = config if isinstance(config, list) else [config]
    print(f"🚀 Monthly Campaign Day: {today} — {len(sends)} send(s) scheduled")

    all_ok = True
    for s in sends:
        segment_id = s["segment"]
        if not segment_id:
            print(f"❌ Segment ID not set for {s['template_dir']} (RESEND_SEGMENT_A/B/C/D/E).")
            all_ok = False
            continue
        print(f"📧 {s['template_dir']} → segment {segment_id}")
        if not send_broadcast(s["template_dir"], segment_id, today):
            all_ok = False

    if all_ok:
        print("✅ Mission Accomplished. All broadcasts dispatched to Resend.")
    else:
        print("⚠️ One or more broadcasts failed — see errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
