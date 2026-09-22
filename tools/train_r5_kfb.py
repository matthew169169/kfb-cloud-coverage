"""Train KFB logistic model on the FULL R5 per-minute set (heuristic labels).

- Features/labels: data/labels_r5_kfb_full.csv (written by
  tools/extract_r5_kfb_full.py). Same 9 MODEL_FEATURES + recipe as src/train.py.
- Holdout: data/golden_labels.csv (142 human labels, 2016) scored as an
  independent generalization check (different year, same camera).
- Backs up the previous model to models/cloud_logreg_v1.json, writes the new
  model to models/cloud_logreg.json and docs/cloud_logreg.json.

Usage: PYTHONPATH=. python3 tools/train_r5_kfb.py
"""
from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
FULL = ROOT / "data" / "labels_r5_kfb_full.csv"
LABELS = ROOT / "data" / "labels.csv"  # 2016 features for golden join
GOLDEN = ROOT / "data" / "golden_labels.csv"
MODEL_JSON = ROOT / "models" / "cloud_logreg.json"
MODEL_BAK = ROOT / "models" / "cloud_logreg_v1.json"
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


def load_full() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    X, y, groups = [], [], []
    with FULL.open() as f:
        for r in csv.DictReader(f):
            X.append([float(r[n]) for n in MODEL_FEATURES])
            y.append(1 if r["label"] == "inside_cloud" else 0)
            groups.append(r["filename"][7:13])  # YYMMDD
    return np.array(X), np.array(y), np.array(groups)


def load_golden() -> tuple[np.ndarray, np.ndarray]:
    with LABELS.open() as f:
        feats = {r["filename"]: r for r in csv.DictReader(f)}
    X, y = [], []
    with GOLDEN.open() as f:
        for r in csv.DictReader(f):
            fr = feats[r["filename"]]
            X.append([float(fr[n]) for n in MODEL_FEATURES])
            y.append(1 if r["golden"] == "inside_cloud" else 0)
    return np.array(X), np.array(y)


def main() -> None:
    X, y, groups = load_full()
    print(f"R5 full n={len(y)} inside={int(y.sum())} "
          f"dates={len(set(groups.tolist()))}", flush=True)

    cv = GroupKFold(n_splits=5)
    scores = cross_val_score(_pipeline(), X, y, cv=cv, groups=groups,
                             scoring="accuracy", n_jobs=-1)
    print(f"5-fold grouped-by-date CV acc {scores.mean():.4f} "
          f"+/- {scores.std():.4f} folds={np.round(scores, 4).tolist()}",
          flush=True)

    Xg, yg = load_golden()
    pipe = _pipeline()
    pipe.fit(X, y)
    print(f"train acc: {(pipe.predict(X) == y).mean():.4f} "
          f"golden-2016 holdout acc: {(pipe.predict(Xg) == yg).mean():.4f} "
          f"(n={len(yg)})", flush=True)

    scaler: StandardScaler = pipe.named_steps["scaler"]
    clf: LogisticRegression = pipe.named_steps["clf"]
    w = clf.coef_.ravel()
    coef = (w / scaler.scale_).tolist()
    intercept = float(clf.intercept_.ravel()[0]
                      - np.dot(w, scaler.mean_ / scaler.scale_))
    payload = json.dumps(
        {"feature_names": MODEL_FEATURES, "coef": coef,
         "intercept": intercept}, indent=2)

    if MODEL_JSON.exists() and not MODEL_BAK.exists():
        shutil.copy(MODEL_JSON, MODEL_BAK)
        print("backed up old model ->", MODEL_BAK, flush=True)
    MODEL_JSON.write_text(payload)
    print("saved", MODEL_JSON, flush=True)
    if DOCS_JSON.parent.exists():
        DOCS_JSON.write_text(payload)
        print("saved", DOCS_JSON, flush=True)


if __name__ == "__main__":
    main()
