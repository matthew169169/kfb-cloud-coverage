"""Predict inside-cloud and print fixed message.

Uses the same visual rules as labeling (heuristic), so day fog whiteout vs
clear valley / night lights stay consistent in CLI, Flask, and the browser.
"""
from __future__ import annotations

import sys
from pathlib import Path

from src.features import extract_features
from src.heuristic import heuristic_label
from src.messages import format_message


def predict_path(path: Path) -> str:
    feats = extract_features(path)
    period = "day" if feats["is_day"] >= 0.5 else "night"
    inside = heuristic_label(feats) == "inside_cloud"
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
