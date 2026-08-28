#!/usr/bin/env python3
"""
Shared registry + page-shell template for the Aurora Corvus static site.
Plain Python string templates (no Jinja2 dependency) — every other generator
script imports from here so the header/nav/footer never drifts between pages.

Multi-language: the JA site lives at the repo root (/, /changelog/, ...);
every other language lives one level down (/en/, /en/changelog/, ...). Pull
translated strings via load_bundle(lang) (data/i18n/<lang>.json, produced by
scripts/extract_bundle.py for ja and by translation agents for the rest).
"""
from __future__ import annotations

import json
import re
from pathlib import Path
import html as _html

ROOT = Path(__file__).resolve().parent.parent
I18N_DIR = ROOT / "data" / "i18n"
DOWNLOADS_DIR = ROOT / "downloads"

# Three distinct names, deliberately kept apart:
#   SITE_TITLE          the website              -> "Aurora Corvus"
#   "Glimpse Alpha"     the mod pack product     -> NEVER renamed
#   LAUNCHER_APP_NAME   the desktop updater app  -> "Corvus" (was
#                       "Glimpse Launcher" until the 1.3.0 rename)
SITE_TITLE = "Aurora Corvus"  # brand name, unchanged across languages
LAUNCHER_APP_NAME = "Corvus"

# Absolute origin+path this site is published at. Needed because Open Graph
# requires an ABSOLUTE og:image URL — a relative one is silently ignored by
# every scraper, which is how a site ends up with no share preview at all.
# (build_glimpse_manifest.py keeps its own copy for the launcher manifest.)
SITE_BASE_URL = "https://iroponcopin.github.io/aurora-corvus"
OG_IMAGE_URL = f"{SITE_BASE_URL}/assets/img/brand/og-image.png"

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
# Pages serves this repo at https://<user>.github.io/aurora-corvus/, not
# the domain root, so every link in this site is prefix-relative.
NAV_SECTIONS = [
    ("home", ""),
    ("download", "download/"),
    ("changelog", "changelog/"),
    ("recipes", "recipes/"),
    ("guide", "guide/"),
    ("launcher", "launcher/"),
    ("gates", "gates/"),
    ("features", "features/"),
    ("roadmap", "roadmap/"),
    ("issues", "known-issues/"),
]

# English fallback nav labels, used only when a language bundle doesn't
# (yet) carry a translated ui.nav[key] entry. All 13 languages have had
# full nav translations since launch, but a newly-added section (like
# "launcher") lands in en/ja first — see load_bundle()/available_langs()
# for the equivalent "English default" convention used throughout the
# per-page build scripts (e.g. build_download.py's dl.get(key, "...")).
NAV_LABEL_FALLBACK = {
    "launcher": LAUNCHER_APP_NAME,
}

# --- Mega menu -------------------------------------------------------------
# The ten sections above are grouped into three hover-revealed panels plus a
# standalone Home link. Every section in NAV_SECTIONS must appear exactly
# once here or in NAV_SOLO — _nav_html() asserts that, so adding an 11th page
# without filing it can't silently drop it out of the navigation.
NAV_SOLO = ["home"]
NAV_GROUPS = [
    ("start", ["download", "launcher", "guide"]),
    ("reference", ["recipes", "gates", "features"]),
    ("status", ["changelog", "roadmap", "issues"]),
]

# English fallbacks for the group heading + one-line blurb shown in each
# panel. Japanese lives in data/ui-strings.ja.json -> ui.nav_groups (and so
# in data/i18n/ja.json); the other 11 languages fall back to English here,
# exactly the way NAV_LABEL_FALLBACK["launcher"] already does.
NAV_GROUP_FALLBACK = {
    "start": {
        "label": "Get started",
        "lede": "Download the pack, install it on your server, and let %s "
                "keep every module up to date." % LAUNCHER_APP_NAME,
    },
    "reference": {
        "label": "Reference",
        "lede": "Every crafting recipe, every dimensional gate, and a tour of what the "
                "suite actually adds to the game.",
    },
    "status": {
        "label": "Status",
        "lede": "What shipped in each release, what is planned next, and what is still "
                "known to be broken.",
    },
}


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


