"""
Rules-based scam signal detector.

Pure Python — zero FastAPI / SQLAlchemy imports.

Each signal function receives the full message text and a meta dict,
and returns a Signal dataclass with .matched and .weight.

The aggregator run_rules() collects all signals, computes a weighted score,
picks the top 3 reasons, and derives advice + category from reason_codes.json.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Load frozen vocabulary once at module import
# ---------------------------------------------------------------------------
_VOCAB_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "shared", "reason_codes.json"
)
with open(os.path.abspath(_VOCAB_PATH), encoding="utf-8") as _fh:
    _VOCAB: dict = json.load(_fh)

_MSG_REASONS: dict[str, dict] = _VOCAB["message_reason_codes"]
_ADVICE_BY_CAT: dict[str, list[str]] = _VOCAB["advice_by_category"]
_TIER_THRESHOLDS = {
    "SAFE":      (0,  39),
    "CAUTION":   (40, 69),
    "HIGH_RISK": (70, 100),
}

# Known brand names for impersonation detection
_BRANDS = [
    "absa", "fnb", "first national bank", "nedbank", "standard bank",
    "capitec", "sars", "sapo", "south african post office",
    "dhl", "fedex", "ups", "aramex", "sassa", "home affairs",
    "vodacom", "mtn", "cell c", "telkom", "discovery",
    "mukuru", "westernunion", "western union", "moneygram",
    "old mutual", "hollard", "liberty",
]

# Known legitimate domains (for lookalike detection)
_LEGIT_DOMAINS = [
    "absa.co.za", "fnb.co.za", "capitecbank.co.za", "nedbank.co.za",
    "standardbank.co.za", "sars.gov.za", "mukuru.com", "postoffice.co.za",
    "dhl.com", "fedex.com", "vodacom.co.za", "mtn.co.za",
    "gov.za", "southafrica.net",
]

# URL shortener domains
_SHORTENERS = {
    "bit.ly", "tinyurl.com", "t.co", "goo.gl",
    "ow.ly", "rb.gy", "short.io", "is.gd", "buff.ly",
}

# Suspicious TLDs that legitimate SA/ZW companies don't use
_BAD_TLDS = {".xyz", ".top", ".click", ".tk", ".ml", ".ga", ".cf", ".gq"}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Signal:
    code: str           # matches a key in _MSG_REASONS
    weight: int         # from reason_codes.json
    matched: bool = False


@dataclass
class RulesResult:
    score: int = 0
    reasons: list[str] = field(default_factory=list)   # up to 3 reason codes
    advice: list[str] = field(default_factory=list)    # up to 3 advice codes
    category: str = "unknown"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _w(code: str) -> int:
    """Look up the weight for a reason code (default 10)."""
    return _MSG_REASONS.get(code, {}).get("weight", 10)


def _has(pattern: re.Pattern, text: str) -> bool:
    return bool(pattern.search(text))


def _extract_domains(text: str) -> list[str]:
    """Pull domain-like strings out of text."""
    domain_re = re.compile(
        r"(?:https?://|www\.)"
        r"([a-z0-9][-a-z0-9.]*\.[a-z]{2,})",
        re.IGNORECASE,
    )
    return [m.group(1).lower() for m in domain_re.finditer(text)]


def _levenshtein(a: str, b: str) -> int:
    """Compute edit distance between two strings."""
    if a == b:
        return 0
    if len(a) < len(b):
        a, b = b, a
    row = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        new_row = [i]
        for j, cb in enumerate(b, 1):
            new_row.append(min(
                row[j] + 1,
                new_row[j - 1] + 1,
                row[j - 1] + (0 if ca == cb else 1),
            ))
        row = new_row
    return row[-1]


# ---------------------------------------------------------------------------
# Individual signal detectors
# Each returns a Signal with .matched set.
# ---------------------------------------------------------------------------

# Pre-compiled patterns (compiled once at import, not on every call)
_OTP_PIN_RE = re.compile(
    r"\b(otp|one[\s-]?time\s*(pin|password|code)|your\s*(pin|otp|password|passcode)"
    r"|verification\s*code|secret\s*code|passcode|enter\s*(your\s*)?(pin|code))\b",
    re.IGNORECASE,
)
_URGENCY_RE = re.compile(
    r"\b(urgent|urgently|immediately|expire[sd]?|act\s*now|within\s*24|last\s*chance"
    r"|final\s*notice|limited\s*time|act\s*fast|respond\s*now|manje|ngokushesha"
    r"|phela\s*namuhla|dringend|immédiatement|haraka|hivi\s*sasa)\b",
    re.IGNORECASE,
)
_BRAND_RE = re.compile(
    r"\b(" + "|".join(re.escape(b) for b in _BRANDS) + r")\b",
    re.IGNORECASE,
)
_WHATSAPP_RE = re.compile(
    r"\b(whatsapp|wa\.me|move\s*(to|on)\s*whatsapp|contact\s*(me\s*)?on\s*whatsapp"
    r"|chat\s*(on|via)\s*whatsapp)\b",
    re.IGNORECASE,
)
_MONEY_RE = re.compile(
    r"(r\s?\d+[\d,]*\.?\d*|\$\s?\d+[\d,]*\.?\d*|£\s?\d+|€\s?\d+"
    r"|\d+\s*(rand|zar|usd|dollars?|pounds?|euros?|imali))",
    re.IGNORECASE,
)
_TRANSFER_VERB_RE = re.compile(
    r"\b(send\s*money|transfer|pay\s*(a\s*)?(fee|now)|deposit|wire|eft"
    r"|thumela\s*imali|thumela|khokha|inkokhelo)\b",
    re.IGNORECASE,
)
_FAKE_JOB_RE = re.compile(
    r"\b(work[\s-]from[\s-]home|wfh|hiring|we\s*are\s*(hiring|looking)|salary"
    r"|registration\s*fee|activation\s*fee|weekly\s*pay|earn\s*r?\d+\s*(per|/)\s*(week|day|hour)"
    r"|earn\s*(up\s*to|r)?\s*\d|umsebenzi|hholela|ukubhalisa|emploi\s*à\s*domicile"
    r"|kazi\s*ya\s*nyumbani|thuisherk)\b",
    re.IGNORECASE,
)
_ADVANCE_FEE_RE = re.compile(
    r"\b(release\s*(your\s*)?funds|processing\s*fee|inheritance|lottery|prize\s*(money|fund)?"
    r"|you\s*(have\s*)?(won|win)|claim\s*(your\s*)?prize|beneficiary|next\s*of\s*kin"
    r"|transfer\s*fee|legal\s*fee|admin\s*fee|facilitation\s*fee)\b",
    re.IGNORECASE,
)
_ROMANCE_RE = re.compile(
    r"\b(i\s*love\s*you|met\s*(you\s*)?online|dating|my\s*(darling|love|dear|sweetheart)"
    r"|send\s*me\s*money|stuck\s*at\s*customs|stranded|deployed\s*overseas|ngiyakuthanda"
    r"|thumela\s*imali|gift\s*card|itunes|google\s*play\s*card)\b",
    re.IGNORECASE,
)
_GENERIC_GREETING_RE = re.compile(
    r"\b(dear\s+customer|dear\s+user|dear\s+beneficiary|dear\s+winner"
    r"|dear\s+account\s+holder|dear\s+valued\s+customer|dear\s+client"
    r"|hello\s+dear|greetings\s+dear)\b",
    re.IGNORECASE,
)
_PHONE_RE = re.compile(
    r"(\+?27|0)[6-8]\d{8}|(\+?263)\d{9}|(\+?254)\d{9}",
)
_SHORTENED_RE = re.compile(
    r"https?://(" + "|".join(re.escape(s) for s in _SHORTENERS) + r")/",
    re.IGNORECASE,
)


def check_suspicious_link(text: str, meta: dict) -> Signal:
    """URL present and matches blocklist or uses a bad TLD."""
    from backend.engine.url_check import extract_urls, check_urls  # noqa: PLC0415
    urls = extract_urls(text)
    if not urls:
        return Signal("SUSPICIOUS_LINK", _w("SUSPICIOUS_LINK"), False)

    result = check_urls(
        urls,
        mock=meta.get("mock_safe_browsing", True),
        api_key=meta.get("safe_browsing_api_key"),
    )
    # Also flag bad TLDs even if not in blocklist
    bad_tld = any(
        any(u.lower().split("?")[0].endswith(t) for t in _BAD_TLDS)
        for u in urls
    )
    matched = result.any_malicious or bad_tld
    return Signal("SUSPICIOUS_LINK", _w("SUSPICIOUS_LINK"), matched)


def check_requests_otp_pin(text: str, _meta: dict) -> Signal:
    """Message asks recipient to share OTP, PIN, or password."""
    return Signal("REQUESTS_OTP_PIN", _w("REQUESTS_OTP_PIN"), _has(_OTP_PIN_RE, text))


def check_urgency_language(text: str, _meta: dict) -> Signal:
    """Message uses urgent language."""
    return Signal("URGENCY_LANGUAGE", _w("URGENCY_LANGUAGE"), _has(_URGENCY_RE, text))


def check_impersonation(text: str, _meta: dict) -> Signal:
    """Message mentions a known brand without coming from that brand."""
    return Signal("IMPERSONATION", _w("IMPERSONATION"), _has(_BRAND_RE, text))


def check_move_to_whatsapp(text: str, _meta: dict) -> Signal:
    """Message asks to move conversation to WhatsApp."""
    return Signal("MOVE_TO_WHATSAPP", _w("MOVE_TO_WHATSAPP"), _has(_WHATSAPP_RE, text))


def check_asks_for_money(text: str, _meta: dict) -> Signal:
    """Message contains a monetary amount AND a transfer verb."""
    has_amount = _has(_MONEY_RE, text)
    has_verb = _has(_TRANSFER_VERB_RE, text)
    return Signal("ASKS_FOR_MONEY", _w("ASKS_FOR_MONEY"), has_amount and has_verb)


def check_fake_job_offer(text: str, _meta: dict) -> Signal:
    """Message offers a job with suspicious conditions (fee, WFH, salary)."""
    return Signal("FAKE_JOB_OFFER", _w("FAKE_JOB_OFFER"), _has(_FAKE_JOB_RE, text))


def check_advance_fee(text: str, _meta: dict) -> Signal:
    """Message requests an upfront fee to release funds/prize/inheritance."""
    return Signal("ADVANCE_FEE", _w("ADVANCE_FEE"), _has(_ADVANCE_FEE_RE, text))


def check_romance_scam(text: str, _meta: dict) -> Signal:
    """Message uses romantic language before asking for money."""
    return Signal("ROMANCE_SCAM", _w("ROMANCE_SCAM"), _has(_ROMANCE_RE, text))


def check_lookalike_domain(text: str, _meta: dict) -> Signal:
    """Extracted domain has edit-distance ≤ 2 from a known legitimate domain."""
    found_domains = _extract_domains(text)
    for dom in found_domains:
        # Strip subdomain — compare base domain only
        parts = dom.split(".")
        base = ".".join(parts[-2:]) if len(parts) >= 2 else dom
        for legit in _LEGIT_DOMAINS:
            legit_base = ".".join(legit.split(".")[-2:])
            if base != legit_base and _levenshtein(base, legit_base) <= 2:
                return Signal("LOOKALIKE_DOMAIN", _w("LOOKALIKE_DOMAIN"), True)
    return Signal("LOOKALIKE_DOMAIN", _w("LOOKALIKE_DOMAIN"), False)


def check_shortened_url(text: str, _meta: dict) -> Signal:
    """Message contains a known URL shortener."""
    return Signal("SHORTENED_URL", _w("SHORTENED_URL"), _has(_SHORTENED_RE, text))


def check_phone_in_message(text: str, meta: dict) -> Signal:
    """Message body contains a phone number different from the declared sender."""
    phones = _PHONE_RE.findall(text)
    sender = meta.get("sender", "")
    # Flatten tuple groups from findall
    flat = [p for group in phones for p in group if p]
    # If there's a phone number AND it's not the sender's, flag it
    matched = bool(flat) and not any(sender in p or p in sender for p in flat)
    return Signal("PHONE_IN_MESSAGE", _w("PHONE_IN_MESSAGE"), matched)


def check_generic_greeting(text: str, meta: dict) -> Signal:
    """Message uses a generic greeting, OR email checks flagged it."""
    from_email = meta.get("email_signals", {}).get("GENERIC_GREETING", False)
    return Signal(
        "GENERIC_GREETING",
        _w("GENERIC_GREETING"),
        _has(_GENERIC_GREETING_RE, text) or from_email,
    )


def check_email_mismatch(_text: str, meta: dict) -> Signal:
    """Sender and reply-to domains differ (email channel only)."""
    matched = meta.get("email_signals", {}).get("EMAIL_MISMATCH", False)
    return Signal("EMAIL_MISMATCH", _w("EMAIL_MISMATCH"), matched)


def check_display_name_spoof(_text: str, meta: dict) -> Signal:
    """Display name is a known brand but sending domain doesn't match."""
    matched = meta.get("email_signals", {}).get("DISPLAY_NAME_SPOOF", False)
    return Signal("DISPLAY_NAME_SPOOF", _w("DISPLAY_NAME_SPOOF"), matched)


