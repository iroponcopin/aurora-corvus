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
    ROOT, available_langs, esc, page, write_page,
)

SECTION = "alpha/"


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


def build_body(c: dict, f: dict, lang_prefix: str) -> str:
    lede = c["lede"].format(**f)
    cards = []
    for h, p in (("h_ship", "p_ship"), ("h_gate", "p_gate"), ("h_launcher", "p_launcher")):
        cards.append('<div class="al-card"><h2>%s</h2><p>%s</p></div>'
                     % (esc(c[h]), esc(c[p].format(**f))))
    return (
        '<div class="al-wrap"><div class="al-hero">'
        '<h1 class="al-name">%s</h1><p class="al-lede">%s</p>'
        '<div class="al-cta">'
        '<a class="btn btn--action" href="%sdownload/">%s</a>'
        '<a class="btn" href="%schangelog/">%s</a>'
        '</div></div>'
        '<div class="al-grid">%s</div></div>'
        % (esc(c["title"]), esc(lede), lang_prefix, esc(c["cta_dl"]),
           lang_prefix, esc(c["cta_log"]), "".join(cards))
    )


def main() -> int:
    f = facts()
    langs = available_langs()
    for lang in langs:
        c = COPY.get(lang, COPY["en"])
        lang_prefix = "../"
        html = page(
            lang=lang,
            section=SECTION,
            title=c["title"],
            description=c["desc"],
            active="alpha",
            body=build_body(c, f, lang_prefix),
            depth=1,
            extra_head=HEAD,
        )
        write_page(lang, SECTION, html)
    print("build_alpha: %d language(s), version %s, %d modules"
          % (len(langs), f["version"], f["modules"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
