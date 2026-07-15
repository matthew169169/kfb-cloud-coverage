import numpy as np
from PIL import Image

from src.features import extract_features, FEATURE_NAMES, parse_timestamp, is_day


def test_extract_features_shape(tmp_path):
    arr = np.full((64, 64, 3), 180, dtype=np.uint8)
    p = tmp_path / "imgKFB_160101_1200.jpg"
    Image.fromarray(arr).save(p)
    feats = extract_features(p)
    assert list(feats.keys()) == FEATURE_NAMES
    assert feats["is_day"] == 1.0
    assert "far_grad" in feats and "far_wash" in feats


def test_extract_features_dark_is_night(tmp_path):
    arr = np.full((64, 64, 3), 20, dtype=np.uint8)
    # filename says noon — must still be night from brightness
    p = tmp_path / "imgKFB_160101_1200.jpg"
    Image.fromarray(arr).save(p)
    feats = extract_features(p)
    assert feats["is_day"] == 0.0


def test_parse_timestamp():
    assert parse_timestamp("imgKFB_160101_0100.jpg") == (1, 0)


def test_is_day_bright():
    assert is_day(120.0) is True


def test_is_night_dark():
    assert is_day(30.0) is False
