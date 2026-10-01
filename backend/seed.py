"""
Database seed script.

Idempotent: safe to run multiple times. If the demo users already exist,
their data is left unchanged.

Run from repo root:
    python backend/seed.py
"""
import hashlib
import os
import sys
import uuid
from datetime import datetime, timedelta

# Ensure the repo root is on the Python path when run as a script
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

# Override DATABASE_URL to an absolute path before importing anything else
_DB_PATH = os.path.join(_REPO_ROOT, "mukuru.db")
os.environ.setdefault("DATABASE_URL", f"sqlite:///{_DB_PATH}")

from passlib.context import CryptContext  # noqa: E402

from backend.database import SessionLocal, init_db  # noqa: E402
from backend.models.audit import AuditLog  # noqa: F401 noqa: E402
from backend.models.scan import ScanResult  # noqa: E402
from backend.models.sms import SMSMessage  # noqa: E402
from backend.models.transaction import Transaction  # noqa: E402
from backend.models.user import User  # noqa: E402

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

SMS_OUTBOX_BODY = (
    "Scam of the Week: Watch out for fake job offers asking for R500 registration fees. "
    "Real jobs never ask for upfront payment. Stay safe!"
)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def seed_blessing(db) -> None:
    """Create Blessing's user, transactions, scan result, and SMS."""
    phone = "+27831234567"
    if db.query(User).filter(User.phone == phone).first():
        print("Blessing already exists — skipping.")
        return

    blessing = User(
        id=str(uuid.uuid4()),
        phone=phone,
        pin_hash=pwd_context.hash("1234"),
        duress_pin_hash=pwd_context.hash("9999"),
        country="ZA",
        language="zu",
        trusted_contact="+27821234567",
    )
    db.add(blessing)
    db.flush()

    # 12 transactions over the past 90 days
    recipients_za = ["Mom", "Grocery", "Airtime", "Mom", "Grocery", "Airtime",
                     "School fees", "Transport", "Water & Lights", "Mom", "Church", "Grocery"]
    amounts_za = [50, 120, 30, 80, 95, 29, 200, 40, 150, 60, 100, 75]
    now = datetime.utcnow()

    for i, (rec, amt) in enumerate(zip(recipients_za, amounts_za)):
        days_ago = 5 + i * 7  # spread over ~90 days
        txn_dt = now - timedelta(days=days_ago, hours=i % 12)
        db.add(Transaction(
            id=str(uuid.uuid4()),
            user_id=blessing.id,
            recipient=rec,
            amount=amt,
            currency="ZAR",
            country="ZA",
            status="completed",
            direction="sent",
            created_at=txn_dt,
        ))

    # One HIGH_RISK scan result
    db.add(ScanResult(
        id=str(uuid.uuid4()),
        user_id=blessing.id,
        text_hash=_sha256("demo_fake_job_seed"),
        channel="sms",
        score=85,
        tier="HIGH_RISK",
        category="fake_job_offer",
        reasons=["FAKE_JOB_OFFER", "ASKS_FOR_MONEY", "MOVE_TO_WHATSAPP"],
        advice=["DO_NOT_PAY_UPFRONT", "VERIFY_SENDER", "REPORT_SCAM"],
        explanation_source="rules",
        detected_language="en",
        created_at=now - timedelta(minutes=10),
    ))

    # Outbound SMS
    db.add(SMSMessage(
        id=str(uuid.uuid4()),
        user_id=blessing.id,
        direction="outbound",
        sender="MukuruAlert",
        body=SMS_OUTBOX_BODY,
        created_at=now,
    ))

    db.commit()
    print("Blessing seeded.")


def seed_tendai(db) -> None:
    """Create Tendai's user, transactions, and SMS."""
    phone = "+263771234567"
    if db.query(User).filter(User.phone == phone).first():
        print("Tendai already exists — skipping.")
        return

    tendai = User(
        id=str(uuid.uuid4()),
        phone=phone,
        pin_hash=pwd_context.hash("1234"),
        duress_pin_hash=pwd_context.hash("9999"),
        country="ZW",
        language="en",
    )
    db.add(tendai)
    db.flush()

    # 10 remittance transactions
    zw_recipients = ["Family", "Mum", "Sister", "Dad", "Cousin",
                     "Uncle", "Brother", "Aunt", "Friend", "Niece"]
    amounts_usd = [30, 50, 25, 40, 20, 60, 35, 45, 55, 70]
    now = datetime.utcnow()

    for i, (rec, amt) in enumerate(zip(zw_recipients, amounts_usd)):
        days_ago = 3 + i * 8
        txn_dt = now - timedelta(days=days_ago, hours=(i * 3) % 24)
        db.add(Transaction(
            id=str(uuid.uuid4()),
            user_id=tendai.id,
            recipient=rec,
            amount=amt,
            currency="USD",
            country="ZW",
            status="completed",
            direction="sent",
            created_at=txn_dt,
        ))

    # Outbound SMS
    db.add(SMSMessage(
        id=str(uuid.uuid4()),
        user_id=tendai.id,
        direction="outbound",
        sender="MukuruAlert",
        body=SMS_OUTBOX_BODY,
        created_at=now,
    ))

    db.commit()
    print("Tendai seeded.")


def main() -> None:
    print(f"Initialising database at: {_DB_PATH}")
    init_db()
    db = SessionLocal()
    try:
        seed_blessing(db)
        seed_tendai(db)
        print("Seed complete.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
