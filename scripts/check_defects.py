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
  2  the download block rendering English on a translated page
  3  ui.page_descriptions.roadmap promising shipped work as upcoming
  4  known-issues losing entries / still listing bugs closed in V2.4.3
  5  the five follow-ups: roadmap intro+warning, changelog identity,
     features/gates/launcher_page translation, the Sapporo tense
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
    for lang in LANGS:
        rel = page_path(lang, "changelog")
        titles = re.findall(r'timeline-entry__release">.*?</span> — (.*?)\s*</h3>',
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
    # B: the published page must not contain the English marker phrases.
    MARKERS = ["For server admins", "How to install", "no Java required",
               "Cross-platform (Windows", "This page always distributes",
               "Add the release bot", "keeps your Alpha mod pack up to date"]
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


# ---------------------------------------------------------------- defect 3
def defect3(fails):
    # A: the stale claim, in each language's own words.
    STALE = {"ja": ["バックルームエリア", "鉄道MOD強化", "UI改善"],
             "en": ["backrooms area", "rail mod enhancements", "UI improvements"],
             "es": ["zona de Backrooms", "MOD de ferrocarril"],
             "fr": ["zone « Backrooms »", "MOD ferroviaire"],
             "zh": ["后室区域", "铁道 MOD 强化"],
             "ko": ["백룸 지역", "철도 MOD 강화"],
             "pt-br": ["área de backrooms", "melhorias na ferrovia"],
             "it": ["area «Backrooms»", "mod ferroviaria"],
             "ar": ["الغرف الخلفية\" وتعزيز", "السكك الحديدية وتحسينات"],
             "ru": ["зона «Задней комнаты»", "усиление мода железной дороги"],
             "id": ["area backrooms", "penguatan MOD kereta"],
             "de": ["Hinterzimmer-Bereich", "Erweiterungen des Schienen-MODs"],
             "tr": ["Backrooms alanı", "demiryolu MOD'unda güçlendirme"]}
    for lang in LANGS:
        v = bundle(lang)["ui"]["page_descriptions"]["roadmap"]
        hit = [s for s in STALE[lang] if s in v]
        if hit:
            _fail(fails, f"[3A] {lang}: ui.page_descriptions.roadmap still promises shipped "
                         f"work as upcoming: {hit}")
    # A2: the JA source file, or the next extract_bundle.py run puts it back.
    u = json.loads((ROOT / "data/ui-strings.ja.json").read_text(encoding="utf-8"))
    hit = [s for s in STALE["ja"] if s in u["page_descriptions"]["roadmap"]]
    if hit:
        _fail(fails, f"[3A] data/ui-strings.ja.json still holds the stale roadmap description: {hit}")
    # B: build_roadmap.py must still READ the key -- otherwise "correct it in
    #    all 13" was the wrong remedy and it should have been deleted instead.
    code = (ROOT / "scripts/build_roadmap.py").read_text(encoding="utf-8")
    if 'ui["page_descriptions"]["roadmap"]' not in code:
        _fail(fails, "[3B] build_roadmap.py no longer reads ui.page_descriptions.roadmap -- "
                     "the key is now dead data and should be removed, not corrected.")


# ---------------------------------------------------------------- defect 4
def defect4(fails):
    src = json.loads((ROOT / "data/known-issues.ja.json").read_text(encoding="utf-8"))
    # EVERY list in the source, not just minor_bugs.
    #
    # ⚠ This used to compare `minor_bugs` alone. Every bug on that list has
    #   since been fixed, so the source holds 0 and all 13 bundles hold 0, and
    #   the comparison was 0 != 0 — a gate that could not fail. Deleting an
    #   entry from a bundle to negative-control it changed nothing, because
    #   there was nothing to delete. A green that cannot go red is the exact
    #   failure this file exists to prevent, so the comparison now covers
    #   standing_limitations and recent_unconfirmed as well, and says out loud
    #   when a list is empty on both sides.
    lists = [k for k, v in src.items() if isinstance(v, list)]
    empty = [k for k in lists if not src[k]]
    if empty:
        print(f"  note: {', '.join(empty)} is empty in data/known-issues.ja.json, so that "
              f"comparison cannot fail today; {len(lists) - len(empty)} other list(s) can")
    if len(lists) == len(empty):
        _fail(fails, "[4A] every list in data/known-issues.ja.json is empty -- this whole "
                     "instrument is vacuous, and the page it guards may be blank")
    for key in lists:
        n = len(src[key])
        for lang in LANGS:
            got = bundle(lang)["known_issues"].get(key)
            if len(got or []) != n:
                _fail(fails, f"[4A] {lang}: known_issues.{key} has {len(got or [])} entries, "
                             f"data/known-issues.ja.json has {n}")
    # B: the three bugs closed in V2.4.3 must not be advertised on any page.
    CLOSED = {"es": "vidrio reforzado", "fr": "verre renforcé", "zh": "强化玻璃窗",
              "ko": "강화유리 창", "pt-br": "vidro reforçado", "it": "vetro rinforzato",
              "ar": "الزجاج المقوى", "ru": "усиленного стекла", "id": "Kaca Diperkuat",
              "de": "verstärkten Glasfenster", "tr": "Güçlendirilmiş cam pencerelerin",
              "ja": "強化ガラスの窓(17色)の名前表示", "en": "reinforced glass window"}
    for lang in LANGS:
        rel = page_path(lang, "known-issues")
        txt = page_text(rel)
        if CLOSED[lang] in txt:
            _fail(fails, f"[4B] {rel} still lists a bug fixed in V2.4.3: {CLOSED[lang]!r}")
        # and the page must not be three empty headings. Counted in CHARACTERS,
        # not whitespace-separated tokens: Japanese does not put spaces between
        # words, so the first version of this line read the 942-character JA
        # page as "29 words" and called it empty.
        body = re.sub(r"\s+", " ", txt).strip()
        if len(body) < 300:
            _fail(fails, f"[4B] {rel} looks empty ({len(body)} characters)")


# ---------------------------------------------------------------- defect 5
# The five follow-ups closed on 2026-08-29.

# 5.1  ui.common.roadmap_intro / roadmap_warning asserted, in all 13 languages,
#      that "nothing on this page has been implemented or shipped" -- while the
#      page led with four shipped releases. Both are LAST-RESORT fallbacks in
#      build_roadmap.py (the data file and then the bundle's own roadmap block
#      shadow them), so they were unreachable on the day, which is exactly the
#      shape of defect 3: wrong text sitting on a live path, one edit away from
#      publishing.
STALE_ROADMAP_WARNING = {
    "ja": ["まだ実装・配布されていません"],
    "en": ["has not yet been implemented or released", "not yet been implemented"],
    "es": ["aún no se ha implementado ni distribuido"],
    "fr": ["n'est ni implémenté ni distribué"],
    "zh": ["尚未实装、尚未发布"],
    "ko": ["아직 구현·배포되지 않았습니다"],
    "pt-br": ["ainda não foi implementado nem distribuído"],
    "it": ["non sono ancora stati implementati né distribuiti"],
    "ar": ["لم يُنفَّذ أو يُوزَّع بعد"],
    "ru": ["ещё не реализовано и не распространяется"],
    "id": ["belum diimplementasikan atau didistribusikan"],
    "de": ["noch nicht umgesetzt oder verteilt"],
    "tr": ["henüz uygulanmamış ve dağıtılmamıştır"],
}
# A version-free string cannot name a release. If one of these turns up in the
# fallback again, it will go stale the same way the last one did.
VERSIONISH = re.compile(r"\bV?[12]\.\d+(\.\d+)*\b")


def defect5_roadmap_ui(fails):
    # A: the data.
    for lang in LANGS:
        c = bundle(lang)["ui"]["common"]
        for key in ("roadmap_intro", "roadmap_warning"):
            if key not in c:
                _fail(fails, f"[5.1A] {lang}: ui.common.{key} is gone, but build_roadmap.py "
                             f"subscripts it directly -- the build will KeyError the moment "
                             f"the fallback fires")
                continue
            if VERSIONISH.search(c[key]):
                _fail(fails, f"[5.1A] {lang}: ui.common.{key} names a version "
                             f"({VERSIONISH.search(c[key]).group(0)}) -- this fallback must be "
                             f"version-free or it goes stale again: {c[key][:90]!r}")
        hit = [s for s in STALE_ROADMAP_WARNING[lang] if s in c.get("roadmap_warning", "")]
        if hit:
            _fail(fails, f"[5.1A] {lang}: ui.common.roadmap_warning still claims nothing on the "
                         f"roadmap has shipped: {hit}")
    u = json.loads((ROOT / "data/ui-strings.ja.json").read_text(encoding="utf-8"))
    for key in ("roadmap_intro", "roadmap_warning"):
        if key not in u["common"]:
            _fail(fails, f"[5.1A] data/ui-strings.ja.json has no common.{key} -- the next "
                         f"extract_bundle.py run would drop it from the ja bundle")
    hit = [s for s in STALE_ROADMAP_WARNING["ja"] if s in u["common"].get("roadmap_warning", "")]
    if hit:
        _fail(fails, f"[5.1A] data/ui-strings.ja.json still holds the stale roadmap warning "
                     f"({hit}) -- the next extract_bundle.py run reverts the fix")

    # B: run the GENERATOR down the fallback path and read what it emits. A
    #    different mechanism from reading the JSON: it proves the key is still
    #    reachable (so correcting it was the right remedy, not deleting it) and
    #    that what reaches the page is the corrected text.
    sys.path.insert(0, str(ROOT / "scripts"))
    import build_roadmap
    captured = {}
    real_write, real_load = build_roadmap.write_page, build_roadmap.load_bundle

    def fake_write(lang, section, html):
        captured[lang] = html

    def fake_load(lang):
        b = json.loads(json.dumps(real_load(lang)))     # deep copy, cache-safe
        b["roadmap"].pop("intro", None)
        b["roadmap"].pop("warning", None)
        return b

    src = build_roadmap._load_source()
    src = dict(src, intro=None, warning=None)
    build_roadmap.write_page, build_roadmap.load_bundle = fake_write, fake_load
    try:
        for lang in LANGS:
            build_roadmap.build_lang(lang, src)
    finally:
        build_roadmap.write_page, build_roadmap.load_bundle = real_write, real_load

    for lang in LANGS:
        rendered = captured.get(lang, "")
        if not rendered:
            _fail(fails, f"[5.1B] {lang}: the roadmap fallback path produced no page at all")
            continue
        # Entities must be undone before comparing: site_common.esc() turns the
        # apostrophe in fr's "ce qu'elles" into &#x27;, and without unescaping
        # here this check was RED on fr alone -- an artefact of escaping, not a
        # missing string.
        body = _html.unescape(re.sub(r"<[^>]+>", " ", rendered))
        hit = [s for s in STALE_ROADMAP_WARNING[lang] if s in body]
        if hit:
            _fail(fails, f"[5.1B] {lang}: with no intro/warning in the data, the roadmap page "
                         f"PUBLISHES the claim that nothing has shipped: {hit}")
        if bundle(lang)["ui"]["common"]["roadmap_warning"] not in body:
            _fail(fails, f"[5.1B] {lang}: ui.common.roadmap_warning is no longer reachable from "
                         f"build_roadmap.py -- it is dead data now and should be removed rather "
                         f"than maintained")


# 5.2  (release, date) is not unique in data/changelog.json. Keying a dict on it
#      published one entry's prose under another's badge in all 13 languages.
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
                      ("scripts/site_common.py", "by_id.get(s[\"id\"]"),
                      ("scripts/extract_bundle.py", '"id": e["id"]')):
        if needle not in (ROOT / f).read_text(encoding="utf-8"):
            _fail(fails, f"[5.2A] {f} no longer uses the entry id ({needle!r}) -- it has gone "
                         f"back to an ambiguous key")
    # B: the published pages. The two entries that share v1.8.0/2026-08-04 must
    #    render as two DIFFERENT entries -- the collapse made them identical.
    for lang in LANGS:
        rel = page_path(lang, "changelog")
        markup = (ROOT / rel).read_text(encoding="utf-8")
        arts = re.findall(r'<article class="timeline-entry".*?</article>', markup, re.S)
        v180 = [a for a in arts if 'timeline-entry__release">v1.8.0</span>' in a]
        if len(v180) != 2:
            _fail(fails, f"[5.2B] {rel}: {len(v180)} v1.8.0 entries rendered, expected 2")
            continue
        t = [re.search(r"</span> — (.*?)\s*</h3>", a, re.S).group(1) for a in v180]
        if t[0] == t[1]:
            _fail(fails, f"[5.2B] {rel}: both v1.8.0 entries render the same title {t[0]!r} -- "
                         f"the duplicate-key collapse is back")
        # EXACTLY ONE of the two is the rename announcement. Not "the first
        # one": build_changelog.py renders newest-first, so the rename is the
        # SECOND v1.8.0 article on the page, and an order-dependent version of
        # this line was RED on all 13 correct pages.
        renames = sum("Glimpse Alpha" in a for a in v180)
        if renames != 1:
            _fail(fails, f"[5.2B] {rel}: {renames} of the 2 v1.8.0 entries announce the rename "
                         f"to Glimpse Alpha, expected exactly 1 -- one entry's prose is "
                         f"rendered against both badges: {t}")


