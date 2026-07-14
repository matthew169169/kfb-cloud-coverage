from pathlib import Path

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
