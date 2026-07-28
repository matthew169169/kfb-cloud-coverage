"""Evaluate and tune the classifier against the hand-labeled golden set.

- Reports the current heuristic's true accuracy.
- Grid-searches simple day/night rule thresholds (kept portable to JS),
  validated with leave-one-date-out CV to avoid overfitting 142 samples.
- Compares a logistic regression trained on the golden labels (same CV).
"""
from __future__ import annotations

import csv
from itertools import product
from pathlib import Path

import numpy as np

from src.heuristic import heuristic_label

ROOT = Path(__file__).resolve().parents[1]


def load() -> list[dict]:
    with (ROOT / "data" / "labels.csv").open() as f:
        feats = {r["filename"]: r for r in csv.DictReader(f)}
    rows = []
    with (ROOT / "data" / "golden_labels.csv").open() as f:
        for r in csv.DictReader(f):
            fr = feats[r["filename"]]
            row = {k: float(fr[k]) for k in (
                "brightness_mean", "brightness_std", "edge_density",
                "saturation_mean", "upper_lower_contrast", "bright_spot_ratio",
                "far_grad", "far_wash", "far_std", "is_day")}
            row["filename"] = r["filename"]
            row["date"] = Path(r["filename"]).stem.split("_")[1]
            row["y"] = 1 if r["golden"] == "inside_cloud" else 0
            rows.append(row)
    return rows


def acc(rows: list[dict], pred_fn) -> float:
    return float(np.mean([pred_fn(r) == r["y"] for r in rows]))


def day_rule(w, g, s):
    """inside if far field is washed AND textureless, or an extreme whiteout."""
    def fn(r):
        if r["far_wash"] >= w and r["far_grad"] <= g:
            return 1
        if r["far_std"] <= s and r["far_wash"] >= 0.9:
            return 1
        return 0
    return fn


def night_rule(spot, std):
    """inside if valley lights are absent and the frame is flat."""
    def fn(r):
        return 1 if (r["bright_spot_ratio"] <= spot and r["brightness_std"] <= std) else 0
    return fn


def cv_rule(rows, grids, rule_factory) -> tuple[tuple, float, float]:
    """Leave-one-date-out CV; returns (best_params_on_all, cv_acc, fit_acc)."""
    dates = sorted({r["date"] for r in rows})
    correct = 0
    for held in dates:
        tr = [r for r in rows if r["date"] != held]
        te = [r for r in rows if r["date"] == held]
        best = max(grids, key=lambda p: acc(tr, rule_factory(*p)))
        correct += sum(rule_factory(*best)(r) == r["y"] for r in te)
    cv_acc = correct / len(rows)
    best_all = max(grids, key=lambda p: acc(rows, rule_factory(*p)))
    return best_all, cv_acc, acc(rows, rule_factory(*best_all))


def cv_logreg(rows) -> float:
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    names = ["brightness_mean", "brightness_std", "edge_density",
             "saturation_mean", "upper_lower_contrast", "bright_spot_ratio",
             "far_grad", "far_wash", "far_std", "is_day"]
    X = np.array([[r[n] for n in names] for r in rows])
    y = np.array([r["y"] for r in rows])
    dates = np.array([r["date"] for r in rows])
    correct = 0
    for held in sorted(set(dates.tolist())):
        m = dates != held
        if y[m].sum() in (0, len(y[m])):
            continue
        pipe = Pipeline([
            ("s", StandardScaler()),
            ("c", LogisticRegression(max_iter=2000, random_state=42,
                                     class_weight="balanced", C=0.5)),
        ])
        pipe.fit(X[m], y[m])
        correct += int((pipe.predict(X[~m]) == y[~m]).sum())
    return correct / len(rows)


def main() -> None:
    rows = load()
    day = [r for r in rows if r["is_day"] >= 0.5]
    night = [r for r in rows if r["is_day"] < 0.5]
    print(f"golden n={len(rows)} (day={len(day)}, night={len(night)}), "
          f"inside={sum(r['y'] for r in rows)}")

    def current(r):
        feats = {k: r[k] for k in r if k not in ("filename", "date", "y")}
        return 1 if heuristic_label(feats) == "inside_cloud" else 0

    print(f"\ncurrent heuristic: all={acc(rows, current):.3f} "
          f"day={acc(day, current):.3f} night={acc(night, current):.3f}")

    day_grid = list(product(
        np.round(np.arange(0.55, 1.0, 0.05), 2),      # far_wash >= w
        np.round(np.arange(0.5, 4.1, 0.25), 2),       # far_grad <= g
        np.round(np.arange(5, 30, 5), 1),             # far_std <= s (whiteout)
    ))
    (w, g, s), cv_d, fit_d = cv_rule(day, day_grid, day_rule)
    print(f"\nday rule tuned:  far_wash>={w} far_grad<={g} "
          f"(whiteout far_std<={s})  CV={cv_d:.3f} fit={fit_d:.3f}")

    night_grid = list(product(
        np.round(np.arange(0.0005, 0.0055, 0.0005), 4),  # bright_spot_ratio <=
        np.round(np.arange(10, 42, 2), 1),               # brightness_std <=
    ))
    (spot, std), cv_n, fit_n = cv_rule(night, night_grid, night_rule)
    print(f"night rule tuned: bright_spot<={spot} brightness_std<={std}  "
          f"CV={cv_n:.3f} fit={fit_n:.3f}")

    n_day, n_night = len(day), len(night)
    combined_cv = (cv_d * n_day + cv_n * n_night) / (n_day + n_night)
    print(f"combined tuned rules CV accuracy: {combined_cv:.3f}")

    print(f"logreg trained on golden (leave-date-out CV): {cv_logreg(rows):.3f}")


if __name__ == "__main__":
    main()
