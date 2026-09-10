#!/usr/bin/env python3
"""Builds cherry/index.html — the Cherry brand page, for every language.

Owner directive (2026-09-10, IROHA, verbatim):

    次世代のModsを作りに着手を始めます。
    Modsのブランド名称はCherryです。桜という意味が込められます。
    ブランドロゴも桜の花を採用すると共にCorvusの様にWebサイトを開くと
    桜の花びらが回転しながら咲くアニメーションが加えられ、Modsの紹介が
    行われます。
    （…）全体的にAppleの様に美しく妥協のないデザインを採用し、Mods自体も
    一切の妥協がない状態で機能することとなります。
    Alphaの上位ブランドという位置付けになるでしょう。
    Alpha Modsと併用して導入することができますが、バージョンは異なります。
    そしてCorvusランチャーにも対応し、自動でアップデート初回はダウンロード
    ボタンが表示されます。

--------------------------------------------------------------------------
What this page IS, and what it is NOT
--------------------------------------------------------------------------
It is the brand's front door: the mark, the blossom animation the owner asked
for, the positioning against Alpha, and the launcher contract.

It is NOT a download page, because **there is nothing to download yet**. Not a
single Cherry mod has been written. Every other page on this site describes
something that ships; this one describes something that has been *started*, and
it says so in its own first paragraph in all 13 languages. The old V3 teaser
(scripts/build_v3_teaser.py, deleted the day V3 shipped) is the precedent for
how a "not yet" page is written here — state the status plainly, on the page,
where the reader is; never imply a build exists.

--------------------------------------------------------------------------
The animation — "桜の花びらが回転しながら咲く"
--------------------------------------------------------------------------
On open, the five petals begin folded into the centre (scaled to nothing and
rotated back by 90 degrees) and unfold outward one after another, each rotating
into its final 72-degree position as it grows. The stamens fade in last. It
runs ONCE on load, like a flower opening — not a loop, because a loop turns a
bloom into a spinner.

It is CSS only: transform + opacity on five <path> elements, which the
compositor animates without touching layout or paint. No JavaScript, no canvas,
no library. `prefers-reduced-motion: reduce` skips straight to the open flower —
a bloom is decoration, and decoration must never be the thing that stops
somebody reading the page.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from site_common import (  # noqa: E402
    ROOT, available_langs, esc, load_bundle, page, write_page,
)

SECTION = "cherry/"

# --- copy -------------------------------------------------------------------
# Japanese is the owner's language and the site's default; English is the
# fallback for the other eleven, exactly as build_skin_gate.py does. Where a
# bundle has no Cherry strings yet, the reader gets English rather than a raw
# key — and the page says which state it is in.
COPY = {
    "ja": {
        "title": "Cherry",
        "desc": "Alpha の上位ブランド。桜の名を持つ次世代 MOD。",
        "status": "着手したところです。まだ配布できるビルドはありません。",
        "lede": "Cherry は Alpha の上位に置くブランドです。名前には桜の意味を込めています。"
                "Alpha と併せて導入でき、バージョンは別に進みます。",
        "h_design": "妥協しない",
        "p_design": "見た目も、動きも、音も、数字で確かめられるところまで作ります。"
                    "Alpha でやってきたとおり、主張ではなく実測で通します。",
        "h_along": "Alpha と一緒に入る",
        "p_along": "Cherry は Alpha を置き換えません。同じワールドに両方入れられます。"
                   "バージョンは互いに独立して進みます。",
        "h_launcher": "Corvus ランチャー対応",
        "p_launcher": "初回はダウンロードボタンが出ます。以後は自動で更新されます。"
                      "Alpha と同じ仕組みの上に載ります。",
        "h_state": "いまの状態",
        "p_state": "ブランド名・ロゴ・このページまでができています。"
                   "MOD 本体はこれからです。進捗はこのページで報告します。",
    },
    "en": {
        "title": "Cherry",
        "desc": "The tier above Alpha. A next-generation mod line named for the cherry blossom.",
        "status": "Just started. There is no build to download yet.",
        "lede": "Cherry sits above Alpha. The name carries the meaning of sakura — the cherry "
                "blossom. It installs alongside Alpha and versions independently.",
        "h_design": "No compromise",
        "p_design": "How it looks, how it moves, how it sounds — built until each can be checked "
                    "with a number. The same standard Alpha is held to: measured, not asserted.",
        "h_along": "Runs alongside Alpha",
        "p_along": "Cherry does not replace Alpha. Both can be installed in the same world, and "
                   "their versions advance independently of each other.",
        "h_launcher": "Corvus launcher",
        "p_launcher": "A download button the first time, automatic updates after that — on the "
                      "same mechanism Alpha already uses.",
        "h_state": "Where it stands",
        "p_state": "The name, the mark and this page exist. The mods themselves do not yet. "
                   "Progress will be reported here.",
    },
}


def _blossom_svg() -> str:
    """The generated mark, inlined so the petals can be animated individually."""
    svg = (ROOT / "assets" / "img" / "cherry" / "blossom.svg").read_text(encoding="utf-8")
    # inline it at the page's own size; the file carries width/height for
    # standalone use (favicon, launcher), which must not win here.
    svg = svg.replace('width="512" height="512"', 'class="ch-bloom" width="100%" height="100%"')
    return svg


HEAD = """<link rel="stylesheet" href="{root}assets/css/cherry-tokens.css">
<style>
.ch-wrap{{background:var(--ch-bg);color:var(--ch-text);padding:4rem 1.25rem 5rem;
  margin:0 calc(50% - 50vw);width:100vw}}
