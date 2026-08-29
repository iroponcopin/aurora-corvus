#!/usr/bin/env python3
"""Builds index.html (home page) for every language.

The home page is deliberately almost wordless. Owner directive (2026-08):

    「Webサイトのホームに紹介映像を配置し、Aurora Curvus以外の文章を削除。
      Apple同様ここは非常に洗練された状態にします。現在はごちゃつき感が
      物凄いので。」

So everything that used to live here — the hero lede, the "not distributed"
callout, the CTA row, the latest-update teaser, the module grid, the feature
grid and the about paragraphs — is gone. What remains is the wordmark and a
scroll-driven film of Corvus, the desktop launcher.

KEPT ON PURPOSE, and not part of the 文章 the owner asked to delete:
  * the site header / mega-menu nav — the only route to Download, Recipes,
    Guide, Changelog... Removing it would leave every visitor stranded on a
    page with nowhere to go.
  * the footer — it carries the "unofficial / not affiliated with Mojang"
    notice.
Both are chrome supplied by site_common.page(); neither is body copy.

The film itself is markup + CSS + a few scroll-driven custom properties. There
is no video file, no canvas, no library — the same technique Apple's own
product pages use. See the "Film" block in assets/css/style.css and the film
module in assets/js/main.js. With JS disabled, or under
prefers-reduced-motion: reduce, the very same markup lays out as a static,
complete, fully legible gallery (the CSS default; the pinned stage is an
enhancement gated on `html.js` + `prefers-reduced-motion: no-preference`).

SCENE 0 — the opening beat. Owner directive (2026-08):

    「ホームではAurora Curvusのロゴを
      Appleイベントの時の様にアニメーショングラフィックを加えてください」

The mark and the name no longer merely fade up. A raked front of aurora light
crosses the frame and DEPOSITS the mark behind it, beak first and the wing
ribbons unfurling last; a blurred copy of the mark blooms and settles; a
specular rake crosses once; and the wordmark resolves one glyph at a time.
That is assets/css/hero-mark.css (all of the motion) plus
assets/js/hero-mark.js (the wordmark's per-glyph gradient slicing, which is
the one part that genuinely cannot be done in CSS — read either file's header
for why). Both are linked from THIS page only, via extra_head.

The extra markup below is inert everywhere the opening does not run: the
layer spans are `display: none` by default and the glyph spans are ordinary
inline text, so the no-JS and reduced-motion renderings are the same picture
they were before this beat existed.

NOTE ON WORDS: the only text nodes this page emits are the product names
("Aurora Corvus"). Every screenshot carries alt="" and the stage is labelled
by the <h1>, so nothing here needs 13 translations — which is why the whole
`home` section of the language bundles was deleted along with the old copy.
Splitting the wordmark into glyph spans does not change that: the <h1>'s text
content is still exactly "Aurora Corvus", and it carries an aria-label with
the same string so that no assistive technology can be tempted to announce it
one letter at a time.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from site_common import (  # noqa: E402
    SITE_TITLE, load_bundle, page, write_page, available_langs,
    asset_root_prefix, esc,
)

# Every frame is the real Corvus 1.5.1 app, cropped to the window (the macOS
# desktop edge visible at the top/bottom of the raw captures is stripped) and
# re-encoded to WebP. Natural size is 1196x824 for all five, which is what the
# width/height attributes below advertise so nothing shifts while they load.
#
# The frames are shot against a THROWAWAY home directory, never the machine's
# own: every path they render is on screen at readable size, so a capture made
# against a real home publishes that home's layout to the world. The 2026-08-28
# reshoot used /Users/Shared/player as $HOME with the pack at
# <home>/Library/Application Support/minecraft, and pointed the app at the live
# manifest so the URL in the Log frame is the real current one. Reshoot the
# same way — the pack rename ("Glimpse Alpha" -> "Alpha") will need one.
FRAME_W, FRAME_H = 1196, 824
FRAMES = {
    "home": "app-home.webp",          # "Update available", installed 2.4.8
    "settings": "app-settings.webp",
    "log": "app-log.webp",
    "updated": "app-updated.webp",    # "Up to date", installed 2.4.9
    "sheet": "app-sheet.webp",        # the detected-folder sheet, real blur
}


def frame_img(prefix: str, key: str, eager: bool = False) -> str:
    """One screenshot. alt="" throughout: these are presentation, the page's
    only actual content is the wordmark in the <h1>. That also keeps the film
    free of any string that would need translating into 13 languages."""
    loading = 'loading="eager" fetchpriority="high"' if eager else 'loading="lazy"'
    return (f'<img src="{prefix}assets/img/film/{FRAMES[key]}" alt="" '
            f'width="{FRAME_W}" height="{FRAME_H}" decoding="async" {loading}>')


# --- scene 0 ---------------------------------------------------------------
# The opening mark. `.film__mark` keeps every dimension, colour and scroll
# transform style.css already gives it; the nested spans are the extra light
# layers hero-mark.css composes the arrival out of, and they are display:none
# unless that file's `html.js` + `prefers-reduced-motion: no-preference` gate
# is satisfied. The three-deep halo is not over-engineering: CSS applies
# filters BEFORE masking on the same element, so the blur has to sit on an
# ancestor of the mask or the glow is clipped back to the mark's hard edge.
OPENING_MARK = """<span class="film__mark hm" aria-hidden="true">
          <span class="hm__bloom"></span>
          <span class="hm__halo"><span class="hm__halo-b"><span class="hm__halo-i"></span></span></span>
          <span class="hm__body">
            <span class="hm__plate"></span>
            <span class="hm__flow"></span>
            <span class="hm__rake"></span>
            <span class="hm__ambient"></span>
          </span>
        </span>"""


def wordmark(text: str) -> str:
    """The wordmark, one span per glyph, so the name can resolve letter by
    letter instead of as one block.

    Emitted at BUILD time rather than by hero-mark.js on purpose: the split
    then exists in the served HTML, so there is no moment where the DOM is
    rewritten under a running animation and nothing depends on a script to
    produce readable markup. hero-mark.js only decorates what is already here.

    Two details that are easy to get wrong:
      * each WORD is wrapped as well, and hero-mark.css gives that wrapper
        `white-space: nowrap`. Once the glyphs are inline-block, every glyph
        is its own line-break opportunity, so without this "Aurora" can wrap
        between the "r" and the "o" on a 375px phone.
      * the space between the words consumes an index of its own, so the
        stagger carries a beat of silence across the gap instead of running
        the two words together at an even tempo.
    """
    out = []
    i = 0
    words = text.split(" ")
    for w_index, w in enumerate(words):
        glyphs = "".join(
            f'<span class="hm-g" style="--i:{i + n}">{esc(ch)}</span>'
            for n, ch in enumerate(w)
        )
        i += len(w)
        out.append(f'<span class="hm-w">{glyphs}</span>')
        if w_index < len(words) - 1:
            out.append(" ")
            i += 1
    return "".join(out)


def build_lang(lang):
    bundle = load_bundle(lang)
    p = asset_root_prefix(0, lang)

    body = f"""
