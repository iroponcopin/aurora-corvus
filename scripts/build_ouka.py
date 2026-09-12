#!/usr/bin/env python3
"""Builds ouka/index.html — the OUKA brand page, for every language.

Owner directive (2026-09-12, IROHA, verbatim):

    新ブランドOUKAを展開
    ブランド名称:英→OUKA、漢→桜花
    ブランド位置:OUKA→Cherry→Alpha(※左から順に上位ブランド)
    (Aureumは別ジャンルModsなので含まれない)
    ブランドロゴをデザインフォルダーに追加しています。ウェブサイトに表示して
    今までにない圧倒的な品質とアニメーションでその名を轟かせ披露してください。

--------------------------------------------------------------------------
What the page says — and what it must never say
--------------------------------------------------------------------------
This page is built to the shape the owner arrived at for Cherry, after he
rejected two earlier drafts of that page (see build_cherry.py's header for his
words). Two things, and nothing else:

  1. OUKA is the tier above Cherry — said once, as a fact, not argued.
  2. A closing line in the register of 乞うご期待.

NOT on this page, by his word on Cherry, which governs here because this is the
same kind of page: where the name comes from; that there is no compromise
(self-evident, and saying it cheapens the brand); what it will contain; any
status, progress, "not yet", "coming later", build, or schedule. OUKA has no
published build — and that is exactly why none of it may be written down, in
either direction. Every one of the 13 languages carries its own copy; nothing
falls back to English.

漢字の「桜花」は意図的にこのページに出していない。所有者は英・漢の両方を
ブランド名として挙げているが、片方を添えると「名前の説明」に読めてしまう
——それは Cherry のページで名指しで禁じられたことである。出すかどうかは
所有者の判断を待つ。

--------------------------------------------------------------------------
The mark
--------------------------------------------------------------------------
The mark is cut out of the logo photograph the owner supplied, and it is the
MARK ONLY — his standing instruction for every one of these logos is
「ロゴにはテキストが含まれていますがこれは一切使用せずロゴだけを切り取り
使用してください」, so the word OUKA under it in the photograph is not used;
the <h1> below the mark is the name.

It never stops moving, the same contract the owner set for Cherry's logo
(「常時動いているロゴ」), one tier more deliberate: it turns once every 90
seconds against Cherry's 60. On open it blooms once, then breathes forever,
between two haloes that breathe out of phase — the inner one the pink of the
mark's left half, the outer one the silver of its right half. Both colours are
MEASURED off the mark's own opaque pixels (479x453, 8766 samples: left mean
#fed1dd, right mean #e7dbe1), not picked by eye.

`prefers-reduced-motion: reduce` skips ONLY the one-time bloom and the wordmark
stagger. The turn, the breath and the haloes are the mark itself and stay on.

Three traps, all of which this repo has actually shipped (see build_cherry.py):
  ★ CSS `transform` REPLACES the element's other transform, so the turn and the
    bloom/breath cannot share an element — one silently erases the other.
  ★ The CSS below is NOT a format string. A mis-doubled brace once emitted
    broken CSS and a logo that never moved. Substitution is str.replace() of
    __TOKENS__, and main() refuses to write a page still holding one.
  ★ A rotating rectangle sweeps its own DIAGONAL; the mark is sized from the
    file's real pixels so it cannot swing outside its box.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from site_common import (  # noqa: E402
    ROOT, asset_root_prefix, available_langs, esc, page, write_page,
)

SECTION = "ouka/"

# --- copy -------------------------------------------------------------------
# Every language the site ships has its own entry; there is no fallback. Brand
# names (OUKA, Cherry, Alpha) are never translated. Keys: title, desc, lede, soon.
# The closing line is the one the owner accepted on the Cherry page, verbatim.
COPY = {
    "ja": {"title": "OUKA", "desc": "Cherry の上位に位置するブランド。",
           "lede": "Cherry の上位に位置するブランド。", "soon": "ご期待ください。"},
    "en": {"title": "OUKA", "desc": "The tier above Cherry.",
           "lede": "The tier above Cherry.", "soon": "Coming soon."},
    "es": {"title": "OUKA", "desc": "El nivel por encima de Cherry.",
           "lede": "El nivel por encima de Cherry.", "soon": "Muy pronto."},
    "fr": {"title": "OUKA", "desc": "Le niveau au-dessus de Cherry.",
           "lede": "Le niveau au-dessus de Cherry.", "soon": "Bientôt disponible."},
    "zh": {"title": "OUKA", "desc": "位于 Cherry 之上的品牌。",
           "lede": "位于 Cherry 之上的品牌。", "soon": "敬请期待。"},
    "ko": {"title": "OUKA", "desc": "Cherry 위에 자리한 브랜드입니다.",
           "lede": "Cherry 위에 자리한 브랜드입니다.", "soon": "기대해 주세요."},
    "pt-br": {"title": "OUKA", "desc": "O nível acima do Cherry.",
              "lede": "O nível acima do Cherry.", "soon": "Em breve."},
    "it": {"title": "OUKA", "desc": "Il livello sopra Cherry.",
           "lede": "Il livello sopra Cherry.", "soon": "In arrivo."},
    "ar": {"title": "OUKA", "desc": "المستوى الأعلى من Cherry.",
           "lede": "المستوى الأعلى من Cherry.", "soon": "ترقّبوا قريباً."},
    "ru": {"title": "OUKA", "desc": "Уровень выше Cherry.",
           "lede": "Уровень выше Cherry.", "soon": "Уже скоро."},
    "id": {"title": "OUKA", "desc": "Tingkat di atas Cherry.",
           "lede": "Tingkat di atas Cherry.", "soon": "Segera hadir."},
    "de": {"title": "OUKA", "desc": "Die Stufe über Cherry.",
           "lede": "Die Stufe über Cherry.", "soon": "Bald verfügbar."},
    "tr": {"title": "OUKA", "desc": "Cherry'nin üzerindeki seviye.",
           "lede": "Cherry'nin üzerindeki seviye.", "soon": "Çok yakında."},
}

KEYS = ("title", "desc", "lede", "soon")

# --- the mark ---------------------------------------------------------------
# Real files on disk, measured with PIL, not guessed.
MARK = {"file": "mark-584.webp", "w": 584, "h": 552,
        "small": "mark-320.webp", "small_w": 320}
BOX = "min(26rem,74vw)"          # the square the mark turns inside

# A rotating rectangle needs its own diagonal to fit inside that square.
FIT_PCT = round(100.0 * MARK["w"] / math.hypot(MARK["w"], MARK["h"]), 1)

# Measured off the mark's own opaque pixels (alpha >= 235), sampled every 2px:
# the left half of the blossom is pink, the right half silver. These two drive
# the haloes and the wordmark's gradient, so the page is coloured by its own
# logo rather than by a palette someone invented next to it.
PINK = "254,209,221"             # #fed1dd, mean of the left half
SILVER = "231,219,225"           # #e7dbe1, mean of the right half

# --- timing -----------------------------------------------------------------
SPIN_S = 90              # one revolution. Cherry turns in 60; the tier above
                         # it moves more deliberately, and still visibly (4°/s).
BLOOM_MS = 1400
BLOOM_START_MS = 160
BREATHE_MS = 6000
HALO_IN_MS = 7000
HALO_OUT_MS = 9000       # out of phase with the inner halo, on purpose
GLYPH_MS = 700
GLYPH_STEP_MS = 90

HEAD = """<style>
.ou-wrap{padding:4.5rem 0 2rem;display:grid;justify-items:center;text-align:center}
.ou-mark{position:relative;width:__BOX__;aspect-ratio:1;
  display:grid;place-items:center;margin-bottom:1.6rem}
