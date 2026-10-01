"""
Decoy account generator for duress mode.

Given a user_id, deterministically generates a plausible-looking account
with synthetic transactions. The output is seeded from the user_id so the
same user always sees the same decoy data (important: do not change the
seed algorithm without updating the duress tests).

NO FastAPI imports in this file.
"""
import hashlib
import random
import uuid
from datetime import datetime, timedelta
from typing import Any

_RECIPIENTS = [
    "Mom",
    "Grocery",
    "Airtime",
    "School fees",
    "Transport",
    "Water & Lights",
    "Church",
    "Rent",
]


def _deterministic_uuid(seed_int: int, index: int) -> str:
    """Generate a deterministic UUID-like string from a seed and index."""
    # Combine seed and index into a stable bytes string, then hash it
    raw = hashlib.sha256(f"{seed_int}:{index}".encode()).hexdigest()
    # Format as UUID: 8-4-4-4-12
    return f"{raw[:8]}-{raw[8:12]}-{raw[12:16]}-{raw[16:20]}-{raw[20:32]}"


def generate_decoy_account(user_id: str) -> dict[str, Any]:
    """
    Return a dict matching the AccountResponse shape populated with
    deterministic synthetic data derived from user_id.
    """
    # Derive a stable integer seed from the user_id
    seed = int(hashlib.sha256(user_id.encode()).hexdigest(), 16) & 0xFFFFFFFF
    rng = random.Random(seed)

    num_txns = rng.randint(8, 15)
    now = datetime.utcnow()

    transactions: list[dict[str, Any]] = []
    for i in range(num_txns):
        days_ago = rng.randint(1, 120)
        txn_dt = now - timedelta(days=days_ago, hours=rng.randint(0, 23))
        amount = rng.randint(2, 20) * 10  # R20–R200 in R10 steps
        direction = "received" if rng.random() < 0.20 else "sent"
        recipient = rng.choice(_RECIPIENTS)

        transactions.append(
            {
                "id": _deterministic_uuid(seed, i),
                "recipient": recipient,
                "amount": f"{amount:.2f}",
                "currency": "ZAR",
                "direction": direction,
                "created_at": txn_dt,
            }
        )

    # Sort most recent first
    transactions.sort(key=lambda t: t["created_at"], reverse=True)

    # Generate a deterministic created_at for the decoy user (1-2 years ago)
    created_days_ago = rng.randint(365, 730)
    created_at = now - timedelta(days=created_days_ago)

    return {
        "id": _deterministic_uuid(seed, 9999),
        "phone": "+2700000" + str(seed)[:7],
        "country": "ZA",
        "language": "en",
        "balance": "0.00",
        "currency": "ZAR",
        "recent_transactions": transactions,
        "created_at": created_at,
    }
