#!/usr/bin/env python3
"""Regression gates for the data defects this site has actually shipped.

  python3 scripts/check_defects.py                 # all groups
  python3 scripts/check_defects.py 1 5             # just these
  python3 scripts/check_defects.py --repo /path    # audit another checkout

Every defect is checked by TWO instruments that do not share a mechanism:

  A  reads data/*.json and data/i18n/*.json   (the input)
  B  reads the rendered *.html, or runs the generator  (the artefact)

A alone cannot see a generator that ignores the data; B alone cannot see a
value that is wrong but not currently reachable. Both must be green.

Run it AFTER a build — the B instruments read what the build produced.

Groups:
  1  changelog entries untranslated / a duplicated key collapsing two entries
  2  the download block rendering English on a translated page (the ordinary block and, since Alpha's
     retirement, the download_retired block that replaces five of its paragraphs)
  5  changelog identity (the one entry left, the retirement notice, renders once, in its own words) and
     launcher_page translation

2026-09-28: groups 3 (the roadmap description), 4 (known-issues) and the roadmap / features / gates / Sapporo
parts of 5 checked pages and text that the owner had erased with Alpha (「抹消」). They are removed, not
weakened: nothing is left for them to look at.
"""
import html as _html
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LANGS = ["ja", "en", "es", "fr", "zh", "ko", "pt-br", "it", "ar", "ru", "id", "de", "tr"]
OTHER = [l for l in LANGS if l != "ja"]

# Kana only. NOT the CJK ideograph block: zh legitimately uses Han characters,
# and ja/zh share them. Kana appears in Japanese and in nothing else here, so
# kana on a non-ja page is Japanese text that fell through.
KANA = re.compile(r"[぀-ゟ゠-ヿ]")

# Kana that is NOT untranslated prose. A Japanese FILENAME quoted verbatim is
# correct in every language -- v1.9.0 retires 「レシピ早見表.html」 by name, and a
# reader who has that file on disk needs to see the name they will actually
# find. Stripped before counting, or this check is red forever for a reason
# that was never real (the first run of it flagged 10 of 12 languages on this
# one string alone).
KANA_OK = ("レシピ早見表.html",)


def bundle(lang):
    return json.loads((ROOT / "data/i18n" / f"{lang}.json").read_text(encoding="utf-8"))


def page_text(rel):
    h = (ROOT / rel).read_text(encoding="utf-8")
    m = re.search(r"<main.*?</main>", h, re.S)
    return re.sub(r"<[^>]+>", " ", m.group(0) if m else h)


def page_path(lang, section):
    return f"{section}/index.html" if lang == "ja" else f"{lang}/{section}/index.html"


def _fail(fails, msg):
    fails.append(msg)
    print(f"  RED  {msg}")


def _walk_strings(node, path=""):
    """(dotted path, value) for every string leaf. Used so a check can say
    WHICH string it matched instead of grepping a whole file's JSON dump."""
    if isinstance(node, dict):
        for k, v in node.items():
            yield from _walk_strings(v, f"{path}.{k}" if path else k)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _walk_strings(v, f"{path}[{i}]")
    elif isinstance(node, str):
        yield path, node


# ---------------------------------------------------------------- defect 1
def defect1(fails):
    src = json.loads((ROOT / "data/changelog.json").read_text(encoding="utf-8"))
    # A: every structural entry has its OWN translation. Duplicated
    #    (release, date) keys are COUNTED, not collapsed -- that collapse is
    #    the bug this check exists for, so this instrument deliberately does
    #    not use the `id` the build now keys on.
    want = Counter((e["release"], e["date"]) for e in src)
    for lang in OTHER:
        have = Counter((t["release"], t["date"]) for t in bundle(lang)["changelog"])
        short = {k: (want[k], have[k]) for k in want if have[k] < want[k]}
        if short:
            _fail(fails, f"[1A] {lang}: {len(short)} changelog entry/entries untranslated: "
                         + ", ".join(f"{k[0]}({n}->{g})" for k, (n, g) in list(short.items())[:8]))
    # B: the published page. Kana on a non-ja page = Japanese fell through.
    for lang in OTHER:
        txt = page_text(f"{lang}/changelog/index.html")
        for ok in KANA_OK:
            txt = txt.replace(ok, "")
        hits = KANA.findall(txt)
        if hits:
            ctx = [m.group(0)[:60] for m in
                   re.finditer(r"[^\s]{0,25}[぀-ヿ]{2,}[^\s]{0,25}", txt)][:3]
            _fail(fails, f"[1B] {lang}/changelog/index.html has {len(hits)} kana characters "
                         f"(untranslated Japanese): {ctx}")
    # B2: a rendered page must not show the same entry title twice -- that is
    #     what the duplicated-key collapse looked like from outside.
    #
    #     2026-09-14: this selector still read the pre-V3.2 markup
    #     (`timeline-entry__release`), which no page has had since the Alcove
    #     restyle -- it matched 0 titles on all 13 pages, so this check could
    #     not fire at all. Moved to the per-release title the restyled page
    #     renders (`cl__entryTitle`, 94 per page, 0 duplicates in every
    #     language when moved). The assertion is unchanged. The brand panels
    #     (OUKA/Cherry/Aureum) render their titles with the same class, and a
    #     brand release that repeated an Alpha title would be the same defect.
    for lang in LANGS:
        rel = page_path(lang, "changelog")
        titles = re.findall(r'<p class="cl__entryTitle">(.*?)</p>',
                            (ROOT / rel).read_text(encoding="utf-8"), re.S)
        dup = [t for t, n in Counter(titles).items() if n > 1]
        if dup:
            _fail(fails, f"[1B] {rel}: {len(dup)} entry title(s) rendered more than once "
                         f"(duplicate-key collapse): {dup[:3]}")


