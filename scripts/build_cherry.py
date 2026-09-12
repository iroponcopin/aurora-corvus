#!/usr/bin/env python3
"""Builds cherry/index.html — the Cherry brand page, for every language.

Owner directive (2026-09-10, IROHA, verbatim):

    次世代のModsを作りに着手を始めます。
    Modsのブランド名称はCherryです。
    ブランドロゴも桜の花を採用すると共にCorvusの様にWebサイトを開くと
    桜の花びらが回転しながら咲くアニメーションが加えられ、Modsの紹介が
    行われます。
    Alphaの上位ブランドという位置付けになるでしょう。
    Alpha Modsと併用して導入することができますが、バージョンは異なります。
    そしてCorvusランチャーにも対応し、自動でアップデート初回はダウンロード
    ボタンが表示されます。

Second directive (2026-09-10, IROHA, verbatim), after the first page was
rejected — this one governs what the page says and how the mark behaves:

    Cherry は Alpha の上位に置くブランドです。Alpha と併せて導入でき、
    バージョンは別に進みます。
    ブランドの強さを説明するだけで良いです。名前の由来など説明しません。
    Appleも同じようにAppleという名前に言及しないのと同じです。
    妥協しないのは当たり前のことわりなのでわざわざ記載しないでください。
    ブランドイメージが軽くなります。
    ランチャー対応とAlphaと併用できること、そして今の状況という記載の仕方
    ではなく、乞うご期待などに変更してください。
    Cherryロゴが一歳動いていません。これは常時動いているロゴです。
    着手したところです。まだ配布できるビルドはありません。こう言った余計な
    文言は排除してください。書くならプレミア感がある文章を添えるだけです。

--------------------------------------------------------------------------
What the page says — and what it must never say
--------------------------------------------------------------------------
Two things, and nothing else:

  1. Where Cherry sits — said once, as a fact, not argued. Until 2026-09-12
     that was "the tier above Alpha"; OUKA now stands above it, so the line
     reads "the tier between OUKA and Alpha" in all 13 languages. The fact
     did not change — Cherry is still above Alpha — but the old wording left
     a reader believing Cherry was the top of the line, and it no longer is.
  2. A closing line in the register of 乞うご期待.

NOT on this page, by the owner's word: where the name comes from; that there
is no compromise (self-evident, and saying it cheapens the brand); that it
works with the Corvus launcher; that it installs alongside Alpha or versions
on its own (「ランチャー対応とAlphaと併用できること、そして今の状況という
記載の仕方ではなく、乞うご期待などに変更してください」 — a rewrite on
2026-09-10 read this backwards and kept both as "capability" cards; they are
gone); any status, progress, "not yet", "coming later", build, or schedule.
Every one of the 13 languages carries its own copy; nothing falls back to English.

--------------------------------------------------------------------------
The mark — the owner's own logo, and it never stops moving
--------------------------------------------------------------------------
2026-09-12: the owner supplied a real Cherry logo, so this page no longer
inlines the generated blossom SVG. It carries the mark cut out of that
photograph (assets/img/cherry/mark*.webp) — the MARK only: 「ロゴにはテキストが
含まれていますがこれは一切使用せずロゴだけを切り取り使用してください」, so the
word CHERRY under it in the photograph is not on this page.

A photograph cannot be taken apart into five petals the way the generated SVG
could, so what was per-petal is now carried by the whole mark, and the
behaviour the owner asked for is unchanged:

  1. it TURNS, from the first frame and forever — one revolution a minute
     (「Cherryロゴが一歳動いていません。これは常時動いているロゴです。」)
  2. it blooms once on open: folded to nothing and rotated back 90 degrees,
     unfolding as it turns into place
  3. it breathes forever (scale 1 -> 0.985 -> 1 over ~5 s)
  4. a soft halo behind it breathes out of phase, in the petal's own colour

All CSS keyframes with `infinite` iteration; no JavaScript, no SMIL, no library.

`prefers-reduced-motion: reduce` skips ONLY the one-time bloom (the mark starts
open). The turn, the breath and the halo are the identity of the mark —
「常時動いているロゴ」 — and stay on regardless.

Three traps this file has actually shipped:
  ★ CSS `transform` REPLACES the element's other transform, so the turn and
    the bloom/breath CANNOT live on the same element — one silently erases the
    other. The turn is on .ch-spin, the bloom/breath on .ch-breathe inside it.
  ★ The CSS below is NOT run through str.format(). An earlier version was, and
    a mis-doubled brace emitted `{{transform-box:...}}` — broken CSS, the whole
    petal rule discarded, and what the owner saw was a logo that never moved.
    Substitution here is str.replace() of __TOKENS__ that cannot collide with
    a brace, and main() refuses to write a page that still holds one.
  ★ A rotating rectangle sweeps its own DIAGONAL. The mark is only as wide as
    it can be and still stay inside its box at every angle — computed below
    from the file's real pixel size, not eyeballed.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from site_common import (  # noqa: E402
    ROOT, asset_root_prefix, available_langs, esc, page, write_page,
)

SECTION = "cherry/"

# --- copy -------------------------------------------------------------------
# Every language the site ships has its own entry; there is no fallback. Brand
# names (Cherry, Alpha, Corvus) are never translated. Keys, in every language:
#   title, desc, lede, soon.
COPY = {
    "ja": {
        "title": "Cherry",
        "desc": "OUKA と Alpha のあいだに位置するブランド。",
        "lede": "OUKA と Alpha のあいだに位置するブランド。",
        "soon": "ご期待ください。",
    },
    "en": {
        "title": "Cherry",
        "desc": "The tier between OUKA and Alpha.",
        "lede": "The tier between OUKA and Alpha.",
        "soon": "Coming soon.",
    },
    "es": {
        "title": "Cherry",
        "desc": "El nivel entre OUKA y Alpha.",
        "lede": "El nivel entre OUKA y Alpha.",
        "soon": "Muy pronto.",
    },
    "fr": {
        "title": "Cherry",
        "desc": "Le niveau entre OUKA et Alpha.",
        "lede": "Le niveau entre OUKA et Alpha.",
        "soon": "Bientôt disponible.",
    },
    "zh": {
        "title": "Cherry",
        "desc": "位于 OUKA 与 Alpha 之间的品牌。",
        "lede": "位于 OUKA 与 Alpha 之间的品牌。",
        "soon": "敬请期待。",
    },
    "ko": {
        "title": "Cherry",
        "desc": "OUKA와 Alpha 사이에 자리한 브랜드입니다.",
        "lede": "OUKA와 Alpha 사이에 자리한 브랜드입니다.",
        "soon": "기대해 주세요.",
    },
    "pt-br": {
        "title": "Cherry",
        "desc": "O nível entre OUKA e Alpha.",
        "lede": "O nível entre OUKA e Alpha.",
        "soon": "Em breve.",
    },
    "it": {
        "title": "Cherry",
        "desc": "Il livello tra OUKA e Alpha.",
        "lede": "Il livello tra OUKA e Alpha.",
        "soon": "In arrivo.",
    },
    "ar": {
        "title": "Cherry",
        "desc": "المستوى بين OUKA و Alpha.",
        "lede": "المستوى بين OUKA و Alpha.",
        "soon": "ترقّبوا قريباً.",
    },
    "ru": {
        "title": "Cherry",
        "desc": "Уровень между OUKA и Alpha.",
        "lede": "Уровень между OUKA и Alpha.",
        "soon": "Уже скоро.",
    },
    "id": {
        "title": "Cherry",
        "desc": "Tingkat di antara OUKA dan Alpha.",
        "lede": "Tingkat di antara OUKA dan Alpha.",
        "soon": "Segera hadir.",
    },
    "de": {
        "title": "Cherry",
        "desc": "Die Stufe zwischen OUKA und Alpha.",
        "lede": "Die Stufe zwischen OUKA und Alpha.",
        "soon": "Bald verfügbar.",
    },
    "tr": {
        "title": "Cherry",
        "desc": "OUKA ile Alpha arasındaki seviye.",
        "lede": "OUKA ile Alpha arasındaki seviye.",
        "soon": "Çok yakında.",
    },
}

KEYS = ("title", "desc", "lede", "soon")


# --- the mark ----------------------------------------------------------------
# The real file on disk, measured (PIL), not guessed. mark-584.webp is the 1x
# source for the hero; mark-320.webp serves narrow screens.
MARK = {"file": "mark-584.webp", "w": 584, "h": 557,
        "small": "mark-320.webp", "small_w": 320}
BOX = "min(22rem,68vw)"          # the square the mark turns inside

# A rotating rectangle needs its own diagonal to fit. 100 * w / hypot(w, h) is
# the widest the mark can be and still stay inside that square at EVERY angle;
# at 100% its corners would swing out over the copy beside it.
FIT_PCT = round(100.0 * MARK["w"] / math.hypot(MARK["w"], MARK["h"]), 1)

# --- timing (ms) --------------------------------------------------------------
BLOOM_MS = 1150          # fold -> open
BLOOM_START_MS = 140     # the bloom starts
BREATHE_MS = 5200        # one breath (1 -> .985 -> 1)
SPIN_S = 60              # one revolution of the whole mark
INTRO_HOLD_MS = BLOOM_START_MS + BLOOM_MS + 600   # then .is-intro comes off
INTRO_SCRIPT = (
    '<script>(function(){var s=document.querySelector(".ch-wrap");'
    'if(!s)return;s.classList.add("is-intro");'
    'setTimeout(function(){s.classList.remove("is-intro")},%d)})();</script>'
    % INTRO_HOLD_MS)
HALO_MS = 7000           # one breath of the halo behind it

# The halo is the petal's own shaded colour, --ch-petal-deep (#e8b4c6) from
# gen_cherry_brand.py's PALETTE, written as rgb so it can carry an alpha inside
# the gradient stop.
HALO_RGB = "232,180,198"


# ★ NOT a format string. See the docstring: a mis-doubled brace once emitted
#   broken CSS and the mark stopped moving. __TOKENS__ cannot collide with a
#   brace, and main() refuses to write a page that still contains one.
HEAD = """<link rel="stylesheet" href="__ROOT__assets/css/cherry-tokens.css">
<style>
.ch-wrap{background:var(--ch-bg);color:var(--ch-text);padding:4rem 1.25rem 5rem;
  margin:0 calc(50% - 50vw);width:100vw}
