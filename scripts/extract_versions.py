#!/usr/bin/env python3
"""
Writes data/versions.json — the single source of truth for "what version is
each mod currently at", used on the home page, the download page and the
recipe pages. Re-run this whenever a new round ships, AFTER the release ZIP
has been copied into downloads/.

Where the numbers come from (changed in V2.5.0)
-----------------------------------------------
This script used to read the sibling `dist/` folder. That stopped working
long before anyone noticed:

  * `dist/` has not been refreshed since V2.1.0, and
  * it has never contained sorakaze-sapporo at all.

So from V2.2.x onward, running this script would have written 2.1.0 over a
correct table and silently dropped a module. It was quietly abandoned instead
— V2.4.9's release notes record that data/versions.json "was regenerated from
the jar names inside the shipped ZIP" because "scripts/extract_versions.py
could not be used". A generator that everyone has learned to route around is
not a generator; it is a stale file with a script next to it. Hand-editing
the output every release is exactly the habit this project bans.

It now reads **the release ZIP actually sitting in downloads/** — the same
artifact the download page links, the feeds hash, and players install. That
is the real ground truth for "what shipped", it contains all eleven modules,
and it cannot go stale relative to the site, because it *is* what the site
serves.

Jar naming (V2.5.0 rename)
--------------------------
V2.5.0 renamed the pack "Glimpse Alpha" -> "Alpha", so the jars inside the
ZIP went from `glimpse-alpha-<mod>-<ver>+mc<mc>.jar` to
`alpha-<mod>-<ver>+mc<mc>.jar`. Mod ids did NOT change. Both spellings are
accepted here so this script still works when pointed at an archived
pre-rename ZIP; the short mod key it records is the same either way.

Usage
-----
  python3 scripts/extract_versions.py             # newest ZIP in downloads/
  python3 scripts/extract_versions.py --zip <path>
"""
import argparse
import json
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from site_common import ROOT, DOWNLOADS_DIR, PACK_NAME  # noqa: E402

OUT = ROOT / "data" / "versions.json"

# Accepts both brands: `alpha-guns-2.5.0+mc26.2.jar` (V2.5.0 on) and
# `glimpse-alpha-guns-2.4.9+mc26.2.jar` (archived pre-rename ZIPs).
JAR_RE = re.compile(r"^(?:glimpse-)?alpha-([a-z]+)-([0-9.]+)\+mc([0-9.]+)\.jar$")

# The pack ZIP, either brand — same tolerance as
# tools/check_dist_drift.py's newest_dist_zip().
ZIP_RE = re.compile(r"^(?:Glimpse_)?Alpha_MODs_v(.+)\+mc([0-9.]+)\.zip$")


def newest_pack_zip():
    cands = []
    for p in DOWNLOADS_DIR.glob("*.zip"):
        m = ZIP_RE.match(p.name)
        if m:
            cands.append(([int(x) for x in re.findall(r"\d+", m.group(1))], p))
    if not cands:
        raise SystemExit(
            f"ERROR: no pack ZIP found in {DOWNLOADS_DIR}. Copy the assembled ZIP "
            f"(tools/build_dist_zip.py) into downloads/ before running this."
        )
    cands.sort()
    return cands[-1][1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", dest="zip_path")
    args = ap.parse_args()

    zpath = Path(args.zip_path) if args.zip_path else newest_pack_zip()
    if not zpath.exists():
        raise SystemExit(f"ERROR: {zpath} does not exist.")

    versions = {}
    mc_version = None
    with zipfile.ZipFile(zpath) as z:
        for name in sorted(z.namelist()):
            base = name.rsplit("/", 1)[-1]
            if not base.endswith(".jar"):
                continue
            m = JAR_RE.match(base)
            if not m:
                print(f"skip (unrecognized name): {base}")
                continue
            mod_key, mod_version, mc = m.groups()
            versions[mod_key] = mod_version
            mc_version = mc

    if not versions:
        raise SystemExit(f"ERROR: no recognizable mod jars inside {zpath.name}.")

    # The pack ships as one coordinated version; a mixed table means the ZIP
    # itself is wrong, and every downstream builder (_mod_version) would stop
    # anyway. Fail here, where the cause is visible, rather than there.
    distinct = sorted(set(versions.values()))
    if len(distinct) != 1:
        rows = "\n".join(f"  {k:<14} {v}" for k, v in sorted(versions.items()))
        raise SystemExit(
            f"ERROR: {zpath.name} contains more than one distinct mod version {distinct}:\n{rows}"
        )

    data = {
        "mc_version": mc_version,
        "mods": versions,
        "pack_name": PACK_NAME,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"read {zpath.name}")
    print(f"wrote {OUT} : {len(versions)} modules at {distinct[0]}, Minecraft {mc_version}")


if __name__ == "__main__":
    main()