def pack_version() -> str:
    """現在配布中のパックのバージョン(例 "2.4.8")。出典は data/versions.json。

    module_counts() と同じ規律: バージョン番号を 13 言語の文面に**書かない**。
    i18n 文字列側は {pack_version} プレースホルダを使う。ダウンロード頁が
    2.4.8 の ZIP を配りながら本文が「最新版は V2.2.0」と言い続けた実績がある。
    """
    p = ROOT / "data" / "versions.json"
    mods = json.loads(p.read_text(encoding="utf-8"))["mods"]
    versions = set(mods.values())
    if len(versions) != 1:
        raise SystemExit(
            f"ERROR: data/versions.json lists more than one distinct version {sorted(versions)} - "
            f"a single {{pack_version}} placeholder cannot be filled from a mixed release.")
    return versions.pop()


# ---------------------------------------------------------------------------
# Launcher release discovery
#
# ⚠ This lives here, shared, on purpose. build_download.py and
#   build_glimpse_manifest.py each used to carry their own private copy of
#   "find the launcher jar", and both copies had the same two defects:
#
#     1. They globbed "glimpse-launcher-*.jar". The app was renamed to
#        Corvus in 1.3.0 and its files became corvus-1.3.0.*, so the glob
#        matched nothing — and because a missing jar is a *supported* state
#        ("no launcher published yet"), the manifest would have quietly
#        shipped with no "launcher" block at all and every installed
#        launcher's self-update would have gone dark. No error, no warning.
#     2. They took sorted(...)[0] — the lexicographically FIRST match, not
#        the newest. That is correct only while exactly one jar sits in the
#        folder. With two present it advertises the OLDER one, and by string
#        order "1.10.0" < "1.2.1", so the first double-digit minor release
#        would have silently downgraded every user.
#
#   Both names are matched (the pre-rename files are still served), and the
#   winner is chosen by a parsed NUMERIC version tuple.
# ---------------------------------------------------------------------------
LAUNCHER_JAR_PREFIXES = ("corvus", "glimpse-launcher")
_LAUNCHER_JAR_RE = re.compile(
    r"^(?P<prefix>corvus|glimpse-launcher)-(?P<version>\d+(?:\.\d+)*)\.jar$")

# Keep in sync with the platform table in build_download.py /
# build_glimpse_manifest.py: (platform_id, extension, human label).
NATIVE_LAUNCHER_PLATFORMS = [
    ("macos", "dmg", "macOS"),
    ("windows", "msi", "Windows"),
    ("linux", "deb", "Linux"),
]


def launcher_version_key(version: str) -> tuple[int, ...]:
    """"1.10.0" -> (1, 10, 0). Numeric, so 1.10.0 > 1.2.1 — which is exactly
    what plain string sorting got wrong."""
    return tuple(int(p) for p in version.split("."))


def find_launcher_jars(download_dir: Path | None = None) -> list[dict]:
    """Every published launcher jar, newest first."""
    d = DOWNLOADS_DIR if download_dir is None else download_dir
    if not d.is_dir():
        return []
    found = []
    for p in d.iterdir():
        if not p.name.endswith(".jar"):
            continue
        if not p.name.startswith(tuple(f"{x}-" for x in LAUNCHER_JAR_PREFIXES)):
            continue
        m = _LAUNCHER_JAR_RE.match(p.name)
        if not m:
            raise SystemExit(
                f"ERROR: {p} looks like a launcher jar but does not match "
                f"<{'|'.join(LAUNCHER_JAR_PREFIXES)}>-<numeric.version>.jar. Refusing to guess "
                f"its version - rename it or the download page and the manifest would disagree "
                f"about what the current release is.")
        found.append({
            "version": m.group("version"),
            "key": launcher_version_key(m.group("version")),
            "prefix": m.group("prefix"),
            "path": p,
            "file_name": p.name,
        })
    found.sort(key=lambda r: r["key"], reverse=True)
    return found


def newest_launcher_jar(download_dir: Path | None = None) -> dict | None:
    """The launcher release this site currently advertises, or None if the
    downloads folder holds no launcher jar at all.

    Two files parsing to the SAME version (e.g. both a corvus-1.3.0.jar and a
    leftover glimpse-launcher-1.3.0.jar) is refused rather than resolved by
    coin-flip: which one wins would decide the download URL every installed
    launcher polls for.
    """
    found = find_launcher_jars(download_dir)
    if not found:
        return None
    top = [r for r in found if r["key"] == found[0]["key"]]
    if len(top) > 1:
        raise SystemExit(
            "ERROR: downloads/ holds %d launcher jars that all parse to version %s (%s). "
            "Exactly one file must be the current release - delete the stale one."
            % (len(top), top[0]["version"], ", ".join(sorted(r["file_name"] for r in top))))
    return found[0]


