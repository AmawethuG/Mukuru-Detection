"""
Lightweight language detection wrapper.

Maps langdetect's output to the 8 language codes we support.
Falls back to "en" on any error — never raises.
"""
from __future__ import annotations

# Supported language codes (matches i18n/ filenames)
SUPPORTED = {"en", "zu", "fr", "sw", "st", "hi", "nl", "pt"}

# langdetect uses slightly different codes for some languages
_REMAP: dict[str, str] = {
    "af": "en",   # Afrikaans → English fallback
    "zu": "zu",
    "xh": "zu",   # Xhosa → isiZulu (closest we support)
    "sw": "sw",
    "fr": "fr",
    "nl": "nl",
    "pt": "pt",
    "hi": "hi",
    "en": "en",
    "st": "st",
    "so": "sw",   # Somali → Swahili fallback
    "mg": "fr",   # Malagasy → French fallback
}


def detect_language(text: str) -> str:
    """Return a supported language code for *text*. Never raises."""
    if not text or len(text.strip()) < 10:
        return "en"
    try:
        from langdetect import detect, LangDetectException  # type: ignore
        raw = detect(text)
        return _REMAP.get(raw, "en" if raw not in SUPPORTED else raw)
    except Exception:  # noqa: BLE001
        return "en"
