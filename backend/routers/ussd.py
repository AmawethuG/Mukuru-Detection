"""
USSD router — POST /ussd

Implements a stateless Africa's Talking-style USSD state machine.
All state is encoded in the `text` parameter (inputs joined by `*`).
No server-side USSD session state is stored between requests.

Response prefixes:
  CON <screen_text>  → session continues, show input field
  END <screen_text>  → session over, hide input field

Language strings come from i18n/<lang>.json loaded via _t().
Scan results are fetched live from the risk engine for option 1.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.engine.rules import run_rules
from backend.engine.language_detect import detect_language
from backend.models.user import User, UserSession
from backend.models.transaction import Transaction
from backend.routers.auth import _make_session, pwd_context
from backend.schemas.auth import _E164_RE, _PIN_RE

router = APIRouter()

# ── i18n loader ─────────────────────────────────────────────────────────────
_I18N_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "i18n")
_CACHE: dict[str, dict] = {}

def _load_lang(lang: str) -> dict:
    if lang not in _CACHE:
        path = os.path.join(_I18N_DIR, f"{lang}.json")
        fallback = os.path.join(_I18N_DIR, "en.json")
        try:
            with open(path, encoding="utf-8") as f:
                _CACHE[lang] = json.load(f)
        except FileNotFoundError:
            if lang not in _CACHE:
                with open(fallback, encoding="utf-8") as f:
                    _CACHE[lang] = json.load(f)
    return _CACHE.get(lang, _CACHE.get("en", {}))

def _t(key: str, lang: str, **kwargs) -> str:
    """Translate key in lang, fall back to en, then to key itself."""
    strings = _load_lang(lang)
    en_strings = _load_lang("en")
    val = strings.get(key) or en_strings.get(key) or key
    for k, v in kwargs.items():
        val = val.replace("{" + k + "}", str(v))
    return val

# ── Country / language maps ──────────────────────────────────────────────────
COUNTRIES = [
    ("ZA", "South Africa"),
    ("ZW", "Zimbabwe"),
    ("MZ", "Mozambique"),
    ("CD", "DR Congo"),
    ("KE", "Kenya"),
]
COUNTRY_DEFAULT_LANG = {"ZA": "zu", "ZW": "en", "MZ": "pt", "CD": "fr", "KE": "sw"}

LANGUAGES = [
    ("en", "English"),
    ("zu", "isiZulu"),
    ("fr", "Français"),
    ("sw", "Kiswahili"),
    ("st", "Sesotho"),
    ("hi", "Hindi"),
    ("nl", "Nederlands"),
    ("pt", "Português"),
]

# ── Request schema ───────────────────────────────────────────────────────────
class UssdRequest(BaseModel):
    sessionId: str = ""
    serviceCode: str = "*123#"
    phoneNumber: str = ""
    text: str = ""

# ── Helpers ──────────────────────────────────────────────────────────────────
def _menu(lang: str) -> str:
    return (
        f"{_t('ussd.menu.title', lang)}\n"
        f"{_t('ussd.menu.check_message', lang)}\n"
        f"{_t('ussd.menu.scam_examples', lang)}\n"
        f"{_t('ussd.menu.my_account', lang)}\n"
        f"{_t('ussd.menu.change_language', lang)}\n"
        f"{_t('ussd.menu.exit', lang)}"
    )

def _lang_menu(lang: str) -> str:
    lines = [_t('ussd.change_language.prompt', lang)]
    for i, (code, name) in enumerate(LANGUAGES, 1):
        lines.append(f"{i}. {name}")
    return "\n".join(lines)

def _country_menu(lang: str) -> str:
    lines = [_t('ussd.register.choose_country', lang)]
    for i, (_, name) in enumerate(COUNTRIES, 1):
        lines.append(f"{i}. {name}")
    lines.append(f"{len(COUNTRIES)+1}. Other")
    return "\n".join(lines)

def _scan_result_short(text: str, lang: str) -> str:
    """Run a scan and return a ≤160-char USSD-friendly result."""
    result = run_rules(text, channel="ussd")
    tier_key = f"tier.{result.tier.lower()}"
    tier_label = _t(tier_key, lang)
    if not result.reasons:
        return _t("ussd.check_message.result.safe", lang)
    top_reason = _t(f"reason.{result.reasons[0].lower()}", lang)
    top_advice = _t(f"advice.{result.advice[0].lower()}", lang) if result.advice else ""
    if result.tier == "HIGH_RISK":
        template = _t("ussd.check_message.result.high_risk", lang)
    elif result.tier == "CAUTION":
        template = _t("ussd.check_message.result.caution", lang)
    else:
        return _t("ussd.check_message.result.safe", lang)
    msg = template.replace("{reason}", top_reason).replace("{advice}", top_advice)
    return msg[:155]  # stay within 160-char USSD limit

# ── State machine ─────────────────────────────────────────────────────────────
@router.post("/ussd", response_class=PlainTextResponse)
def ussd_handler(body: UssdRequest, db: Session = Depends(get_db)) -> str:
    """
    Stateless USSD handler.
    State is derived entirely from the accumulated `text` field.
    """
    inputs = body.text.split("*") if body.text else []
    phone = body.phoneNumber or ""

    # ── Welcome screen ──────────────────────────────────────────────────────
    if not inputs or inputs == [""]:
        return (
            "CON " +
            _t("ussd.welcome", "en") + "\n" +
            _t("ussd.new_or_login", "en")
        )

    choice = inputs[0]

    # ════════════════════════════════════════════════════════════════════════
    # PATH 1: New user registration
    # ════════════════════════════════════════════════════════════════════════
    if choice == "1":
        depth = len(inputs)

        if depth == 1:
            return "CON " + _t("ussd.enter_phone", "en")

        reg_phone = inputs[1]

        if depth == 2:
            return "CON " + _country_menu("en")

        country_idx = inputs[2]
        try:
            ci = int(country_idx) - 1
            country_code, _ = (COUNTRIES[ci] if ci < len(COUNTRIES) else ("OTHER", "Other"))
        except (ValueError, IndexError):
            country_code = "OTHER"
        lang = COUNTRY_DEFAULT_LANG.get(country_code, "en")

        if depth == 3:
            return "CON " + _lang_menu(lang)

        lang_idx = inputs[3]
        try:
            li = int(lang_idx) - 1
            lang = LANGUAGES[li][0] if 0 <= li < len(LANGUAGES) else "en"
        except (ValueError, IndexError):
            lang = "en"

        if depth == 4:
            return "CON " + _t("ussd.register.set_pin", lang)

        pin = inputs[4]

        if depth == 5:
            return "CON " + _t("ussd.register.confirm_pin", lang)

        pin_confirm = inputs[5]
        if pin != pin_confirm:
            return "CON " + _t("ussd.register.pin_mismatch", lang) + "\n" + _t("ussd.register.set_pin", lang)

        if depth == 6:
            return "CON " + _t("ussd.register.set_duress_pin", lang)

        duress_pin = inputs[6]

        if depth == 7:
            return "CON " + _t("ussd.register.confirm_duress_pin", lang)

        if depth >= 8:
            duress_confirm = inputs[7]
            if duress_pin != duress_confirm:
                return "CON " + _t("ussd.register.pin_mismatch", lang) + "\n" + _t("ussd.register.set_duress_pin", lang)
            if pin == duress_pin:
                return "CON " + _t("ussd.register.pins_same", lang)
            if not _E164_RE.match(reg_phone):
                return "END Invalid phone number. Please try again."
            if not _PIN_RE.match(pin) or not _PIN_RE.match(duress_pin):
                return "END " + _t("auth.error.pin_length", lang)

            # Check if already registered
            existing = db.query(User).filter(User.phone == reg_phone).first()
            if existing:
                return "END " + _t("auth.error.phone_taken", lang)

            # Create user
            new_user = User(
                id=str(__import__("uuid").uuid4()),
                phone=reg_phone,
                pin_hash=pwd_context.hash(pin),
                duress_pin_hash=pwd_context.hash(duress_pin),
                country=country_code,
                language=lang,
            )
            db.add(new_user)
            db.commit()
            return "CON " + _t("ussd.register.success", lang) + "\n\n" + _menu(lang)

    # ════════════════════════════════════════════════════════════════════════
    # PATH 2: Login
    # ════════════════════════════════════════════════════════════════════════
    if choice == "2":
        depth = len(inputs)

        if depth == 1:
            return "CON " + _t("ussd.enter_phone", "en")

        login_phone = inputs[1]

        if depth == 2:
            return "CON " + _t("ussd.enter_pin", "en")

        login_pin = inputs[2]

        # Attempt login (constant-time, same as REST auth)
        import secrets  # noqa: PLC0415
        user = db.query(User).filter(User.phone == login_phone).first()
        _dummy = "$2b$12$AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        pin_hash = user.pin_hash if user else _dummy
        duress_hash = user.duress_pin_hash if user else _dummy
        normal_ok = pwd_context.verify(login_pin, pin_hash)
        duress_ok = pwd_context.verify(login_pin, duress_hash)
        normal_match = secrets.compare_digest(b"\x01" if normal_ok else b"\x00", b"\x01")
        duress_match = secrets.compare_digest(b"\x01" if duress_ok else b"\x00", b"\x01")

        if not user or (not normal_match and not duress_match):
            return "CON " + _t("ussd.login_failed", "en") + "\n" + _t("ussd.enter_pin", "en")

        lang = user.language

        if depth == 3:
            # Logged in — show main menu
            return "CON " + _menu(lang)

        menu_choice = inputs[3]

        # ── Option 1: Check a message ──────────────────────────────────────
        if menu_choice == "1":
            if depth == 4:
                return "CON " + _t("ussd.check_message.prompt", lang)
            message_text = "*".join(inputs[4:])  # rejoin in case message had *
            result_text = _scan_result_short(message_text, lang)
            return "END " + result_text

        # ── Option 2: Scam examples ────────────────────────────────────────
        if menu_choice == "2":
            return "END " + _t("ussd.scam_examples.title", lang)

        # ── Option 3: My account ───────────────────────────────────────────
        if menu_choice == "3":
            is_duress = duress_match and not normal_match
            if is_duress:
                return "END " + _t("ussd.account.balance", lang,
                                   balance="R0.00", last_send="N/A")
            last_txn = (
                db.query(Transaction)
                .filter(Transaction.user_id == user.id, Transaction.is_decoy.is_(False))
                .order_by(Transaction.created_at.desc())
                .first()
            )
            last_str = f"R{float(last_txn.amount):.0f} to {last_txn.recipient}" if last_txn else "None"
            return "END " + _t("ussd.account.balance", lang,
                               balance="R0.00", last_send=last_str)

        # ── Option 4: Change language ──────────────────────────────────────
        if menu_choice == "4":
            if depth == 4:
                return "CON " + _lang_menu(lang)
            new_lang_idx = inputs[4]
            try:
                li = int(new_lang_idx) - 1
                new_lang = LANGUAGES[li][0] if 0 <= li < len(LANGUAGES) else lang
            except (ValueError, IndexError):
                return "END " + _t("ussd.error.invalid_option", lang)
            user.language = new_lang
            db.commit()
            return "END " + _t("ussd.change_language.success", new_lang,
                               language=dict(LANGUAGES).get(new_lang, new_lang))

        # ── Option 5: Exit ─────────────────────────────────────────────────
        if menu_choice == "5":
            return "END " + _t("ussd.exit", lang)

        return "END " + _t("ussd.error.invalid_option", "en")

    # ── Unknown initial choice ─────────────────────────────────────────────
    return "CON " + _t("ussd.error.invalid_option", "en") + "\n" + _t("ussd.new_or_login", "en")
