# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Automated email campaign system for **AniOne** (anione.me) that sends marketing emails via the **Resend API** using **Broadcasts** to managed **Segments**. Deployed on **Railway** as a daily cron job.

## Architecture

- **`deploy_new_year.py`** — Active campaign dispatcher (runs daily via Railway cron). Uses a date-keyed `CAMPAIGN_MAP` to determine which local template folder and which Resend Segment to send for a given day. Reads the template's HTML/text/Subject from disk and sends it as a Resend **Broadcast** (create + send in one API call). Alternates between GROUP_A and GROUP_B segments (~2,600 users each) on consecutive days.
- **`sync_contacts.py`** — Pushes the `email/` CSV lists into the two Resend Segments (`RESEND_SEGMENT_A` / `RESEND_SEGMENT_B`). The CSVs remain the source of truth; run this once per month after updating lists. Use `--create` the first time to create the segments and print their IDs. (Resend has no bulk-import API, so contacts are created one-by-one, throttled under the 5 req/s rate limit.)
- **`send_daily.py`** — Legacy multi-phase campaign script (Christmas campaign). Sends to VIP list first, waits 90 minutes for IP warmup, then sends to cold list. Run manually with `--day N` flag.
- **`scrub_lists.py`** — Interactive email list cleaner. Validates emails (syntax + MX records via `email_validator`), filters bot patterns (+ aliases, excessive dots). Reads from and writes `CLEANED_` prefixed files to `email/` folder.
- **`remove_duplicates.py`** — Deduplicates CSV email lists with Gmail normalization (dot/plus-alias handling). Hardcoded `INPUT_FILE`/`OUTPUT_FILE` paths must be edited per use.
- **`test.py`** — Scratch file for formatting raw email lists; not a test suite.
- **`email/`** — CSV files containing user email lists segmented by signup date and payment status. Column header is `email` (lowercase) in newer files.

## Key Configuration

- **Environment** (in `.env`, loaded via `python-dotenv`): `RESEND_API_KEY`, plus `RESEND_SEGMENT_A` / `RESEND_SEGMENT_B` (segment IDs). Optional: `SENDER_EMAIL`, `SENDER_NAME`.
- **Sender**: `AniOne <contact@mail.anione.me>` — the `mail.anione.me` domain must be verified in Resend (DKIM/SPF/MX) before sends succeed.
- **Sending model**: Resend Broadcasts → Segments (no Postmark message streams). Unsubscribe is handled automatically by Resend via the `{{{RESEND_UNSUBSCRIBE_URL}}}` placeholder in the template footer.
- **Rate limit**: 5 requests/sec per team (relevant to `sync_contacts.py`, which throttles itself). Broadcasts are a single call per send.
- **Railway cron**: Runs `deploy_new_year.py` daily at 03:00 UTC (`railway.json`)

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the active daily campaign (normally triggered by Railway cron)
python deploy_new_year.py

# First-time setup: create the two Resend segments and print their IDs
python sync_contacts.py --create

# Sync the CSV lists into the Resend segments (run monthly after updating lists)
python sync_contacts.py

# Clean email lists (interactive file selector)
python scrub_lists.py

# Deduplicate emails (edit INPUT_FILE/OUTPUT_FILE in script first)
python remove_duplicates.py
```

## Important Patterns

- Campaign schedules are defined as hardcoded date maps in `CAMPAIGN_MAP` — update this dict for each new campaign period (each date → `{template_dir, segment}`).
- User lists alternate between GROUP_A and GROUP_B (two Resend Segments) on consecutive days to spread sends evenly.
- CSV files in `email/` remain the source of truth for recipients; `sync_contacts.py` pushes them into the Resend Segments. The CSV email column is `email` (lowercase); the cleaning scripts do case-insensitive header lookup.
- Templates are sent **inline** (read from `templates/{month}/day-N/`) — there is no server-side template upload step. Every template footer must keep the `{{{RESEND_UNSUBSCRIBE_URL}}}` placeholder so Resend can wire up managed unsubscribe.
- The `.env` file is gitignored (not tracked); set the same vars in Railway's environment for the cron deploy.
