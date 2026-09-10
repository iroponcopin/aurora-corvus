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
    # V4.3.8: writes assets/img/cherry/blossom.svg and assets/css/cherry-tokens.css.
    # Must precede build_cherry.py, which inlines that SVG so the five petals can
    # be animated one at a time.
    "gen_cherry_brand.py",
    "build_recipe_overlays.py",
    "build_home.py",
    "build_download.py",
    # Right after build_download.py: build_aureum.py imports _aureum_facts()
    # from it to discover the published jar (see build_aureum.py's header),
    # and this page's download CTA is a companion to that page's Aureum
    # section, not to anything below.
    "build_aureum.py",
    # V4.3.8: Cherry's brand page. It inlines assets/img/cherry/blossom.svg,
    # which gen_cherry_brand.py (first in this list) writes.
    "build_cherry.py",
    # 2026-09-10: Alpha finally gets a brand page of its own, so the Store
    # mega-menu has three real destinations instead of two.
    "build_alpha.py",
    "build_changelog.py",
    "build_recipes.py",
    "build_guide.py",
    "build_launcher.py",
    "build_gates.py",
    "build_features.py",
    "build_roadmap.py",
    # After the roadmap (same family of page) and before the feeds/sitemap,
    # because it writes upcoming.json at the site root for the Discord bot.
    "build_upcoming.py",
    # After build_upcoming.py and before the feeds/sitemap. It imports
    # _discord_invite() from build_download.py so the invite link on this page
    # and on the Download page cannot diverge, and it reads the command export
    # copied from the bot repo (data/discord_commands.json).
    "build_discord.py",
    "build_known_issues.py",
    # V4.3.0: the Sparxie skin behind its PIN. After the download page (it is a
    # companion to it) and before the feeds, which walk whatever pages exist.
    # Without AURORA_SKIN_PIN in the environment this re-publishes the committed
    # blob and REFUSES if the skin has changed since it was sealed.
    "build_skin_gate.py",
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
