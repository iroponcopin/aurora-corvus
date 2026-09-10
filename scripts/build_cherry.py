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

  1. Cherry is the tier above Alpha — said once, as a fact, not argued.
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
The mark — it blooms once, then it never stops moving
--------------------------------------------------------------------------
On open, the five petals begin folded into the centre (scaled to nothing and
rotated back by 90 degrees) and unfold outward one after another, each rotating
into its final 72-degree seat as it grows. The stamens fade in last.

From the first frame and forever after, the whole flower turns — one
revolution a minute, linear, on the <g class="ch-spin"> wrapper the generator
provides. As each petal finishes opening it starts to breathe (scale 1 ->
0.985 -> 1 over ~5 s, staggered), and a soft band of light glides from the
heart of each petal to its tip every ~7 s, also staggered. All of it is CSS
keyframes with `infinite` iteration; no JavaScript, no SMIL, no library.

`prefers-reduced-motion: reduce` skips ONLY the one-time bloom (the flower
starts open). The rotation, the breathing and the light are the identity of
the mark — 「常時動いているロゴ」 — and stay on regardless.

Two traps this file inherits from gen_cherry_brand.py (read its docstring):
CSS `transform` REPLACES an element's own `transform` attribute, so the whole-
flower rotation lives on the wrapper (which has no attribute) and every petal
keyframe re-states the petal's seat angle as a literal; and var(--i) does not
resolve per element inside @keyframes, so the generator writes five sets.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from site_common import (  # noqa: E402
    ROOT, available_langs, esc, page, write_page,
)

SECTION = "cherry/"

# --- copy -------------------------------------------------------------------
# Every language the site ships has its own entry; there is no fallback. Brand
# names (Cherry, Alpha, Corvus) are never translated. Keys, in every language:
#   title, desc, lede, soon.
COPY = {
    "ja": {
        "title": "Cherry",
        "desc": "Alpha の上位に位置するブランド。",
        "lede": "Alpha の上位に位置するブランド。",
        "soon": "ご期待ください。",
    },
    "en": {
        "title": "Cherry",
        "desc": "The tier above Alpha.",
        "lede": "The tier above Alpha.",
        "soon": "Coming soon.",
    },
    "es": {
        "title": "Cherry",
        "desc": "El nivel por encima de Alpha.",
        "lede": "El nivel por encima de Alpha.",
        "soon": "Muy pronto.",
    },
    "fr": {
        "title": "Cherry",
        "desc": "Le niveau au-dessus d'Alpha.",
        "lede": "Le niveau au-dessus d'Alpha.",
        "soon": "Bientôt disponible.",
    },
    "zh": {
        "title": "Cherry",
        "desc": "位于 Alpha 之上的品牌。",
        "lede": "位于 Alpha 之上的品牌。",
        "soon": "敬请期待。",
    },
    "ko": {
        "title": "Cherry",
        "desc": "Alpha 위에 자리한 브랜드입니다.",
        "lede": "Alpha 위에 자리한 브랜드입니다.",
        "soon": "기대해 주세요.",
    },
    "pt-br": {
        "title": "Cherry",
        "desc": "O nível acima do Alpha.",
        "lede": "O nível acima do Alpha.",
        "soon": "Em breve.",
    },
    "it": {
        "title": "Cherry",
        "desc": "Il livello sopra Alpha.",
        "lede": "Il livello sopra Alpha.",
        "soon": "In arrivo.",
    },
    "ar": {
        "title": "Cherry",
        "desc": "المستوى الأعلى من Alpha.",
        "lede": "المستوى الأعلى من Alpha.",
        "soon": "ترقّبوا قريباً.",
    },
    "ru": {
        "title": "Cherry",
        "desc": "Уровень выше Alpha.",
        "lede": "Уровень выше Alpha.",
        "soon": "Уже скоро.",
    },
    "id": {
        "title": "Cherry",
        "desc": "Tingkat di atas Alpha.",
        "lede": "Tingkat di atas Alpha.",
        "soon": "Segera hadir.",
    },
    "de": {
        "title": "Cherry",
        "desc": "Die Stufe über Alpha.",
        "lede": "Die Stufe über Alpha.",
        "soon": "Bald verfügbar.",
    },
    "tr": {
        "title": "Cherry",
        "desc": "Alpha'nın üzerindeki seviye.",
        "lede": "Alpha'nın üzerindeki seviye.",
        "soon": "Çok yakında.",
    },
}

