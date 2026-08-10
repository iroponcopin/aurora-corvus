#!/usr/bin/env python3
"""Builds guide/index.html for every language that has a bundle, from
bundle["install_guide"] (a list of {id, audience, title, body_html} written
by the guide-adaptation agent into data/guide.json, then folded into every
language's bundle by scripts/extract_bundle.py / the translation agents)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from site_common import esc, page, write_page, load_bundle, available_langs  # noqa: E402

AUDIENCE_KEY = {"player": "audience_player", "admin": "audience_admin", "all": "audience_all"}


def section_html(ui, sec):
    label_key = AUDIENCE_KEY.get(sec.get("audience", "all"), "audience_all")
    badge = "" if sec.get("audience") == "all" else (
        f'<span class="type-badge type-visual">{esc(ui["common"][label_key])}</span>'
    )
    return f"""<div class="card" style="margin-bottom:20px;">
      {f'<div class="badge-row">{badge}</div>' if badge else ""}
      <h2 style="margin-top:0;border-top:none;padding-top:0;">{esc(sec['title'])}</h2>
      {sec['body_html']}
    </div>"""


def build_lang(lang):
    bundle = load_bundle(lang)
    ui = bundle["ui"]
    sections = bundle.get("install_guide", [])

    if not sections:
        body = f"""
<div class="hero">
  <span class="hero__eyebrow">{esc(ui['page_titles']['guide'])}</span>
  <h1>{esc(ui['page_titles']['guide'])}</h1>
  <p class="callout callout--info">準備中です。</p>
</div>"""
    else:
        toc_items = "".join(f'<li><a href="#{esc(s["id"])}">{esc(s["title"])}</a></li>' for s in sections)
        sections_html = "\n".join(
            f'<div id="{esc(s["id"])}">{section_html(ui, s)}</div>' for s in sections
        )
        body = f"""
<div class="hero">
  <span class="hero__eyebrow">{esc(ui['page_titles']['guide'])}</span>
  <h1>{esc(ui['page_titles']['guide'])}</h1>
  <p class="lede">{esc(ui['common']['guide_intro'])}</p>
</div>
<div class="toc"><div class="toc__title">{esc(ui['common']['toc_label'])}</div><ol>{toc_items}</ol></div>
{sections_html}
"""
    html = page(
        lang=lang,
        section="guide/",
        title=ui["page_titles"]["guide"],
        description=ui["page_descriptions"]["guide"],
        active="guide",
        body=body,
        depth=1,
    )
    write_page(lang, "guide/", html)


def build():
    for lang in available_langs():
        build_lang(lang)


if __name__ == "__main__":
    build()
