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
