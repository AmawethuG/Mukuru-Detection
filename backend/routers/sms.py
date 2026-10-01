"""
SMS router stub — full implementation in a later FEAT.
"""
from fastapi import APIRouter

from backend.schemas.sms import SmsInboundRequest, SmsInboundResponse, SmsOutboxResponse

router = APIRouter()


@router.post("/sms/inbound", response_model=SmsInboundResponse)
def sms_inbound(body: SmsInboundRequest) -> SmsInboundResponse:
    """Stub: echoes received status."""
    return SmsInboundResponse(
        status="received",
        reply="Mukuru: SMS handler not yet implemented. Reply HELP for options.",
    )


@router.get("/sms/outbox", response_model=SmsOutboxResponse)
def sms_outbox(limit: int = 20, offset: int = 0) -> SmsOutboxResponse:
    """Stub: returns empty outbox."""
    return SmsOutboxResponse(messages=[], total=0, limit=limit, offset=offset)
