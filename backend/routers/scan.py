"""
Scan router stub — full implementation in FEAT-002.
"""
import uuid
from datetime import datetime

from fastapi import APIRouter

from backend.schemas.scan import ScanRequest, ScanResponse

router = APIRouter()


@router.post("/scan", response_model=ScanResponse)
def scan_message(body: ScanRequest) -> ScanResponse:
    """Stub: returns a placeholder SAFE result."""
    return ScanResponse(
        id=str(uuid.uuid4()),
        score=0,
        tier="SAFE",
        category="unknown",
        reasons=[],
        advice=[],
        explanation="Scan engine not yet implemented.",
        explanation_source="rules",
        detected_language="en",
        scanned_at=datetime.utcnow(),
    )
