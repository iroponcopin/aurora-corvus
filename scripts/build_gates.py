#!/usr/bin/env python3
"""Builds gates/index.html for every language that has a bundle, from
bundle["gates"] (a list of {id, title, body_html} written directly into
data/i18n/<lang>.json — this content is short and hand-authored per language
rather than routed through a top-level data/gates.json + extract step).

Every gate on the server gets a page: vanilla Nether/End (untouched by this
pack, but the brief is explicit that "every gate" still means them), the
Amethyst Gate, the Heaven (sky) gate, and the Backrooms End City rift.
body_html may contain the placeholder "{img_root}", replaced here with the
correct depth-relative asset prefix for this language (ja sits at the site
root; every other language sits one level deeper) so a single string works
for both.

⚠ An ABSENT `gates` key stops the build; it used to render "Coming soon."
  and exit 0. `gates` is one of the four blocks that live ONLY in
  data/i18n/*.json with no source file behind them, and until 2026-08-29
  scripts/extract_bundle.py deleted all four every time it ran. See the
  matching ⚠ block in scripts/build_features.py for the full chain.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from site_common import esc, page, write_page, load_bundle, available_langs, asset_root_prefix  # noqa: E402

# The language this content is authored in. Empty here means it was lost, not
# that it is awaiting translation.
AUTHORING_LANG = "ja"


def require_sections(bundle, lang, key, what):
    """The bundle's `key` list, or a stopped build. See the ⚠ block above.

    Deliberately a copy of build_features.py's function rather than a shared
    import: these two page builders do not import from each other on purpose
    (a cross-import between two page builders is how a helper ends up deleted
    out from under its only remaining caller -- site_common.py says the same
    thing about load_latest_changelog_entry), and site_common.py is not the
    place for a rule about two specific pages' data.
    """
    if key not in bundle:
        raise SystemExit(
            f"ERROR: data/i18n/{lang}.json has no {key!r} block at all.\n"
            f"  {what} is hand-authored directly in the bundle -- there is no data/{key}.json to "
            f"rebuild it from, so an absent key means the content was DELETED, not that it is "
            f"awaiting translation.\n"
            f"  Refusing to publish a placeholder page over it. Restore the block "
            f"(git show HEAD:data/i18n/{lang}.json) before re-running.")
    sections = bundle[key]
    if not isinstance(sections, list):
        raise SystemExit(
            f"ERROR: data/i18n/{lang}.json's {key!r} is {type(sections).__name__}, expected a list "
            f"of {{id, title, body_html}}.")
    if not sections:
        if lang == AUTHORING_LANG:
            raise SystemExit(
                f"ERROR: data/i18n/{lang}.json's {key!r} is empty, and {lang} is the language "
                f"{what} is AUTHORED in -- there is nothing for the other twelve to be translated "
                f"from. An empty authoring bundle is content loss, not a translation gap.")
        n = len(load_bundle(AUTHORING_LANG).get(key) or [])
        print(f"  NOTE [{lang}] no translation of {what} yet -- publishing the placeholder "
              f"page ({AUTHORING_LANG} has {n} section(s)).")
    return sections


def section_html(sec, img_root):
    body = sec["body_html"].replace("{img_root}", img_root)
    return f"""<div class="card" style="margin-bottom:20px;">
      <h2 style="margin-top:0;border-top:none;padding-top:0;">{esc(sec['title'])}</h2>
      {body}
    </div>"""


def build_lang(lang):
    bundle = load_bundle(lang)
    ui = bundle["ui"]
    gates = require_sections(bundle, lang, "gates", "the gate list")
    img_root = asset_root_prefix(1, lang)

    if not gates:
        body = f"""
<div class="hero">
  <span class="hero__eyebrow">{esc(ui['page_titles']['gates'])}</span>
  <h1>{esc(ui['page_titles']['gates'])}</h1>
  <p class="callout callout--info">Coming soon.</p>
</div>"""
    else:
        toc_items = "".join(f'<li><a href="#{esc(g["id"])}">{esc(g["title"])}</a></li>' for g in gates)
        gates_html = "\n".join(
            f'<div id="{esc(g["id"])}">{section_html(g, img_root)}</div>' for g in gates
        )
        body = f"""
<div class="hero">
  <span class="hero__eyebrow">{esc(ui['page_titles']['gates'])}</span>
  <h1>{esc(ui['page_titles']['gates'])}</h1>
  <p class="lede">{esc(ui['common']['gates_intro'])}</p>
</div>
<div class="toc"><div class="toc__title">{esc(ui['common']['toc_label'])}</div><ol>{toc_items}</ol></div>
{gates_html}
"""
    html = page(
        lang=lang,
        section="gates/",
        title=ui["page_titles"]["gates"],
        description=ui["page_descriptions"]["gates"],
        active="gates",
        body=body,
        depth=1,
    )
    write_page(lang, "gates/", html)


def build():
    for lang in available_langs():
        build_lang(lang)


if __name__ == "__main__":
    build()
