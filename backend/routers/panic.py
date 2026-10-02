"""
Panic router — POST /panic

Activates emergency / decoy mode for the current session.
After this call:
  - session.is_duress is set to True
  - All subsequent GET /accounts/me and GET /transactions/history return decoy data
  - A silent alert SMS is written to the trusted contact's simulated outbox
  - An AuditLog entry is created

The response shape is deliberately minimal — nothing reveals duress mode is active.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Tuple

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.audit import AuditLog
from backend.models.sms import SMSMessage
from backend.models.user import User, UserSession
from backend.routers.auth import get_current_user
from backend.routers.ussd import _t

router = APIRouter()


@router.post("/panic")
def trigger_panic(
    current: Tuple[User, UserSession] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Activate emergency mode. Response is identical regardless of previous state."""
    user, session = current
    now = datetime.utcnow()

    # Mark session as duress
    session.is_duress = True
    db.add(session)

    # Audit log — stored for later review
    db.add(AuditLog(
        id=str(uuid.uuid4()),
        user_id=user.id,
        event_type="panic_triggered",
        detail={"phone": user.phone, "timestamp": now.isoformat()},
    ))

    # Silent alert to trusted contact (simulated outbox only)
    if user.trusted_contact:
        alert_body = _t(
            "panic.trusted_contact.alert",
            user.language,
            timestamp=now.strftime("%Y-%m-%d %H:%M UTC"),
        )
        db.add(SMSMessage(
            id=str(uuid.uuid4()),
            user_id=user.id,   # stored in sender's outbox for demo visibility
            direction="outbound",
            sender=f"MukuruAlert→{user.trusted_contact}",
            body=alert_body,
            created_at=now,
        ))

    db.commit()
    # Return minimal response — no field reveals duress mode
    return {"status": "ok"}
