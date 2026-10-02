"""
Risk engine rules tests.

One positive + one negative example per signal.
Integration tests for full run_rules() pipeline.
"""
import pytest

from backend.engine.rules import (
    run_rules,
    check_suspicious_link,
    check_requests_otp_pin,
    check_urgency_language,
    check_impersonation,
    check_move_to_whatsapp,
    check_asks_for_money,
    check_fake_job_offer,
    check_advance_fee,
    check_romance_scam,
    check_lookalike_domain,
    check_shortened_url,
    check_phone_in_message,
    check_generic_greeting,
    check_email_mismatch,
    check_display_name_spoof,
)

META = {}  # empty meta for most tests


# ── Individual signal tests ──────────────────────────────────────────────────

def test_suspicious_link_positive():
    sig = check_suspicious_link("Visit http://absa-secure-login.co to verify.", META)
    assert sig.matched

def test_suspicious_link_negative():
    sig = check_suspicious_link("Visit https://absa.co.za for banking.", META)
    assert not sig.matched

def test_requests_otp_pin_positive():
    sig = check_requests_otp_pin("Please enter your OTP to continue.", META)
    assert sig.matched

def test_requests_otp_pin_negative():
    sig = check_requests_otp_pin("Your order has been delivered.", META)
    assert not sig.matched

def test_urgency_language_positive():
    sig = check_urgency_language("Act now or your account expires within 24 hours!", META)
    assert sig.matched

def test_urgency_language_negative():
    sig = check_urgency_language("Your package will arrive tomorrow.", META)
    assert not sig.matched

def test_impersonation_positive():
    sig = check_impersonation("ABSA Bank: please verify your account.", META)
    assert sig.matched

def test_impersonation_negative():
    sig = check_impersonation("Hi, how are you doing today?", META)
    assert not sig.matched

def test_move_to_whatsapp_positive():
    sig = check_move_to_whatsapp("Contact us on WhatsApp at +27611223344.", META)
    assert sig.matched

def test_move_to_whatsapp_negative():
    sig = check_move_to_whatsapp("We'll email you the confirmation shortly.", META)
    assert not sig.matched

def test_asks_for_money_positive():
    sig = check_asks_for_money("Please transfer R500 to account 123456.", META)
    assert sig.matched

def test_asks_for_money_negative():
    sig = check_asks_for_money("Your balance is R1200.", META)
    assert not sig.matched

def test_fake_job_offer_positive():
    sig = check_fake_job_offer("Work from home job! Pay R300 registration fee to start.", META)
    assert sig.matched

def test_fake_job_offer_negative():
    sig = check_fake_job_offer("The meeting is scheduled for 3pm tomorrow.", META)
    assert not sig.matched

def test_advance_fee_positive():
    sig = check_advance_fee("You have won a prize! Pay a processing fee of $50 to claim.", META)
    assert sig.matched

def test_advance_fee_negative():
    sig = check_advance_fee("Your DSTV subscription renews next month.", META)
    assert not sig.matched

def test_romance_scam_positive():
    sig = check_romance_scam("My darling, I love you. I am stuck at customs. Please send $200.", META)
    assert sig.matched

def test_romance_scam_negative():
    sig = check_romance_scam("See you at the office party on Friday.", META)
    assert not sig.matched

def test_lookalike_domain_positive():
    sig = check_lookalike_domain("Visit https://absa-secure-login.co for your banking.", META)
    assert sig.matched

def test_lookalike_domain_negative():
    sig = check_lookalike_domain("Visit https://absa.co.za for your banking.", META)
    assert not sig.matched

def test_shortened_url_positive():
    sig = check_shortened_url("Click here: https://bit.ly/3xYz9a to verify.", META)
    assert sig.matched

def test_shortened_url_negative():
    sig = check_shortened_url("See https://www.mukuru.com for more details.", META)
    assert not sig.matched

def test_phone_in_message_positive():
    meta_with_sender = {"sender": "+27800000000"}
    sig = check_phone_in_message("Call us now on +27611223344 to process your application.", meta_with_sender)
    assert sig.matched

def test_phone_in_message_negative():
    # No phone number in message at all
    sig = check_phone_in_message("Your parcel has been delivered.", META)
    assert not sig.matched

def test_generic_greeting_positive():
    sig = check_generic_greeting("Dear Customer, your account has been flagged.", META)
    assert sig.matched

def test_generic_greeting_negative():
    sig = check_generic_greeting("Hi Blessing, your transfer is complete.", META)
    assert not sig.matched

def test_email_mismatch_positive():
    meta = {"email_signals": {"EMAIL_MISMATCH": True, "DISPLAY_NAME_SPOOF": False, "GENERIC_GREETING": False}}
    sig = check_email_mismatch("", meta)
    assert sig.matched

def test_email_mismatch_negative():
    meta = {"email_signals": {"EMAIL_MISMATCH": False, "DISPLAY_NAME_SPOOF": False, "GENERIC_GREETING": False}}
    sig = check_email_mismatch("", meta)
    assert not sig.matched

def test_display_name_spoof_positive():
    meta = {"email_signals": {"EMAIL_MISMATCH": False, "DISPLAY_NAME_SPOOF": True, "GENERIC_GREETING": False}}
    sig = check_display_name_spoof("", meta)
    assert sig.matched

def test_display_name_spoof_negative():
    meta = {"email_signals": {"EMAIL_MISMATCH": False, "DISPLAY_NAME_SPOOF": False, "GENERIC_GREETING": False}}
    sig = check_display_name_spoof("", meta)
    assert not sig.matched


# ── run_rules() integration tests ────────────────────────────────────────────

FAKE_JOB_SMS = (
    "Congratulations! You have been selected for a work-from-home job paying R5000/week. "
    "To activate your position, pay a R500 registration fee via EFT. "
    "WhatsApp +27600000001 to confirm."
)

BANK_OTP = "Your ABSA OTP is 483921. Valid for 5 minutes. Do not share this code with anyone."

PHISHING = (
    "ABSA BANK: Your account has been suspended. Verify now at http://absa-secure-login.co "
    "to avoid permanent closure."
)


def test_fake_job_is_high_risk():
    result = run_rules(FAKE_JOB_SMS, channel="sms")
    assert result.score >= 70, f"Expected HIGH_RISK score, got {result.score}"
    assert result.category == "fake_job_offer", f"Expected fake_job_offer, got {result.category}"
    assert len(result.reasons) >= 1, "Must have at least one reason"
    assert len(result.reasons) <= 3, "Must not have more than 3 reasons"


def test_bank_otp_is_not_fake_job():
    result = run_rules(BANK_OTP, channel="sms")
    assert result.category != "fake_job_offer", "Bank OTP should not be classified as fake job offer"


def test_high_risk_always_has_reason():
    """Safety invariant: HIGH_RISK must have ≥ 1 reason."""
    result = run_rules(FAKE_JOB_SMS, channel="sms")
    if result.score >= 70:
        assert len(result.reasons) >= 1, "HIGH_RISK result has no reasons"


def test_reasons_never_exceed_three():
    result = run_rules(FAKE_JOB_SMS, channel="sms")
    assert len(result.reasons) <= 3, f"Too many reasons: {result.reasons}"


def test_safe_message_low_score():
    result = run_rules("Hi, are we still meeting at 3pm?", channel="sms")
    assert result.score < 40, f"Benign message scored too high: {result.score}"


def test_phishing_detected():
    result = run_rules(PHISHING, channel="sms")
    assert result.score >= 40, f"Phishing message not flagged: {result.score}"
    assert result.category in ("phishing", "impersonation")
