from src.heuristic import heuristic_label


def test_day_whiteout_inside():
    feats = {
        "brightness_mean": 176.0,
        "brightness_std": 50.0,
        "edge_density": 0.032,
        "saturation_mean": 0.046,
        "upper_lower_contrast": 0.27,
        "bright_spot_ratio": 0.43,
        "is_day": 1.0,
    }
    assert heuristic_label(feats) == "inside_cloud"


def test_day_clearish_not_inside():
    feats = {
        "brightness_mean": 155.0,
        "brightness_std": 74.0,
        "edge_density": 0.029,
        "saturation_mean": 0.053,
        "upper_lower_contrast": 0.50,
        "bright_spot_ratio": 0.45,
        "is_day": 1.0,
    }
    assert heuristic_label(feats) == "not_inside"


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


def test_night_fog_inside():
    feats = {
        "brightness_mean": 40.0,
        "brightness_std": 18.0,
        "edge_density": 0.016,
        "saturation_mean": 0.13,
        "upper_lower_contrast": 0.07,
        "bright_spot_ratio": 0.0005,
        "is_day": 0.0,
    }
    assert heuristic_label(feats) == "inside_cloud"
