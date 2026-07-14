import numpy as np
from PIL import Image

from src.features import extract_features, FEATURE_NAMES, parse_timestamp, is_day


def test_extract_features_shape(tmp_path):
    # tiny synthetic grey image
    arr = np.full((64, 64, 3), 180, dtype=np.uint8)
    p = tmp_path / "imgKFB_160101_1200.jpg"
    Image.fromarray(arr).save(p)
    feats = extract_features(p)
    assert list(feats.keys()) == FEATURE_NAMES
    assert feats["is_day"] in (0.0, 1.0)


def test_parse_timestamp():
    assert parse_timestamp("imgKFB_160101_0100.jpg") == (1, 0)  # hour, minute


def test_is_day_noon():
    assert is_day(hour=12, mean_brightness=120.0) is True


def test_is_night_0100():
    assert is_day(hour=1, mean_brightness=30.0) is False
