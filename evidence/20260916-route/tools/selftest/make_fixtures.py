#!/usr/bin/env python3
"""Deterministic selftest fixtures for detect_menu_popup.py (synthetic only)."""
from PIL import Image, ImageDraw
import os

OUT = os.path.dirname(os.path.abspath(__file__))
W, H = 400, 700

def base():
    im = Image.new("L", (W, H), 30)
    d = ImageDraw.Draw(im)
    d.rectangle([10, 400, 390, 470], fill=46)           # album row card
    d.text((16, 430), "2024/05/13~05/17", fill=200)      # title
    d.text((16, 452), "57", fill=200)                    # count
    for i, y in enumerate((438, 444, 450)):              # vertical ellipsis
        d.rectangle([303, y, 305, y + 1], fill=200)
    return im

b = base(); b.save(os.path.join(OUT, "fixture-base.png"))
menu = base(); d = ImageDraw.Draw(menu)
d.rectangle([240, 300, 372, 372], fill=210, outline=120)   # new popup rectangle
d.text((250, 310), "Save All", fill=20)
d.text((250, 330), "Open Album", fill=20)
d.text((250, 350), "Settings", fill=20)
menu.save(os.path.join(OUT, "fixture-post-menu.png"))
hover = base(); d = ImageDraw.Draw(hover)
d.ellipse([296, 432, 312, 456], fill=60)                   # hover halo only
hover.save(os.path.join(OUT, "fixture-post-hover.png"))
print("fixtures written to", OUT)
