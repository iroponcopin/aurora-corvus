#!/usr/bin/env python3
"""Flag emoji + inline-SVG fallback flags for the language switcher.

WHY THIS FILE EXISTS
--------------------
The switcher shows one flag per language. The flag is written as a *regional
indicator pair* emoji (🇬🇧 = U+1F1EC U+1F1E7) because that is the correct,
accessible, zero-asset way to do it — on macOS, iOS, Android and most Linux
desktops the pair composes into a single flag glyph.

Windows does not. Segoe UI Emoji ships **no** flag glyphs at all, so Chrome and
Edge on Windows render 🇬🇧 as two letter-boxes reading "GB", 🇯🇵 as "JP", and so
on. That is a large fraction of this site's visitors seeing a broken control.
(Firefox on Windows bundles its own Twemoji-derived font and *does* render
flags — so this is a per-browser, not per-OS, capability.)

So: emoji is primary, and `assets/js`-free CSS swaps in these SVGs when a
runtime capability check says the platform cannot compose the pair. The check
and the swap live in the page shell (site_common.py `_lang_detect_script`) and
in the generated assets/css/lang-flags.css (scripts/build_lang_flags.py).

DRAWING RULES
-------------
* Every flag is drawn into the SAME 60x40 (3:2) box. Real flags disagree about
  aspect ratio (the Union Flag is 1:2, Japan's is 2:3), but a switcher menu
  whose rows are different widths looks broken, and every serious flag icon set
  normalises for exactly this reason. Each flag's geometry is CONSTRUCTED for
  the 3:2 box — nothing here is a squashed 1:2 drawing.
* Detail that cannot survive ~20px is dropped: Spain's coat of arms, Brazil's
  27 stars and its motto, Saudi Arabia's calligraphy (reduced to the white mass
  it reads as at this size). Identifying geometry is never dropped: China keeps
  all five stars in their real positions, Korea keeps all four trigrams, the
  Union Flag keeps the counterchanged saltire.
* Star polygons and the taegeuk are COMPUTED, not typed, so they are correct by
  construction rather than by transcription luck.
"""
from __future__ import annotations

import math

# --- the emoji, which is what actually ships to most visitors ---------------
#
# en -> 🇬🇧 (GB), NOT 🇺🇸: owner directive. British English is this site's
# standard, so the switcher shows the British flag.
#
# ar -> 🇸🇦 (SA). JUDGEMENT CALL, and the one someone will question: Arabic is
# the official language of 20+ states and no flag means "Arabic". Saudi Arabia
# is the convention used by essentially every language picker that shows a flag
# for Modern Standard Arabic. Worth knowing before re-litigating it: Unicode
# CLDR's likelySubtags actually resolves bare "ar" to *Egypt* (ar-Arab-EG), so
# this is a UI convention, not a data-derived answer. The alternatives were all
# worse here — the Arab League flag has no emoji at all, and 🇪🇬 would read to
# most visitors as "Egyptian Arabic" (a specific dialect) rather than fusha.
#
# zh -> 🇨🇳 (CN) because the bundle is 简体中文 (Simplified); see the zh-TW note
# in site_common.py's matcher for how Traditional-preferring devices are
# handled.
# pt-br -> 🇧🇷 (BR): the bundle is explicitly Português (Brasil).
FLAG_EMOJI = {
    "ja": "\U0001F1EF\U0001F1F5",     # JP
    "en": "\U0001F1EC\U0001F1E7",     # GB
    "es": "\U0001F1EA\U0001F1F8",     # ES
    "fr": "\U0001F1EB\U0001F1F7",     # FR
    "zh": "\U0001F1E8\U0001F1F3",     # CN
    "ko": "\U0001F1F0\U0001F1F7",     # KR
    "pt-br": "\U0001F1E7\U0001F1F7",  # BR
    "it": "\U0001F1EE\U0001F1F9",     # IT
    "ar": "\U0001F1F8\U0001F1E6",     # SA
    "ru": "\U0001F1F7\U0001F1FA",     # RU
    "id": "\U0001F1EE\U0001F1E9",     # ID
    "de": "\U0001F1E9\U0001F1EA",     # DE
    "tr": "\U0001F1F9\U0001F1F7",     # TR
}

W, H = 60.0, 40.0


def _n(v: float) -> str:
    """Shortest exact-enough number: 20.0 -> '20', 22.5 -> '22.5'."""
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    return s if s not in ("", "-0") else "0"


