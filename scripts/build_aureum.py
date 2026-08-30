#!/usr/bin/env python3
"""Builds aureum/index.html (the Aureum landing page) for every language.

Aureum is a real, shipped, separately-versioned mod (its own repo, its own
download, reviewed and already shipped as a card on the Download page — see
build_download.py's _aureum_section_html()). This page is a PERMANENT premium
showcase for it, not a "coming soon" teaser: unlike the old V3 teaser
(scripts/build_v3_teaser.py, deleted the day V3 shipped — see git history),
there is no removal checklist here and none belongs here.

Owner directive (paraphrased, 2026-08): build a luxury announcement page for
Aureum from the reference artwork in Design/image.jpg, using the same
technology as the home page (the pinned scroll-driven "film"), at an
"extremely high level."

--------------------------------------------------------------------------
Colour palette — MEASURED, not guessed
--------------------------------------------------------------------------
Every colour in assets/css/aureum.css's --au-* tokens was sampled from real
pixels in Design/image.jpg with Pillow, not eyeballed, per this project's own
established standard for reference-image work. The sampling (image is
1168x784):

  --au-bg          #030201   mean of ~1,270 random points OUTSIDE the beam/
                              monogram region (background corners + margins)
  --au-gold-shadow #1a1106   mean of monogram-region pixels with luminance
                              sum in (15, 120) -- the deep ambient shadow
                              gold at the shape's own edges
  --au-gold-dim    #46331a   mean of the upper beam column (x 0.35-0.65,
                              y 0.0-0.15), pixels with luminance sum > 60
  --au-gold        #b08741   mean of monogram-region pixels with luminance
                              sum in (200, 650) -- the metal's own midtone,
                              used as the page's primary accent
  --au-gold-bright #f3e3a5   mean of the AUREUM wordmark's own glyph pixels
                              with luminance sum > 150 -- the specular
                              highlight tone, used for headings/emphasis

Contrast (WCAG relative luminance formula, computed against --au-bg
#030201): --au-gold 6.31:1, --au-gold-bright 16.13:1, --au-text (#ece3d1, a
warm ivory chosen for body copy so long paragraphs don't run in shouting-gold)
16.26:1, --au-text-muted (#c9b98f) 10.68:1. All four clear WCAG AA (4.5:1) at
every size; all but --au-gold clear AAA (7:1). Button text (--au-contrast
#0a0704 on a --au-gold/--au-gold-bright fill) is 6.1-6.4:1.

--------------------------------------------------------------------------
The hero visual — real artwork, not a from-scratch recreation
--------------------------------------------------------------------------
assets/img/aureum/monogram.webp is a crop of Design/image.jpg itself (box
x 0.26-0.76, y 0.13-0.71 of the 1168x784 source — the "A" monogram plus its
own beam rays and particle dust, deliberately excluding the AUREUM wordmark
and tagline text below it, which this page re-sets as real, translatable
HTML text instead of baking English words into a raster). The black
background was keyed to transparent with a per-pixel alpha ramp on
perceptual luminance (alpha 0 at/under luminance 6, alpha 255 at/over
luminance 70, gamma 0.85 to keep the glow's own natural falloff rather than
a hard silhouette edge) -- see the project's Aureum work session for the
exact numpy one-liner. This is a deliberate choice over redrawing the mark in
CSS/SVG: the reference artwork already has convincing liquid-metal
highlights and organic-curve shading, and the owner's directive was to use
that art, not merely take inspiration from it. Everything else on the page
(the ambient glow wash, the drifting particle dust, the spotlight-adjacent
gradients) IS recreated in CSS, for the usual reason -- resolution
independence, and transform/opacity-only animation. See assets/css/
aureum.css's own header for the full reasoning split.

assets/img/aureum/og-aureum.jpg is a 1200x630 "cover" crop of the FULL
original artwork (monogram + wordmark + tagline, exactly as the owner
supplied it) for the Open Graph / Twitter card image.

--------------------------------------------------------------------------
Content — every claim is a real, measured fact
--------------------------------------------------------------------------
Sourced from aureum-src's own README.md and docs/BENCHMARKS.md — the SAME
facts already reviewed and shipped in build_download.py's
_aureum_section_html() (aureum_heading/aureum_body/aureum_cta/aureum_note in
data/i18n/*.json's "download" block, reused verbatim here rather than
re-authored, so this page can never quietly drift from the numbers the
Download page already promises): the -6.3 MB (loaded-chunk heap) and
-17.2 MB (after generating new terrain) deltas, "not a Sodium replacement",
and the two client-side toggles that ship off and unmeasured. This script
adds a small amount of genuinely NEW copy beyond that (the "every
optimisation is optional" config note, from the README's config section, and
the plain requirements line) -- translated into all 13 languages in data/
i18n/*.json's new "aureum_page" block (NOT an 11-language English-fallback:
every language here is a real, authored translation, matching the standard
the aureum_* keys on the Download page already set, not the older
AUTHORING_LANG-with-fallback pattern build_launcher.py uses for
launcher_page). "Aureum" the brand name is the one exception -- see
site_common.NAV_LABEL_FALLBACK's comment for why a proper noun is not
translated into 11 more scripts.

--------------------------------------------------------------------------
Motion
--------------------------------------------------------------------------
A pinned two-beat "film" (hero, then the headline stats) using the exact
same technique as the home page's own film — a sticky stage driven by
scroll-linked CSS custom properties written once per rAF frame, transform/
opacity only, a complete static fallback under `prefers-reduced-motion:
reduce` or with JS disabled. See assets/css/aureum.css and assets/js/
aureum.js for the mechanism, and build_home.py / the "Film" block in
assets/css/style.css for the original this was modelled on. Neither the
home page's film markup, CSS, nor JS is touched by this file — same
reasoning the (deleted) V3 teaser gave for its own separate v3-teaser.css/js.

The stat tiles, config/requirements sections, and CTA below the pinned film
are plain `main > section` elements (via .au-section, a direct child of
DIRECT children of <main> (no wrapping div -- see the body-assembly comment
in build_lang() below for why) so they pick up the site's existing
scroll-entrance reveal (main.js's REVEAL_SELECTOR + .reveal in style.css) at
zero extra cost, the same "reuse what's already there" convention the V3
teaser used for its own category sections.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from site_common import (  # noqa: E402
    esc, page, write_page, load_bundle, available_langs, load_bundle as _lb,
    asset_root_prefix, SITE_BASE_URL,
)
from build_download import _aureum_facts  # noqa: E402  (single source of truth
    # for "which jar is current" -- see site_common.py's own comment on why
    # find_launcher_jars()/newest_launcher_jar() exist instead of a second
    # private copy of this logic; build_download.py's is a script but is
    # import-safe, guarded by `if __name__ == "__main__":`)

IMG = "assets/img/aureum"
OG_IMAGE = "og-aureum.jpg"
MONOGRAM = {"file": "monogram.webp", "w": 584, "h": 455}

# Technical requirements — universal (version numbers, product names), so
# unlike everything else on this page these are NOT run through translation;
# see aureum-src/README.md's own opening lines for the source facts.
REQUIREMENTS = ["Minecraft 26.2 (Fabric)", "Fabric Loader 0.19.3+", "Fabric API", "Java 25+"]

# The two measured memory deltas, reproduced exactly from aureum-src/docs/
# BENCHMARKS.md (resident dedupe+detector pair, and the genrun TTL pair).
# Universal (a number + a unit), so also not translated — only the LABEL
# next to each one is (aureum_page.stat_heap_label / stat_gen_label below).
STAT_HEAP_VALUE = "−6.3 MB"
STAT_GEN_VALUE = "−17.2 MB"


def wordmark(text: str) -> str:
    """"AUREUM" split into one span per glyph so the per-glyph reveal stagger
    in aureum.css (.au-g, --i-indexed animation-delay) has something to
    stagger. Emitted at BUILD time, same discipline as build_home.py's own
    wordmark(): the split exists in the served HTML, so nothing depends on a
    script to produce readable markup -- hero-mark.js-style helpers only ever
    decorate what is already there. "Aureum" is one word, so (unlike
    build_home's version) there is no inter-word space to account for."""
    glyphs = "".join(
        f'<span class="au-g" style="--i:{i}">{esc(ch)}</span>' for i, ch in enumerate(text)
    )
    return f'<span class="au-g-word">{glyphs}</span>'


def _stat(value: str, label: str) -> str:
    return (f'<div class="au-stat"><p class="au-stat__value">{esc(value)}</p>'
            f'<p class="au-stat__label">{esc(label)}</p></div>')


def build_lang(lang: str, aureum):
    bundle = load_bundle(lang)
    ui = bundle["ui"]
    dl = bundle["download"]
    ap = bundle.get("aureum_page")
    if not ap:
        raise SystemExit(
            f"ERROR: data/i18n/{lang}.json has no 'aureum_page' block. Every one of the 13 "
            f"language bundles must carry a real translation for this page (see "
            f"build_aureum.py's header) -- there is no English-fallback path for it, on "
            f"purpose, so a missing block must stop the build rather than quietly publish "
            f"English prose at /{lang}/aureum/.")
    p = asset_root_prefix(1, lang)

    monogram_html = (
        f'<span class="au-hero__monogram"><img src="{p}{IMG}/{MONOGRAM["file"]}" '
        f'width="{MONOGRAM["w"]}" height="{MONOGRAM["h"]}" alt="" decoding="async" '
        f'fetchpriority="high" loading="eager"></span>'
    )

    hero = f"""<div class="au-film-shell">
  <div class="au-film">
    <div class="au-film__track" id="auTrack">
      <div class="au-film__stage" id="auStage">

        <div class="au-film__scene au-film__scene--hero" data-au-scene="0">
          <div class="au-hero">
            <div class="au-hero__ambient" aria-hidden="true"></div>
            <div class="au-hero__motes" aria-hidden="true">
              <span class="au-hero__mote"></span><span class="au-hero__mote"></span>
              <span class="au-hero__mote"></span><span class="au-hero__mote"></span>
              <span class="au-hero__mote"></span><span class="au-hero__mote"></span>
            </div>
            <div class="au-hero__inner">
              {monogram_html}
              <h1 class="au-word" aria-label="Aureum">{wordmark("AUREUM")}</h1>
              <p class="au-tagline">{esc(ap['tagline'])}</p>
            </div>
          </div>
        </div>

        <div class="au-film__scene au-film__scene--stats" data-au-scene="1">
          <div class="au-stats">
            {_stat(STAT_HEAP_VALUE, ap['stat_heap_label'])}
            {_stat(STAT_GEN_VALUE, ap['stat_gen_label'])}
            {_stat(ap['stat_mspt_value'], ap['stat_mspt_label'])}
          </div>
        </div>

        <span class="au-cue" aria-hidden="true"></span>
        <span class="au-progress" aria-hidden="true"><i></i></span>
      </div>
    </div>
  </div>
</div>"""

    intro_section = f"""<section class="au-section">
  <div class="au-section__inner au-section__inner--wide">
    <h2>{esc(dl.get('aureum_heading', 'Aureum'))}</h2>
    <p>{esc(dl.get('aureum_body', ''))}</p>
    <div class="au-note">{esc(dl.get('aureum_note', ''))}</div>
  </div>
</section>"""

    config_section = f"""<section class="au-section">
  <div class="au-section__inner">
    <h2>{esc(ap['section_config'])}</h2>
    <p>{esc(ap['config_body'])}</p>
  </div>
</section>"""

    req_items = "".join(f"<li>{esc(r)}</li>" for r in REQUIREMENTS)
    requirements_section = f"""<section class="au-section">
  <div class="au-section__inner">
    <h2>{esc(ap['section_requirements'])}</h2>
    <ul class="au-requirements">{req_items}</ul>
  </div>
</section>"""

    version_badge = ""
    cta_primary = ""
    if aureum is not None:
        jar_href = f"{p}downloads/{aureum['file_name']}"
        version_label = esc(dl.get('version_label', 'Version'))
        version_badge = (f'<p class="au-closing" style="margin-bottom:0">'
                          f'{version_label} {esc(aureum["version"])} · SHA-256 '
                          f'<code>{esc(aureum["sha256"][:16])}…</code></p>')
        cta_primary = (f'<a class="au-btn au-btn--fill" href="{esc(jar_href)}" download>'
                        f'{esc(dl.get("aureum_cta", "Download Aureum"))}</a>')
    cta_secondary = f'<a class="au-btn au-btn--ghost" href="{p}download/#aureum">{esc(ap["cta_secondary"])}</a>'

    cta_section = f"""<section class="au-section">
  <div class="au-section__inner">
    <div class="au-cta-row">
      {cta_primary}
      {cta_secondary}
    </div>
    {version_badge}
    <p class="au-closing">{esc(ap['closing_line'])}</p>
  </div>
</section>"""

    # Deliberately NOT wrapped in one enclosing <div> -- style.css's own
    # scroll-entrance reveal system (main.js's REVEAL_SELECTOR) only ever
    # matches elements that are DIRECT children of <main> ("main > section",
    # "main > .hero", ...). Wrapping everything in a div would silently opt
    # every section below the pinned film out of that reveal -- no error, no
    # visual breakage, just a page that never gets the fade-up-on-scroll
    # treatment the rest of the site has. See aureum.css's header for how
    # the shared --au-* colour tokens still reach every one of these
    # siblings without a wrapping element: `main:has(> .au-film-shell)`
    # defines them on <main> itself (the same :has() trick style.css already
    # uses for `main:has(> .film)`), so they cascade to every child of
    # <main> normally, sibling or not.
    body = f"""
{hero}
{intro_section}
{config_section}
{requirements_section}
{cta_section}
"""

    extra_head = (
        f'<link rel="stylesheet" href="{p}assets/css/aureum.css">\n'
        f'<script defer src="{p}assets/js/aureum.js"></script>\n'
    )

    title = ui["page_titles"].get("aureum", "Aureum")
    description = ui["page_descriptions"].get("aureum", dl.get("aureum_body", ""))
    og_image_url = f"{SITE_BASE_URL}/{IMG}/{OG_IMAGE}"

    html = page(
        lang=lang,
        section="aureum/",
        title=title,
        description=description,
        active="aureum",
        body=body,
        depth=1,
        extra_head=extra_head,
        og_image=og_image_url,
    )
    write_page(lang, "aureum/", html)


def build():
    aureum = _aureum_facts()
    if aureum is None:
        print("  NOTE: downloads/ has no aureum-*.jar yet -- the page will publish without a "
              "direct download button (the same 'optional in every sense' fallback "
              "build_download.py's _aureum_section_html() uses).")
    for lang in available_langs():
        build_lang(lang, aureum)


if __name__ == "__main__":
    build()
