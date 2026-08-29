#!/usr/bin/env python3
"""Builds v3/index.html (the V3 update teaser) for every language.

============================================================================
THIS PAGE IS TEMPORARY. Read this before touching anything else in here.

V3 is a real upcoming mod-pack update that has not shipped yet. This page
exists only as a "coming soon" teaser for the interim, per owner directive
(2026-08): once V3 actually ships, the whole page must come down. When that
day comes, deletion is exactly these four steps and nothing else:

  1. Delete this file (scripts/build_v3_teaser.py).
  2. Delete assets/img/v3-teaser/ (hero-source.jpg, hero-illustration.webp,
     launcher.webp, og-v3-teaser.jpg), assets/css/v3-teaser.css and
     assets/js/v3-teaser.js.
  3. Delete data/v3_teaser.json.
  4. Remove the "v3" entry from scripts/site_common.py: the ("v3", "v3/")
     tuple in NAV_SECTIONS, the "v3" string in NAV_SOLO, and the
     NAV_LABEL_FALLBACK["v3"] line.
  5. Remove "build_v3_teaser.py" from scripts/build.py's BUILD_SCRIPTS list.
  6. Re-run `python3 scripts/build.py` — this deletes v3/, en/v3/, etc. only
     if you also `rm -rf` the old output directories first (the generator
     never deletes stale output on its own; nothing else does either, so do
     that as part of the same cleanup: `rm -rf v3 */v3` from the repo root).

That is the whole footprint. This page was deliberately kept out of the
general-purpose i18n bundles (data/i18n/*.json) and out of the shared
assets/css/style.css / assets/js/main.js specifically so removal is exactly
the steps above, not an archaeology dig through shared files for orphaned
strings or rules once V3 ships and this teaser stops being true.
============================================================================

Content: data/v3_teaser.json, one block per language, written for this page
alone (not shared with data/i18n/*.json — see above). Sourced from
Update/V3_Update.md's own "Implementation order (recommended)" grouping;
the 50-feature count and the six category groupings are copied from that
document, not invented here.

Motion: a pinned two-beat "film" (title card, then the flagship missile
launcher) using the exact same technique as the home page's film — a sticky
stage driven by scroll-linked CSS custom properties written once per rAF
frame, transform/opacity only, complete static fallback under
`prefers-reduced-motion: reduce` or with JS disabled. See
assets/css/v3-teaser.css and assets/js/v3-teaser.js for the mechanism, and
scripts/build_home.py / the "Film" block in assets/css/style.css for the
original this was modelled on. Neither the home page's film markup, CSS, nor
JS is touched by this file.

The six category sections below the pinned film are plain `main > section`
elements on purpose: that makes them pick up the site's existing
scroll-entrance reveal (main.js's REVEAL_SELECTOR + .reveal in style.css) at
zero extra cost, rather than inventing a second scroll-reveal mechanism for
content that doesn't need the pinned treatment.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from site_common import (  # noqa: E402
    ROOT, SITE_BASE_URL, esc, page, write_page, available_langs,
    asset_root_prefix,
)

DATA_PATH = ROOT / "data" / "v3_teaser.json"
IMG = "assets/img/v3-teaser"

HERO_ILLUSTRATION = {"file": "hero-illustration.webp", "w": 488, "h": 784}
LAUNCHER_PHOTO = {"file": "launcher.webp", "w": 1118, "h": 759}
OG_IMAGE = "og-v3-teaser.jpg"

FEATURE_COUNT = "50"  # sourced from Update/V3_Update.md; never re-typed elsewhere

# Prefix for links to ANOTHER PAGE OF THIS SITE, from a page at depth 1.
# Language-RELATIVE: "../changelog/" from /v3/ reaches /changelog/, and from
# /en/v3/ reaches /en/changelog/.
#
# ⚠ This is NOT asset_root_prefix(). That one resolves to the SITE root, which
#   for a non-Japanese language is one level further up -- so using it for a
#   page link sends every reader of the other twelve languages to the JAPANESE
#   page. That is exactly what the closing section's "see the changelog" link
#   did on all twelve non-JA V3 pages until 2026-08-29. Assets (CSS, JS,
#   images) DO live at the site root and DO want asset_root_prefix; pages do
#   not. Same convention as build_download.py's `<a href="../changelog/">` and
#   build_roadmap.py's LANG_PREFIX, and the same thing site_common.page()
#   computes for itself as lang_prefix = _prefix(depth) with depth=1.
LANG_PREFIX = "../"

# CJK text has no spaces, so EVERY character boundary is a valid line break
# as far as the browser is concerned -- a <wbr> hint doesn't help, because it
# only ever ADDS a break opportunity, never removes the others. Observed at
# 375px: the JA flagship title's text-wrap: balance (sitewide, style.css
# h1/h2/h3/h4) chose to split "ミサイルランチャー" (missile launcher) right
# through the middle of "ミサイル" (missile) -- legible, but jarring for a
# hand-quality JA string. The actual fix is to make that one loanword atomic
# (white-space: nowrap) so the only place left to break is the real word
# boundary right before it. Only languages that need this get an entry.
FLAGSHIP_TITLE_NOWRAP = {
    "ja": "ミサイルランチャー",
}


def wrap_nowrap(escaped_text: str, phrase: str) -> str:
    """Wraps the first occurrence of `phrase` in ALREADY-ESCAPED text with a
    white-space:nowrap span, so it can no longer be split mid-word by
    text-wrap: balance. Same trusted-markup-after-escaping discipline as
    emphasize_number() below."""
    if phrase and phrase in escaped_text:
        return escaped_text.replace(
            phrase, f'<span style="white-space:nowrap">{phrase}</span>', 1)
    return escaped_text


def load_data() -> dict:
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def emphasize_number(escaped_text: str, num: str = FEATURE_COUNT) -> str:
    """Wraps the first occurrence of `num` in escaped_text with a span for
    the big-number typographic treatment (see v3-teaser.css's
    .v3t-count__num-inline). Operates on ALREADY-ESCAPED text and inserts a
    single trusted <span> — never runs on raw, unescaped input."""
    if num in escaped_text:
        return escaped_text.replace(
            num, f'<span class="v3t-count__num-inline">{num}</span>', 1)
    return escaped_text


# --- decorative motifs (inline SVG, no assets) -----------------------------
# Two shapes, echoing the hero plate's own visual language: a wireframe
# hex/octahedron (like the floating cube's supporting frame) and a right-
# angled circuit trace with small node squares (like the amber circuit-lines
# threaded through the plate's terrain). Purely decorative -- aria-hidden,
# never carry information, and are hidden below 860px where there's no room
# for them to breathe (see v3-teaser.css).
def _wireframe_svg(rotate: int) -> str:
    return f"""<svg viewBox="0 0 200 200" aria-hidden="true" style="transform:rotate({rotate}deg)">
  <polygon points="100,18 170,60 170,140 100,182 30,140 30,60" fill="none" stroke="currentColor" stroke-width="1.4"/>
  <polygon points="100,55 138,78 138,122 100,145 62,122 62,78" fill="none" stroke="currentColor" stroke-width="1" opacity="0.6"/>
  <line x1="100" y1="18" x2="100" y2="55" stroke="currentColor" stroke-width="1" opacity="0.6"/>
  <line x1="170" y1="60" x2="138" y2="78" stroke="currentColor" stroke-width="1" opacity="0.6"/>
  <line x1="170" y1="140" x2="138" y2="122" stroke="currentColor" stroke-width="1" opacity="0.6"/>
  <line x1="100" y1="182" x2="100" y2="145" stroke="currentColor" stroke-width="1" opacity="0.6"/>
  <line x1="30" y1="140" x2="62" y2="122" stroke="currentColor" stroke-width="1" opacity="0.6"/>
  <line x1="30" y1="60" x2="62" y2="78" stroke="currentColor" stroke-width="1" opacity="0.6"/>
  <rect x="94" y="12" width="12" height="12" fill="currentColor"/>
  <rect x="164" y="54" width="12" height="12" fill="currentColor"/>
  <rect x="164" y="134" width="12" height="12" fill="currentColor"/>
  <rect x="94" y="176" width="12" height="12" fill="currentColor"/>
  <rect x="24" y="134" width="12" height="12" fill="currentColor"/>
  <rect x="24" y="54" width="12" height="12" fill="currentColor"/>
