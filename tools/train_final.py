"""Train the shipped logistic model on every unique labeled KFB frame.

Sources (filename-deduped; later rows win):
  1. data/labels_r5_kfb_full.csv     Jan–Apr 2023 per-minute heuristic
  2. data/labels_r5_kfb2023.csv      2023 hourly heuristic, full year
  3. data/golden_labels.csv          2016 human GT
  4. review_r5/manifest.csv          111 visual GT overrides

Weights: (1 / n_frames_on_that_date) × 20 if the label is human, else × 1.
That keeps May–Dec hourly days in the loss and stops 172k minutes from
erasing 253 human rows.

Holdout: GroupShuffleSplit 80/20 by date (random_state=42). Shipped JSON is
the train-split fit (no full-data refit), so test metrics stay honest.

Usage: PYTHONPATH=. python3 tools/train_final.py
"""
from __future__ import annotations

import csv
import json
import shutil
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "data" / "golden_labels.csv"
FEATS_2016 = ROOT / "data" / "labels.csv"
HOURLY = ROOT / "data" / "labels_r5_kfb2023.csv"
FULL = ROOT / "data" / "labels_r5_kfb_full.csv"
REVIEW = ROOT / "review_r5" / "manifest.csv"
MODEL_JSON = ROOT / "models" / "cloud_logreg.json"
MODEL_BAK = ROOT / "models" / "cloud_logreg_d413d74.json"
DOCS_JSON = ROOT / "docs" / "cloud_logreg.json"
REPORT_JSON = ROOT / "models" / "train_report.json"

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
W_HUMAN = 20.0


def _pipeline() -> Pipeline:
    return Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(max_iter=2000, random_state=42,
                                   class_weight="balanced", C=0.5)),
    ])


def _date(filename: str) -> str:
    return filename[7:13]


def _vec(row: dict) -> list[float]:
    return [float(row[n]) for n in MODEL_FEATURES]


def _metrics(y, p) -> dict:
    y = np.asarray(y)
    p = np.asarray(p)
    if len(y) == 0:
        return {"n": 0, "inside": 0, "acc": None, "precision": None,
                "recall": None, "f1": None, "cm": [[0, 0], [0, 0]]}
    acc = float((y == p).mean())
    cm = confusion_matrix(y, p, labels=[0, 1]).tolist()
    prec, rec, f1, _ = precision_recall_fscore_support(
        y, p, average="binary", zero_division=0,
    )
    return {
        "n": int(len(y)),
        "inside": int(y.sum()),
        "acc": round(acc, 4),
        "precision": round(float(prec), 4),
        "recall": round(float(rec), 4),
        "f1": round(float(f1), 4),
        "cm": cm,
    }


def _predict_raw(X: np.ndarray, coef: np.ndarray, intercept: float) -> np.ndarray:
    return (intercept + X @ coef > 0).astype(int)


def load_old_model() -> tuple[np.ndarray, float]:
    src = MODEL_BAK if MODEL_BAK.exists() else MODEL_JSON
    payload = json.loads(src.read_text())
    assert payload["feature_names"] == MODEL_FEATURES
    return np.array(payload["coef"], dtype=float), float(payload["intercept"])


def _counts(arr: np.ndarray) -> dict[str, int]:
    return {str(k): int(v) for k, v in Counter(arr.tolist()).items()}


def load_combined() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    feats_2016 = {r["filename"]: r for r in csv.DictReader(FEATS_2016.open())}
    review = {r["filename"]: r["golden"] for r in csv.DictReader(REVIEW.open())}

    rows: dict[str, dict] = {}
    with FULL.open() as f:
        for r in csv.DictReader(f):
            rows[r["filename"]] = {
                "y": 1 if r["label"] == "inside_cloud" else 0,
                "x": _vec(r),
                "origin": "r5_minute",
                "human": False,
            }
    with HOURLY.open() as f:
        for r in csv.DictReader(f):
            rows[r["filename"]] = {
                "y": 1 if r["label"] == "inside_cloud" else 0,
                "x": _vec(r),
                "origin": "r5_hourly",
                "human": False,
            }
    with GOLDEN.open() as f:
        for r in csv.DictReader(f):
            fr = feats_2016[r["filename"]]
            rows[r["filename"]] = {
                "y": 1 if r["golden"] == "inside_cloud" else 0,
                "x": _vec(fr),
                "origin": "golden_2016",
                "human": True,
            }
    with HOURLY.open() as f:
        hourly = {r["filename"]: r for r in csv.DictReader(f)}
    for fn, label in review.items():
        rows[fn] = {
            "y": 1 if label == "inside_cloud" else 0,
            "x": _vec(hourly[fn]),
            "origin": "human_2023",
            "human": True,
        }

    order = sorted(rows)
    X = np.array([rows[k]["x"] for k in order], dtype=float)
    y = np.array([rows[k]["y"] for k in order], dtype=int)
    origins = np.array([rows[k]["origin"] for k in order])
    human = np.array([rows[k]["human"] for k in order], dtype=bool)
    groups = np.array([_date(k) for k in order])
    return X, y, groups, origins, human


