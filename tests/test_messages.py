from src.messages import format_message


def test_inside_day():
    assert format_message(True, "day") == (
        "Camera is inside cloud (day). Cloud base at or below ~150 m."
    )


def test_not_inside_night():
    assert format_message(False, "night") == (
        "I am not inside cloud (night). The cloud base should be above 150 m."
    )


def test_not_inside_day():
    assert format_message(False, "day") == (
        "I am not inside cloud (day). The cloud base should be above 150 m."
    )
