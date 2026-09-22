"""Extract features for EVERY per-minute KFB frame on R5_USB_14 (full range).

Labels are heuristic auto-labels (no human verification in this pipeline).
Resumable: appends per-day to data/labels_r5_kfb_full.csv, skips filenames
already present. Run in background:

    nohup python3 tools/extract_r5_kfb_full.py >> extract_r5.log 2>&1 &
"""
from __future__ import annotations

import csv
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path

SRC = Path("/Volumes/R5_USB_14/KFB")
OUT = Path("data/labels_r5_kfb_full.csv")
D0 = date(2023, 1, 1)
D1 = date(2024, 2, 1)  # end-exclusive; days with no files just yield gaps
WORKERS = 8

FIELDS = [
    "filename", "camera", "label", "period", "source",
    "brightness_mean", "brightness_std", "edge_density",
    "saturation_mean", "upper_lower_contrast", "bright_spot_ratio",
    "far_grad", "far_wash", "far_std", "is_day",
]


def process_one(name: str) -> dict | None:
    from src.features import extract_features
    from src.heuristic import heuristic_label

    p = SRC / name
    try:
        feats = extract_features(p)
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"ERR {name}: {e}", flush=True)
        return None
    label = heuristic_label(feats)
    period = "day" if feats["is_day"] >= 0.5 else "night"
    return {
        "filename": name, "camera": "KFB", "label": label,
        "period": period, "source": "heuristic_r5_full",
        **{k: f"{v:.6f}" for k, v in feats.items()},
    }


def main() -> None:
    done: set[str] = set()
    newfile = not OUT.exists()
    if not newfile:
        with OUT.open() as f:
            for r in csv.DictReader(f):
                done.add(r["filename"])
        print(f"resume: {len(done)} frames already done", flush=True)
    else:
        with OUT.open("w", newline="") as f:
            csv.DictWriter(f, fieldnames=FIELDS).writeheader()

    days: list[date] = []
    d = D0
    while d < D1:
        days.append(d)
        d += timedelta(days=1)

    total = len(done)
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        for i, d in enumerate(days):
            names = [
                f"imgKFB_{d:%y%m%d}_{h:02d}{m:02d}.jpg"
                for h in range(24) for m in range(60)
            ]
            todo = [n for n in names if n not in done]
            if not todo:
                continue
            rows = [r for r in ex.map(process_one, todo) if r is not None]
            rows.sort(key=lambda r: r["filename"])
            if rows:
                with OUT.open("a", newline="") as f:
                    csv.DictWriter(f, fieldnames=FIELDS).writerows(rows)
                done.update(r["filename"] for r in rows)
                total += len(rows)
            if (i + 1) % 10 == 0 or d == days[-1]:
                print(f"{d} day_rows={len(rows)} total={total}", flush=True)
    print(f"DONE total={total} -> {OUT}", flush=True)


if __name__ == "__main__":
    main()
