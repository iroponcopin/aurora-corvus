#!/usr/bin/env python3
"""Safety-relevant figures must survive translation exactly.

  python3 scripts/check_figures.py                 # all 12 non-ja languages
  python3 scripts/check_figures.py es fr           # just these
  python3 scripts/check_figures.py --advisory      # + per-string digit diff
  python3 scripts/check_figures.py --repo /path    # audit another checkout

This carries a HAND-WRITTEN table of the figures a reader would act on, per
content block. It is deliberately NOT the whole-number-multiset comparison a
previous agent built and threw away: that one compared every number in the JA
source against every number in the translation, fired on all 12 languages over
notation alone, and therefore distinguished nothing.

Two normalisations make the comparison mean something:

  * thousands separators (`,` `.` space nbsp narrow-nbsp) are stripped, so
    2.000 / 2,000 / "2 000" all read as 2000, while version-like 2.5.0 and
    26.2 are left intact — those are strings a reader types into a filename;
  * CJK/Korean myriad notation is expanded, so ja 「1,000万」, zh 「1000 万」
    and ko 「1,000만」 all read as 10000000. Without this the check is RED on
    ja, zh and ko for a reason that was never real — the correct value, in the
    correct local notation.

Figures are matched as whole tokens, not substrings: "1000000" must not be
allowed to satisfy a requirement for "10000000".

⚠ If a language legitimately spells a magnitude in words ("10 millones"), this
  goes RED and the RED is an artefact of notation, not a wrong number. Read the
  output, confirm the value by eye, and add the form to _WORD_SCALES below
  rather than deleting the requirement.
"""
import json
import re
import sys
from pathlib import Path

ALL_LANGS = ["en", "es", "fr", "zh", "ko", "pt-br", "it", "ar", "ru", "id", "de", "tr"]

# ---------------------------------------------------------------- normalising
_THOUSANDS = re.compile(r"(?<=\d)[,.   ](\d{3})(?!\d)")
# Decimal COMMA, applied only after the thousands pass has run to fixpoint, so
# "1,152" has already become 1152 by the time this sees it and only a genuine
# decimal tail is left. Eight of this site's twelve target languages -- es fr
# de it pt-br tr ru id -- write 0,35 where en writes 0.35, and without this the
# escalating-dehydration figures are unfindable in all eight.
_DECIMAL_COMMA = re.compile(r"(?<=\d),(\d{1,2})(?!\d)")
# 万 (1e4), 億/亿 (1e8), and their Korean readings 만/억.
_SCALES = [("億", 10 ** 8), ("亿", 10 ** 8), ("억", 10 ** 8),
           ("万", 10 ** 4), ("만", 10 ** 4)]
# Word forms a translation may legitimately use instead of digits. Extend this
# when a real RED turns out to be notation; never delete the requirement.
_WORD_SCALES = []


def norm(s: str) -> str:
    prev = None
    while prev != s:
        prev = s
        s = _THOUSANDS.sub(r"\1", s)
    s = _DECIMAL_COMMA.sub(r".\1", s)
    for word, mult in _WORD_SCALES:
        s = re.sub(r"(\d+(?:\.\d+)?)\s*" + word,
                   lambda m: str(int(float(m.group(1)) * mult)), s)
    for ch, mult in _SCALES:
        s = re.sub(r"(\d+(?:\.\d+)?)\s*" + ch,
                   lambda m, k=mult: str(int(float(m.group(1)) * k)), s)
    return s


def tokens(s: str) -> set:
    return set(re.findall(r"\d+(?:\.\d+)*", norm(s)))


def text_tokens(body_html: str) -> set:
    """Figures a READER can see: markup stripped first.

    Without this, `style="max-width:520px;margin:12px 0;"` contributes 520, 12
    and 0 to every section's token set, and a required figure could be
    satisfied by a CSS length it has nothing to do with -- a false green.
    <code> payloads survive, because that is where the config values live.
    """
    return tokens(re.sub(r"<[^>]+>", " ", body_html))


