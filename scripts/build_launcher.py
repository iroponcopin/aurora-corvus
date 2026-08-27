#!/usr/bin/env python3
"""Builds launcher/index.html for every language that has a bundle — the
player-facing guide to Glimpse Launcher (the desktop auto-updater for the
Glimpse Alpha mod pack, built by a separate project against
glimpse_manifest.json).

Follows the same pattern as build_guide.py: page()/write_page() from
site_common.py, one page per available_langs() language. Real content is
authored in English and Japanese only (bundle["launcher_page"], added to
data/i18n/en.json and data/i18n/ja.json); the other 11 languages don't have
a translated bundle entry yet, so this script falls back to the English
copy defined in _DEFAULT_SECTIONS below — the same "English default in the
build script" convention build_download.py already uses via dl.get(key,
"..."), rather than a half-translated or blank page.

Content discipline: describes only what's specified for Glimpse Launcher —
keeping the pack up to date, verifying downloads by SHA-256 against this
Wiki, pointing it at an existing pack folder, automatic vs manual update
mode, and restoring from a backup. Nothing beyond that is claimed.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from site_common import esc, page, write_page, load_bundle, available_langs  # noqa: E402

# English fallback content — used whenever a language bundle has no
# "launcher_page" key of its own (currently: every language except en/ja).
_DEFAULT_INTRO = (
    "Glimpse Launcher is a small desktop app that keeps your Glimpse Alpha mod pack up to "
    "date automatically. It checks this Wiki for the current release, downloads updates for "
    "you, and verifies every file it downloads against a SHA-256 checksum published here "
    "before it touches your pack folder. This Wiki is the only source it trusts — it does not "
    "pull updates from anywhere else."
)
_DEFAULT_SECTIONS = [
    {
        "id": "what-it-is",
        "title": "What it is, and why it exists",
        "body_html": (
            "<p>Keeping a large mod pack up to date by hand means re-visiting the Download page, "
            "comparing version numbers, downloading a new ZIP, and re-extracting it into the "
            "right folder every time a release ships. Glimpse Launcher automates that: it reads "
            "this Wiki's release manifest, compares it against the pack you already have "
            "installed, and fetches only what's changed.</p>"
            "<p>Every download the launcher makes is checked against a SHA-256 checksum "
            "published by this Wiki before it's used. If a downloaded file doesn't match, the "
            "launcher will not install it. The Wiki is the launcher's only source of truth for "
            "what the \"current\" release is.</p>"
        ),
    },
    {
        "id": "installing",
        "title": "Installing Glimpse Launcher",
        "body_html": (
            "<p>Glimpse Launcher is available from the Download page on this Wiki in two forms — "
            "the same place the mod pack ZIP itself is distributed:</p>"
            "<ul>"
            "<li><strong>Native installers</strong> (a Windows <code>.msi</code>, a macOS "
            "<code>.dmg</code>, a Linux <code>.deb</code>) — install like a normal desktop app, "
            "no Java required. These are not code-signed yet, so your OS will show a first-run "
            "warning: on macOS, right-click the app and choose Open instead of double-clicking; "
            "on Windows, click \"More info\" then \"Run anyway\" on the SmartScreen prompt.</li>"
            "<li><strong>The cross-platform jar</strong>, <code>glimpse-launcher-1.2.0.jar</code> "
            "— the same file runs on Windows, macOS, and Linux, but needs Java 21 or newer "
            "already installed. If double-clicking it doesn't open it, run "
            "<code>java -jar glimpse-launcher-1.2.0.jar</code> from a terminal or command prompt "
            "in the folder you downloaded it to.</li>"
            "</ul>"
        ),
    },
    {
        "id": "pointing-at-existing-pack",
        "title": "Pointing it at an existing pack folder",
        "body_html": (
            "<p>If you've already installed Glimpse Alpha manually, you don't need to start "
            "over. On first run, the launcher lets you choose the folder your mod pack already "
            "lives in instead of creating a new one. Point it at your existing mods folder and "
            "the launcher will treat that installation as the one it manages from then on.</p>"
        ),
    },
    {
        "id": "update-modes",
        "title": "Automatic vs. manual update mode",
        "body_html": (
            "<p>In <strong>automatic mode</strong>, the launcher checks this Wiki's release "
            "manifest on its own and installs new versions as soon as they're available, so your "
            "pack folder stays current without you having to do anything.</p>"
            "<p>In <strong>manual mode</strong>, the launcher still checks for updates, but waits "
            "for you to review and confirm before it downloads or installs anything — useful if "
            "you'd rather choose exactly when an update lands, for example to avoid interrupting "
            "a play session.</p>"
        ),
    },
    {
        "id": "confirming-an-update-applied",
        "title": "Confirming an update actually applied",
        "body_html": (
            "<p>As of version 1.1.0, clicking Update writes the new mod files directly into your "
            "pack's <code>mods</code> folder, and the launcher will not show \"Update complete\" "
            "unless it has re-checked the folder afterwards and confirmed the expected files are "
            "really there. If something goes wrong partway through, it reports failure instead of "
            "a false success.</p>"
            "<p>To see the change for yourself on macOS: open the folder shown in Settings "
            "(<kbd>&#8984;</kbd>+<kbd>&#8679;</kbd>+<kbd>G</kbd> in Finder, then paste the path), "
            "look inside <code>mods</code>, and check the version number in each "
            "<code>glimpse-alpha-*.jar</code> filename before and after clicking Update.</p>"
            "<p class=\"callout callout--info\">If you're updating from a pack folder that was "
            "last touched by a launcher older than 1.1.0, the very first update may leave one "
            "old-versioned jar sitting alongside the new one for that mod (the launcher didn't "
            "yet have a record of which files it had previously placed). This clears up on its "
            "own from the next update onward. If it bothers you sooner, it's safe to delete the "
            "older-numbered <code>glimpse-alpha-*.jar</code> by hand once the new one is "
            "confirmed present.</p>"
        ),
    },
    {
        "id": "restoring-from-backup",
        "title": "Restoring from a backup if an update goes wrong",
        "body_html": (
            "<p>If an update leaves your pack in a state you don't want — a mod misbehaving, or "
            "an update you'd rather undo — the launcher keeps a backup of your previous pack "
            "state so you can restore it. Use the launcher's restore option to roll your pack "
            "folder back to the backed-up version rather than trying to fix files by hand.</p>"
        ),
    },
]


def _launcher_content(bundle):
    lp = bundle.get("launcher_page")
    if lp and lp.get("sections"):
        return lp.get("intro", _DEFAULT_INTRO), lp["sections"]
    return _DEFAULT_INTRO, _DEFAULT_SECTIONS


def section_html(sec):
    return f"""<div class="card" style="margin-bottom:20px;">
      <h2 style="margin-top:0;border-top:none;padding-top:0;">{esc(sec['title'])}</h2>
      {sec['body_html']}
    </div>"""


def build_lang(lang):
    bundle = load_bundle(lang)
    ui = bundle["ui"]
    intro, sections = _launcher_content(bundle)

    toc_items = "".join(f'<li><a href="#{esc(s["id"])}">{esc(s["title"])}</a></li>' for s in sections)
    sections_html = "\n".join(f'<div id="{esc(s["id"])}">{section_html(s)}</div>' for s in sections)

    title = ui["page_titles"].get("launcher", "Glimpse Launcher")
    description = ui["page_descriptions"].get(
        "launcher",
        "What Glimpse Launcher is, how to install it, point it at an existing pack folder, use "
        "automatic or manual update mode, and restore from a backup."
    )

    body = f"""
<div class="hero">
  <span class="hero__eyebrow">{esc(title)}</span>
  <h1>{esc(title)}</h1>
  <p class="lede">{esc(intro)}</p>
</div>
<div class="toc"><div class="toc__title">{esc(ui['common'].get('toc_label', 'On this page'))}</div><ol>{toc_items}</ol></div>
{sections_html}
"""
    html = page(
        lang=lang,
        section="launcher/",
        title=title,
        description=description,
        active="launcher",
        body=body,
        depth=1,
    )
    write_page(lang, "launcher/", html)


def build():
    for lang in available_langs():
        build_lang(lang)


if __name__ == "__main__":
    build()