def launcher_native_files(version: str, download_dir: Path | None = None) -> list[dict]:
    """Native installers actually present on disk for `version`, in display
    order. Matches whichever of the two name prefixes is really there, so a
    half-migrated downloads/ folder still resolves instead of silently
    reporting "no native builds"."""
    d = DOWNLOADS_DIR if download_dir is None else download_dir
    out = []
    for platform_id, ext, label in NATIVE_LAUNCHER_PLATFORMS:
        for prefix in LAUNCHER_JAR_PREFIXES:
            candidate = d / f"{prefix}-{version}-{platform_id}.{ext}"
            if candidate.exists():
                out.append({
                    "platform_id": platform_id,
                    "label": label,
                    "path": candidate,
                    "file_name": candidate.name,
                    "size_bytes": candidate.stat().st_size,
                })
                break
    return out


def _launcher_placeholders() -> tuple[str, str]:
    """(jar file name, version) for the {launcher_jar}/{launcher_version}
    placeholders. Same rule as {pack_version}: the number is NEVER typed into
    a translated string, it is read off the file actually being served."""
    rel = newest_launcher_jar()
    if rel is None:
        print("WARNING: downloads/ has no launcher jar - {launcher_jar}/{launcher_version} "
              "fall back to a generic name. Publish a launcher build before relying on this copy.")
        return f"{LAUNCHER_APP_NAME.lower()}.jar", "latest"
    return rel["file_name"], rel["version"]


def _fill_counts(node, subs: dict):
    if isinstance(node, dict):
        return {k: _fill_counts(v, subs) for k, v in node.items()}
    if isinstance(node, list):
        return [_fill_counts(v, subs) for v in node]
    if isinstance(node, str):
        for k, v in subs.items():
            node = node.replace(k, v)
        return node
    return node


_placeholder_cache: dict | None = None


def bundle_placeholders() -> dict:
    """The values substituted into every translated string at load time.

    Every entry here exists so a number or a file name is never typed into 13
    language bundles by hand — the class of bug this codebase has already
    been burned by twice (a "9 MODs" count that outlived the 10th module, and
    a "latest is V2.2.0" line shipping next to a V2.4.8 ZIP). {launcher_jar}
    and {launcher_version} joined for the same reason: the install
    instructions used to spell out glimpse-launcher-1.2.1.jar in both the EN
    and JA bundles, so the Corvus 1.3.0 rename would have left two languages
    telling people to run a file that no longer exists.
    """
    global _placeholder_cache
    if _placeholder_cache is None:
        n_mods, n_jars = module_counts()
        jar_name, jar_version = _launcher_placeholders()
        _placeholder_cache = {
            "{mod_count}": str(n_mods),
            "{jar_count}": str(n_jars),
            "{pack_version}": pack_version(),
            "{launcher_app}": LAUNCHER_APP_NAME,
            "{launcher_jar}": jar_name,
            "{launcher_version}": jar_version,
        }
    return _placeholder_cache


def fill_placeholders(node):
    """Run the same {pack_version}/{launcher_jar}/... substitution over
    content that did NOT come from a language bundle — specifically the
    English fallback copy the per-page build scripts carry inline, which
    must not be allowed to state a version the bundles no longer state."""
    return _fill_counts(node, bundle_placeholders())


def load_bundle(lang: str) -> dict:
    if lang not in _bundle_cache:
        p = I18N_DIR / f"{lang}.json"
        _bundle_cache[lang] = _fill_counts(
            json.loads(p.read_text(encoding="utf-8")), bundle_placeholders())
    return _bundle_cache[lang]


def available_langs() -> list[str]:
    """Languages that actually have a bundle on disk yet (lets pages render
    JA-only during development before translations land)."""
    return [c for c in LANG_CODES if (I18N_DIR / f"{c}.json").exists()]


