"""Print stratified sample filenames from labels.csv for spot-checking."""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LABELS = ROOT / "data" / "labels.csv"
BUCKETS = [
    ("day", "inside_cloud"),
    ("day", "not_inside"),
    ("night", "inside_cloud"),
    ("night", "not_inside"),
]
SAMPLE = 3


def main() -> None:
    by_key: dict[tuple[str, str], list[str]] = {b: [] for b in BUCKETS}
    with LABELS.open(newline="") as f:
        for row in csv.DictReader(f):
            key = (row["period"], row["label"])
            if key in by_key:
                by_key[key].append(row["filename"])
    for period, label in BUCKETS:
        files = by_key[(period, label)]
        take = files[: min(SAMPLE, len(files))]
        print(f"{period} + {label} ({len(take)} shown, {len(files)} total):")
        for name in take:
            print(f"  {name}")
        if not take:
            print("  (none)")


if __name__ == "__main__":
    main()
