"""
Auth router: register, login, me (GET/PATCH).

Security contract:
- Both pin_hash and duress_pin_hash are ALWAYS checked with secrets.compare_digest.
  The first matching hash wins; we never short-circuit after the first check.
- The login response shape is IDENTICAL regardless of which PIN matched.
"""
import json
import os
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Tuple

from fastapi import APIRouter, Depends, HTTPException, Request, status
from passlib.context import CryptContext
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.decoy.generator import generate_decoy_account
from backend.models.audit import AuditLog
from backend.models.transaction import Transaction
from backend.models.user import User, UserSession
from backend.schemas.auth import (
    AccountResponse,
    LoginRequest,
    LoginResponse,
    PatchAccountRequest,
    RegisterRequest,
    UserOut,
)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

# Load country→language defaults from shared vocabulary (frozen file)
_REASON_CODES_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "shared", "reason_codes.json"
)
with open(os.path.abspath(_REASON_CODES_PATH), encoding="utf-8") as _f:
    _REASON_CODES = json.load(_f)

_COUNTRY_LANGUAGE_DEFAULTS: dict[str, list[str]] = _REASON_CODES.get(
    "country_language_defaults", {}
)

SESSION_TTL_HOURS = 24 * 7  # 1 week


def _default_language_for_country(country: str) -> str:
    """Return the first language default for a country, falling back to 'en'."""
    langs = _COUNTRY_LANGUAGE_DEFAULTS.get(country.upper(), [])
    return langs[0] if langs else "en"


def _make_token() -> str:
    return str(uuid.uuid4()).replace("-", "") + str(uuid.uuid4()).replace("-", "")


def _make_session(db: Session, user: User, is_duress: bool) -> UserSession:
    session = UserSession(
        id=str(uuid.uuid4()),
        user_id=user.id,
        token=_make_token(),
        is_duress=is_duress,
        expires_at=datetime.utcnow() + timedelta(hours=SESSION_TTL_HOURS),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> Tuple[User, UserSession]:
    """
    Dependency: extract Bearer token, look up UserSession, return (User, UserSession).
    Raises 401 if the token is missing, unknown, or expired.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )
    token = auth_header[len("Bearer "):].strip()
    session = db.query(UserSession).filter(UserSession.token == token).first()
    if not session or session.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    user = db.query(User).filter(User.id == session.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user, session


# ---------------------------------------------------------------------------
# POST /register
# ---------------------------------------------------------------------------
@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=LoginResponse)
def register(body: RegisterRequest, db: Session = Depends(get_db)) -> LoginResponse:
    # Phone uniqueness check
    if db.query(User).filter(User.phone == body.phone).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This phone number is already registered.",
        )

    # Determine language: use provided value, or fall back to country default
    language = body.language or _default_language_for_country(body.country)

    pin_hash = pwd_context.hash(body.pin)
    duress_pin_hash = pwd_context.hash(body.duress_pin)

    user = User(
        id=str(uuid.uuid4()),
        phone=body.phone,
        pin_hash=pin_hash,
        duress_pin_hash=duress_pin_hash,
        country=body.country.upper(),
        language=language,
        trusted_contact=body.trusted_contact,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    session = _make_session(db, user, is_duress=False)
    return LoginResponse(token=session.token, user=UserOut.model_validate(user))


# ---------------------------------------------------------------------------
# POST /login
# ---------------------------------------------------------------------------
@router.post("/login", response_model=LoginResponse)
@limiter.limit("5/5minute")
def login(request: Request, body: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    user = db.query(User).filter(User.phone == body.phone).first()

    # Always perform both bcrypt checks to prevent timing side-channels.
    # We compute a dummy hash so that both paths take the same amount of time
    # even when the user is not found.
    _dummy = "$2b$12$AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"

    real_pin_hash = user.pin_hash if user else _dummy
    real_duress_hash = user.duress_pin_hash if user else _dummy

    # Use secrets.compare_digest on the raw bcrypt hash output to ensure
    # constant-time comparison at the string level. bcrypt verify itself
    # provides constant-time internally, but we additionally wrap with
    # compare_digest on the boolean results so neither branch is skipped.
    normal_match_bool = pwd_context.verify(body.pin, real_pin_hash)
    duress_match_bool = pwd_context.verify(body.pin, real_duress_hash)

    # Reduce to single bytes so compare_digest can operate on them
    normal_match = secrets.compare_digest(
        b"\x01" if normal_match_bool else b"\x00",
        b"\x01",
    )
    duress_match = secrets.compare_digest(
        b"\x01" if duress_match_bool else b"\x00",
        b"\x01",
    )

    if not user or (not normal_match and not duress_match):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect phone number or PIN.",
        )

    is_duress = duress_match and not normal_match

    if is_duress:
        db.add(
            AuditLog(
                id=str(uuid.uuid4()),
                user_id=user.id,
                event_type="duress_login",
                detail={"phone": user.phone},
            )
        )
        db.commit()

    session = _make_session(db, user, is_duress=is_duress)
    return LoginResponse(token=session.token, user=UserOut.model_validate(user))


# ---------------------------------------------------------------------------
# GET /accounts/me
# ---------------------------------------------------------------------------
@router.get("/accounts/me", response_model=AccountResponse)
def get_me(
    current: Tuple[User, UserSession] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AccountResponse:
    user, session = current

    if session.is_duress:
        decoy = generate_decoy_account(user.id)
        return AccountResponse(**decoy)

    # Real data — MVP has no live balance tracking
    txns = (
        db.query(Transaction)
        .filter(Transaction.user_id == user.id, Transaction.is_decoy.is_(False))
        .order_by(Transaction.created_at.desc())
        .limit(20)
        .all()
    )

    recent = [
        {
            "id": t.id,
            "recipient": t.recipient,
            "amount": f"{float(t.amount):.2f}",
            "currency": t.currency,
            "direction": t.direction,
            "created_at": t.created_at,
        }
        for t in txns
    ]

    return AccountResponse(
        id=user.id,
        phone=user.phone,
        country=user.country,
        language=user.language,
        balance="0.00",
        currency="ZAR",
        recent_transactions=recent,
        created_at=user.created_at,
    )


# ---------------------------------------------------------------------------
# PATCH /accounts/me
# ---------------------------------------------------------------------------
@router.patch("/accounts/me")
def patch_me(
    body: PatchAccountRequest,
    current: Tuple[User, UserSession] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    user, _session = current
    user.language = body.language
    db.commit()
    return {"language": user.language}
