# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Automated email campaign system for **AniOne** (anione.me) that sends marketing emails via the **Postmark API** using template-based batch sending. Deployed on **Railway** as a daily cron job.

## Architecture

- **`deploy_new_year.py`** — Active campaign dispatcher (runs daily via Railway cron). Uses a date-keyed `CAMPAIGN_MAP` to determine which Postmark template and user lists to send for a given day. Alternates between GROUP_A and GROUP_B user segments (~2,600 users each) to stay within daily send limits.
- **`send_daily.py`** — Legacy multi-phase campaign script (Christmas campaign). Sends to VIP list first, waits 90 minutes for IP warmup, then sends to cold list. Run manually with `--day N` flag.
- **`scrub_lists.py`** — Interactive email list cleaner. Validates emails (syntax + MX records via `email_validator`), filters bot patterns (+ aliases, excessive dots). Reads from and writes `CLEANED_` prefixed files to `email/` folder.
- **`remove_duplicates.py`** — Deduplicates CSV email lists with Gmail normalization (dot/plus-alias handling). Hardcoded `INPUT_FILE`/`OUTPUT_FILE` paths must be edited per use.
- **`test.py`** — Scratch file for formatting raw email lists; not a test suite.
- **`email/`** — CSV files containing user email lists segmented by signup date and payment status. Column header is `email` (lowercase) in newer files.

## Key Configuration

- **Environment**: `POSTMARK_SERVER_TOKEN` in `.env` (loaded via `python-dotenv`)
- **Sender**: `contact@mail.anione.me`
- **Message streams**: `monthly-campaign` (current), `christmas-campaign` (legacy)
- **Batch size**: 500 emails per API call (Postmark limit)
- **Railway cron**: Runs `deploy_new_year.py` daily at 03:00 UTC (`railway.json`)

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the active daily campaign (normally triggered by Railway cron)
python deploy_new_year.py

# Run legacy campaign manually (requires interactive confirmation)
python send_daily.py --day 1

# Clean email lists (interactive file selector)
python scrub_lists.py

# Deduplicate emails (edit INPUT_FILE/OUTPUT_FILE in script first)
python remove_duplicates.py
```

## Important Patterns

- Campaign schedules are defined as hardcoded date-to-template maps in `CAMPAIGN_MAP` — update this dict for each new campaign period.
- User lists alternate between GROUP_A and GROUP_B on consecutive days to spread sends evenly.
- CSV email column is `email` (lowercase) in `deploy_new_year.py` and `scrub_lists.py`, but `Email` (capitalized) in the older `send_daily.py`. The scrub/dedup scripts do case-insensitive header lookup.
- The `.env` file is tracked in git (only `.env` is in `.gitignore` — verify this is intentional before modifying).
