"""
Login Guard router — POST /login-guard/event

Simulates a dating-app check-in. When the user answers "yes" to the
romance-scam check-in question, we raise their risk state for 60 minutes.
This feeds into AFTER_RISKY_MESSAGE in the transaction rules engine.

The UI must clearly label this as a simulation.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Tuple

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.audit import AuditLog
from backend.models.user import User, UserSession
from backend.routers.auth import get_current_user
from backend.shared_vocab import ADVICE_BY_CAT

router = APIRouter()

# Romance scam advice codes (from reason_codes.json)
_ROMANCE_ADVICE = ADVICE_BY_CAT.get("romance_scam", ["TRUST_YOUR_INSTINCTS", "DO_NOT_PAY_UPFRONT", "BLOCK_AND_REPORT"])

LOGIN_GUARD_WINDOW_MINUTES = 60


class LoginGuardRequest(BaseModel):
    event_type: str = "dating_app_login"
    answer: str | None = None   # "yes" | "no" | None (first call = no answer yet)


@router.post("/login-guard/event")
def login_guard_event(
    body: LoginGuardRequest,
    current: Tuple[User, UserSession] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    Step 1 — no answer yet: return the check-in question.
    Step 2 — answer provided:
      "yes" → raise risk state, return romance-scam advice.
      "no"  → return reassurance.
    """
    user, _session = current

    # First call — just return the question
    if body.answer is None:
        return {
            "status": "awaiting_answer",
            "checkin_question": "Has someone you met online asked you for money?",
        }

    if body.answer.lower() == "yes":
        # Raise the user's risk state for LOGIN_GUARD_WINDOW_MINUTES
        user.login_guard_alert_until = datetime.utcnow() + timedelta(
            minutes=LOGIN_GUARD_WINDOW_MINUTES
        )
        db.add(AuditLog(
            id=str(uuid.uuid4()),
            user_id=user.id,
            event_type="login_guard_alert",
            detail={"event_type": body.event_type, "window_minutes": LOGIN_GUARD_WINDOW_MINUTES},
        ))
        db.commit()
        return {
            "status": "risk_raised",
            "advice": _ROMANCE_ADVICE,
            "explanation": (
                "This is a common romance scam pattern. "
                "People you meet online who quickly ask for money are very often scammers. "
                "Do not send money to anyone you have not met in person."
            ),
        }

    # answer == "no"
    db.commit()
    return {
        "status": "ok",
        "advice": [],
        "explanation": "Good. If anything changes, use this tool to raise an alert.",
    }
