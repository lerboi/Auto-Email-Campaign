import csv
import os
import re
from email_validator import validate_email, EmailNotValidError

# Configuration
EMAIL_FOLDER = "email"

# --- DISPOSABLE / TEMPORARY EMAIL DOMAINS ---
DISPOSABLE_DOMAINS = {
    "guerrillamail.com", "guerrillamail.net", "guerrillamail.org",
    "tempmail.com", "temp-mail.org", "temp-mail.io",
    "yopmail.com", "yopmail.fr",
    "mailinator.com", "maildrop.cc", "dispostable.com",
    "throwaway.email", "throwaway.cc",
    "fakeinbox.com", "sharklasers.com", "guerrillamailblock.com",
    "grr.la", "trashmail.com", "trashmail.net", "trashmail.me",
    "10minutemail.com", "10minute.email",
    "minutemail.com", "tempinbox.com",
    "mohmal.com", "burnermail.io",
    "mailnesia.com", "mailnator.com",
    "getnada.com", "nada.email",
    "emailondeck.com", "33mail.com",
    "discard.email", "discardmail.com",
    "tmail.ws", "tmpmail.net", "tmpmail.org",
    "crazymailing.com", "mytemp.email",
    "mailcatch.com", "inboxbear.com",
    "spamgourmet.com", "tempr.email",
    "emailfake.com", "generator.email",
    "harakirimail.com", "dropmail.me",
}

# --- ROLE-BASED PREFIXES (not real users) ---
ROLE_PREFIXES = {
    "info", "admin", "support", "contact", "help",
    "sales", "billing", "noreply", "no-reply", "no.reply",
    "postmaster", "webmaster", "hostmaster", "abuse",
    "marketing", "newsletter", "office", "hello",
    "team", "hr", "press", "media", "service",
}

# --- SUSPICIOUS TLDs ---
SPAM_TLDS = {
    ".xyz", ".top", ".click", ".buzz", ".gdn",
    ".bid", ".win", ".loan", ".racing", ".review",
    ".stream", ".party", ".trade", ".webcam", ".download",
    ".cricket", ".science", ".accountant", ".faith", ".date",
    ".icu", ".monster", ".surf", ".rest", ".casa",
}

def normalize_gmail(email):
    """Normalizes Gmail addresses by removing dots and plus-aliases."""
    local, domain = email.lower().split("@")
    if domain in ("gmail.com", "googlemail.com"):
        local = local.split("+")[0].replace(".", "")
    return f"{local}@{domain}"

def is_gibberish(username):
    """Detects keyboard-mash / random-string usernames."""
    # Strip digits to analyze letter patterns
    letters = re.sub(r'[^a-zA-Z]', '', username)
    if len(letters) < 3:
        return False  # Too short to judge consonant ratio

    consonants = sum(1 for c in letters.lower() if c in 'bcdfghjklmnpqrstvwxyz')
    consonant_ratio = consonants / len(letters)

    # Flag if almost all consonants (e.g. "xkjhqzwd")
    if consonant_ratio > 0.85 and len(letters) >= 6:
        return True

    # Flag long runs of consonants without vowels (5+)
    if re.search(r'[bcdfghjklmnpqrstvwxyz]{5,}', letters.lower()):
        return True

    return False

def normalize_and_validate(email):
    """
    Performs deliverability checks and multi-layer bot/spam filtering.
    Returns (is_valid, reason_string).
    """
    email = email.lower().strip()

    # 1. Standard Validation (Syntax & MX records)
    try:
        validate_email(email, check_deliverability=True)
    except EmailNotValidError:
        return False, "invalid"

    username, domain = email.split("@")

    # 2. Disposable / temporary email domain
    if domain in DISPOSABLE_DOMAINS:
        return False, "disposable_domain"

    # 3. Suspicious TLD
    if any(domain.endswith(tld) for tld in SPAM_TLDS):
        return False, "spam_tld"

    # 4. Role-based address
    if username in ROLE_PREFIXES:
        return False, "role_address"

    # 5. Plus-alias (bot farming)
    if "+" in username:
        return False, "bot_pattern"

    # 6. Excessive dots (>3)
    if username.count(".") > 3:
        return False, "bot_pattern"

    # 7. Very short username (1-2 chars)
    if len(username) <= 2:
        return False, "too_short"

    # 8. Excessive digits (>60% of username is digits)
    digit_count = sum(1 for c in username if c.isdigit())
    if len(username) >= 5 and digit_count / len(username) > 0.6:
        return False, "digit_heavy"

    # 9. Gibberish / keyboard-mash detection
    if is_gibberish(username):
        return False, "gibberish"

    return True, "valid"

