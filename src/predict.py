"""Predict inside-cloud and print fixed message."""
from __future__ import annotations
import sys
from pathlib import Path
from joblib import load
from src.features import extract_features, feature_vector
from src.messages import format_message

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "models" / "cloud_clf.joblib"
_clf = None


def _get_clf():
    global _clf
    if _clf is None:
        if not MODEL.exists():
            raise FileNotFoundError(
                f"Model not found: {MODEL}. Run: python3 -m src.train"
            )
        _clf = load(MODEL)["model"]
    return _clf


def predict_path(path: Path) -> str:
    clf = _get_clf()
    feats = extract_features(path)
    period = "day" if feats["is_day"] >= 0.5 else "night"
    x = feature_vector(feats).reshape(1, -1)
    inside = bool(clf.predict(x)[0] == 1)
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
