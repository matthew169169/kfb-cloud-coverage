def heuristic_label(feats: dict[str, float]) -> str:
    """inside_cloud | not_inside — mid/far fog cues (ignore dark foreground trees)."""
    day = feats["is_day"] >= 0.5
    if day:
        # Soft fog / in cloud (e.g. 160101_1550): washed far field, low texture
        if feats["far_wash"] >= 0.60 and feats["far_grad"] <= 5.0:
            return "inside_cloud"
        # Hard whiteout
        if feats["far_std"] <= 30.0 and feats["far_wash"] >= 0.75:
            return "inside_cloud"
        if feats["far_wash"] >= 0.85 and feats["far_grad"] <= 6.0:
            return "inside_cloud"
        return "not_inside"

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
