#!/usr/bin/env python3
"""Builds v4/index.html (the V4 update teaser) for every language.

============================================================================
THIS PAGE IS TEMPORARY. Read this before touching anything else in here.

V4 is a real upcoming mod-pack update that has not shipped yet. This page
exists only as a "coming soon" announcement for the interim, per owner
directive (2026-09-01: 「V3の時と同様に期間限定で告知されます」). Once V4
actually ships, the whole page must come down. When that day comes, deletion
is exactly these six steps and nothing else:

  1. Delete this file (scripts/build_v4_teaser.py).
  2. Delete assets/img/v4-teaser/ (sheet-1..3.webp, og-v4-teaser.jpg),
     assets/audio/v4-teaser/ (theme.opus, theme.m4a),
     assets/css/v4-teaser.css and assets/js/v4-teaser.js.
  3. Delete data/v4_teaser.json.
  4. Remove the "v4" entry from scripts/site_common.py: the ("v4", "v4/")
     tuple in NAV_SECTIONS, the "v4" string in NAV_SOLO, and the
     NAV_LABEL_FALLBACK["v4"] line.
  5. Remove "build_v4_teaser.py" from scripts/build.py's BUILD_SCRIPTS list.
  6. `rm -rf v4 */v4` from the repo root, then re-run
     `python3 scripts/build.py`. The generator never deletes stale output on
     its own, so the removal has to do it -- V3's own documented removal was
     incomplete in three places for exactly this class of reason, and that is
     recorded in commit e021c79.

That is the whole footprint. This page is deliberately kept out of the
general-purpose i18n bundles (data/i18n/*.json) and out of the shared
assets/css/style.css / assets/js/main.js specifically so removal is exactly
the steps above, not an archaeology dig through shared files for orphaned
strings or rules once V4 ships and this announcement stops being true.
============================================================================

Content: data/v4_teaser.json, one block per language, written for this page
alone. Sourced from Update/V4_Update.md's own twenty numbered modules; the
count and the numbering are copied from that document, not invented here.

Artwork: the owner's three V4WEB sheets (Design/V4WEB{,2,3}.png), converted
to WebP. They cover 17 of the 20 modules; the remaining three are listed in
the index below the sheets and marked as not yet illustrated rather than
quietly omitted -- a grid that shows 17 items under the heading "the twenty
modules" is a page that lies about its own subject.

Music: the owner supplied Music/video.mp4 and asked for it to play while the
V4 tab is open, with a mute button (「崩壊スターレイルなどと似た様な形で公式
ページでは音楽が流れるのと同じ仕様です」). The audio stream is extracted to
assets/audio/v4-teaser/theme.opus (+ .m4a for Safari) -- see
assets/js/v4-teaser.js for the autoplay-policy handling, which is the whole
difficulty: no browser will start audible sound before a user gesture, so a
naive autoplay attempt yields a page that is silently mute for most visitors
while the button claims the music is on.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from site_common import (  # noqa: E402
    ROOT, esc, page, write_page, available_langs, asset_root_prefix,
)

DATA_PATH = ROOT / "data" / "v4_teaser.json"
IMG = "assets/img/v4-teaser"
AUDIO = "assets/audio/v4-teaser"
OG_IMAGE = "og-v4-teaser.jpg"

#: The sheets, in page order. Sizes are the real pixel sizes of the shipped
#: WebP files -- written here so the markup can carry width/height and the
#: browser reserves the box before the image lands (no layout shift).
SHEETS = [
    {"file": "sheet-1.webp", "w": 1408, "h": 768},
    {"file": "sheet-2.webp", "w": 1408, "h": 768},
    {"file": "sheet-3.webp", "w": 1408, "h": 768},
]

#: Sourced from Update/V4_Update.md. Never re-typed anywhere else on the page:
#: every "20" a visitor reads comes from len(modules) in the data file.
MODULE_COUNT_SOURCE = "Update/V4_Update.md"


def _load():
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    modules = data["modules"]
    if len(modules) != 20:
        raise SystemExit(
            f"v4 teaser: data/v4_teaser.json lists {len(modules)} modules, but "
            f"{MODULE_COUNT_SOURCE} specifies 20. The page's headline count is derived "
            f"from this list, so a mismatch would put a wrong number in 13 languages."
        )
    if not any(m["sheet"] == 0 for m in modules):
        raise SystemExit(
            "v4 teaser: every module claims to be illustrated. The three sheets cover 17 of "
            "20; if that ever becomes true the 'artwork to follow' wording below must go too, "
            "so this fails rather than shipping a stale caveat."
        )
    for s in (1, 2, 3):
        if not any(m["sheet"] == s for m in modules):
            raise SystemExit(f"v4 teaser: no module is filed under sheet {s}, so that sheet's "
                             f"caption would describe nothing.")
    return data, modules


def _audio_block(t, prefix):
    """The music player + its control.

    The <audio> element carries BOTH sources: Opus is smaller and is what
    Chrome/Firefox/Edge take; Safari has never shipped Opus-in-Ogg, so the
    AAC file is not a nicety, it is the only thing Safari can play.
    """
    return f"""