def sample_weights(groups: np.ndarray, human: np.ndarray) -> np.ndarray:
    counts = Counter(groups.tolist())
    w = np.array([1.0 / counts[d] for d in groups], dtype=float)
    w[human] *= W_HUMAN
    return w / w.mean()


def load_review_111():
    feats = {r["filename"]: r for r in csv.DictReader(HOURLY.open())}
    X, y, day, names, heur = [], [], [], [], []
    with REVIEW.open() as f:
        for r in csv.DictReader(f):
            fr = feats[r["filename"]]
            X.append(_vec(fr))
            y.append(1 if r["golden"] == "inside_cloud" else 0)
            day.append(float(fr["is_day"]) >= 0.5)
            names.append(r["filename"])
            heur.append(1 if r["heuristic"] == "inside_cloud" else 0)
    return (np.array(X, dtype=float), np.array(y, dtype=int),
            np.array(day, dtype=bool), np.array(names),
            np.array(heur, dtype=int))


def load_golden_all():
    feats = {r["filename"]: r for r in csv.DictReader(FEATS_2016.open())}
    X, y = [], []
    with GOLDEN.open() as f:
        for r in csv.DictReader(f):
            X.append(_vec(feats[r["filename"]]))
            y.append(1 if r["golden"] == "inside_cloud" else 0)
    return np.array(X, dtype=float), np.array(y, dtype=int)


def fold_coef(pipe: Pipeline) -> tuple[list[float], float]:
    scaler: StandardScaler = pipe.named_steps["scaler"]
    clf: LogisticRegression = pipe.named_steps["clf"]
    w = clf.coef_.ravel()
    coef = (w / scaler.scale_).tolist()
    intercept = float(clf.intercept_.ravel()[0]
                      - np.dot(w, scaler.mean_ / scaler.scale_))
    return coef, intercept


def save_model(coef: list[float], intercept: float) -> None:
    payload = json.dumps(
        {"feature_names": MODEL_FEATURES, "coef": coef, "intercept": intercept},
        indent=2,
    ) + "\n"
    MODEL_JSON.parent.mkdir(parents=True, exist_ok=True)
    MODEL_JSON.write_text(payload)
    if DOCS_JSON.parent.exists():
        DOCS_JSON.write_text(payload)


