"""Train RandomForest on data/labels.csv; save models/cloud_clf.joblib."""
from __future__ import annotations
import csv
from pathlib import Path
import numpy as np
from joblib import dump
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
from src.features import FEATURE_NAMES

ROOT = Path(__file__).resolve().parents[1]
LABELS = ROOT / "data" / "labels.csv"
MODEL = ROOT / "models" / "cloud_clf.joblib"

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
    clf = RandomForestClassifier(
        n_estimators=100, max_depth=12, random_state=42, n_jobs=-1
    )
    clf.fit(X_tr, y_tr)
    pred = clf.predict(X_te)
    print("test_accuracy", accuracy_score(y_te, pred))
    print("confusion_matrix [[tn, fp], [fn, tp]]")
    print(confusion_matrix(y_te, pred))
    print(classification_report(y_te, pred, target_names=["not_inside", "inside_cloud"]))
    MODEL.parent.mkdir(parents=True, exist_ok=True)
    dump({"model": clf, "feature_names": FEATURE_NAMES}, MODEL)
    print("saved", MODEL)

if __name__ == "__main__":
    main()
