import csv
import os
import requests
import sys
from datetime import datetime
from dotenv import load_dotenv

# --- CONFIGURATION ---
load_dotenv()
SERVER_TOKEN = os.getenv("POSTMARK_SERVER_TOKEN")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "contact@mail.anione.me")
MESSAGE_STREAM = "monthly-campaign"

# Folder where CSVs are stored
EMAIL_FOLDER = "email"

# Updated User Bases (Paths inside /email folder)
FREE_JULY_APRIL = os.path.join(EMAIL_FOLDER, "July+April_freeUsers_CLEANED.csv")
FREE_APR2026 = os.path.join(EMAIL_FOLDER, "Apr2026_freeUsers_CLEANED.csv")
PAID_NO_PKG = os.path.join(EMAIL_FOLDER, "paidNoPackage_April.csv")

# Alternating Groups
GROUP_A = [FREE_JULY_APRIL, PAID_NO_PKG]
GROUP_B = [FREE_APR2026]

# --- MAY CAMPAIGN MAPPING ---
# Logic: Map the current date to the Template Alias and specific CSV paths
# Template aliases sourced from templates/may/day-*/metadata.txt
CAMPAIGN_MAP = {
    "2026-05-02": {"template": "may-gift-day-1", "lists": GROUP_A},
    "2026-05-03": {"template": "may-gift-day-1", "lists": GROUP_B},
    "2026-05-04": {"template": "may-voice-nights-day-3", "lists": GROUP_A},
    "2026-05-05": {"template": "may-voice-nights-day-3", "lists": GROUP_B},
    "2026-05-06": {"template": "may-voice-deep-day-5", "lists": GROUP_A},
    "2026-05-07": {"template": "may-voice-deep-day-5", "lists": GROUP_B},
    "2026-05-08": {"template": "may-sale-day-7", "lists": GROUP_A},
    "2026-05-09": {"template": "may-sale-day-7", "lists": GROUP_B},
    "2026-05-10": {"template": "may-multiplier-day-9", "lists": GROUP_A},
    "2026-05-11": {"template": "may-multiplier-day-9", "lists": GROUP_B},
    "2026-05-12": {"template": "may-urgency-final-day-10", "lists": GROUP_A},
    "2026-05-13": {"template": "may-urgency-final-day-10", "lists": GROUP_B},
}

def load_emails(filenames):
    """Loads and de-duplicates emails from a list of CSV files in the /email folder."""
    emails = set()
    for filename in filenames:
        if not os.path.exists(filename):
            print(f"⚠️ Warning: File '{filename}' not found. Skipping.")
            continue
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                email = row.get("email")
                if email:
                    emails.add(email.strip())
    return list(emails)

def send_batch(email_list, template_alias):
    """Sends emails in batches of 500 using Postmark batchWithTemplates."""
    url = "https://api.postmarkapp.com/email/batchWithTemplates"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Postmark-Server-Token": SERVER_TOKEN
    }
    
    batch_size = 500
    total_sent = 0
    
    for i in range(0, len(email_list), batch_size):
        chunk = email_list[i:i + batch_size]
        messages_payload = []
        
        for email in chunk:
            messages_payload.append({
                "From": SENDER_EMAIL,
                "To": email,
                "TemplateAlias": template_alias,
                "TemplateModel": {}, 
                "MessageStream": MESSAGE_STREAM
            })
        
        payload = {"Messages": messages_payload}
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                total_sent += len(chunk)
                print(f"   ✅ Sent batch of {len(chunk)} emails. (Total: {total_sent})")
            else:
                print(f"   ❌ API Error {response.status_code}: {response.text}")
        except Exception as e:
            print(f"   ❌ Network Error: {e}")
            
    return total_sent

def main():
    if not SERVER_TOKEN:
        print("❌ Error: POSTMARK_SERVER_TOKEN missing in environment.")
        sys.exit(1)

    # Use Today's Date (Format: YYYY-MM-DD)
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"📅 Current Date detected: {today}")

    config = CAMPAIGN_MAP.get(today)
    
    if not config:
        print("🛑 No campaign scheduled for today. Exiting.")
        return

    print(f"🚀 Launching Monthly Campaign Day: {today} | Template: {config['template']}")
    email_list = load_emails(config['lists'])
    
    if not email_list:
        print("⚠️ No emails found for today's target lists.")
        return

    print(f"📧 Targeting {len(email_list)} unique users from subfolder: /{EMAIL_FOLDER}")
    count = send_batch(email_list, config['template'])
    print(f"✅ Mission Accomplished. {count} emails delivered.")

if __name__ == "__main__":
    main()