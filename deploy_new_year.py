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
MESSAGE_STREAM = "new-year-campaign"

# Folder where CSVs are stored
EMAIL_FOLDER = "email"

# Define Audience Groups (Paths updated to /email folder)
FREE_APRIL = os.path.join(EMAIL_FOLDER, "April_freeUsers.csv")
FREE_MAY = os.path.join(EMAIL_FOLDER, "May_freeUsers.csv")
FREE_JUNE = os.path.join(EMAIL_FOLDER, "June_freeUsers.csv")
FREE_JULY = os.path.join(EMAIL_FOLDER, "July_freeUsers.csv")
PAID_HIGH = [
    os.path.join(EMAIL_FOLDER, "paid_appRegisteredFALSE.csv"),
    os.path.join(EMAIL_FOLDER, "paidNoPackage.csv")
]

ALL_FREE = [FREE_APRIL, FREE_MAY, FREE_JUNE, FREE_JULY]
ALL_LISTS = ALL_FREE + PAID_HIGH

# --- CAMPAIGN MAPPING ---
# Logic: Map the current date to the Template Alias and specific CSV paths
CAMPAIGN_MAP = {
    "2025-12-29": {"template": "ny-gift-day-1", "lists": ALL_LISTS},
    "2025-12-30": {"template": "xmas-day-2", "lists": [FREE_MAY]},
    "2025-12-31": {"template": "xmas-day-2", "lists": [FREE_APRIL, FREE_JULY]},
    "2026-01-01": {"template": "nye-countdown-day-4", "lists": [FREE_JULY] + PAID_HIGH},
    "2026-01-02": {"template": "xmas-day-4", "lists": [FREE_APRIL, FREE_MAY]},
    "2026-01-03": {"template": "xmas-day-4", "lists": [FREE_JUNE, FREE_JULY]},
    "2026-01-04": {"template": "ny-gift-2-day-7", "lists": ALL_LISTS},
    "2026-01-05": {"template": "token-multiplier-day-8", "lists": [FREE_JUNE] + PAID_HIGH},
    "2026-01-06": {"template": "multiplier-urgency-day-9", "lists": PAID_HIGH},
    "2026-01-07": {"template": "final-call-day-10", "lists": [FREE_JULY] + PAID_HIGH},
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

    print(f"🚀 Launching Campaign Day: {today} | Template: {config['template']}")
    email_list = load_emails(config['lists'])
    
    if not email_list:
        print("⚠️ No emails found for today's target lists.")
        return

    print(f"📧 Targeting {len(email_list)} unique users from subfolder: /{EMAIL_FOLDER}")
    count = send_batch(email_list, config['template'])
    print(f"✅ Mission Accomplished. {count} emails delivered.")

if __name__ == "__main__":
    main()