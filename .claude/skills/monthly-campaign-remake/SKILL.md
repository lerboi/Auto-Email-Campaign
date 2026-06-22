---
name: monthly-campaign-remake
description: Recreates Anione's monthly Resend email campaign templates for a new month. Use this skill whenever the user says things like "new month campaign", "remake templates for April", "update campaign for next month", "create new monthly emails", "prepare next campaign", or any request about generating fresh email templates for a new campaign period. This is the primary skill for the monthly email marketing workflow.
---

# Monthly Campaign Remake

This skill handles the end-to-end process of remaking Anione's monthly Resend email campaign templates for a new month. It takes the previous month's 6 unique templates (10 campaign days with A/B group alternation) and produces refreshed versions with new copy, promo codes, seasonal theming, and updated metadata. Templates are sent **inline** via Resend Broadcasts (read from disk at send time) — there is no template-upload-to-dashboard step.

## Before You Start

1. **Read the current templates** in `templates/{month}/` (e.g., `templates/march/`) to understand what already exists. Browse `templates/` to see previous months' campaigns for reference.
2. **Ask the user** for the following inputs (do not assume):
   - **Target month** (e.g., "April 2026")
   - **Campaign start date** (e.g., "2026-04-01") — the first day emails go out
   - **Seasonal theme / vibe** (e.g., "Spring renewal", "Summer heat", "Back to school")
   - **Promo codes** — the user decides these. Typical pattern:
     - Day 1 gift code (e.g., `APR2026` for free tokens)
     - Day 7 sale code (e.g., `APRIL20` for 20% off)
     - Day 9/10 multiplier code (e.g., `APRSURGE` for 1.5x tokens)
   - **Day 3 & Day 5 feature topics** — these are the flexible "feature showcase" slots. The user picks what to highlight each month (e.g., Custom Characters, Custom Scenarios, Voice Calls, Image Generation, Relationship System, etc.). Ask what features they want for Day 3 and Day 5 this month.
   - **Any new features or updates** on Anione to highlight (check `references/anione-features.md` for the platform's feature set)
   - **Any changes to offers** (different discount %, different token amounts, new pricing)
   - **Hero images** — whether to reuse existing ones or if new ones are available
3. **Read `deploy_new_year.py`** to see the current `CAMPAIGN_MAP` structure

## Campaign Structure (6 Unique Templates, 12 Send Days)

The campaign follows this proven funnel structure. Each template is sent twice (once to GROUP_A, once to GROUP_B on consecutive days, as two Resend Broadcasts to two Segments) to spread the audience over two days:

| Day | Template Purpose | Tone | Goal |
|-----|-----------------|------|------|
| **Day 1** | Free Gift (token voucher) | Warm, generous | Reactivation hook — get users back on the site |
| **Day 3** | Feature Showcase #1 (variable — user chooses) | Aspirational, creative | Educate users on a key platform feature |
| **Day 5** | Feature Showcase #2 (variable — user chooses) | Imaginative, empowering | Educate users on a different platform feature |
| **Day 7** | Flash Sale (subscription discount) | Urgent, value-driven | Convert free users to paid ($7.99/mo with discount) |
| **Day 9** | Token Multiplier (bonus tokens) | Exciting, deal-focused | Drive token pack purchases with 1.5x multiplier |
| **Day 10** | Final Urgency (deadline reminder) | Urgent, FOMO | Last push — remind about expiring multiplier offer |

## Template Content Anatomy (What Goes In Each Day)

Each day's email has a distinct content recipe. When remaking for a new month, preserve these structural patterns — they're what makes each email feel different while maintaining the funnel progression.

### Day 1 — Free Gift (Voucher Code Email)

**Content blocks:**
1. Hero image (character art, links to redemption page with code pre-filled)
2. Warm greeting + 2-3 paragraphs: "new month, new possibilities" seasonal opener → mention the gift → explain what it unlocks
3. Horizontal divider line
4. **Green dashed offer box** (bg `#f0fdf4`, border `#166534`):
   - Box title: "{MONTH} GIFT VOUCHER" (uppercase, bold, green)
   - Description: "Use this code to get **10 Image tokens** or explore our brand new characters for free"
   - Expiry notice: "Expires in 48 Hours" (red text, uppercase)
   - Code display: `{CODE}` in monospace on white bg with dashed green border
   - CTA button: "Redeem My Gift Now →" (red `#D42426`)
5. P.S. line teasing upcoming month updates (italic, gray, centered)

**CTA link pattern:** `https://www.anione.me/en/Profile?tab=redeem&code={CODE}`
**Unique to Day 1:** Only template with an expiry timer on a free gift. Simplest offer box (no bullet list). Horizontal divider before the box.

---

### Day 3 — Feature Showcase #1 (Variable Content)

> **This is a flexible slot.** The specific feature changes each month based on what the user wants to highlight. March used Custom Characters; another month might use Voice Calls, Image Generation, or a new feature. Ask the user what feature to showcase.

**Structural pattern (stays the same regardless of feature):**
1. Hero image (relevant to the featured topic)
2. Bold heading emphasizing the feature's core appeal
3. 1-2 paragraphs about what the feature lets you do
4. **Embedded GIF** showing the feature in action (captioned)
5. 1 paragraph going deeper on the experience + unrestricted environment
6. **Optional: Showcase image** (static screenshot, with subtle 1px border) — use when the feature is visual (characters, images) but skip for non-visual features (voice, chat)
7. **Blue dashed feature box** (bg `#eff6ff`, border `#3b82f6`):
   - Box title: descriptive toolkit name (uppercase, bold, blue `#1e40af`)
   - **3 bullet-point features** (each with bold label + description) — highlight the top 3 selling points of the chosen feature
   - CTA button: action-oriented text + " →" (blue `#3b82f6`)
8. Closing one-liner (bold, centered)

**CTA link pattern:** `https://www.anione.me/en` (or a more specific page if the feature has one)
**Key traits:** Most image-heavy template (hero + GIF + optional showcase = 2-3 visuals). 3-item bullet feature list. No promo code. Blue color scheme.

**Previous feature topics used:**
- March 2026: Custom Characters ("She's exactly who you want her to be")

---

### Day 5 — Feature Showcase #2 (Variable Content)

> **This is a flexible slot.** The specific feature changes each month. March used Custom Scenarios; another month might use a different feature. Must be different from whatever Day 3 covers. Ask the user.

**Structural pattern (stays the same regardless of feature):**
1. Hero image (relevant to featured topic, can differ from Day 3)
2. Bold heading emphasizing the feature's empowerment angle
3. 1-2 paragraphs about the feature — position the user as the one in control
4. **Embedded GIF** showing the feature in action (captioned)
5. 1 paragraph expanding on the experience and freedom
6. **Purple dashed feature box** (bg `#f5f3ff`, border `#8b5cf6`):
   - Box title: thematic/seasonal name rather than just descriptive (uppercase, bold, purple `#5b21b6`)
   - **5 bullet-point features** (each with bold label + description) — more comprehensive breakdown than Day 3
   - CTA button: action-oriented text + " →" (purple `#8b5cf6`)
7. Closing challenge line (bold, centered)

**CTA link pattern:** `https://www.anione.me/en` (or a more specific page)
**Key traits:** Longer feature list (5 bullets vs. Day 3's 3). Has GIF but typically no showcase image (2 visuals). No promo code. Purple color scheme. Box title is themed to the month, not just the feature name.

**Previous feature topics used:**
- March 2026: Custom Scenarios ("Your World. Your Story. Your Rules.")

---

### Day 7 — Flash Sale (Subscription Discount)

**Content blocks:**
1. Hero image (different character art from Days 3/5)
2. Bold urgent heading with timer emoji (e.g., "⏳ 48-HOUR {MONTH} FLASH SALE")
3. Greeting + 2 paragraphs: seasonal transition opener → "For the next 48 hours, upgrade for **20% less**"
4. **Green dashed offer box** (bg `#f0fdf4`, border `#166534`):
   - Box title: "EXCLUSIVE: $7.99/mo DEAL" (bold, centered, green `#166534`)
   - Instruction text with code name bolded
   - **3 benefit bullets** (with special characters as bullet markers):
     - "∞ Unlimited Text & High-Intel Roleplay"
     - "200 AI Images per month"
     - "50 Tokens + 25% OFF Daily Wheel Spins"
   - Code display: `CODE: {CODE}` on white bg with dashed border
   - Fine print: "*Applicable on subscriptions only" (11px, gray, italic)
   - CTA button: "Upgrade My {Month} →" (red `#D42426`)
5. Closing urgency line (italic, centered)

**CTA link pattern:** `https://www.anione.me/en/Pricing?voucher={CODE}`
**Unique to Day 7:** Only template showing actual pricing ($X.XX/mo). Has fine print disclaimer. Benefit bullets use special characters (∞) not just text. Links to Pricing page, not homepage or Profile.

---

### Day 9 — Token Multiplier (1.5x Bonus)

**Content blocks:**
1. Hero image (different character art)
2. Bold exciting heading with lightning emoji (e.g., "⚡ 1.5x TOKEN MULTIPLIER ACTIVATED!")
3. Greeting + 2 paragraphs: "Why settle for standard when you can have **50% MORE?**" → explain the 1.5x multiplier on all token pack purchases for 48 hours
4. **Red/pink dashed offer box** (bg `#fdf2f2`, border `#D42426`):
   - Box title: "🚀 LIMITED TIME: 50% BONUS TOKENS" (bold, centered, red `#D42426`)
   - Simple instruction text: "Use the code below at checkout to receive 1.5x more tokens on any pack purchase"
   - Code display: `CODE: {CODE}` on white bg with dashed red border
   - CTA button: "Get My Bonus Tokens →" (red `#D42426`)
5. Closing confidence line (italic, centered)

**CTA link pattern:** `https://www.anione.me/en/Pricing?voucher={CODE}`
**Unique to Day 9:** Simpler box than Day 7 — no bullet list, just instructional text + code + CTA. Focuses on token packs, not subscriptions. Red/pink color scheme.

---

### Day 10 — Final Urgency (24-Hour Deadline)

**Content blocks:**
1. Hero image (can be different from Day 9 or platform homepage hero)
2. Bold urgent heading with timer emoji (e.g., "⏳ FINAL HOURS: Don't miss your bonus tokens!")
3. Greeting + 2 paragraphs: "This is a quick reminder" that the multiplier ends in <24 hours → "Once the timer hits zero, the 50% bonus tokens will disappear"
4. **Orange/warm dashed offer box** (bg `#fffaf0`, border `#D42426`):
   - Box title: "⚠️ ENDING SOON: 1.5x MULTIPLIER" (bold, centered, dark orange `#9a3412`)
   - Instruction text about using code before expiry
   - Code display: `CODE: {CODE}` — **larger font (20px)** than Day 9's code display for emphasis
   - CTA button: "Claim My Bonus Tokens →" (red `#D42426`)
5. Closing gratitude line: "Thank you for being a part of Anione. Happy {Month} creating!"

**CTA link pattern:** `https://www.anione.me/en/Pricing?voucher={CODE}`
**Unique to Day 10:** Uses same code as Day 9 (it's a reminder). Warning emoji (⚠️) instead of rocket. Orange-warm background. Larger code font for visual emphasis. Closing line shifts from confidence to gratitude. Simplest offer box overall.

---

### Quick Reference: Content Ingredients by Day

| Element | Day 1 | Day 3 | Day 5 | Day 7 | Day 9 | Day 10 |
|---------|-------|-------|-------|-------|-------|--------|
| **Hero image** | Yes | Yes | Yes | Yes | Yes | Yes |
| **Inline GIF** | No | Yes | Yes | No | No | No |
| **Showcase image** | No | Optional | No | No | No | No |
| **Total visuals** | 1 | 2-3 | 2 | 1 | 1 | 1 |
| **Box color** | Green | Blue | Purple | Green | Red/pink | Orange/warm |
| **Bullet list** | None | 3 items | 5 items | 3 items | None | None |
| **Content fixed?** | Yes | **No — variable** | **No — variable** | Yes | Yes | Yes |
| **Promo code** | Gift code | None | None | Sale code | Multiplier code | Same as Day 9 |
| **Expiry shown** | "48 Hours" | None | None | Implied 48h | Implied 48h | "24 Hours" |
| **Pricing shown** | Free | None | None | $X.XX/mo | Multiplier | Multiplier |
| **Fine print** | No | No | No | Yes | No | No |
| **CTA links to** | Profile/Redeem | Homepage | Homepage | Pricing | Pricing | Pricing |
| **CTA button color** | Red | Blue | Purple | Red | Red | Red |
| **Closing tone** | Anticipation | Confidence | Challenge | Urgency | Confidence | Gratitude |

## File Structure Per Template

Each template lives in `templates/{month}/day-N/` (e.g., `templates/april/day-1/`) with exactly 3 files:

### `metadata.txt`
```
Name: {Month} Day {N} ({Short Description})
Subject: {emoji} {Subject Line}
Alias: {mon}-{purpose}-day-{N}
```

**Alias naming convention**: 3-letter lowercase month prefix + purpose keyword + day number.
Examples: `apr-gift-day-1`, `apr-sale-day-7`, `apr-multiplier-day-9`
For Day 3/5 (variable feature slots), the alias reflects whatever feature is chosen: e.g., `apr-voice-calls-day-3`, `apr-image-gen-day-5`

> Note: with Resend, `Alias` is now just an internal label (kept for readability/history). The dispatcher (`deploy_new_year.py`) sends a Broadcast using the `Subject` and `Name` from `metadata.txt` and the inline `template.html`/`template.txt` — it does **not** look up a template by alias. `CAMPAIGN_MAP` keys each date to a `template_dir` + `segment`, not an alias.

### `template.html`
The HTML email template. Uses a consistent 600px-wide table layout with:
- **Preheader text** (hidden div at top for email client previews)
- **Anione logo** header with link to `https://www.anione.me`
- **Hero image** (600px wide, links to relevant page)
- **Main heading** with emoji
- **Body copy** — 2-3 paragraphs, conversational tone
- **Feature/offer box** — dashed border box with the key CTA:
  - Green dashed border (`#166534`) for gift/free offers
  - Blue dashed border (`#3b82f6`) for character features
  - Purple dashed border (`#8b5cf6`) for scenario features
  - Red/green dashed border for sale offers
  - Red/pink dashed border for token multiplier
  - Orange/red dashed border for urgency/final
- **CTA button** — inline-styled link button
- **Footer** with copyright year and the `{{{RESEND_UNSUBSCRIBE_URL}}}` Resend managed-unsubscribe placeholder
- **Full dark mode support** via `@media (prefers-color-scheme: dark)`
- **Mobile responsive** via `@media screen and (max-width: 600px)`

### `template.txt`
Plain text fallback version with the same key information, promo codes, and links.

## Step-by-Step Remake Process

### Step 1: Generate All 6 Templates

For each of the 6 template days, create the 3 files (`metadata.txt`, `template.html`, `template.txt`) in `templates/{month}/day-{N}/` (e.g., `templates/april/day-1/`). Use the lowercase full month name as the folder.

**What changes per month:**
- Month name and seasonal references in all copy
- Promo/voucher codes (user-provided)
- Subject lines (fresh, not recycled)
- Preheader text
- Body copy (new angles on the same features — don't repeat last month's phrasing)
- Seasonal emoji choices
- Template alias prefix (3-letter month abbreviation)
- Copyright year (if it changes)
- Any new feature callouts or pricing changes

**What stays the same:**
- HTML structure and CSS (the layout, responsive styles, dark mode support)
- Anione logo and branding
- Color scheme for each template type (green=gift, blue=characters, purple=scenarios, etc.)
- CTA link patterns (e.g., `https://www.anione.me/en/Profile?tab=redeem&code={CODE}`)
- Resend unsubscribe placeholder `{{{RESEND_UNSUBSCRIBE_URL}}}`
- 600px table width, font families, general styling
- The funnel progression (free gift → features → sale → multiplier → urgency)

### Step 2: Update `deploy_new_year.py`

Update the `CAMPAIGN_MAP` dictionary with new dates. Each date maps to a local
template folder (`template_dir`) and the Resend segment to send to (`segment`):

```python
CAMPAIGN_MAP = {
    "{start_date}":   {"template_dir": "templates/{month}/day-1",  "segment": SEGMENT_A},
    "{start+1}":      {"template_dir": "templates/{month}/day-1",  "segment": SEGMENT_B},
    "{start+2}":      {"template_dir": "templates/{month}/day-3",  "segment": SEGMENT_A},
    "{start+3}":      {"template_dir": "templates/{month}/day-3",  "segment": SEGMENT_B},
    "{start+4}":      {"template_dir": "templates/{month}/day-5",  "segment": SEGMENT_A},
    "{start+5}":      {"template_dir": "templates/{month}/day-5",  "segment": SEGMENT_B},
    "{start+6}":      {"template_dir": "templates/{month}/day-7",  "segment": SEGMENT_A},
    "{start+7}":      {"template_dir": "templates/{month}/day-7",  "segment": SEGMENT_B},
    "{start+8}":      {"template_dir": "templates/{month}/day-9",  "segment": SEGMENT_A},
    "{start+9}":      {"template_dir": "templates/{month}/day-9",  "segment": SEGMENT_B},
    "{start+10}":     {"template_dir": "templates/{month}/day-10", "segment": SEGMENT_A},
    "{start+11}":     {"template_dir": "templates/{month}/day-10", "segment": SEGMENT_B},
}
```

`{month}` is the lowercase month folder (e.g. `july`). `SEGMENT_A`/`SEGMENT_B`
are read from `RESEND_SEGMENT_A`/`RESEND_SEGMENT_B` at the top of the file.
Also update the comment above `CAMPAIGN_MAP` to reflect the new month.

### Step 3: Verify User Group CSVs

Ask the user if the email lists (GROUP_A, GROUP_B) need updating. If new CSVs are available, update the `GROUP_A_FILES` / `GROUP_B_FILES` paths at the top of `deploy_new_year.py`, then run `python sync_contacts.py` to push the updated lists into the Resend segments. (The CSVs remain the source of truth; the segments are just where Resend reads recipients from at send time.)

### Step 4: Present Summary for Review

After generating everything, present a summary table:

| Day | Alias | Subject Line | Promo Code |
|-----|-------|-------------|------------|
| 1 | ... | ... | ... |
| 3 | ... | ... | ... |
| ... | ... | ... | ... |

And the updated `CAMPAIGN_MAP` dates for confirmation.

### Step 5: Resend Send Checklist

There is **no template upload step** with Resend — the HTML/text/subject are read from
disk and sent inline as a Broadcast. After reviewing the templates, remind the user to:
1. Confirm the `mail.anione.me` sending domain is verified in Resend (DKIM/SPF/MX).
2. If the recipient lists changed this month, run `python sync_contacts.py` to push the CSVs into the Resend segments (see Step 3).
3. Ensure `RESEND_API_KEY`, `RESEND_SEGMENT_A`, and `RESEND_SEGMENT_B` are set in the environment (Railway + `.env`).
4. Verify each `template.html`/`template.txt` footer still contains the `{{{RESEND_UNSUBSCRIBE_URL}}}` placeholder (managed unsubscribe).
5. The Railway cron runs `deploy_new_year.py` daily; it sends the scheduled broadcast on each `CAMPAIGN_MAP` date — no manual send needed.

## Writing Guidelines for Email Copy

- **Tone**: Conversational, slightly playful, not corporate. Address the reader as "you".
- **Length**: Keep body copy to 2-3 short paragraphs max. People skim emails.
- **Urgency**: Use time-limited language for sale/multiplier days ("48 hours", "expires soon")
- **Feature emails**: Focus on what the user can DO, not what the feature IS. Paint a picture.
- **Avoid**: Repeating the same phrases across emails. Each should feel fresh.
- **Seasonal hooks**: Tie the month/season into the opening line naturally — don't force it.
- **P.S. lines**: Use sparingly (Day 1 is good for teasing upcoming content).

## Base Templates

The `base-templates/` directory contains ready-to-use HTML and plain text skeleton templates for each email type. These have the exact layout, CSS, dark mode support, and structural elements already locked in — you only need to replace the `{{PLACEHOLDER}}` variables with month-specific content.

```
base-templates/
├── gift-day-1/            # Day 1: Free gift voucher (green box, red CTA)
│   ├── template.html
│   └── template.txt
├── feature-showcase-day-3/ # Day 3: Feature spotlight #1 (blue box, 3 bullets, GIF)
│   ├── template.html
│   └── template.txt
├── feature-showcase-day-5/ # Day 5: Feature spotlight #2 (purple box, 5 bullets, GIF)
│   ├── template.html
│   └── template.txt
├── sale-day-7/            # Day 7: Flash sale (green box, pricing, 3 benefit bullets)
│   ├── template.html
│   └── template.txt
├── multiplier-day-9/      # Day 9: Token multiplier (red/pink box, code + CTA)
│   ├── template.html
│   └── template.txt
└── urgency-day-10/        # Day 10: Final urgency (orange/warm box, larger code font)
    ├── template.html
    └── template.txt
```

**How to use:** Read the base template, replace all `{{PLACEHOLDER}}` variables with the new month's content, and write the result to `templates/{month}/day-N/` (e.g., `templates/april/day-1/`). See `references/placeholder-variables.md` for the full variable reference per template type.

**Best practices baked into the templates:**
- Outlook dark mode fix (`[data-ogsc]` selectors) on all templates
- Mobile responsive breakpoints at 600px
- Preheader text div for inbox preview optimization
- Proper MSO attributes for Outlook table rendering
- `role="presentation"` on layout tables for accessibility
- All images have alt text attributes
- Resend managed-unsubscribe placeholder `{{{RESEND_UNSUBSCRIBE_URL}}}` in footer
- Inline styles for maximum email client compatibility (no external CSS)

## References

- `references/anione-features.md` — Platform features, pricing, and messaging angles for writing email copy
- `references/placeholder-variables.md` — Complete variable reference for all 6 base templates with examples
