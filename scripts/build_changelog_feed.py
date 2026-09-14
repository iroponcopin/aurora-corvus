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
from build_changelog import (  # noqa: E402
    merged_entries, group_entries, DEFAULT_BRAND, NOTE_BRANDS, brand_order, brand_name,
    load_brand_structural, merged_brand_entries, group_brand_entries, brand_empty_line,
)

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


# ---------------------------------------------------------------------------
# BRANDS (2026-09-14, owner): 「更新履歴をOUKA、Cherry、Alpha、Aureumを選べる様にしてください。」
#   Corvus learns the brand line from changelog_feed/brands.json and fetches each
#   brand's feed from the path written there. Alpha's feed stays EXACTLY where and
#   what it was (changelog_feed/<lang>.json): every installed launcher reads that
#   path, and a Corvus that predates brands must keep seeing Alpha's history and
#   nothing else. The other brands get their own directories beside it, in the
#   same shape plus "brand", and -- for a brand with no releases (OUKA) -- a
#   "message" that is the brand page's own line instead of an empty history.
# ---------------------------------------------------------------------------
BRANDS_INDEX = OUT_DIR / "brands.json"


def brand_feed_for(lang, brand, structural):
    bundle = load_bundle(lang)
    c = bundle["ui"]["common"]
    entries_desc = list(reversed(merged_brand_entries(bundle, lang, brand, structural[brand])))
    groups = []
    for label, entries in group_brand_entries(entries_desc):
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
        groups.append({"label": label, "summary": entries[0].get("title", ""), "releases": releases})
    newest = entries_desc[0]["date"] if entries_desc else ""
    payload = {
        "lang": lang,
        "brand": brand,
        "updated": newest,
        "title": bundle["ui"]["page_titles"]["changelog"],
        "updated_label": c["changelog_updated"].replace("{date}", newest) if newest else "",
        "note": c["changelog_note"] if brand in NOTE_BRANDS else "",
        "groups": groups,
    }
    if not entries_desc:
        payload["message"] = brand_empty_line(lang, brand)
    return payload


def brands_index():
    return {
        "schema": 1,
        "default": DEFAULT_BRAND,
        "brands": [{
            "id": b,
            "name": brand_name(b),
            "feed": "changelog_feed/{lang}.json" if b == DEFAULT_BRAND else f"changelog_feed/{b}/{{lang}}.json",
        } for b in brand_order()],
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

    structural = load_brand_structural()
    for brand in brand_order():
        if brand == DEFAULT_BRAND:
            continue
        brand_dir = OUT_DIR / brand
        brand_dir.mkdir(parents=True, exist_ok=True)
        for lang in available_langs():
            path = brand_dir / f"{lang}.json"
            payload = brand_feed_for(lang, brand, structural)
            if not payload["groups"] and not payload.get("message"):
                raise SystemExit(f"ERROR: {brand}/{lang}: no releases and no message -- Corvus would show an error "
                                 f"where the brand should show its own line")
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
            total = sum(len(g["releases"]) for g in payload["groups"])
            print(f"wrote {path.relative_to(ROOT)} ({total} releases{', message' if payload.get('message') else ''}, "
                  f"{path.stat().st_size:,} bytes)")
    BRANDS_INDEX.write_text(json.dumps(brands_index(), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {BRANDS_INDEX.relative_to(ROOT)} ({', '.join(brand_order())})")


if __name__ == "__main__":
    build()
