"""Scan image/ and write data/labels.csv with heuristic labels."""
from __future__ import annotations
import csv
from pathlib import Path
from src.features import extract_features
from src.heuristic import heuristic_label

ROOT = Path(__file__).resolve().parents[1]
IMAGE_DIR = ROOT / "image"
OUT = ROOT / "data" / "labels.csv"

def main() -> None:
    paths = sorted(IMAGE_DIR.glob("imgKFB_*.jpg"))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for i, p in enumerate(paths):
        feats = extract_features(p)
        label = heuristic_label(feats)
        period = "day" if feats["is_day"] >= 0.5 else "night"
        rows.append(
            {
                "filename": p.name,
                "label": label,
                "period": period,
                "source": "heuristic",
                **{k: f"{v:.6f}" for k, v in feats.items()},
            }
        )
        if (i + 1) % 200 == 0:
            print(f"labeled {i + 1}/{len(paths)}")
    fieldnames = list(rows[0].keys()) if rows else ["filename", "label", "period", "source"]
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    inside = sum(1 for r in rows if r["label"] == "inside_cloud")
    print(f"Wrote {OUT} n={len(rows)} inside={inside} not_inside={len(rows) - inside}")

if __name__ == "__main__":
    main()
