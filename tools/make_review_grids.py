"""Build stratified 3x3 review grids so a human (or vision model) can
hand-label a golden validation set quickly.

Reads data/labels.csv (heuristic labels), samples per (period, label) cell
plus borderline cases near the day fog thresholds, renders numbered grids to
/tmp/golden_grids/ and writes the sample manifest to /tmp/golden_sample.csv.
"""
from __future__ import annotations

import csv
import random
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
LABELS = ROOT / "data" / "labels.csv"
IMAGE_DIR = ROOT / "image"
OUT_DIR = Path("/tmp/golden_grids")
MANIFEST = Path("/tmp/golden_sample.csv")

PER_CELL = 30
N_BORDERLINE = 24
CELL_W, CELL_H = 512, 288
COLS = ROWS = 3


def sample_rows() -> list[dict]:
    with LABELS.open() as f:
        rows = list(csv.DictReader(f))
    rng = random.Random(42)
    picked: dict[str, dict] = {}

    for period in ("day", "night"):
        for label in ("inside_cloud", "not_inside"):
            cell = [r for r in rows if r["period"] == period and r["label"] == label]
            for r in rng.sample(cell, min(PER_CELL, len(cell))):
                picked[r["filename"]] = r

    # borderline day cases: closest to the far_wash >= 0.60 rule boundary
    day = sorted(
        (r for r in rows if r["period"] == "day"),
        key=lambda r: abs(float(r["far_wash"]) - 0.60),
    )
    for r in day[: N_BORDERLINE // 2]:
        picked[r["filename"]] = r
    # borderline night cases: bright_spot_ratio near the 0.004 rule boundary
    night = sorted(
        (r for r in rows if r["period"] == "night"),
        key=lambda r: abs(float(r["bright_spot_ratio"]) - 0.004),
    )
    for r in night[: N_BORDERLINE // 2]:
        picked[r["filename"]] = r

    out = sorted(picked.values(), key=lambda r: r["filename"])
    rng.shuffle(out)
    return out


def render_grids(rows: list[dict]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for f in OUT_DIR.glob("grid_*.jpg"):
        f.unlink()
    per_grid = COLS * ROWS
    for g in range(0, len(rows), per_grid):
        chunk = rows[g : g + per_grid]
        canvas = Image.new("RGB", (CELL_W * COLS, (CELL_H + 22) * ROWS), "black")
        draw = ImageDraw.Draw(canvas)
        for i, r in enumerate(chunk):
            cx = (i % COLS) * CELL_W
            cy = (i // COLS) * (CELL_H + 22)
            img = Image.open(IMAGE_DIR / r["filename"]).convert("RGB")
            img = img.resize((CELL_W, CELL_H), Image.BILINEAR)
            canvas.paste(img, (cx, cy))
            tag = f"#{g + i + 1}  {r['filename']}  heur={r['label']}"
            draw.text((cx + 6, cy + CELL_H + 4), tag, fill="yellow")
        idx = g // per_grid + 1
        canvas.save(OUT_DIR / f"grid_{idx:02d}.jpg", quality=88)
    print(f"wrote {(len(rows) + per_grid - 1) // per_grid} grids to {OUT_DIR}")


def main() -> None:
    rows = sample_rows()
    with MANIFEST.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["n", "filename", "period", "heuristic"])
        w.writeheader()
        for i, r in enumerate(rows, start=1):
            w.writerow({"n": i, "filename": r["filename"],
                        "period": r["period"], "heuristic": r["label"]})
    render_grids(rows)
    print(f"manifest: {MANIFEST} ({len(rows)} images)")


if __name__ == "__main__":
    main()
