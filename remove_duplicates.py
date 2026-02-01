import csv
import os

# Configuration
INPUT_FILE = "email/all_paid_users.csv"  # Change to your filename
OUTPUT_FILE = "email/DEDUPLICATED_all_paid_users.csv"

def normalize_email(email):
    """
    Standardizes email for comparison. 
    Removes dots and plus-aliases for Gmail/Googlemail.
    """
    email = email.lower().strip()
    if not email or "@" not in email:
        return email
    
    local, domain = email.split("@")
    
    if domain in ["gmail.com", "googlemail.com"]:
        # 1. Remove everything after '+'
        local = local.split("+")[0]
        # 2. Remove all '.'
        local = local.replace(".", "")
        
    return f"{local}@{domain}"

def deduplicate():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Error: {INPUT_FILE} not found.")
        return

    seen_normalized = set()
    unique_rows = []
    duplicate_count = 0

    print(f"🚀 Processing {INPUT_FILE}...")

    with open(INPUT_FILE, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        
        # Find the email column (case-insensitive)
        email_key = next((h for h in headers if h.lower() == 'email'), None)
        
        if not email_key:
            print(f"❌ Error: Could not find 'email' column. Headers: {headers}")
            return

        for row in reader:
            raw_email = row[email_key]
            normalized = normalize_email(raw_email)
            
            if normalized not in seen_normalized:
                seen_normalized.add(normalized)
                unique_rows.append(row)
            else:
                duplicate_count += 1

    # Save the unique results
    with open(OUTPUT_FILE, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(unique_rows)

    print(f"✅ Success!")
    print(f"   - Total unique users kept: {len(unique_rows)}")
    print(f"   - Duplicates removed: {duplicate_count}")
    print(f"   - Saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    deduplicate()