KEYS = ("title", "desc", "lede", "soon")


def _blossom_svg() -> str:
    """The generated mark, inlined so the petals can be animated individually."""
    svg = (ROOT / "assets" / "img" / "cherry" / "blossom.svg").read_text(encoding="utf-8")
    # inline it at the page's own size; the file carries width/height for
    # standalone use (favicon, launcher), which must not win here.
    svg = svg.replace('width="512" height="512"', 'class="ch-bloom" width="100%" height="100%"')
    return svg


# --- timing (ms) --------------------------------------------------------------
BLOOM_MS = 1150          # one petal, fold -> seat
BLOOM_STEP_MS = 105      # petal-to-petal stagger of the bloom
BLOOM_START_MS = 140     # petal 0 starts
BREATHE_MS = 5200        # one breath (1 -> .985 -> 1)
BREATHE_STEP_MS = 420    # petal-to-petal stagger of the breath
SPIN_S = 60              # one revolution of the whole flower
SHEEN_MS = 7000          # one pass of light along a petal, pause included
SHEEN_STEP_MS = 260      # petal-to-petal stagger of the light


HEAD = """<link rel="stylesheet" href="{root}assets/css/cherry-tokens.css">
<style>
.ch-wrap{{background:var(--ch-bg);color:var(--ch-text);padding:4rem 1.25rem 5rem;
  margin:0 calc(50% - 50vw);width:100vw}}
.ch-inner{{max-width:60rem;margin:0 auto}}
.ch-hero{{display:grid;gap:2.5rem;align-items:center;
  grid-template-columns:minmax(0,1fr)}}
@media (min-width:52rem){{.ch-hero{{grid-template-columns:22rem minmax(0,1fr)}}}}
.ch-mark{{width:min(22rem,68vw);aspect-ratio:1;margin-inline:auto}}
.ch-name{{font-size:clamp(2.6rem,7vw,4.2rem);line-height:1.02;margin:0 0 .8rem;
  letter-spacing:-.02em;color:var(--ch-petal)}}
.ch-lede{{font-size:1.12rem;line-height:1.75;color:var(--ch-text);margin:0}}
.ch-soon{{margin:4rem 0 0;text-align:center;font-size:1.25rem;letter-spacing:.08em;
  color:var(--ch-petal-deep)}}

/* --- the mark ------------------------------------------------------------
   Blooms once on load; from then on it never stops moving.

   ★ 角度は<b>1 枚ずつ literal で書き出す</b>。最初は
     `rotate(calc(var(--i) * 72deg))` を 1 つの @keyframes で共有していたが、
     実際にブラウザで開くと<b>花弁が 1 枚しか見えなかった</b> ——
     @keyframes の中の var() が花弁ごとに解決されず、5 枚とも rotate(0) に
     畳まれて重なっていた。生成器が 5 組を書き出せば、その曖昧さは消える。

   ★ 原点もユーザー単位で明示する。50%% 50%% は view-box ではなく要素自身の
     箱に対して解決されていた。viewBox は 512 なので中心は 256。

   ★ CSS の transform は要素の transform 属性を<b>置き換える</b>。花全体の
     回転は属性を持たない包み .ch-spin にだけ掛け、花弁の keyframe は
     どれも自分の座席角を literal で書き直す。 */

/* 1. the whole flower turns, forever, from the first frame */
.ch-bloom .ch-spin{{transform-box:view-box;transform-origin:256px 256px;
  animation:ch-spin {spin_s}s linear infinite}}
@keyframes ch-spin{{from{{transform:rotate(0deg)}}to{{transform:rotate(360deg)}}}}

/* 2. each petal: bloom once, then breathe forever (literal angle per petal) */
{petals}

/* 3. a soft light glides from the heart of each petal to its tip, forever */
{sheen}
@keyframes ch-sheen{{0%{{transform:translateY(0)}}58%{{transform:translateY(-560px)}}
  100%{{transform:translateY(-560px)}}}}

/* 4. the stamens fade in last (once) */
.ch-bloom .ch-stamens,.ch-bloom .ch-anthers{{
  animation:ch-fade 700ms ease-out backwards;animation-delay:900ms}}
@keyframes ch-fade{{from{{opacity:0}}to{{opacity:1}}}}

/* Reduced motion skips ONLY the one-time bloom: the flower starts open. The
   rotation, the breath and the light are the mark itself and stay on. */
@media (prefers-reduced-motion:reduce){{
  .ch-bloom .ch-stamens,.ch-bloom .ch-anthers{{animation:none}}
{petals_reduced}
}}
</style>"""