.ch-inner{{max-width:60rem;margin:0 auto}}
.ch-hero{{display:grid;gap:2.5rem;align-items:center;
  grid-template-columns:minmax(0,1fr)}}
@media (min-width:52rem){{.ch-hero{{grid-template-columns:22rem minmax(0,1fr)}}}}
.ch-mark{{width:min(22rem,68vw);aspect-ratio:1;margin-inline:auto}}
.ch-name{{font-size:clamp(2.6rem,7vw,4.2rem);line-height:1.02;margin:0 0 .6rem;
  letter-spacing:-.02em;color:var(--ch-petal)}}
.ch-lede{{font-size:1.12rem;line-height:1.75;color:var(--ch-text);margin:0 0 1rem}}
.ch-status{{display:inline-block;border:1px solid var(--ch-blush);color:var(--ch-petal-deep);
  border-radius:999px;padding:.3rem .9rem;font-size:.86rem;margin-bottom:1.1rem}}
.ch-grid{{display:grid;gap:1.25rem;margin-top:3.5rem;
  grid-template-columns:repeat(auto-fit,minmax(15rem,1fr))}}
.ch-card{{background:var(--ch-bg-lift);border:1px solid var(--ch-line);border-radius:14px;
  padding:1.4rem 1.3rem}}
.ch-card h2{{font-size:1.06rem;margin:0 0 .5rem;color:var(--ch-petal)}}
.ch-card p{{margin:0;color:var(--ch-text-muted);line-height:1.7;font-size:.97rem}}

/* --- the bloom -----------------------------------------------------------
   Each petal starts folded into the centre and unfolds into its own
   72-degree seat.

   ★ 角度は<b>1 枚ずつ literal で書き出す</b>。最初は
     `rotate(calc(var(--i) * 72deg))` を 1 つの @keyframes で共有していたが、
     実際にブラウザで開くと<b>花弁が 1 枚しか見えなかった</b> ——
     @keyframes の中の var() が花弁ごとに解決されず、5 枚とも rotate(0) に
     畳まれて重なっていた。生成器が 5 組を書き出せば、その曖昧さは消える。

   ★ 原点もユーザー単位で明示する。50%% 50%% は view-box ではなく要素自身の
     箱に対して解決されていた。viewBox は 512 なので中心は 256。 */
{petals}
.ch-bloom .ch-stamens,.ch-bloom .ch-anthers{{
  animation:ch-fade 700ms ease-out backwards;animation-delay:900ms}}
@keyframes ch-fade{{from{{opacity:0}}to{{opacity:1}}}}
@media (prefers-reduced-motion:reduce){{
  .ch-bloom .ch-petal,.ch-bloom .ch-stamens,.ch-bloom .ch-anthers{{animation:none}}}}
</style>"""


def _petal_css() -> str:
    """5 枚ぶんの @keyframes と割り当て。角度は literal、原点は user unit。"""
    out = []
    for i in range(5):
        end = i * 72.0
        start = end - 90.0
        out.append(
            ".ch-bloom .ch-petal[style*='--i:%d']{{transform-box:view-box;"
            "transform-origin:256px 256px;"
            "animation:ch-open-%d 1150ms cubic-bezier(.16,.84,.28,1) backwards;"
            "animation-delay:%dms}}" % (i, i, 140 + i * 105))
        out.append(
            "@keyframes ch-open-%d{{"
            "from{{transform:rotate(%.1fdeg) scale(.04);opacity:0}}"
            "60%%{{opacity:1}}"
            "to{{transform:rotate(%.1fdeg) scale(1);opacity:1}}}}" % (i, start, end))
    return "\n".join(out)


def build_body(c: dict) -> str:
    cards = []
    for h, p in (("h_design", "p_design"), ("h_along", "p_along"),
                 ("h_launcher", "p_launcher"), ("h_state", "p_state")):
        cards.append('<div class="ch-card"><h2>%s</h2><p>%s</p></div>'
                     % (esc(c[h]), esc(c[p])))
    return (
        '<div class="ch-wrap"><div class="ch-inner">'
        '<div class="ch-hero">'
        '<div class="ch-mark">%s</div>'
        '<div><span class="ch-status">%s</span>'
        '<h1 class="ch-name">%s</h1>'
        '<p class="ch-lede">%s</p></div>'
        '</div>'
        '<div class="ch-grid">%s</div>'
        '</div></div>'
        % (_blossom_svg(), esc(c["status"]), esc(c["title"]), esc(c["lede"]), "".join(cards))
    )


def main() -> int:
    langs = available_langs()
    for lang in langs:
        c = COPY.get(lang, COPY["en"])
        # the mark's own rotation is applied by the CSS animation's `to` state,
        # so the static SVG's transform must not fight it.
        body = build_body(c)
        root = "" if lang == "ja" else "../"
        html = page(
            lang=lang,
            section=SECTION,
            title=c["title"],
            description=c["desc"],
            active="cherry",
            body=body,
            depth=1,
            extra_head=HEAD.format(root="../" if lang == "ja" else "../../",
                                   petals=_petal_css()),
        )
        write_page(lang, SECTION, html)
    print("build_cherry: %d language(s)" % len(langs))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
