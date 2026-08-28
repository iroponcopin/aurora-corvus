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

NOTE ON WORDS: the only text nodes this page emits are the product names
("Aurora Corvus"). Every screenshot carries alt="" and the stage is labelled
by the <h1>, so nothing here needs 13 translations — which is why the whole
`home` section of the language bundles was deleted along with the old copy.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from site_common import (  # noqa: E402
    SITE_TITLE, load_bundle, page, write_page, available_langs,
    asset_root_prefix,
)

# Every frame is the real Corvus 1.4.0 app, cropped to the window (the macOS
# desktop edge visible at the top/bottom of the raw captures is stripped) and
# re-encoded to WebP. Natural size is 1196x824 for all five, which is what the
# width/height attributes below advertise so nothing shifts while they load.
FRAME_W, FRAME_H = 1196, 824
FRAMES = {
    "home": "app-home.webp",          # "Update available", installed 2.4.6
    "settings": "app-settings.webp",
    "log": "app-log.webp",
    "updated": "app-updated.webp",    # "Up to date", installed 2.4.8
    "sheet": "app-sheet.webp",        # the detected-folder sheet, real blur
}


def frame_img(prefix: str, key: str, eager: bool = False) -> str:
    """One screenshot. alt="" throughout: these are presentation, the page's
    only actual content is the wordmark in the <h1>. That also keeps the film
    free of any string that would need translating into 13 languages."""
    loading = 'loading="eager" fetchpriority="high"' if eager else 'loading="lazy"'
    return (f'<img src="{prefix}assets/img/film/{FRAMES[key]}" alt="" '
            f'width="{FRAME_W}" height="{FRAME_H}" decoding="async" {loading}>')


def build_lang(lang):
    bundle = load_bundle(lang)
    p = asset_root_prefix(0, lang)

    body = f"""
<section class="film" aria-labelledby="filmWord">
  <div class="film__track" id="filmTrack">
    <div class="film__stage" id="filmStage">

      <!-- 1. the mark and the name resolve out of the dark -->
      <div class="film__scene film__scene--title" data-film-scene="0">
        <span class="film__mark" aria-hidden="true"></span>
        <h1 class="film__word" id="filmWord">{SITE_TITLE}</h1>
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
    html = page(
        lang=lang,
        section="",
        title="",
        description=bundle["ui"]["site_description"],
        active="home",
        body=body,
        depth=0,
    )
    write_page(lang, "", html)


def build():
    for lang in available_langs():
        build_lang(lang)


if __name__ == "__main__":
    build()
