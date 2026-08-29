#!/usr/bin/env python3
"""Builds download/index.html for every language that has a bundle.

Design note: every fact on this page (version, file size, sha256, release
date) is computed from the real shipped ZIP and data/*.json at build time —
never typed as a literal in this script or in the i18n bundles. That mirrors
this project's `module_counts()` discipline in site_common.py: a number typed
by hand in 13 language files is a number that goes stale in 12 of them the
next time only one file changes. If the ZIP or its changelog entry is
missing, the build stops loudly instead of publishing an invented value.

The same rule now covers the page's PROSE. `download` is one of four blocks
that live only in data/i18n/*.json with no source file behind them, and until
2026-08-29 scripts/extract_bundle.py deleted all four every time it ran (see
the ⚠ block in scripts/build_features.py). Every one of this page's own
strings was read with `dl.get(key, "")`, so losing the block published a
download page with an empty lede, empty headings, an empty install note and
an empty "do not put this on a server" warning — at exit 0. REQUIRED_KEYS
below stops that. The discord_*/launcher_* keys are deliberately NOT in it:
those genuinely exist in en/ja only and have real English defaults.
"""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from site_common import (  # noqa: E402
    esc, page, write_page, load_bundle, available_langs, ROOT, asset_root_prefix,
    LAUNCHER_APP_NAME, newest_launcher_jar, launcher_native_files,
    load_latest_changelog_entry, PACK_NAME, pack_zip_path,
)

MC_VERSION = "26.2"
DOWNLOAD_DIR = ROOT / "downloads"

# bundle["download"] keys that are rendered with an EMPTY fallback, i.e. the
# ones whose loss shows up as a blank on the page rather than as English. All
# 13 bundles carry all of them.
REQUIRED_KEYS = (
    "intro", "server_note", "sapporo_note",
    "whats_new_heading", "whats_new_body",
    "install_heading", "install_body", "older_versions_note",
    "changelog_link_text", "guide_link_text",
    "version_label", "size_label", "sha_label", "primary_cta",
)


def _require_download_block(bundle, lang):
    if "download" not in bundle:
        raise SystemExit(
            f"ERROR: data/i18n/{lang}.json has no 'download' block at all. It is hand-authored "
            f"directly in the bundle -- there is no data/download.json to rebuild it from, so an "
            f"absent key means the content was DELETED. Publishing this page anyway would put out "
            f"a download page with a blank lede and a blank server warning at exit 0. Restore the "
            f"block (git show HEAD:data/i18n/{lang}.json) before re-running.")
    dl = bundle["download"]
    missing = [k for k in REQUIRED_KEYS if not str(dl.get(k, "")).strip()]
    if missing:
        raise SystemExit(
            f"ERROR: data/i18n/{lang}.json's 'download' block is missing or blank for: "
            f"{', '.join(missing)}. These render with an empty fallback, so the page would "
            f"publish with those paragraphs simply absent and no error.")
    return dl


def _mod_version():
    mods = json.loads((ROOT / "data" / "versions.json").read_text(encoding="utf-8"))["mods"]
    versions = set(mods.values())
    if len(versions) != 1:
        raise SystemExit(
            f"ERROR: data/versions.json lists more than one distinct version {sorted(versions)} "
            f"across its mods - the Download page cannot say a single 'version 2.2.0' when the "
            f"table itself disagrees. Fix versions.json (or teach this page to handle a mixed "
            f"release) before building."
        )
    return versions.pop()