</svg>"""


def _circuit_svg(rotate: int) -> str:
    return f"""<svg viewBox="0 0 200 200" aria-hidden="true" style="transform:rotate({rotate}deg)">
  <path d="M20 170 L20 110 L80 110 L80 60 L150 60 L150 30" fill="none" stroke="currentColor" stroke-width="1.4"/>
  <path d="M40 170 L40 130 L100 130 L100 90 L170 90" fill="none" stroke="currentColor" stroke-width="1" opacity="0.55"/>
  <rect x="14" y="164" width="12" height="12" fill="currentColor"/>
  <rect x="74" y="104" width="12" height="12" fill="currentColor"/>
  <rect x="144" y="24" width="12" height="12" fill="currentColor"/>
  <rect x="94" y="84" width="10" height="10" fill="currentColor" opacity="0.75"/>
  <rect x="164" y="84" width="10" height="10" fill="currentColor" opacity="0.75"/>
  <circle cx="20" cy="170" r="4" fill="currentColor"/>
  <circle cx="150" cy="30" r="4" fill="currentColor"/>
</svg>"""


def motif_pair(index: int) -> str:
    """One .v3t-cat__visual's worth of decoration: a wireframe shape in one
    corner, a circuit trace in the other, rotated per section for variety
    without needing unique geometry per category."""
    wire_rot = (index * 47) % 360
    circuit_rot = (index * 83 + 15) % 360
    return f"""<div class="v3t-motif v3t-motif--wire" style="width:72%;height:72%;top:0;{'left' if index % 2 == 0 else 'right'}:0;">{_wireframe_svg(wire_rot)}</div>
      <div class="v3t-motif v3t-motif--circuit" style="width:60%;height:60%;bottom:0;{'right' if index % 2 == 0 else 'left'}:0;">{_circuit_svg(circuit_rot)}</div>"""


def hero_media(prefix: str, spec: dict) -> str:
    return (f'<div class="v3t-scene__media">'
            f'<img src="{prefix}{IMG}/{spec["file"]}" width="{spec["w"]}" height="{spec["h"]}" '
            f'alt="" decoding="async" fetchpriority="high" loading="eager"></div>')


def render_cat_section(index: int, s: dict) -> str:
    chips = "".join(f'<li class="v3t-chip">{esc(c)}</li>' for c in s["chips"])
    return f"""<section class="v3t-cat">
  <div class="v3t-grid-bg" aria-hidden="true"></div>
  <div class="v3t-cat__inner">
    <div class="v3t-cat__visual" aria-hidden="true">
      {motif_pair(index)}
    </div>
    <div class="v3t-cat__text">
      <p class="v3t-cat__phrase">{esc(s['phrase'])}</p>
      <p class="v3t-cat__body">{esc(s['body'])}</p>
      <ul class="v3t-chip-row">{chips}</ul>
    </div>
  </div>
