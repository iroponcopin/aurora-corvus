#!/usr/bin/env python3
"""Writes changelog_feed/<lang>.json — the changelog in a shape Corvus can render.

WHY A FEED RATHER THAN SCRAPING THE PAGE
  The launcher shows the changelog in-app (V3.2, owner's request). It could have
  fetched changelog/index.html and pulled the text out, and that would have
  broken the first time this page's markup changed — which is exactly what
  happened to it this release. A feed is a contract; HTML is not.

WHY ONE FILE PER LANGUAGE
  All thirteen in one file is roughly 1.5 MB, and the launcher only ever needs
  the one the player reads. Per-language keeps each fetch around 100 KB.

WHY THE SHAPE MIRRORS THE PAGE
  Same grouping, same summaries, same section labels, from the same functions in
  build_changelog.py. If the page and the app disagreed about what V2.5 contains,
  one of them would be lying and nobody could tell which — so they are built from
  one source, not two.

THE FILENAME IS A CROSS-REPO CONTRACT
  glimpse-launcher fetches these paths. Renaming this directory silently breaks
  the in-app changelog for every installed launcher, and neither repo's tests can
  see the other — the same class of break as the pack ZIP's filename
  (see site_common.PACK_ZIP_STEM). Grep the launcher before touching it.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from site_common import ROOT, load_bundle, available_langs  # noqa: E402
from build_changelog import merged_entries, group_entries  # noqa: E402

OUT_DIR = ROOT / "changelog_feed"

# Kept identical to the page's own section order, so a reader moving between the
# app and the site never sees the same release described in a different order.
SECTIONS = (
    ("highlights", "changelog_highlights_label"),
    ("balance_changes", "changelog_balance_label"),
    ("warnings", "changelog_warnings_label"),
    ("known_limitations", "changelog_limitations_label"),
)


def feed_for(lang):
    bundle = load_bundle(lang)
    c = bundle["ui"]["common"]
    entries_desc = list(reversed(merged_entries(bundle, lang)))
    groups = []
    for label, entries in group_entries(entries_desc):
        releases = []
        for e in entries:
            sections = []
            for field, label_key in SECTIONS:
                items = [str(x) for x in (e.get(field) or [])]
                if items:
                    sections.append({"title": c[label_key], "items": items})
            releases.append({
                "version": e["release"],
                "date": e["date"],
                "type": e.get("type", "release"),
                "title": e.get("title", ""),
                "summary": e.get("summary", ""),
                "sections": sections,
            })
        groups.append({
            "label": label,
            # Same rule the page uses: the newest release's own title.
            "summary": entries[0].get("title", ""),
            "releases": releases,
        })
    return {
        "lang": lang,
        "updated": entries_desc[0]["date"] if entries_desc else "",
        "title": bundle["ui"]["page_titles"]["changelog"],
        "updated_label": c["changelog_updated"].replace(
            "{date}", entries_desc[0]["date"] if entries_desc else ""),
        "note": c["changelog_note"],
        "groups": groups,
    }


def build():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    written = 0
    for lang in available_langs():
        path = OUT_DIR / f"{lang}.json"
        payload = feed_for(lang)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n",
                        encoding="utf-8")
        total = sum(len(g["releases"]) for g in payload["groups"])
        print(f"wrote {path.relative_to(ROOT)} "
              f"({len(payload['groups'])} groups, {total} releases, {path.stat().st_size:,} bytes)")
        written += 1
    if written == 0:
        raise SystemExit("ERROR: no language bundles found — the feed would be empty, "
                         "and an empty feed is indistinguishable in the app from "
                         "'this pack has no history'.")


if __name__ == "__main__":
    build()