<div class="v4t-audio" data-v4t-audio>
  <audio id="v4t-theme" loop preload="none" playsinline>
    <source src="{prefix}{AUDIO}/theme.opus" type="audio/ogg; codecs=opus">
    <source src="{prefix}{AUDIO}/theme.m4a" type="audio/mp4; codecs=mp4a.40.2">
  </audio>
  <button type="button" class="v4t-audio-btn" data-v4t-toggle
          aria-pressed="false"
          data-label-on="{esc(t['audio_on'])}"
          data-label-off="{esc(t['audio_off'])}"
          aria-label="{esc(t['audio_off'])}">
    <span class="v4t-audio-icon" aria-hidden="true">
      <svg viewBox="0 0 24 24" width="18" height="18" fill="none"
           stroke="currentColor" stroke-width="1.8"
           stroke-linecap="round" stroke-linejoin="round">
        <path d="M4 9.5h3.2L12 5.6v12.8L7.2 14.5H4z"></path>
        <g class="v4t-wave"><path d="M15.6 9.4a3.6 3.6 0 0 1 0 5.2"></path>
          <path d="M18.1 7.2a7 7 0 0 1 0 9.6"></path></g>
        <g class="v4t-cross"><path d="M15.8 9.8l4.6 4.6"></path>
          <path d="M20.4 9.8l-4.6 4.6"></path></g>
      </svg>
    </span>
    <span class="v4t-audio-text" data-v4t-label>{esc(t['audio_off'])}</span>
  </button>
</div>"""


def _sheet_section(lang, t, sheet_meta, sheet_text, modules, index, prefix):
    sep = "、" if lang in _IDEOGRAPHIC_COMMA_LANGS else ", "
    listed = sep.join(esc(m["name"]) for m in modules if m["sheet"] == index)
    return f"""
<section class="v4t-sheet">
  <div class="v4t-sheet-head">
    <p class="v4t-eyebrow">{esc(sheet_text['eyebrow'])}</p>
    <h2>{esc(sheet_text['title'])}</h2>
    <p class="v4t-sheet-body">{esc(sheet_text['body'])}</p>
  </div>
  <figure class="v4t-figure">
    <img src="{prefix}{IMG}/{sheet_meta['file']}"
         width="{sheet_meta['w']}" height="{sheet_meta['h']}"
         loading="lazy" decoding="async"
         alt="{esc(sheet_text['alt'])}">
    <figcaption>{listed}</figcaption>
  </figure>