def main() -> None:
    if MODEL_JSON.exists() and not MODEL_BAK.exists():
        shutil.copy(MODEL_JSON, MODEL_BAK)
        print("backed up previous model ->", MODEL_BAK, flush=True)

    old_coef, old_intercept = load_old_model()
    X, y, groups, origins, human = load_combined()
    w = sample_weights(groups, human)
    print(
        f"combined n={len(y)} inside={int(y.sum())} "
        f"dates={len(set(groups.tolist()))} origins={_counts(origins)}",
        flush=True,
    )
    mass = {o: round(float(w[origins == o].sum() / w.sum()), 3)
            for o in sorted(set(origins.tolist()))}
    print(f"weighted mass by origin {mass}", flush=True)

    gss = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=42)
    train_idx, test_idx = next(gss.split(X, y, groups))
    pipe = _pipeline()
    pipe.fit(X[train_idx], y[train_idx], clf__sample_weight=w[train_idx])
    pred_tr = pipe.predict(X[train_idx])
    pred_te = pipe.predict(X[test_idx])
    pred_te_old = _predict_raw(X[test_idx], old_coef, old_intercept)
    origin_te = origins[test_idx]
    day_te = X[test_idx][:, -1] >= 0.5

    X111, y111, day111, n111, h111 = load_review_111()
    Xg, yg = load_golden_all()
    pred_111 = pipe.predict(X111)
    pred_111_old = _predict_raw(X111, old_coef, old_intercept)
    pred_g = pipe.predict(Xg)
    pred_g_old = _predict_raw(Xg, old_coef, old_intercept)
    test_dates = set(groups[test_idx].tolist())
    held_111 = np.array([_date(fn) in test_dates for fn in n111])

    coef, intercept = fold_coef(pipe)
    save_model(coef, intercept)

    report = {
        "name": "combined_final",
        "recipe": "StandardScaler + LogReg(C=0.5, balanced); "
                  "weight = (1/n_frames_on_date) × 20 if human else × 1",
        "split": "GroupShuffleSplit test_size=0.20 random_state=42 grouped by YYMMDD",
        "shipped": "train_split_fit on all unique frames (minutes+hourly+golden+111)",
        "counts": {
            "combined": int(len(y)),
            "inside": int(y.sum()),
            "dates": int(len(set(groups.tolist()))),
            "origins": _counts(origins),
            "train": int(len(train_idx)),
            "train_inside": int(y[train_idx].sum()),
            "train_dates": int(len(set(groups[train_idx].tolist()))),
            "test": int(len(test_idx)),
            "test_inside": int(y[test_idx].sum()),
            "test_dates": int(len(set(groups[test_idx].tolist()))),
            "test_origins": _counts(origin_te),
            "review_111_in_test_dates": int(held_111.sum()),
            "weighted_mass": mass,
        },
        "holdout": {
            "train": _metrics(y[train_idx], pred_tr),
            "test": _metrics(y[test_idx], pred_te),
            "test_day": _metrics(y[test_idx][day_te], pred_te[day_te]),
            "test_night": _metrics(y[test_idx][~day_te], pred_te[~day_te]),
            "test_golden": _metrics(y[test_idx][origin_te == "golden_2016"],
                                    pred_te[origin_te == "golden_2016"]),
            "test_hourly": _metrics(y[test_idx][origin_te == "r5_hourly"],
                                    pred_te[origin_te == "r5_hourly"]),
            "test_minute": _metrics(y[test_idx][origin_te == "r5_minute"],
                                    pred_te[origin_te == "r5_minute"]),
            "test_human_2023": _metrics(y[test_idx][origin_te == "human_2023"],
                                        pred_te[origin_te == "human_2023"]),
            "old_same_test": _metrics(y[test_idx], pred_te_old),
        },
        "golden_all_142": {
            "new": _metrics(yg, pred_g),
            "old": _metrics(yg, pred_g_old),
        },
        "review_111": {
            "heuristic": _metrics(y111, h111),
            "new": _metrics(y111, pred_111),
            "old": _metrics(y111, pred_111_old),
            "new_day": _metrics(y111[day111], pred_111[day111]),
            "old_day": _metrics(y111[day111], pred_111_old[day111]),
            "new_night": _metrics(y111[~day111], pred_111[~day111]),
            "old_night": _metrics(y111[~day111], pred_111_old[~day111]),
            "new_held_dates": _metrics(y111[held_111], pred_111[held_111]),
            "old_held_dates": _metrics(y111[held_111], pred_111_old[held_111]),
        },
        "coef": coef,
        "intercept": intercept,
        "feature_names": MODEL_FEATURES,
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2) + "\n")

    h, r111 = report["holdout"], report["review_111"]
    print(
        f"holdout test {h['test']['acc']} (old {h['old_same_test']['acc']}) "
        f"golden-slice {h['test_golden']['acc']} "
        f"111-held-dates {h['test_human_2023']['acc']} "
        f"n={h['test_human_2023']['n']}",
        flush=True,
    )
    print(
        f"111 {r111['new']['acc']} (old {r111['old']['acc']}, "
        f"heuristic {r111['heuristic']['acc']}) "
        f"day {r111['new_day']['acc']} night {r111['new_night']['acc']}",
        flush=True,
    )
    print("saved", MODEL_JSON, DOCS_JSON, REPORT_JSON, flush=True)


if __name__ == "__main__":
    main()
