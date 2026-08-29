#!/usr/bin/env python3
"""Builds known-issues/index.html for every language that has a bundle.

⚠ A bundle with no `known_issues` content stops the build. The three lists
  were each read with `.get(key, [])`, so losing the block published three
  headings with their explanatory ledes and nothing underneath them -- which
  reads as "there are no known issues", the opposite of the truth, at exit 0.
  Individual sections ARE allowed to be empty (ja and en legitimately list no
  minor bugs right now); all three empty at once is not.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from site_common import esc, page, write_page, load_bundle, available_langs  # noqa: E402


def item_block(item, show_since=False):
    tag = f' <span class="card__meta">({esc(item["since"])})</span>' if show_since and item.get("since") else ""
    return f"<h4>{esc(item['title'])}{tag}</h4><p>{esc(item['body'])}</p>"


def build_lang(lang):
    bundle = load_bundle(lang)
    ui = bundle["ui"]
    c = ui["common"]
    ki = bundle.get("known_issues") or {}
    if not any(ki.get(s) for s in ("minor_bugs", "standing_limitations", "recent_unconfirmed")):
        raise SystemExit(
            f"ERROR: data/i18n/{lang}.json's 'known_issues' block is absent or has no items in "
            f"any of its three sections. Publishing anyway would put out a page whose three "
            f"headings each say 'here is what is broken' followed by nothing -- indistinguishable "
            f"from 'nothing is broken'. The block is folded in from data/known-issues.ja.json by "
            f"scripts/extract_bundle.py; check that file, then re-run it before building.")

    minor_html = "".join(item_block(i, show_since=True) for i in ki.get("minor_bugs", []))
    standing_html = "".join(item_block(i) for i in ki.get("standing_limitations", []))
    unconfirmed_html = "".join(
        f"<li><strong>{esc(i['title'])}:</strong> {esc(i['body'])}</li>"
        for i in ki.get("recent_unconfirmed", [])
    )

    body = f"""
<div class="hero">
  <span class="hero__eyebrow">{esc(ui['page_titles']['issues'])}</span>
  <h1>{esc(ui['page_titles']['issues'])}</h1>
  <p class="lede">{esc(c['issues_intro'])}</p>
</div>

<h2>{esc(c['issues_minor_heading'])}</h2>
<p class="section-lede">{esc(c['issues_minor_lede'])}</p>
{minor_html}

<h2>{esc(c['issues_standing_heading'])}</h2>
<p class="section-lede">{esc(c['issues_standing_lede'])}</p>
{standing_html}

<h2>{esc(c['issues_unconfirmed_heading'])}</h2>
<p class="callout callout--info">{esc(c['issues_unconfirmed_note'])}</p>
<ul>{unconfirmed_html}</ul>
"""
    html = page(
        lang=lang,
        section="known-issues/",
        title=ui["page_titles"]["issues"],
        description=ui["page_descriptions"]["issues"],
        active="issues",
        body=body,
        depth=1,
    )
    write_page(lang, "known-issues/", html)


def build():
    for lang in available_langs():
        build_lang(lang)


if __name__ == "__main__":
    build()
