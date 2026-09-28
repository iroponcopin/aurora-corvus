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
    # 2026-09-28: Alpha's changelog history was erased with the rest of Alpha (owner: 「抹消」); the one
    # entry left is the notice that ended it. The figures a reader acts on there: the 13 mods replaced, and the
    # overworld ceiling the sky placeholder keeps (Y up to 1023) against the vanilla one (Y=319) -- a drifted
    # 319 would tell a player the wrong height above which their build is deleted.
    "v4.4.0.2": ["13", "1023", "319"],
}

LAUNCHER = {"__all__": ["25", "256"]}   # Java 25 (the launcher jar is class-file version 69), SHA-256

FIELDS = ("title", "summary", "highlights", "balance_changes", "warnings",
          "known_limitations")


def entry_text(e):
    out = [e.get("title", ""), e.get("summary", "")]
    for k in FIELDS[2:]:
        out.extend(e.get(k) or [])
    return "\n".join(out)


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
