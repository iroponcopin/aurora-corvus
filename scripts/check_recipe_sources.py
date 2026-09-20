#!/usr/bin/env python3
"""レシピ集が、いまサイトが配っている版から作られているかを確かめる。

なぜ要るか
----------
2026-09-20 以降、`extract_recipes.py` はレシピ・テクスチャ・表示名を**配布物**
(downloads/ の pack zip とブランド zip)から読む。おかげで「まだ配られていない
作り方」が載ることは無くなったが、**逆向きの古さ**が残る —— 新しい版を配り始めた
のに早見表を作り直していなければ、サイトは新しい zip を配りながら**古い作り方**を
表示し続ける。しかも出力は正常に見え、リンク切れも起きないので誰も気づかない。

Cherry V1.1.0 はレシピを 9 件足すと予告されている(2026-09-20、Cherry セッション)。
つまりこれは仮定の話ではない。

何を見るか
----------
`data/recipes.json` の "sources"(生成時に読んだ配布物の版)と、
`glimpse_manifest.json` がいま配っている版を突き合わせる。1 つでも違えば RED。

直しかた: `python3 scripts/extract_recipes.py` を走らせ直して、
`scripts/build.py` でページを作り直す。
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    recipes_path = ROOT / "data" / "recipes.json"
    manifest_path = ROOT / "glimpse_manifest.json"
    for p in (recipes_path, manifest_path):
        if not p.exists():
            print(f"RED: {p} is missing")
            return 1

    recipes = json.loads(recipes_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    sources = recipes.get("sources")
    if not sources:
        print("RED: data/recipes.json carries no 'sources' block, so nothing can tell whether "
              "it was generated from what the site currently serves. Re-run "
              "scripts/extract_recipes.py.")
        return 1

    # いま配られている版。ブランドは名前で決め打ちせず、マニフェストの**形**から拾う
    # (mod_id と jars を持つブロック)。次にブランドが増えたとき黙って外れないように。
    live = {}
    pack = manifest.get("pack") or {}
    if pack.get("latest"):
        live["pack"] = pack["latest"]
    for block, info in manifest.items():
        if isinstance(info, dict) and "mod_id" in info and isinstance(info.get("jars"), dict):
            if info.get("latest"):
                live[block] = info["latest"]

    if not live:
        print("RED: the manifest declares no published version at all - this checker is reading "
              "the wrong shape, and an empty comparison would pass for the wrong reason.")
        return 1

    bad = []
    for name in sorted(set(live) | set(sources)):
        was, now = sources.get(name), live.get(name)
        if was is None:
            bad.append(f"{name}: published as {now}, but the sheet was not generated from it at all")
        elif now is None:
            bad.append(f"{name}: the sheet was generated from {was}, but nothing publishes it now")
        elif was != now:
            bad.append(f"{name}: the sheet was generated from {was}, the site now serves {now}")

    if bad:
        print("RED: the recipe sheet is out of step with what the site publishes:")
        for line in bad:
            print(f"  - {line}")
        print("  Fix: python3 scripts/extract_recipes.py && python3 scripts/build.py")
        return 1

    print("GREEN: recipe sheet generated from " +
          ", ".join(f"{k} {v}" for k, v in sorted(sources.items())) +
          " - the same versions the site publishes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
