#!/usr/bin/env python3
"""Builds features/index.html for every language that has a bundle, from
bundle["features"] (a list of {id, title, body_html} written directly into
data/i18n/<lang>.json, same pattern as build_gates.py).

Covers the player-facing V2.2 feature tour: glass lanterns, Backrooms,
overworld raids, turrets, video, the Sparxie staff, the firearm rebalance,
the drone + drone app, and the Sapporo reconstruction. body_html may contain
the placeholder "{img_root}", replaced here with the correct depth-relative
asset prefix for this language.

⚠ An ABSENT `features` key stops the build. It used to render the literal
  string "Coming soon." and exit 0.

  That was the back half of a two-part trap. scripts/extract_bundle.py --
  which its own docstring tells you to run after any JA source change --
  rebuilt data/i18n/ja.json from six source files and wrote the result over
  the bundle, deleting the four blocks that are hand-authored in the bundle
  itself. One of them is this one, and it holds the undocumented-mechanics
  disclosure published in commit 3eee807. So: follow the documented
  workflow, lose the disclosure, build succeeds, site publishes "Coming
  soon." where a page of safety-relevant mechanics used to be. Nothing went
  red anywhere.

  extract_bundle.py no longer does that. This is the second lock: absent
  key = stop; empty list in the AUTHORING language (ja) = stop; empty list
  in a translated language = the ordinary "not translated yet" state, which
  11 of 13 languages are genuinely in, but it is now PRINTED rather than
  silently rendered.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from site_common import esc, page, write_page, load_bundle, available_langs, asset_root_prefix  # noqa: E402

# The language this content is authored in. Empty here means it was lost, not
# that it is awaiting translation.
AUTHORING_LANG = "ja"


def require_sections(bundle, lang, key, what):
    """The bundle's `key` list, or a stopped build. See the ⚠ block above."""
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
    features = require_sections(bundle, lang, "features", "the feature tour")
    img_root = asset_root_prefix(1, lang)

    if not features:
        body = f"""
<div class="hero">
  <span class="hero__eyebrow">{esc(ui['page_titles']['features'])}</span>
  <h1>{esc(ui['page_titles']['features'])}</h1>
  <p class="callout callout--info">Coming soon.</p>
</div>"""
    else:
        toc_items = "".join(f'<li><a href="#{esc(f["id"])}">{esc(f["title"])}</a></li>' for f in features)
        features_html = "\n".join(
            f'<div id="{esc(f["id"])}">{section_html(f, img_root)}</div>' for f in features
        )
        body = f"""
<div class="hero">
  <span class="hero__eyebrow">{esc(ui['page_titles']['features'])}</span>
  <h1>{esc(ui['page_titles']['features'])}</h1>
  <p class="lede">{esc(ui['common']['features_intro'])}</p>
</div>
<div class="toc"><div class="toc__title">{esc(ui['common']['toc_label'])}</div><ol>{toc_items}</ol></div>
{features_html}
"""
    html = page(
        lang=lang,
        section="features/",
        title=ui["page_titles"]["features"],
        description=ui["page_descriptions"]["features"],
        active="features",
        body=body,
        depth=1,
    )
    write_page(lang, "features/", html)


def build():
    for lang in available_langs():
        build_lang(lang)


if __name__ == "__main__":
    build()
