#!/usr/bin/env python3
"""Builds changelog/index.html for every language that has a bundle.
Structural fields (release, date, type, mod_versions) come from
data/changelog.json (never translated); prose fields (title, summary,
highlights, ...) come from the language's bundle, matched by (release, date).
"""
import re
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


# ---------------------------------------------------------------------------
# V3.2: the page is presented the way the owner asked for -- like
# https://tryalcove.com/changelog . Releases are grouped by MINOR version, each
# group carries one summary line, and the individual releases collapse to a
# version + date row that opens on click.
#
# WHY GROUPING IS AN IMPROVEMENT AND NOT JUST A RESKIN
#   This page carries 61 entries. Rendered flat and always-expanded (what it did
#   before) the newest release sits above roughly nine screens of history, so
#   "what changed?" -- the only question anyone opens a changelog to answer --
#   was the hardest thing on the page. Collapsed rows put every version of the
#   pack on one screen.
#
# NOTHING IS LOST. Every field that used to render always-open (summary,
# highlights, balance changes, warnings, limitations) still renders; it moved
# inside the row's detail panel. The reference does exactly this too: its rows
# open onto "Features (2) / Fixes (20)" lists.
# ---------------------------------------------------------------------------

# How many releases a series shows before "Show more".
#
# The reference's own cut is not a fixed ten -- its 1.6 series renders sixteen
# rows and still offers the control -- so copying "10" literally would have left
# a button that never appears on THIS data: the biggest series here are 10, 10
# and 9. A control that can never fire is dead code that rots unnoticed, so the
# cut is 8, where it actually does the job it exists for on the three long
# series and keeps every version of the pack within about two screens.
COLLAPSE_AFTER = 8


def minor_key(release):
    """"V2.4.9" / "v1.8.0" -> "V2.4". None when the label carries no version
    (the "Disclosure" entry), which the caller folds into the group it sits in
    by date rather than stranding in a group of one."""
    m = re.match(r"^[Vv]?(\d+)\.(\d+)", str(release))
    return f"V{m.group(1)}.{m.group(2)}" if m else None


def group_entries(entries_desc):
    """[(group_label, [entry, ...]), ...] newest group first.

    `entries_desc` must already be newest-first.

    An entry whose label carries no version (the "Disclosure" entry) joins the
    NEXT group encountered -- i.e. the nearest OLDER series. That is the series
    it is about: Disclosure (2026-08-28) documents what was already running in
    V2.5.1, so it belongs under V2.5. Attaching it to the nearest *newer* group
    instead would have filed it under V3.0, a release it predates and says
    nothing about, which is what the first cut of this function did.
    """
    groups, order, pending = {}, [], []
    for e in entries_desc:
        key = minor_key(e["release"])
        if key is None:
            pending.append(e)
            continue
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(e)
        if pending:
            groups[key].extend(pending)
            pending = []
    # Anything still pending is older than every versioned entry; give it the
    # last group rather than dropping it on the floor.
    if pending:
        if order:
            groups[order[-1]].extend(pending)
        else:
            groups["-"] = pending
            order.append("-")
    return [(k, groups[k]) for k in order]


def detail_html(bundle, e):
    c = bundle["ui"]["common"]

    def section(label, items, extra=""):
        if not items:
            return ""
        lis = "".join(f"<li>{esc(x)}</li>" for x in items)
        return (f'<div class="cl__section">'
                f'<h4 class="cl__sectionTitle">{esc(label)} <span>({len(items)})</span></h4>'
                f'<ul class="cl__list{extra}">{lis}</ul></div>')

    # The release's own title. Rendering only the group summary (the newest
    # title in each series) would have quietly dropped 45 of the 61 translated
    # titles -- the first cut of this page did exactly that, and check_defects'
    # 5.2B gate is what caught it.
    return (
        (f'<p class="cl__entryTitle">{esc(e["title"])}</p>' if e.get("title") else "")
        + (f'<p class="cl__lede">{esc(e["summary"])}</p>' if e.get("summary") else "")
        + section(c["changelog_highlights_label"], e.get("highlights"))
        + section(c["changelog_balance_label"], e.get("balance_changes"))
        + section(c["changelog_warnings_label"], e.get("warnings"), " cl__list--warn")
        + section(c["changelog_limitations_label"], e.get("known_limitations"))
    )