# 5.3  features / gates / launcher_page were untranslated in 11 languages. The
#      features block is the undocumented-mechanics disclosure: mechanics that
#      can kill a character or destroy a base.
BLOCK_PAGES = {"features": "features", "gates": "gates", "launcher_page": "launcher"}


def defect5_blocks(fails):
    ja = bundle("ja")
    en = bundle("en")
    for key in ("features", "gates"):
        want_ids = [s["id"] for s in ja[key]]
        want_img = json.dumps(ja[key], ensure_ascii=False).count("{img_root}")
        want_jar = json.dumps(ja[key], ensure_ascii=False).count("{launcher_jar}")
        for lang in LANGS:
            got = bundle(lang).get(key)
            if got is None:
                _fail(fails, f"[5.3A] {lang}: no {key!r} block at all")
                continue
            ids = [s.get("id") for s in got]
            if ids != want_ids:
                _fail(fails, f"[5.3A] {lang}: {key} section ids do not match ja "
                             f"({len(ids)} vs {len(want_ids)}): "
                             f"missing={[i for i in want_ids if i not in ids][:5]}")
                continue
            blob = json.dumps(got, ensure_ascii=False)
            if blob.count("{img_root}") != want_img:
                _fail(fails, f"[5.3A] {lang}: {key} has {blob.count('{img_root}')} "
                             f"{{img_root}} placeholders, ja has {want_img} -- a translated "
                             f"brace is a broken image")
            if blob.count("{launcher_jar}") != want_jar:
                _fail(fails, f"[5.3A] {lang}: {key} has {blob.count('{launcher_jar}')} "
                             f"{{launcher_jar}} placeholders, ja has {want_jar}")
            if lang not in ("ja", "en"):
                same = [s["id"] for s, e in zip(got, en[key]) if s["body_html"] == e["body_html"]]
                if same:
                    _fail(fails, f"[5.3A] {lang}: {key} section(s) still verbatim English: {same}")
    # launcher_page has a different shape: {intro, sections}
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
    # B: the rendered pages. Placeholder copy, leftover English, leftover kana.
    EN_MARKERS = ["are all live in the currently distributed pack",
                  "This pack makes no changes to it at all",
                  "keeps your Alpha mod pack up to date automatically",
                  "Common mistakes", "Coming soon."]
    for lang in LANGS:
        for section in ("features", "gates", "launcher"):
            rel = page_path(lang, section)
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


