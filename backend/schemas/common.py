"""
Shared response schemas.
"""
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    error: str
    message: str
    field: str | None = None


class SuccessResponse(BaseModel):
    status: str = "ok"