def load_latest_changelog_entry(bundle: dict):
    """The newest changelog entry, with translated strings merged in from the
    bundle (falling back to the JA structural file for release/date/type/
    mod_versions, which never need translation).

    Lived in build_home.py until the home page was reduced to the wordmark +
    film and stopped rendering a "latest update" teaser at all. It is here,
    not in build_download.py, because a cross-import between two page
    builders is exactly how a helper ends up deleted out from under its only
    remaining caller.

    ⚠ "Latest" is selected by (date, parsed release version), NOT by file
      position: data/changelog.json once had newer entries hand-prepended at
      the top, and structural[-1] silently promoted V2.4.1 to "latest update"
      while the download page shipped V2.4.8.
    """
    p = ROOT / "data" / "changelog.json"
    if not p.exists():
        return None
    structural = json.loads(p.read_text(encoding="utf-8"))
    if not structural:
        return None
    by_release_date = {(t["release"], t["date"]): t
                       for t in (bundle.get("changelog") or [])}

    def _key(e):
        return (e.get("date", ""),
                tuple(int(n) for n in re.findall(r"\d+", str(e.get("release", "")))))

    s = max(structural, key=_key)
    t = by_release_date.get((s["release"], s["date"]), s)
    merged = dict(s)
    merged.update({k: t[k] for k in ("title", "summary", "highlights") if k in t})
    return merged


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


def _nav_label(bundle: dict, key: str) -> str:
    return bundle["ui"]["nav"].get(key, NAV_LABEL_FALLBACK.get(key, key))


def _nav_group_strings(bundle: dict, gkey: str) -> dict:
    """Group heading + blurb for one mega-menu panel.

    Same English-default convention as NAV_LABEL_FALLBACK: a language that
    has translated ui.nav_groups gets its own strings, everyone else gets
    the English ones rather than a raw key.
    """
    fallback = NAV_GROUP_FALLBACK[gkey]
    got = (bundle["ui"].get("nav_groups") or {}).get(gkey) or {}
    return {
        "label": got.get("label") or fallback["label"],
        "lede": got.get("lede") or fallback["lede"],
    }


def _mega_link_html(bundle: dict, key: str, slug: str, lang_prefix: str, active: str) -> str:
    """One two-line link inside a mega panel.

    The second line reuses ui.page_titles[key] — the fuller name of the same
    page ("ゲート" in the nav bar, "ゲート・門一覧" as the page title) — so the
    panel reads like Apple's (label + short descriptor) without inventing a
    new string that would need 13 translations. It is dropped when the two
    are identical, which is what happens for the languages whose nav label
    and page title are the same word.
    """
    label = _nav_label(bundle, key)
    sub = (bundle["ui"].get("page_titles") or {}).get(key, "")
    sub_html = f'<span class="mega-link__sub">{esc(sub)}</span>' if sub and sub != label else ""
    is_cur = key == active
    cls = "mega-link is-current" if is_cur else "mega-link"
    cur = ' aria-current="page"' if is_cur else ""
    return (f'<li><a class="{cls}" href="{lang_prefix}{slug}"{cur}>'
            f'<span class="mega-link__label">{esc(label)}</span>{sub_html}</a></li>')


