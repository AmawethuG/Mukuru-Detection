"""
Panic router stub — full implementation in a later FEAT.
"""
from fastapi import APIRouter

from backend.schemas.common import SuccessResponse

router = APIRouter()


@router.post("/panic", response_model=SuccessResponse)
def panic() -> SuccessResponse:
    """Stub: acknowledge panic request."""
    return SuccessResponse(status="ok")
