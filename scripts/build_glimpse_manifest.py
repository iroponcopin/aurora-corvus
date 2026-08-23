#!/usr/bin/env python3
"""Builds glimpse_manifest.json at the repo root — the contract the Glimpse
Launcher desktop app (a separate project, built independently) polls to
check for pack/launcher updates.

This is a DIFFERENT file from releases.json (see build_releases_feed.py):
releases.json already has a tested consumer (the Discord release bot) with
a fixed schema, and must not be repurposed. glimpse_manifest.json is a new,
separate contract for the launcher.

Design note: same discipline as build_releases_feed.py / build_download.py —
every fact here is computed from the real shipped ZIP and data/*.json at
build time, never typed as a literal. If a fact is missing (no matching
changelog entry, no ZIP on disk), the build stops loudly rather than
inventing one.

The "launcher" block is OMITTED entirely unless a real
downloads/glimpse-launcher-*.jar exists on disk. We do not invent
placeholder launcher facts just to keep the schema "complete" — an absent
key is honest; a fabricated sha256 is not.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from site_common import ROOT  # noqa: E402

MC_VERSION = "26.2"
DOWNLOAD_DIR = ROOT / "downloads"
SITE_BASE_URL = "https://iroponcopin.github.io/glimpse-alpha-wiki"


def _mod_version():
    mods = json.loads((ROOT / "data" / "versions.json").read_text(encoding="utf-8"))["mods"]
    versions = set(mods.values())
    if len(versions) != 1:
        raise SystemExit(
            f"ERROR: data/versions.json lists more than one distinct version {sorted(versions)} "
            f"- glimpse_manifest.json cannot describe a single pack release when the table "
            f"itself disagrees."
        )
    return versions.pop()


def _zip_path(version):
    name = f"Glimpse_Alpha_MODs_v{version}+mc{MC_VERSION}.zip"
    p = DOWNLOAD_DIR / name
    if not p.exists():
        raise SystemExit(
            f"ERROR: {p} does not exist. glimpse_manifest.json must not describe a file that "
            f"isn't actually in the wiki's served tree."
        )
    return p


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _changelog_entry(version):
    entries = json.loads((ROOT / "data" / "changelog.json").read_text(encoding="utf-8"))
    for e in entries:
        rel = str(e.get("release", "")).lstrip("vV")
        if rel == version:
            return e
    raise SystemExit(
        f"ERROR: data/changelog.json has no entry with release == V{version}. "
        f"glimpse_manifest.json needs a real title/summary/date, not an invented one."
    )


def _english_summary(entry):
    """Same derivation as build_releases_feed.py's _english_summary: a
    plain, honest English restatement of release type + highlight count,
    not a translation of the Japanese summary field."""
    kind = "Hotfix" if entry.get("type") == "hotfix" else "Release"
    highlight_count = len(entry.get("highlights", []))
    if highlight_count:
        return (f"{kind} {entry['release']}. {highlight_count} change(s) in this update - "
                f"see the full changelog on the Wiki for details.")
    return f"{kind} {entry['release']}. See the full changelog on the Wiki for details."


def _find_launcher_jar():
    """Returns a Path to the real launcher jar if one has been published to
    downloads/, else None. Does not invent one."""
    candidates = sorted(DOWNLOAD_DIR.glob("glimpse-launcher-*.jar"))
    return candidates[0] if candidates else None


_LAUNCHER_VERSION_RE = re.compile(r"^glimpse-launcher-(.+)\.jar$")


def _launcher_block(jar_path):
    m = _LAUNCHER_VERSION_RE.match(jar_path.name)
    if not m:
        raise SystemExit(
            f"ERROR: {jar_path} does not match the expected glimpse-launcher-<version>.jar "
            f"naming pattern - cannot determine its version without guessing."
        )
    version = m.group(1)
    size_bytes = jar_path.stat().st_size
    sha256_hex = _sha256(jar_path)

    notes_path = ROOT / "data" / "launcher_notes.json"
    notes_table = json.loads(notes_path.read_text(encoding="utf-8")) if notes_path.exists() else {}
    if version not in notes_table:
        raise SystemExit(
            f"ERROR: {notes_path} has no entry for launcher version {version!r} - add real release "
            f"notes there before publishing this build (see the existing entries for the style: "
            f"plain, honest, no invented features)."
        )

    return {
        "latest": version,
        "download_url": f"{SITE_BASE_URL}/downloads/{jar_path.name}",
        "file_name": jar_path.name,
        "file_size": size_bytes,
        "sha256": sha256_hex,
        "notes": notes_table[version],
    }


def build():
    version = _mod_version()
    zpath = _zip_path(version)
    entry = _changelog_entry(version)
    size_bytes = zpath.stat().st_size
    sha256_hex = _sha256(zpath)
    published_at = f"{entry['date']}T00:00:00+00:00"

    manifest = {
        "pack": {
            "id": "glimpse-pack",
            "latest": version,
            "published_at": published_at,
            "title": f"Glimpse Alpha {entry['release']}",
            "summary": _english_summary(entry),
            "download_url": f"{SITE_BASE_URL}/downloads/{zpath.name}",
            "file_name": zpath.name,
            "file_size": size_bytes,
            "sha256": sha256_hex,
            "changelog_url": f"{SITE_BASE_URL}/en/changelog/",
        }
    }

    jar_path = _find_launcher_jar()
    if jar_path is not None:
        manifest["launcher"] = _launcher_block(jar_path)
        print(f"glimpse_manifest.py: found launcher build {jar_path.name}, including 'launcher' block")
    else:
        print("glimpse_manifest.py: no downloads/glimpse-launcher-*.jar found yet - "
              "writing manifest with 'pack' only (expected until a launcher build ships)")

    out_path = ROOT / "glimpse_manifest.json"
    out_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out_path} (pack version {version}, sha256 {sha256_hex[:12]}...)")


if __name__ == "__main__":
    build()
