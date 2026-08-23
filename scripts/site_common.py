#!/usr/bin/env python3
"""
Shared registry + page-shell template for the Glimpse Alpha Wiki static site.
Plain Python string templates (no Jinja2 dependency) — every other generator
script imports from here so the header/nav/footer never drifts between pages.

Multi-language: the JA site lives at the repo root (/, /changelog/, ...);
every other language lives one level down (/en/, /en/changelog/, ...). Pull
translated strings via load_bundle(lang) (data/i18n/<lang>.json, produced by
scripts/extract_bundle.py for ja and by translation agents for the rest).
"""
from __future__ import annotations

import json
from pathlib import Path
import html as _html

ROOT = Path(__file__).resolve().parent.parent
I18N_DIR = ROOT / "data" / "i18n"

SITE_TITLE = "Glimpse Alpha Wiki"  # brand name, unchanged across languages

# (code, native display name, text direction). Order = language-switcher order.
LANGUAGES = [
    ("ja", "日本語", "ltr"),
    ("en", "English", "ltr"),
    ("es", "Español", "ltr"),
    ("fr", "Français", "ltr"),
    ("zh", "简体中文", "ltr"),
    ("ko", "한국어", "ltr"),
    ("pt-br", "Português (Brasil)", "ltr"),
    ("it", "Italiano", "ltr"),
    ("ar", "العربية", "rtl"),
    ("ru", "Русский", "ltr"),
    ("id", "Bahasa Indonesia", "ltr"),
    ("de", "Deutsch", "ltr"),
    ("tr", "Türkçe", "ltr"),
]
LANG_CODES = [c for c, _, _ in LANGUAGES]
LANG_NAME = {c: n for c, n, _ in LANGUAGES}
LANG_DIR = {c: d for c, n, d in LANGUAGES}

# The 10 modules of the suite, in the order they were introduced. Colors are
# used as accent hues across nav tags, recipe category tabs, and changelog mod
# badges. Names/taglines are looked up per-language from the bundle's ui.mods;
# "key" here is also the lookup key into that dict.
#
# "cat" is this module's primary recipe-category tab, **by name**, resolved
# against data/recipes.json at build time by recipe_cat_index() below.
# ⚠ It used to be a hard-typed integer, and that broke silently the moment a
#   10th tab appeared: backrooms (0 recipes) carried cat_index 9 as a
#   deliberate "points at a tab that does not exist", and when 二相楽園
#   became tab 9 the backrooms card on the home page started deep-linking
#   into Planarcadia's recipes. Nothing errored; the link just went somewhere
#   wrong. Names are resolved, and an unknown name stops the build.
#   cat=None means "this module has no recipe tab" -> the card links to the
#   recipes page with no hash instead of to a wrong tab.
# deco also has a secondary "ドア" category, not linked here for simplicity.
MOD_ORDER = [
    {"id": "sorakaze_guns", "key": "guns", "color": "#c0533a", "cat": "銃"},
    {"id": "sorakaze_rail", "key": "rail", "color": "#3d7dc4", "cat": "電車"},
    {"id": "sorakaze_deco", "key": "deco", "color": "#4f8f43", "cat": "建材"},
    {"id": "sorakaze_boss", "key": "boss", "color": "#9349b8", "cat": "ボス"},
    {"id": "sorakaze_sky", "key": "sky", "color": "#3badc9", "cat": "天空"},
    {"id": "sorakaze_survival", "key": "survival", "color": "#c19a2e", "cat": "サバイバル"},
    {"id": "sorakaze_vehicles", "key": "vehicles", "color": "#d17a34", "cat": "乗り物"},
    {"id": "sorakaze_power", "key": "power", "color": "#d4b32e", "cat": "電力"},
    {"id": "sorakaze_backrooms", "key": "backrooms", "color": "#7d7d52", "cat": None},
    # V2.0.0 で初出荷。V2.1.0 まで、このサイトのどこにも載っていなかった。
    {"id": "sorakaze_planarcadia", "key": "planarcadia", "color": "#b0559b", "cat": "二相楽園"},
]
MODS_BY_ID = {m["id"]: m for m in MOD_ORDER}
MODS_BY_KEY = {m["key"]: m for m in MOD_ORDER}

_cat_index_cache: dict | None = None


