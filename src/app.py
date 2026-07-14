"""Simple web UI: upload a photo → cloud / day-night result."""
from __future__ import annotations

import os
from pathlib import Path

import gradio as gr

from src.predict import predict_path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = [
    str(ROOT / "image" / "imgKFB_160101_0100.jpg"),
    str(ROOT / "image" / "imgKFB_160101_1200.jpg"),
    str(ROOT / "image" / "imgKFB_160103_1400.jpg"),
]


def analyze(image_path: str | None) -> str:
    if not image_path:
        return "Please upload a photo."
    try:
        return predict_path(Path(image_path))
    except FileNotFoundError as e:
        return str(e)
    except Exception as e:
        return f"Could not analyze this image: {e}"


def build_demo() -> gr.Blocks:
    examples = [p for p in EXAMPLES if Path(p).exists()]
    return gr.Interface(
        fn=analyze,
        inputs=gr.Image(
            type="filepath",
            label="Upload weather-camera photo",
            sources=["upload"],
        ),
        outputs=gr.Textbox(label="Result", lines=3),
        title="KFB Cloud Coverage",
        description=(
            "Upload a photo. Day/night is judged from image brightness only "
            "(not the filename). Result says if the camera is inside cloud, "
            "and whether cloud base is at/below or above ~150 m."
        ),
        examples=examples or None,
        flagging_mode="never",
    )


demo = build_demo()


def main() -> None:
    port = int(os.environ.get("PORT", "7861"))
    # share=True only for local ad-hoc public tunnels; cloud hosts set PORT.
    share = os.environ.get("GRADIO_SHARE", "").lower() in {"1", "true", "yes"}
    demo.launch(server_name="0.0.0.0", server_port=port, share=share)


if __name__ == "__main__":
    main()
