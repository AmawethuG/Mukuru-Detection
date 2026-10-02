"""
TF-IDF + Logistic Regression classifier wrapper.

Loads the trained model from backend/model/classifier.pkl once at import
time. Degrades gracefully (returns 0.5) if the model file is absent.

Pure Python — no FastAPI imports.
"""
from __future__ import annotations

import functools
import logging
import pathlib
import pickle

logger = logging.getLogger(__name__)

MODEL_PATH = pathlib.Path(__file__).parent.parent / "model" / "classifier.pkl"


@functools.lru_cache(maxsize=1)
def _load_model():
    """Load and cache the classifier pipeline. Returns None if unavailable."""
    if not MODEL_PATH.exists():
        logger.warning("classifier.pkl not found at %s — using neutral score 0.5", MODEL_PATH)
        return None
    try:
        with open(MODEL_PATH, "rb") as fh:
            model = pickle.load(fh)
        logger.info("Classifier loaded from %s", MODEL_PATH)
        return model
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to load classifier: %s — using neutral score 0.5", exc)
        return None


def predict_scam_probability(text: str) -> float:
    """
    Return the probability (0.0 – 1.0) that *text* is a scam.

    Falls back to 0.5 if the model is unavailable (neutral — no bias).
    """
    model = _load_model()
    if model is None:
        return 0.5
    try:
        proba = model.predict_proba([text])[0]
        # Index 1 = "scam" class (set during training)
        return float(proba[1])
    except Exception as exc:  # noqa: BLE001
        logger.warning("Classifier prediction failed: %s", exc)
        return 0.5