def _petal_css() -> tuple[str, str, str]:
    """Per-petal rules: (normal, reduced-motion, sheen). Angles literal, origin user units.

    ★ ここは HEAD.format() に<b>値として</b>差し込まれる。テンプレート側と違って
      波括弧を {{ }} と二重にしてはいけない —— 最初の版はそうしていて、出力が
      `{{transform-box:...}}` という<b>壊れた CSS</b> になり、花弁の規則が
      丸ごと捨てられていた。所有者が見た「一切動かないロゴ」の正体はこれ。
      生成後の cherry/index.html を grep して `{{` が無いことを確かめること。
    """
    normal, reduced, sheen = [], [], []
    for i in range(5):
        end = i * 72.0
        start = end - 90.0
        bloom_delay = BLOOM_START_MS + i * BLOOM_STEP_MS
        breathe_delay = bloom_delay + BLOOM_MS + i * BREATHE_STEP_MS  # never before its bloom ends
        sel = ".ch-bloom .ch-petal[style*='--i:%d']" % i
        normal.append(
            "%s{transform-box:view-box;transform-origin:256px 256px;"
            "animation:ch-open-%d %dms cubic-bezier(.16,.84,.28,1) %dms backwards,"
            "ch-breathe-%d %dms ease-in-out %dms infinite}"
            % (sel, i, BLOOM_MS, bloom_delay, i, BREATHE_MS, breathe_delay))
        normal.append(
            "@keyframes ch-open-%d{"
            "from{transform:rotate(%.1fdeg) scale(.04);opacity:0}"
            "60%%{opacity:1}"
            "to{transform:rotate(%.1fdeg) scale(1);opacity:1}}" % (i, start, end))
        normal.append(
            "@keyframes ch-breathe-%d{"
            "0%%,100%%{transform:rotate(%.1fdeg) scale(1)}"
            "50%%{transform:rotate(%.1fdeg) scale(.985)}}" % (i, end, end))
        reduced.append(
            "  %s{animation:ch-breathe-%d %dms ease-in-out %dms infinite}"
            % (sel, i, BREATHE_MS, i * BREATHE_STEP_MS))
        sheen.append(
            "%s .ch-sheen{animation:ch-sheen %dms ease-in-out %dms infinite}"
            % (sel, SHEEN_MS, bloom_delay + BLOOM_MS + 400 + i * SHEEN_STEP_MS))
    return "\n".join(normal), "\n".join(reduced), "\n".join(sheen)


def build_body(c: dict) -> str:
    return (
        '<div class="ch-wrap"><div class="ch-inner">'
        '<div class="ch-hero">'
        '<div class="ch-mark">%s</div>'
        '<div><h1 class="ch-name">%s</h1>'
        '<p class="ch-lede">%s</p></div>'
        '</div>'
        '<p class="ch-soon">%s</p>'
        '</div></div>'
        % (_blossom_svg(), esc(c["title"]), esc(c["lede"]), esc(c["soon"]))
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
    petals, petals_reduced, sheen = _petal_css()
    for lang in langs:
        c = COPY[lang]
        body = build_body(c)
        html = page(
            lang=lang,
            section=SECTION,
            title=c["title"],
            description=c["desc"],
            active="cherry",
            body=body,
            depth=1,
            extra_head=HEAD.format(root="../" if lang == "ja" else "../../",
                                   spin_s=SPIN_S, petals=petals,
                                   petals_reduced=petals_reduced, sheen=sheen),
        )
        write_page(lang, SECTION, html)
    print("build_cherry: %d language(s)" % len(langs))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
