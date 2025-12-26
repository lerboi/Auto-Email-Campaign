import csv
import time
import sys
import os
import argparse
import requests # Using requests directly to avoid library conflicts
import json
from dotenv import load_dotenv

# --- CONFIGURATION ---
load_dotenv()
SERVER_TOKEN = os.getenv("POSTMARK_SERVER_TOKEN")
SENDER_EMAIL = "contact@mail.anione.me" # Ensure this matches your confirmed Sender Signature

# Map Day Numbers to Template Aliases
TEMPLATE_MAP = {
    1: "xmas-day-1",
    2: "xmas-day-2",
    3: "xmas-day-3",
    4: "xmas-day-4",
    5: "xmas-day-5",
    6: "xmas-day-6",
    7: "xmas-day-7"
}

# Which days do we SKIP the Cold List?
COLD_LIST_SKIP_DAYS = [] 

if not SERVER_TOKEN:
    print("❌ Error: POSTMARK_SERVER_TOKEN not found in .env")
    sys.exit(1)

def load_emails(filename):
    emails = []
    # Check if file exists in the current directory
    if not os.path.exists(filename):
        print(f"❌ Error: File '{filename}' not found.")
        print("   Make sure the .csv file is in the same folder as this script.")
        return []
        
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("Email"):
                emails.append(row["Email"])
    return emails

def send_batch(email_list, template_alias):
    """Sends emails in batches of 500 using the Postmark API directly"""
    url = "https://api.postmarkapp.com/email/batchWithTemplates"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Postmark-Server-Token": SERVER_TOKEN
    }
    
    batch_size = 500
    total_sent = 0
    
    # Break list into chunks of 500
    for i in range(0, len(email_list), batch_size):
        chunk = email_list[i:i + batch_size]
        
        messages_payload = []
        for email in chunk:
            messages_payload.append({
                "From": SENDER_EMAIL,
                "To": email,
                "TemplateAlias": template_alias,
                "TemplateModel": {}, 
                "MessageStream": "christmas-campaign"
            })
        
        # Wrap in the required "Messages" key
        payload = {"Messages": messages_payload}
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                total_sent += len(chunk)
                print(f"   ✅ Sent batch of {len(chunk)} emails... (Total: {total_sent})")
            else:
                print(f"   ❌ API Error {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Network Error sending batch: {e}")
            
    return total_sent

def run_campaign(day):
    template_alias = TEMPLATE_MAP.get(day)
    if not template_alias:
        print(f"❌ Error: No template defined for Day {day}")
        return

    print(f"\n🎄 STARTING CAMPAIGN: DAY {day}")
    print(f"📧 Using Template: {template_alias}")
    
    # --- PHASE 1: VIP LIST ---
    print("\n👑 Phase 1: Sending to VIP List...")
    vip_emails = load_emails("postmark_opened_users.csv")
    
    if not vip_emails:
        print("⚠️ VIP List empty or skipped.")
    else:
        count = send_batch(vip_emails, template_alias)
        print(f"✨ Phase 1 Complete. {count} VIPs emailed.")

    # Check if we skip cold list today
    if day in COLD_LIST_SKIP_DAYS:
        print(f"\n🛑 Strategy Alert: Day {day} is VIP ONLY. Skipping Cold List.")
        return

    # --- PHASE 2: WARM UP WAIT ---
    wait_minutes = 90
    print(f"\n☕ Phase 2: Trojan Horse Wait ({wait_minutes} Minutes)")
    print("   Do not close this window. Using VIP engagement to warm up IP...")
    
    try:
        for remaining in range(wait_minutes * 60, 0, -1):
            mins, secs = divmod(remaining, 60)
            sys.stdout.write(f"\r   ⏳ Waiting... {mins:02d}:{secs:02d} remaining   ")
            sys.stdout.flush()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Wait skipped by user! Proceeding to Cold List...")

    print("\n\n   🚀 Wait complete. Engaging Cold List.")

    # --- PHASE 3: COLD LIST ---
    print("\n❄️ Phase 3: Sending to Cold List...")
    cold_emails = load_emails("cleaned_cold_list.csv")
    
    if not cold_emails:
        print("⚠️ Cold List empty or skipped.")
    else:
        count = send_batch(cold_emails, template_alias)
        print(f"🎉 Phase 3 Complete. {count} Cold users emailed.")
    
    print(f"\n✅ DAY {day} MISSION ACCOMPLISHED.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--day", type=int, help="Which day of the campaign to run (1-7)", required=True)
    args = parser.parse_args()
    
    confirm = input(f"⚠️ Are you sure you want to blast DAY {args.day}? (type 'yes'): ")
    if confirm.lower() == "yes":
        run_campaign(args.day)
    else:
        print("Aborted.")