# KFB Cloud Coverage Determination Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local Python pipeline that auto-labels KFB webcam images, trains a RandomForest on classical features, and prints fixed inside-cloud / cloud-base messages for day and night.

**Architecture:** Crop timestamp → extract brightness/edges/saturation/half-contrast (+ night bright-spots) → heuristic seed labels in CSV → date-split train RandomForest → `predict` emits the two fixed strings. Camera altitude constant = 150 m.

**Tech Stack:** Python 3.10+, numpy, Pillow, scikit-learn, joblib, pytest

**Note:** Workspace currently has no git repo. Skip commit steps unless user asks to `git init` / commit.

---

## File map

| File | Responsibility |
|------|----------------|
| `requirements.txt` | Dependencies |
| `src/__init__.py` | Package marker |
| `src/features.py` | Load image, day/night, feature vector |
| `src/heuristic.py` | Seed label from features |
| `src/messages.py` | Fixed output strings |
| `src/auto_label.py` | CLI: write `data/labels.csv` |
| `src/train.py` | CLI: train + save `models/cloud_clf.joblib` |
| `src/predict.py` | CLI: infer + print message |
| `tests/test_features.py` | Day/night + features |
| `tests/test_heuristic.py` | Heuristic labels |
| `tests/test_messages.py` | Message strings |
| `tests/test_smoke.py` | End-to-end on real images (if present) |

---

### Task 1: Scaffold

**Files:**
- Create: `requirements.txt`
- Create: `src/__init__.py`
- Create: `data/.gitkeep`
- Create: `models/.gitkeep`

- [ ] **Step 1: Write requirements and package dirs**

```text
numpy>=1.24
Pillow>=10.0
scikit-learn>=1.3
joblib>=1.3
pytest>=7.0
```

Create empty `src/__init__.py`, `data/.gitkeep`, `models/.gitkeep`.

- [ ] **Step 2: Install deps**

Run: `pip install -r requirements.txt`
Expected: packages install cleanly

- [ ] **Step 3: Commit (optional)** — skip if no git

---

### Task 2: Day/night + messages (TDD)

**Files:**
- Create: `src/messages.py`
- Create: `src/features.py` (partial: parse + day/night)
- Create: `tests/test_messages.py`
- Create: `tests/test_features.py`

- [ ] **Step 1: Write failing tests**

`tests/test_messages.py`:

```python
from src.messages import format_message

def test_inside_day():
    assert format_message(True, "day") == (
        "Camera is inside cloud (day). Cloud base at or below ~150 m."
    )

def test_not_inside():
    assert format_message(False, "night") == (
        "I am not inside cloud. The cloud base should be above 150 m."
    )
```

`tests/test_features.py` (day/night part):

```python
from src.features import parse_timestamp, is_day

def test_parse_timestamp():
    assert parse_timestamp("imgKFB_160101_0100.jpg") == (1, 0)  # hour, minute

def test_is_day_noon():
    assert is_day(hour=12, mean_brightness=120.0) is True

def test_is_night_0100():
    assert is_day(hour=1, mean_brightness=30.0) is False
```

- [ ] **Step 2: Run tests — expect FAIL**

Run: `pytest tests/test_messages.py tests/test_features.py -v`
Expected: FAIL (import errors)

- [ ] **Step 3: Implement**

`src/messages.py`:

```python
CAMERA_ALT_M = 150

def format_message(inside_cloud: bool, period: str) -> str:
    if inside_cloud:
        return (
            f"Camera is inside cloud ({period}). "
            f"Cloud base at or below ~{CAMERA_ALT_M} m."
        )
    return (
        f"I am not inside cloud. "
        f"The cloud base should be above {CAMERA_ALT_M} m."
    )
```

`src/features.py` (start):

```python
from pathlib import Path
import numpy as np
from PIL import Image

DAY_HOUR_START = 7
DAY_HOUR_END = 18
DAY_BRIGHT_MIN = 40.0

FEATURE_NAMES = [
    "brightness_mean",
    "brightness_std",
    "edge_density",
    "saturation_mean",
    "upper_lower_contrast",
    "bright_spot_ratio",
    "is_day",
]

def parse_timestamp(name: str) -> tuple[int, int]:
    stem = Path(name).stem  # imgKFB_160101_0100
    hhmm = stem.split("_")[-1]
    return int(hhmm[:2]), int(hhmm[2:4])

def is_day(hour: int, mean_brightness: float) -> bool:
    return DAY_HOUR_START <= hour < DAY_HOUR_END and mean_brightness >= DAY_BRIGHT_MIN
```

- [ ] **Step 4: Run tests — expect PASS**

Run: `pytest tests/test_messages.py tests/test_features.py -v`
Expected: PASS

