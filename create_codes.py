"""
Create the campaign's redemption CODES and checkout VOUCHERS in animechat-ai
(anione.me) by POSTing to its admin API. Re-usable every campaign: edit the
CONFIG block below, then run.

TWO KINDS (see CLAUDE.md "Campaign Codes & Vouchers" for the full rules):
  • CODE  (token grant)  -> RedeemCodes via POST /api/admin/codes
        Redeemed at /Profile?tab=redeem&code=X. Grants image/text tokens.
        Has startsAt + expiresAt (both scheduleable).
  • VOUCHER (checkout)   -> Vouchers via POST /api/admin/vouchers
        Applied at /Pricing?voucher=X. A % discount or a token multiplier.
        Has expires_at ONLY — no start date (it is live the moment it's created).

Usage:
  python create_codes.py            # DRY RUN: print every payload, POST nothing
  python create_codes.py --create   # actually create them (idempotent: skips existing)
  python create_codes.py --verify   # GET each code/voucher and print what is stored

Schedules below are LOCAL wall-clock time (anione.me = UTC+8). The script converts
to the exact format each endpoint stores: codes -> UTC ISO (+00:00); vouchers ->
naive local ISO. That mirrors what the admin dashboard writes.
"""
import sys
import json
import requests
from datetime import datetime, timedelta, timezone

# Force UTF-8 stdout so emoji status lines don't crash on Windows (cp1252) consoles.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

# ============================ CONFIG — edit each campaign ============================
BASE_URL = "https://www.anione.me"
LOCAL_UTC_OFFSET_HOURS = 8     # anione.me local time = UTC+8

# CODES = token grants (RedeemCodes). `starts`/`expires` are LOCAL "YYYY-MM-DD HH:MM"
# (omit `starts` to make it live immediately). At least one token field must be > 0.
CODES = [
    {"code": "JUL2026",   "image_tokens": 10, "text_tokens": 0,
     "starts": "2026-06-30 00:00", "expires": "2026-07-31 23:59"},
    {"code": "PREMIUM30", "image_tokens": 30, "text_tokens": 0,
     "starts": "2026-07-24 00:00", "expires": "2026-07-31 23:59"},
    # Paid token "care package" drops (Wave-2 window, sent to Segment E on Jul 13/17/21).
    # Each is a separate code (a redeem code is once-per-user), 20 image tokens, starts a day before its send.
    {"code": "DROP1", "image_tokens": 20, "text_tokens": 0,
     "starts": "2026-07-12 00:00", "expires": "2026-07-31 23:59"},
    {"code": "DROP2", "image_tokens": 20, "text_tokens": 0,
     "starts": "2026-07-16 00:00", "expires": "2026-07-31 23:59"},
    {"code": "DROP3", "image_tokens": 20, "text_tokens": 0,
     "starts": "2026-07-20 00:00", "expires": "2026-07-31 23:59"},
]

# VOUCHERS = checkout discounts/multipliers (Vouchers). No start date (live on create).
#   type "tokenDiscount"   -> set percent_off (1-100)
#   type "tokenMultiplier" -> set multiplier (1.1-5.0)
#   not_applicable_to: "tokens"  = subscriptions only (a subscription discount)
#                      "packages" = token purchases only (a token-pack multiplier)
#                      None       = applies to both
VOUCHERS = [
    {"code": "JULY20",   "description": "July 20% off subscription (day-7)",
     "type": "tokenDiscount", "percent_off": 20, "not_applicable_to": "tokens",
     "expires": "2026-07-31 23:59"},
    {"code": "FINAL20",  "description": "Final 20% off subscription (finale day-26)",
     "type": "tokenDiscount", "percent_off": 20, "not_applicable_to": "tokens",
     "expires": "2026-07-31 23:59"},
    {"code": "JULSURGE", "description": "July 1.5x token multiplier (day-9/day-10)",
     "type": "tokenMultiplier", "multiplier": 1.5, "not_applicable_to": "packages",
     "expires": "2026-07-31 23:59"},
]
# ====================================================================================

LOCAL_TZ = timezone(timedelta(hours=LOCAL_UTC_OFFSET_HOURS))


def _parse_local(s):
    return datetime.strptime(s, "%Y-%m-%d %H:%M").replace(tzinfo=LOCAL_TZ)


def to_utc_iso(s):
    """Codes endpoint format: local wall-clock -> UTC ISO with +00:00 offset."""
    if not s:
        return None
    return _parse_local(s).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")


def to_naive_local_iso(s):
    """Vouchers endpoint format: send local wall-clock as a naive ISO string."""
    if not s:
        return None
    return _parse_local(s).strftime("%Y-%m-%dT%H:%M:%S")


