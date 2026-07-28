"""Compare classifiers on the heuristic labels with grouped-by-date CV.

Accuracy here means agreement with the heuristic seed labels; the golden
set (tools/eval_golden.py) measures accuracy against human labels.
"""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.features import FEATURE_NAMES

ROOT = Path(__file__).resolve().parents[1]
LABELS = ROOT / "data" / "labels.csv"


def load() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    with LABELS.open() as f:
        rows = list(csv.DictReader(f))
    X = np.array([[float(r[n]) for n in FEATURE_NAMES] for r in rows])
    y = np.array([1 if r["label"] == "inside_cloud" else 0 for r in rows])
    groups = np.array([Path(r["filename"]).stem.split("_")[1] for r in rows])
    return X, y, groups


def candidates() -> dict:
    return {
        "logreg(10 feats)": Pipeline([
            ("s", StandardScaler()),
            ("c", LogisticRegression(max_iter=2000, random_state=42,
                                     class_weight="balanced", C=0.5)),
        ]),
        "random_forest": RandomForestClassifier(
            n_estimators=300, max_depth=12, random_state=42, n_jobs=-1,
            class_weight="balanced"),
        "hist_gb": HistGradientBoostingClassifier(
            max_iter=300, max_depth=6, random_state=42),
    }


def main() -> None:
    X, y, groups = load()
    n_dates = len(set(groups.tolist()))
    cv = GroupKFold(n_splits=min(5, n_dates))
    print(f"n={len(y)} inside={int(y.sum())} dates={n_dates} "
          f"features={len(FEATURE_NAMES)}")
    for name, model in candidates().items():
        scores = cross_val_score(model, X, y, cv=cv, groups=groups,
                                 scoring="accuracy", n_jobs=-1)
        print(f"{name:18s} CV acc {scores.mean():.4f} +/- {scores.std():.4f}  "
              f"folds={np.round(scores, 4).tolist()}")


if __name__ == "__main__":
    main()