# 5.4  download.sapporo_note read 「V2.2.0 で初めて配布されます」 -- future tense
#      for something that shipped in V2.2.0. Only the JA authoring string was
#      left behind; the 11 translations were already past tense.
def defect5_sapporo(fails):
    # A: the data.
    note = bundle("ja")["download"]["sapporo_note"]
    if "配布されます" in note:
        _fail(fails, "[5.4A] ja: download.sapporo_note is still future tense "
                     "(「配布されます」) for a mod that shipped in V2.2.0")
    if "配布されました" not in note:
        _fail(fails, f"[5.4A] ja: download.sapporo_note no longer says 「配布されました」: {note[:60]!r}")
    # The key lives only in the bundle's hand-authored `download` block, which
    # extract_bundle.py carries through untouched; if it ever gains a source
    # file, that file has to be fixed too or the next run reverts this.
    #
    # Scoped to a string that is BOTH about Sapporo AND future tense. A first
    # version of this line searched data/ui-strings.ja.json for 「配布されます」
    # alone and was RED on common.issues_intro -- 「修正版が配布されます」, a
    # correct statement about future fix releases that has nothing to do with
    # the Sapporo mod.
    u = json.loads((ROOT / "data/ui-strings.ja.json").read_text(encoding="utf-8"))
    for path, value in _walk_strings(u):
        if "札幌" in value and "配布されます" in value:
            _fail(fails, f"[5.4A] data/ui-strings.ja.json {path} holds a future-tense Sapporo "
                         f"note -- the next extract_bundle.py run would revert the fix: "
                         f"{value[:60]!r}")
    # B: the published page.
    txt = page_text("download/index.html")
    if "配布されます" in txt:
        _fail(fails, "[5.4B] download/index.html still publishes the future-tense Sapporo note")


def defect5(fails):
    defect5_roadmap_ui(fails)
    defect5_changelog_identity(fails)
    defect5_blocks(fails)
    defect5_sapporo(fails)


GROUPS = {"1": defect1, "2": defect2, "3": defect3, "4": defect4, "5": defect5}


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
