#!/usr/bin/env python3
"""check_changelog_brands.py -- the changelog's brand panels and the brand feeds Corvus reads.

2026-09-14, owner: 「更新履歴をOUKA、Cherry、Alpha、Aureumを選べる様にしてください。
選んだModsブランドの更新履歴を確認できます。」 Answers the same day: both the site
and Corvus; OUKA, which has no releases, shows its page's own line; Cherry and
Aureum are written from verified facts only.

WHAT CAN GO WRONG, AND WHY EACH CHECK EXISTS
  A  The tabs or panels are not the Store brand line (OUKA -> Cherry -> Alpha,
     then Aureum), or Alpha is not the tab that opens. Every existing link to
     /changelog/ expects Alpha's history.
  B  Alpha's panel is missing releases, or Alpha's releases land in another
     brand's panel. Alpha's history is what the page always was.
  C  Another brand's panel does not hold exactly its own releases, each with its
     own translated title. A title is what tells a reader what a version was.
  D  OUKA's panel says anything but its page's own line, or holds release rows.
     The owner's answer, and the OUKA page's rule against status wording.
  E  An HTML id appears twice. Cherry and Aureum are both at 1.0 while Alpha has
     v1.0.0, so un-namespaced ids WOULD collide, and a duplicate id silently
     breaks the row buttons (aria-controls) and deep links.
  F  changelog_feed/brands.json is not the brand line with the right feed paths,
     or a brand feed is missing, has the wrong releases, or (OUKA) is not its
     line with no groups.
  G  Alpha's feed changed shape or gained anything. Every installed Corvus reads
     changelog_feed/<lang>.json and must keep seeing Alpha's history exactly.
  H  A language lacks a brand entry's translation (it would fall back to
     Japanese) or carries one the structural file does not have.

--self-test plants one defect per check into copies of the real data and
requires each to turn red with its own letter. A clean run must be green first,
or the plants prove nothing.
"""
import copy
import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from site_common import ROOT, LANG_CODES, esc  # noqa: E402
from build_changelog import (  # noqa: E402
    DEFAULT_BRAND, brand_order, brand_name, load_brand_structural, rich,
)
from build_ouka import COPY as OUKA_COPY  # noqa: E402

ALPHA_FEED_KEYS = {"lang", "updated", "title", "updated_label", "note", "groups"}
TAB = re.compile(r'<button class="cl__brandTab"[^>]*?data-brand="([a-z]+)"[^>]*?aria-selected="(true|false)"')
PANEL = re.compile(r'<section class="cl__brand" id="clBrand-([a-z]+)" data-brand="([a-z]+)">')
ROW = '<div class="cl__release"'


def page_rel(lang):
    return "changelog/index.html" if lang == "ja" else f"{lang}/changelog/index.html"