def _nav_html(bundle: dict, active: str, lang_prefix: str) -> str:
    """Top-level nav: standalone links + hover-revealed mega-menu panels.

    Guards against a new NAV_SECTIONS entry going unfiled — an unreachable
    page is exactly the kind of silent breakage this file exists to prevent.
    """
    slug_of = dict(NAV_SECTIONS)
    filed = set(NAV_SOLO)
    for _g, keys in NAV_GROUPS:
        filed.update(keys)
    missing = [k for k, _s in NAV_SECTIONS if k not in filed]
    if missing:
        raise SystemExit(
            "ERROR: site_common.NAV_SECTIONS lists %s, which no NAV_GROUPS group and no "
            "NAV_SOLO entry claims. Those pages would build but be unreachable from the "
            "navigation on all 13 languages." % ", ".join(repr(m) for m in missing))

    items = []
    for key in NAV_SOLO:
        cls = "nav-link nav-link--solo" + (" is-current" if key == active else "")
        cur = ' aria-current="page"' if key == active else ""
        items.append(
            f'<li class="nav-item">'
            f'<a class="{cls}" href="{lang_prefix}{slug_of[key]}"{cur}>'
            f'{esc(_nav_label(bundle, key))}</a></li>')

    for gkey, keys in NAV_GROUPS:
        g = _nav_group_strings(bundle, gkey)
        panel_id = f"mega-{gkey}"
        open_cls = " is-current" if active in keys else ""
        links = "\n            ".join(
            _mega_link_html(bundle, k, slug_of[k], lang_prefix, active) for k in keys)
        items.append(f"""<li class="nav-item nav-item--mega">
          <button class="nav-link nav-link--mega{open_cls}" type="button"
                  aria-expanded="false" aria-haspopup="true" aria-controls="{panel_id}">
            <span>{esc(g['label'])}</span><span class="nav-link__caret" aria-hidden="true"></span>
          </button>
          <div class="mega-panel" id="{panel_id}" role="group" aria-label="{esc(g['label'])}">
            <div class="mega-panel__inner">
              <div class="mega-panel__blurb">
                <p class="mega-panel__title">{esc(g['label'])}</p>
                <p class="mega-panel__lede">{esc(g['lede'])}</p>
              </div>
              <ul class="mega-links">
            {links}
              </ul>
            </div>
          </div>
        </li>""")
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
        e.g. "/aurora-corvus/" to force every link/asset in the shell to
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
    # Every page gets a share card. og_image may override it per page, but it
    # must be absolute either way (see OG_IMAGE_URL).
    og_src = og_image or OG_IMAGE_URL
    og = (f'<meta property="og:image" content="{esc(og_src)}">\n'
          f'<meta property="og:image:width" content="1200">\n'
          f'<meta property="og:image:height" content="630">\n'
          f'<meta property="og:image:alt" content="{esc(SITE_TITLE)}">\n'
          f'<meta name="twitter:card" content="summary_large_image">\n    ')
    lang_switch = _lang_switcher_html(lang, section, root_prefix)

    return f"""<!doctype html>
<html lang="{lang}" dir="{text_dir}">
<head>
<meta charset="utf-8">
<!-- viewport-fit=cover so env(safe-area-inset-*) is non-zero on notched
     iPhones; every edge-anchored surface (header, drawer, main, footer,
     modal) pads itself with max(gutter, inset) in style.css. -->
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(full_title)}</title>
<meta name="description" content="{esc(description)}">
<meta property="og:title" content="{esc(full_title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{esc(SITE_TITLE)}">
{og}<link rel="icon" href="{root_prefix}assets/img/brand/favicon.ico" sizes="any">
<link rel="icon" type="image/png" sizes="32x32" href="{root_prefix}assets/img/brand/favicon-32.png">
<link rel="icon" type="image/png" sizes="16x16" href="{root_prefix}assets/img/brand/favicon-16.png">
<link rel="apple-touch-icon" sizes="180x180" href="{root_prefix}assets/img/brand/apple-touch-icon.png">
<!-- Typography is the Apple system stack (SF Pro on macOS/iOS, Hiragino Sans
     for Japanese) — see style.css. Cormorant Garamond and Zen Kaku Gothic New
     were dropped on owner directive (hard to read), and their font request
     went with them rather than being left behind as a dead download. Inter is
     the cross-platform stand-in for SF and sits after the native names in the
     stack, so on Apple hardware the face files are never fetched at all. -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap">
<link rel="stylesheet" href="{root_prefix}assets/css/style.css">
<script>
/* Boot: tag JS availability for the motion layer, and apply the persisted
   theme before first paint. Dark is the flagship default; "light" is the
   secondary theme (see style.css + main.js theme toggle). */
(function () {{
  var d = document.documentElement;
  d.classList.add("js");
  var t = "dark";
  try {{
    var s = localStorage.getItem("aurora-corvus-theme");
    if (s === "light" || s === "dark") t = s;
  }} catch (e) {{ /* storage unavailable: stay dark */ }}
  d.setAttribute("data-theme", t);
}})();
</script>
{extra_head}</head>
<body>
<div class="sky" aria-hidden="true"><div class="sky__aurora"></div></div>
<a class="skip-link" href="#main">{esc(ui['skip_link'])}</a>
<div class="nav-scrim" id="navScrim" aria-hidden="true"></div>
<header class="site-header">
  <div class="site-header__inner">
    <a class="brand" href="{lang_prefix}">
      <span class="brand__mark" aria-hidden="true"></span>
      <span class="brand__text">{esc(SITE_TITLE)}</span>
    </a>
    <button class="nav-toggle" id="navToggle" aria-expanded="false" aria-controls="siteNav" aria-label="{esc(ui['menu_toggle'])}">
      <span></span><span></span><span></span>
    </button>
    <nav class="site-nav" id="siteNav">
      <ul class="nav-list">
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
    <p class="site-footer__brand"><span class="brand__mark" aria-hidden="true"></span> {esc(SITE_TITLE)}</p>
    <p>{esc(ui['site_tagline'])}</p>
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