.ou-halo,.ou-halo--out{position:absolute;border-radius:50%;pointer-events:none}
.ou-halo{inset:-2%;
  background:radial-gradient(circle,rgba(__PINK__,.26),rgba(__PINK__,0) 68%);
  animation:ou-halo __HALO_IN_MS__ms ease-in-out infinite}
.ou-halo--out{inset:-14%;
  background:radial-gradient(circle,rgba(__SILVER__,.16),rgba(__SILVER__,0) 72%);
  animation:ou-halo-out __HALO_OUT_MS__ms ease-in-out infinite}
/* the turn lives alone on this wrapper: a CSS transform REPLACES the other */
.ou-spin{display:block;width:__FIT__%;position:relative;
  animation:ou-spin __SPIN_S__s linear infinite}
.ou-breathe{display:block;
  animation:ou-open __BLOOM_MS__ms cubic-bezier(.16,.84,.28,1) __BLOOM_DELAY__ms backwards,
            ou-breathe __BREATHE_MS__ms ease-in-out __BREATHE_DELAY__ms infinite}
.ou-img{display:block;width:100%;height:auto}

.ou-name{font-size:clamp(2.8rem,8vw,5rem);line-height:1;margin:0 0 1rem;
  letter-spacing:.06em;font-weight:700;
  background:linear-gradient(100deg,rgb(__PINK__) 12%,#ffffff 48%,rgb(__SILVER__) 88%);
  -webkit-background-clip:text;background-clip:text;color:transparent}
.ou-g{display:inline-block;animation:ou-glyph __GLYPH_MS__ms
  cubic-bezier(.16,.84,.28,1) backwards;animation-delay:calc(var(--i) * __GLYPH_STEP_MS__ms + __BLOOM_DELAY__ms)}
.ou-lede{font-size:1.14rem;line-height:1.78;color:var(--text);margin:0;max-width:34rem}
.ou-soon{margin:4.5rem 0 0;font-size:1.25rem;letter-spacing:.08em;color:var(--text-muted)}

@keyframes ou-spin{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}
@keyframes ou-open{from{transform:rotate(-90deg) scale(.04);opacity:0}
  55%{opacity:1}
  to{transform:rotate(0deg) scale(1);opacity:1}}
@keyframes ou-breathe{0%,100%{transform:scale(1)}50%{transform:scale(.982)}}
@keyframes ou-halo{0%,100%{opacity:.5;transform:scale(1)}
  50%{opacity:1;transform:scale(1.05)}}
@keyframes ou-halo-out{0%,100%{opacity:.9;transform:scale(1.04)}
  50%{opacity:.45;transform:scale(1)}}
@keyframes ou-glyph{from{opacity:0;transform:translateY(18px)}
  to{opacity:1;transform:none}}

/* Reduced motion skips ONLY what happens once -- the bloom and the wordmark's
   stagger. The turn, the breath and the haloes are the mark itself. */
@media (prefers-reduced-motion:reduce){
  .ou-breathe{animation:ou-breathe __BREATHE_MS__ms ease-in-out infinite}
  .ou-g{animation:none}
}
</style>"""

TOKENS = ("__BOX__", "__FIT__", "__PINK__", "__SILVER__", "__SPIN_S__",
          "__BLOOM_MS__", "__BLOOM_DELAY__", "__BREATHE_MS__", "__BREATHE_DELAY__",
          "__HALO_IN_MS__", "__HALO_OUT_MS__", "__GLYPH_MS__", "__GLYPH_STEP_MS__")


def head_css() -> str:
    out = HEAD
    for token, value in (
        ("__BOX__", BOX),
        ("__FIT__", "%g" % FIT_PCT),
        ("__PINK__", PINK),
        ("__SILVER__", SILVER),
        ("__SPIN_S__", str(SPIN_S)),
        ("__BLOOM_MS__", str(BLOOM_MS)),
        ("__BLOOM_DELAY__", str(BLOOM_START_MS)),
        ("__BREATHE_MS__", str(BREATHE_MS)),
        ("__BREATHE_DELAY__", str(BLOOM_START_MS + BLOOM_MS)),
        ("__HALO_IN_MS__", str(HALO_IN_MS)),
        ("__HALO_OUT_MS__", str(HALO_OUT_MS)),
        ("__GLYPH_MS__", str(GLYPH_MS)),
        ("__GLYPH_STEP_MS__", str(GLYPH_STEP_MS)),
    ):
        out = out.replace(token, value)
    return out


def wordmark(text: str) -> str:
    """One span per glyph so the reveal can stagger. Emitted at BUILD time, the
    same discipline as build_aureum.py's: the split is in the served HTML, so
    nothing depends on a script running for the name to be readable."""
    return "".join('<span class="ou-g" style="--i:%d">%s</span>' % (i, esc(ch))
                   for i, ch in enumerate(text))


def _mark_html(root: str) -> str:
    """The cut-out mark. alt="" on purpose: the <h1> directly below already
    says OUKA, and an alt that repeated it would say the name twice."""
    base = root + "assets/img/ouka/"
    return (
        '<div class="ou-mark">'
        '<span class="ou-halo--out" aria-hidden="true"></span>'
        '<span class="ou-halo" aria-hidden="true"></span>'
        '<span class="ou-spin"><span class="ou-breathe">'
        '<img class="ou-img" src="%s%s" srcset="%s%s %dw, %s%s %dw" '
        'sizes="calc(%s * %g / 100)" width="%d" height="%d" alt="" '
        'decoding="async" fetchpriority="high" loading="eager">'
        '</span></span></div>'
        % (base, MARK["file"], base, MARK["small"], MARK["small_w"],
           base, MARK["file"], MARK["w"], BOX, FIT_PCT, MARK["w"], MARK["h"])
    )


def build_body(c: dict, root: str) -> str:
    return (
        '<div class="ou-wrap">'
        '%s'
        '<h1 class="ou-name" aria-label="%s">%s</h1>'
        '<p class="ou-lede">%s</p>'
        '<p class="ou-soon">%s</p>'
        '</div>'
        % (_mark_html(root), esc(c["title"]), wordmark(c["title"]),
           esc(c["lede"]), esc(c["soon"]))
    )


def main() -> int:
    langs = available_langs()
    missing = [lang for lang in langs if lang not in COPY]
    if missing:
        print("build_ouka: no copy for %s (no fallback by design)" % ", ".join(missing))
        return 1
    for lang, c in COPY.items():
        gaps = [k for k in KEYS if not c.get(k)]
        if gaps:
            print("build_ouka: %s is missing %s" % (lang, ", ".join(gaps)))
            return 1
    css = head_css()
    for lang in langs:
        c = COPY[lang]
        # NOT "../" for every language: /de/ouka/ is two levels below the site
        # root but one below its language root.
        root = asset_root_prefix(1, lang)
        html = page(
            lang=lang,
            section=SECTION,
            title=c["title"],
            description=c["desc"],
            active="ouka",
            body=build_body(c, root),
            depth=1,
            extra_head=css,
        )
        # Everything below has a failure mode that looks fine: a surviving
        # token discards the rule and the mark sits still; a missing <img>
        # still renders a clean text hero; a wrong prefix 404s only in a
        # browser. None of them turns anything red on its own.
        left = [tok for tok in TOKENS if tok in html]
        if left or "{{" in html:
            raise SystemExit(
                "ERROR: build_ouka: %s still holds %s -- the CSS would be "
                "discarded and the mark would not move." % (lang, left or ["{{"]))
        for needed in ("ou-img", "@keyframes ou-spin", "@keyframes ou-open",
                       "@keyframes ou-breathe", "prefers-reduced-motion"):
            if needed not in html:
                raise SystemExit("ERROR: build_ouka: %s is missing %r." % (lang, needed))
        want = root + "assets/img/ouka/" + MARK["file"]
        target = ROOT / ("" if lang == "ja" else lang) / SECTION / "index.html"
        probe = (target.parent / want).resolve()
        if not probe.is_file():
            raise SystemExit(
                "ERROR: build_ouka: %s references %s, which resolves to %s -- no "
                "such file. The mark would 404." % (lang, want, probe))
        write_page(lang, SECTION, html)
    print("build_ouka: %d language(s), mark %s at %g%% of %s, one turn per %ds"
          % (len(langs), MARK["file"], FIT_PCT, BOX, SPIN_S))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