def _pts(pairs) -> str:
    return "M" + "L".join(f"{_n(x)},{_n(y)}" for x, y in pairs) + "Z"


def _star(cx: float, cy: float, r: float, rot_deg: float) -> str:
    """A five-pointed star as a path. `rot_deg` is the direction (SVG angle,
    y-down, 0 = right, -90 = up) of the FIRST outer point.

    Inner radius is the geometric one for a regular {5/2} star polygon,
    r * sin(18)/sin(54) = 0.38197 r — the value that makes the points meet at
    the correct 36 degrees. Typed approximations here are why hand-written
    flag SVGs end up with fat, wrong-looking stars.
    """
    ri = r * math.sin(math.radians(18)) / math.sin(math.radians(54))
    pts = []
    for k in range(5):
        ao = math.radians(rot_deg + 72 * k)
        ai = math.radians(rot_deg + 36 + 72 * k)
        pts.append((cx + r * math.cos(ao), cy + r * math.sin(ao)))
        pts.append((cx + ri * math.cos(ai), cy + ri * math.sin(ai)))
    return _pts(pts)


def _taegeuk_comma(cx: float, cy: float, r: float) -> str:
    """One half of a taegeuk (yin-yang) whose dividing axis is VERTICAL, with
    the fat lobe at the BOTTOM: right half-disc, plus a half-disc of radius r/2
    bulging left at the bottom, minus one bulging right at the top. Rotate it
    into place with a transform rather than re-deriving the arcs."""
    h = r / 2.0
    return (f"M{_n(cx)},{_n(cy - r)}"
            f"A{_n(r)},{_n(r)} 0 0 1 {_n(cx)},{_n(cy + r)}"
            f"A{_n(h)},{_n(h)} 0 0 1 {_n(cx)},{_n(cy)}"
            f"A{_n(h)},{_n(h)} 0 0 0 {_n(cx)},{_n(cy - r)}Z")


def _rect(x, y, w, h, fill) -> str:
    return (f"<rect x='{_n(x)}' y='{_n(y)}' width='{_n(w)}' height='{_n(h)}' "
            f"fill='{fill}'/>")


def _trigram(broken: tuple, angle: float) -> str:
    """One trigram, rotated `angle` degrees about the flag centre and pushed
    out along that direction. `broken` says which of the three bars are split.

    Proportions for H=40: bar length 0.4H, thickness H/24, gap between bars
    H/24 (pitch H/12), split H/12 wide, trigram centre 16 from the flag centre.

    ⚠ The first cut used the often-quoted "bar length = H/2". It does not fit:
      with a taegeuk of radius H/4 in a 3:2 field, a 20-long bar set far enough
      out to clear the circle puts the outer bar's corner at y = -0.07, i.e.
      bleeding off the top edge — visible in a side-by-side against the system
      emoji, where the trigrams sit well inside the field. Bar length and the
      stand-off distance are solved together against that constraint.

    All four trigrams used on the Korean flag are symmetric under reversal
    (☰ ☲ ☵ ☷), so bar ORDER cannot be got wrong here."""
    t = H / 24.0          # 1.667  bar thickness
    pitch = H / 12.0      # 3.333  bar-to-bar spacing
    half = 0.2 * H        # 8      half the bar length
    gap = H / 24.0        # half-width of the split in a broken bar
    dist = 16.0           # centre-of-flag -> centre-of-trigram
    parts = []
    for i, ycen in enumerate((-pitch, 0.0, pitch)):
        y = ycen - t / 2.0
        if broken[i]:
            parts.append(_rect(-half, y, half - gap, t, "%23000"))
            parts.append(_rect(gap, y, half - gap, t, "%23000"))
        else:
            parts.append(_rect(-half, y, 2 * half, t, "%23000"))
    return (f"<g transform='rotate({_n(angle)} {_n(W / 2)} {_n(H / 2)}) "
            f"translate({_n(W / 2)} {_n(H / 2 - dist)})'>" + "".join(parts) + "</g>")


# Hash is percent-encoded up front: these strings go straight into a CSS
# url("data:image/svg+xml,...") where a bare '#' would start a fragment.
def _c(hexcolor: str) -> str:
    return "%23" + hexcolor.lstrip("#")


def _flag_ja() -> str:
    # White field, red disc. Official: disc diameter 3/5 of the hoist, centred.
    return (_rect(0, 0, W, H, _c("fff")) +
            f"<circle cx='30' cy='20' r='{_n(H * 0.3)}' fill='{_c('bc002d')}'/>")


