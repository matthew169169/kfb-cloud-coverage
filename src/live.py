"""Fetch the latest KFB webcam frame from HKO and run the predictor on it.

Frames are published at
https://www.weather.gov.hk/wxinfo/aws/hko_mica/kfb/imgKFB_YYMMDD_HHMM.jpg
every 5 minutes (HKT), typically a few minutes after the nominal time, so we
probe backwards from "now" until a frame exists.
"""
from __future__ import annotations

import tempfile
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

FRAME_BASE = "https://www.weather.gov.hk/wxinfo/aws/hko_mica/kfb/"
HKT = timezone(timedelta(hours=8))
STEP = timedelta(minutes=5)
MAX_LOOKBACK = 9  # 45 minutes
FETCH_TIMEOUT_S = 10
MIN_JPEG_BYTES = 1000


def frame_name(dt: datetime) -> str:
    return f"imgKFB_{dt:%y%m%d_%H%M}.jpg"


def candidate_times(now: datetime | None = None) -> list[datetime]:
    """Most recent 5-minute marks in HKT, newest first."""
    now = now or datetime.now(HKT)
    base = now.replace(minute=now.minute - now.minute % 5, second=0, microsecond=0)
    return [base - i * STEP for i in range(MAX_LOOKBACK)]


def fetch_latest() -> tuple[datetime, bytes] | None:
    """Return (photo time, jpeg bytes) of the newest available frame."""
    for ts in candidate_times():
        url = FRAME_BASE + frame_name(ts)
        req = urllib.request.Request(url, headers={"User-Agent": "kfb-cloud-coverage"})
        try:
            with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT_S) as resp:
                data = resp.read()
        except Exception:
            continue
        if len(data) >= MIN_JPEG_BYTES:
            return ts, data
    return None


def predict_latest() -> dict:
    """Fetch the newest frame and predict; returns a JSON-ready dict."""
    from src.predict import predict_path

    got = fetch_latest()
    if got is None:
        return {"ok": False, "error": "No recent KFB frame available from HKO."}
    ts, data = got
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp.write(data)
        path = Path(tmp.name)
    try:
        message = predict_path(path)
    finally:
        path.unlink(missing_ok=True)
    return {
        "ok": True,
        "photo_time": ts.strftime("%Y-%m-%d %H:%M HKT"),
        "image_url": FRAME_BASE + frame_name(ts),
        "message": message,
    }


def main() -> None:
    result = predict_latest()
    if not result["ok"]:
        raise SystemExit(result["error"])
    print(f"{result['photo_time']}: {result['message']}")


if __name__ == "__main__":
    main()