def _zip_path(version):
    # The filename comes from site_common.pack_zip_name(), not an f-string
    # here: the V2.5.0 rename (Glimpse_Alpha_MODs_* -> Alpha_MODs_*) had to be
    # made in one place, not three.
    return pack_zip_path(version, MC_VERSION, why="The Download page")


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _release_date(version):
    """Pull the release date from the matching changelog entry rather than
    typing "today" by hand - a build re-run on a later day must not silently
    relabel an old release as freshly-dated."""
    entries = json.loads((ROOT / "data" / "changelog.json").read_text(encoding="utf-8"))
    for e in entries:
        rel = str(e.get("release", "")).lstrip("vV")
        if rel == version:
            return e["date"]
    raise SystemExit(
        f"ERROR: data/changelog.json has no entry with release == V{version}. The Download page "
        f"needs a real release date, not an invented one - add the changelog entry first "
        f"(a concurrent pass owns data/changelog.json; re-read it fresh before building)."
    )


def _fmt_size(num_bytes):
    mb = num_bytes / (1024 * 1024)
    return f"{mb:.1f} MB"


def _discord_invite():
    """Reads data/discord.json. client_id is a placeholder until the server
    owner registers a real Discord Application (an account-bound step this
    build cannot do on their behalf - see discord-release-bot/README.md).
    Returns (invite_url_or_None, is_configured)."""
    cfg = json.loads((ROOT / "data" / "discord.json").read_text(encoding="utf-8"))
    client_id = cfg.get("client_id", "")
    permissions = cfg.get("permissions", "0")
    configured = bool(client_id) and "REPLACE_WITH" not in client_id
    if not configured:
        return None, False
    url = (
        "https://discord.com/oauth2/authorize"
        f"?client_id={client_id}&scope=bot%20applications.commands&permissions={permissions}"
    )
    return url, True


def _launcher_facts():
    """The real facts about the published launcher build, computed straight
    from the file on disk the same way _zip_path()/_sha256() do for the pack
    ZIP - never read back out of glimpse_manifest.json, so this page does not
    depend on build.py's script ordering. Returns None if no launcher build
    has been published yet.

    Discovery and version ordering come from site_common so this page and
    glimpse_manifest.json can never disagree about which jar is current; the
    private copy that used to live here globbed the pre-rename name only and
    picked the lexicographically first match (see site_common's comment).
    """
    release = newest_launcher_jar(DOWNLOAD_DIR)
    if release is None:
        return None
    return {
        "version": release["version"],
        "file_name": release["file_name"],
        "size_bytes": release["path"].stat().st_size,
        "sha256": _sha256(release["path"]),
    }


def _launcher_native_facts(version):
    """Published native (no-Java-required) installers for `version`, read
    straight from disk - possibly empty, possibly partial if only some
    platforms have shipped. Never invents a platform that has not actually
    published a file.

    Native builds come from the launcher project's own GitHub Actions CI
    (real macOS/Windows/Linux runners - jpackage is not a cross-compiler),
    copied into downloads/ by hand from the CI run's artifacts.
    """
    out = []
    for n in launcher_native_files(version, DOWNLOAD_DIR):
        out.append({
            "platform_id": n["platform_id"],
            "label": n["label"],
            "file_name": n["file_name"],
            "size_bytes": n["size_bytes"],
            "sha256": _sha256(n["path"]),
        })
    return out


