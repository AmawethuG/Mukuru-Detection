"""
Scan-related Pydantic schemas.
"""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, field_validator


class ScanRequest(BaseModel):
    text: str
    channel: Literal["web", "ussd", "sms", "email"]
    user_id: str | None = None

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        if len(v) > 10000:
            raise ValueError("text must not exceed 10 000 characters")
        return v


class ScanResponse(BaseModel):
    id: str
    score: int
    tier: str
    category: str
    reasons: list[str]
    advice: list[str]
    explanation: str
    explanation_source: str
    detected_language: str
    scanned_at: datetime