</section>"""


#: Languages that write lists with an ideographic comma rather than ", ".
#: Getting this wrong is not a crash, it is a page that reads as though it
#: were machine-translated -- which is the one thing a launch announcement
#: cannot look like.
_IDEOGRAPHIC_COMMA_LANGS = {"ja", "zh"}


def _module_index(lang, t, modules):
    pending = [m["name"] for m in modules if m["sheet"] == 0]
    sep = "、" if lang in _IDEOGRAPHIC_COMMA_LANGS else ", "
    note = t["modules_note"].replace("{names}", sep.join(pending))
    items = []
    for m in modules:
        cls = "v4t-mod" if m["sheet"] else "v4t-mod v4t-mod-pending"
        badge = ("" if m["sheet"] else
                 f'<span class="v4t-pending">{esc(t["pending_label"])}</span>')
        items.append(
            f'<li class="{cls}"><span class="v4t-mod-no">{m["no"]:02d}</span>'
            f'<span class="v4t-mod-name">{esc(m["name"])}</span>{badge}</li>')
    return f"""
<section class="v4t-index">
  <h2>{esc(t['modules_title'])}</h2>
  <p class="v4t-index-note">{esc(note)}</p>
  <ol class="v4t-mod-list">
    {"".join(items)}
  </ol>
</section>"""


def build_lang(lang, data, modules):
    t = data[lang]
    prefix = asset_root_prefix(1, lang)
    # Deliberately NOT wrapped in one enclosing <div>, and no element here
    # carries class="reveal" by hand. Both are traps this repo has already
    # documented (see build_aureum.py's note above its `body =`):
    #
    #   * main.js's REVEAL_SELECTOR only matches DIRECT children of <main>
    #     ("main > section", ...). A wrapper opts every section out of the
    #     scroll-entrance reveal -- silently.
    #   * main.js ADDS the .reveal class itself. Writing it into the markup
    #     applies style.css's `opacity: 0` to an element the observer never
    #     manages, so it never fades in. The first version of this page did
    #     both at once and rendered a blank column below the hero.
    #
    # The --v4t-* tokens reach these siblings via `main:has(> .v4t-hero)` in
    # v4-teaser.css -- the same :has() trick aureum.css uses.
    body = [
        _audio_block(t, prefix),
        f"""
<header class="v4t-hero">
  <p class="v4t-eyebrow v4t-eyebrow-hero">{esc(t['eyebrow'])}</p>
  <p class="v4t-hero-sub">{esc(t['hero_subtitle'])}</p>
  <h1 class="v4t-title"><span class="v4t-title-mark">V4</span></h1>
  <p class="v4t-count">{esc(t['hero_count_label'])}</p>
  <p class="v4t-lede">{esc(t['hero_lede'])}</p>
  <p class="v4t-audio-hint">{esc(t['audio_hint'])}</p>
</header>""",
    ]
    for i, meta in enumerate(SHEETS, start=1):
        body.append(_sheet_section(lang, t, meta, t["sheets"][i - 1], modules, i, prefix))
    body.append(_module_index(lang, t, modules))
    body.append(f"""
<section class="v4t-closing">
  <p class="v4t-status">{esc(t['closing_status'])}</p>
  <p class="v4t-cta"><a class="v4t-link" href="../changelog/"
     >{esc(t['closing_changelog'])}</a></p>
</section>""")

    extra_head = (
        f'<link rel="stylesheet" href="{prefix}assets/css/v4-teaser.css">\n'
        f'<script defer src="{prefix}assets/js/v4-teaser.js"></script>'
    )
    return page(
        lang=lang, section="v4/", title=t["title"], description=t["description"],
        active="v4", body="\n".join(body), depth=1,
        extra_head=extra_head, og_image=f"{IMG}/{OG_IMAGE}",
    )


def main():
    data, modules = _load()
    langs = available_langs()
    built = 0
    for lang in langs:
        if lang not in data:
            raise SystemExit(
                f"v4 teaser: data/v4_teaser.json has no block for '{lang}'. This page is a "
                f"public announcement; falling back to Japanese for one language would be a "
                f"silent regression, so this fails instead."
            )
        write_page(lang, "v4/", build_lang(lang, data, modules))
        built += 1
    if built == 0:
        raise SystemExit("v4 teaser: built ZERO pages; available_langs() returned nothing.")
    print(f"v4 teaser: {built} languages, {len(modules)} modules, "
          f"{sum(1 for m in modules if m['sheet'])} illustrated")


if __name__ == "__main__":
    main()
