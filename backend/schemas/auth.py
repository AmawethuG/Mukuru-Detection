"""
Auth-related Pydantic schemas.
"""
import re
from datetime import datetime
from typing import Any

from pydantic import BaseModel, field_validator, model_validator

VALID_LANGUAGES = {"en", "zu", "fr", "sw", "st", "hi", "nl", "pt"}
_E164_RE = re.compile(r"^\+[1-9]\d{6,14}$")
_PIN_RE = re.compile(r"^\d{4}$")


class RegisterRequest(BaseModel):
    phone: str
    country: str
    language: str = "en"
    pin: str
    duress_pin: str
    trusted_contact: str | None = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not _E164_RE.match(v):
            raise ValueError("Phone must be in E.164 format (e.g. +27831234567)")
        return v

    @field_validator("country")
    @classmethod
    def validate_country(cls, v: str) -> str:
        if len(v) != 2 or not v.isalpha():
            raise ValueError("Country must be a 2-character ISO code")
        return v.upper()

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        if v not in VALID_LANGUAGES:
            raise ValueError(f"Language must be one of: {', '.join(sorted(VALID_LANGUAGES))}")
        return v

    @field_validator("pin", "duress_pin")
    @classmethod
    def validate_pin(cls, v: str) -> str:
        if not _PIN_RE.match(v):
            raise ValueError("PIN must be exactly 4 digits")
        return v

    @field_validator("trusted_contact")
    @classmethod
    def validate_trusted_contact(cls, v: str | None) -> str | None:
        if v is not None and not _E164_RE.match(v):
            raise ValueError("trusted_contact must be in E.164 format")
        return v

    @model_validator(mode="after")
    def pins_must_differ(self) -> "RegisterRequest":
        if self.pin == self.duress_pin:
            raise ValueError("pin and duress_pin must be different")
        return self


class LoginRequest(BaseModel):
    phone: str
    pin: str


class UserOut(BaseModel):
    id: str
    phone: str
    country: str
    language: str
    created_at: datetime

    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    token: str
    user: UserOut


class AccountResponse(BaseModel):
    id: str
    phone: str
    country: str
    language: str
    balance: str
    currency: str
    recent_transactions: list[Any]
    created_at: datetime

    model_config = {"from_attributes": True}


class PatchAccountRequest(BaseModel):
    language: str

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        if v not in VALID_LANGUAGES:
            raise ValueError(f"Language must be one of: {', '.join(sorted(VALID_LANGUAGES))}")
        return v
