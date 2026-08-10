#!/usr/bin/env python3
"""Builds roadmap/index.html for every language that has a bundle."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from site_common import esc, page, write_page, load_bundle, available_langs  # noqa: E402


def render_plan(ui, p):
    blocks = ""
    for g in p["groups"]:
        lis = "".join(f"<li>{esc(b)}</li>" for b in g["bullets"])
        blocks += f"<h4>{esc(g['subtitle'])}</h4><ul>{lis}</ul>"
    return f"""<div class="card" style="margin-bottom:20px;">
      <div class="badge-row"><span class="type-badge type-visual">{esc(ui['common']['planned_badge'])}</span>
        <span class="timeline-entry__release">{esc(p['release'])}</span></div>
      <h3 style="margin-top:0">{esc(p['title'])}</h3>
      {blocks}
    </div>"""


def build_lang(lang):
    bundle = load_bundle(lang)
    ui = bundle["ui"]
    plans = bundle.get("roadmap", [])
    plans_html = "\n".join(render_plan(ui, p) for p in plans)

    body = f"""
<div class="hero">
  <span class="hero__eyebrow">{esc(ui['page_titles']['roadmap'])}</span>
  <h1>{esc(ui['page_titles']['roadmap'])}</h1>
  <p class="lede">{esc(ui['common']['roadmap_intro'])}</p>
  <p class="callout callout--warn">{esc(ui['common']['roadmap_warning'])}</p>
</div>
{plans_html}
"""
    html = page(
        lang=lang,
        section="roadmap/",
        title=ui["page_titles"]["roadmap"],
        description=ui["page_descriptions"]["roadmap"],
        active="roadmap",
        body=body,
        depth=1,
    )
    write_page(lang, "roadmap/", html)


def build():
    for lang in available_langs():
        build_lang(lang)


if __name__ == "__main__":
    build()
