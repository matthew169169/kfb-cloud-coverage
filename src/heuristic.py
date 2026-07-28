def heuristic_label(feats: dict[str, float]) -> str:
    """inside_cloud | not_inside — seed-label rules, tuned on the golden set.

    Thresholds were grid-searched against data/golden_labels.csv with
    leave-one-date-out CV (tools/eval_golden.py). Haze with a visible valley
    counts as not_inside; only a washed-out, textureless far field (day) or a
    lightless flat frame (night) counts as inside_cloud.

    The trained logistic model (models/cloud_logreg.json) outperforms these
    rules and is what predict/web/browser use; the rules remain for
    auto-labeling and as an offline fallback.
    """
    day = feats["is_day"] >= 0.5
    if day:
        if feats["far_wash"] >= 0.85 and feats["far_grad"] <= 4.0:
            return "inside_cloud"
        if feats["far_std"] <= 5.0 and feats["far_wash"] >= 0.90:
            return "inside_cloud"
        return "not_inside"
    if feats["bright_spot_ratio"] <= 0.0005 and feats["brightness_std"] <= 10.0:
        return "inside_cloud"
    return "not_inside"
