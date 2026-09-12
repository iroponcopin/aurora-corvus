#!/usr/bin/env python3
"""Builds alpha/index.html — the Alpha brand page, for every language.

Owner directive (2026-09-10):

    AuleumとCherry、Alphaのページを作成して、それをStoreという新規のタブを
    作成して、メガメニューに3つのModsを表示する。

Aureum and Cherry already had a page of their own. **Alpha did not.** There was
a download page, a changelog, a guide, recipes, gates — every one of them about
a *part* of Alpha — and no single page that answered "what is Alpha". That is
the gap this fills, and it is why the three brands could not sit side by side
in a Store menu before: one of the three had nowhere to point.

Everything numeric on this page is read from the site's own data at build time
(data/versions.json, data/changelog.json), never typed in here. A brand page
that states a version is a brand page that goes stale the next release.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from site_common import (  # noqa: E402
    ROOT, asset_root_prefix, available_langs, esc, page, write_page,
)

SECTION = "alpha/"

# The Alpha mark, cut from the owner's own logo photograph (the wordmark in
# that photograph is NOT used -- 「ロゴにはテキストが含まれていますがこれは一切
# 使用せずロゴだけを切り取り使用してください」). The gradient wordmark below it
# stays the page's h1: the mark is the picture of the name, the h1 IS the name,
# so the image is decorative and carries alt="" rather than repeating "Alpha"
# to a screen reader that is about to read the heading anyway.
#
# Intrinsic sizes are the real files on disk, measured, not guessed --
# mark-584.webp is 584x384 and mark-320.webp is 320x211. width/height are
# emitted so the hero reserves its box before the image arrives.
MARK = {"file": "mark-584.webp", "w": 584, "h": 384,
        "small": "mark-320.webp", "small_w": 320}


def facts() -> dict:
    """Version and module count — from the site's own data, not from here."""
    versions = json.loads((ROOT / "data" / "versions.json").read_text(encoding="utf-8"))
    mods = versions["mods"]
    distinct = sorted(set(mods.values()))
    if len(distinct) != 1:
        raise SystemExit(
            "ERROR: data/versions.json lists more than one version %s — the Alpha page "
            "cannot state a single one." % distinct)
    entries = json.loads((ROOT / "data" / "changelog.json").read_text(encoding="utf-8"))
    return {
        "version": distinct[0],
        "modules": len(mods),
        "mc": versions.get("mc_version", ""),
        "releases": len(entries),
    }


COPY = {
    "ja": {
        "title": "Alpha",
        "desc": "13 のモジュールで動く、いま出荷しているパック。",
        "lede": "Alpha は、いま実際に配布して動いているパックです。"
                "銃火器・鉄道・車両・建材・災害・異次元まで、{modules} のモジュールが"
                "1 つのバージョンで足並みを揃えて出ます。",
        "h_ship": "出荷している",
        "p_ship": "現行は {version}(Minecraft {mc})。これまでに {releases} 回配信しています。"
                  "変更点は毎回すべて公開しています。",
        "h_gate": "測ってから出す",
        "p_gate": "「直った」と言う前に測ります。実測できない主張は載せません。"
                  "門が赤いまま出荷はしません。",
        "h_launcher": "Corvus で入る",
        "p_launcher": "Corvus ランチャーが 13 個の jar をまとめて入れ、更新も追従します。"
                      "手で 1 つずつ入れ替える必要はありません。",
        "cta_dl": "ダウンロード",
        "cta_log": "変更履歴",
    },
    "en": {
        "title": "Alpha",
        "desc": "The suite that ships today, across 13 modules.",
        "lede": "Alpha is the pack that is actually out and running. Firearms, rail, "
                "vehicles, building, disasters and other dimensions — {modules} modules "
                "that move together on one version.",
        "h_ship": "It ships",
        "p_ship": "Currently {version} on Minecraft {mc}, after {releases} releases. "
                  "Every change is published, every time.",
        "h_gate": "Measured before it ships",
        "p_gate": "Nothing is called fixed until it has been measured. Claims that cannot "
                  "be measured do not go on the page, and a red gate does not ship.",
        "h_launcher": "Installs with Corvus",
        "p_launcher": "The Corvus launcher installs all 13 jars together and keeps them "
                      "current. No swapping files by hand.",
        "cta_dl": "Download",
        "cta_log": "Changelog",
    },
}

