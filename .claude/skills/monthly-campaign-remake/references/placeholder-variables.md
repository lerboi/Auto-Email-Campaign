# Placeholder Variable Reference

All base templates use `{{VARIABLE_NAME}}` placeholders. When generating a new month's campaign, replace every placeholder with the actual content. This document lists all variables per template type.

## Shared Variables (all templates)

| Variable | Description | Example |
|----------|-------------|---------|
| `{{YEAR}}` | Copyright year | `2026` |
| `{{MONTH_NAME}}` | Full month name | `April` |
| `{{EMAIL_TITLE}}` | HTML `<title>` tag (not visible in email body) | `Your April Gift` |
| `{{PREHEADER_TEXT}}` | Hidden preview text shown in email client inbox | `Use code APR2026 to unlock 10 free tokens...` |
| `{{HEADING}}` | Main H1 heading with emoji | `🎁 Fresh start, fresh tokens.` |
| `{{HERO_IMAGE_URL}}` | Full URL to hero image | `https://anione.me/blogs/makima-ai-chat/makima-ai-chat-hero.webp` |
| `{{CTA_BUTTON_TEXT}}` | Button label text | `Redeem My Gift Now →` |
| `{{CLOSING_LINE}}` | Italic closing/P.S. line | `P.S. Big things are coming this April...` |

---

## Day 1 — Gift Template (`gift-day-1/`)

| Variable | Description | Example |
|----------|-------------|---------|
| `{{GIFT_CODE}}` | Redemption voucher code | `APR2026` |
| `{{BODY_PARAGRAPH_1}}` | First body paragraph (seasonal opener + context) | `A new month means new possibilities. Spring is in full bloom...` |
| `{{BODY_PARAGRAPH_2}}` | Second body paragraph (introduce the gift) | `We've loaded a special <strong>"April Bloom" Voucher</strong> into your account. No strings attached.` |
| `{{VOUCHER_TITLE}}` | Title inside the green box (uppercase) | `APRIL GIFT VOUCHER` |
| `{{VOUCHER_DESCRIPTION}}` | Description inside the green box | `Use this code to get <strong>10 Image tokens</strong> or explore our brand new characters for free.` |
| `{{PS_LINE}}` | P.S. line at bottom | `P.S. Keep an eye on your inbox. We have some major updates dropping this April...` |

---

## Day 3 — Feature Showcase #1 (`feature-showcase-day-3/`)

| Variable | Description | Example |
|----------|-------------|---------|
| `{{INTRO_PARAGRAPH}}` | Centered intro paragraph about the feature | `Spring is for new beginnings. Stop searching for the "right" character—create her yourself...` |
| `{{GIF_URL}}` | URL to animated GIF showing feature in action | `https://anione.me/blogs/Gif-imageCreate.gif` |
| `{{GIF_ALT_TEXT}}` | Alt text for GIF | `Creation in Action` |
| `{{DETAIL_PARAGRAPH}}` | Left-aligned detail paragraph (deeper explanation) | `Dive into a world of unprecedented customization...` |
| `{{SHOWCASE_IMAGE_URL}}` | Optional: URL to static showcase screenshot | `https://anione.me/blogs/custom-character-showcase.png` |
| `{{SHOWCASE_IMAGE_ALT}}` | Optional: Alt text for showcase image | `Character Showcase` |
| `{{HERO_IMAGE_ALT}}` | Alt text for hero image | `Create Your Character` |
| `{{BOX_TITLE}}` | Blue box title (uppercase) | `YOUR CREATIVE TOOLKIT` |
| `{{FEATURE_1_LABEL}}` | First bullet bold label | `Visualize Perfection` |
| `{{FEATURE_1_DESC}}` | First bullet description | `Total control over her look.` |
| `{{FEATURE_2_LABEL}}` | Second bullet bold label | `Forge a Soul` |
| `{{FEATURE_2_DESC}}` | Second bullet description | `Define her voice, past, and personality.` |
| `{{FEATURE_3_LABEL}}` | Third bullet bold label | `Pure Freedom` |
| `{{FEATURE_3_DESC}}` | Third bullet description | `Unrestricted interactions, zero filters.` |
| `{{CTA_LINK}}` | CTA destination URL | `https://www.anione.me/en` |

**Note:** The showcase image block is commented out in the HTML template by default. Uncomment it when the featured topic is visual (characters, images). Leave it commented out for non-visual features (voice, chat).

---

## Day 5 — Feature Showcase #2 (`feature-showcase-day-5/`)

Same as Day 3 but with 5 bullets instead of 3, and purple color scheme:

