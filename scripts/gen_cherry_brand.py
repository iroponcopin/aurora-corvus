#!/usr/bin/env python3
"""Cherry — the brand mark and palette. GENERATED; do not hand-edit the output.

Owner directive (2026-09-10, IROHA, verbatim):

    次世代のModsを作りに着手を始めます。
    Modsのブランド名称はCherryです。桜という意味が込められます。
    ブランドロゴも桜の花を採用すると共にCorvusの様にWebサイトを開くと
    桜の花びらが回転しながら咲くアニメーションが加えられ、Modsの紹介が
    行われます。

Cherry is the tier ABOVE Alpha: it installs alongside Alpha, versions
independently, and is served through the Corvus launcher exactly as Alpha and
Aureum are.

--------------------------------------------------------------------------
The mark — a real five-petal sakura, constructed, not traced
--------------------------------------------------------------------------
A cherry blossom is not a generic five-pointed flower. Three things make it
read as *sakura* rather than plum or peach, and all three are in the geometry
below:

  1. the notch.  Every petal tip is CLEFT. Plum petals are round; cherry
     petals are split. This is the single feature people identify the flower
     by, so it is the one thing the mark must not smooth away.
  2. the waist.  Petals narrow to a stalk near the centre rather than meeting
     it edge to edge, leaving five slivers of background between them.
  3. the stamens.  A ring of fine filaments with heavier anthers, shorter than
     the petals, slightly irregular in length.

Each petal is one cubic Bezier outline, mirrored about its own axis, so the
five are identical under a 72-degree rotation and the mark is exactly
symmetric by construction — not by nudging control points until it looks even.

--------------------------------------------------------------------------
Palette — stated, and contrast-checked
--------------------------------------------------------------------------
Aureum's palette was SAMPLED from a reference image the owner supplied. No
reference image was supplied for Cherry, so these are CHOSEN, and this file
says so plainly rather than implying a measurement that did not happen. What
IS measured is the contrast: every pair below is computed with the WCAG
relative-luminance formula against the page background, and the numbers are
printed when this script runs.

    python3 scripts/gen_cherry_brand.py            # write the assets
    python3 scripts/gen_cherry_brand.py --check    # byte-compare with disk
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / "assets" / "img" / "cherry"
CSS = ROOT / "assets" / "css"

# --- palette (chosen, then contrast-checked) --------------------------------
# Sakura is not "pink"; it is a very pale pink that reads almost white in
# daylight and warms towards the centre. A saturated pink would read as plastic
# — the exact failure the owner named for the Alpha gun sounds ("toy").
PALETTE = {
    "--ch-bg": "#0b0709",          # near-black with a red bias, not blue
    "--ch-bg-lift": "#150e12",     # panels
    "--ch-petal": "#f7dbe4",       # the petal body
    "--ch-petal-deep": "#e8b4c6",  # the petal's shaded edge and the waist
    "--ch-blush": "#c9748f",       # the flush at the petal's throat
    "--ch-stamen": "#f6e6b8",      # filaments
    "--ch-anther": "#d9a441",      # anther tips
    "--ch-text": "#f2e8ec",        # body copy
    "--ch-text-muted": "#c2a9b4",
    "--ch-line": "#2a1c23",
}


def _luminance(hex_colour):
    r, g, b = (int(hex_colour[i:i + 2], 16) / 255.0 for i in (1, 3, 5))

    def lin(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def contrast(fg, bg):
    a, b = _luminance(fg), _luminance(bg)
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


# --- the petal --------------------------------------------------------------
# Built in a local frame: the petal grows along +Y from the origin, is mirrored
# about X, and is then rotated into place. Units are arbitrary and scaled at
# the end, so the numbers below are ratios of the flower's radius.
# ★ 最初に描いた版は belly=0.470 / notch=0.150 で、実際に描き出して見たところ
#   <b>5 枚が重なって塊になり</b>、切れ込みは小さな V にしか見えなかった。
#   72 度おきに並ぶので、半幅が 0.36 を超えると隣と食い合う。桜が桜に見えるのは
#   <b>花弁のあいだに背景が見えること</b>と<b>先の切れ込みが深いこと</b>による。
#   2 度目に描き出したときは切れ込みは出たが、<b>肩がまだ交差して</b>
#   角ばった継ぎ目が出ていたので、0.335 -> 0.300 まで絞った。
#   ここは 3 回描き出して<b>実際に見て</b>決めている。
PETAL = dict(
    waist=0.105,      # half-width where the petal leaves the centre
    belly=0.300,      # half-width at its widest
    belly_at=0.620,   # how far up the widest point sits (0..1 of the length)
    tip=0.240,        # half-width just below the cleft
    notch=0.230,      # how deep the cleft cuts back into the tip
)


def _petal_path(length, cx=0.0, cy=0.0):
    """One petal as an SVG path.

    Authored growing along +Y (up), then written out in SVG's own Y-down
    coordinates around ({@code cx}, {@code cy}).
    """
    p = PETAL
    waist = p["waist"] * length
    belly = p["belly"] * length
    tip = p["tip"] * length
    belly_y = p["belly_at"] * length
    notch = p["notch"] * length
    top = length
    cleft = top - notch

    def fx(v):
        return ("%.3f" % (cx + v)).rstrip("0").rstrip(".")

    def fy(v):
        return ("%.3f" % (cy - v)).rstrip("0").rstrip(".")

    # right-hand outline, up from the waist to the cleft
    d = [
        "M %s %s" % (fx(-waist), fy(0.0)),
        # left side, mirrored control points of the right side
        "C %s %s %s %s %s %s" % (fx(-waist * 1.05), fy(belly_y * 0.30),
                                 fx(-belly), fy(belly_y * 0.72),
                                 fx(-belly), fy(belly_y)),
        "C %s %s %s %s %s %s" % (fx(-belly), fy(belly_y + (cleft - belly_y) * 0.55),
                                 fx(-tip * 1.25), fy(cleft - notch * 0.15),
                                 fx(-tip), fy(cleft)),
        # the cleft: in to the notch floor and back out
        # 切れ込み。角を丸めた V ではなく、<b>2 つの丸い裂片</b>に見えるよう
        # 曲線で登って、谷は深く落とす。
        "C %s %s %s %s %s %s" % (fx(-tip * 0.98), fy(cleft + notch * 0.62),
                                 fx(-tip * 0.62), fy(top), fx(-tip * 0.30), fy(top)),
        "C %s %s %s %s %s %s" % (fx(-tip * 0.13), fy(top - notch * 0.16),
                                 fx(-tip * 0.06), fy(cleft + notch * 0.12),
                                 fx(0.0), fy(cleft + notch * 0.06)),
        "C %s %s %s %s %s %s" % (fx(tip * 0.06), fy(cleft + notch * 0.12),
                                 fx(tip * 0.13), fy(top - notch * 0.16),
                                 fx(tip * 0.30), fy(top)),
        "C %s %s %s %s %s %s" % (fx(tip * 0.62), fy(top),
                                 fx(tip * 0.98), fy(cleft + notch * 0.62),
                                 fx(tip), fy(cleft)),
        "L %s %s" % (fx(tip), fy(cleft)),
        "C %s %s %s %s %s %s" % (fx(tip * 1.25), fy(cleft - notch * 0.15),
                                 fx(belly), fy(belly_y + (cleft - belly_y) * 0.55),
                                 fx(belly), fy(belly_y)),
        "C %s %s %s %s %s %s" % (fx(belly), fy(belly_y * 0.72),
                                 fx(waist * 1.05), fy(belly_y * 0.30),
                                 fx(waist), fy(0.0)),
        "Z",
    ]
    return " ".join(d)


def _stamens(count, inner, outer, seed=20260910):
    """A ring of filaments with anthers. Lengths vary; the pattern is fixed."""
    out = []
    rnd = seed
    for i in range(count):
        rnd = (1103515245 * rnd + 12345) & 0x7FFFFFFF
        jitter = (rnd / 0x7FFFFFFF) * 0.22 - 0.11
        ang = 2.0 * math.pi * i / count + jitter * 0.35
        length = outer * (0.82 + 0.18 * ((rnd >> 7) % 100) / 100.0)
        x0, y0 = inner * math.cos(ang), inner * math.sin(ang)
        x1, y1 = length * math.cos(ang), length * math.sin(ang)
        out.append((x0, y0, x1, y1))
    return out


def build_svg(size=512):
    """The mark, in ABSOLUTE viewBox coordinates.

    ★ 最初の版は花全体を {@code <g transform="translate(r r)">} で包み、花弁は
      その中で {@code rotate(i*72)} していた。ところがページ側の CSS が
      同じ花弁に {@code transform} のアニメーションを掛けるので、
      <b>CSS の変換が属性の変換を丸ごと置き換え</b>、包みの translate だけが
      残って花弁が散らばった(実際にブラウザで開いて確認)。

      いまは<b>中心を座標に焼き込んで</b>包みを無くし、回転は
      {@code rotate(角度 cx cy)} で明示する。CSS 側も
      {@code transform-box:view-box; transform-origin:50% 50%} で同じ点を回すので、
      静止状態(CSS の無い favicon など)と動く状態が一致する。
    """
    r = size * 0.5
    length = r * 0.88
    petal = _petal_path(length, cx=r, cy=r)
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" '
        'width="%d" height="%d" role="img" aria-label="Cherry">' % (size, size, size, size),
        "<defs>",
        '<radialGradient id="chPetal" cx="50%" cy="78%" r="78%">',
        '<stop offset="0" stop-color="%s"/>' % PALETTE["--ch-blush"],
        '<stop offset="0.42" stop-color="%s"/>' % PALETTE["--ch-petal-deep"],
        '<stop offset="1" stop-color="%s"/>' % PALETTE["--ch-petal"],
        "</radialGradient>",
        "</defs>",
        '<g class="ch-petals">',
    ]
    for i in range(5):
        parts.append(
            '<path class="ch-petal" style="--i:%d" transform="rotate(%.3f %.3f %.3f)" d="%s" '
            'fill="url(#chPetal)" stroke="%s" stroke-width="%.2f" stroke-linejoin="round"/>'
            % (i, i * 72.0, r, r, petal, PALETTE["--ch-petal-deep"], size * 0.0045))
    parts.append("</g>")
    parts.append('<g class="ch-stamens" stroke="%s" stroke-width="%.2f" stroke-linecap="round">'
                 % (PALETTE["--ch-stamen"], size * 0.0055))
    for x0, y0, x1, y1 in _stamens(24, r * 0.050, r * 0.40):
        parts.append('<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f"/>'
                     % (r + x0, r - y0, r + x1, r - y1))
    parts.append("</g>")
    parts.append('<g class="ch-anthers" fill="%s">' % PALETTE["--ch-anther"])
    for _x0, _y0, x1, y1 in _stamens(24, r * 0.050, r * 0.40):
        parts.append('<circle cx="%.2f" cy="%.2f" r="%.2f"/>' % (r + x1, r - y1, size * 0.011))
    parts.append("</g>")
    parts.append('<circle cx="%.2f" cy="%.2f" r="%.2f" fill="%s"/>'
                 % (r, r, r * 0.048, PALETTE["--ch-blush"]))
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def build_tokens_css():
    lines = ["/* GENERATED by scripts/gen_cherry_brand.py - DO NOT EDIT BY HAND. */",
             "/* Cherry brand tokens. Contrast against --ch-bg is printed by that script. */",
             ":root {"]
    for k, v in PALETTE.items():
        lines.append("  %s: %s;" % (k, v))
    lines.append("}")
    return "\n".join(lines) + "\n"


def artefacts():
    return {
        IMG / "blossom.svg": build_svg(512),
        IMG / "blossom-mark.svg": build_svg(128),
        CSS / "cherry-tokens.css": build_tokens_css(),
    }


def main():
    check = "--check" in sys.argv[1:]
    bg = PALETTE["--ch-bg"]
    print("Cherry palette — contrast against %s (WCAG relative luminance)" % bg)
    worst = None
    for key in ("--ch-text", "--ch-text-muted", "--ch-petal", "--ch-petal-deep",
                "--ch-blush", "--ch-stamen", "--ch-anther"):
        c = contrast(PALETTE[key], bg)
        flag = "AAA" if c >= 7.0 else ("AA" if c >= 4.5 else "**below AA**")
        print("  %-18s %s  %5.2f:1  %s" % (key, PALETTE[key], c, flag))
        if key in ("--ch-text", "--ch-text-muted"):
            worst = c if worst is None else min(worst, c)
    if worst is None or worst < 4.5:
        print("FAIL body text does not clear WCAG AA against the background")
        return 1
    print("  body text worst case: %.2f:1 (AA needs 4.5)" % worst)

    problems = []
    for path, text in artefacts().items():
        rel = path.relative_to(ROOT)
        if check:
            if not path.exists() or path.read_text(encoding="utf-8") != text:
                problems.append("out of date (regenerate): %s" % rel)
            else:
                print("  OK   %s" % rel)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
            print("  wrote %s" % rel)
    if problems:
        print("\nFAIL")
        for p in problems:
            print("  - " + p)
        return 1
    print("\nCHERRY BRAND RESULT = PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