---

### Task 3: Feature extraction

**Files:**
- Modify: `src/features.py`
- Modify: `tests/test_features.py`

- [ ] **Step 1: Add failing feature-shape test**

```python
import numpy as np
from PIL import Image
from src.features import extract_features, FEATURE_NAMES

def test_extract_features_shape(tmp_path):
    # tiny synthetic grey image
    arr = np.full((64, 64, 3), 180, dtype=np.uint8)
    p = tmp_path / "imgKFB_160101_1200.jpg"
    Image.fromarray(arr).save(p)
    feats = extract_features(p)
    assert list(feats.keys()) == FEATURE_NAMES
    assert feats["is_day"] in (0.0, 1.0)
```

- [ ] **Step 2: Run — expect FAIL**

Run: `pytest tests/test_features.py::test_extract_features_shape -v`
Expected: FAIL (`extract_features` missing)

- [ ] **Step 3: Implement `load_rgb`, `extract_features`**

Append to `src/features.py`:

```python
def load_rgb(path: Path) -> np.ndarray:
    img = Image.open(path).convert("RGB")
    arr = np.asarray(img, dtype=np.float32)
    # crop top-left timestamp banner (~8% height, full width ok to crop top strip)
    h = arr.shape[0]
    return arr[int(h * 0.08) :, :, :]

def _edge_density(gray: np.ndarray) -> float:
    # simple Laplacian magnitude mean
    g = gray
    up = np.roll(g, 1, 0)
    down = np.roll(g, -1, 0)
    left = np.roll(g, 1, 1)
    right = np.roll(g, -1, 1)
    lap = np.abs(4 * g - up - down - left - right)
    return float(lap.mean() / 255.0)

def extract_features(path: Path | str) -> dict[str, float]:
    path = Path(path)
    hour, _ = parse_timestamp(path.name)
    rgb = load_rgb(path)
    gray = rgb.mean(axis=2)
    bright_mean = float(gray.mean())
    bright_std = float(gray.std())
    # saturation approx: max-min per pixel / 255
    cmax = rgb.max(axis=2)
    cmin = rgb.min(axis=2)
    sat = float(((cmax - cmin) / 255.0).mean())
    mid = gray.shape[0] // 2
    upper = gray[:mid].mean()
    lower = gray[mid:].mean()
    upper_lower = float(abs(upper - lower) / 255.0)
    edge = _edge_density(gray)
    # night lights: fraction of pixels above high threshold
    bright_spot_ratio = float((gray > 200).mean())
    day = is_day(hour, bright_mean)
    return {
        "brightness_mean": bright_mean,
        "brightness_std": bright_std,
        "edge_density": edge,
        "saturation_mean": sat,
        "upper_lower_contrast": upper_lower,
        "bright_spot_ratio": bright_spot_ratio,
        "is_day": 1.0 if day else 0.0,
    }

def feature_vector(feats: dict[str, float]) -> np.ndarray:
    return np.array([feats[n] for n in FEATURE_NAMES], dtype=np.float64)
```

- [ ] **Step 4: Run — expect PASS**

Run: `pytest tests/test_features.py -v`
Expected: PASS

---

### Task 4: Heuristic labeling

**Files:**
- Create: `src/heuristic.py`
- Create: `tests/test_heuristic.py`

- [ ] **Step 1: Write failing tests**

```python
from src.heuristic import heuristic_label

def test_day_whiteout_inside():
    feats = {
        "brightness_mean": 200.0,
        "brightness_std": 15.0,
        "edge_density": 0.02,
        "saturation_mean": 0.05,
        "upper_lower_contrast": 0.02,
        "bright_spot_ratio": 0.0,
        "is_day": 1.0,
    }
    assert heuristic_label(feats) == "inside_cloud"

def test_night_lights_not_inside():
    feats = {
        "brightness_mean": 25.0,
        "brightness_std": 40.0,
        "edge_density": 0.08,
        "saturation_mean": 0.1,
        "upper_lower_contrast": 0.15,
        "bright_spot_ratio": 0.02,
        "is_day": 0.0,
    }
    assert heuristic_label(feats) == "not_inside"
```

- [ ] **Step 2: Run — expect FAIL**

Run: `pytest tests/test_heuristic.py -v`
Expected: FAIL

- [ ] **Step 3: Implement**

`src/heuristic.py`:

```python
def heuristic_label(feats: dict[str, float]) -> str:
    """Seed label: inside_cloud | not_inside."""
    day = feats["is_day"] >= 0.5
    low_structure = (
        feats["brightness_std"] < 28.0
        and feats["edge_density"] < 0.045
        and feats["saturation_mean"] < 0.12
    )
    if day:
        # bright + washed / low structure → inside
        if feats["brightness_mean"] > 140 and low_structure:
            return "inside_cloud"
        if feats["edge_density"] < 0.03 and feats["upper_lower_contrast"] < 0.04:
            return "inside_cloud"
        return "not_inside"
    # night: no valley lights + flat → inside
    if feats["bright_spot_ratio"] < 0.002 and feats["brightness_std"] < 25.0:
        return "inside_cloud"
    if feats["bright_spot_ratio"] >= 0.005:
        return "not_inside"
    if low_structure:
        return "inside_cloud"
    return "not_inside"
```

- [ ] **Step 4: Run — expect PASS**

Run: `pytest tests/test_heuristic.py -v`
Expected: PASS

---

### Task 5: Auto-label CLI

**Files:**
- Create: `src/auto_label.py`

- [ ] **Step 1: Implement CLI**

```python
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
```

- [ ] **Step 2: Run on full set (may take a few minutes)**

Run: `python -m src.auto_label`
Expected: `data/labels.csv` with ~3497 rows and class counts printed

---

### Task 6: Train

**Files:**
- Create: `src/train.py`

- [ ] **Step 1: Implement train with date split**

```python
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
    # imgKFB_160101_0100.jpg -> 160101
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
```

- [ ] **Step 2: Run train**

Run: `python -m src.train`
Expected: accuracy + confusion matrix printed; `models/cloud_clf.joblib` exists

---

### Task 7: Predict CLI

**Files:**
- Create: `src/predict.py`
- Create: `tests/test_smoke.py`

- [ ] **Step 1: Implement predict**

```python
"""Predict inside-cloud and print fixed message."""
from __future__ import annotations
import sys
from pathlib import Path
from joblib import load
from src.features import extract_features, feature_vector, FEATURE_NAMES
from src.messages import format_message

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "models" / "cloud_clf.joblib"

def predict_path(path: Path) -> str:
    bundle = load(MODEL)
    clf = bundle["model"]
    feats = extract_features(path)
    period = "day" if feats["is_day"] >= 0.5 else "night"
    x = feature_vector(feats).reshape(1, -1)
    inside = bool(clf.predict(x)[0] == 1)
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
```

- [ ] **Step 2: Smoke test file**

`tests/test_smoke.py`:

```python
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "models" / "cloud_clf.joblib"
IMG = ROOT / "image"

@pytest.mark.skipif(not MODEL.exists(), reason="model not trained")
def test_predict_night_and_day():
    from src.predict import predict_path
    night = IMG / "imgKFB_160101_0100.jpg"
    day = IMG / "imgKFB_160101_1200.jpg"
    assert night.exists() and day.exists()
    mn = predict_path(night)
    md = predict_path(day)
    assert "150 m" in mn and "150 m" in md
    assert mn.startswith("Camera is inside") or mn.startswith("I am not inside")
    assert md.startswith("Camera is inside") or md.startswith("I am not inside")
```

- [ ] **Step 3: Run predict on samples + pytest**

Run:
```bash
python -m src.predict image/imgKFB_160101_0100.jpg image/imgKFB_160101_1200.jpg image/imgKFB_160110_1550.jpg
pytest -v
```
Expected: three messages printed; all tests PASS

---

### Task 8: Spot-check helper + README

**Files:**
- Create: `README.md`
- Create: `src/sample_review.py` (optional tiny helper)

- [ ] **Step 1: Write README with run instructions**

```markdown
# KFB cloud coverage

## Setup
pip install -r requirements.txt

## Pipeline
python -m src.auto_label
# edit data/labels.csv label column if needed
python -m src.train
python -m src.predict image/imgKFB_160101_1200.jpg

## Tests
pytest -v
```

- [ ] **Step 2: Quick review script (print 12 stratified samples)**

`src/sample_review.py` — load `labels.csv`, print 3 day-inside, 3 day-not, 3 night-inside, 3 night-not filenames for manual eye-check. Keep under ~40 lines.

- [ ] **Step 3: Full verification**

Run: `pytest -v && python -m src.sample_review`
Expected: green tests; sample list printed for human review

---

## Spec coverage checklist

| Spec item | Task |
|-----------|------|
| Day/night inside-cloud detection | 2–4, 7 |
| Fixed messages @ 150 m | 2, 7 |
| Heuristic auto-label + CSV edit | 4, 5 |
| RandomForest train, date split, metrics | 6 |
| predict CLI | 7 |
| Unit + smoke tests | 2–4, 7 |
| No RH / no CNN / no web | respected |

## Self-review notes

- No TBD placeholders
- `FEATURE_NAMES` / label strings consistent across modules
- Thresholds in `heuristic.py` are starting points; tune after `sample_review` eye-check
