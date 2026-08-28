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

The "launcher" block is OMITTED only when downloads/ has never held a
launcher jar at all. We do not invent placeholder launcher facts just to
keep the schema "complete" — an absent key is honest; a fabricated sha256 is
not. But an absent key is only honest when the launcher really has not
shipped: once data/launcher_notes.json lists released versions, a downloads/
folder with no jar in it means the *lookup* broke, not that the product
vanished, and build() now stops loudly instead of publishing a manifest that
would switch off self-update for every installed launcher.

Jar discovery and version ordering live in site_common (find_launcher_jars /
newest_launcher_jar) so this script and build_download.py cannot drift apart
about which file is "current" — see the comment there for the two bugs the
old private copies shared.
"""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from site_common import (  # noqa: E402
    ROOT, LAUNCHER_APP_NAME, newest_launcher_jar, launcher_native_files,
    PACK_NAME, pack_zip_path,
)

MC_VERSION = "26.2"
DOWNLOAD_DIR = ROOT / "downloads"
SITE_BASE_URL = "https://iroponcopin.github.io/aurora-corvus"


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
    # Filename from site_common.pack_zip_name() — see the note there about the
    # V2.5.0 Glimpse_Alpha_MODs_* -> Alpha_MODs_* rename. This one matters
    # most of the three: Corvus downloads exactly the `file_name` this block
    # publishes, so a name invented here is a 404 for every installed app.
    return pack_zip_path(version, MC_VERSION, why="glimpse_manifest.json")


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


def _launcher_notes_table():
    notes_path = ROOT / "data" / "launcher_notes.json"
    if not notes_path.exists():
        return notes_path, {}
    return notes_path, json.loads(notes_path.read_text(encoding="utf-8"))


def _launcher_block(release):
    """release is a dict from site_common.newest_launcher_jar()."""
    jar_path = release["path"]
    version = release["version"]
    size_bytes = jar_path.stat().st_size
    sha256_hex = _sha256(jar_path)

    notes_path, notes_table = _launcher_notes_table()
    if version not in notes_table:
        raise SystemExit(
            f"ERROR: {notes_path} has no entry for launcher version {version!r} - add real release "
            f"notes there before publishing this build (see the existing entries for the style: "
            f"plain, honest, no invented features)."
        )

    block = {
        "latest": version,
        "download_url": f"{SITE_BASE_URL}/downloads/{jar_path.name}",
        "file_name": jar_path.name,
        "file_size": size_bytes,
        "sha256": sha256_hex,
        "notes": notes_table[version],
    }

    # Native builds: produced by the launcher project's own GitHub Actions CI
    # (real macOS/Windows/Linux runners), copied here by hand from the CI
    # run's artifacts. Included only for platforms that actually have a
    # published file -- read straight from disk, never assumed.
    native = {}
    for n in launcher_native_files(version, DOWNLOAD_DIR):
        native[n["platform_id"]] = {
            "download_url": f"{SITE_BASE_URL}/downloads/{n['file_name']}",
            "file_name": n["file_name"],
            "file_size": n["size_bytes"],
            "sha256": _sha256(n["path"]),
        }
    if native:
        block["native"] = native
    return block


def build():
    version = _mod_version()
    zpath = _zip_path(version)
    entry = _changelog_entry(version)
    size_bytes = zpath.stat().st_size
    sha256_hex = _sha256(zpath)
    published_at = f"{entry['date']}T00:00:00+00:00"

    manifest = {
        "pack": {
            # `id` is a stable key, not a display name: Corvus keys its
            # installed-pack record off it, so the V2.5.0 brand rename
            # deliberately does NOT touch it. Renaming it would orphan every
            # existing install's record. `title` below carries the new name.
            "id": "glimpse-pack",
            "latest": version,
            "published_at": published_at,
            "title": f"{PACK_NAME} {entry['release']}",
            "summary": _english_summary(entry),
            "download_url": f"{SITE_BASE_URL}/downloads/{zpath.name}",
            "file_name": zpath.name,
            "file_size": size_bytes,
            "sha256": sha256_hex,
            "changelog_url": f"{SITE_BASE_URL}/en/changelog/",
        }
    }

    release = newest_launcher_jar(DOWNLOAD_DIR)
    if release is not None:
        manifest["launcher"] = _launcher_block(release)
        print(f"glimpse_manifest.py: {LAUNCHER_APP_NAME} build {release['file_name']} "
              f"(version {release['version']}) selected, including 'launcher' block")
    else:
        # An empty result is only acceptable before the first launcher ever
        # shipped. After that it means the discovery broke (a rename, a moved
        # folder) and shipping a manifest without a launcher block would
        # silently switch off self-update for everyone already running it.
        _notes_path, notes_table = _launcher_notes_table()
        if notes_table:
            raise SystemExit(
                "ERROR: no launcher jar found in %s, but %s already lists released versions "
                "(%s). A manifest with no 'launcher' block would silently disable self-update "
                "for every installed %s. Publish the jar, or fix the naming - do not ship this."
                % (DOWNLOAD_DIR, _notes_path,
                   ", ".join(sorted(notes_table)), LAUNCHER_APP_NAME))
        print("glimpse_manifest.py: no launcher jar found yet - writing manifest with 'pack' "
              "only (expected until the first launcher build ships)")

    out_path = ROOT / "glimpse_manifest.json"
    out_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out_path} (pack version {version}, sha256 {sha256_hex[:12]}...)")


if __name__ == "__main__":
    build()