def release_html(bundle, e, index):
    mod_keys = " ".join(
        MODS_BY_ID[mid]["key"] for mid in e.get("mod_versions", {}) if mid in MODS_BY_ID
    )
    panel_id = "cl-" + re.sub(r"[^A-Za-z0-9]+", "-", f'{e["id"]}').strip("-").lower()
    # Rows past COLLAPSE_AFTER start hidden; the group's "Show more" reveals them.
    hidden = " hidden" if index >= COLLAPSE_AFTER else ""
    chev = ('<svg class="cl__chev" viewBox="0 0 16 16" aria-hidden="true" fill="none" '
            'stroke="currentColor" stroke-width="1.75" stroke-linecap="round" '
            'stroke-linejoin="round"><path d="M6 3.5 10.5 8 6 12.5"/></svg>')
    return f"""<div class="cl__release" data-type="{esc(e['type'])}" data-mods="{esc(mod_keys)}" data-version="{esc(e['release'])}"{hidden}>
        <button class="cl__row" type="button" aria-expanded="false" aria-controls="{panel_id}">
          <h3 class="cl__version">{esc(e['release'])}</h3>
          <span class="cl__right"><span class="cl__date">{esc(e['date'])}</span>{chev}</span>
        </button>
        <div class="cl__detail" id="{panel_id}" hidden>{detail_html(bundle, e)}</div>
      </div>"""


def group_html(bundle, label, entries, gi):
    c = bundle["ui"]["common"]
    # The group's one-line summary is the NEWEST release's own title in that
    # series. The reference hand-writes a sentence per series; taking the title
    # keeps the same shape without inventing prose -- and it is already
    # translated into all thirteen languages, so no language falls back.
    summary = entries[0].get("title", "")
    rows = "\n".join(release_html(bundle, e, i) for i, e in enumerate(entries))
    more = ""
    if len(entries) > COLLAPSE_AFTER:
        more = (f'<button class="cl__more" type="button" data-more="{esc(c["changelog_show_more"])}"'
                f' data-less="{esc(c["changelog_show_fewer"])}" aria-expanded="false">'
                f'{esc(c["changelog_show_more"])}</button>')
    return f"""<section class="cl__group" id="v{esc(label.lstrip('Vv'))}">
      <h2 class="cl__groupTitle">{esc(label)}</h2>
      <p class="cl__groupSummary">{esc(summary)}</p>
      <div class="cl__releases">
{rows}
      </div>
      {more}
    </section>"""


def build_lang(lang):
    bundle = load_bundle(lang)
    ui = bundle["ui"]
    c = ui["common"]
    entries = merged_entries(bundle, lang)
    entries_desc = list(reversed(entries))
    groups = group_entries(entries_desc)

    from site_common import MOD_ORDER
    mod_chips = "".join(
        f'<button class="cl__chip" type="button" data-filter-mod="{esc(m["key"])}" aria-pressed="false">'
        f'{esc(ui["mods"].get(m["key"], {}).get("name", m["key"]))}</button>'
        for m in MOD_ORDER
    )
    type_chips = "".join(
        f'<button class="cl__chip" type="button" data-filter-type="{t}" aria-pressed="false">'
        f'{esc(ui["type_badge"].get(t, t))}</button>'
        for t in ("release", "hotfix", "visual-update", "disclosure")
    )

    updated = c["changelog_updated"].replace("{date}", entries_desc[0]["date"]) if entries_desc else ""
    doc_icon = ('<svg viewBox="0 0 16 16" aria-hidden="true" fill="none" stroke="currentColor" '
                'stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round">'
                '<path d="M9.5 1.5H4a1 1 0 0 0-1 1v11a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V5z"/>'
                '<path d="M9.5 1.5V5H13"/></svg>')

    body = f"""
<div class="cl">
  <header class="cl__head">
    <h1 class="cl__title">{esc(ui['page_titles']['changelog'])}</h1>
    <p class="cl__updated">{doc_icon}<span>{esc(updated)}</span></p>
    <p class="cl__note">{esc(c['changelog_note'])}</p>
  </header>

  <div class="cl__tools" role="group">
    <input type="search" id="changelogSearch" class="cl__search"
           placeholder="{esc(c['search_placeholder_changelog'])}"
           aria-label="{esc(c['search_placeholder_changelog'])}">
    <label>{esc(c['filter_mod_label'])}</label>{mod_chips}
    <label>{esc(c['filter_type_label'])}</label>{type_chips}
  </div>

  <p id="changelogEmpty" class="cl__empty" hidden>{esc(c['empty_changelog'])}</p>

  <div id="changelogGroups" data-cut="{COLLAPSE_AFTER}">
{"".join(group_html(bundle, label, es, i) for i, (label, es) in enumerate(groups))}
  </div>
</div>
"""
    prefix = asset_root_prefix(1, lang)
    html = page(
        lang=lang,
        section="changelog/",
        title=ui["page_titles"]["changelog"],
        description=ui["page_descriptions"]["changelog"],
        active="changelog",
        body=body,
        depth=1,
        extra_head=(f'<link rel="stylesheet" href="{prefix}assets/css/changelog.css">\n'
                    f'<script defer src="{prefix}assets/js/changelog.js"></script>\n'),
    )
    write_page(lang, "changelog/", html)


def build():
    for lang in available_langs():
        build_lang(lang)


if __name__ == "__main__":
    build()