def recipe_cat_index(cat_name):
    """data/recipes.json の "cats" から、ジャンル名 -> タブ番号を引く。

    番号を書き写さない。書き写した瞬間に、ジャンルが 1 つ増えた日に
    どこかのリンクが黙って別のジャンルを指す(実際そうなった)。
    知らない名前は **例外で止める** —— 静かに 0 番へ落とさない。
    """
    global _cat_index_cache
    if cat_name is None:
        return None
    if _cat_index_cache is None:
        p = ROOT / "data" / "recipes.json"
        cats = json.loads(p.read_text(encoding="utf-8"))["cats"]
        _cat_index_cache = {c[0]: i for i, c in enumerate(cats)}
        if not _cat_index_cache:
            raise SystemExit(f"ERROR: {p} lists no recipe categories at all - every deep link "
                             f"below would resolve to nothing")
    if cat_name not in _cat_index_cache:
        raise SystemExit(
            "ERROR: MOD_ORDER names recipe category %r, which is not a tab in data/recipes.json "
            "(tabs: %s). Re-run scripts/extract_recipes.py, or fix the name - a deep link to a "
            "non-existent tab fails silently in the browser."
            % (cat_name, ", ".join(_cat_index_cache)))
    return _cat_index_cache[cat_name]

# slugs are relative to EACH LANGUAGE's own root (no leading slash!). GitHub
# Pages serves this repo at https://<user>.github.io/glimpse-alpha-wiki/, not
# the domain root, so every link in this site is prefix-relative.
NAV_SECTIONS = [
    ("home", ""),
    ("download", "download/"),
    ("changelog", "changelog/"),
    ("recipes", "recipes/"),
    ("guide", "guide/"),
    ("gates", "gates/"),
    ("features", "features/"),
    ("roadmap", "roadmap/"),
    ("issues", "known-issues/"),
]


def esc(s) -> str:
    return _html.escape(str(s), quote=True)


_bundle_cache: dict[str, dict] = {}


def module_counts() -> tuple[int, int]:
    """(このスイートの MOD 数, 導入に要る jar の数)。出典は data/versions.json。

    ⚠ 数を文章に**書かない**ための関数である。V2.0.0 で 10 個目(二相楽園)が
      出荷されたのに、13 言語ぶんの本文・導入手引き・レシピ頁の見出しが
      「9」と書いたまま公開され続けた。人が 13 言語を追いかけて直す作業に
      なっているかぎり、11 個目でも同じことが起きる。
    """
    p = ROOT / "data" / "versions.json"
    mods = json.loads(p.read_text(encoding="utf-8"))["mods"]
    n = len(mods)
    if n < 2:
        raise SystemExit(
            f"ERROR: {p} lists {n} module(s). That is not a small suite - it means "
            f"scripts/extract_versions.py did not see the dist/ jars, and every page would "
            f"publish a wrong module count with no error.")
    return n, n + 1          # +1 = Fabric API


def _fill_counts(node, mods: str, jars: str):
    if isinstance(node, dict):
        return {k: _fill_counts(v, mods, jars) for k, v in node.items()}
    if isinstance(node, list):
        return [_fill_counts(v, mods, jars) for v in node]
    if isinstance(node, str):
        return node.replace("{mod_count}", mods).replace("{jar_count}", jars)
    return node


def load_bundle(lang: str) -> dict:
    if lang not in _bundle_cache:
        p = I18N_DIR / f"{lang}.json"
        n_mods, n_jars = module_counts()
        _bundle_cache[lang] = _fill_counts(
            json.loads(p.read_text(encoding="utf-8")), str(n_mods), str(n_jars))
    return _bundle_cache[lang]


def available_langs() -> list[str]:
    """Languages that actually have a bundle on disk yet (lets pages render
    JA-only during development before translations land)."""
    return [c for c in LANG_CODES if (I18N_DIR / f"{c}.json").exists()]


def mod_badge(bundle: dict, mod_id: str, small: bool = False) -> str:
    m = MODS_BY_ID.get(mod_id)
    if not m:
        return ""
    name = bundle["ui"]["mods"].get(m["key"], {}).get("name", m["key"])
    cls = "mod-badge mod-badge--sm" if small else "mod-badge"
    return f'<span class="{cls}" style="--mod-color:{m["color"]}">{esc(name)}</span>'


def type_badge(bundle: dict, t: str) -> str:
    label = bundle["ui"]["type_badge"].get(t, t)
    cls = {"release": "type-release", "hotfix": "type-hotfix", "visual-update": "type-visual"}.get(t, "type-release")
    return f'<span class="type-badge {cls}">{esc(label)}</span>'


def _levels_to_root(depth: int, lang: str) -> int:
    return depth + (0 if lang == "ja" else 1)


def _prefix(levels: int) -> str:
    return "../" * levels if levels else "./"


def asset_root_prefix(depth: int, lang: str) -> str:
    """Public helper for build scripts that need to reference assets/data
    from inside `extra_head` (e.g. a page-specific <script src>) -- must use
    this rather than a hardcoded "../", since non-ja languages sit one
    directory deeper than ja. Mirrors page()'s own root_prefix computation
    exactly; see the recipes.js/changelog.js 404 this fixed (§ commit
    history) for what goes wrong if a build script hardcodes the prefix
    instead of calling this."""
    return _prefix(_levels_to_root(depth, lang))


