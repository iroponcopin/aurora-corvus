#!/usr/bin/env python3
"""One entry point for every audit in this repo. Run it after scripts/build.py.

  python3 scripts/check_site.py               # everything
  python3 scripts/check_site.py --list        # what it would run
  python3 scripts/check_site.py defects 404   # just these

Each checker is a separate process with its own hand-written expectations, and
none of them imports the page builders' shared helpers except where noted, so a
mistake inside site_common.py cannot make them all agree with it.

Deliberately NOT wired into scripts/build.py: these audit the OUTPUT of that
build, and running them as part of producing it would be circular — a checker
that runs before the pages it reads have been written would be green on a stale
site. build.py stays the thing that produces; this stays the thing that judges.

Exit code is the number of checkers that went RED (0 = all green). The verdict
is the printed summary, not the exit code alone: read it.
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

# name -> (script, args, what it looks at)
CHECKS = [
    ("defects", "check_defects.py", [],
     "data/*.json + the rendered pages: the 5 defect groups this site has shipped"),
    ("figures", "check_figures.py", [],
     "data/i18n/*.json: safety-relevant figures surviving translation"),
    ("404", "check_404.py", [],
     "404.html: one message section per language, resolver, no hreflang"),
    ("lang", "check_lang_switcher.py", [],
     "every rendered page: switcher, flags, hreflang alternates, detector"),
    ("discord", "check_discord_page.py", [],
     "/discord/ vs the bot's own command export, in all 13 languages"),
    # V4.3.0. The half of the skin gate that needs no secret: the page exists in
    # every language, its blob path resolves, the blob is well formed, it is NOT
    # stale against the skin the game ships, and no digit run leaked into the
    # markup. The PIN-bearing half is scripts/check_skin_gate.py, run by hand at
    # release time with AURORA_SKIN_PIN set — it cannot live here because this
    # entry point must stay runnable by anyone.
    ("skin", "check_skin_page.py", [],
     "/skin/ in 13 languages + downloads/sparxie-skin.acsk vs the in-game skin"),
]


def main():
    argv = sys.argv[1:]
    if "--list" in argv:
        for name, script, _a, what in CHECKS:
            print(f"  {name:9} {script:24} {what}")
        return 0
    want = [a for a in argv if not a.startswith("-")]
    todo = [c for c in CHECKS if not want or c[0] in want]
    unknown = [w for w in want if w not in {c[0] for c in CHECKS}]
    if unknown:
        raise SystemExit(f"ERROR: no such check: {', '.join(unknown)}. "
                         f"Known: {', '.join(c[0] for c in CHECKS)}")

    results = []
    for name, script, args, _what in todo:
        path = HERE / script
        print(f"\n{'=' * 72}\n== {name}  ({script})\n{'=' * 72}")
        if not path.exists():
            print(f"  RED  {script} is missing from scripts/")
            results.append((name, None))
            continue
        r = subprocess.run([sys.executable, str(path), *args])
        results.append((name, r.returncode))

    print(f"\n{'=' * 72}\nSUMMARY")
    red = 0
    for name, code in results:
        if code is None:
            verdict, red = "MISSING", red + 1
        elif code == 0:
            verdict = "GREEN"
        else:
            verdict, red = f"RED (exit {code})", red + 1
        print(f"  {name:9} {verdict}")
    print(f"\n{red} of {len(results)} checker(s) RED")
    return red


if __name__ == "__main__":
    sys.exit(main())
