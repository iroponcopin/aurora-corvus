#!/usr/bin/env python3
"""Builds /upcoming/ in every language, and the upcoming.json feed the bot polls.

This page is the "coming next" board: what is being worked on, told before it
is settled. It is NOT the roadmap (long-range intentions, some of them years
out) and NOT the changelog (what actually shipped). Those two already exist
and neither could carry this without becoming a worse version of itself --
the roadmap would bury next month under five years, and the changelog cannot
list something that has not happened.

Unlike /v4/, this page is PERMANENT. It has no removal steps because it never
empties: when V3.8.0 ships, its entry moves out of data/upcoming.json and the
next one moves in.

== The feed ==============================================================
build() also writes upcoming.json at the site root, next to releases.json and
glimpse_manifest.json, and the Discord bot polls it exactly as it polls those.
That is deliberate: the site stays the single source of truth, so what a
visitor reads and what Discord announces cannot disagree.

The feed carries ENGLISH prose, matching releases.json (whose "title" is
"Alpha V3.7.0" and whose summary is English). One language in the feed keeps
the bot's own embeds in one language; the page itself is in all thirteen.

Announcement identity is the entry's `id`, never its prose. Editing the text
of an already-announced entry must not re-announce it; adding a new id must.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from site_common import (  # noqa: E402
    ROOT, SITE_BASE_URL, esc, page, write_page, available_langs, asset_root_prefix,
)

DATA_PATH = ROOT / "data" / "upcoming.json"
FEED_PATH = ROOT / "upcoming.json"

#: The language whose prose goes into the machine-readable feed. See header.
FEED_LANG = "en"

#: Statuses an entry may declare. A typo here would render a blank badge, so
#: it fails instead.
KNOWN_STATUSES = ("planned", "in_progress")


def _load():
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    entries = data.get("entries") or []
    if not entries:
        raise SystemExit(
            "upcoming: data/upcoming.json lists no entries. An empty 'coming next' page is "
            "not a page -- either add an entry or take the nav link down deliberately, "
            "rather than shipping a heading with nothing under it."
        )
    seen = set()
    for e in entries:
        for key in ("id", "status", "target"):
            if not e.get(key):
                raise SystemExit(f"upcoming: entry {e!r} is missing '{key}'.")
        if e["status"] not in KNOWN_STATUSES:
            raise SystemExit(
                f"upcoming: entry '{e['id']}' has status {e['status']!r}, which is not one of "
                f"{KNOWN_STATUSES}. Its badge would render blank in all 13 languages."
            )
        if e["id"] in seen:
            raise SystemExit(
                f"upcoming: entry id '{e['id']}' appears twice. The bot keys 'already "
                f"announced' on the id, so a duplicate would announce once and hide the other."
            )
        seen.add(e["id"])
    return data, entries


def _entry_html(lang, entry, prose, labels, prefix):
    text = prose[entry["id"]]
    items = "".join(f"<li>{esc(i)}</li>" for i in text["items"])
    badge = esc(labels.get(entry["status"], entry["status"]))
    link = ""
    if entry.get("url_path") and entry["url_path"] != "upcoming/":
        link = (f'<p class="up-more"><a href="../{esc(entry["url_path"])}">'
                f'{esc(text["headline"])} →</a></p>')
    return f"""
<section class="card up-entry">
  <p class="up-meta">
    <span class="up-badge up-badge--{esc(entry['status'])}">{badge}</span>
    <span class="up-target">{esc(text['target_label'])}</span>
  </p>
  <h2>{esc(text['headline'])}</h2>
  <p class="up-body">{esc(text['body'])}</p>
  <ul class="up-items">{items}</ul>
  {link}
</section>"""


def build_lang(lang, data, entries):
    t = data[lang]
    prefix = asset_root_prefix(1, lang)
    body = [f"""
<div class="hero up-hero">
  <h1>{esc(t['title'])}</h1>
  <p class="up-intro">{esc(t['intro'])}</p>
</div>"""]
    for entry in entries:
        body.append(_entry_html(lang, entry, t["entries"], t["status_labels"], prefix))
    body.append(f"""
<section class="card up-disclaimer">
  <p>{esc(t['disclaimer'])}</p>
</section>""")
    return page(
        lang=lang, section="upcoming/", title=t["title"], description=t["description"],
        active="upcoming", body="\n".join(body), depth=1,
    )


def write_feed(data, entries):
    """The machine-readable half, for the bot.

    Deliberately flat and small: the bot needs an id to key announcements on,
    a headline to print, and a URL to point at. Everything else on the page
    is for humans and stays on the page.
    """
    prose = data[FEED_LANG]["entries"]
    labels = data[FEED_LANG]["status_labels"]
    feed = {
        "generated_at": datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0).isoformat(),
        "page_url": f"{SITE_BASE_URL}/upcoming/",
        "entries": [
            {
                "id": e["id"],
                "status": e["status"],
                "status_label": labels.get(e["status"], e["status"]),
                "target": e["target"],
                "headline": prose[e["id"]]["headline"],
                "body": prose[e["id"]]["body"],
                "items": list(prose[e["id"]]["items"]),
                "url": f"{SITE_BASE_URL}/{e.get('url_path', 'upcoming/')}",
            }
            for e in entries
        ],
    }
    FEED_PATH.write_text(json.dumps(feed, ensure_ascii=False, indent=2) + "\n",
                         encoding="utf-8")
    print(f"wrote {FEED_PATH.relative_to(ROOT)} ({len(feed['entries'])} entries, "
          f"{FEED_LANG} prose)")


def main():
    data, entries = _load()
    langs = available_langs()
    built = 0
    for lang in langs:
        if lang not in data:
            raise SystemExit(
                f"upcoming: data/upcoming.json has no block for '{lang}'. Falling back to "
                f"Japanese for one language would be a silent regression on a page whose "
                f"whole job is telling people what is coming."
            )
        missing = [e["id"] for e in entries if e["id"] not in data[lang]["entries"]]
        if missing:
            raise SystemExit(
                f"upcoming: '{lang}' has no prose for entries {missing}. The page would render "
                f"that entry as an empty card."
            )
        write_page(lang, "upcoming/", build_lang(lang, data, entries))
        built += 1
    if built == 0:
        raise SystemExit("upcoming: built ZERO pages; available_langs() returned nothing.")
    write_feed(data, entries)
    print(f"upcoming: {built} languages, {len(entries)} entries")


if __name__ == "__main__":
    main()