# ---------------------------------------------------------------------------
# Aggregator
# ---------------------------------------------------------------------------

# All detectors in order
_ALL_DETECTORS = [
    check_suspicious_link,
    check_requests_otp_pin,
    check_urgency_language,
    check_impersonation,
    check_move_to_whatsapp,
    check_asks_for_money,
    check_fake_job_offer,
    check_advance_fee,
    check_romance_scam,
    check_lookalike_domain,
    check_shortened_url,
    check_phone_in_message,
    check_generic_greeting,
    check_email_mismatch,
    check_display_name_spoof,
]

# Category inference: which reason codes most strongly signal each category
_CATEGORY_SIGNALS: dict[str, list[str]] = {
    "fake_job_offer": ["FAKE_JOB_OFFER"],
    "advance_fee":    ["ADVANCE_FEE"],
    "romance_scam":   ["ROMANCE_SCAM"],
    "phishing":       ["REQUESTS_OTP_PIN", "EMAIL_MISMATCH", "DISPLAY_NAME_SPOOF"],
    "impersonation":  ["IMPERSONATION", "LOOKALIKE_DOMAIN", "SUSPICIOUS_LINK"],
}


def _infer_category(matched_codes: list[str]) -> str:
    """Pick the most likely category from the matched signal codes."""
    code_set = set(matched_codes)
    for category, signals in _CATEGORY_SIGNALS.items():
        if code_set & set(signals):
            return category
    return "unknown"


