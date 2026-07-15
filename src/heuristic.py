def heuristic_label(feats: dict[str, float]) -> str:
    """Seed label: inside_cloud | not_inside.

    Tuned for MAX_SIDE=640 features (must match train + browser).
    Day cue: fog whiteout flattens upper/lower contrast (valley gone).
    Night cue: valley city lights visible as bright spots.
    """
    day = feats["is_day"] >= 0.5
    if day:
        # Thick cloud / fog at camera: bright, grey, valley contrast collapsed.
        if (
            feats["brightness_mean"] >= 145.0
            and feats["saturation_mean"] <= 0.085
            and feats["upper_lower_contrast"] <= 0.38
        ):
            return "inside_cloud"
        # Very washed scene
        if (
            feats["brightness_mean"] >= 160.0
            and feats["brightness_std"] <= 55.0
            and feats["upper_lower_contrast"] <= 0.32
        ):
            return "inside_cloud"
        return "not_inside"

    # Night: visible point lights ⇒ not inside cloud/fog
    if feats["bright_spot_ratio"] >= 0.004:
        return "not_inside"
    if feats["bright_spot_ratio"] < 0.0015 and feats["brightness_std"] < 22.0:
        return "inside_cloud"
    if (
        feats["bright_spot_ratio"] < 0.003
        and feats["brightness_std"] < 30.0
        and feats["upper_lower_contrast"] < 0.10
    ):
        return "inside_cloud"
    return "not_inside"
