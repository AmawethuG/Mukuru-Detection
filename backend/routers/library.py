"""
Scam library router stub — full implementation in a later FEAT.
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/scams/library")
def scam_library(lang: str = "en", category: str | None = None) -> dict:
    """Stub: returns an empty library."""
    return {"lang": lang, "entries": []}