.ch-inner{max-width:60rem;margin:0 auto}
.ch-hero{display:grid;gap:2.5rem;align-items:center;
  grid-template-columns:minmax(0,1fr)}
@media (min-width:52rem){.ch-hero{grid-template-columns:22rem minmax(0,1fr)}}
.ch-mark{position:relative;width:__BOX__;aspect-ratio:1;margin-inline:auto;
  display:grid;place-items:center}
.ch-name{font-size:clamp(2.6rem,7vw,4.2rem);line-height:1.02;margin:0 0 .8rem;
  letter-spacing:-.02em;color:var(--ch-petal)}
.ch-lede{font-size:1.12rem;line-height:1.75;color:var(--ch-text);margin:0}
.ch-soon{margin:4rem 0 0;text-align:center;font-size:1.25rem;letter-spacing:.08em;
  color:var(--ch-petal-deep)}

/* --- the mark: the owner's logo, always turning -------------------------- */
.ch-halo{position:absolute;inset:-4%;border-radius:50%;pointer-events:none;
  background:radial-gradient(circle,rgba(__HALO_RGB__,.30),rgba(__HALO_RGB__,0) 70%);
  animation:ch-halo __HALO_MS__ms ease-in-out infinite}
/* the turn lives alone on this wrapper -- see the docstring's first trap */
.ch-spin{display:block;width:__FIT__%;
  animation:ch-spin __SPIN_S__s linear infinite}
