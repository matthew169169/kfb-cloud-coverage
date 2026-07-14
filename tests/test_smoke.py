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
