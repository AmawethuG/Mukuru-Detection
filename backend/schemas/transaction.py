"""
Transaction-related Pydantic schemas.
"""
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class TransactionCheckRequest(BaseModel):
    recipient: str
    amount: Decimal
    currency: str
    country: str


class TransactionCheckResponse(BaseModel):
    score: int
    tier: str
    reasons: list[str]
    advice: list[str]
    checked_at: datetime


class SendRequest(BaseModel):
    recipient: str
    amount: Decimal
    currency: str
    country: str
    force: bool = False


class SendResponse(BaseModel):
    transaction_id: str
    status: str
    amount: str
    currency: str
    recipient: str
    sent_at: datetime
