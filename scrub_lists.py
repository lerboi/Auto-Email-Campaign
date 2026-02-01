import csv
import os
from email_validator import validate_email, EmailNotValidError

# Configuration
EMAIL_FOLDER = "email"

def normalize_and_validate(email):
    """
    Performs deliverability checks and bot-pattern filtering.
    """
    try:
        # 1. Standard Validation (Syntax & MX records)
        validate_email(email, check_deliverability=True)
        
        # 2. Bot Filtering Logic (Username portion)
        username = email.split('@')[0]

        # REMOVE if email has a '+' or more than 3 dots '.'
        if "+" in username or username.count(".") > 3:
            return False, "bot_pattern"

        return True, "valid"
    except EmailNotValidError:
        return False, "invalid"

def scrub_csv(filename):
    input_path = os.path.join(EMAIL_FOLDER, filename)
    output_path = os.path.join(EMAIL_FOLDER, f"CLEANED_{filename}")
    
    valid_count = 0
    invalid_count = 0
    farm_bot_count = 0
    cleaned_data = []

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
            
            if is_valid:
                cleaned_data.append(row)
                valid_count += 1
            elif status == "bot_pattern":
                farm_bot_count += 1
            else:
                invalid_count += 1

    # Save the cleaned results
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cleaned_data)

    print(f"✅ Finished {filename}:")
    print(f"   - Valid: {valid_count}")
    print(f"   - Removed (Invalid): {invalid_count}")
    print(f"   - Removed (Bot/Farming Pattern): {farm_bot_count}")
    print(f"   - Saved to: {output_path}")

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