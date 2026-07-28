"""Predict inside-cloud and print the fixed message.

Primary path: the logistic model trained on the golden set
(models/cloud_logreg.json — scaler already folded into the coefficients, so
inference is one dot product). Falls back to the heuristic rules when the
model file is missing.
"""
from __future__ import annotations

import json
import sys
from functools import lru_cache
from pathlib import Path

from src.features import extract_features
from src.heuristic import heuristic_label
from src.messages import format_message

ROOT = Path(__file__).resolve().parents[1]
MODEL_JSON = ROOT / "models" / "cloud_logreg.json"


@lru_cache(maxsize=1)
def _load_model() -> dict | None:
    try:
        return json.loads(MODEL_JSON.read_text())
    except (OSError, ValueError):
        return None


def predict_inside(feats: dict[str, float]) -> bool:
    model = _load_model()
    if model is not None:
        score = model["intercept"] + sum(
            c * feats[n] for c, n in zip(model["coef"], model["feature_names"])
        )
        return score > 0.0
    return heuristic_label(feats) == "inside_cloud"


def predict_path(path: Path) -> str:
    feats = extract_features(path)
    period = "day" if feats["is_day"] >= 0.5 else "night"
    return format_message(predict_inside(feats), period)


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
