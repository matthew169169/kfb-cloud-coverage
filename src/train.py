"""Train classifiers; save a tiny JSON logistic model for low-RAM web deploy."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.features import FEATURE_NAMES

ROOT = Path(__file__).resolve().parents[1]
LABELS = ROOT / "data" / "labels.csv"
MODEL_JSON = ROOT / "models" / "cloud_logreg.json"


def _date_key(filename: str) -> str:
    return Path(filename).stem.split("_")[1]


def load_xy():
    with LABELS.open() as f:
        rows = list(csv.DictReader(f))
    dates = sorted({_date_key(r["filename"]) for r in rows})
    cut = max(1, int(len(dates) * 0.8))
    train_dates = set(dates[:cut])
    X_tr, y_tr, X_te, y_te = [], [], [], []
    for r in rows:
        x = [float(r[n]) for n in FEATURE_NAMES]
        y = 1 if r["label"] == "inside_cloud" else 0
        if _date_key(r["filename"]) in train_dates:
            X_tr.append(x)
            y_tr.append(y)
        else:
            X_te.append(x)
            y_te.append(y)
    return np.array(X_tr), np.array(y_tr), np.array(X_te), np.array(y_te)


def main() -> None:
    X_tr, y_tr, X_te, y_te = load_xy()
    pipe = Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "clf",
                LogisticRegression(max_iter=1000, random_state=42),
            ),
        ]
    )
    pipe.fit(X_tr, y_tr)
    pred = pipe.predict(X_te)
    print("test_accuracy", accuracy_score(y_te, pred))
    print("confusion_matrix [[tn, fp], [fn, tp]]")
    print(confusion_matrix(y_te, pred))
    print(classification_report(y_te, pred, target_names=["not_inside", "inside_cloud"]))

    # Fold scaler into linear weights so runtime needs no sklearn.
    scaler: StandardScaler = pipe.named_steps["scaler"]
    clf: LogisticRegression = pipe.named_steps["clf"]
    # z = (x - mean) / scale ; score = w·z + b = (w/scale)·x + (b - w·mean/scale)
    w = clf.coef_.ravel()
    scale = scaler.scale_
    mean = scaler.mean_
    coef = (w / scale).tolist()
    intercept = float(clf.intercept_.ravel()[0] - np.dot(w, mean / scale))

    MODEL_JSON.parent.mkdir(parents=True, exist_ok=True)
    MODEL_JSON.write_text(
        json.dumps(
            {
                "feature_names": FEATURE_NAMES,
                "coef": coef,
                "intercept": intercept,
            },
            indent=2,
        )
    )
    print("saved", MODEL_JSON)


if __name__ == "__main__":
    main()