# ---------------------------------------------------------------- defect 2
def defect2(fails):
    en = bundle("en")["download"]
    SHARED_OK = {"sha_label", "launcher_heading", "version_label", "launcher_version_label"}
    prose = [k for k in en if k not in SHARED_OK]
    for lang in OTHER:
        if lang == "en":
            continue
        dl = bundle(lang)["download"]
        missing = [k for k in en if k not in dl]
        if missing:
            _fail(fails, f"[2A] {lang}: download block missing {missing}")
        same = [k for k in prose if dl.get(k) == en[k]]
        if same:
            _fail(fails, f"[2A] {lang}: download {len(same)} key(s) still verbatim English: {same}")
    # A2: the download_retired block (2026-09-28) replaces five paragraphs while Alpha is retired; the same
    #     two questions about it: every language carries all five keys, and none is verbatim English.
    en_r = bundle("en")["download_retired"]
    for lang in OTHER:
        if lang == "en":
            continue
        dr = bundle(lang).get("download_retired") or {}
        miss = [k for k in en_r if not str(dr.get(k, "")).strip()]
        if miss:
            _fail(fails, f"[2A] {lang}: download_retired missing {miss}")
        same = [k for k in en_r if dr.get(k) == en_r[k]]
        if same:
            _fail(fails, f"[2A] {lang}: download_retired {len(same)} key(s) still verbatim English: {same}")
    # B: the published page must not contain the English marker phrases.
    MARKERS = ["For server admins", "How to install", "no Java required",
               "Cross-platform (Windows", "This page always distributes",
               "Add the release bot", "keeps your Alpha mod pack up to date",
               "Alpha has been retired. This page carries", "How to switch Alpha off",
               "Back up your worlds before you install it"]
    for lang in OTHER:
        if lang == "en":
            continue
        txt = page_text(f"{lang}/download/index.html")
        hit = [m for m in MARKERS if m in txt]
        if hit:
            _fail(fails, f"[2B] {lang}/download/index.html still shows English: {hit}")
    # ja too: three keys used to render English even on the Japanese page.
    ja_txt = page_text("download/index.html")
    hit = [m for m in ["no Java required", "Cross-platform (Windows"] if m in ja_txt]
    if hit:
        _fail(fails, f"[2B] download/index.html (ja) still shows English: {hit}")


# ---------------------------------------------------------------- defect 5
# The five follow-ups closed on 2026-08-29.

