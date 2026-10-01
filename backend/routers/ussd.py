"""
USSD router stub — full implementation in a later FEAT.
"""
from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

router = APIRouter()


@router.post("/ussd", response_class=PlainTextResponse)
def ussd_handler(body: dict = None) -> str:
    """Stub: returns a placeholder USSD menu."""
    return (
        "CON Mukuru Detection\n"
        "1. Check a message\n"
        "2. Scam examples\n"
        "3. My account\n"
        "4. Change language\n"
        "5. Exit"
    )
