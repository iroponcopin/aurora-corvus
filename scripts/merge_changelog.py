#!/usr/bin/env python3
"""Merges the 4 agent-written changelog chunks into data/changelog.json,
sorted chronologically, with basic sanity checks."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHUNKS = ["A", "B", "C", "D"]


def main():
    entries = []
    for c in CHUNKS:
        p = ROOT / "data" / f"changelog-raw-{c}.json"
        chunk = json.loads(p.read_text(encoding="utf-8"))
        for e in chunk:
            e["_chunk"] = c
            entries.append(e)

    # Sort by date, then keep original within-chunk order for same-date entries
    # (chunks are already internally chronological, and same-date same-release
    # pairs like the v1.8.0 release+hotfix must stay release-then-hotfix).
    entries.sort(key=lambda e: (e.get("date", ""), CHUNKS.index(e["_chunk"])))

    required = {"release", "date", "title", "type", "summary", "highlights"}
    problems = []
    seen_releases = []
    for e in entries:
        missing = required - set(e.keys())
        if missing:
            problems.append(f"{e.get('release')}/{e.get('date')}: missing fields {missing}")
        if e.get("type") not in ("release", "hotfix", "visual-update"):
            problems.append(f"{e.get('release')}: unexpected type {e.get('type')!r}")
        seen_releases.append(e.get("release"))
        for k in ("balance_changes", "warnings", "known_limitations"):
            e.setdefault(k, [])
        e.setdefault("mod_versions", {})
        del e["_chunk"]

    versions = json.loads((ROOT / "data" / "versions.json").read_text(encoding="utf-8"))
    print(f"{len(entries)} total changelog entries, {len(set(seen_releases))} distinct release labels")
    print("date range:", entries[0]["date"], "->", entries[-1]["date"])

    # Cross-check: the final mod_versions mentioned across all entries should
    # reach (but not necessarily exceed) the ground-truth current versions.
    last_seen = {}
    for e in entries:
        for mod, ver in e["mod_versions"].items():
            short = mod.replace("sorakaze_", "")
            last_seen[short] = ver
    for mod, ver in versions["mods"].items():
        seen = last_seen.get(mod)
        if seen != ver:
            problems.append(
                f"mod '{mod}': changelog's last mentioned version is {seen!r}, "
                f"but ground truth (dist/ jar) is {ver!r}"
            )

    if problems:
        print("\n".join("PROBLEM: " + p for p in problems))
    else:
        print("cross-check OK: every mod's last-mentioned changelog version matches its shipped jar")

    out = ROOT / "data" / "changelog.json"
    out.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {out} ({len(entries)} entries)")


if __name__ == "__main__":
    main()
