#!/usr/bin/env python3
"""Audits /discord/ against the bot it documents.

The page is generated from data/discord_commands.json, which is a COPY of
discord-release-bot/data/commands.json. A copy is the weak link: rename a
subcommand in the bot, forget to re-copy, and this site keeps confidently
telling people to run a command that no longer exists. Nothing renders wrong,
no build fails, and the page looks exactly as authoritative as before.

So this compares the copy against the original whenever the bot repo is
sitting next to this one, and says so LOUDLY when it cannot -- an audit that
silently checks nothing is worse than no audit, because it reports green.

Written with its own expectations, like every checker here: it re-reads the
built HTML rather than asking build_discord.py what it wrote.

  python3 scripts/check_discord_page.py
"""
import html as htmllib
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BOT_EXPORT = REPO.parent / "discord-release-bot" / "data" / "commands.json"
LOCAL_EXPORT = REPO / "data" / "discord_commands.json"
PROSE = REPO / "data" / "discord_bot.json"

LANGS = ["ja", "en", "es", "fr", "zh", "ko", "pt-br", "it", "ar", "ru", "id", "de", "tr"]

problems = []
checks = 0
skipped = []


def bad(msg):
    problems.append(msg)


def check(cond, msg):
    global checks
    checks += 1
    if not cond:
        bad(msg)
    return cond


def page_path(lang):
    return REPO / ("" if lang == "ja" else lang) / "discord" / "index.html"


def main():
    global checks
    local = json.loads(LOCAL_EXPORT.read_text(encoding="utf-8"))

    # --- 1. the copy still matches the bot ---------------------------------
    if BOT_EXPORT.is_file():
        original = json.loads(BOT_EXPORT.read_text(encoding="utf-8"))
        check(local == original,
              f"{LOCAL_EXPORT.relative_to(REPO)} differs from {BOT_EXPORT}. The page is "
              f"documenting a command surface the bot no longer has. Re-run "
              f"discord-release-bot/export_commands.py and copy the result across.")
    else:
        skipped.append(
            f"the bot repo is not at {BOT_EXPORT}, so the copy could NOT be compared "
            f"against the real command tree. This run does not prove the page is current.")

    # --- 2. every command in the export reaches every rendered page ---------
    expected = []
    for group in local["groups"]:
        for sub in group["subcommands"]:
            expected.append(f"/{group['name']} {sub['name']}")
    check(len(expected) >= 20,
          f"only {len(expected)} commands in the export; the bot has far more than that, "
          f"so the export is truncated and the page is missing most of it.")

    for lang in LANGS:
        path = page_path(lang)
        if not check(path.is_file(), f"{lang}: /discord/ was not built"):
            continue
        text = path.read_text(encoding="utf-8")
        codes = {htmllib.unescape(m) for m in re.findall(r"<code>(/[^<]+)</code>", text)}
        codes = {re.sub(r"\s+", " ", c).strip() for c in codes}
        missing = [c for c in expected if c not in codes]
        check(not missing, f"{lang}: /discord/ never mentions {missing[:4]}"
                           f"{' and more' if len(missing) > 4 else ''}")

        # No command may appear with an empty explanation: that is what a
        # missing translation looks like once it is rendered.
        blanks = re.findall(r"<td><code>(/[^<]+)</code>[^<]*(?:<span[^>]*>[^<]*</span>\s*)*"
                            r"</td>\s*<td>\s*</td>", text)
        check(not blanks, f"{lang}: {blanks[:3]} render with a blank description")

        # The three permission words must both appear: a table where every row
        # says the same thing is not telling anyone anything.
        n_admin = text.count("dc-who--admin")
        n_open = len(re.findall(r'class="dc-who"', text))
        check(n_admin > 0 and n_open > 0,
              f"{lang}: {n_admin} admin / {n_open} open badges — one of the two states "
              f"never renders, so the 'who can use it' column is decoration")
        check(n_admin + n_open == len(expected),
              f"{lang}: {n_admin + n_open} permission badges for {len(expected)} commands")

    # --- 3. the invite link is the real one --------------------------------
    en = page_path("en")
    if en.is_file():
        text = en.read_text(encoding="utf-8")
        m = re.search(r"https://discord\.com/oauth2/authorize\?client_id=(\d+)[^\"']*"
                      r"permissions=(\d+)", htmllib.unescape(text))
        if check(m is not None, "en: /discord/ has no Discord invite link at all"):
            client_id, perms = m.group(1), m.group(2)
            check(len(client_id) >= 17,
                  f"en: invite client_id {client_id!r} is not a Discord snowflake")
            declared = str(local.get("invite_permissions", ""))
            check(perms == declared,
                  f"en: the invite asks for permissions {perms}, but the bot's own export "
                  f"says {declared}. The page is telling people the wrong thing about what "
                  f"they are granting.")
            check("administrator" not in text.lower() or "never asks" in text.lower()
                  or "一切要求しません" in text,
                  "en: the page mentions administrator without saying the bot never asks "
                  "for it")

    # --- 4. every language actually has its own prose ----------------------
    prose = json.loads(PROSE.read_text(encoding="utf-8"))
    for lang in LANGS:
        check(lang in prose, f"data/discord_bot.json has no block for '{lang}'")
    ja_title = prose.get("ja", {}).get("title")
    for lang in LANGS:
        if lang in ("ja",):
            continue
        block = prose.get(lang, {})
        check(block.get("lede") != prose["ja"]["lede"],
              f"{lang}: the lede is the Japanese one verbatim — untranslated")

    for note in skipped:
        print(f"  SKIPPED: {note}")
    for p in problems:
        print(f"  - {p}")
    print(f"\n{checks} assertions over {len(LANGS)} pages and {len(expected)} commands")
    if problems:
        print(f"RED: {len(problems)} failure(s)")
        return 1
    if skipped:
        print("GREEN, but see the SKIPPED note above — not everything could be checked.")
        return 0
    print("GREEN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
