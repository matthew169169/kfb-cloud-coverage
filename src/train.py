"""Train a logistic model on the 2016 golden set only (comparison / fallback).

The shipped production trainer is tools/train_final.py (2016 golden + 2023
hourly + 111 visual overrides, date-grouped holdout). This module remains a
small 142-row baseline. Features come from data/labels.csv; labels from
data/golden_labels.csv. The StandardScaler is folded into the coefficients.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
LABELS = ROOT / "data" / "labels.csv"
GOLDEN = ROOT / "data" / "golden_labels.csv"
MODEL_JSON = ROOT / "models" / "cloud_logreg.json"
DOCS_JSON = ROOT / "docs" / "cloud_logreg.json"

MODEL_FEATURES = [
    "brightness_mean",
    "brightness_std",
    "saturation_mean",
    "upper_lower_contrast",
    "bright_spot_ratio",
    "far_grad",
    "far_wash",
    "far_std",
    "is_day",
]


def _pipeline() -> Pipeline:
    return Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(max_iter=2000, random_state=42,
                                   class_weight="balanced", C=0.5)),
    ])


def load_golden() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    with LABELS.open() as f:
        feats = {r["filename"]: r for r in csv.DictReader(f)}
    X, y, dates = [], [], []
    with GOLDEN.open() as f:
        for r in csv.DictReader(f):
            fr = feats[r["filename"]]
            X.append([float(fr[n]) for n in MODEL_FEATURES])
            y.append(1 if r["golden"] == "inside_cloud" else 0)
            dates.append(Path(r["filename"]).stem.split("_")[1])
    return np.array(X), np.array(y), np.array(dates)


def cv_report(X: np.ndarray, y: np.ndarray, dates: np.ndarray) -> None:
    correct = 0
    for held in sorted(set(dates.tolist())):
        m = dates != held
        pipe = _pipeline()
        pipe.fit(X[m], y[m])
        correct += int((pipe.predict(X[~m]) == y[~m]).sum())
    print(f"leave-one-date-out CV accuracy: {correct / len(y):.4f} (n={len(y)})")


def main() -> None:
    X, y, dates = load_golden()
    print(f"golden set n={len(y)} inside={int(y.sum())} dates={len(set(dates.tolist()))}")
    cv_report(X, y, dates)

    pipe = _pipeline()
    pipe.fit(X, y)
    scaler: StandardScaler = pipe.named_steps["scaler"]
    clf: LogisticRegression = pipe.named_steps["clf"]
    w = clf.coef_.ravel()
    coef = (w / scaler.scale_).tolist()
    intercept = float(clf.intercept_.ravel()[0] - np.dot(w, scaler.mean_ / scaler.scale_))

    payload = json.dumps(
        {"feature_names": MODEL_FEATURES, "coef": coef, "intercept": intercept},
        indent=2,
    )
    MODEL_JSON.parent.mkdir(parents=True, exist_ok=True)
    MODEL_JSON.write_text(payload)
    print("saved", MODEL_JSON)
    if DOCS_JSON.parent.exists():
        DOCS_JSON.write_text(payload)
        print("saved", DOCS_JSON)


if __name__ == "__main__":
    main()
