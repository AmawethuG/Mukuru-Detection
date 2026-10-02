"""
Scam library router — GET /scams/library

Loads entries from data/scam_library.json and translates reason/advice
codes into human-readable strings using i18n/<lang>.json.

Query params:
  lang     — language code (default "en")
  category — optional filter by category slug
"""
from __future__ import annotations

import json
import os

from fastapi import APIRouter, Query

from backend.routers.ussd import _t   # reuse the same i18n helper

router = APIRouter()

# Load library data once at module import
_LIBRARY_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "scam_library.json"
)
with open(os.path.abspath(_LIBRARY_PATH), encoding="utf-8") as _f:
    _LIBRARY: list[dict] = json.load(_f)

_VALID_LANGS = {"en", "zu", "fr", "sw", "st", "hi", "nl", "pt"}


@router.get("/scams/library")
def get_library(
    lang: str = Query(default="en"),
    category: str | None = Query(default=None),
) -> dict:
    """Return scam library entries with translated reason and advice strings."""
    if lang not in _VALID_LANGS:
        lang = "en"

    entries = _LIBRARY
    if category:
        entries = [e for e in entries if e.get("category") == category]

    translated = []
    for entry in entries:
        red_flags_translated = [
            _t(f"reason.{code.lower()}", lang)
            for code in entry.get("red_flags", [])
        ]
        advice_translated = [
            _t(f"advice.{code.lower()}", lang)
            for code in entry.get("advice", [])
        ]
        translated.append({
            "id": entry["id"],
            "category": entry["category"],
            "category_label": _t(f"category.{entry['category']}", lang),
            "example_message": entry["example_message"],
            "red_flags": entry.get("red_flags", []),
            "red_flags_translated": red_flags_translated,
            "advice": entry.get("advice", []),
            "advice_translated": advice_translated,
        })

    return {"lang": lang, "entries": translated}