def scrub_csv(filename):
    input_path = os.path.join(EMAIL_FOLDER, filename)
    output_path = os.path.join(EMAIL_FOLDER, f"CLEANED_{filename}")

    stats = {
        "valid": 0,
        "invalid": 0,
        "disposable_domain": 0,
        "spam_tld": 0,
        "role_address": 0,
        "bot_pattern": 0,
        "too_short": 0,
        "digit_heavy": 0,
        "gibberish": 0,
        "duplicate": 0,
    }
    cleaned_data = []
    seen_normalized = set()

    print(f"\n🔍 Starting scrub for: {filename}...")

    with open(input_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames

        # Case-insensitive check for 'email' column
        email_key = next((h for h in fieldnames if h.lower() == 'email'), None)

        if not email_key:
            print(f"❌ Error: Could not find 'email' column in {filename}.")
            return

        for row in reader:
            email = row.get(email_key, "").strip()
            if not email:
                continue

            is_valid, status = normalize_and_validate(email)

            if not is_valid:
                stats[status] = stats.get(status, 0) + 1
                continue

            # Deduplicate via Gmail normalization
            norm = normalize_gmail(email)
            if norm in seen_normalized:
                stats["duplicate"] += 1
                continue
            seen_normalized.add(norm)

            cleaned_data.append(row)
            stats["valid"] += 1

    # Save the cleaned results
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cleaned_data)

    total_removed = sum(v for k, v in stats.items() if k != "valid")
    print(f"✅ Finished {filename}:")
    print(f"   ✓ Valid kept:              {stats['valid']}")
    print(f"   ✗ Invalid (syntax/MX):     {stats['invalid']}")
    print(f"   ✗ Disposable domains:      {stats['disposable_domain']}")
    print(f"   ✗ Spam TLDs:               {stats['spam_tld']}")
    print(f"   ✗ Role addresses:          {stats['role_address']}")
    print(f"   ✗ Bot patterns (+/dots):   {stats['bot_pattern']}")
    print(f"   ✗ Too short (<3 chars):    {stats['too_short']}")
    print(f"   ✗ Digit-heavy:             {stats['digit_heavy']}")
    print(f"   ✗ Gibberish:               {stats['gibberish']}")
    print(f"   ✗ Duplicates (Gmail norm): {stats['duplicate']}")
    print(f"   — Total removed:           {total_removed}")
    print(f"   💾 Saved to: {output_path}")

def main():
    if not os.path.exists(EMAIL_FOLDER):
        print(f"❌ Error: Folder '{EMAIL_FOLDER}' not found.")
        return

    # 1. List files in the 'email' folder
    files = [f for f in os.listdir(EMAIL_FOLDER) if f.endswith('.csv') and not f.startswith('CLEANED_')]
    
    if not files:
        print("⚠️ No CSV files found in the 'email' folder.")
        return

    print("\n--- Available Email Lists ---")
    for i, file in enumerate(files, 1):
        print(f"{i}. {file}")

    # 2. Ask user to select files
    try:
        selection = input("\nEnter the numbers of the files to clean (separated by commas, e.g., 1,3): ")
        selected_indices = [int(x.strip()) - 1 for x in selection.split(',')]
        
        selected_files = [files[i] for i in selected_indices if 0 <= i < len(files)]
        
        if not selected_files:
            print("❌ Invalid selection. Exiting.")
            return

        print(f"\n🚀 Preparing to clean: {', '.join(selected_files)}")
        
        # 3. Process selected files
        for file in selected_files:
            scrub_csv(file)
            
    except ValueError:
        print("❌ Error: Please enter valid numbers separated by commas.")

if __name__ == "__main__":
    main()