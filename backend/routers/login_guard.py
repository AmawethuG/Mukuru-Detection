"""
Login Guard router stub — full implementation in a later FEAT.
"""
from fastapi import APIRouter

router = APIRouter()


@router.post("/login-guard/event")
def login_guard_event(body: dict = None) -> dict:
    """Stub: returns a placeholder check-in question."""
    return {
        "checkin_question": "Has someone you met online asked you for money?",
        "status": "awaiting_answer",
    }
