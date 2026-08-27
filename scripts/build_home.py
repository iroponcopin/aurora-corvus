#!/usr/bin/env python3
"""Builds index.html (home page) for every language that has a bundle."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from site_common import (  # noqa: E402
    ROOT, MOD_ORDER, esc, page, write_page, load_bundle, available_langs,
    recipe_cat_index,
)


def load_versions():
    p = ROOT / "data" / "versions.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def load_latest_changelog_entry(lang, bundle):
    """Returns the newest entry, with translated strings merged in from the
    bundle (falling back to the JA structural file for release/date/type/
    mod_versions, which never need translation)."""
    p = ROOT / "data" / "changelog.json"
    if not p.exists():
        return None
    structural = json.loads(p.read_text(encoding="utf-8"))
    if not structural:
        return None
    translated_list = bundle.get("changelog") or []
    by_release_date = {(t["release"], t["date"]): t for t in translated_list}
    s = structural[-1]
    t = by_release_date.get((s["release"], s["date"]), s)
    merged = dict(s)
    merged.update({k: t[k] for k in ("title", "summary", "highlights") if k in t})
    return merged


def mod_card(bundle, m, versions):
    ui_mod = bundle["ui"]["mods"].get(m["key"], {})
    v = versions["mods"].get(m["key"]) if versions else None
    ver_html = f'<div class="card__meta">v{esc(v)}</div>' if v else ""
    idx = recipe_cat_index(m.get("cat"))
    href = "recipes/" if idx is None else f"recipes/#{idx}"
    return f"""<a class="card card--mod" href="{href}" style="--mod-color:{m['color']}">
      <h3>{esc(ui_mod.get('name', m['key']))}</h3>
      <p class="card__meta">{esc(ui_mod.get('tagline', ''))}</p>
      {ver_html}
    </a>"""


def feature_card(f):
    return f"""<a class="card" href="{esc(f['href'])}">
      <h3>{esc(f['title'])}</h3>
      <p>{esc(f['desc'])}</p>
      <p class="card__meta">{esc(f['cta'])} →</p>
    </a>"""


def latest_teaser(bundle, entry):
    if not entry:
        return ""
    from site_common import mod_badge, type_badge  # noqa: E402
    mods_html = "".join(mod_badge(bundle, mid, small=True) for mid in (entry.get("mod_versions") or {}))
    highlights = entry.get("highlights") or []
    li = "".join(f"<li>{esc(h)}</li>" for h in highlights[:4])
    ui = bundle["ui"]["common"]
    return f"""
    <div class="card" style="margin-top:28px;">
      <div class="badge-row">{type_badge(bundle, entry.get('type', 'release'))}
        <span class="timeline-entry__release">{esc(entry.get('release',''))}</span>
        <span class="card__meta">{esc(entry.get('date',''))}</span>
      </div>
      <h3 style="margin-top:0">{esc(ui['latest_update_heading'])} {esc(entry.get('title',''))}</h3>
      <p>{esc(entry.get('summary',''))}</p>
      <ul>{li}</ul>
      <div class="badge-row">{mods_html}</div>
      <p><a href="changelog/">{esc(ui['read_changelog'])}</a></p>
    </div>"""


def build_lang(lang):
    bundle = load_bundle(lang)
    home = bundle["home"]
    versions = load_versions()
    latest = load_latest_changelog_entry(lang, bundle)
    mc = versions["mc_version"] if versions else "26.2"

    mods_grid = "\n      ".join(mod_card(bundle, m, versions) for m in MOD_ORDER)
    features_html = "\n  ".join(feature_card(f) for f in home["features"])

    body = f"""
<section class="hero">
  <span class="hero__eyebrow">{esc(home['hero_eyebrow'])}</span>
  <h1>{esc(SITE_TITLE_FOR_H1)}</h1>
  <p class="lede">
    {esc(home['hero_lede_1'])}<strong>{esc(home['hero_lede_pack_name'])}</strong>{esc(home['hero_lede_2'])}
    <strong>{esc(home['hero_lede_mod_count'])}</strong>{esc(home['hero_lede_3'])}
    <strong>{esc(mc)}</strong>{esc(home['hero_lede_4'])}
  </p>
  <p class="callout callout--info">{esc(home['not_distributed_notice'])}</p>
  <div class="tag-row" style="margin-top:20px;">
    <a class="btn" href="recipes/">{esc(home['btn_recipes'])}</a>
    <a class="btn btn--ghost" href="changelog/">{esc(home['btn_changelog'])}</a>
    <a class="btn btn--ghost" href="guide/">{esc(home['btn_guide'])}</a>
  </div>
</section>
{latest_teaser(bundle, latest)}

<h2>{esc(home['mods_heading'])}</h2>
<p class="section-lede">{esc(home['mods_lede'])}</p>
<div class="grid grid--mods">
  {mods_grid}
</div>

<h2>{esc(home['features_heading'])}</h2>
<div class="grid" style="grid-template-columns:repeat(auto-fill,minmax(240px,1fr));">
  {features_html}
</div>

<h2>{esc(home['about_heading'])}</h2>
<p>{esc(home['about_p1'])}</p>
<p>{esc(home['about_p2'])}</p>
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


SITE_TITLE_FOR_H1 = "Aurora Corvus"


def build():
    for lang in available_langs():
        build_lang(lang)


if __name__ == "__main__":
    build()
