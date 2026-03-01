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
FREE_OCT = os.path.join(EMAIL_FOLDER, "Feb2026-freeUsers.csv")
FREE_DEC = os.path.join(EMAIL_FOLDER, "June_freeUsers.csv")
PAID_NO_PKG = os.path.join(EMAIL_FOLDER, "paidNoPackage_new.csv")

# Alternating Groups to maintain ~2,600 sends/day
GROUP_A = [FREE_DEC, PAID_NO_PKG] # ~2,563 users
GROUP_B = [FREE_OCT]              # ~2,624 users

# --- MARCH CAMPAIGN MAPPING ---
# Logic: Map the current date to the Template Alias and specific CSV paths
CAMPAIGN_MAP = {
    "2026-03-02": {"template": "mar-gift-day-1", "lists": GROUP_A},
    "2026-03-03": {"template": "mar-gift-day-1", "lists": GROUP_B},
    "2026-03-04": {"template": "mar-custom-char-day-3", "lists": GROUP_A},
    "2026-03-05": {"template": "mar-custom-char-day-3", "lists": GROUP_B},
    "2026-03-06": {"template": "mar-custom-scenario-day-5", "lists": GROUP_A},
    "2026-03-07": {"template": "mar-custom-scenario-day-5", "lists": GROUP_B},
    "2026-03-08": {"template": "mar-sale-day-7", "lists": GROUP_A},
    "2026-03-09": {"template": "mar-sale-day-7", "lists": GROUP_B},
    "2026-03-10": {"template": "mar-multiplier-day-9", "lists": GROUP_A},
    "2026-03-11": {"template": "mar-multiplier-day-9", "lists": GROUP_B},
    "2026-03-12": {"template": "mar-urgency-final-day-8", "lists": GROUP_A},
    "2026-03-13": {"template": "mar-urgency-final-day-8", "lists": GROUP_B},
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