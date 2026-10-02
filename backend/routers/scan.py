"""
Scan router — POST /scan

Pipeline:
  1. Detect language
  2. Extract + check URLs (mock or Safe Browsing)
  3. Run rules engine  → rules_score, reasons, advice, category
  4. Run classifier    → classifier_score
  5. Blend scores      → final score
  6. Optional LLM fallback when score is inconclusive (30-60)
  7. Persist ScanResult (hashed text only — never raw)
  8. Return ScanResponse
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime
from typing import Tuple

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import get_db
from backend.engine.classifier import predict_scam_probability
from backend.engine.language_detect import detect_language
from backend.engine.rules import run_rules
from backend.engine.url_check import extract_urls, check_urls
from backend.models.scan import ScanResult
from backend.routers.auth import get_current_user
from backend.schemas.scan import ScanRequest, ScanResponse

router = APIRouter()


def _tier(score: int) -> str:
    if score >= 70:
        return "HIGH_RISK"
    if score >= 40:
        return "CAUTION"
    return "SAFE"


def _blend(rules_score: int, classifier_score: int) -> int:
    blended = settings.RULES_WEIGHT * rules_score + settings.CLASSIFIER_WEIGHT * classifier_score
    return max(0, min(100, round(blended)))


def _try_llm(text: str, lang: str) -> tuple[str, str]:
    """Call LLM fallback if enabled. Returns (explanation, source)."""
    if not settings.LLM_ENABLED:
        return ("", "rules")
    try:
        import httpx  # noqa: PLC0415
        headers = {"Authorization": f"Bearer {settings.LLM_API_KEY}", "Content-Type": "application/json"}
        base = settings.LLM_BASE_URL or "https://api.openai.com"
        payload = {
            "model": settings.LLM_MODEL,
            "messages": [
                {"role": "system", "content": (
                    f"You are a scam detection assistant. Classify the following message and "
                    f"give a one-sentence explanation in language code '{lang}'. "
                    "Reply with only the explanation sentence."
                )},
                {"role": "user", "content": text[:500]},
            ],
            "max_tokens": 80,
        }
        resp = httpx.post(f"{base}/v1/chat/completions", json=payload, headers=headers, timeout=8.0)
        resp.raise_for_status()
        explanation = resp.json()["choices"][0]["message"]["content"].strip()
        return (explanation, "llm")
    except Exception:  # noqa: BLE001
        return ("", "rules")


@router.post("/scan", response_model=ScanResponse)
def scan_message(
    body: ScanRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> ScanResponse:
    """
    Scan a message for scam signals.
    Authentication is optional — anonymous scans are allowed.
    """
    # Resolve optional user_id from body or auth header
    user_id: str | None = body.user_id
    if not user_id:
        try:
            user, _session = get_current_user(request, db)
            user_id = user.id
        except Exception:  # noqa: BLE001
            pass  # anonymous scan — fine

    # 1. Language detection
    lang = detect_language(body.text)

    # 2. URL check — only URLs are sent externally, never message text
    urls = extract_urls(body.text)
    url_result = check_urls(
        urls,
        mock=settings.MOCK_SAFE_BROWSING,
        api_key=settings.SAFE_BROWSING_API_KEY or None,
    )

    # 3. Rules engine
    meta: dict = {
        "mock_safe_browsing": settings.MOCK_SAFE_BROWSING,
        "safe_browsing_api_key": settings.SAFE_BROWSING_API_KEY or None,
        # Pass pre-computed URL result so check_suspicious_link doesn't call check_urls again
        "_url_result": url_result,
    }
    rules_result = run_rules(body.text, channel=body.channel, meta=meta)

    # 4. Classifier
    classifier_prob = predict_scam_probability(body.text)
    classifier_score = round(classifier_prob * 100)

    # 5. Blend
    blended = _blend(rules_result.score, classifier_score)

    # Safety: HIGH_RISK requires at least 1 reason
    if blended >= 70 and not rules_result.reasons:
        blended = 69

    tier = _tier(blended)

    # 6. LLM fallback for inconclusive scores
    explanation = ""
    explanation_source = "rules"
    if 30 <= blended <= 60 and settings.LLM_ENABLED:
        explanation, explanation_source = _try_llm(body.text, lang)

    # 7. Persist (hash the text — never store raw message)
    text_hash = hashlib.sha256(body.text.encode()).hexdigest()
    scan_id = str(uuid.uuid4())
    db.add(ScanResult(
        id=scan_id,
        user_id=user_id,
        text_hash=text_hash,
        channel=body.channel,
        score=blended,
        tier=tier,
        category=rules_result.category,
        reasons=rules_result.reasons,
        advice=rules_result.advice,
        explanation_source=explanation_source,
        detected_language=lang,
        created_at=datetime.utcnow(),
    ))
    db.commit()

    # 8. Return response
    return ScanResponse(
        id=scan_id,
        score=blended,
        tier=tier,
        category=rules_result.category,
        reasons=rules_result.reasons,
        advice=rules_result.advice,
        explanation=explanation,
        explanation_source=explanation_source,
        detected_language=lang,
        scanned_at=datetime.utcnow(),
    )
