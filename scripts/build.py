#!/usr/bin/env python3
"""Rebuilds every static page in the site from data/*.json.
Does NOT re-run the data extraction scripts (extract_versions.py,
extract_recipes.py, merge_changelog.py) — those pull from the source mod
pack project and should be re-run explicitly when that project ships an
update. This script only re-renders HTML from whatever is currently in data/.
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUILD_SCRIPTS = [
    # Writes assets/css/lang-flags.css and assets/js/lang.js, which every
    # page's <head> links to. First so a flag/language mismatch stops the
    # build before 143 pages are written against it.
    "build_lang_assets.py",
    "build_recipe_overlays.py",
    "build_home.py",
    "build_download.py",
    # Right after build_download.py: build_aureum.py imports _aureum_facts()
    # from it to discover the published jar (see build_aureum.py's header),
    # and this page's download CTA is a companion to that page's Aureum
    # section, not to anything below.
    "build_aureum.py",
    # TEMPORARY (2026-09-01): the V4 announcement page. Placed right after the
    # home/Aureum pair because it is a marketing page, not a reference one,
    # and it must build before build_sitemap.py so its URLs are listed.
    # Deleted in one line when V4 ships; see scripts/build_v4_teaser.py.
    "build_v4_teaser.py",
    "build_changelog.py",
    "build_recipes.py",
    "build_guide.py",
    "build_launcher.py",
    "build_gates.py",
    "build_features.py",
    "build_roadmap.py",
    "build_known_issues.py",
    "build_changelog_feed.py",
    "build_releases_feed.py",
    "build_glimpse_manifest.py",
    "build_404.py",
    "build_sitemap.py",  # must run last -- walks whatever pages exist on disk
]


def main():
    for name in BUILD_SCRIPTS:
        script = HERE / name
        if not script.exists():
            print(f"skip (not written yet): {name}")
            continue
        print(f"--- {name} ---")
        subprocess.run([sys.executable, str(script)], check=True)


if __name__ == "__main__":
    main()
