#!/usr/bin/env python3
"""
Reads the current (non-superseded, non-quarantined) jar filenames from the
mod pack's dist/ folder and writes data/versions.json — the single source of
truth for "what version is each mod currently at" used on the home page and
recipe pages. Re-run this whenever a new round ships.

The dist/ folder itself is NOT part of this repo (no jars are distributed
here) — this script just reads it from the sibling project directory at
build time.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIST = Path(
    "/Volumes/ORICO/Minecraft Sorakazekarasu Server developer/dist"
)
OUT = ROOT / "data" / "versions.json"

JAR_RE = re.compile(r"^glimpse-alpha-([a-z]+)-([0-9.]+)\+mc([0-9.]+)\.jar$")


def main():
    versions = {}
    mc_version = None
    for jar in sorted(SOURCE_DIST.glob("glimpse-alpha-*.jar")):
        name = jar.name
        if name.endswith((".superseded", ".quarantined")):
            continue
        m = JAR_RE.match(name)
        if not m:
            print(f"skip (unrecognized name): {name}")
            continue
        mod_key, mod_version, mc = m.groups()
        versions[mod_key] = mod_version
        mc_version = mc

    if not versions:
        raise SystemExit("No current jars found — check SOURCE_DIST path.")

    data = {
        "mc_version": mc_version,
        "mods": versions,
        "pack_name": "Glimpse Alpha",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT} : {json.dumps(versions, ensure_ascii=False)}")
    print(f"Minecraft {mc_version}")


if __name__ == "__main__":
    main()