def code_payload(c):
    img, txt = c.get("image_tokens", 0), c.get("text_tokens", 0)
    if max(img, txt) <= 0:
        raise ValueError(f"code {c['code']}: at least one of image_tokens/text_tokens must be > 0")
    return {
        "code": c["code"],  # codes are CASE-SENSITIVE — must match the email URL exactly
        "imageTokens": img,
        "textTokens": txt,
        "active": True,
        "startsAt": to_utc_iso(c.get("starts")),
        "expiresAt": to_utc_iso(c.get("expires")),
    }


def voucher_payload(v):
    code = v["code"].upper()  # the API uppercases voucher codes; do it here so it matches the email URL
    if not v.get("description"):
        raise ValueError(f"voucher {code}: 'description' is required")
    vtype = v.get("type")
    p = {
        "code": code,
        "description": v["description"],
        "type": vtype,
        "is_active": True,
        "not_applicable_to": v.get("not_applicable_to"),
        "expires_at": to_naive_local_iso(v.get("expires")),
    }
    if vtype == "tokenDiscount":
        po, ao = v.get("percent_off"), v.get("amount_off")
        if po is not None and not (1 <= po <= 100):
            raise ValueError(f"voucher {code}: percent_off must be 1-100")
        if po is None and ao is None:
            raise ValueError(f"voucher {code}: tokenDiscount needs percent_off or amount_off")
        p["percent_off"] = po
        p["amount_off"] = ao  # usually None
    elif vtype == "tokenMultiplier":
        m = v.get("multiplier")
        if m is None or not (1.1 <= m <= 5.0):
            raise ValueError(f"voucher {code}: tokenMultiplier needs multiplier in 1.1-5.0")
        p["multiplier"] = m
    else:
        raise ValueError(f"voucher {code}: type must be 'tokenDiscount' or 'tokenMultiplier'")
    return p


def _is_already_exists(resp):
    return resp.status_code in (400, 409) and "exist" in resp.text.lower()


def run(create):
    mode = "CREATE" if create else "DRY RUN (no writes)"
    print(f"=== {mode} - {BASE_URL} ===\n")
    try:
        plan = [("codes", code_payload(c)) for c in CODES]
        plan += [("vouchers", voucher_payload(v)) for v in VOUCHERS]
    except ValueError as e:
        print(f"CONFIG ERROR: {e}")
        sys.exit(1)

    created = skipped = failed = 0
    for ep, payload in plan:
        print(f"[{ep}] {payload['code']}")
        print("   payload: " + json.dumps(payload))
        if not create:
            continue
        try:
            r = requests.post(f"{BASE_URL}/api/admin/{ep}", json=payload, timeout=30)
        except Exception as e:
            failed += 1
            print(f"   ❌ network error: {e}")
            continue
        if 200 <= r.status_code < 300:
            created += 1
            print(f"   ✅ created (HTTP {r.status_code})")
        elif _is_already_exists(r):
            skipped += 1
            print(f"   ⏭️  already exists — skipped (HTTP {r.status_code})")
        else:
            failed += 1
            print(f"   ❌ HTTP {r.status_code}: {r.text[:200]}")

    if create:
        print(f"\nDone: {created} created, {skipped} already existed, {failed} failed.")
    else:
        print("\nDry run only — re-run with --create to write these.")


def _get_items(ep, page):
    r = requests.get(f"{BASE_URL}/api/admin/{ep}", params={"page": page}, timeout=30)
    d = r.json()
    if isinstance(d, list):
        return d, None
    items = d.get(ep) or d.get("data") or d.get("items") or []
    return items, d.get("totalPages")


def verify(max_pages=40):
    targets = {c["code"] for c in CODES} | {v["code"] for v in VOUCHERS}
    found = {}
    for ep in ("codes", "vouchers"):
        page = 1
        while page <= max_pages:
            items, total_pages = _get_items(ep, page)
            if not items:
                break
            for it in items:
                if str(it.get("code", "")) in targets:
                    found[it["code"]] = it
            if all(t in found for t in targets):
                break
            if not total_pages or page >= total_pages:
                break
            page += 1

    print("=== stored values ===")
    for code in sorted(targets):
        it = found.get(code)
        if not it:
            print(f"   {code}: ❌ NOT FOUND")
            continue
        if "imageTokens" in it:
            print(f"   {code}: img={it.get('imageTokens')} txt={it.get('textTokens')} "
                  f"active={it.get('active')} starts={it.get('startsAt')} expires={it.get('expiresAt')}")
        else:
            print(f"   {code}: type={it.get('type')} pct={it.get('percent_off')} mult={it.get('multiplier')} "
                  f"n/a_to={it.get('not_applicable_to')} active={it.get('is_active')} expires={it.get('expires_at')}")


if __name__ == "__main__":
    if "--verify" in sys.argv:
        verify()
    else:
        run(create="--create" in sys.argv)
