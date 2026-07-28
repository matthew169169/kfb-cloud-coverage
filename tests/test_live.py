from datetime import datetime

from src.live import HKT, MAX_LOOKBACK, candidate_times, frame_name


def test_frame_name_format():
    dt = datetime(2026, 7, 28, 9, 55, tzinfo=HKT)
    assert frame_name(dt) == "imgKFB_260728_0955.jpg"


def test_frame_name_zero_padding():
    dt = datetime(2026, 1, 3, 0, 5, tzinfo=HKT)
    assert frame_name(dt) == "imgKFB_260103_0005.jpg"


def test_candidate_times_floors_to_5_minutes():
    now = datetime(2026, 7, 28, 10, 9, 42, tzinfo=HKT)
    cands = candidate_times(now)
    assert cands[0] == datetime(2026, 7, 28, 10, 5, tzinfo=HKT)
    assert cands[1] == datetime(2026, 7, 28, 10, 0, tzinfo=HKT)
    assert len(cands) == MAX_LOOKBACK


def test_candidate_times_cross_midnight():
    now = datetime(2026, 7, 28, 0, 2, tzinfo=HKT)
    cands = candidate_times(now)
    assert cands[0] == datetime(2026, 7, 28, 0, 0, tzinfo=HKT)
    assert cands[1] == datetime(2026, 7, 27, 23, 55, tzinfo=HKT)
