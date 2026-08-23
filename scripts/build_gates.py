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
    gates = bundle.get("gates", [])
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
