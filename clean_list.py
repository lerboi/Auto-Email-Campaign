import csv
import os

from clean_tools.remove_duplicates import normalize_email
from clean_tools.scrub_lists import normalize_and_validate

EMAIL_FOLDER = "email"


def list_csv_files():
    return sorted(
        f for f in os.listdir(EMAIL_FOLDER)
        if f.lower().endswith(".csv")
        and not f.startswith("CLEANED_")
        and not f.lower().endswith("_cleaned.csv")
    )


def pick_file(files):
    print("\n--- Available Email Lists ---")
    for i, name in enumerate(files, 1):
        print(f"{i}. {name}")
    raw = input("\nEnter the number of the file to clean: ").strip()
    try:
        idx = int(raw) - 1
    except ValueError:
        return None
    if idx < 0 or idx >= len(files):
        return None
    return files[idx]


def deduplicate(rows, email_key):
    seen = set()
    unique = []
    dupes = 0
    for row in rows:
        email = (row.get(email_key) or "").strip()
        if not email:
            continue
        norm = normalize_email(email)
        if norm in seen:
            dupes += 1
            continue
        seen.add(norm)
        unique.append(row)
    return unique, dupes


def scrub(rows, email_key):
    kept = []
    stats = {}
    for row in rows:
        email = (row.get(email_key) or "").strip()
        is_valid, status = normalize_and_validate(email)
        if is_valid:
            kept.append(row)
        stats[status] = stats.get(status, 0) + 1
    return kept, stats


def process(filename):
    input_path = os.path.join(EMAIL_FOLDER, filename)
    base, ext = os.path.splitext(filename)
    output_path = os.path.join(EMAIL_FOLDER, f"{base}_CLEANED{ext}")

    print(f"\n🚀 Processing {filename}...")

    with open(input_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        email_key = next((h for h in fieldnames if h.lower() == "email"), None)
        if not email_key:
            print(f"❌ Could not find 'email' column. Headers: {fieldnames}")
            return
        rows = list(reader)

    original = len(rows)
    print(f"   📥 Loaded {original} rows.")

    print("   🔁 Step 1/2: Removing duplicates (Gmail-normalized)...")
    deduped, dupes = deduplicate(rows, email_key)
    print(f"      - Duplicates removed: {dupes}")
    print(f"      - Remaining: {len(deduped)}")

    print("   🧼 Step 2/2: Scrubbing (syntax, MX, bots, disposable, role, gibberish)...")
    cleaned, stats = scrub(deduped, email_key)
    print(f"      ✓ Valid kept:              {stats.get('valid', 0)}")
    print(f"      ✗ Invalid (syntax/MX):     {stats.get('invalid', 0)}")
    print(f"      ✗ Disposable domains:      {stats.get('disposable_domain', 0)}")
    print(f"      ✗ Spam TLDs:               {stats.get('spam_tld', 0)}")
    print(f"      ✗ Role addresses:          {stats.get('role_address', 0)}")
    print(f"      ✗ Bot patterns (+/dots):   {stats.get('bot_pattern', 0)}")
    print(f"      ✗ Too short (<3 chars):    {stats.get('too_short', 0)}")
    print(f"      ✗ Gibberish:               {stats.get('gibberish', 0)}")

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cleaned)

    total_removed = original - len(cleaned)
    print(f"\n✅ Done. {original} → {len(cleaned)} rows.")
    print(f"   🗑️  Total removed: {total_removed}")
    print(f"   💾 Saved to: {output_path}")


def main():
    if not os.path.isdir(EMAIL_FOLDER):
        print(f"❌ Folder '{EMAIL_FOLDER}' not found.")
        return

    files = list_csv_files()
    if not files:
        print(f"⚠️ No CSV files found in '{EMAIL_FOLDER}'.")
        return

    choice = pick_file(files)
    if not choice:
        print("❌ Invalid selection. Exiting.")
        return

    process(choice)


if __name__ == "__main__":
    main()
