from src.heuristic import heuristic_label


def _base(**kwargs):
    feats = {
        "brightness_mean": 150.0,
        "brightness_std": 50.0,
        "edge_density": 0.03,
        "saturation_mean": 0.05,
        "upper_lower_contrast": 0.45,
        "bright_spot_ratio": 0.3,
        "far_grad": 5.0,
        "far_wash": 0.5,
        "far_std": 40.0,
        "is_day": 1.0,
    }
    feats.update(kwargs)
    return feats


def test_day_soft_fog_1550_inside():
    assert (
        heuristic_label(
            _base(
                brightness_mean=146,
                brightness_std=75,
                upper_lower_contrast=0.49,
                far_grad=2.5,
                far_wash=0.74,
                far_std=46,
            )
        )
        == "inside_cloud"
    )


def test_day_whiteout_inside():
    assert (
        heuristic_label(
            _base(far_grad=4.1, far_wash=0.95, far_std=23, upper_lower_contrast=0.27)
        )
        == "inside_cloud"
    )


def test_day_clear_structure_not_inside():
    assert (
        heuristic_label(_base(far_grad=9.0, far_wash=0.62, far_std=56))
        == "not_inside"
    )


def test_night_lights_not_inside():
    assert (
        heuristic_label(
            _base(
                is_day=0.0,
                brightness_mean=25,
                brightness_std=40,
                bright_spot_ratio=0.02,
                upper_lower_contrast=0.15,
            )
        )
        == "not_inside"
    )


def test_night_fog_inside():
    assert (
        heuristic_label(
            _base(
                is_day=0.0,
                brightness_mean=40,
                brightness_std=18,
                bright_spot_ratio=0.0005,
                upper_lower_contrast=0.07,
            )
        )
        == "inside_cloud"
    )