.ch-breathe{display:block;
  animation:ch-breathe __BREATHE_MS__ms ease-in-out __BREATHE_DELAY__ms infinite}
/* The bloom is OPT-IN, for the reason written against .is-intro in
   build_ouka.py: a renderer that runs script but never advances animation
   time holds this `backwards` fill at frame 0 for ever, and frame 0 of
   ch-open is rotate(-90deg) scale(.04) at opacity 0 -- an invisible mark on
   a page whose whole subject is the mark. The class comes off on a timer,
   which needs no frame, so such a renderer settles on the base style: the
   mark, open and turning. */
.is-intro .ch-breathe{
  animation:ch-open __BLOOM_MS__ms cubic-bezier(.16,.84,.28,1) __BLOOM_DELAY__ms backwards,
            ch-breathe __BREATHE_MS__ms ease-in-out __BREATHE_DELAY__ms infinite}
.ch-img{display:block;width:100%;height:auto}

@keyframes ch-spin{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}
@keyframes ch-open{from{transform:rotate(-90deg) scale(.04);opacity:0}
  60%{opacity:1}
  to{transform:rotate(0deg) scale(1);opacity:1}}
@keyframes ch-breathe{0%,100%{transform:scale(1)}50%{transform:scale(.985)}}
@keyframes ch-halo{0%,100%{opacity:.55;transform:scale(1)}
  50%{opacity:.95;transform:scale(1.045)}}

