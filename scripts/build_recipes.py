#!/usr/bin/env python3
"""Builds recipes/index.html for every language. The card grid, tabs, and
crafting-grid modal are all rendered client-side by assets/js/recipes.js,
which fetches the language-neutral data/recipes.json (grids/images, shared
across all languages) plus, for any lang != ja, a small per-language overlay
data/recipes.<lang>.json (translated names/categories/how-to-use text) --
see scripts/build_recipe_overlays.py."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from site_common import ROOT, esc, page, write_page, load_bundle, available_langs, asset_root_prefix  # noqa: E402


def build_lang(lang):
    bundle = load_bundle(lang)
    ui = bundle["ui"]
    c = ui["common"]
    recipes = json.loads((ROOT / "data" / "recipes.json").read_text(encoding="utf-8"))
    total = recipes["total"]
    intro = c["recipes_intro"].replace("{count}", str(total))

    body = f"""
<div class="hero">
  <span class="hero__eyebrow">{esc(ui['page_titles']['recipes'])}</span>
  <h1>{esc(ui['page_titles']['recipes'])}</h1>
  <p class="lede">{esc(intro)}</p>
</div>

<noscript>
  <p class="callout callout--warn">{esc(c['js_required'])}</p>
</noscript>

<div id="recipeApp" hidden>
  <div class="filter-bar">
    <input type="search" id="recipeSearch" placeholder="{esc(c['search_placeholder_recipes'])}" aria-label="{esc(c['search_placeholder_recipes'])}">
  </div>
  <div class="tab-bar" id="recipeTabs" role="tablist"></div>
  <p class="recipe-count" id="recipeCount"></p>
  <p id="recipeEmpty" class="empty-state" hidden>{esc(c['empty_recipes'])}</p>
  <div class="grid grid--recipes" id="recipeGrid"></div>
  <div id="guidePane" hidden></div>
</div>

<div class="recipe-modal-backdrop" id="recipeModalBackdrop">
  <div class="recipe-modal" role="dialog" aria-modal="true" aria-labelledby="recipeModalTitle">
    <button class="recipe-modal__close" id="recipeModalClose" aria-label="{esc(c['close'])}">&times;</button>
    <div id="recipeModalBody"></div>
  </div>
</div>
<script>
  window.SITE_LANG = {json.dumps(lang)};
  window.SITE_STRINGS = {json.dumps({
      "tabAll": c["tab_all"], "tabGuides": c["tab_guides"],
      "howToObtain": c["how_to_obtain"], "noRecipeInfo": c["no_recipe_info"],
      "countSuffix": c["count_suffix"], "loadError": c["data_load_error"],
      "ioIn": c["guide_io_in"], "ioOut": c["guide_io_out"],
  }, ensure_ascii=False)};
</script>
"""
    html = page(
        lang=lang,
        section="recipes/",
        title=ui["page_titles"]["recipes"],
        description=ui["page_descriptions"].get("recipes", ui["site_description"]),
        active="recipes",
        body=body,
        depth=1,
        extra_head=f'<script defer src="{asset_root_prefix(1, lang)}assets/js/recipes.js"></script>\n',
    )
    write_page(lang, "recipes/", html)


def build():
    for lang in available_langs():
        build_lang(lang)


if __name__ == "__main__":
    build()