<section class="film" aria-labelledby="filmWord">
  <div class="film__track" id="filmTrack">
    <div class="film__stage" id="filmStage">

      <!-- 1. the mark and the name resolve out of the dark -->
      <div class="film__scene film__scene--title" data-film-scene="0">
        {OPENING_MARK}
        <h1 class="film__word" id="filmWord" aria-label="{esc(SITE_TITLE)}">{wordmark(SITE_TITLE)}</h1>
      </div>

      <!-- 2. the app arrives, with weight -->
      <div class="film__scene film__scene--arrive" data-film-scene="1">
        <figure class="film__frame">{frame_img(p, "home", eager=True)}</figure>
      </div>

      <!-- 3. its surfaces fan out: home, settings, log -->
      <!-- DOM order is the order the STATIC (no-JS / reduced-motion) gallery
           reads in; the pinned film sets its own z-index, so it is free. -->
      <div class="film__scene film__scene--stack" data-film-scene="2">
        <figure class="film__frame film__frame--front">{frame_img(p, "home")}</figure>
        <figure class="film__frame film__frame--back1">{frame_img(p, "settings")}</figure>
        <figure class="film__frame film__frame--back2">{frame_img(p, "log")}</figure>
      </div>

      <!-- 4. the update, told by a dissolve between two real states -->
      <div class="film__scene film__scene--update" data-film-scene="3">
        <div class="film__detail">
          <div class="film__detail-layer film__detail-layer--a">{frame_img(p, "home")}</div>
          <div class="film__detail-layer film__detail-layer--b">{frame_img(p, "updated")}</div>
          <span class="film__sweep" aria-hidden="true"></span>
        </div>
      </div>

      <!-- 5. the sheet, and the app's real backdrop blur behind it -->
      <div class="film__scene film__scene--sheet" data-film-scene="4">
        <figure class="film__frame film__frame--sharp">{frame_img(p, "home")}</figure>
        <figure class="film__frame film__frame--blurred">{frame_img(p, "sheet")}</figure>
      </div>

      <!-- 6. sign-off -->
      <div class="film__scene film__scene--sign" data-film-scene="5" aria-hidden="true">
        <span class="film__mark film__mark--sign"></span>
        <p class="film__word film__word--sign">{SITE_TITLE}</p>
      </div>

      <span class="film__cue" aria-hidden="true"></span>
      <span class="film__progress" aria-hidden="true"><i></i></span>
    </div>
  </div>
</section>
"""
    # Scene 0's opening beat, home page only. A page-scoped stylesheet
    # plus a deferred script,
    # both addressed through asset_root_prefix() rather than a hardcoded
    # "../" (non-ja languages sit one directory deeper — see the note on that
    # helper for the 404 a hardcoded prefix caused last time).
    extra_head = (
        f'<link rel="stylesheet" href="{p}assets/css/hero-mark.css">\n'
        f'<script defer src="{p}assets/js/hero-mark.js"></script>\n'
    )

    html = page(
        lang=lang,
        section="",
        title="",
        description=bundle["ui"]["site_description"],
        active="home",
        body=body,
        depth=0,
        extra_head=extra_head,
    )
    write_page(lang, "", html)


def build():
    for lang in available_langs():
        build_lang(lang)


if __name__ == "__main__":
    build()
