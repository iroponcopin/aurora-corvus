#!/usr/bin/env python3
"""The OUKA share card: the cut mark on the site's own ground, and nothing else.

No wordmark. The owner's standing instruction for every one of these logos is
「ロゴにはテキストが含まれていますがこれは一切使用せずロゴだけを切り取り使用して
ください」, and the photograph's own OUKA lettering is therefore never used; the
page's <h1> is the name. Nothing is invented here — the card is the mark the
owner supplied, scaled and centred on --bg (#07090f, read from style.css).

Deterministic: LANCZOS + optimised PNG, so a second run is byte-identical.
"""
import os, hashlib
from PIL import Image

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(SITE, "assets/img/ouka/mark.png")
OUT = os.path.join(SITE, "assets/img/ouka/og-ouka.png")

W, H = 1200, 630          # what og:image:width/height already declare
GROUND = (7, 9, 15)       # --bg #07090f, style.css:40
MARK_H = 430              # 68.3% of the card's height


def main():
    mark = Image.open(SRC).convert("RGBA")
    scale = MARK_H / mark.height
    w = round(mark.width * scale)
    mark = mark.resize((w, MARK_H), Image.LANCZOS)

    card = Image.new("RGB", (W, H), GROUND)
    x, y = (W - w) // 2, (H - MARK_H) // 2
    card.paste(mark, (x, y), mark)
    card.save(OUT, "PNG", optimize=True)

    b = os.path.getsize(OUT)
    print("source   %s %s" % (os.path.basename(SRC), Image.open(SRC).size))
    print("mark on card %dx%d at (%d,%d)" % (w, MARK_H, x, y))
    print("card     %dx%d  %d B  md5 %s"
          % (W, H, b, hashlib.md5(open(OUT, "rb").read()).hexdigest()))


if __name__ == "__main__":
    main()
