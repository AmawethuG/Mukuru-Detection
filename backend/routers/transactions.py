"""
Transactions router.

POST /transactions/check  — pre-send risk check (no money moves)
POST /transactions/send   — execute transfer (duress-safe)
GET  /transactions/history — real or decoy history
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Tuple

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.decoy.generator import generate_decoy_account
from backend.engine.transaction_rules import check_transaction
from backend.models.scan import ScanResult
from backend.models.transaction import Transaction
from backend.models.user import User, UserSession
from backend.routers.auth import get_current_user
from backend.schemas.transaction import (
    SendRequest,
    SendResponse,
    TransactionCheckRequest,
    TransactionCheckResponse,
)

router = APIRouter()


def _txn_to_dict(t: Transaction) -> dict:
    """Serialize a Transaction ORM row to a plain dict for the engine."""
    return {
        "id": t.id,
        "recipient": t.recipient,
        "amount": float(t.amount),
        "currency": t.currency,
        "country": t.country,
        "direction": t.direction,
        "status": t.status,
        "created_at": t.created_at,
    }


def _scan_to_dict(s: ScanResult) -> dict:
    """Serialize a ScanResult ORM row to a plain dict for the engine."""
    return {
        "id": s.id,
        "tier": s.tier,
        "score": s.score,
        "category": s.category,
        "created_at": s.created_at,
    }


def _load_user_context(user_id: str, db: Session) -> tuple[list[dict], list[dict], bool]:
    """Return (transaction_history, recent_scans, login_guard_active) for a user."""
    from datetime import timedelta  # noqa: PLC0415
    from backend.models.user import User as UserModel  # noqa: PLC0415

    history = [
        _txn_to_dict(t)
        for t in db.query(Transaction)
        .filter(Transaction.user_id == user_id, Transaction.is_decoy.is_(False))
        .order_by(Transaction.created_at.desc())
        .limit(100)
        .all()
    ]

    cutoff = datetime.utcnow() - timedelta(minutes=30)
    recent_scans = [
        _scan_to_dict(s)
        for s in db.query(ScanResult)
        .filter(ScanResult.user_id == user_id, ScanResult.created_at >= cutoff)
        .all()
    ]

    user_row = db.query(UserModel).filter(UserModel.id == user_id).first()
    login_guard_active = bool(
        user_row
        and user_row.login_guard_alert_until
        and user_row.login_guard_alert_until > datetime.utcnow()
    )
    return history, recent_scans, login_guard_active


# ── POST /transactions/check ────────────────────────────────────────────────

@router.post("/transactions/check", response_model=TransactionCheckResponse)
def check_txn(
    body: TransactionCheckRequest,
    current: Tuple[User, UserSession] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TransactionCheckResponse:
    """Run pre-send risk check. No money moves."""
    user, _session = current
    proposed = {
        "recipient": body.recipient,
        "amount": float(body.amount),
        "currency": body.currency,
        "country": body.country,
    }
    history, recent_scans, login_guard_active = _load_user_context(user.id, db)
    result = check_transaction(proposed, history, recent_scans, login_guard_active)
    return TransactionCheckResponse(
        score=result.score,
        tier=result.tier,
        reasons=result.reasons,
        advice=result.advice,
        checked_at=datetime.utcnow(),
    )


# ── POST /transactions/send ─────────────────────────────────────────────────

@router.post("/transactions/send", response_model=SendResponse)
def send_txn(
    body: SendRequest,
    current: Tuple[User, UserSession] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SendResponse:
    """
    Execute a transfer.
    - Duress session → writes is_decoy=True; returns identical success shape.
    - HIGH_RISK + force=False → 422 with risk details.
    """
    user, session = current
    proposed = {
        "recipient": body.recipient,
        "amount": float(body.amount),
        "currency": body.currency,
        "country": body.country,
    }

    # Always run the risk check (even in duress mode, to keep response timing consistent)
    history, recent_scans, login_guard_active = _load_user_context(user.id, db)
    risk = check_transaction(proposed, history, recent_scans, login_guard_active)

    # Block HIGH_RISK transfers unless the user explicitly forces it
    if risk.tier == "HIGH_RISK" and not body.force and not session.is_duress:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "high_risk_transfer_blocked",
                "score": risk.score,
                "tier": risk.tier,
                "reasons": risk.reasons,
                "advice": risk.advice,
            },
        )

    # In duress mode: record a decoy transaction and return a convincing success response
    txn_id = str(uuid.uuid4())
    txn = Transaction(
        id=txn_id,
        user_id=user.id,
        recipient=body.recipient,
        amount=float(body.amount),
        currency=body.currency,
        country=body.country,
        direction="sent",
        status="completed",
        is_decoy=session.is_duress,  # real money only moves when is_decoy=False
    )
    db.add(txn)
    db.commit()

    return SendResponse(
        transaction_id=txn_id,
        status="completed",
        amount=f"{float(body.amount):.2f}",
        currency=body.currency,
        recipient=body.recipient,
        sent_at=datetime.utcnow(),
    )


# ── GET /transactions/history ───────────────────────────────────────────────

@router.get("/transactions/history")
def txn_history(
    limit: int = 20,
    offset: int = 0,
    current: Tuple[User, UserSession] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Return real or decoy transaction history."""
    user, session = current

    if session.is_duress:
        decoy = generate_decoy_account(user.id)
        txns = decoy["recent_transactions"][offset: offset + limit]
        return {"transactions": txns, "total": len(decoy["recent_transactions"]),
                "limit": limit, "offset": offset}

    rows = (
        db.query(Transaction)
        .filter(Transaction.user_id == user.id, Transaction.is_decoy.is_(False))
        .order_by(Transaction.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    total = (
        db.query(Transaction)
        .filter(Transaction.user_id == user.id, Transaction.is_decoy.is_(False))
        .count()
    )
    txns = [
        {
            "id": t.id,
            "recipient": t.recipient,
            "amount": f"{float(t.amount):.2f}",
            "currency": t.currency,
            "direction": t.direction,
            "country": t.country,
            "status": t.status,
            "created_at": t.created_at.isoformat(),
        }
        for t in rows
    ]
    return {"transactions": txns, "total": total, "limit": limit, "offset": offset}