# ------------------------------------------------------------------- the table
# changelog: keyed on the entry's stable `id` (NOT on release -- see
# site_common.load_changelog_structural for why release/date is not an identity).
CHANGELOG = {
    # Boss HP. A drifted boss HP is not cosmetic: a player who reads 2400 and
    # brings gear for 2400 dies to a 4000-HP boss.
    "v1.3.0": ["900", "3"],
    "v1.4.0-bosses": ["1024", "2400", "4000", "3000", "3400", "2800"],
    "v1.5.6": ["6000", "9000", "3000", "16", "32"],
    "v1.9.0": ["600", "24000"],
    "v2.2.0": ["24", "12", "52", "18", "17", "15", "16", "9"],
    "v2.2.1": ["4"],
    "v2.4.0": [],
    "v2.4.1": [],
    "v2.4.3": ["17", "3"],
    "v2.4.4": ["3"],
    "v2.4.5": ["2000"],
    "v2.4.6": ["2000"],
    "v2.4.7": ["30", "10", "6000", "4"],
    "v2.4.8": ["30", "50", "10", "4"],
    "v2.4.9": ["60", "180", "100", "50", "200", "36", "3"],
    "v2.5.0": ["11", "2.5.0", "26.2", "1.5.1", "13"],
    "v2.5.1": ["1.7.0"],
    # "seven mechanics" is spelled out in every language that has a word for
    # it, so the count is not in this list; the figures a player acts on are.
    "disclosure": ["814", "320", "10", "100", "5", "6", "4"],
}

# features: the undocumented-mechanics disclosure is the reason this gate
# exists. These are mechanics that can kill a character or destroy a base, and
# the numbers are the whole content -- a drifted one is worse than clumsy prose.
FEATURES = {
    "glass-lanterns": ["52", "17", "18", "15"],
    "backrooms": ["1"],
    "overworld-raids": ["12"],
    "turrets": [],
    "video": ["4", "16", "9"],
    "sparxie-staff": ["24"],
    "firearm-rebalance": [],
    "drone": ["16", "9"],
    # NOT "3": the only 3 in this section is the "3D" of PLATEAU's dataset
    # name, which ar (correctly) writes as ثلاثي الأبعاد and other languages
    # may spell out too. It is part of a proper noun, not a figure a reader
    # acts on, and requiring it made this gate RED on a correct translation.
    "sapporo": ["100", "20"],
    "undocumented-mechanics": [
        "814",          # mask durability
        "320", "6400",  # revival delay, in seconds and in ticks
        "800",          # the "about 800" the original spec called for
        "4",            # 1 diamond = 4 emeralds; also 1 HP / 4 s
        "10000000",     # interest ceiling, emeralds
        "1000000", "1000000000",   # Singapore real estate, before and after
        "1152",         # what a vanilla trade slot can hold
        "0.05", "24", "6",         # eruption chance, vent clearance, crater
        "1800", "90", "12000",     # hydration tick rate, escalation delay
        "0.1", "1.4", "0.35",      # escalating dehydration damage
        "54", "60",     # air purifier, measured and by design
        "20",           # hydration scale 0-20
        "1.0",          # legacyVehicleFillFraction
    ],
}

GATES = {
    "nether": ["2", "21", "3", "4", "5"],
    "end": ["12", "5"],
    "amethyst": ["2", "21", "3"],
    "heaven": ["4", "5", "2", "3"],
    "backrooms": ["3", "2", "1"],
}

LAUNCHER = {"__all__": ["21", "256"]}   # Java 21, SHA-256

# The two emerald interest ceilings live in the roadmap block, not in features.
# ja/zh/ko write them as 1,000万 / 1000 万 / 1,000만 and 5,000万 / 5000 万 /
# 5,000만 -- correct values in local notation, which norm() expands.
# 600/800/750/1200 are the four Planarcadia bosses' HP, which the roadmap block
# recounts (they are NOT in the v2.0.0 changelog entry -- that entry describes
# the release without listing them).
ROADMAP = ["10000000", "50000000", "600", "800", "750", "1200"]

FIELDS = ("title", "summary", "highlights", "balance_changes", "warnings",
          "known_limitations")


def entry_text(e):
    out = [e.get("title", ""), e.get("summary", "")]
    for k in FIELDS[2:]:
        out.extend(e.get(k) or [])
    return "\n".join(out)