def _launcher_section_html(dl, lang, launcher):
    if launcher is None:
        pending = esc(dl.get(
            'launcher_pending',
            f'{LAUNCHER_APP_NAME} is not yet available for download - no build has been '
            f'published to the Wiki yet.'
        ))
        return f'<p class="callout callout--info">{pending}</p>'

    jar_href = f"{asset_root_prefix(1, lang)}downloads/{launcher['file_name']}"
    version_label = esc(dl.get('launcher_version_label', 'Version'))
    size_label = esc(dl.get('size_label', 'File size'))
    sha_label = esc(dl.get('sha_label', 'SHA-256'))
    cta = esc(dl.get('launcher_cta', f'Download {LAUNCHER_APP_NAME}'))
    jar_card = f"""<div class="card" style="margin-bottom:20px;">
  <div class="badge-row">
    <span class="type-badge type-release">{version_label} {esc(launcher['version'])}</span>
  </div>
  <h3 style="margin-top:0">{esc(launcher['file_name'])}</h3>
  <p>{esc(dl.get('launcher_jar_note',
        'Cross-platform (Windows, macOS, Linux) - needs Java 21 or newer already installed.'))}</p>
  <table style="width:100%; border-collapse:collapse;">
    <tr><td style="padding:4px 12px 4px 0; color:var(--text-muted)">{size_label}</td>
        <td><code>{esc(_fmt_size(launcher['size_bytes']))}</code> ({launcher['size_bytes']:,} bytes)</td></tr>
    <tr><td style="padding:4px 12px 4px 0; color:var(--text-muted); vertical-align:top">{sha_label}</td>
        <td style="word-break:break-all"><code>{esc(launcher['sha256'])}</code></td></tr>
  </table>
  <p style="margin-top:16px">
    <a class="btn" href="{esc(jar_href)}" download>{cta}</a>
  </p>
</div>"""

    natives = _launcher_native_facts(launcher['version'])
    if not natives:
        return jar_card

    native_heading = esc(dl.get('launcher_native_heading', 'Native installers (no Java required)'))
    native_note = esc(dl.get('launcher_native_note',
        'These install like a normal desktop app and do not need Java installed separately. '
        'They are not code-signed yet, so your OS will show a first-run warning - see the '
        'install guide for how to proceed past it.'))
    cards = "\n".join(f"""<div class="card" style="margin-bottom:12px;">
  <div class="badge-row">
    <span class="type-badge type-visual">{esc(n['label'])}</span>
  </div>
  <h4 style="margin-top:0">{esc(n['file_name'])}</h4>
  <table style="width:100%; border-collapse:collapse;">
    <tr><td style="padding:4px 12px 4px 0; color:var(--text-muted)">{size_label}</td>
        <td><code>{esc(_fmt_size(n['size_bytes']))}</code> ({n['size_bytes']:,} bytes)</td></tr>
    <tr><td style="padding:4px 12px 4px 0; color:var(--text-muted); vertical-align:top">{sha_label}</td>
        <td style="word-break:break-all"><code>{esc(n['sha256'])}</code></td></tr>
  </table>
  <p style="margin-top:16px">
    <a class="btn" href="{esc(f"{asset_root_prefix(1, lang)}downloads/{n['file_name']}")}" download>{cta} ({esc(n['label'])})</a>
  </p>
</div>""" for n in natives)

    return f"""{jar_card}
<h3>{native_heading}</h3>
<p>{native_note}</p>
{cards}"""


def _discord_section_html(dl, invite_url, discord_configured):
    if discord_configured:
        cta = esc(dl.get('discord_invite_cta', 'Invite release bot'))
        body = esc(dl.get('discord_body', 'Add the release bot to your Discord server to get a '
                                           'message posted automatically whenever a new update ships. '
                                           'After inviting it, run /release channel in your server to '
                                           'choose where announcements go.'))
        return f"""<p class="callout callout--info">{body}</p>
<p><a class="btn" href="{esc(invite_url)}" target="_blank" rel="noopener">{cta}</a></p>"""
    pending = esc(dl.get('discord_pending', 'The Discord release bot is not yet available for this '
                                             'server - the invite link has not been published yet.'))
    return f'<p class="callout callout--info">{pending}</p>'


def _whats_new_body(lang, bundle, dl):
    """The "what's new" paragraph is sourced from the newest changelog entry
    (translated when the bundle has it, JA structural text otherwise) — the
    same convention as the home page's latest-update teaser. It used to be a
    hand-written i18n string, which described V2.2.0 forever while the page
    itself shipped ever-newer ZIPs. The heading's version number comes from
    the {pack_version} placeholder (site_common.load_bundle) for the same
    reason."""
    latest = load_latest_changelog_entry(bundle)
    if latest and latest.get("summary"):
        return latest["summary"]
    return dl.get("whats_new_body", "")


