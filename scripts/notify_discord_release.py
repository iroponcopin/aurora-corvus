#!/usr/bin/env python3
"""Pushes the current release to the Discord release bot's webhook.

This is the "release webhook" trigger path (Option A in the bot's spec) —
optional and separate from the bot's own poller, which already picks up
new releases from releases.json on its own schedule without this script
ever running. Call this manually (or from a future CI step) right after
`python3 scripts/build.py` + `git push`, to get a near-instant Discord
announcement instead of waiting for the next poll.

Never run this before releases.json is rebuilt for the new version and
pushed live - the bot may fetch download_url before it resolves if this
runs first in a race, though in practice the manual "build, commit, push,
then run this" order given in README.md avoids that entirely.

Reads two secrets from the environment, never from argv or a committed
file:
  RELEASE_BOT_WEBHOOK_URL     e.g. http://your-bot-host:8930/hooks/wiki-release
  RELEASE_BOT_WEBHOOK_SECRET  must match WEBHOOK_SECRET in the bot's own .env
"""
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    webhook_url = os.environ.get("RELEASE_BOT_WEBHOOK_URL", "").strip()
    webhook_secret = os.environ.get("RELEASE_BOT_WEBHOOK_SECRET", "").strip()
    if not webhook_url or not webhook_secret:
        raise SystemExit(
            "ERROR: set RELEASE_BOT_WEBHOOK_URL and RELEASE_BOT_WEBHOOK_SECRET in the environment "
            "before running this script (see discord-release-bot/README.md). This script never "
            "reads secrets from argv or from a file in this repo - the bot's webhook secret must "
            "not end up in Wiki git history."
        )

    feed_path = ROOT / "releases.json"
    if not feed_path.exists():
        raise SystemExit(
            f"ERROR: {feed_path} does not exist. Run scripts/build.py first - it writes "
            f"releases.json (via build_releases_feed.py) from the real shipped ZIP."
        )
    payload = json.loads(feed_path.read_text(encoding="utf-8"))

    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        webhook_url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-Webhook-Secret": webhook_secret,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"ERROR: webhook call failed with HTTP {exc.code}: {detail}")
    except urllib.error.URLError as exc:
        raise SystemExit(f"ERROR: could not reach {webhook_url}: {exc.reason}")

    print(f"notified release bot: {result}")
    if result.get("status") == "duplicate":
        print("(the bot had already seen this exact version+sha256 - no message was posted, "
              "which is correct if this release was already announced, e.g. by the poller)")


if __name__ == "__main__":
    main()