def _flag_en() -> str:
    # Union Flag, constructed for 3:2 (the real flag is 1:2, so the bands are
    # re-derived from the HOIST, which is how the official spec expresses them:
    # white saltire H/5, red saltire 2H/15, white cross H/3, red cross H/5).
    # The counterchange of the red saltire is done with the standard four-
    # triangle clip; each data-URI SVG is its own document so the id is safe.
    ws, rs, wc, rc = H / 5, 2 * H / 15, H / 3, H / 5
    return (
        "<defs><clipPath id='u'><path d='M30,20h30v20zv20h-30zh-30v-20zv-20h30z'/>"
        "</clipPath></defs>"
        + _rect(0, 0, W, H, _c("012169")) +
        f"<path d='M0,0L60,40M60,0L0,40' stroke='{_c('fff')}' stroke-width='{_n(ws)}'/>"
        f"<path d='M0,0L60,40M60,0L0,40' clip-path='url(%23u)' stroke='{_c('C8102E')}'"
        f" stroke-width='{_n(rs)}'/>"
        f"<path d='M30,0v40M0,20h60' stroke='{_c('fff')}' stroke-width='{_n(wc)}'/>"
        f"<path d='M30,0v40M0,20h60' stroke='{_c('C8102E')}' stroke-width='{_n(rc)}'/>")


def _flag_es() -> str:
    # Red / yellow / red at 1:2:1. Coat of arms omitted: it is 3px wide here.
    return (_rect(0, 0, W, H, _c("AA151B")) +
            _rect(0, H / 4, W, H / 2, _c("F1BF00")))


def _flag_fr() -> str:
    return (_rect(0, 0, W / 3, H, _c("000091")) +
            _rect(W / 3, 0, W / 3, H, _c("fff")) +
            _rect(2 * W / 3, 0, W / 3, H, _c("E1000F")))


def _flag_zh() -> str:
    # Positions are the official 30x20 construction grid, doubled to 60x40:
    # big star centre (5,5) r3; small stars (10,2) (12,4) (12,7) (10,9) r1.
    # Each small star points AT the big one, which is the detail most hand-made
    # copies of this flag get wrong.
    big = (10.0, 10.0, 6.0)
    smalls = [(20.0, 4.0), (24.0, 8.0), (24.0, 14.0), (20.0, 18.0)]
    y = _c("FFDE00")
    out = [_rect(0, 0, W, H, _c("DE2910")),
           f"<path d='{_star(big[0], big[1], big[2], -90)}' fill='{y}'/>"]
    for cx, cy in smalls:
        rot = math.degrees(math.atan2(big[1] - cy, big[0] - cx))
        out.append(f"<path d='{_star(cx, cy, 2.0, rot)}' fill='{y}'/>")
    return "".join(out)


def _flag_ko() -> str:
    # Circle diameter = half the hoist. Blue disc, red comma laid over it, four
    # trigrams on the diagonals of a 3:2 field (atan(20/30) = 33.69 deg, so the
    # trigram rotations are +-56.31 / +-123.69 from vertical).
    r = H / 4
    return (_rect(0, 0, W, H, _c("fff")) +
            f"<circle cx='30' cy='20' r='{_n(r)}' fill='{_c('0047A0')}'/>"
            # -123.69 deg puts the red (yang) lobe on top with the dividing S
            # entering at the upper hoist and leaving at the lower fly, which
            # is the orientation the system flag emoji shows. Picked by
            # rendering all six plausible rotations against the emoji rather
            # than by reasoning about which diagonal the axis follows — the
            # sign is easy to talk yourself into getting backwards.
            f"<path d='{_taegeuk_comma(30, 20, r)}' fill='{_c('CD2E3A')}'"
            f" transform='rotate(-123.69 30 20)'/>"
            # ☰ Geon, upper hoist
            + _trigram((0, 0, 0), -56.31)
            # ☲ Ri, lower hoist
            + _trigram((0, 1, 0), -123.69)
            # ☵ Gam, upper fly
            + _trigram((1, 0, 1), 56.31)
            # ☷ Gon, lower fly
            + _trigram((1, 1, 1), 123.69))


