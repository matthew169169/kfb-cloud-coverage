"""Build the process-update deck.

Usage: python3 -m ppt_gen.generate_update
"""
from pptx import Presentation

from ppt_gen import theme as T
from ppt_gen.update_charts import build_all
from ppt_gen.update_slides import build_slides

OUT = T.ROOT / "KFB_Process_Update.pptx"  # process update deck for the combined final model


def main() -> None:
    build_all()
    prs = Presentation()
    prs.slide_width = T.SLIDE_W
    prs.slide_height = T.SLIDE_H
    build_slides(prs)
    prs.save(OUT)
    print(f"saved {OUT} ({len(prs.slides._sldIdLst)} slides)")


if __name__ == "__main__":
    main()
