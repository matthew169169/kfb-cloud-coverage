from src.features import parse_timestamp, is_day


def test_parse_timestamp():
    assert parse_timestamp("imgKFB_160101_0100.jpg") == (1, 0)  # hour, minute


def test_is_day_noon():
    assert is_day(hour=12, mean_brightness=120.0) is True


def test_is_night_0100():
    assert is_day(hour=1, mean_brightness=30.0) is False
