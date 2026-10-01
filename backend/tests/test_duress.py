"""
Duress login tests.

Tests:
(a) POST /login with normal pin and duress_pin return identical JSON keys (sorted)
(b) GET /accounts/me with duress session returns balance='0.00'
(c) Decoy recent_transactions contains no real transaction IDs
(d) AuditLog has a duress_login row after duress login
"""
import uuid

import pytest
from fastapi.testclient import TestClient

# Override DATABASE_URL is done in conftest.py before any app import


def _register_and_seed(client: TestClient) -> dict:
    """Register a test user and seed a real transaction, return user info."""
    resp = client.post(
        "/register",
        json={
            "phone": "+27801234567",
            "country": "ZA",
            "language": "en",
            "pin": "1234",
            "duress_pin": "9999",
        },
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    return data  # {token, user}


def _login(client: TestClient, phone: str, pin: str) -> dict:
    resp = client.post("/login", json={"phone": phone, "pin": pin})
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    return resp.json()


# ---------------------------------------------------------------------------
# (a) Normal login and duress login return identical JSON key sets
# ---------------------------------------------------------------------------
def test_login_response_keys_identical(client: TestClient):
    _register_and_seed(client)

    normal_resp = client.post("/login", json={"phone": "+27801234567", "pin": "1234"})
    duress_resp = client.post("/login", json={"phone": "+27801234567", "pin": "9999"})

    assert normal_resp.status_code == 200
    assert duress_resp.status_code == 200

    normal_keys = sorted(normal_resp.json().keys())
    duress_keys = sorted(duress_resp.json().keys())

    assert normal_keys == duress_keys, (
        f"Key mismatch:\n  normal: {normal_keys}\n  duress: {duress_keys}"
    )

    # Also check nested user keys are identical
    normal_user_keys = sorted(normal_resp.json()["user"].keys())
    duress_user_keys = sorted(duress_resp.json()["user"].keys())
    assert normal_user_keys == duress_user_keys


# ---------------------------------------------------------------------------
# (b) GET /accounts/me with duress session returns balance='0.00'
# ---------------------------------------------------------------------------
def test_duress_session_returns_zero_balance(client: TestClient):
    _register_and_seed(client)
    duress_data = _login(client, "+27801234567", "9999")
    token = duress_data["token"]

    me_resp = client.get("/accounts/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200, me_resp.text
    body = me_resp.json()

    assert body["balance"] == "0.00", f"Expected balance '0.00', got '{body['balance']}'"


# ---------------------------------------------------------------------------
# (c) Decoy recent_transactions contains no real transaction IDs
# ---------------------------------------------------------------------------
def test_decoy_transactions_are_not_real(client: TestClient, db_session):
    from backend.models.transaction import Transaction

    reg_data = _register_and_seed(client)
    user_id = reg_data["user"]["id"]
    normal_token = reg_data["token"]

    # Add a real transaction for the user
    real_txn = Transaction(
        id=str(uuid.uuid4()),
        user_id=user_id,
        recipient="Mom",
        amount=50.00,
        currency="ZAR",
        country="ZA",
        status="completed",
        direction="sent",
    )
    db_session.add(real_txn)
    db_session.commit()

    # Get real transaction IDs from DB
    real_ids = {t.id for t in db_session.query(Transaction).filter(Transaction.user_id == user_id).all()}

    # Login with duress PIN and get /accounts/me
    duress_data = _login(client, "+27801234567", "9999")
    duress_token = duress_data["token"]

    me_resp = client.get("/accounts/me", headers={"Authorization": f"Bearer {duress_token}"})
    assert me_resp.status_code == 200

    decoy_txn_ids = {t["id"] for t in me_resp.json()["recent_transactions"]}

    overlap = real_ids & decoy_txn_ids
    assert not overlap, (
        f"Decoy transactions contain real DB IDs: {overlap}"
    )


# ---------------------------------------------------------------------------
# (d) AuditLog has a duress_login row after duress login
# ---------------------------------------------------------------------------
def test_audit_log_records_duress_login(client: TestClient, db_session):
    from backend.models.audit import AuditLog

    _register_and_seed(client)
    _login(client, "+27801234567", "9999")

    # There should be exactly one duress_login audit entry
    entries = (
        db_session.query(AuditLog)
        .filter(AuditLog.event_type == "duress_login")
        .all()
    )
    assert len(entries) >= 1, "Expected at least one duress_login audit log entry"
    assert entries[0].event_type == "duress_login"
