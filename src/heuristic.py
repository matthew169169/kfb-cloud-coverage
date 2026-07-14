def heuristic_label(feats: dict[str, float]) -> str:
    """Seed label: inside_cloud | not_inside."""
    day = feats["is_day"] >= 0.5
    if day:
        # Fog whiteout: bright, low edges/sat; upper-lower gap moderate
        # (dark trees keep brightness_std high — do NOT require low std)
        if (
            feats["brightness_mean"] > 140.0
            and feats["edge_density"] < 0.030
            and feats["saturation_mean"] < 0.09
            and feats["upper_lower_contrast"] < 0.35
        ):
            return "inside_cloud"
        if feats["edge_density"] < 0.015 and feats["saturation_mean"] < 0.06:
            return "inside_cloud"
        return "not_inside"
    # night unchanged
    low_structure = (
        feats["brightness_std"] < 28.0
        and feats["edge_density"] < 0.045
        and feats["saturation_mean"] < 0.12
    )
    if feats["bright_spot_ratio"] < 0.002 and feats["brightness_std"] < 25.0:
        return "inside_cloud"
    if feats["bright_spot_ratio"] >= 0.005:
        return "not_inside"
    if low_structure:
        return "inside_cloud"
    return "not_inside"
