"""
SMS router.

POST /sms/inbound  — receive an SMS command from the simulator
GET  /sms/outbox   — return the user's SMS outbox (most recent first)

Commands (case-insensitive, leading/trailing space stripped):
  "1" or "result"          → format last scan result for this user
  "SCAM <message text>"    → run scan on the text, append result to outbox
  "HELP"                   → append help text to outbox
  anything else            → append unknown-command response to outbox

SMS results are kept ≤160 chars for Latin-script languages.
Hindi (hi) gets a shorter limit (~70 chars) because UCS-2 encoding halves capacity.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Tuple

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.engine.rules import run_rules
from backend.models.scan import ScanResult
from backend.models.sms import SMSMessage
from backend.models.user import User, UserSession
from backend.routers.auth import get_current_user
from backend.routers.ussd import _t  # reuse the same i18n helper

router = APIRouter()

_SMS_LIMIT = 155   # safe limit for GSM-7 (160 − a few chars for sender tag)
_UCS2_LIMIT = 67   # Hindi / Devanagari via UCS-2


def _char_limit(lang: str) -> int:
    return _UCS2_LIMIT if lang == "hi" else _SMS_LIMIT


def _format_scan_result(scan: ScanResult, lang: str) -> str:
    """Format a ScanResult as a short SMS string."""
    limit = _char_limit(lang)
    tier_label = _t(f"tier.{scan.tier.lower()}", lang)
    reason = _t(f"reason.{scan.reasons[0].lower()}", lang) if scan.reasons else ""
    advice = _t(f"advice.{scan.advice[0].lower()}", lang) if scan.advice else ""
    msg = _t("sms.inbound.result", lang,
             tier=tier_label, reason=reason, advice=advice)
    return msg[:limit]


def _append_outbound(db: Session, user_id: str, body: str) -> None:
    """Write one outbound SMS message to the outbox."""
    db.add(SMSMessage(
        id=str(uuid.uuid4()),
        user_id=user_id,
        direction="outbound",
        sender="MukuruAlert",
        body=body,
        created_at=datetime.utcnow(),
    ))
    db.commit()


class SMSInboundRequest(BaseModel):
    from_: str | None = None   # phone number of sender (optional for anon)
    body: str

    model_config = {"populate_by_name": True}

    # Accept "from" as a JSON key (it's a Python reserved word)
    @classmethod
    def model_validate(cls, obj, *args, **kwargs):
        if isinstance(obj, dict) and "from" in obj and "from_" not in obj:
            obj = {**obj, "from_": obj.pop("from")}
        return super().model_validate(obj, *args, **kwargs)


@router.post("/sms/inbound")
def sms_inbound(
    body: SMSInboundRequest,
    current: Tuple[User, UserSession] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    user, _session = current
    lang = user.language
    cmd = body.body.strip()

    # ── Command: 1 / result ─────────────────────────────────────────────────
    if cmd in ("1", "result", "RESULT"):
        last_scan = (
            db.query(ScanResult)
            .filter(ScanResult.user_id == user.id)
            .order_by(ScanResult.created_at.desc())
            .first()
        )
        if not last_scan:
            reply = _t("sms.inbound.unknown_command", lang)
        else:
            reply = _format_scan_result(last_scan, lang)

    # ── Command: SCAM <text> ────────────────────────────────────────────────
    elif cmd.upper().startswith("SCAM "):
        message_text = cmd[5:].strip()
        if message_text:
            result = run_rules(message_text, channel="sms")
            # Build a fake ScanResult object (not persisted) for formatting
            class _FakeScan:
                tier = result.tier or "SAFE"
                reasons = result.reasons
                advice = result.advice
            reply = _format_scan_result(_FakeScan(), lang)  # type: ignore[arg-type]
        else:
            reply = _t("sms.inbound.help", lang)

    # ── Command: HELP ───────────────────────────────────────────────────────
    elif cmd.upper() == "HELP":
        reply = _t("sms.inbound.help", lang)

    # ── Unknown ─────────────────────────────────────────────────────────────
    else:
        reply = _t("sms.inbound.unknown_command", lang)

    _append_outbound(db, user.id, reply)
    return {"status": "received", "reply": reply}


@router.get("/sms/outbox")
def sms_outbox(
    limit: int = 20,
    offset: int = 0,
    current: Tuple[User, UserSession] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Return the user's SMS outbox, most recent first."""
    user, _session = current
    rows = (
        db.query(SMSMessage)
        .filter(SMSMessage.user_id == user.id)
        .order_by(SMSMessage.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    total = db.query(SMSMessage).filter(SMSMessage.user_id == user.id).count()
    messages = [
        {
            "id": m.id,
            "direction": m.direction,
            "sender": m.sender,
            "body": m.body,
            "created_at": m.created_at.isoformat(),
        }
        for m in rows
    ]
    return {"messages": messages, "total": total, "limit": limit, "offset": offset}
