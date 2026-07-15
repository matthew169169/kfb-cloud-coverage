from pathlib import Path

import numpy as np
from PIL import Image

# Image-only day/night: mean brightness after cropping timestamp banner.
# KFB day scenes are typically >140; night (even with city lights) usually <60.
DAY_BRIGHT_MIN = 80.0

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
    """Optional helper for filenames; not used for day/night."""
    stem = Path(name).stem  # imgKFB_160101_0100
    hhmm = stem.split("_")[-1]
    return int(hhmm[:2]), int(hhmm[2:4])


def is_day(mean_brightness: float) -> bool:
    """Day/night from photo brightness only (no filename)."""
    return mean_brightness >= DAY_BRIGHT_MIN


def load_rgb(path: Path) -> np.ndarray:
    img = Image.open(path).convert("RGB")
    # Downscale large uploads — big win for Render free-tier RAM.
    img.thumbnail((640, 640))
    arr = np.asarray(img, dtype=np.float32)
    # crop top timestamp banner (~8% height)
    h = arr.shape[0]
    return arr[int(h * 0.08) :, :, :]


def _edge_density(gray: np.ndarray) -> float:
    g = gray
    up = np.roll(g, 1, 0)
    down = np.roll(g, -1, 0)
    left = np.roll(g, 1, 1)
    right = np.roll(g, -1, 1)
    lap = np.abs(4 * g - up - down - left - right)
    return float(lap.mean() / 255.0)


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
    day = is_day(bright_mean)
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