def _json_or_none(path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def load_world():
    langs = [c for c in LANG_CODES if (ROOT / "data" / "i18n" / f"{c}.json").exists()]
    order = brand_order()
    return {
        "langs": langs,
        "order": order,
        "alpha": json.loads((ROOT / "data" / "changelog.json").read_text(encoding="utf-8")),
        "brands": load_brand_structural(),
        "pages": {lang: (ROOT / page_rel(lang)).read_text(encoding="utf-8") for lang in langs},
        "bundles": {lang: json.loads((ROOT / "data" / "i18n" / f"{lang}.json").read_text(encoding="utf-8")) for lang in langs},
        "index": _json_or_none(ROOT / "changelog_feed" / "brands.json"),
        "alpha_feeds": {lang: _json_or_none(ROOT / "changelog_feed" / f"{lang}.json") for lang in langs},
        "brand_feeds": {f"{b}/{lang}": _json_or_none(ROOT / "changelog_feed" / b / f"{lang}.json")
                        for b in order if b != DEFAULT_BRAND for lang in langs},
        "ouka": {lang: OUKA_COPY[lang]["soon"] for lang in langs},
    }


def panels_of(html):
    starts = [(m.start(), m.group(1), m.group(2)) for m in PANEL.finditer(html)]
    bounds = [s[0] for s in starts] + [len(html)]
    return starts, {starts[i][1]: html[bounds[i]:bounds[i + 1]] for i in range(len(starts))}


def check(world):
    fails = []
    order = world["order"]
    alpha_count = len(world["alpha"])
    for lang in world["langs"]:
        rel = page_rel(lang)
        html = world["pages"][lang]
        bundle = world["bundles"][lang]

        tabs = TAB.findall(html)
        if [b for b, _ in tabs] != order:
            fails.append(f"[A] {rel}: tabs {[b for b, _ in tabs]} are not the brand line {order}")
        selected = [b for b, s in tabs if s == "true"]
        if selected != [DEFAULT_BRAND]:
            fails.append(f"[A] {rel}: the tab that opens is {selected}, expected ['{DEFAULT_BRAND}']")
        starts, panel = panels_of(html)
        if [s[1] for s in starts] != order or any(a != b for _, a, b in starts):
            fails.append(f"[A] {rel}: panels {[s[1] for s in starts]} are not the brand line {order}")
            continue

        rows = {b: panel[b].count(ROW) for b in order}
        if ROW in html[:starts[0][0]]:
            fails.append(f"[B] {rel}: a release row sits outside every brand panel")
        if rows[DEFAULT_BRAND] != alpha_count:
            fails.append(f"[B] {rel}: Alpha's panel holds {rows[DEFAULT_BRAND]} releases, data/changelog.json has {alpha_count}")

        for b in order:
            if b == DEFAULT_BRAND:
                continue
            entries = world["brands"][b]
            prose = {t.get("id"): t for t in ((bundle.get("changelog_brands") or {}).get(b) or [])}
            extra = sorted(set(prose) - {e["id"] for e in entries} - {None})
            if extra:
                fails.append(f"[H] data/i18n/{lang}.json: changelog_brands.{b} has id(s) the structural file does not: {extra}")
            if rows[b] != len(entries):
                fails.append(f"[C] {rel}: {b}'s panel holds {rows[b]} releases, data/changelog_brands.json has {len(entries)}")
            for e in entries:
                t = prose.get(e["id"])
                if not t or not t.get("title"):
                    fails.append(f"[H] data/i18n/{lang}.json: no translated title for {b} release {e['id']}")
                    continue
                if f'<p class="cl__entryTitle">{rich(t["title"])}</p>' not in panel[b]:
                    fails.append(f"[C] {rel}: {b} release {e['id']} does not render its own title")
            if not entries:
                if b != "ouka":
                    fails.append(f"[D] {rel}: {b} has no releases and no agreed empty state")
                elif panel[b].count(f'<p class="cl__soon">{esc(world["ouka"][lang])}</p>') != 1:
                    fails.append(f"[D] {rel}: OUKA's panel does not show its page's own line "
                                 f"{world['ouka'][lang]!r} exactly once")
            elif '<p class="cl__soon">' in panel[b]:
                fails.append(f"[D] {rel}: {b} has releases but also shows an empty-state line")

        ids = re.findall(r'\sid="([^"]+)"', html)
        dup = sorted(i for i, n in Counter(ids).items() if n > 1)
        if dup:
            fails.append(f"[E] {rel}: id(s) used more than once: {dup[:6]}")

        feed = world["alpha_feeds"].get(lang)
        if feed is None:
            fails.append(f"[G] changelog_feed/{lang}.json is missing")
        else:
            if set(feed) != ALPHA_FEED_KEYS:
                fails.append(f"[G] changelog_feed/{lang}.json keys {sorted(feed)} are not Alpha's contract {sorted(ALPHA_FEED_KEYS)}")
            total = sum(len(g.get("releases", [])) for g in feed.get("groups", []))
            if total != alpha_count:
                fails.append(f"[G] changelog_feed/{lang}.json holds {total} releases, Alpha has {alpha_count}")

        for b in order:
            if b == DEFAULT_BRAND:
                continue
            key = f"{b}/{lang}"
            bf = world["brand_feeds"].get(key)
            if bf is None:
                fails.append(f"[F] changelog_feed/{key}.json is missing")
                continue
            entries = world["brands"][b]
            if bf.get("brand") != b or bf.get("lang") != lang:
                fails.append(f"[F] changelog_feed/{key}.json names brand {bf.get('brand')!r} / lang {bf.get('lang')!r}")
            total = sum(len(g.get("releases", [])) for g in bf.get("groups", []))
            if total != len(entries):
                fails.append(f"[F] changelog_feed/{key}.json holds {total} releases, the structural file has {len(entries)}")
            if not entries:
                if bf.get("groups") != [] or bf.get("message") != world["ouka"].get(lang):
                    fails.append(f"[F] changelog_feed/{key}.json: a brand with no releases must carry no groups and "
                                 f"its page's line as the message")
            elif "message" in bf:
                fails.append(f"[F] changelog_feed/{key}.json has releases and a message")

    index = world["index"]
    want = [{"id": b, "name": brand_name(b),
             "feed": "changelog_feed/{lang}.json" if b == DEFAULT_BRAND else f"changelog_feed/{b}/{{lang}}.json"}
            for b in order]
    if index is None:
        fails.append("[F] changelog_feed/brands.json is missing")
    elif index.get("brands") != want or index.get("default") != DEFAULT_BRAND or index.get("schema") != 1:
        fails.append(f"[F] changelog_feed/brands.json is not the brand line with its feed paths: {index}")
    return fails


# ------------------------------------------------------------------ self-test
def _swap_first_two_tabs(w):
    html = w["pages"]["en"]
    buttons = re.findall(r'<button class="cl__brandTab".*?</button>', html)
    w["pages"]["en"] = html.replace(buttons[0], "\0").replace(buttons[1], buttons[0]).replace("\0", buttons[1])


def _select_ouka(w):
    html = w["pages"]["es"]
    html = html.replace('data-brand="alpha" aria-controls="clBrand-alpha" aria-selected="true"',
                        'data-brand="alpha" aria-controls="clBrand-alpha" aria-selected="false"')
    w["pages"]["es"] = html.replace('data-brand="ouka" aria-controls="clBrand-ouka" aria-selected="false"',
                                    'data-brand="ouka" aria-controls="clBrand-ouka" aria-selected="true"')


def _in_panel(w, lang, brand, old, new):
    html = w["pages"][lang]
    starts, panel = panels_of(html)
    start = next(s for s, b, _ in starts if b == brand)
    body = panel[brand]
    assert old in body, (lang, brand, old)
    w["pages"][lang] = html[:start] + body.replace(old, new, 1) + html[start + len(body):]


def _lose_alpha_row(w):
    _in_panel(w, "de", "alpha", ROW, '<div class="cl__gone"')


def _double_cherry_row(w):
    _in_panel(w, "fr", "cherry", '<div class="cl__groups"', '<div class="cl__groups">' + ROW + '></div><div')


def _wrong_cherry_title(w):
    html = w["pages"]["it"]
    starts, panel = panels_of(html)
    start = next(s for s, b, _ in starts if b == "cherry")
    body = re.sub(r'<p class="cl__entryTitle">.*?</p>', '<p class="cl__entryTitle">PLANTED</p>', panel["cherry"], count=1)
    w["pages"]["it"] = html[:start] + body + html[start + len(panel["cherry"]):]


def _ouka_status_line(w):
    _in_panel(w, "ja", "ouka", f'<p class="cl__soon">{esc(w["ouka"]["ja"])}</p>', '<p class="cl__soon">まだリリースはありません。</p>')


def _duplicate_id(w):
    _in_panel(w, "ko", "aureum", 'id="aureum-v1.0"', 'id="cherry-v1.0"')


def _missing_feed(w):
    w["brand_feeds"]["aureum/ru"] = None


def _index_reversed(w):
    w["index"] = dict(w["index"], brands=list(reversed(w["index"]["brands"])))


def _alpha_feed_gains_brand(w):
    w["alpha_feeds"]["en"]["brand"] = "cherry"


def _translation_missing(w):
    w["bundles"]["tr"]["changelog_brands"]["cherry"] = []


PLANTS = [
    ("A", "the tab row swaps OUKA and Cherry", _swap_first_two_tabs),
    ("A", "OUKA opens instead of Alpha", _select_ouka),
    ("B", "Alpha's panel loses a release", _lose_alpha_row),
    ("C", "Cherry's panel gains a release row", _double_cherry_row),
    ("C", "a Cherry release renders someone else's title", _wrong_cherry_title),
    ("D", "OUKA shows status wording", _ouka_status_line),
    ("E", "Aureum's series reuses Cherry's id", _duplicate_id),
    ("F", "a brand feed is missing", _missing_feed),
    ("F", "brands.json is out of order", _index_reversed),
    ("G", "Alpha's feed gains a brand field", _alpha_feed_gains_brand),
    ("H", "a language loses a Cherry translation", _translation_missing),
]


def self_test():
    world = load_world()
    clean = check(world)
    if clean:
        print("SELF-TEST REFUSED: the real site is not green, so a red plant would prove nothing:")
        for f in clean[:10]:
            print("  " + f)
        return 1
    problems = 0
    for letter, what, plant in PLANTS:
        w = copy.deepcopy(world)
        plant(w)
        reds = check(w)
        mine = [r for r in reds if r.startswith(f"[{letter}]")]
        ok = bool(mine)
        problems += 0 if ok else 1
        print(f"  self-test [{'ok' if ok else 'MISSED'}] {letter}: {what}: " + (mine[0] if mine else f"no [{letter}] failure; saw {reds[:2]}"))
    print(f"SELF-TEST VERDICT: {'PASS' if problems == 0 else 'FAIL'} ({len(PLANTS) - problems}/{len(PLANTS)} plants caught, clean run green)")
    return 0 if problems == 0 else 1


def main(argv):
    if "--self-test" in argv:
        return self_test()
    world = load_world()
    fails = check(world)
    for f in fails:
        print("FAIL " + f)
    pages = len(world["langs"])
    feeds = sum(1 for v in world["brand_feeds"].values() if v is not None)
    print(f"changelog brands: {pages} pages, {feeds} brand feeds, line {' -> '.join(world['order'])}: "
          f"{'GREEN' if not fails else f'RED ({len(fails)})'}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
