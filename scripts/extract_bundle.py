#!/usr/bin/env python3
"""Folds every JA content source into data/i18n/ja.json -- the full bundle
used to render the JA site, and the file each per-language translation agent
works from.

Sources: data/ui-strings.ja.json, data/changelog.json, data/roadmap.ja.json,
data/known-issues.ja.json, data/guide.json (install guide, written by a
separate agent), data/recipes.json (cat names + item names + the recipe
page's own "使い方" howto tab).

Run this after any JA source file changes, before re-running translation.

⚠ THIS SCRIPT MERGES. IT MUST NEVER REPLACE.
  Until 2026-08-29 it built a fresh dict from the six sources above and wrote
  it over data/i18n/ja.json. But four whole content blocks are hand-authored
  DIRECTLY in that bundle and have no source file to be rebuilt from:

      features        the V2.2 feature tour + the undocumented-mechanics
                      disclosure published in commit 3eee807
      gates           every dimension gate on the server (build_gates.py)
      download        the download page's own copy (build_download.py)
      launcher_page   the Corvus guide (build_launcher.py)

  ...plus 13 leaves inside `ui` (nav/page_titles/page_descriptions for those
  pages, type_badge.disclosure, the two page intros) that were added to the
  bundle without ever being added to data/ui-strings.ja.json.

  So doing exactly what this docstring told you to do DELETED the published
  disclosure, and build_features.py rendered a literal "Coming soon." in its
  place with no error. The build went green over the hole. Nothing anywhere
  went red.

  The shape below is what stops that happening again:
    * start from the bundle already on disk and overwrite only the blocks
      this script actually generates -- anything else in it is carried
      through untouched;
    * deep-merge `ui` so a leaf that exists in the bundle but not in
      data/ui-strings.ja.json survives;
    * ASSERT the result afterwards. No top-level key and no `ui` leaf may
      disappear, and no generated list may shrink. These are post-conditions
      on the merge, not preconditions on the input: if someone later
      "simplifies" this back into a whole-file rewrite, the assertions fire
      instead of the site quietly losing a page.
    * print every `ui` value the sources CHANGE. Overwriting is legitimate
      (that is what running this is for), but it must not be silent -- a
      stale data/ui-strings.ja.json once reverted
      ui.mods_not_distributed_notice to "this site does not distribute the
      mod jars", which stopped being true in V2.2.0.

  --prune-ui      replace `ui` outright instead of merging, so leaves that
                  data/ui-strings.ja.json no longer has are dropped. Prints
                  what it dropped. This is the ONLY way to remove a string
                  with this tool, and it reaches `ui` only -- the four
                  hand-authored blocks have no source file, so there is
                  nothing for this script to decide about them. Delete those
                  by editing data/i18n/ja.json, where they were written.
  --allow-shrink  allow a generated list to get shorter (e.g. a changelog
                  entry really was removed).

There is deliberately no "home" section any more. The home page was reduced
to the wordmark plus a wordless scroll-driven film (owner directive,
2026-08), so data/home.ja.json and the `home` block of all 13 bundles were
deleted rather than left behind as strings nothing renders. See
scripts/build_home.py.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
I18N = DATA / "i18n"
BUNDLE = I18N / "ja.json"

# The only top-level keys this script is entitled to write. Everything else
# found in the bundle is hand-authored content with no source file, and is
# passed through untouched.
GENERATED_KEYS = ("lang", "ui", "changelog", "roadmap", "known_issues",
                  "install_guide", "recipes")

# Generated blocks whose length is a meaningful "did we lose content?" signal.
COUNTED_KEYS = ("changelog", "install_guide")


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def deep_merge(base, incoming):
    """`incoming` wins, but a key present only in `base` survives."""
    if not isinstance(base, dict) or not isinstance(incoming, dict):
        return incoming
    out = dict(base)
    for k, v in incoming.items():
        out[k] = deep_merge(base[k], v) if k in base else v
    return out


def leaf_paths(node, prefix=""):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from leaf_paths(v, f"{prefix}.{k}" if prefix else k)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from leaf_paths(v, f"{prefix}[{i}]")
    else:
        yield prefix, node


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    prune_ui = "--prune-ui" in argv
    allow_shrink = "--allow-shrink" in argv
    unknown = [a for a in argv if a not in ("--prune-ui", "--allow-shrink")]
    if unknown:
        raise SystemExit(f"ERROR: unrecognised argument(s): {' '.join(unknown)}")

    ui = load("ui-strings.ja.json")
    changelog = load("changelog.json")
    roadmap = load("roadmap.ja.json")
    known_issues = load("known-issues.ja.json")
    recipes = load("recipes.json")

    guide_path = DATA / "guide.json"
    install_guide = json.loads(guide_path.read_text(encoding="utf-8")) if guide_path.exists() else []
    if not install_guide:
        print("WARNING: data/guide.json missing or empty -- install guide will be blank "
              "in the bundle until the guide-writing agent finishes and this is re-run.")

    # ---- changelog: split into translatable strings vs structural fields ----
    changelog_strings = []
    missing_id = [f"{e.get('release')}({e.get('date')})" for e in changelog if not e.get("id")]
    if missing_id:
        raise SystemExit(
            f"ERROR: {len(missing_id)} entr(ies) in data/changelog.json have no 'id': "
            + ", ".join(missing_id[:6])
            + "\n  The id is what each language's translation is matched on "
              "(see site_common.load_changelog_structural). Writing a bundle without it would "
              "leave every entry unmatchable and publish the Japanese prose on 12 pages.")
    for e in changelog:
        changelog_strings.append({
            # The entry's identity. NOT (release, date) -- that pair is not
            # unique in data/changelog.json, and keying on it once published
            # one entry's prose under another's badge in all 13 languages.
            "id": e["id"],
            "release": e["release"],  # not translated, kept for display/realignment
            "date": e["date"],
            "title": e["title"],
            "summary": e["summary"],
            "highlights": e.get("highlights", []),
            "balance_changes": e.get("balance_changes", []),
            "warnings": e.get("warnings", []),
            "known_limitations": e.get("known_limitations", []),
        })

    # ---- recipes: category names + item display names (JA + existing EN) ----
    cat_names = [c[0] for c in recipes["cats"]]
    items = {iid: {"ja": v[0], "en": v[1]} for iid, v in recipes["items"].items()}
    recipe_howto = recipes.get("guides", [])

    generated = {
        "lang": "ja",
        "ui": ui,
        "changelog": changelog_strings,
        "roadmap": roadmap,
        "known_issues": known_issues,
        "install_guide": install_guide,
        "recipes": {
            "cat_names": cat_names,
            "items": items,
            "howto": recipe_howto,
        },
    }
    assert set(generated) == set(GENERATED_KEYS), (
        "GENERATED_KEYS is out of step with what main() actually builds: "
        f"{sorted(set(generated) ^ set(GENERATED_KEYS))}")

    existing = json.loads(BUNDLE.read_text(encoding="utf-8")) if BUNDLE.exists() else {}

    # ---- merge, never replace -------------------------------------------
    bundle = dict(existing)
    for key, value in generated.items():
        # `ui` is the only block assembled from a source that has drifted
        # BEHIND the bundle, so it is the only one merged leaf-by-leaf. The
        # rest are wholly derived from their source file.
        if key == "ui" and not prune_ui:
            bundle[key] = deep_merge(existing.get(key), value)
        else:
            bundle[key] = value

    carried = [k for k in existing if k not in GENERATED_KEYS]
    if carried:
        print("carried through untouched (hand-authored, no source file): "
              + ", ".join(sorted(carried)))

    before_ui = dict(leaf_paths(existing.get("ui", {})))
    after_ui = dict(leaf_paths(bundle.get("ui", {})))

    # ---- post-conditions on the merge -----------------------------------
    # These cannot fire while the merge above is correct. They exist so that
    # if it is ever "simplified" back into a whole-file rewrite, THIS goes
    # red instead of the site quietly losing a page. Not overridable by a
    # flag: there is no input that legitimately triggers them.
    lost_blocks = sorted(set(existing) - set(bundle))
    lost_ui = sorted(set(before_ui) - set(after_ui))
    if lost_blocks or (lost_ui and not prune_ui):
        raise SystemExit(
            "ERROR: refusing to write data/i18n/ja.json -- this run would DELETE published "
            "content that has no source file to be rebuilt from.\n"
            + (f"  - top-level block(s): {', '.join(lost_blocks)}\n" if lost_blocks else "")
            + (f"  - {len(lost_ui)} ui leaf/leaves: {', '.join(lost_ui)}\n" if lost_ui else "")
            + "\nThis is a bug in scripts/extract_bundle.py, not in your data: the merge is "
              "supposed to make it impossible. See the ⚠ block in this file's docstring.")

    if prune_ui and lost_ui:
        print(f"--prune-ui: DROPPED {len(lost_ui)} ui leaf/leaves not in data/ui-strings.ja.json:")
        for p in lost_ui:
            print(f"  - {p} = {json.dumps(before_ui[p], ensure_ascii=False)[:100]}")

    # ---- did a source file get shorter than what is already published? ---
    shrunk = [(k, len(existing.get(k) or []), len(bundle.get(k) or []))
              for k in COUNTED_KEYS
              if len(bundle.get(k) or []) < len(existing.get(k) or [])]
    if shrunk and not allow_shrink:
        raise SystemExit(
            "ERROR: refusing to write data/i18n/ja.json -- a source file now has FEWER entries "
            "than the bundle already holds:\n  - "
            + "\n  - ".join(f"{k}: {was} -> {now} entries" for k, was, now in shrunk)
            + "\n\nThat is usually a truncated or half-written source file, not a deletion. "
              "Re-run with --allow-shrink if the removal really is intended.")
    for k, was, now in shrunk:
        print(f"--allow-shrink: {k} {was} -> {now} entries")

    changed_ui = [p for p in after_ui if p in before_ui and before_ui[p] != after_ui[p]]
    if changed_ui:
        print(f"ui values CHANGED by data/ui-strings.ja.json ({len(changed_ui)}):")
        for p in changed_ui:
            print(f"  ~ {p}")
            print(f"      was: {json.dumps(before_ui[p], ensure_ascii=False)[:120]}")
            print(f"      now: {json.dumps(after_ui[p], ensure_ascii=False)[:120]}")
    new_ui = sorted(set(after_ui) - set(before_ui))
    if new_ui:
        print(f"ui leaves ADDED ({len(new_ui)}): " + ", ".join(new_ui))

    I18N.mkdir(parents=True, exist_ok=True)
    # Trailing newline: every other file in data/ has one, and without it a
    # no-op run of this script produced a whole-file diff whose only content
    # was the missing byte -- which is exactly the kind of noise that hides a
    # real one-line change in a review.
    BUNDLE.write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {BUNDLE}")
    print(f"  changelog entries: {len(changelog_strings)}")
    print(f"  recipe items: {len(items)}")
    print(f"  recipe categories: {len(cat_names)}")
    print(f"  recipe howto topics: {len(recipe_howto)}")
    print(f"  install guide sections: {len(install_guide)}")
    roadmap_plans = roadmap.get("plans", []) if isinstance(roadmap, dict) else roadmap
    print(f"  roadmap cards: {len(roadmap_plans)}")


if __name__ == "__main__":
    main()
