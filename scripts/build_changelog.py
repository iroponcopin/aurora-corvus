#!/usr/bin/env python3
"""Builds changelog/index.html for every language that has a bundle.
Structural fields (release, date, type, mod_versions) come from
data/changelog.json (never translated); prose fields (title, summary,
highlights, ...) come from the language's bundle, matched by (release, date).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from site_common import (  # noqa: E402
    ROOT, MODS_BY_ID, esc, page, write_page, mod_badge, type_badge,
    load_bundle, available_langs,
)


def merged_entries(bundle):
    structural = json.loads((ROOT / "data" / "changelog.json").read_text(encoding="utf-8"))
    translated = {(t["release"], t["date"]): t for t in bundle.get("changelog", [])}
    out = []
    for s in structural:
        t = translated.get((s["release"], s["date"]), s)
        merged = dict(s)
        for k in ("title", "summary", "highlights", "balance_changes", "warnings", "known_limitations"):
            if k in t:
                merged[k] = t[k]
        out.append(merged)
    return out


def entry_html(bundle, e):
    mods_html = "".join(mod_badge(bundle, mid) for mid in sorted(e.get("mod_versions", {})))
    mod_keys = " ".join(
        MODS_BY_ID[mid]["key"] for mid in e.get("mod_versions", {}) if mid in MODS_BY_ID
    )

    def ul(items):
        if not items:
            return ""
        return "<ul>" + "".join(f"<li>{esc(x)}</li>" for x in items) + "</ul>"

    ui = bundle["ui"]
    c = ui["common"]
    warn_block = ""
    if e.get("warnings"):
        warn_block = f"""<div class="callout callout--warn">
          <div class="callout__title">⚠ {esc(c['changelog_warnings_label'])}</div>
          {ul(e['warnings'])}
        </div>"""

    balance_block = (
        f"<h4>{esc(c['changelog_balance_label'])}</h4>{ul(e['balance_changes'])}"
        if e.get("balance_changes") else ""
    )
    limit_block = (
        f"<h4>{esc(c['changelog_limitations_label'])}</h4>{ul(e['known_limitations'])}"
        if e.get("known_limitations") else ""
    )

    return f"""<article class="timeline-entry" data-type="{esc(e['type'])}" data-mods="{esc(mod_keys)}">
      <div class="timeline-entry__date">{esc(e['date'])}</div>
      <h3 class="timeline-entry__title">
        <span class="timeline-entry__release">{esc(e['release'])}</span> — {esc(e['title'])}
      </h3>
      <div class="badge-row">{type_badge(bundle, e['type'])}{mods_html}</div>
      <p>{esc(e['summary'])}</p>
      {ul(e.get('highlights'))}
      {balance_block}
      {warn_block}
      {limit_block}
    </article>"""


def build_lang(lang):
    bundle = load_bundle(lang)
    ui = bundle["ui"]
    entries = merged_entries(bundle)
    entries_desc = list(reversed(entries))

    from site_common import MOD_ORDER
    mod_chips = "".join(
        f'<button class="chip" type="button" data-filter-mod="{esc(m["key"])}" aria-pressed="false">'
        f'{esc(ui["mods"].get(m["key"], {}).get("name", m["key"]))}</button>'
        for m in MOD_ORDER
    )
    type_chips = "".join(
        f'<button class="chip" type="button" data-filter-type="{t}" aria-pressed="false">{esc(ui["type_badge"][t])}</button>'
        for t in ("release", "hotfix", "visual-update")
    )

    items_html = "\n".join(entry_html(bundle, e) for e in entries_desc)
    c = ui["common"]

    intro = c["changelog_intro"].replace("{count}", str(len(entries)))
    body = f"""
<div class="hero">
  <span class="hero__eyebrow">{esc(ui['page_titles']['changelog'])}</span>
  <h1>{esc(ui['page_titles']['changelog'])}</h1>
  <p class="lede">{esc(intro)}</p>
  <p class="callout callout--info">{esc(c['changelog_note'])}</p>
</div>

<div class="filter-bar" role="group">
  <input type="search" id="changelogSearch" placeholder="{esc(c['search_placeholder_changelog'])}" aria-label="{esc(c['search_placeholder_changelog'])}">
</div>
<div class="filter-bar" role="group" style="top:auto;position:static;padding-top:0;">
  <span class="card__meta" style="align-self:center;">{esc(c['filter_mod_label'])}</span>
  {mod_chips}
</div>
<div class="filter-bar" role="group" style="top:auto;position:static;padding-top:0;">
  <span class="card__meta" style="align-self:center;">{esc(c['filter_type_label'])}</span>
  {type_chips}
</div>

<p id="changelogEmpty" class="empty-state" hidden>{esc(c['empty_changelog'])}</p>
<div class="timeline" id="changelogTimeline">
{items_html}
</div>
"""
    html = page(
        lang=lang,
        section="changelog/",
        title=ui["page_titles"]["changelog"],
        description=ui["page_descriptions"]["changelog"],
        active="changelog",
        body=body,
        depth=1,
        extra_head='<script defer src="../assets/js/changelog.js"></script>\n',
    )
    write_page(lang, "changelog/", html)


def build():
    for lang in available_langs():
        build_lang(lang)


if __name__ == "__main__":
    build()
