"""
Thin helper that loads read-only data from shared/reason_codes.json.
Import from here so other modules don't each open the file separately.
"""
import json, os

_PATH = os.path.join(os.path.dirname(__file__), "..", "shared", "reason_codes.json")

with open(os.path.abspath(_PATH), encoding="utf-8") as _f:
    _VOCAB: dict = json.load(_f)

TIERS:           dict = _VOCAB["tiers"]
CATEGORIES:      dict = _VOCAB["categories"]
MSG_REASONS:     dict = _VOCAB["message_reason_codes"]
TXN_REASONS:     dict = _VOCAB["transaction_reason_codes"]
ADVICE_CODES:    dict = _VOCAB["advice_codes"]
ADVICE_BY_CAT:   dict = _VOCAB["advice_by_category"]
ADVICE_BY_TXN:   dict = _VOCAB["advice_by_transaction_reason"]
CHANNELS:        list = _VOCAB["channels"]
COUNTRY_LANG:    dict = _VOCAB["country_language_defaults"]
