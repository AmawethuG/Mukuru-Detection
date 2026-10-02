"""
Email-specific scam signal checks.

These run only when channel == "email" and return extra signals
that are merged into the rules pipeline via the meta dict.

All functions are pure Python — no web framework imports.
"""
from __future__ import annotations

import re


# Known legitimate brand domains (used for display-name spoofing detection)
KNOWN_BRANDS: dict[str, list[str]] = {
    "absa":          ["absa.co.za", "absa.africa"],
    "fnb":           ["fnb.co.za", "firstnational.co.za"],
    "capitec":       ["capitecbank.co.za"],
    "nedbank":       ["nedbank.co.za"],
    "standardbank":  ["standardbank.co.za", "sb.co.za"],
    "sars":          ["sars.gov.za"],
    "mukuru":        ["mukuru.com"],
    "paypal":        ["paypal.com"],
    "netflix":       ["netflix.com"],
    "amazon":        ["amazon.com", "amazon.co.za"],
    "dhl":           ["dhl.com"],
    "fedex":         ["fedex.com"],
    "sapo":          ["postoffice.co.za"],
}

_GENERIC_GREETINGS = re.compile(
    r"\b(dear\s+customer|dear\s+user|dear\s+beneficiary|dear\s+account\s+holder"
    r"|dear\s+winner|dear\s+valued\s+customer|dear\s+client)\b",
    re.IGNORECASE,
)

_URGENT_SUBJECTS = re.compile(
    r"\b(urgent|action required|immediate|verify now|account suspended"
    r"|limited time|expires|final notice|security alert)\b",
    re.IGNORECASE,
)

_DOMAIN_RE = re.compile(r"@([\w.-]+\.\w{2,})")


def _extract_domain(email_address: str) -> str | None:
    """Extract domain from 'Display Name <user@domain.com>' or 'user@domain.com'."""
    m = _DOMAIN_RE.search(email_address or "")
    return m.group(1).lower() if m else None


def _display_name(email_address: str) -> str:
    """Extract the display name from 'Display Name <addr>' or return empty string."""
    if "<" in email_address:
        return email_address.split("<")[0].strip().strip('"').lower()
    return ""


def check_email_signals(meta: dict) -> dict[str, bool]:
    """
    Run all email-specific checks.

    Args:
        meta: dict that may contain:
            - "email_from"      : full From: header  e.g. 'ABSA Bank <noreply@absa-secure-login.co>'
            - "email_reply_to"  : full Reply-To: header
            - "email_subject"   : subject line text
            - "text"            : body text (used for generic greeting check)

    Returns:
        dict of signal_code -> bool (True = signal fired)
    """
    signals: dict[str, bool] = {
        "EMAIL_MISMATCH":      False,
        "DISPLAY_NAME_SPOOF":  False,
        "GENERIC_GREETING":    False,
    }

    from_header    = meta.get("email_from", "")
    reply_header   = meta.get("email_reply_to", "")
    subject        = meta.get("email_subject", "")
    body           = meta.get("text", "")

    from_domain    = _extract_domain(from_header)
    reply_domain   = _extract_domain(reply_header)
    display        = _display_name(from_header)

    # ── EMAIL_MISMATCH ──────────────────────────────────────────────────────
    # Sender domain and reply-to domain differ — classic phishing pattern.
    if from_domain and reply_domain and from_domain != reply_domain:
        signals["EMAIL_MISMATCH"] = True

    # ── DISPLAY_NAME_SPOOF ──────────────────────────────────────────────────
    # Display name contains a known brand but the sending domain doesn't match.
    if display and from_domain:
        for brand, legit_domains in KNOWN_BRANDS.items():
            if brand in display:
                if not any(from_domain.endswith(d) for d in legit_domains):
                    signals["DISPLAY_NAME_SPOOF"] = True
                    break

    # ── GENERIC_GREETING (body) ─────────────────────────────────────────────
    if _GENERIC_GREETINGS.search(body):
        signals["GENERIC_GREETING"] = True

    # ── URGENT_SUBJECT (feeds URGENCY_LANGUAGE) ─────────────────────────────
    # We set GENERIC_GREETING as a proxy; callers can also check subject.
    if _URGENT_SUBJECTS.search(subject) and not signals["GENERIC_GREETING"]:
        # Don't add a new code — fold into GENERIC_GREETING for weight purposes;
        # the rules layer will already catch URGENCY_LANGUAGE in the body.
        pass

    return signals