def _check_sections(fails, lang, sections, table, what):
    by_id = {s["id"]: s for s in sections if isinstance(s, dict) and s.get("id")}
    if not by_id:
        fails.append(f"{lang} {what}: no sections at all (untranslated?)")
        print(f"  RED  {lang} {what}: block is empty -- nothing to check")
        return
    for sid, wanted in table.items():
        s = by_id.get(sid)
        if s is None:
            fails.append(f"{lang} {what}.{sid}: section missing")
            print(f"  RED  {lang} {what}.{sid}: section missing entirely")
            continue
        have = text_tokens(s.get("title", "") + " " + s.get("body_html", ""))
        missing = [w for w in wanted if w not in have]
        if missing:
            fails.append(f"{lang} {what}.{sid}: {missing}")
            print(f"  RED  {lang} {what}.{sid}: figures missing from the translation: "
                  f"{', '.join(missing)}")


def main(langs, repo):
    fails = []
    for lang in langs:
        bundle = json.loads((repo / "data/i18n" / f"{lang}.json").read_text(encoding="utf-8"))

        by_id = {t["id"]: t for t in bundle.get("changelog", []) if t.get("id")}
        for eid, wanted in CHANGELOG.items():
            t = by_id.get(eid)
            if t is None:
                fails.append(f"{lang} changelog {eid}: no translated entry")
                print(f"  RED  {lang} changelog.{eid}: no translated entry at all")
                continue
            have = tokens(entry_text(t))
            missing = [w for w in wanted if w not in have]
            if missing:
                fails.append(f"{lang} changelog {eid}: {missing}")
                print(f"  RED  {lang} changelog.{eid}: figures missing from the "
                      f"translation: {', '.join(missing)}")

        _check_sections(fails, lang, bundle.get("features") or [], FEATURES, "features")
        _check_sections(fails, lang, bundle.get("gates") or [], GATES, "gates")

        rm = bundle.get("roadmap") or {}
        have = text_tokens(json.dumps(rm, ensure_ascii=False))
        missing = [w for w in ROADMAP if w not in have]
        if missing:
            fails.append(f"{lang} roadmap: {missing}")
            print(f"  RED  {lang} roadmap: figure(s) missing from the "
                  f"translation: {', '.join(missing)}")

        lp = bundle.get("launcher_page")
        if not lp:
            fails.append(f"{lang} launcher_page: absent")
            print(f"  RED  {lang} launcher_page: block absent (falls back to English)")
        else:
            have = text_tokens(json.dumps(lp, ensure_ascii=False))
            missing = [w for w in LAUNCHER["__all__"] if w not in have]
            if missing:
                fails.append(f"{lang} launcher_page: {missing}")
                print(f"  RED  {lang} launcher_page: figures missing from the "
                      f"translation: {', '.join(missing)}")

    print(f"\n{'RED' if fails else 'GREEN'}: named-figure gate, {len(fails)} failure(s) "
          f"over {len(langs)} language(s)")
    return len(fails)


def advisory(langs, repo):
    src = {e["id"]: e for e in
           json.loads((repo / "data/changelog.json").read_text(encoding="utf-8"))}
    for lang in langs:
        bundle = json.loads((repo / "data/i18n" / f"{lang}.json").read_text(encoding="utf-8"))
        by_id = {t["id"]: t for t in bundle.get("changelog", []) if t.get("id")}
        for eid in CHANGELOG:
            t, s = by_id.get(eid), src.get(eid)
            if not t or not s:
                continue
            for field in FIELDS:
                sv, tv = s.get(field), t.get(field)
                pairs = ([(sv, tv)] if isinstance(sv, str)
                         else list(zip(sv or [], tv or [])))
                for i, (a, b) in enumerate(pairs):
                    da, db = sorted(tokens(a or "")), sorted(tokens(b or ""))
                    if da != db:
                        print(f"  ~ {lang} {eid}.{field}"
                              f"{'' if isinstance(sv, str) else f'[{i}]'}: "
                              f"JA-only={[x for x in da if x not in db]} "
                              f"TR-only={[x for x in db if x not in da]}")


if __name__ == "__main__":
    argv = sys.argv[1:]
    repo = Path(__file__).resolve().parent.parent
    if "--repo" in argv:
        i = argv.index("--repo")
        repo = Path(argv[i + 1]).resolve()
        del argv[i:i + 2]
    langs = [a for a in argv if not a.startswith("--")] or ALL_LANGS
    n = main(langs, repo)
    if "--advisory" in sys.argv:
        print("\n--- advisory per-string digit diff (review by hand) ---")
        advisory(langs, repo)
    sys.exit(1 if n else 0)
