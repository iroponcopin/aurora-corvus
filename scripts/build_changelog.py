#!/usr/bin/env python3
"""Builds changelog/index.html for every language that has a bundle.
Structural fields (release, date, type, mod_versions) come from
data/changelog.json (never translated); prose fields (title, summary,
highlights, ...) come from the language's bundle, matched by (release, date).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from site_common import (  # noqa: E402
    MODS_BY_ID, esc, page, write_page, mod_badge, type_badge,
    load_bundle, available_langs, asset_root_prefix,
    load_changelog_structural, index_bundle_changelog,
)

PROSE_KEYS = ("title", "summary", "highlights", "balance_changes", "warnings",
              "known_limitations")


def merged_entries(bundle, lang=None):
    """Structural fields from data/changelog.json, prose from the bundle,
    matched on the entry's `id`.

    ⚠ (release, date) is NOT a unique key in data/changelog.json and is not
      used as one any more. Two pairs share one:
          v1.3.2 / 2026-07-22   "乗り物大型化…"  and  "建材ブロック138種追加…"
          v1.8.0 / 2026-08-04   "「Glimpse Alpha」への名称変更"  and
                                "設定ファイルの自動修復(v1.8.0 再配布版)"
      This function used to build `{(release, date): t}` as a dict
      comprehension, so for those two pairs the SECOND translation silently
      won and was rendered against BOTH structural entries. On every one of
      the 13 published pages that meant v1.8.0's rename announcement — the
      entry that explains why the jar filenames changed — was replaced by a
      second copy of the config-auto-repair text, wearing the rename's
      "release" badge. Nothing went red: the count was right, the badges were
      right, the dates were right, and both entries were fluent prose in the
      reader's own language.

      Consuming duplicates in order fixed the symptom but left the data
      ambiguous, so the identity now lives in the data: every entry carries an
      explicit `id`, validated unique by site_common.load_changelog_structural().
      A structural entry whose id has no translation falls back to the
      Japanese source — visible on the page — rather than borrowing a
      neighbour's prose, which is not.

      Both readers of data/changelog.json go through the same two helpers in
      site_common.py, so there is exactly one place where identity is decided.
    """
    structural = load_changelog_structural()
    by_id = index_bundle_changelog(bundle, lang)
    stale = sorted(set(by_id) - {s["id"] for s in structural})
    if stale and lang not in (None, "ja"):
        print(f"  NOTE [{lang}] {len(stale)} translated changelog entr(ies) the structural "
              f"file no longer has, dropped: {', '.join(stale[:6])}")

    out, untranslated = [], []
    for s in structural:
        t = by_id.get(s["id"])
        if t is None:
            t = s
            untranslated.append(f"{s['release']}({s['date']}) [{s['id']}]")
        merged = dict(s)
        for k in PROSE_KEYS:
            if k in t:
                merged[k] = t[k]
        out.append(merged)

    # Not fatal -- falling back to Japanese is the deliberate design (see the
    # type_badge .get(t, t) comment below). But it must not be SILENT: 11
    # bundles sat 14 entries behind for days while this build printed nothing
    # and exited 0, so English and eleven other languages served Japanese
    # prose for every release after V2.1.0.
    if untranslated and lang not in (None, "ja"):
        print(f"  WARNING: {lang}: {len(untranslated)}/{len(structural)} changelog "
              f"entries have no translation and will render in Japanese: "
              + ", ".join(untranslated))
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
    entries = merged_entries(bundle, lang)
    entries_desc = list(reversed(entries))

    from site_common import MOD_ORDER
    mod_chips = "".join(
        f'<button class="chip" type="button" data-filter-mod="{esc(m["key"])}" aria-pressed="false">'
        f'{esc(ui["mods"].get(m["key"], {}).get("name", m["key"]))}</button>'
        for m in MOD_ORDER
    )
    # .get(t, t) (not [t]): "disclosure" was added for the "previously
    # undocumented mechanics" entry (ja/en only, so far). A language bundle
    # that hasn't translated ui.type_badge["disclosure"] yet falls back to
    # the raw key instead of a KeyError -- same convention as type_badge()
    # itself and as NAV_LABEL_FALLBACK elsewhere in site_common.py.
    type_chips = "".join(
        f'<button class="chip" type="button" data-filter-type="{t}" aria-pressed="false">{esc(ui["type_badge"].get(t, t))}</button>'
        for t in ("release", "hotfix", "visual-update", "disclosure")
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
        extra_head=f'<script defer src="{asset_root_prefix(1, lang)}assets/js/changelog.js"></script>\n',
    )
    write_page(lang, "changelog/", html)


def build():
    for lang in available_langs():
        build_lang(lang)


if __name__ == "__main__":
    build()
