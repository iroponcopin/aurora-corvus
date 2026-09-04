#!/usr/bin/env python3
"""Builds /upcoming/ in every language, and the upcoming.json feed the bot polls.

This page is the "coming next" board: what is being worked on, told before it
is settled. It is NOT the roadmap (long-range intentions, some of them years
out) and NOT the changelog (what actually shipped). Those two already exist
and neither could carry this without becoming a worse version of itself --
the roadmap would bury next month under five years, and the changelog cannot
list something that has not happened.

Unlike /v4/, this page is PERMANENT. It has no removal steps. It was first
written on the assumption that it never empties (when V3.8.0 ships, its entry
moves out and the next one moves in), but on 2026-09-02 V4.0.1 shipped with
nothing decided after it. An empty board is therefore a real state, and it is
rendered honestly: every language must provide an `empty` line ("nothing is
scheduled right now"), the page shows that line instead of cards, and the feed
carries `"entries": []` so the bot keeps a valid file to poll. A board with
zero entries and no `empty` line still refuses to build -- that is the case
where somebody deleted the last entry without deciding what the page says.

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
        lacking = [lang for lang, block in data.items()
                   if isinstance(block, dict) and "entries" in block and not block.get("empty")]
        if lacking:
            raise SystemExit(
                "upcoming: data/upcoming.json lists no entries, and these languages have no "
                f"'empty' line to show instead: {lacking}. An empty board is a real state "
                "(V4.0.1, 2026-09-02) but it must SAY so in every language -- either add the "
                "next entry or write the 'empty' line, rather than shipping a heading with "
                "nothing under it."
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


_INLINE_TAG = __import__("re").compile(r"</?[A-Za-z][A-Za-z0-9]*(?:\\s[^>]*)?/?>")


def _refuse_markup(lang, eid, field, value):
    """**この頁の散文は素のテキストである。**タグを書いても描画されない。

    2026-09-04 実測: V4.2.1 と V4.2.2 の予告に書いた <b> は `esc()` に食われて
    <b>そのまま文字として</b>出ており、公開中の頁で読者に見えていた
    (13 言語 × 36 か所)。更新履歴の散文 71 件には 1 つもタグが無い ——
    つまり素のテキストがこの site の作法で、予告だけがそれを破っていた。
    escape は安全側の既定として正しいので、直すべきは<b>黙って通したこと</b>である。
    強調したいならその言語の言い回しで書くこと(鍵括弧など)。
    """
    m = _INLINE_TAG.search(value)
    if m:
        raise SystemExit(
            f"upcoming: {lang}/{eid} の {field} に HTML タグ {m.group(0)!r} がある。"
            f"この頁は散文を escape するので、タグは描画されず**文字として出る**。"
            f"data/upcoming.json から取り除くこと。"
        )


def _entry_html(lang, entry, prose, labels, prefix):
    text = prose[entry["id"]]
    for field in ("headline", "target_label", "body"):
        _refuse_markup(lang, entry["id"], field, text[field])
    for n, item in enumerate(text["items"]):
        _refuse_markup(lang, entry["id"], f"items[{n}]", item)
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
    if not entries:
        body.append(f"""
<section class="card up-entry up-entry--empty">
  <p class="up-body">{esc(t['empty'])}</p>
</section>""")
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