def _flag_pt_br() -> str:
    # Green field, yellow rhombus inset 1.7/14 of the hoist, blue celestial
    # globe r = 3.5/14 of the hoist, white band.
    #
    # The band sits in the UPPER half of the globe, ends higher than the
    # middle. That is not decoration: exactly one of the 27 stars (Spica, for
    # Pará) is above the band and 26 are below, so a band drawn across the
    # lower half is the wrong flag. ORDEM E PROGRESSO is dropped (unreadable
    # even at 300px here), and the stars are reduced to a representative
    # scatter of dots — their real positions are a sky chart, and inventing
    # 27 of them would be pretending to a precision this drawing does not have.
    k = H / 14.0
    ins = 1.7 * k
    r = 3.5 * k
    stars = [(30, 12.4), (24.6, 21.6), (27.4, 23.4), (31.8, 22.4), (35.4, 24.6),
             (26.2, 26.4), (30.4, 27.2), (34.2, 21.2), (22.6, 24.2), (33.2, 26.8)]
    dots = "".join(f"<circle cx='{_n(x)}' cy='{_n(y)}' r='0.75' fill='{_c('fff')}'/>"
                   for x, y in stars)
    return (_rect(0, 0, W, H, _c("009B3A")) +
            f"<path d='{_pts([(W / 2, ins), (W - ins, H / 2), (W / 2, H - ins), (ins, H / 2)])}'"
            f" fill='{_c('FEDF00')}'/>"
            f"<circle cx='30' cy='20' r='{_n(r)}' fill='{_c('002776')}'/>"
            "<defs><clipPath id='g'><circle cx='30' cy='20' r='" + _n(r) + "'/></clipPath></defs>"
            + dots +
            f"<path d='M12,11.5Q30,27.5 48,11.5L48,8.5Q30,24.5 12,8.5Z' fill='{_c('fff')}'"
            " clip-path='url(%23g)'/>")


def _flag_it() -> str:
    return (_rect(0, 0, W / 3, H, _c("008C45")) +
            _rect(W / 3, 0, W / 3, H, _c("F4F5F0")) +
            _rect(2 * W / 3, 0, W / 3, H, _c("CD212A")))


def _flag_ar() -> str:
    # Saudi Arabia. The shahada is calligraphy that is literally unreadable at
    # 20px, so it is reduced to the white mass a reader actually perceives —
    # a broken band of strokes above a horizontal sword. Dropping it entirely
    # would leave a plain green rectangle, which is a DIFFERENT flag (Libya
    # 1977-2011), and that is exactly the "wrong flag is worse than a globe"
    # failure. Sword points to the hoist, hilt to the fly, as on the obverse.
    w = _c("fff")
    # The shahada's visual signature is a dense baseline with a crowd of
    # UNEVENLY spaced ascenders (the alif/lam uprights of لا and ال). An evenly
    # spaced comb reads as a rake, not as writing, so the spacings and heights
    # below are deliberately irregular and the baseline is broken.
    marks = [
        (15.0, 14.6, 9.6, 1.1), (26.0, 14.6, 6.6, 1.1), (34.0, 14.6, 11.0, 1.1),
        (15.6, 11.6, 1.0, 3.1), (17.2, 10.7, 1.0, 4.0), (18.6, 12.1, 0.9, 2.6),
        (21.2, 11.0, 1.0, 3.7), (22.6, 11.8, 0.9, 2.9), (25.8, 10.8, 1.0, 3.9),
        (28.2, 12.0, 0.9, 2.7), (30.4, 11.1, 1.0, 3.6), (31.8, 12.2, 0.9, 2.5),
        (34.8, 10.7, 1.0, 4.0), (36.4, 11.9, 0.9, 2.8), (39.0, 11.0, 1.0, 3.7),
        (40.4, 12.1, 0.9, 2.6), (42.2, 11.5, 0.9, 3.2),
        (19.6, 16.6, 2.6, 1.0), (29.4, 16.6, 3.2, 1.0), (38.4, 16.6, 2.3, 1.0),
    ]
    strokes = "".join(
        f"<rect x='{_n(x)}' y='{_n(yy)}' width='{_n(ww)}' height='{_n(hh)}'"
        f" rx='0.4' fill='{w}'/>" for x, yy, ww, hh in marks)
    # Blade tip to the hoist, hilt to the fly — the orientation the emoji and
    # the obverse of the real flag both use. Deliberately thin: on the real
    # flag the sword is a hairline next to the mass of the script, and a fat
    # sword is the single thing that makes a drawn Saudi flag look fake.
    sword = (f"<path d='M15.5,25.5L20,24.9H39.6V26.1H20Z' fill='{w}'/>"
             f"<rect x='39.4' y='23.4' width='0.9' height='4.2' rx='0.4' fill='{w}'/>"
             f"<rect x='40.3' y='25' width='3' height='1' rx='0.5' fill='{w}'/>"
             f"<circle cx='43.6' cy='25.5' r='0.9' fill='{w}'/>")
    return _rect(0, 0, W, H, _c("006C35")) + strokes + sword


