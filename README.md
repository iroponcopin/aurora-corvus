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

- `index.html`, `download/`, `changelog/`, `recipes/`, `launcher/`, `upcoming/`,
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

## Rebuilding the site

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

## License

Site code (`scripts/`, `assets/css`, `assets/js`) is available for reuse. Content
(recipe names, changelog text, screenshots/icons derived from the mods) documents
specific modded servers and isn't guaranteed accurate for others.
