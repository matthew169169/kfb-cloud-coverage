def heuristic_label(feats: dict[str, float]) -> str:
    """Seed label: inside_cloud | not_inside."""
    day = feats["is_day"] >= 0.5
    low_structure = (
        feats["brightness_std"] < 28.0
        and feats["edge_density"] < 0.045
        and feats["saturation_mean"] < 0.12
    )
    if day:
        if feats["brightness_mean"] > 140 and low_structure:
            return "inside_cloud"
        if feats["edge_density"] < 0.03 and feats["upper_lower_contrast"] < 0.04:
            return "inside_cloud"
        return "not_inside"
    if feats["bright_spot_ratio"] < 0.002 and feats["brightness_std"] < 25.0:
        return "inside_cloud"
    if feats["bright_spot_ratio"] >= 0.005:
        return "not_inside"
    if low_structure:
        return "inside_cloud"
    return "not_inside"
