"""
Transaction risk rules engine.

Pure Python — no FastAPI / SQLAlchemy imports.
Receives plain dicts (not ORM objects) so it's fully testable in isolation.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal

# Load weights from shared vocabulary
_VOCAB_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "shared", "reason_codes.json"
)
with open(os.path.abspath(_VOCAB_PATH), encoding="utf-8") as _fh:
    _VOCAB = json.load(_fh)

_TXN_REASONS: dict[str, dict] = _VOCAB["transaction_reason_codes"]
_ADVICE_BY_TXN: dict[str, list[str]] = _VOCAB["advice_by_transaction_reason"]
_TIER_THRESHOLDS = {"SAFE": (0, 39), "CAUTION": (40, 69), "HIGH_RISK": (70, 100)}


def _w(code: str) -> int:
    return _TXN_REASONS.get(code, {}).get("weight", 10)


def _to_decimal(value) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception:  # noqa: BLE001
        return Decimal("0")


@dataclass
class TxnSignal:
    code: str
    triggered: bool
    detail: str = ""


@dataclass
class TxnRiskResult:
    score: int
    tier: str
    reasons: list[str] = field(default_factory=list)
    advice: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Individual rule functions
# ---------------------------------------------------------------------------

def rule_new_recipient(proposed: dict, history: list[dict]) -> TxnSignal:
    """Recipient not seen in the past 90 days."""
    recipient = proposed.get("recipient", "").strip().lower()
    cutoff = datetime.utcnow() - timedelta(days=90)
    known = {
        t["recipient"].strip().lower()
        for t in history
        if _parse_dt(t.get("created_at")) >= cutoff
    }
    triggered = bool(recipient) and recipient not in known
    return TxnSignal("NEW_RECIPIENT", triggered)


def rule_unusual_amount(proposed: dict, history: list[dict]) -> TxnSignal:
    """Amount > 2× the user's 90-day average send amount (requires ≥ 5 past sends)."""
    amount = _to_decimal(proposed.get("amount", 0))
    cutoff = datetime.utcnow() - timedelta(days=90)
    past_sends = [
        _to_decimal(t["amount"])
        for t in history
        if t.get("direction") == "sent"
        and _parse_dt(t.get("created_at")) >= cutoff
    ]
    if len(past_sends) < 5:
        return TxnSignal("UNUSUAL_AMOUNT", False, "insufficient history")
    avg = sum(past_sends) / len(past_sends)
    triggered = avg > 0 and amount > avg * Decimal("2")
    return TxnSignal("UNUSUAL_AMOUNT", triggered, f"amount={amount}, avg={avg:.2f}")


def rule_round_large_amount(proposed: dict, _history: list[dict]) -> TxnSignal:
    """Amount ≥ 500 and divisible by 100 — classic coercion amount."""
    amount = _to_decimal(proposed.get("amount", 0))
    triggered = amount >= 500 and amount % 100 == 0
    return TxnSignal("ROUND_LARGE_AMOUNT", triggered)


def rule_rapid_repeat_sends(proposed: dict, history: list[dict]) -> TxnSignal:
    """≥ 3 sends to the same recipient in the past 24 hours."""
    recipient = proposed.get("recipient", "").strip().lower()
    cutoff = datetime.utcnow() - timedelta(hours=24)
    recent_to_same = [
        t for t in history
        if t.get("recipient", "").strip().lower() == recipient
        and t.get("direction") == "sent"
        and _parse_dt(t.get("created_at")) >= cutoff
    ]
    triggered = len(recent_to_same) >= 3
    return TxnSignal("RAPID_REPEAT_SENDS", triggered)


def rule_after_risky_message(
    _proposed: dict,
    _history: list[dict],
    recent_scans: list[dict],
    login_guard_active: bool = False,
) -> TxnSignal:
    """HIGH_RISK scan in the past 30 minutes, OR login guard raised an alert."""
    if login_guard_active:
        return TxnSignal("AFTER_RISKY_MESSAGE", True, "login_guard_active")
    cutoff = datetime.utcnow() - timedelta(minutes=30)
    triggered = any(
        s.get("tier") == "HIGH_RISK"
        and _parse_dt(s.get("created_at")) >= cutoff
        for s in recent_scans
    )
    return TxnSignal("AFTER_RISKY_MESSAGE", triggered)


def rule_new_country(proposed: dict, history: list[dict]) -> TxnSignal:
    """Destination country not present in the user's transaction history."""
    country = proposed.get("country", "").upper().strip()
    if not country or country == "OTHER":
        return TxnSignal("NEW_COUNTRY", False)
    known_countries = {t.get("country", "").upper() for t in history}
    return TxnSignal("NEW_COUNTRY", country not in known_countries)


# ---------------------------------------------------------------------------
# Aggregator
# ---------------------------------------------------------------------------

def check_transaction(
    proposed: dict,
    history: list[dict],
    recent_scans: list[dict] | None = None,
    login_guard_active: bool = False,
) -> TxnRiskResult:
    """
    Evaluate a proposed transaction against the user's history.

    Args:
        proposed:           {recipient, amount, currency, country}
        history:            List of past Transaction dicts (plain, not ORM)
        recent_scans:       List of recent ScanResult dicts
        login_guard_active: True if the user triggered the Login Guard alert

    Returns:
        TxnRiskResult with score, tier, reasons (≤3), advice (≤3)
    """
    if recent_scans is None:
        recent_scans = []

    signals = [
        rule_new_recipient(proposed, history),
        rule_unusual_amount(proposed, history),
        rule_round_large_amount(proposed, history),
        rule_rapid_repeat_sends(proposed, history),
        rule_after_risky_message(proposed, history, recent_scans, login_guard_active),
        rule_new_country(proposed, history),
    ]

    triggered = [s for s in signals if s.triggered]
    raw_score = sum(_w(s.code) for s in triggered)
    score = min(100, raw_score)

    tier = "SAFE"
    for t, (lo, hi) in _TIER_THRESHOLDS.items():
        if lo <= score <= hi:
            tier = t
            break

    # Top 3 triggered rules by weight
    top3 = sorted(triggered, key=lambda s: _w(s.code), reverse=True)[:3]
    reasons = [s.code for s in top3]

    # Collect advice from all triggered rules, deduplicate
    advice_set: list[str] = []
    for code in reasons:
        for adv in _ADVICE_BY_TXN.get(code, []):
            if adv not in advice_set:
                advice_set.append(adv)
    advice = advice_set[:3]

    return TxnRiskResult(score=score, tier=tier, reasons=reasons, advice=advice)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _parse_dt(value) -> datetime:
    """Parse a datetime or ISO string; return epoch on failure."""
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value))
    except Exception:  # noqa: BLE001
        return datetime.utcfromtimestamp(0)
