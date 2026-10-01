"""
SMS-related Pydantic schemas.
"""
from datetime import datetime

from pydantic import BaseModel, Field


class SmsInboundRequest(BaseModel):
    from_number: str = Field(alias="from")
    body: str
    timestamp: datetime | None = None

    model_config = {"populate_by_name": True}


class SmsInboundResponse(BaseModel):
    status: str
    reply: str


class SmsMessage(BaseModel):
    id: str
    direction: str
    sender: str
    body: str
    created_at: datetime


class SmsOutboxResponse(BaseModel):
    messages: list[SmsMessage]
    total: int
    limit: int
    offset: int
