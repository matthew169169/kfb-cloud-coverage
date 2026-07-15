def heuristic_label(feats: dict[str, float]) -> str:
    """Seed / deploy label: inside_cloud | not_inside.

    Day: ignore dark foreground trees — use mid/far wash + gradient.
    Soft fog (valley gone, trees still dark) has low far_grad + high far_wash.
    Night: city lights (bright spots) ⇒ not inside.
    """
    day = feats["is_day"] >= 0.5
    if day:
        # Soft fog / camera in cloud layer (e.g. imgKFB_160101_1550)
        if feats["far_grad"] <= 3.5 and feats["far_wash"] >= 0.65:
            return "inside_cloud"
        # Hard whiteout
        if feats["far_std"] <= 28.0 and feats["far_wash"] >= 0.80:
            return "inside_cloud"
        if (
            feats["far_grad"] <= 4.3
            and feats["far_wash"] >= 0.88
            and feats["far_std"] <= 32.0
        ):
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
