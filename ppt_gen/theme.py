"""Visual constants shared by the deck builder."""
from pathlib import Path

from pptx.dml.color import RGBColor
from pptx.util import Inches

ROOT = Path(__file__).resolve().parents[1]
ASSETS = Path(__file__).resolve().parent / "assets"
IMAGES = ROOT / "image"

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)

# palette
NAVY = RGBColor(0x14, 0x2A, 0x3E)
INK = RGBColor(0x22, 0x30, 0x3C)
MUTED = RGBColor(0x5B, 0x70, 0x83)
SKY = RGBColor(0x2F, 0x80, 0xB9)
SKY_LIGHT = RGBColor(0xA9, 0xD3, 0xEE)
GREEN = RGBColor(0x2E, 0x8B, 0x57)
CARD_BG = RGBColor(0xF2, 0xF6, 0xF9)
CARD_SKY = RGBColor(0xE3, 0xEF, 0xF8)
CARD_GREEN = RGBColor(0xE6, 0xF3, 0xEB)
LINE = RGBColor(0xD5, 0xDF, 0xE7)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

LATIN_FONT = "Helvetica Neue"
EA_FONT = "PingFang TC"
MONO_FONT = "Menlo"

# hex twins for matplotlib
HEX_NAVY = "#142A3E"
HEX_SKY = "#2F80B9"
HEX_SLATE = "#8CA3B5"
HEX_GREEN = "#2E8B57"
