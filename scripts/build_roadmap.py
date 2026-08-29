#!/usr/bin/env python3
"""Builds roadmap/index.html for every language that has a bundle.

Structured deliberately like build_changelog.py: data/roadmap.ja.json is the
STRUCTURAL source of truth — which cards exist, in what order, and what
status each one carries — and a language bundle supplies only TRANSLATED
prose, matched card-by-card on a stable `key`. A language with no
translation for a card falls back to the Japanese text rather than rendering
whatever its own bundle happens to still hold.

⚠ That fallback is not a nicety. It is the fix for how this page went wrong.
  The page used to render `bundle["roadmap"]` outright, with no key match
  against any source at all. So when the Japanese source was rewritten, the
  other twelve languages went on rendering their OWN older translation, and
  nothing in the build could tell that they had gone stale. As of
  2026-08-29 all thirteen languages were still announcing
  「V2.2(次回。まだ着手前…)」 — V2.2 as unstarted future work — while
  V2.2.0, V2.2.1, V2.4.x and V2.5.1 had all shipped; and all thirteen were
  still calling five weather systems 「どれも構想段階です」 while this same
  site's own feature page documented those five as enabled by default, with
  measured numbers read out of the mod source. Keying the cards means a
  rewrite of the Japanese source can no longer leave twelve languages
  quietly serving the old story: the worst case is now Japanese text on a
  non-Japanese page, which is visible, instead of a fluent translation of
  something untrue, which is not.

The page's intro and warning line follow the same rule, and for the same
reason: ui.common.roadmap_intro / roadmap_warning are translated in all
thirteen bundles, but their content ("このページの内容はまだ実装・配布され
ていません" — nothing on this page has been implemented or shipped) stopped
being true the moment the page started reporting what had actually shipped.
The data file supplies its own intro/warning, and the bundle's ui strings
are only the last-resort fallback.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from site_common import (  # noqa: E402
    ROOT, NAV_SECTIONS, esc, page, write_page, load_bundle, available_langs,
    fill_placeholders,
)

SOURCE = ROOT / "data" / "roadmap.ja.json"

# Every card carries a status, and the status decides the badge colour. Only
# two colours are used on purpose — green for "this is real, you can play it"
# and blue for "this is not in your game yet" — because that is precisely the
# distinction the old page got wrong (four shipped releases wearing 計画中).
# The finer shade ("next up" vs "not started") is carried by the card's own
# badge TEXT, which travels with the card through translation.
#
# Unknown statuses stop the build rather than defaulting: a typo'd status
# silently falling back to "planned" would recreate the original defect
# exactly — shipped work rendered as a plan.
STATUS_BADGE_CLASS = {
    "shipped": "type-release",
    "next": "type-visual",
    "unstarted": "type-visual",
}

# Links out of a card. Language-RELATIVE, so "../v3/" from /roadmap/ reaches
# /v3/ and from /en/roadmap/ reaches /en/v3/. This is NOT asset_root_prefix()
# — that one resolves to the SITE root, which for a non-Japanese language is
# one level further up and would send every reader of the other twelve
# languages to the Japanese page. (Same convention as build_download.py's
# `<a href="../changelog/">`, and the same thing site_common.page() computes
# for itself as lang_prefix = _prefix(depth) with depth=1.)
LANG_PREFIX = "../"

_KNOWN_SLUGS = {slug for _key, slug in NAV_SECTIONS if slug}


def _load_source() -> dict:
    """The Japanese source, normalised to {"intro", "warning", "plans"}.

    A bare list is still accepted (that was the shape before this page was
    rewritten) so nothing breaks if an older data file is restored.
    """
    if not SOURCE.exists():
        raise SystemExit(
            f"ERROR: {SOURCE} does not exist. The roadmap page is built FROM that file - "
            f"without it every language would publish an empty roadmap with no error at all, "
            f"which is worse than not publishing the page.")
    raw = json.loads(SOURCE.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        raw = {"plans": raw}
    plans = raw.get("plans") or []
    if not plans:
        raise SystemExit(
            f"ERROR: {SOURCE} lists no roadmap cards. An empty roadmap page is indistinguishable "
            f"from a broken build - if the roadmap is genuinely empty, say so in a card.")
    return {"intro": raw.get("intro"), "warning": raw.get("warning"),
            "description": raw.get("description"), "plans": plans}


def _check_plan(p, where: str):
    """Structural validation of one card. Everything here stops the build,
    because every one of these would otherwise render as a plausible-looking
    but wrong card rather than as an error."""
    for field in ("key", "release", "title", "status", "groups"):
        if not p.get(field):
            raise SystemExit(
                f"ERROR: {where} is missing '{field}'. Every roadmap card needs all of "
                f"key/release/title/status/groups - a card missing one renders as a blank or "
                f"mislabelled panel instead of failing.")
    if p["status"] not in STATUS_BADGE_CLASS:
        raise SystemExit(
            f"ERROR: {where} has status {p['status']!r}, which is not one of "
            f"{', '.join(sorted(STATUS_BADGE_CLASS))}. Refusing to guess: an unrecognised status "
            f"quietly rendered as 'planned' is exactly how four shipped releases ended up "
            f"labelled 計画中 on this page.")
    if not p.get("badge"):
        raise SystemExit(
            f"ERROR: {where} has no 'badge' label. The badge text travels WITH the card through "
            f"translation (it is what distinguishes 'shipped' from 'not started', since both "
            f"share a colour with only one other status) - it must not fall back to a generic "
            f"'planned' string.")
    for i, g in enumerate(p["groups"]):
        gwhere = f"{where} group {i} ({g.get('subtitle', '?')!r})"
        if not g.get("subtitle"):
            raise SystemExit(f"ERROR: {gwhere} has no subtitle.")
        if not g.get("bullets"):
            raise SystemExit(
                f"ERROR: {gwhere} has no bullets. An empty group renders as a heading with "
                f"nothing under it, which reads as content that was lost.")
    link = p.get("link")
    if link:
        if not link.get("section") or not link.get("label"):
            raise SystemExit(f"ERROR: {where} has a 'link' without both 'section' and 'label'.")
        if link["section"] not in _KNOWN_SLUGS:
            raise SystemExit(
                "ERROR: %s links to section %r, which is not a page this site builds "
                "(known: %s). A dead internal link fails silently in the browser."
                % (where, link["section"], ", ".join(sorted(_KNOWN_SLUGS))))


def _merge(source_plans, bundle_roadmap, lang):
    """Source cards, each carrying this language's translation if it has one.

    Returns (plans, intro, warning, description). Matching is by `key`.
    A bundle entry whose key is not in the source is DROPPED — that is a card
    the Japanese source no longer has, i.e. a leftover from a previous version
    of this page, and rendering it is precisely the staleness this page is
    being fixed for.
    """
    if isinstance(bundle_roadmap, dict):
        translated_list = bundle_roadmap.get("plans") or []
        intro = bundle_roadmap.get("intro")
        warning = bundle_roadmap.get("warning")
        description = bundle_roadmap.get("description")
    else:
        # Pre-rewrite bundle shape: a bare list, and no key on any entry, so
        # nothing matches and every card falls back to Japanese. Intended.
        translated_list = bundle_roadmap or []
        intro = warning = description = None

    translated = {t["key"]: t for t in translated_list if isinstance(t, dict) and t.get("key")}
    # Entries with no key at all are pre-rewrite cards. They are dropped, and
    # saying so out loud matters: silently dropping them is indistinguishable
    # from a bundle that simply had nothing, and "nothing was reported" is how
    # this page stayed wrong in twelve languages for a week.
    keyless = len(translated_list) - len(translated)
    if keyless:
        print(f"  NOTE [{lang}] ignored {keyless} roadmap card(s) with no 'key' - pre-rewrite "
              f"bundle content, superseded by data/roadmap.ja.json")

    merged = []
    untranslated = []
    for s in source_plans:
        t = translated.get(s["key"])
        card = dict(s)
        if t is None:
            untranslated.append(s["key"])
        else:
            # `release` is translatable because it is RENDERED, not because it
            # is prose: the third card's release reads 未定 ("undecided"), and
            # leaving it structural published a Japanese word on twelve pages
            # while every other string around it was translated. Version
            # numbers travel through unchanged in practice -- a translation
            # that omits `release` still falls back to the Japanese source,
            # same as every other field.
            for k in ("title", "badge", "release", "groups"):
                if k in t:
                    card[k] = t[k]
            if t.get("link") and card.get("link"):
                card["link"] = dict(card["link"], label=t["link"].get("label", card["link"]["label"]))
        merged.append(card)

    if untranslated and lang != "ja":
        print(f"  NOTE [{lang}] {len(untranslated)}/{len(source_plans)} roadmap card(s) not "
              f"translated yet, falling back to Japanese: {', '.join(untranslated)}")
    stale = sorted(set(translated) - {s["key"] for s in source_plans})
    if stale:
        print(f"  NOTE [{lang}] dropped {len(stale)} roadmap card(s) the Japanese source no "
              f"longer has: {', '.join(stale)}")
    return merged, intro, warning, description


def render_plan(p):
    blocks = ""
    for g in p["groups"]:
        lis = "".join(f"<li>{esc(b)}</li>" for b in g["bullets"])
        blocks += f"<h4>{esc(g['subtitle'])}</h4><ul>{lis}</ul>"
    link = p.get("link")
    link_html = ""
    if link:
        link_html = (f'<p><a href="{LANG_PREFIX}{esc(link["section"])}">'
                     f'{esc(link["label"])}</a></p>')
    return f"""<div class="card" style="margin-bottom:20px;">
      <div class="badge-row"><span class="type-badge {STATUS_BADGE_CLASS[p['status']]}">{esc(p['badge'])}</span>
        <span class="timeline-entry__release">{esc(p['release'])}</span></div>
      <h3 style="margin-top:0">{esc(p['title'])}</h3>
      {blocks}{link_html}
    </div>"""


def build_lang(lang, source):
    bundle = load_bundle(lang)
    ui = bundle["ui"]
    plans, intro, warning, description = _merge(source["plans"], bundle.get("roadmap"), lang)

    # Japanese source text has to go through the same {mod_count}/{pack_version}
    # substitution the bundles get at load time -- it does not come from a
    # bundle when it is used as a fallback, so nothing else would fill it and
    # a literal "{mod_count}" would be published on twelve pages.
    plans = fill_placeholders(plans)
    intro = intro or fill_placeholders(source["intro"]) or ui["common"]["roadmap_intro"]
    warning = warning or fill_placeholders(source["warning"]) or ui["common"]["roadmap_warning"]
    # The search/share description too. ui.page_descriptions.roadmap is
    # translated in all 13 bundles and still advertises "a Backrooms area,
    # rail-MOD enhancements, UI improvements" as what is coming -- all of
    # which shipped between V1.9.0 and V2.2.0. A stale meta description is
    # the version of this page that search engines and chat previews show,
    # so it gets the same source-of-truth treatment as the body.
    description = (description or fill_placeholders(source["description"])
                   or ui["page_descriptions"]["roadmap"])

    plans_html = "\n".join(render_plan(p) for p in plans)

    body = f"""
<div class="hero">
  <span class="hero__eyebrow">{esc(ui['page_titles']['roadmap'])}</span>
  <h1>{esc(ui['page_titles']['roadmap'])}</h1>
  <p class="lede">{esc(intro)}</p>
  <p class="callout callout--warn">{esc(warning)}</p>
</div>
{plans_html}
"""
    html = page(
        lang=lang,
        section="roadmap/",
        title=ui["page_titles"]["roadmap"],
        description=description,
        active="roadmap",
        body=body,
        depth=1,
    )
    write_page(lang, "roadmap/", html)


def build():
    source = _load_source()
    keys = [p.get("key") for p in source["plans"]]
    dupes = sorted({k for k in keys if keys.count(k) > 1})
    if dupes:
        raise SystemExit(
            f"ERROR: {SOURCE} has duplicate card key(s): {', '.join(map(str, dupes))}. Keys are "
            f"what each language's translation is matched on - duplicates would give two cards "
            f"the same translation.")
    for i, p in enumerate(source["plans"]):
        _check_plan(p, f"{SOURCE.name} card {i} ({p.get('key', '?')!r})")
    for lang in available_langs():
        build_lang(lang, source)


if __name__ == "__main__":
    build()