def _flag_ru() -> str:
    return (_rect(0, 0, W, H / 3, _c("fff")) +
            _rect(0, H / 3, W, H / 3, _c("0039A6")) +
            _rect(0, 2 * H / 3, W, H / 3, _c("D52B1E")))


def _flag_id() -> str:
    return (_rect(0, 0, W, H / 2, _c("CE1126")) +
            _rect(0, H / 2, W, H / 2, _c("fff")))


def _flag_de() -> str:
    return (_rect(0, 0, W, H / 3, _c("000")) +
            _rect(0, H / 3, W, H / 3, _c("DD0000")) +
            _rect(0, 2 * H / 3, W, H / 3, _c("FFCE00")))


def _flag_tr() -> str:
    # TSE 11762 proportions, expressed against the hoist G=40 on a 3:2 field
    # (Turkey's real ratio, so nothing is distorted): crescent outer circle
    # d=G/2 centred G/2 from the hoist, inner circle d=2G/5 centred 0.5625G
    # from the hoist, star circumradius 0.075G centred 0.815G from the hoist
    # with one point toward the crescent. The crescent's bite is drawn as a
    # field-coloured disc, which is exact, not an approximation.
    g = H
    red = _c("E30A17")
    return (_rect(0, 0, W, H, red) +
            f"<circle cx='{_n(0.5 * g)}' cy='20' r='{_n(0.25 * g)}' fill='{_c('fff')}'/>"
            f"<circle cx='{_n(0.5625 * g)}' cy='20' r='{_n(0.2 * g)}' fill='{red}'/>"
            f"<path d='{_star(0.815 * g, 20, 0.075 * g, 180)}' fill='{_c('fff')}'/>")


_BUILDERS = {
    "ja": _flag_ja, "en": _flag_en, "es": _flag_es, "fr": _flag_fr,
    "zh": _flag_zh, "ko": _flag_ko, "pt-br": _flag_pt_br, "it": _flag_it,
    "ar": _flag_ar, "ru": _flag_ru, "id": _flag_id, "de": _flag_de,
    "tr": _flag_tr,
}


def svg_body(code: str) -> str:
    build = _BUILDERS.get(code)
    if build is None:
        raise SystemExit(
            f"ERROR: flag_svgs.py has no flag for language {code!r}. A language was "
            f"added to site_common.LANGUAGES without a flag, and the switcher would "
            f"fall back to a blank box on every Windows visitor.")
    return build()


def data_uri(code: str) -> str:
    """The flag as a CSS-safe data: URI. Only the characters that actually
    break inside url(\"...\") are escaped, which keeps these an order of
    magnitude smaller than base64 and leaves them readable in the emitted CSS.
    """
    svg = (f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {_n(W)} {_n(H)}'>"
           + svg_body(code) + "</svg>")
    # Every '#' in the markup was already written as %23 by _c()/url(%23...),
    # and no other '%' is ever produced here — asserted rather than assumed,
    # because a stray raw '#' silently truncates the URI at the CSS parser and
    # the flag just vanishes.
    if "#" in svg:
        raise SystemExit(f"ERROR: flag {code!r} contains a raw '#'; use _c()/%23. "
                         f"A raw '#' truncates the data: URI and the flag disappears.")
    bad = [seg for seg in svg.split("%")[1:] if not seg.startswith("23")]
    if bad:
        raise SystemExit(f"ERROR: flag {code!r} contains a '%' that is not part of %23.")
    # BOTH quote characters are escaped, not just one. The markup above uses
    # single quotes for attributes, so leaving them raw works in
    # url("...") and silently produces an EMPTY BOX inside url('...') or an
    # HTML style="..." attribute — which is exactly how this first went wrong.
    out = (svg.replace("<", "%3C").replace(">", "%3E")
              .replace('"', "%22").replace("'", "%27").replace(" ", "%20"))
    return "data:image/svg+xml," + out


if __name__ == "__main__":
    for c in _BUILDERS:
        print(f"{c:6s} {len(data_uri(c)):5d} bytes  {FLAG_EMOJI[c]}")