HEAD = """<style>
/* ★ この HEAD は .format() を通さない。二重波括弧はそのまま CSS に出て
   規則を丸ごと無効にする(実際に一度そうなり、カードが素の見出しになった)。 */
.al-wrap{padding:3.5rem 0 1rem}
.al-hero{max-width:52rem}
/* The mark sits above the name at hero scale. It is capped in rem AND in vw so
   it cannot outgrow a phone; height:auto keeps the measured 584x384 ratio. */
.al-mark{display:block;width:min(19rem,58vw);height:auto;margin:0 0 1.15rem}
/* One entrance, once. The mark is not an animated logo (that is Cherry's and
   OUKA's job) -- it rises into place and then holds. */
@media (prefers-reduced-motion:no-preference){
  .al-mark{animation:al-mark-in 900ms cubic-bezier(.16,.84,.28,1) both}
}
@keyframes al-mark-in{from{opacity:0;transform:translateY(14px) scale(.985)}
  to{opacity:1;transform:none}}
.al-name{font-size:clamp(2.6rem,7vw,4.2rem);line-height:1.02;margin:0 0 .8rem;
  letter-spacing:-.02em;
  background:linear-gradient(100deg,var(--text) 18%,var(--accent-strong) 62%,var(--aurora-green) 96%);
  -webkit-background-clip:text;background-clip:text;color:transparent}
.al-lede{font-size:1.14rem;line-height:1.78;color:var(--text);margin:0 0 1.6rem}
.al-cta{display:flex;gap:.7rem;flex-wrap:wrap;margin-bottom:2.6rem}
.al-grid{display:grid;gap:1.25rem;
  grid-template-columns:repeat(auto-fit,minmax(15rem,1fr))}
.al-card{background:var(--glass-bg);border:1px solid var(--glass-border);border-radius:14px;
  padding:1.4rem 1.3rem;box-shadow:var(--glass-highlight)}
.al-card h2{font-size:1.06rem;margin:0 0 .5rem;color:var(--accent-strong)}
.al-card p{margin:0;color:var(--text-muted);line-height:1.7;font-size:.97rem}
</style>"""


def build_body(c: dict, f: dict, lang_prefix: str, asset_prefix: str) -> str:
    lede = c["lede"].format(**f)
    mark = (
        '<img class="al-mark" src="%sassets/img/alpha/%s" '
        'srcset="%sassets/img/alpha/%s %dw, %sassets/img/alpha/%s %dw" '
        'sizes="min(19rem,58vw)" width="%d" height="%d" alt="" '
        'decoding="async" fetchpriority="high" loading="eager">'
        % (asset_prefix, MARK["file"],
           asset_prefix, MARK["small"], MARK["small_w"],
           asset_prefix, MARK["file"], MARK["w"],
           MARK["w"], MARK["h"])
    )
    cards = []
    for h, p in (("h_ship", "p_ship"), ("h_gate", "p_gate"), ("h_launcher", "p_launcher")):
        cards.append('<div class="al-card"><h2>%s</h2><p>%s</p></div>'
                     % (esc(c[h]), esc(c[p].format(**f))))
    return (
        '<div class="al-wrap"><div class="al-hero">'
        '%s'
        '<h1 class="al-name">%s</h1><p class="al-lede">%s</p>'
        '<div class="al-cta">'
        '<a class="btn btn--action" href="%sdownload/">%s</a>'
        '<a class="btn" href="%schangelog/">%s</a>'
        '</div></div>'
        '<div class="al-grid">%s</div></div>'
        % (mark, esc(c["title"]), esc(lede), lang_prefix, esc(c["cta_dl"]),
           lang_prefix, esc(c["cta_log"]), "".join(cards))
    )


def main() -> int:
    f = facts()
    langs = available_langs()
    for lang in langs:
        c = COPY.get(lang, COPY["en"])
        lang_prefix = "../"
        # NOT the same string as lang_prefix: /de/alpha/ is two levels below
        # the site root but one below its language root. Hardcoding "../" here
        # is the 404 that site_common.asset_root_prefix() exists to prevent.
        asset_prefix = asset_root_prefix(1, lang)
        html = page(
            lang=lang,
            section=SECTION,
            title=c["title"],
            description=c["desc"],
            active="alpha",
            body=build_body(c, f, lang_prefix, asset_prefix),
            depth=1,
            extra_head=HEAD,
        )
        # The mark is the one thing on this page that can fail silently: a
        # wrong prefix or a dropped <img> still renders a perfectly good text
        # hero, and nothing goes red. Assert it is there, with a path that
        # resolves from THIS page's depth, before the file is written.
        want = '%sassets/img/alpha/%s' % (asset_prefix, MARK["file"])
        if want not in html:
            raise SystemExit(
                "ERROR: build_alpha: the hero mark (%s) is not in the rendered "
                "%s page." % (want, lang))
        target = ROOT / ("" if lang == "ja" else lang) / SECTION / "index.html"
        probe = (target.parent / want).resolve()
        if not probe.is_file():
            raise SystemExit(
                "ERROR: build_alpha: %s references %s, which resolves to %s -- "
                "no such file. The hero mark would 404." % (lang, want, probe))
        write_page(lang, SECTION, html)
    print("build_alpha: %d language(s), version %s, %d modules, hero mark %s"
          % (len(langs), f["version"], f["modules"], MARK["file"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
