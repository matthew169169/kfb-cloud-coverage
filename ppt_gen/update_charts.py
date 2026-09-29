"""Charts for the process-update deck, computed from models/train_report.json."""
from __future__ import annotations

import json
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

REPORT = T.ROOT / "models" / "train_report.json"


def load_report() -> dict:
    return json.loads(REPORT.read_text())


def cover_image(out: Path) -> None:
    src = next(T.IMAGES.glob("imgKFB_*.jpg"), None) if T.IMAGES.exists() else None
    if src is None:
        src = next(T.ROOT.glob("review_r5/grid_*.jpg"))
    img = Image.open(src).convert("RGB")
    h = img.height
    img = img.crop((0, int(h * 0.06), img.width, h))
    img = img.filter(ImageFilter.GaussianBlur(1.1))
    img = ImageEnhance.Brightness(img).enhance(0.48)
    img = ImageEnhance.Color(img).enhance(0.75)
    overlay = Image.new("RGB", img.size, (20, 42, 62))
    Image.blend(img, overlay, 0.38).save(out, quality=88)


def chart_data_mix(out: Path, report: dict) -> None:
    origins = report["counts"]["origins"]
    fig, ax = plt.subplots(figsize=(7.4, 3.5), dpi=200)
    labels = [
        "Golden 2016\n(human)",
        "R5 2023 hourly\n(full-year seed)",
        "Review 111\n(visual override)",
        "R5 extra minutes\n(Jan–Apr)",
    ]
    sizes = [
        origins.get("golden_2016", 142),
        origins.get("r5_hourly", 8101),
        origins.get("human_2023", 111),
        origins.get("r5_minute", 163989),
    ]
    colors = [T.HEX_GREEN, T.HEX_SKY, "#C47B2D", T.HEX_SLATE]
    bars = ax.barh(labels[::-1], sizes[::-1], color=colors[::-1], height=0.62)
    ax.set_xscale("log")
    ax.set_xlabel("Rows (log scale)")
    ax.bar_label(bars, labels=[f"{n:,}" for n in sizes[::-1]], padding=4, fontsize=10)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_title("Every unique labeled frame is in the combined model", fontsize=13)
    fig.tight_layout()
    fig.savefig(out, transparent=True)
    plt.close(fig)


def chart_accuracy(out: Path, report: dict) -> None:
    r111 = report["review_111"]
    fig, ax = plt.subplots(figsize=(7.6, 3.6), dpi=200)
    names = [
        "Heuristic\n111 GT",
        "d413d74\n111 GT",
        "Final\ntest 42,714",
        "Final\ngolden 142",
        "Final\n111 photos",
        "Final\nday 111",
        "Final\nnight 111",
    ]
    vals = [
        r111["heuristic"]["acc"],
        r111["old"]["acc"],
        report["holdout"]["test"]["acc"],
        report["golden_all_142"]["new"]["acc"],
        r111["new"]["acc"],
        r111["new_day"]["acc"],
        r111["new_night"]["acc"],
    ]
    colors = [T.HEX_SLATE, T.HEX_SLATE, T.HEX_SKY, T.HEX_GREEN,
              T.HEX_SKY, T.HEX_GREEN, "#C47B2D"]
    bars = ax.bar(range(len(names)), [v * 100 for v in vals], color=colors, width=0.72)
    ax.set_xticks(range(len(names)), names, fontsize=8.5)
    ax.set_ylabel("Accuracy %")
    ax.set_ylim(60, 105)
    ax.axhline(80, color="#D5DFE7", lw=1)
    ax.bar_label(bars, fmt="%.1f", fontsize=9, padding=2)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_title("Golden and day rose; night is still the gap", fontsize=13)
    fig.tight_layout()
    fig.savefig(out, transparent=True)
    plt.close(fig)


def chart_confusion_111(out: Path, report: dict) -> None:
    cm = np.array(report["review_111"]["new"]["cm"])
    acc = report["review_111"]["new"]["acc"]
    fig, ax = plt.subplots(figsize=(4.5, 3.7), dpi=200)
    ax.imshow(cm, cmap="Blues", vmin=0, vmax=cm.max() * 1.2)
    ticks = ["not_inside", "inside_cloud"]
    ax.set_xticks([0, 1], ticks, fontsize=11)
    ax.set_yticks([0, 1], ticks, fontsize=11)
    ax.set_xlabel("Predicted", fontsize=12)
    ax.set_ylabel("Ground truth (visual)", fontsize=12)
    for i in range(2):
        for j in range(2):
            color = "white" if cm[i, j] > cm.max() * 0.55 else T.HEX_NAVY
            ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                    fontsize=18, fontweight="bold", color=color)
    ax.set_title(f"111 visual 2023 photos  ·  acc {acc:.1%}", fontsize=12)
    fig.tight_layout()
    fig.savefig(out, transparent=True)
    plt.close(fig)


def chart_day_night(out: Path, report: dict) -> None:
    r111 = report["review_111"]
    fig, ax = plt.subplots(figsize=(5.2, 3.6), dpi=200)
    x = np.arange(2)
    w = 0.26
    heur = [78.18, 67.86]
    old = [r111["old_day"]["acc"] * 100, r111["old_night"]["acc"] * 100]
    new = [r111["new_day"]["acc"] * 100, r111["new_night"]["acc"] * 100]
    b1 = ax.bar(x - w, heur, w, color=T.HEX_SLATE, label="Heuristic")
    b2 = ax.bar(x, old, w, color="#8CA3B5", label="d413d74")
    b3 = ax.bar(x + w, new, w, color=T.HEX_SKY, label="Shipped final")
    ax.bar_label(b1, fmt="%.0f", fontsize=8, padding=2)
    ax.bar_label(b2, fmt="%.0f", fontsize=8, padding=2)
    ax.bar_label(b3, fmt="%.1f", fontsize=8, padding=2)
    ax.set_xticks(x, ["Day (n=55)", "Night (n=56)"], fontsize=12)
    ax.set_ylabel("Accuracy % vs visual GT")
    ax.set_ylim(50, 110)
    ax.legend(frameon=False, fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_title("111-photo check, day vs night", fontsize=12)
    fig.tight_layout()
    fig.savefig(out, transparent=True)
    plt.close(fig)


def build_all() -> Path:
    report = load_report()
    T.ASSETS.mkdir(parents=True, exist_ok=True)
    cover_image(T.ASSETS / "update_cover.jpg")
    chart_data_mix(T.ASSETS / "update_data.png", report)
    chart_accuracy(T.ASSETS / "update_acc.png", report)
    chart_confusion_111(T.ASSETS / "update_cm.png", report)
    chart_day_night(T.ASSETS / "update_dn.png", report)
    return T.ASSETS