| Variable | Description | Example |
|----------|-------------|---------|
| `{{INTRO_PARAGRAPH}}` | Centered intro paragraph | `Why settle for a story told by someone else?...` |
| `{{GIF_URL}}` | URL to animated GIF | `https://anione.me/blogs/Gif-imageCreate.gif` |
| `{{GIF_ALT_TEXT}}` | Alt text for GIF | `Create Your World` |
| `{{DETAIL_PARAGRAPH}}` | Left-aligned detail paragraph | `Think of any situation you can imagine...` |
| `{{HERO_IMAGE_ALT}}` | Alt text for hero image | `Unlimited Worlds` |
| `{{BOX_TITLE}}` | Purple box title — use a **seasonal/thematic** name | `UNLIMITED MASTER APRIL` |
| `{{FEATURE_1_LABEL}}` through `{{FEATURE_5_LABEL}}` | Five bullet bold labels | `Design Any Location`, etc. |
| `{{FEATURE_1_DESC}}` through `{{FEATURE_5_DESC}}` | Five bullet descriptions | `Pick the setting, from neon rooftops to cozy cabins.` |
| `{{CTA_LINK}}` | CTA destination URL | `https://www.anione.me/en` |

---

## Day 7 — Flash Sale (`sale-day-7/`)

| Variable | Description | Example |
|----------|-------------|---------|
| `{{SALE_CODE}}` | Discount code for checkout | `APRIL20` |
| `{{BODY_PARAGRAPH_1}}` | First body paragraph (seasonal + context) | `A new season means new beginnings...` |
| `{{BODY_PARAGRAPH_2}}` | Second body paragraph (introduce the deal + urgency) | `For the next 48 hours, we are opening an exclusive window for you to upgrade your experience for <strong>20% less</strong>.` |
| `{{DEAL_TITLE}}` | Green box title showing the price | `EXCLUSIVE: $7.99/mo DEAL` |
| `{{BENEFIT_BULLETS}}` | HTML benefit list inside the box | `&bull; ∞ Unlimited Text &amp; High-Intel Roleplay<br/>&bull; 200 AI Images per month<br/>&bull; 50 Tokens + 25% OFF Daily Wheel Spins` |
| `{{BENEFIT_BULLETS_PLAIN}}` | Plain text version of benefits (for .txt) | See below |

**Plain text benefits format:**
```
- Unlimited Text & High-Intel Roleplay
- 200 AI Images per month
- 50 Tokens + 25% OFF Daily Wheel Spins
```

---

## Day 9 — Token Multiplier (`multiplier-day-9/`)

| Variable | Description | Example |
|----------|-------------|---------|
| `{{MULTIPLIER_CODE}}` | Token multiplier checkout code | `APRSURGE` |
| `{{BODY_PARAGRAPH_1}}` | First body paragraph (excitement + hook) | `Why settle for the standard amount when you can have <strong>50% MORE?</strong>` |
| `{{BODY_PARAGRAPH_2}}` | Second body paragraph (explain the multiplier) | `For the next 48 hours, we are activating a 1.5x Multiplier on all token pack purchases...` |
| `{{BOX_TITLE}}` | Red box title with emoji | `🚀 LIMITED TIME: 50% BONUS TOKENS` |
| `{{BOX_DESCRIPTION}}` | Instruction text inside box | `Use the code below at checkout to receive 1.5x more tokens on any pack purchase.` |

---

## Day 10 — Urgency/Final (`urgency-day-10/`)

Uses the **same `{{MULTIPLIER_CODE}}`** as Day 9 (it's a reminder email).

| Variable | Description | Example |
|----------|-------------|---------|
| `{{MULTIPLIER_CODE}}` | Same code as Day 9 | `APRSURGE` |
| `{{BODY_PARAGRAPH_1}}` | First body paragraph (reminder framing) | `This is a quick reminder that our April <strong>1.5x Token Multiplier</strong> event is officially ending in less than 24 hours.` |
| `{{BODY_PARAGRAPH_2}}` | Second body paragraph (FOMO + call to action) | `If you've been planning to stock up... now is the time to act. Once the timer hits zero, the 50% bonus tokens will disappear from the shop.` |
| `{{BOX_TITLE}}` | Orange box title with warning emoji | `⚠️ ENDING SOON: 1.5x MULTIPLIER` |
| `{{BOX_DESCRIPTION}}` | Urgency instruction text | `Every pack you purchase comes with 50% more tokens. Use the code at checkout before it expires.` |

**Key difference from Day 9:** Box background is warm/orange (`#fffaf0`) instead of pink (`#fdf2f2`). Code font is larger (20px vs 18px). Closing line should express gratitude rather than excitement.