/* Reduced motion skips ONLY the one-time bloom: the mark starts open. The
   turn, the breath and the halo are the mark itself and stay on. */
@media (prefers-reduced-motion:reduce){
  .ch-breathe,.is-intro .ch-breathe{
    animation:ch-breathe __BREATHE_MS__ms ease-in-out infinite}
}
</style>"""

TOKENS = ("__ROOT__", "__BOX__", "__FIT__", "__SPIN_S__", "__BLOOM_MS__",
          "__BLOOM_DELAY__", "__BREATHE_MS__", "__BREATHE_DELAY__",
          "__HALO_MS__", "__HALO_RGB__")


def head_css(root: str) -> str:
    out = HEAD
    for token, value in (
        ("__ROOT__", root),
        ("__BOX__", BOX),
        ("__FIT__", "%g" % FIT_PCT),
        ("__SPIN_S__", str(SPIN_S)),
        ("__BLOOM_MS__", str(BLOOM_MS)),
        ("__BLOOM_DELAY__", str(BLOOM_START_MS)),
        ("__BREATHE_MS__", str(BREATHE_MS)),
        ("__BREATHE_DELAY__", str(BLOOM_START_MS + BLOOM_MS)),
        ("__HALO_MS__", str(HALO_MS)),
        ("__HALO_RGB__", HALO_RGB),
    ):
        out = out.replace(token, value)
    return out


def _mark_html(root: str) -> str:
    """The cut-out mark, wrapped so the turn and the bloom cannot erase each
    other. alt="" on purpose: the <h1> beside it already says Cherry, so a
    screen reader that announced the image too would say the name twice."""
    base = root + "assets/img/cherry/"
    return (
        '<div class="ch-mark"><span class="ch-halo" aria-hidden="true"></span>'
        '<span class="ch-spin"><span class="ch-breathe">'
        '<img class="ch-img" src="%s%s" srcset="%s%s %dw, %s%s %dw" '
        'sizes="calc(%s * %g / 100)" width="%d" height="%d" alt="" '
        'decoding="async" fetchpriority="high" loading="eager">'
        '</span></span></div>'
        % (base, MARK["file"], base, MARK["small"], MARK["small_w"],
           base, MARK["file"], MARK["w"], BOX, FIT_PCT, MARK["w"], MARK["h"])
    )


def build_body(c: dict, root: str) -> str:
    return (
        '<div class="ch-wrap"><div class="ch-inner">'
        '<div class="ch-hero">'
        '%s'
        '<div><h1 class="ch-name">%s</h1>'
        '<p class="ch-lede">%s</p></div>'
        '</div>'
        '<p class="ch-soon">%s</p>'
        '</div></div>%s'
        % (_mark_html(root), esc(c["title"]), esc(c["lede"]), esc(c["soon"]),
           INTRO_SCRIPT)
    )


def main() -> int:
    langs = available_langs()
    missing = [lang for lang in langs if lang not in COPY]
    if missing:
        print("build_cherry: no copy for %s (no fallback by design)" % ", ".join(missing))
        return 1
    for lang, c in COPY.items():
        gaps = [k for k in KEYS if not c.get(k)]
        if gaps:
            print("build_cherry: %s is missing %s" % (lang, ", ".join(gaps)))
            return 1
    for lang in langs:
        c = COPY[lang]
        # NOT "../" for every language: /de/cherry/ is two levels below the
        # site root but one below its language root.
        root = asset_root_prefix(1, lang)
        html = page(
            lang=lang,
            section=SECTION,
            title=c["title"],
            description=c["desc"],
            active="cherry",
            body=build_body(c, root),
            depth=1,
            extra_head=head_css(root),
        )
        # --- the three ways this page has failed silently, all refused here.
        # 1. a substitution token surviving into the CSS (the broken-brace
        #    defect's successor): the rule would be discarded and the mark
        #    would sit still, with nothing red anywhere.
        left = [tok for tok in TOKENS if tok in html]
        if left or "{{" in html:
            raise SystemExit(
                "ERROR: build_cherry: %s still holds %s -- the CSS would be "
                "discarded and the mark would not move."
                % (lang, left or ["{{"]))
        # 2. the mark missing, or its animations gone: a text-only hero still
        #    renders perfectly well and looks intentional.
        for needed in ("ch-img", "@keyframes ch-spin", "@keyframes ch-open",
                       "@keyframes ch-breathe", "prefers-reduced-motion"):
            if needed not in html:
                raise SystemExit(
                    "ERROR: build_cherry: %s is missing %r." % (lang, needed))
        # 2b. the bloom must be opt-in and must switch itself off. Frame 0 of
        #    ch-open is an invisible mark, and a renderer that never advances
        #    animation time holds it for ever behind the `backwards` fill.
        if ".is-intro .ch-breathe{\n  animation:ch-open" not in html:
            raise SystemExit(
                "ERROR: build_cherry: %s does not scope the bloom to "
                ".is-intro. A renderer that never advances animation time "
                "would hold frame 0 -- rotate(-90deg) scale(.04) at opacity "
                "0, an invisible mark." % lang)
        if ".ch-breathe{display:block;\n  animation:ch-open" in html:
            raise SystemExit(
                "ERROR: build_cherry: %s still blooms outside .is-intro." % lang)
        for needed in ('classList.add("is-intro")',
                       'classList.remove("is-intro")', str(INTRO_HOLD_MS)):
            if needed not in html:
                raise SystemExit(
                    "ERROR: build_cherry: %s is missing %r -- without it the "
                    "bloom either never runs or never ends." % (lang, needed))
        # 3. the image path resolving to nothing from THIS page's depth.
        want = root + "assets/img/cherry/" + MARK["file"]
        target = ROOT / ("" if lang == "ja" else lang) / SECTION / "index.html"
        probe = (target.parent / want).resolve()
        if not probe.is_file():
            raise SystemExit(
                "ERROR: build_cherry: %s references %s, which resolves to %s "
                "-- no such file. The mark would 404." % (lang, want, probe))
        write_page(lang, SECTION, html)
    print("build_cherry: %d language(s), mark %s at %g%% of %s"
          % (len(langs), MARK["file"], FIT_PCT, BOX))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