def defect5_changelog_identity(fails):
    src = json.loads((ROOT / "data/changelog.json").read_text(encoding="utf-8"))
    # A: the data carries a unique identity, and every bundle uses the same one.
    no_id = [f"{e.get('release')}({e.get('date')})" for e in src if not e.get("id")]
    if no_id:
        _fail(fails, f"[5.2A] data/changelog.json: {len(no_id)} entr(ies) with no 'id': {no_id[:5]}")
    dup = sorted({i for i, c in Counter(e.get("id") for e in src).items() if c > 1 and i})
    if dup:
        _fail(fails, f"[5.2A] data/changelog.json: duplicate id(s) {dup} -- two entries sharing "
                     f"an identity is the defect itself")
    want_ids = {e["id"] for e in src if e.get("id")}
    for lang in LANGS:
        got = [t.get("id") for t in bundle(lang)["changelog"]]
        missing_id = [i for i, t in enumerate(bundle(lang)["changelog"]) if not t.get("id")]
        if missing_id:
            _fail(fails, f"[5.2A] {lang}: {len(missing_id)} bundle changelog entr(ies) carry no "
                         f"'id' and can no longer be matched (index {missing_id[:5]})")
        d = sorted({i for i, c in Counter(i for i in got if i).items() if c > 1})
        if d:
            _fail(fails, f"[5.2A] {lang}: duplicate changelog id(s) {d}")
        orphan = sorted({i for i in got if i and i not in want_ids})
        if orphan:
            _fail(fails, f"[5.2A] {lang}: changelog id(s) the structural file does not have: {orphan}")
        absent = sorted(want_ids - {i for i in got if i})
        if absent:
            _fail(fails, f"[5.2A] {lang}: {len(absent)} structural entr(ies) have no translation "
                         f"under their id: {absent[:5]}")
    # A2: both consumers must actually key on it.
    for f, needle in (("scripts/build_changelog.py", "index_bundle_changelog"),
                      ("scripts/site_common.py", "by_id.get(s[\"id\"]")):
        # (scripts/extract_bundle.py was the third consumer; it read the erased Alpha sources and was
        #  removed with them on 2026-09-28.)
        if needle not in (ROOT / f).read_text(encoding="utf-8"):
            _fail(fails, f"[5.2A] {f} no longer uses the entry id ({needle!r}) -- it has gone "
                         f"back to an ambiguous key")
    # B: the published pages. The one entry that remains, the retirement notice, must render exactly once on
    #    every language's changelog page, with its own title. (Until 2026-09-28 this looked at the two
    #    v1.8.0 entries that once shared a (release, date) key: they are erased with the rest of Alpha's
    #    history, and the assertion moved to what is there now rather than being dropped.)
    src_ids = sorted(want_ids)
    for lang in LANGS:
        rel = page_path(lang, "changelog")
        markup = (ROOT / rel).read_text(encoding="utf-8")
        for eid in src_ids:
            n = markup.count('data-version="%s"' % eid)
            if n != 1:
                _fail(fails, f"[5.2B] {rel}: {n} entries rendered for {eid}, expected exactly 1")
        t = next(t for t in bundle(lang)["changelog"] if t["id"] == "v4.4.0.2")
        if _html.escape(t["title"], quote=False) not in markup and t["title"] not in markup:
            _fail(fails, f"[5.2B] {rel}: the retirement entry's own title {t['title']!r} is not on the page")


# 5.3  features / gates / launcher_page were untranslated in 11 languages. The
#      features block is the undocumented-mechanics disclosure: mechanics that
#      can kill a character or destroy a base.
def defect5_blocks(fails):
    ja = bundle("ja")
    en = bundle("en")
    # launcher_page has the shape {intro, sections}
    want_ids = [s["id"] for s in ja["launcher_page"]["sections"]]
    for lang in LANGS:
        lp = bundle(lang).get("launcher_page")
        if not lp:
            _fail(fails, f"[5.3A] {lang}: no 'launcher_page' block -- the launcher page "
                         f"publishes build_launcher.py's inline English copy")
            continue
        ids = [s.get("id") for s in lp.get("sections", [])]
        if ids != want_ids:
            _fail(fails, f"[5.3A] {lang}: launcher_page section ids do not match ja "
                         f"({len(ids)} vs {len(want_ids)})")
        elif lang not in ("ja", "en"):
            same = [s["id"] for s, e in zip(lp["sections"], en["launcher_page"]["sections"])
                    if s["body_html"] == e["body_html"]]
            if same or lp.get("intro") == en["launcher_page"].get("intro"):
                _fail(fails, f"[5.3A] {lang}: launcher_page still verbatim English: "
                             f"{same or ['intro']}")
    # B: the rendered launcher page. Leftover English, leftover kana.
    EN_MARKERS = ["keeps your mods up to date automatically", "Coming soon."]
    for lang in LANGS:
        rel = page_path(lang, "launcher")
        txt = page_text(rel)
        if "Coming soon." in txt:
            _fail(fails, f"[5.3B] {rel} is still the placeholder page ('Coming soon.')")
        if lang not in ("ja", "en"):
            hit = [m for m in EN_MARKERS if m in txt]
            if hit:
                _fail(fails, f"[5.3B] {rel} still shows English: {hit}")
            clean = txt
            for ok in KANA_OK:
                clean = clean.replace(ok, "")
            hits = KANA.findall(clean)
            if hits:
                ctx = [m.group(0)[:60] for m in
                       re.finditer(r"[^\s]{0,25}[぀-ヿ]{2,}[^\s]{0,25}", clean)][:3]
                _fail(fails, f"[5.3B] {rel} has {len(hits)} kana characters "
                             f"(untranslated Japanese): {ctx}")


def defect5(fails):
    defect5_changelog_identity(fails)
    defect5_blocks(fails)


GROUPS = {"1": defect1, "2": defect2, "5": defect5}


def main():
    global ROOT
    argv = sys.argv[1:]
    if "--repo" in argv:
        i = argv.index("--repo")
        ROOT = Path(argv[i + 1]).resolve()
        del argv[i:i + 2]
    which = [a for a in argv if a in GROUPS] or sorted(GROUPS)
    fails = []
    for n in which:
        print(f"--- defect {n} ---")
        GROUPS[n](fails)
    print(f"\n{'RED' if fails else 'GREEN'}: {len(fails)} failure(s)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
