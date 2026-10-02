"""
Evaluate the classifier against the legitimate sample set.

Reports precision, recall, and false-positive rate on legit messages.
Exits with code 1 if FP rate exceeds 10 %.

Usage (from repo root):
    python scripts/evaluate_classifier.py
"""
import json
import pathlib
import pickle
import sys

ROOT       = pathlib.Path(__file__).resolve().parent.parent
MODEL_PATH = ROOT / "backend" / "model" / "classifier.pkl"
LEGIT_PATH = ROOT / "data" / "legit_samples.json"
SCAM_PATH  = ROOT / "data" / "scam_samples.json"


def main() -> None:
    if not MODEL_PATH.exists():
        print(f"ERROR: Model not found at {MODEL_PATH}")
        print("Run: python scripts/train_classifier.py")
        sys.exit(1)

    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)

    with open(LEGIT_PATH, encoding="utf-8") as f:
        legit_samples = json.load(f)
    with open(SCAM_PATH, encoding="utf-8") as f:
        scam_samples = json.load(f)

    legit_texts = [s["text"] for s in legit_samples]
    scam_texts  = [s["text"] for s in scam_samples]

    # ── False-positive rate on legit messages ────────────────────────────────
    legit_preds = model.predict(legit_texts)
    fp = sum(1 for p in legit_preds if p == 1)  # legit predicted as scam
    fp_rate = fp / len(legit_texts)

    # ── Precision / recall on scam messages ──────────────────────────────────
    scam_preds = model.predict(scam_texts)
    tp = sum(1 for p in scam_preds if p == 1)
    fn = len(scam_texts) - tp
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0

    print("=" * 50)
    print("Mukuru Detection — Classifier Evaluation")
    print("=" * 50)
    print(f"Legit samples :  {len(legit_texts)}")
    print(f"Scam  samples :  {len(scam_texts)}")
    print()
    print(f"True  positives (scam  caught):  {tp}/{len(scam_texts)}")
    print(f"False positives (legit flagged): {fp}/{len(legit_texts)}")
    print()
    print(f"Precision :  {precision:.1%}")
    print(f"Recall    :  {recall:.1%}")
    print(f"FP rate   :  {fp_rate:.1%}  {'✓ PASS' if fp_rate <= 0.10 else '✗ FAIL (>10%)'}")
    print("=" * 50)

    if fp_rate > 0.10:
        print("\nFP rate exceeds 10 % threshold — retrain or expand legit samples.")
        sys.exit(1)
    print("\nEvaluation passed.")


if __name__ == "__main__":
    main()