</section>"""


def build_lang(lang: str, all_data: dict):
    d = all_data.get(lang)
    if d is None:
        return  # no content for this language yet; skip rather than publish a half page
    p = asset_root_prefix(1, lang)

    count_line = emphasize_number(esc(d["hero_count_label"]))
    flagship_title_html = wrap_nowrap(esc(d["flagship"]["title"]), FLAGSHIP_TITLE_NOWRAP.get(lang, ""))

    hero = f"""<div class="v3t-hero-shell">
  <section class="v3t-hero" aria-label="{esc(d['title'])}">
    <div class="v3t-hero__track" id="v3tTrack">
      <div class="v3t-hero__stage" id="v3tStage">

        <div class="v3t-scene v3t-scene--title" data-v3t-scene="0">
          <div class="v3t-scene__row">
            {hero_media(p, HERO_ILLUSTRATION)}
            <div class="v3t-scene__text">
              <span class="v3t-eyebrow">{esc(d['eyebrow'])}</span>
              <h1 class="v3t-word">V3</h1>
              <p class="v3t-subtitle">{esc(d['hero_subtitle'])}</p>
              <p class="v3t-count">{count_line}</p>
              <p class="v3t-lede">{esc(d['hero_lede'])}</p>
            </div>
          </div>
        </div>

        <div class="v3t-scene v3t-scene--flagship" data-v3t-scene="1">
          <div class="v3t-scene__row">
            {hero_media(p, LAUNCHER_PHOTO)}
            <div class="v3t-scene__text">
              <span class="v3t-eyebrow">{esc(d['flagship']['eyebrow'])}</span>
              <h2 class="v3t-flagship-title">{flagship_title_html}</h2>
              <p class="v3t-lede">{esc(d['flagship']['body'])}</p>
            </div>
          </div>
        </div>

        <span class="v3t-cue" aria-hidden="true"></span>
        <span class="v3t-progress" aria-hidden="true"><i></i></span>
      </div>
    </div>
  </section>
</div>"""

    cats = "\n".join(render_cat_section(i, s) for i, s in enumerate(d["sections"]))

    closing = f"""<section class="v3t-closing">
  <div class="v3t-closing__inner">
    <p class="v3t-closing__quality">{esc(d['closing']['quality_line'])}</p>
    <p class="v3t-closing__status">{esc(d['closing']['status_line'])} <a href="{LANG_PREFIX}changelog/">{esc(d['closing']['changelog_label'])}</a></p>
  </div>
</section>"""

    body = f"{hero}\n{cats}\n{closing}"

    og_image_url = f"{SITE_BASE_URL}/{IMG}/{OG_IMAGE}"
    extra_head = f'<link rel="stylesheet" href="{p}assets/css/v3-teaser.css">\n<script defer src="{p}assets/js/v3-teaser.js"></script>\n'

    html = page(
        lang=lang,
        section="v3/",
        title=d["title"],
        description=d["description"],
        active="v3",
        body=body,
        depth=1,
        extra_head=extra_head,
        og_image=og_image_url,
    )
    write_page(lang, "v3/", html)


def build():
    all_data = load_data()
    for lang in available_langs():
        build_lang(lang, all_data)


if __name__ == "__main__":
    build()
