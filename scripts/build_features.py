#!/usr/bin/env python3
"""Builds features/index.html for every language that has a bundle, from
bundle["features"] (a list of {id, title, body_html} written directly into
data/i18n/<lang>.json, same pattern as build_gates.py).

Covers the player-facing V2.2 feature tour: glass lanterns, Backrooms,
overworld raids, turrets, video, the Sparxie staff, the firearm rebalance,
the drone + drone app, and the Sapporo reconstruction. body_html may contain
the placeholder "{img_root}", replaced here with the correct depth-relative
asset prefix for this language.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from site_common import esc, page, write_page, load_bundle, available_langs, asset_root_prefix  # noqa: E402


def section_html(sec, img_root):
    body = sec["body_html"].replace("{img_root}", img_root)
    return f"""<div class="card" style="margin-bottom:20px;">
      <h2 style="margin-top:0;border-top:none;padding-top:0;">{esc(sec['title'])}</h2>
      {body}
    </div>"""


def build_lang(lang):
    bundle = load_bundle(lang)
    ui = bundle["ui"]
    features = bundle.get("features", [])
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
