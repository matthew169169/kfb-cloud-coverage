CAMERA_ALT_M = 150


def format_message(inside_cloud: bool, period: str) -> str:
    if inside_cloud:
        return (
            f"Camera is inside cloud ({period}). "
            f"Cloud base at or below ~{CAMERA_ALT_M} m."
        )
    return (
        f"I am not inside cloud ({period}). "
        f"The cloud base should be above {CAMERA_ALT_M} m."
    )