def _nav_html(bundle: dict, active: str, lang_prefix: str) -> str:
    items = []
    for key, slug in NAV_SECTIONS:
        label = bundle["ui"]["nav"][key]
        cls = ' class="active"' if key == active else ""
        items.append(f'<li><a href="{lang_prefix}{slug}"{cls}>{esc(label)}</a></li>')
    return "\n        ".join(items)


def _lang_switcher_html(lang: str, section: str, root_prefix: str) -> str:
    items = []
    for code, name, _dir in LANGUAGES:
        if not available_langs() or code not in available_langs():
            continue
        target = root_prefix + ("" if code == "ja" else f"{code}/") + section
        cls = ' class="active" aria-current="true"' if code == lang else ""
        items.append(f'<li><a href="{target}"{cls}>{esc(name)}</a></li>')
    return "\n        ".join(items)


def page(
    *,
    lang: str,
    section: str,
    title: str,
    description: str,
    active: str,
    body: str,
    depth: int = 0,
    extra_head: str = "",
    og_image: str | None = None,
    absolute_base: str | None = None,
) -> str:
    """Wrap body HTML in the full site shell (head, nav, footer).

    lang: language code (e.g. "ja", "en").
    section: this page's slug relative to its language root ("" for home,
        "changelog/" etc.) — used to build the language-switcher links.
    depth: 0 for the language-root page (home), 1 for a one-level section.
    absolute_base: for the one page that isn't reachable via a predictable
        relative depth (the site-wide 404.html — GitHub Pages serves its
        *content* at whatever broken URL the visitor hit, at any depth, so
        relative asset/nav paths would resolve against the wrong base). Pass
        e.g. "/glimpse-alpha-wiki/" to force every link/asset in the shell to
        an absolute path instead of a depth-relative one.
    """
    bundle = load_bundle(lang)
    ui = bundle["ui"]
    if absolute_base is not None:
        root_prefix = absolute_base
        lang_prefix = absolute_base if lang == "ja" else f"{absolute_base}{lang}/"
    else:
        root_prefix = _prefix(_levels_to_root(depth, lang))
        lang_prefix = _prefix(depth)
    text_dir = LANG_DIR.get(lang, "ltr")

    full_title = f"{title} | {SITE_TITLE}" if title else SITE_TITLE
    og = f'<meta property="og:image" content="{esc(og_image)}">\n    ' if og_image else ""
    lang_switch = _lang_switcher_html(lang, section, root_prefix)

    return f"""<!doctype html>
<html lang="{lang}" dir="{text_dir}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(full_title)}</title>
<meta name="description" content="{esc(description)}">
<meta property="og:title" content="{esc(full_title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:type" content="website">
{og}<link rel="icon" href="{root_prefix}assets/img/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{root_prefix}assets/css/style.css">
{extra_head}</head>
<body>
<a class="skip-link" href="#main">{esc(ui['skip_link'])}</a>
<header class="site-header">
  <div class="site-header__inner">
    <a class="brand" href="{lang_prefix}">
      <span class="brand__mark" aria-hidden="true">◆</span>
      <span class="brand__text">{esc(SITE_TITLE)}</span>
    </a>
    <button class="nav-toggle" id="navToggle" aria-expanded="false" aria-controls="siteNav" aria-label="{esc(ui['menu_toggle'])}">
      <span></span><span></span><span></span>
    </button>
    <nav class="site-nav" id="siteNav">
      <ul>
        {_nav_html(bundle, active, lang_prefix)}
      </ul>
      <div class="lang-switch">
        <button class="lang-switch__toggle" id="langToggle" type="button" aria-expanded="false" aria-controls="langMenu" title="{esc(ui['lang_switch_label'])}">
          🌐 <span>{esc(LANG_NAME.get(lang, lang))}</span>
        </button>
        <ul class="lang-switch__menu" id="langMenu">
          {lang_switch}
        </ul>
      </div>
      <button class="theme-toggle" id="themeToggle" type="button" aria-label="{esc(ui['theme_toggle'])}" title="{esc(ui['theme_toggle'])}">🌓</button>
    </nav>
  </div>
</header>
<main id="main">
{body}
</main>
<footer class="site-footer">
  <div class="site-footer__inner">
    <p>{esc(SITE_TITLE)} — {esc(ui['site_tagline'])}</p>
    <p class="site-footer__note">{esc(ui['footer_note'])}</p>
  </div>
</footer>
<script src="{root_prefix}assets/js/main.js"></script>
</body>
</html>
"""


def out_dir_for(lang: str, section: str) -> Path:
    base = ROOT if lang == "ja" else ROOT / lang
    return (base / section) if section else base


def write_page(lang: str, section: str, html: str):
    out_path = out_dir_for(lang, section) / "index.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    print(f"wrote {out_path.relative_to(ROOT)} ({len(html):,} bytes)")
