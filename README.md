# Corvus

An unofficial site for the Fabric mods **OUKA**, **Cherry** and **Aureum** and for
the **Corvus** launcher that keeps them up to date: their recipes, update history,
downloads and release notices.

**Alpha**, the mod pack this site was first made for (called *Glimpse Alpha* until
V2.5.0, and *Sorakaze* before that), ended distribution on 2026-09-28 and was removed
from this site. `alpha/` is now a single page saying so, and `downloads/` carries its
last release, `Alpha_MODs_v4.4.0.2+mc26.3.zip` — 13 placeholder jars that switch Alpha
off, which Corvus delivers as an ordinary update. `data/retirement.json` is the one
switch the builders and checkers read for this.

Live site: served via GitHub Pages from this repository.

## What's here

- `index.html`, `download/`, `changelog/`, `recipes/`, `launcher/`, `upcoming/`, `teasers/`,
  `discord/`, `skin/`, `ouka/`, `cherry/`, `cherry-controls/`, `aureum/`, `alpha/` —
  the Japanese (primary) site, generated as static HTML.
- `en/`, `es/`, `fr/`, `zh/`, `ko/`, `pt-br/`, `it/`, `ar/`, `ru/`, `id/`, `de/`, `tr/` —
  the same site in 12 additional languages, one directory per
  [BCP-47-ish](https://en.wikipedia.org/wiki/IETF_language_tag) language code.
- `downloads/` — the release archives the site links to and that Corvus installs
  (`glimpse_manifest.json` is what Corvus reads; every entry carries a sha256 and a size,
  and `scripts/check_published_artefacts.py` compares them with what is actually served).
- `assets/` — shared CSS/JS/images, including the recipe item icons (extracted from the
  published Cherry and OUKA archives), reused by every language.
- `data/` — the underlying JSON data (recipes, changelog, per-language bundles, etc.)
  that the `scripts/build_*.py` generators render into the static HTML above.
- `scripts/` — the static-site generator and its gates. Plain Python, no framework.

> **Since the portal cutover (29 September 2026) the pages of this site are the 3D portal's**, built from this
> repository's data and laid over this tree. Portal 4.0 (October 2026) is built by `web/` in this repository
> (Next.js 15, static export; `cd web && npm run build && npm run apply`); the 3.x exports were built by
> `Minecraft/corvus-web` (`npm run build:portal`). `scripts/build.py` refuses to write the old pages while
> `portal/build.json` exists; the section "Releasing" below is the routine. The section after it describes how the
> pages were generated BEFORE the cutover and is kept for the rollback (`git revert` of the cutover commit restores
> those pages byte for byte).

## Rebuilding the site (before the cutover; kept for the rollback)

The site is pre-rendered static HTML committed to this repo (no build step runs
on GitHub Pages). To regenerate it after editing content:

```bash
# Only when a brand published a new release (these read the archives in downloads/):
python3 scripts/extract_versions.py     # per-mod version numbers of the pack archive
python3 scripts/extract_recipes.py      # recipe data + item icons (Cherry and OUKA)

# Render every page in every available language:
python3 scripts/build.py

# Then the gates:
python3 scripts/check_site.py
python3 scripts/check_release_version_switch.py --baseline scripts/release_history_baseline_26.2.json
```

Each language only renders once its bundle exists at `data/i18n/<lang>.json`.

## Releasing (since the portal cutover)

What the launcher and the Discord bot read are the **contract files** — `glimpse_manifest.json`, `releases.json`,
`upcoming.json`, `changelog_feed/**`, `downloads/**`, `data/**`, `robots.txt`, `.nojekyll` — and the portal never
writes them. A release (a new pack, a new brand version, a new launcher) is:

1. **Edit the data** the release changes (the brand's inputs, all read by the portal too, read-only):
   `build_<brand>.py`'s copy tables (`COPY`, `COPY_FOR`, `CONTROLS_FOR` — the brand page's line and codename; these
   files must stay importable, the portal reads them through `scripts/portal/extract_wiki.py`),
   `data/i18n/<lang>.json` ×13, `data/changelog_brands.json` (a brand's history — never `data/changelog.json`),
   `data/upcoming.json`, `data/recipes*.json` (from `extract_recipes.py`, which keeps running), and the new files in
   `downloads/`.
2. **Rebuild what is read by machines:** `python3 scripts/build.py --feeds` (manifest, releases feed, changelog feeds,
   `upcoming.json`). `build.py` without `--feeds` refuses to run: it would write the old pages over the portal.
   Writing `upcoming.json` also archives the board in `data/teasers.json` (`scripts/build_teaser_archive.py`): a new
   id is stamped `announced`, and the day an entry leaves the board it is stamped `retired` and keeps its last
   wording, which is what the portal's Teasers page plays. `python3 scripts/build_teaser_archive.py --check` says
   whether the archive is behind the board.
3. **The wiki's data gates:** `python3 scripts/check_site.py` (with the portal in place it runs only the data checks:
   `figures`, `recipe-sources` and `changelog-feeds` — the brand-changelog checker's feed half, `check_changelog_brands.py
   --feeds-only` — and says which page checkers it retired) and
   `python3 scripts/check_release_version_switch.py --baseline scripts/release_history_baseline_26.2.json`.
4. **Rebuild the pages:** `cd web && npm ci && npm run build` (it reads this checkout's data, the same files and
   copy tables as before, through `web/scripts/extract_wiki.py`; nothing in it writes outside `web/`), then
   `npm run typecheck && npm run lint && npm run check:export`. The Download, Corvus Store and brand pages print the
   manifest's names, sizes and SHA-256 **at build time**: a release that rebuilds the manifest but not the portal
   leaves pages that describe files that are no longer the ones served.
5. **Lay the export over this tree:** `npm run apply` (in `web/`). It runs `check:export` first, replaces `_next/`
   and `portal/`, copies `web/out/` over the root without deleting anything else, then applies the diff filter: only
   pages, `404.html`, `sitemap.xml`, `_next/`, `portal/` and `index.txt` files may change, and no contract file may;
   anything else stops it with the list.
6. **Commit, push, and after Pages has deployed** (about a minute to ten): `python3 scripts/check_published_artefacts.py`,
   and a look at the live pages (the export's own gate can be pointed at any served copy of the tree).

Tell the other brand sessions before pushing (they share this repository). Going back is `git revert` of the cutover
or release commit; nothing the launcher or the bot reads is in a page diff.

## License

Site code (`scripts/`, `assets/css`, `assets/js`) is available for reuse. Content
(recipe names, changelog text, screenshots/icons derived from the mods) documents
specific modded servers and isn't guaranteed accurate for others.
