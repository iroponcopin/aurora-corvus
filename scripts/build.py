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
    "build_recipe_overlays.py",
    "build_home.py",
    "build_download.py",
    "build_changelog.py",
    "build_recipes.py",
    "build_guide.py",
    "build_gates.py",
    "build_features.py",
    "build_roadmap.py",
    "build_known_issues.py",
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
