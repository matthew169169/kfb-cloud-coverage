"""Build chart PNGs and the cover image used by the deck."""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

from ppt_gen import theme as T

plt.rcParams["font.family"] = ["Helvetica Neue", "Heiti TC", "Arial Unicode MS"]
plt.rcParams["axes.edgecolor"] = "#B9C6D0"
plt.rcParams["text.color"] = T.HEX_NAVY
plt.rcParams["axes.labelcolor"] = T.HEX_NAVY
plt.rcParams["xtick.color"] = T.HEX_NAVY
plt.rcParams["ytick.color"] = T.HEX_NAVY

LABELS_CSV = T.ROOT / "data" / "labels.csv"


def _load_rows() -> list[dict]:
    with LABELS_CSV.open() as f:
        return list(csv.DictReader(f))


def chart_distribution(out: Path) -> None:
    rows = _load_rows()
    combos = {
        ("day", "not_inside"): 0, ("day", "inside_cloud"): 0,
        ("night", "not_inside"): 0, ("night", "inside_cloud"): 0,
    }
    for r in rows:
        combos[(r["period"], r["label"])] += 1

    fig, ax = plt.subplots(figsize=(6.4, 3.6), dpi=200)
    groups = ["Day", "Night"]
    not_in = [combos[("day", "not_inside")], combos[("night", "not_inside")]]
    inside = [combos[("day", "inside_cloud")], combos[("night", "inside_cloud")]]
    x = np.arange(2)
    w = 0.34
    b1 = ax.bar(x - w / 2, not_in, w, color=T.HEX_SKY, label="not_inside (clear view)")
    b2 = ax.bar(x + w / 2, inside, w, color=T.HEX_SLATE, label="inside_cloud (in cloud)")
    for bars in (b1, b2):
        ax.bar_label(bars, fontsize=11, padding=2)
    ax.set_xticks(x, groups, fontsize=12)
    ax.set_ylabel("Images")
    ax.set_ylim(0, 1450)
    ax.legend(frameon=False, fontsize=10, loc="upper right")
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_title(f"Auto-label distribution ({len(rows)} images, Jan 2016)", fontsize=13)
    fig.tight_layout()
    fig.savefig(out, transparent=True)
    plt.close(fig)


def chart_confusion(out: Path) -> None:
    # Confusion matrix from re-running the date-split logreg evaluation.
    cm = np.array([[112, 17], [18, 311]])
    acc = (cm[0, 0] + cm[1, 1]) / cm.sum()

    fig, ax = plt.subplots(figsize=(4.4, 3.6), dpi=200)
    ax.imshow(cm, cmap="Blues", vmin=0, vmax=cm.max() * 1.15)
    ticks = ["not_inside", "inside_cloud"]
    ax.set_xticks([0, 1], ticks, fontsize=11)
    ax.set_yticks([0, 1], ticks, fontsize=11)
    ax.set_xlabel("Predicted", fontsize=12)
    ax.set_ylabel("Actual", fontsize=12)
    for i in range(2):
        for j in range(2):
            color = "white" if cm[i, j] > cm.max() * 0.6 else T.HEX_NAVY
            ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                    fontsize=17, fontweight="bold", color=color)
    ax.set_title(f"Confusion matrix (test accuracy {acc:.1%})", fontsize=13)
    fig.tight_layout()
    fig.savefig(out, transparent=True)
    plt.close(fig)


def chart_features(out: Path) -> None:
    """Standardized logistic-regression weights (sign = push toward inside_cloud)."""
    import warnings

    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    names = ["brightness_mean", "brightness_std", "edge_density", "saturation_mean",
             "upper_lower_contrast", "bright_spot_ratio", "is_day"]
    labels = {
        "brightness_mean": "Brightness mean",
        "brightness_std": "Brightness std",
        "edge_density": "Edge density",
        "saturation_mean": "Saturation mean",
        "upper_lower_contrast": "Upper/lower contrast",
        "bright_spot_ratio": "Bright-spot ratio (night lights)",
        "is_day": "Day/night flag",
    }
    rows = _load_rows()

    def dk(fn: str) -> str:
        return Path(fn).stem.split("_")[1]

    dates = sorted({dk(r["filename"]) for r in rows})
    train_dates = set(dates[: max(1, int(len(dates) * 0.8))])
    X, y = [], []
    for r in rows:
        if dk(r["filename"]) in train_dates:
            X.append([float(r[n]) for n in names])
            y.append(1 if r["label"] == "inside_cloud" else 0)
    pipe = Pipeline([
        ("s", StandardScaler()),
        ("c", LogisticRegression(max_iter=2000, random_state=42,
                                 class_weight="balanced", C=0.5)),
    ])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        pipe.fit(np.array(X), np.array(y))
    w = pipe.named_steps["c"].coef_.ravel()

    order = np.argsort(np.abs(w))
    fig, ax = plt.subplots(figsize=(6.6, 3.6), dpi=200)
    colors = [T.HEX_SLATE if v > 0 else T.HEX_SKY for v in w[order]]
    ax.barh([labels[names[i]] for i in order], w[order], color=colors, height=0.62)
    ax.axvline(0, color="#B9C6D0", lw=1)
    ax.set_xlabel("Standardized weight (right = toward inside_cloud)", fontsize=11)
    ax.tick_params(axis="y", labelsize=11)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_title("Logistic-regression feature weights", fontsize=13)
    fig.tight_layout()
    fig.savefig(out, transparent=True)
    plt.close(fig)


def cover_image(out: Path) -> None:
    """Darkened + softened KFB photo as the title-slide backdrop."""
    src = T.IMAGES / "imgKFB_160101_1200.jpg"
    img = Image.open(src).convert("RGB")
    img = img.crop((0, int(img.height * 0.08), img.width, img.height))
    img = img.filter(ImageFilter.GaussianBlur(1.2))
    img = ImageEnhance.Brightness(img).enhance(0.55)
    img = ImageEnhance.Color(img).enhance(0.8)
    overlay = Image.new("RGB", img.size, (20, 42, 62))
    img = Image.blend(img, overlay, 0.35)
    img.save(out, quality=88)


def build_all() -> None:
    T.ASSETS.mkdir(parents=True, exist_ok=True)
    chart_distribution(T.ASSETS / "distribution.png")
    chart_confusion(T.ASSETS / "confusion.png")
    chart_features(T.ASSETS / "features.png")
    cover_image(T.ASSETS / "cover.jpg")
    print("assets ready:", sorted(p.name for p in T.ASSETS.iterdir()))


if __name__ == "__main__":
    build_all()
