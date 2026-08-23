# Glimpse Alpha Wiki

An unofficial reference site for **Glimpse Alpha** (formerly *Sorakaze*), a set of
Fabric mods for a private Minecraft server. It documents the mod pack's crafting
recipes, update history, and install instructions. As of V2.2.0 it also hosts the
current release ZIP directly (`downloads/`, linked from the `/download/` page) —
earlier versions were owner-distributed only and are not archived here.

Live site: served via GitHub Pages from this repository.

## What's here

- `index.html`, `download/`, `changelog/`, `recipes/`, `guide/`, `roadmap/`,
  `known-issues/` — the Japanese (primary) site, generated as static HTML.
- `en/`, `es/`, `fr/`, `zh/`, `ko/`, `pt-br/`, `it/`, `ar/`, `ru/`, `id/`, `de/`, `tr/` —
  the same site in 12 additional languages, one directory per
  [BCP-47-ish](https://en.wikipedia.org/wiki/IETF_language_tag) language code.
- `downloads/` — the current release ZIP (`Glimpse_Alpha_MODs_v<version>+mc26.2.zip`),
  assembled by `tools/build_dist_zip.py` at the repo root and copied here. Only the
  current version is kept; `scripts/build_download.py` reads its real size/sha256/
  version at build time rather than trusting a typed-in value.
- `assets/` — shared CSS/JS and the recipe item icon images (908 PNGs extracted
  from the mod pack's own textures), reused by every language.
- `data/` — the underlying JSON data (recipes, changelog, guide content, etc.)
  that the `scripts/build_*.py` generators render into the static HTML above.
- `scripts/` — the static-site generator. Plain Python, no framework. See below.

## Rebuilding the site

The site is pre-rendered static HTML committed to this repo (no build step runs
on GitHub Pages). To regenerate it after editing content:

```bash
# 1. Re-pull source data from the mod pack project (only if that project shipped
#    an update — these read from a sibling directory on the maintainer's machine,
#    not from anything in this repo):
python3 scripts/extract_versions.py     # current per-mod version numbers
python3 scripts/extract_recipes.py      # recipe data + item icons
python3 scripts/merge_changelog.py      # merges data/changelog-raw-*.json

# 2. Re-extract the Japanese translation-source bundle:
python3 scripts/extract_bundle.py

# 3. (Only if data/i18n/ja.json content changed) re-run translation for the
#    12 other languages, then place each result at data/i18n/<lang>.json.

# 4. Render every page in every available language:
python3 scripts/build.py
```

Each language only renders once its bundle exists at `data/i18n/<lang>.json` —
the Japanese site works standalone even before other languages are translated.

## License

Site code (`scripts/`, `assets/css`, `assets/js`) is available for reuse. Content
(recipe names, changelog text, screenshots/icons derived from the mod pack) documents
a specific private modded server and isn't guaranteed accurate for other servers or
mod pack versions.
