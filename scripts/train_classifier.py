"""
Train the TF-IDF + Logistic Regression scam classifier.

Usage (from repo root):
    python scripts/train_classifier.py

Outputs:
    backend/model/classifier.pkl  — trained sklearn Pipeline
"""
import json
import os
import pathlib
import pickle
import sys

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT = pathlib.Path(__file__).resolve().parent.parent
SCAM_PATH  = ROOT / "data" / "scam_samples.json"
LEGIT_PATH = ROOT / "data" / "legit_samples.json"
MODEL_DIR  = ROOT / "backend" / "model"
MODEL_PATH = MODEL_DIR / "classifier.pkl"


def load_data() -> tuple[list[str], list[int]]:
    """Load scam + legit samples. Returns (texts, labels) where 1=scam, 0=legit."""
    with open(SCAM_PATH, encoding="utf-8") as f:
        scam = json.load(f)
    with open(LEGIT_PATH, encoding="utf-8") as f:
        legit = json.load(f)

    texts  = [s["text"] for s in scam]  + [s["text"] for s in legit]
    labels = [1]         * len(scam)    + [0]         * len(legit)
    print(f"Loaded {len(scam)} scam samples and {len(legit)} legit samples.")
    return texts, labels


def build_pipeline() -> Pipeline:
    """Build the TF-IDF + LogisticRegression pipeline."""
    return Pipeline([
        ("tfidf", TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 2),
            sublinear_tf=True,
            strip_accents="unicode",
            analyzer="word",
            token_pattern=r"\b\w+\b",
        )),
        ("clf", LogisticRegression(
            C=1.0,
            max_iter=1000,
            class_weight="balanced",   # handles label imbalance
            solver="saga",
            random_state=42,
        )),
    ])


def main() -> None:
    texts, labels = load_data()

    pipeline = build_pipeline()

    # 5-fold stratified cross-validation
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    scores = cross_val_score(pipeline, texts, labels, cv=cv, scoring="f1")
    print(f"\n5-fold CV F1 scores: {scores.round(3)}")
    print(f"Mean F1: {scores.mean():.3f}  ±  {scores.std():.3f}")

    # Train on full dataset
    pipeline.fit(texts, labels)

    # Quick in-sample report (for reference — not a substitute for held-out eval)
    preds = pipeline.predict(texts)
    print("\nIn-sample classification report:")
    print(classification_report(labels, preds, target_names=["legit", "scam"]))

    # Save model
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(pipeline, f)
    print(f"\nModel saved to {MODEL_PATH}")


if __name__ == "__main__":
    main()
