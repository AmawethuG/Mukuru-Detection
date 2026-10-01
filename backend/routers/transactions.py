"""
Transactions router stub — full implementation in a later FEAT.
"""
import uuid
from datetime import datetime

from fastapi import APIRouter, Request

from backend.schemas.transaction import (
    SendRequest,
    SendResponse,
    TransactionCheckRequest,
    TransactionCheckResponse,
)

router = APIRouter()


@router.post("/transactions/check", response_model=TransactionCheckResponse)
def check_transaction(body: TransactionCheckRequest) -> TransactionCheckResponse:
    """Stub: returns a placeholder SAFE result."""
    return TransactionCheckResponse(
        score=0,
        tier="SAFE",
        reasons=[],
        advice=[],
        checked_at=datetime.utcnow(),
    )


@router.post("/transactions/send", response_model=SendResponse)
def send_transaction(body: SendRequest) -> SendResponse:
    """Stub: records a placeholder completed transfer."""
    return SendResponse(
        transaction_id=str(uuid.uuid4()),
        status="completed",
        amount=f"{body.amount:.2f}",
        currency=body.currency,
        recipient=body.recipient,
        sent_at=datetime.utcnow(),
    )


@router.get("/transactions/history")
def transaction_history(limit: int = 20, offset: int = 0) -> dict:
    """Stub: returns empty history."""
    return {"transactions": [], "total": 0, "limit": limit, "offset": offset}
