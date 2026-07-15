"""Predict inside-cloud and print fixed message.

Uses a tiny JSON logistic-regression model (no scikit-learn at runtime)
so Render free-tier (~512MB) does not OOM.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from src.features import FEATURE_NAMES, extract_features, feature_vector
from src.messages import format_message

ROOT = Path(__file__).resolve().parents[1]
MODEL_JSON = ROOT / "models" / "cloud_logreg.json"
_model: dict | None = None


def _get_model() -> dict:
    global _model
    if _model is None:
        if not MODEL_JSON.exists():
            raise FileNotFoundError(
                f"Model not found: {MODEL_JSON}. Run: python3 -m src.train"
            )
        _model = json.loads(MODEL_JSON.read_text())
        if _model.get("feature_names") != FEATURE_NAMES:
            raise ValueError("Model feature_names mismatch FEATURE_NAMES")
    return _model


def _predict_inside(x) -> bool:
    m = _get_model()
    # score = intercept + coef · x
    score = float(m["intercept"])
    for c, v in zip(m["coef"], x):
        score += float(c) * float(v)
    return score >= 0.0


def predict_path(path: Path) -> str:
    feats = extract_features(path)
    period = "day" if feats["is_day"] >= 0.5 else "night"
    x = feature_vector(feats)
    inside = _predict_inside(x)
    return format_message(inside, period)


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python -m src.predict <image.jpg> [more.jpg ...]")
        sys.exit(1)
    for arg in sys.argv[1:]:
        p = Path(arg)
        msg = predict_path(p)
        print(f"{p.name}: {msg}")


if __name__ == "__main__":
    main()