def build_lang(lang, version, zip_name, size_bytes, sha256_hex, release_date):
    bundle = load_bundle(lang)
    ui = bundle["ui"]
    c = ui["common"]
    dl = _require_download_block(bundle, lang)
    invite_url, discord_configured = _discord_invite()
    launcher = _launcher_facts()

    # downloads/ lives at the wiki repo root, *outside* every per-language
    # directory - it needs the language-aware root prefix (asset_root_prefix),
    # not the same-language section prefix ("../") used for changelog/guide/.
    zip_href = f"{asset_root_prefix(1, lang)}downloads/{zip_name}"

    body = f"""
<div class="hero">
  <span class="hero__eyebrow">{esc(ui['page_titles']['download'])}</span>
  <h1>{esc(ui['page_titles']['download'])}</h1>
  <p class="lede">{esc(dl.get('intro', ''))}</p>
</div>

<div class="card" style="margin-bottom:20px;">
  <div class="badge-row">
    <span class="type-badge type-release">{esc(dl.get('version_label', 'Version'))} {esc(version)}</span>
    <span class="timeline-entry__release">{esc(release_date)}</span>
  </div>
  <h3 style="margin-top:0">{esc(zip_name)}</h3>
  <table style="width:100%; border-collapse:collapse;">
    <tr><td style="padding:4px 12px 4px 0; color:var(--text-muted)">{esc(dl.get('size_label', 'Size'))}</td>
        <td><code>{esc(_fmt_size(size_bytes))}</code> ({size_bytes:,} bytes)</td></tr>
    <tr><td style="padding:4px 12px 4px 0; color:var(--text-muted); vertical-align:top">{esc(dl.get('sha_label', 'SHA-256'))}</td>
        <td style="word-break:break-all"><code>{esc(sha256_hex)}</code></td></tr>
  </table>
  <p style="margin-top:16px">
    <a class="btn" href="{esc(zip_href)}" download>{esc(dl.get('primary_cta', 'Download'))}</a>
  </p>
  <p class="callout callout--info">{esc(dl.get('server_note', ''))}</p>
  <p class="callout callout--warn">{esc(dl.get('sapporo_note', ''))}</p>
</div>

<h2>{esc(dl.get('whats_new_heading', ''))}</h2>
<p>{esc(_whats_new_body(lang, bundle, dl))}
  <a href="../changelog/">{esc(dl.get('changelog_link_text', ''))}</a>
</p>

<h2>{esc(dl.get('install_heading', ''))}</h2>
<p>{esc(dl.get('install_body', ''))}
  <a href="../guide/">{esc(dl.get('guide_link_text', ''))}</a>
</p>

<p class="callout callout--info">{esc(dl.get('older_versions_note', ''))}</p>

<h2>{esc(dl.get('launcher_heading', LAUNCHER_APP_NAME))}</h2>
<p>{esc(dl.get('launcher_body', f'{LAUNCHER_APP_NAME} is a desktop app that keeps your {PACK_NAME} '
                                'mod pack up to date automatically, verifying every download against '
                                'this Wiki by SHA-256.'))}</p>
{_launcher_section_html(dl, lang, launcher)}

<h2>{esc(dl.get('discord_heading', 'Discord release notifications'))}</h2>
{_discord_section_html(dl, invite_url, discord_configured)}
"""
    html = page(
        lang=lang,
        section="download/",
        title=ui["page_titles"]["download"],
        description=ui["page_descriptions"]["download"],
        active="download",
        body=body,
        depth=1,
    )
    write_page(lang, "download/", html)


def build():
    version = _mod_version()
    zpath = _zip_path(version)
    size_bytes = zpath.stat().st_size
    sha256_hex = _sha256(zpath)
    release_date = _release_date(version)
    for lang in available_langs():
        build_lang(lang, version, zpath.name, size_bytes, sha256_hex, release_date)


if __name__ == "__main__":
    build()
