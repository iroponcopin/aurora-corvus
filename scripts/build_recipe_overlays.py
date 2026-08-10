#!/usr/bin/env python3
"""Builds data/recipes.<lang>.json for every non-Japanese language bundle:
a small overlay of {cat_names, items, howto} (translated names/text only --
NOT the grid/image/structural data, which lives once in the shared
data/recipes.json and is reused by every language). See assets/js/recipes.js
for how these are merged client-side.

Skips "ja" (the JA page reads data/recipes.json directly, no overlay needed).
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
I18N = ROOT / "data" / "i18n"


def build():
    master = json.loads((ROOT / "data" / "recipes.json").read_text(encoding="utf-8"))
    master_item_ids = set(master["items"].keys())
    written = []
    for bundle_path in sorted(I18N.glob("*.json")):
        lang = bundle_path.stem
        if lang == "ja":
            continue
        bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
        recipes = bundle.get("recipes")
        if not recipes:
            print(f"skip {lang}: bundle has no 'recipes' section")
            continue

        items = recipes.get("items", {})
        missing = master_item_ids - set(items.keys())
        extra = set(items.keys()) - master_item_ids
        if missing:
            print(f"WARNING [{lang}]: {len(missing)} item id(s) from the master are missing "
                  f"in the translation (will fall back to EN/JA name at render time), "
                  f"e.g. {sorted(missing)[:3]}")
        if extra:
            print(f"WARNING [{lang}]: {len(extra)} translated item id(s) don't exist in the "
                  f"master data (ignored), e.g. {sorted(extra)[:3]}")

        cat_names = recipes.get("cat_names", [])
        if len(cat_names) != len(master["cats"]):
            print(f"WARNING [{lang}]: expected {len(master['cats'])} category names, "
                  f"got {len(cat_names)}")

        overlay = {
            "cat_names": cat_names,
            "items": items,
            "howto": recipes.get("howto", []),
        }
        out_path = ROOT / "data" / f"recipes.{lang}.json"
        out_path.write_text(json.dumps(overlay, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        written.append((lang, out_path.stat().st_size))

    for lang, size in written:
        print(f"wrote data/recipes.{lang}.json ({size:,} bytes)")
    if not written:
        print("No non-ja language bundles found yet in data/i18n/ -- nothing to do.")


if __name__ == "__main__":
    build()
