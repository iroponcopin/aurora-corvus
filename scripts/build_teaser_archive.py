#!/usr/bin/env python3
"""Keeps every advance notice the Coming-next board has published: data/teasers.json.

The board (data/upcoming.json) only ever shows what is still to come; an entry leaves it the day its
release ships, and its prose was gone with it. The portal's Teasers page plays and lists them again,
so this file keeps each one after it leaves:

  * an id the board carries for the first time is added, `announced` stamped with today's date;
  * while an id is on the board its prose, status and target follow the board (the latest wording);
  * the day an id leaves the board it is stamped `retired` and keeps the last prose it had.

Glimpse Alpha's notices are not kept while Alpha is retired (data/retirement.json): the owner had Alpha
erased from the site on 2026-09-28 (「Alphaは公式に配信を終了したことを記載し、抹消」), and this file
would otherwise bring its history back.

build_upcoming.py runs this after it writes the feed, so a board change is archived without a step
to remember. Run it by hand with no arguments to do the same.

    python3 scripts/build_teaser_archive.py               # merge the board into the archive
    python3 scripts/build_teaser_archive.py --check       # refuse if the archive is behind the board
    python3 scripts/build_teaser_archive.py --from-git D  # rebuild from the board's git history in D

`--from-git` replays every commit that touched data/upcoming.json (a full or a blobless clone will
do: `git clone --bare --filter=blob:none ...`), which is how the archive was first filled.
"""
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOARD = ROOT / "data" / "upcoming.json"
ARCHIVE = ROOT / "data" / "teasers.json"
RETIREMENT = ROOT / "data" / "retirement.json"
LANGS = ["ja", "en", "es", "fr", "zh", "ko", "pt-br", "it", "ar", "ru", "id", "de", "tr"]
NOTE = (
    "Every advance notice the Coming-next board (data/upcoming.json) has published, kept after it leaves "
    "the board, for the portal's Teasers page. Written by scripts/build_teaser_archive.py (build_upcoming.py "
    "runs it): `announced` is the day an id first appeared on the board, `retired` the day it left (null while "
    "it is still there), `prose` the last wording it had in each language. Glimpse Alpha's notices are not "
    "kept while Alpha is retired and erased (data/retirement.json; owner, 2026-09-28)."
)


def kept(kind: str | None, retired_brands: set[str]) -> bool:
    """Alpha's notices are kind "pack" (the Glimpse Alpha pack); a retired brand's are not kept."""
    brand = "alpha" if kind in (None, "pack") else kind
    return brand not in retired_brands


def retired_brands() -> set[str]:
    if not RETIREMENT.exists():
        return set()
    data = json.loads(RETIREMENT.read_text(encoding="utf-8"))
    return {k for k, v in data.items() if isinstance(v, dict) and v.get("retired")}


def prose_of(board: dict, eid: str) -> dict:
    out = {}
    for lang in LANGS:
        block = board.get(lang)
        entries = block.get("entries") if isinstance(block, dict) else None
        if isinstance(entries, dict) and eid in entries:
            p = entries[eid]
            out[lang] = {k: p[k] for k in ("headline", "target_label", "body", "items") if k in p}
    return out


def merge(archive: list[dict], board: dict, day: str, retired: set[str]) -> list[dict]:
    """One board state into the archive (pure: returns a new list, in first-announced order)."""
    by_id = {t["id"]: dict(t) for t in archive}
    order = [t["id"] for t in archive]
    on_board = []
    for e in board.get("entries", []):
        if not kept(e.get("kind"), retired):
            continue
        eid = e["id"]
        on_board.append(eid)
        t = by_id.get(eid)
        if t is None:
            t = {"id": eid, "announced": day}
            order.append(eid)
        t.update({"kind": e.get("kind") or "pack", "url_path": e.get("url_path") or "upcoming/",
                  "status": e.get("status"), "target": e.get("target"), "retired": None})
        prose = prose_of(board, eid)
        if prose:
            t["prose"] = prose
        by_id[eid] = t
    for eid, t in by_id.items():
        if eid not in on_board and t.get("retired") is None:
            t["retired"] = day
    return [by_id[i] for i in order if kept(by_id[i].get("kind"), retired)]


def document(teasers: list[dict]) -> dict:
    return {"_note": NOTE, "teasers": teasers}


def load_archive() -> list[dict]:
    if not ARCHIVE.exists():
        return []
    return json.loads(ARCHIVE.read_text(encoding="utf-8")).get("teasers", [])


def write(teasers: list[dict]) -> bool:
    text = json.dumps(document(teasers), ensure_ascii=False, indent=1) + "\n"
    if ARCHIVE.exists() and ARCHIVE.read_text(encoding="utf-8") == text:
        return False
    ARCHIVE.write_text(text, encoding="utf-8")
    return True


def from_git(git_dir: str, retired: set[str]) -> list[dict]:
    git = ["git", "--git-dir", git_dir]
    log = subprocess.run(git + ["log", "--reverse", "--format=%H %cI", "main", "--", "data/upcoming.json"],
                         capture_output=True, text=True, check=True).stdout.split("\n")
    archive: list[dict] = []
    for line in filter(None, log):
        sha, when = line.split()
        shown = subprocess.run(git + ["show", f"{sha}:data/upcoming.json"], capture_output=True, text=True)
        if shown.returncode != 0:
            continue  # the commit deleted the file
        day = datetime.fromisoformat(when).astimezone(timezone.utc).date().isoformat()
        archive = merge(archive, json.loads(shown.stdout), day, retired)
    return archive


def update() -> str:
    """Merge today's board into the archive (what build_upcoming.py calls after it writes the feed)."""
    archive = merge(load_archive(), json.loads(BOARD.read_text(encoding="utf-8")),
                    datetime.now(timezone.utc).date().isoformat(), retired_brands())
    changed = write(archive)
    on = sum(1 for t in archive if t["retired"] is None)
    return (f"teasers: {len(archive)} kept ({on} still on the board), {'written' if changed else 'unchanged'}: "
            f"{ARCHIVE.relative_to(ROOT)}")


def main() -> int:
    args = sys.argv[1:]
    retired = retired_brands()
    board = json.loads(BOARD.read_text(encoding="utf-8"))
    today = datetime.now(timezone.utc).date().isoformat()
    if args[:1] == ["--from-git"]:
        if len(args) < 2:
            raise SystemExit("build_teaser_archive: --from-git needs the path of a clone's git directory")
        # The history ends at the last commit; the board on disk may be newer, and merging it is idempotent.
        archive = merge(from_git(args[1], retired), board, today, retired)
    elif args[:1] != ["--check"]:
        print(update())
        return 0
    else:
        archive = merge(load_archive(), board, today, retired)
    if args[:1] == ["--check"]:
        current = load_archive()
        stale = [t["id"] for t in archive if t not in current]
        if stale:
            print(f"TEASER ARCHIVE = BEHIND the board ({', '.join(stale)}): run scripts/build_teaser_archive.py")
            return 1
        print(f"TEASER ARCHIVE = PASS ({len(current)} teasers, the board's {sum(1 for t in current if t['retired'] is None)} included)")
        return 0
    changed = write(archive)
    on = sum(1 for t in archive if t["retired"] is None)
    print(f"teasers: {len(archive)} kept ({on} still on the board), {'written' if changed else 'unchanged'}: "
          f"{ARCHIVE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