def _score_to_tier(score: int) -> str:
    for tier, (lo, hi) in _TIER_THRESHOLDS.items():
        if lo <= score <= hi:
            return tier
    return "HIGH_RISK"


def run_rules(text: str, channel: str = "web", meta: dict | None = None) -> RulesResult:
    """
    Run all signal detectors and return a RulesResult.

    Args:
        text:    The raw message text.
        channel: One of web | ussd | sms | email.
        meta:    Optional dict that may carry:
                   - mock_safe_browsing (bool, default True)
                   - safe_browsing_api_key (str | None)
                   - sender (str) — for phone-in-message check
                   - email_from, email_reply_to, email_subject — for email checks
                   - email_signals (dict) — pre-computed from email_checks.py

    Returns:
        RulesResult with score, reasons (≤3), advice (≤3), category.
    """
    if meta is None:
        meta = {}

    # Inject email signals into meta before running detectors
    if channel == "email" and "email_signals" not in meta:
        from backend.engine.email_checks import check_email_signals  # noqa: PLC0415
        meta["email_signals"] = check_email_signals(meta)

    # Run every detector
    all_signals: list[Signal] = [fn(text, meta) for fn in _ALL_DETECTORS]
    matched = [s for s in all_signals if s.matched]

    if not matched:
        return RulesResult(score=0, reasons=[], advice=[], category="unknown")

    # Score = sum of weights, capped at 100
    raw_score = sum(s.weight for s in matched)
    score = min(100, raw_score)

    # Top 3 signals by weight → reason codes
    top3 = sorted(matched, key=lambda s: s.weight, reverse=True)[:3]
    reasons = [s.code for s in top3]

    # Infer category from ALL matched codes (not just top 3)
    all_matched_codes = [s.code for s in matched]
    category = _infer_category(all_matched_codes)

    # Derive advice from category
    advice = _ADVICE_BY_CAT.get(category, _ADVICE_BY_CAT["unknown"])[:3]

    # Safety: HIGH_RISK must have ≥ 1 reason (already guaranteed since matched is non-empty)
    return RulesResult(score=score, reasons=reasons, advice=advice, category=category)
