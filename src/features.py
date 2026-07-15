from pathlib import Path

import numpy as np
from PIL import Image

DAY_BRIGHT_MIN = 80.0
MAX_SIDE = 640

FEATURE_NAMES = [
    "brightness_mean",
    "brightness_std",
    "edge_density",
    "saturation_mean",
    "upper_lower_contrast",
    "bright_spot_ratio",
    "far_grad",
    "far_wash",
    "far_std",
    "is_day",
]


def parse_timestamp(name: str) -> tuple[int, int]:
    stem = Path(name).stem
    hhmm = stem.split("_")[-1]
    return int(hhmm[:2]), int(hhmm[2:4])


def is_day(mean_brightness: float) -> bool:
    return mean_brightness >= DAY_BRIGHT_MIN


def load_rgb(path: Path) -> np.ndarray:
    """Match browser canvas: bilinear resize to fit MAX_SIDE, then crop banner."""
    img = Image.open(path).convert("RGB")
    w, h = img.size
    scale = min(1.0, MAX_SIDE / max(w, h))
    nw = max(1, round(w * scale))
    nh = max(1, round(h * scale))
    if (nw, nh) != (w, h):
        img = img.resize((nw, nh), Image.BILINEAR)
    arr = np.asarray(img, dtype=np.float32)
    return arr[int(arr.shape[0] * 0.08) :, :, :]


def _edge_density(gray: np.ndarray) -> float:
    g = gray
    up = np.roll(g, 1, 0)
    down = np.roll(g, -1, 0)
    left = np.roll(g, 1, 1)
    right = np.roll(g, -1, 1)
    lap = np.abs(4 * g - up - down - left - right)
    return float(lap.mean() / 255.0)


def _far_metrics(gray: np.ndarray) -> tuple[float, float, float]:
    h = gray.shape[0]
    y0 = int(h * 0.05)
    y1 = max(y0 + 1, int(h * 0.72))
    far = gray[y0:y1]
    gx = float(np.abs(np.diff(far, axis=1)).mean())
    gy = float(np.abs(np.diff(far, axis=0)).mean())
    wash = float((far > 170).mean())
    return gx + gy, wash, float(far.std())


def extract_features(path: Path | str) -> dict[str, float]:
    path = Path(path)
    rgb = load_rgb(path)
    gray = rgb.mean(axis=2)
    bright_mean = float(gray.mean())
    bright_std = float(gray.std())
    cmax = rgb.max(axis=2)
    cmin = rgb.min(axis=2)
    sat = float(((cmax - cmin) / 255.0).mean())
    mid = gray.shape[0] // 2
    upper = gray[:mid].mean()
    lower = gray[mid:].mean()
    upper_lower = float(abs(upper - lower) / 255.0)
    edge = _edge_density(gray)
    bright_spot_ratio = float((gray > 200).mean())
    far_grad, far_wash, far_std = _far_metrics(gray)
    day = is_day(bright_mean)
    return {
        "brightness_mean": bright_mean,
        "brightness_std": bright_std,
        "edge_density": edge,
        "saturation_mean": sat,
        "upper_lower_contrast": upper_lower,
        "bright_spot_ratio": bright_spot_ratio,
        "far_grad": far_grad,
        "far_wash": far_wash,
        "far_std": far_std,
        "is_day": 1.0 if day else 0.0,
    }


def feature_vector(feats: dict[str, float]) -> np.ndarray:
    return np.array([feats[n] for n in FEATURE_NAMES], dtype=np.float64)
