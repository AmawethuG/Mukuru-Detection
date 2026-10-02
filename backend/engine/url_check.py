"""
URL extraction and safety checking.

Mock mode (default): checks against a local blocklist.
Live mode: calls Google Safe Browsing Lookup API v4.

The API key and mode are passed in by the caller (from settings),
keeping this module free of FastAPI/config imports.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Local blocklist (used in mock mode)
# ---------------------------------------------------------------------------
LOCAL_BLOCKLIST: set[str] = {
    "absa-secure-login.co",
    "absa-verify.net",
    "absa-secure-login.com",
    "fnb-secure.xyz",
    "fnb-verify.co.za",
    "sars-refund-portal.net",
    "sars-refund-portal.co.za",
    "mukuru-verify.com",
    "capitec-alert.co",
    "capitec-secure.xyz",
    "nedbank-verify.co",
    "standardbank-verify.net",
    "mtn-verify.co",
    "vodacom-account-verify.co.za",
    "paypal-secure-check.com",
    "netflix-billing-update.co",
    "gov-relief-grant.co.za",
    "sapo-collect.co.za",
    "visa-protect-za.com",
    "telkom-account.xyz",
    "jobs-za.xyz",
    "banque-secure-verification.fr",
    "abnamro-secure.nl",
    "posbverify.net",
}

# Known URL shorteners — presence alone is a mild signal
SHORTENER_DOMAINS: set[str] = {
    "bit.ly", "tinyurl.com", "t.co", "goo.gl",
    "ow.ly", "rb.gy", "short.io", "is.gd", "buff.ly",
}

# Regex to pull URLs out of arbitrary text
_URL_RE = re.compile(
    r"https?://[^\s\]\)>\"']+|"          # http(s):// URLs
    r"www\.[a-z0-9][-a-z0-9.]+\.[a-z]{2,}[^\s\]\)>\"']*",  # bare www. URLs
    re.IGNORECASE,
)

# Regex to extract just the domain from a URL
_DOMAIN_RE = re.compile(
    r"(?:https?://)?(?:www\.)?([a-z0-9][-a-z0-9.]+\.[a-z]{2,}).*",
    re.IGNORECASE,
)


@dataclass
class UrlCheckResult:
    urls_found: list[str] = field(default_factory=list)
    any_malicious: bool = False
    any_shortened: bool = False
    source: str = "mock"   # "mock" | "safe_browsing"


def extract_urls(text: str) -> list[str]:
    """Return a list of URLs found in *text*."""
    return _URL_RE.findall(text)


def _domain(url: str) -> str:
    """Extract the bare domain from a URL string."""
    m = _DOMAIN_RE.match(url.lower())
    return m.group(1) if m else url.lower()


def check_urls(
    urls: list[str],
    mock: bool = True,
    api_key: str | None = None,
) -> UrlCheckResult:
    """
    Check a list of URLs for malicious indicators.

    Args:
        urls:    URLs to check (from extract_urls).
        mock:    If True, use LOCAL_BLOCKLIST. If False, call Safe Browsing API.
        api_key: Google Safe Browsing API key (required when mock=False).

    Returns:
        UrlCheckResult with any_malicious set if a threat was found.
    """
    if not urls:
        return UrlCheckResult(urls_found=[])

    domains = [_domain(u) for u in urls]
    any_shortened = any(d in SHORTENER_DOMAINS for d in domains)

    if mock:
        any_malicious = any(d in LOCAL_BLOCKLIST for d in domains)
        return UrlCheckResult(
            urls_found=urls,
            any_malicious=any_malicious,
            any_shortened=any_shortened,
            source="mock",
        )

    # --- Live Google Safe Browsing Lookup API v4 ---
    # Only send URLs — never the surrounding message text.
    try:
        import httpx  # noqa: PLC0415

        payload = {
            "client": {"clientId": "mukuru-detection", "clientVersion": "1.0.0"},
            "threatInfo": {
                "threatTypes": [
                    "MALWARE", "SOCIAL_ENGINEERING",
                    "UNWANTED_SOFTWARE", "POTENTIALLY_HARMFUL_APPLICATION",
                ],
                "platformTypes": ["ANY_PLATFORM"],
                "threatEntryTypes": ["URL"],
                "threatEntries": [{"url": u} for u in urls],
            },
        }
        resp = httpx.post(
            f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={api_key}",
            json=payload,
            timeout=5.0,
        )
        resp.raise_for_status()
        data = resp.json()
        any_malicious = bool(data.get("matches"))
        return UrlCheckResult(
            urls_found=urls,
            any_malicious=any_malicious,
            any_shortened=any_shortened,
            source="safe_browsing",
        )
    except Exception:  # noqa: BLE001 — degrade gracefully
        # Fall back to mock if the API call fails
        any_malicious = any(d in LOCAL_BLOCKLIST for d in domains)
        return UrlCheckResult(
            urls_found=urls,
            any_malicious=any_malicious,
            any_shortened=any_shortened,
            source="mock_fallback",
        )
