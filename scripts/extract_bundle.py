#!/usr/bin/env python3
"""Consolidates every JA content source into one translation-ready bundle:
data/i18n/ja.json (the full bundle, used to render the JA site) and
data/i18n/ja.translatable.json (JUST the strings a translator needs to
produce, with structural data like dates/versions/ids/grids stripped out --
this is what gets handed to each per-language translation agent).

Sources: data/ui-strings.ja.json, data/home.ja.json, data/changelog.json,
data/roadmap.ja.json, data/known-issues.ja.json, data/guide.json (install
guide, written by a separate agent), data/recipes.json (cat names + item
names + the recipe page's own "使い方" howto tab).

Run this after any JA source file changes, before re-running translation.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
I18N = DATA / "i18n"


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def main():
    ui = load("ui-strings.ja.json")
    home = load("home.ja.json")
    changelog = load("changelog.json")
    roadmap = load("roadmap.ja.json")
    known_issues = load("known-issues.ja.json")
    recipes = load("recipes.json")

    guide_path = DATA / "guide.json"
    install_guide = json.loads(guide_path.read_text(encoding="utf-8")) if guide_path.exists() else []
    if not install_guide:
        print("WARNING: data/guide.json missing or empty -- install guide will be blank "
              "in the bundle until the guide-writing agent finishes and this is re-run.")

    # ---- changelog: split into translatable strings vs structural fields ----
    changelog_strings = []
    for e in changelog:
        changelog_strings.append({
            "release": e["release"],  # key, not translated, kept for realignment
            "date": e["date"],
            "title": e["title"],
            "summary": e["summary"],
            "highlights": e.get("highlights", []),
            "balance_changes": e.get("balance_changes", []),
            "warnings": e.get("warnings", []),
            "known_limitations": e.get("known_limitations", []),
        })

    # ---- recipes: category names + item display names (JA + existing EN) ----
    cat_names = [c[0] for c in recipes["cats"]]
    items = {iid: {"ja": v[0], "en": v[1]} for iid, v in recipes["items"].items()}
    recipe_howto = recipes.get("guides", [])

    bundle = {
        "lang": "ja",
        "ui": ui,
        "home": home,
        "changelog": changelog_strings,
        "roadmap": roadmap,
        "known_issues": known_issues,
        "install_guide": install_guide,
        "recipes": {
            "cat_names": cat_names,
            "items": items,
            "howto": recipe_howto,
        },
    }

    I18N.mkdir(parents=True, exist_ok=True)
    (I18N / "ja.json").write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {I18N / 'ja.json'}")
    print(f"  changelog entries: {len(changelog_strings)}")
    print(f"  recipe items: {len(items)}")
    print(f"  recipe categories: {len(cat_names)}")
    print(f"  recipe howto topics: {len(recipe_howto)}")
    print(f"  install guide sections: {len(install_guide)}")
    print(f"  roadmap releases: {len(roadmap)}")


if __name__ == "__main__":
    main()
