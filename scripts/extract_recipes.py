#!/usr/bin/env python3
"""
Generates レシピ早見表.html from the actual recipe JSON + texture PNGs of the seven
sorakaze mods (no hand-authored recipe data - re-run this any time a recipe or texture
changes, per UPDATE-v1.1.md section 7's "drift prevention via script" requirement).

Since 2026-08-04 the sheet is rendered as a Minecraft recipe-book style page
(owner's request): a browsable slot grid of all result items, category tabs,
click-to-open crafting recipes (3x3 grid in real positions), and MC-style hover
tooltips showing 日本語名 + English name. The page is still ONE self-contained
HTML file (no external requests), and every texture payload is embedded exactly
once (content-hash dedup + verified-lossless PNG recompression) instead of once
per occurrence, which is what keeps the file size in check.

The data layer (recipe parsing, texture resolution, SPECIAL_ITEMS, the food
catalogue reader, YOMI sorting and its warnings) is unchanged: a card per grid
recipe + a card per no-recipe item, same categories, same五十音 order. Only the
presentation/emission changed. Zero warnings on a healthy run is still the bar.

Usage: python3 tools/gen_recipe_sheet.py

---------------------------------------------------------------------------
ADAPTED FOR THE GLIMPSE ALPHA WIKI (aurora-corvus repo).
This is a copy of the mod pack's own tools/gen_recipe_sheet.py, kept
byte-identical from the top of the file down through the end of main()'s
data-assembly + validation logic (every hard-won bug fix / self-check stays
intact). Only the final few lines of main() differ: instead of splicing
everything into one giant self-contained HTML file, it dumps the same
underlying data as data/recipes.json + individual PNGs, which this repo's
own recipes/ page renders with the wiki's own look. See the bottom of
main() for the actual diff.

This script reads from the *source* mod-pack project (mods-src/, the vanilla
client jar, lang files, etc.) which is NOT part of this repo — only the
generated JSON/PNG output is committed here. Re-run this any time the source
project's recipes or textures change, same as the original.
---------------------------------------------------------------------------
"""
import json
import base64
import math
import re
import zipfile
from pathlib import Path

ROOT = Path("/Volumes/ORICO/Minecraft Sorakazekarasu Server developer")
OUT_HTML = ROOT / "レシピ早見表.html"  # unused here; original single-file output
SITE_ROOT = Path(__file__).resolve().parent.parent
OUT_DATA_DIR = SITE_ROOT / "data"
OUT_IMG_DIR = SITE_ROOT / "assets" / "img" / "recipes"

MODS = [
    ("sorakaze-guns", "sorakaze_guns", "銃"),
    ("sorakaze-rail", "sorakaze_rail", "電車"),
    ("sorakaze-deco", "sorakaze_deco", "建材"),
    ("sorakaze-vehicles", "sorakaze_vehicles", "乗り物"),
    ("sorakaze-boss", "sorakaze_boss", "ボス"),
    # V1.4.1: 天空 MOD。これを入れ忘れると天空ブロックとエンジェルアローが早見表から丸ごと落ちる。
    ("sorakaze-sky", "sorakaze_sky", "天空"),
    # v1.5.0: サバイバル MOD(7 つ目)。仮面・大盾・水筒・真珠/ルビーの精錬。
    ("sorakaze-survival", "sorakaze_survival", "サバイバル"),
    # v1.8.1: 電力 MOD(8 つ目)。ケーブル・変圧器・分電盤・発電機・原子力発電所・暖炉・エアコン。
    # **ここに足し忘れると 10 レシピが早見表から丸ごと落ちる**(§31.4 と同じ形の欠落。
    # 生成器はカテゴリが未知なら落ちるが、MODS に無いモジュールは黙って存在しないことになる)。
    ("sorakaze-power", "sorakaze_power", "電力"),
    # V2.0.0: 二相楽園(Planarcadia)MOD。**V2.0.0 で初めて配布されたのに、ここに 2 度の
    # ラウンドを跨いで足されないままだった** —— つまり 2 枚のレシピが V2.0.0・V2.1.0 の
    # どちらの早見表にも一度も出ていない。§31.4 / §39 と同じ「MODS に無いものは黙って
    # 存在しないことになる」欠落である。同じことを 3 度やらないために、この直後の
    # `check_mods_roster()` が **一覧を手で信じるのをやめ、mods-src を数えて突き合わせる**。
    ("sorakaze-planarcadia", "sorakaze_planarcadia", "二相楽園"),
]

# ---------------------------------------------------------------------------
# MODS の取りこぼし検出(V2.1.0 で新設)
# ---------------------------------------------------------------------------
# ⚠ **「無い」と宣言することが、無いことを検出する仕掛けを切る。**
#    バックルームズは「レシピが 0 件だから MODS に要らない」と分かっていた。
#    その判断は正しかったが、同じ判断の下で **本当にレシピを持つ二相楽園も**
#    黙って外れていた。だから下の一覧は「免除リスト」ではなく **主張** であり、
#    `check_mods_roster()` は毎回その主張を **実際に数え直して検証する**。
#    ここに載っているモジュールが 1 件でもレシピを持ったら、生成は止まる。
NO_RECIPE_MODULES = {
    "sorakaze-backrooms": "階層そのものが中身で、クラフト可能なアイテムを 1 つも持たない",
    "sorakaze-sapporo": "V2.1.0 には同梱されていない(V2.2 へ持ち越し)",
}

# 「今日 mods-src にレシピを持つモジュールがいくつあるか」の下限。
# 数が減る = 数え方が壊れた(パスの構造が変わった等)ということなので、
# **0 件や 1 件を『見つからなかった』ではなく『無い』と読んで素通りする**のを防ぐ。
MODS_FLOOR = 9


def check_mods_roster():
    """mods-src を歩いて、レシピを持つモジュールが全部 MODS に載っているか確かめる。

    出典は **ディスク上の mods-src ただ 1 つ**。ここに名前を書き写さない ——
    書き写した瞬間に、次に増えるモジュールがまた黙って落ちる。
    バックアップ用の複製(`sorakaze-boss.pre-...` のように名前に `.` を含む)は
    出荷対象ではないので数えない。
    """
    src = ROOT / "mods-src"
    if not src.is_dir():
        raise SystemExit(f"ERROR: {src} is not a directory - the roster check cannot run, and "
                         f"skipping it is exactly how sorakaze-planarcadia went missing")
    found = {}          # mod_dir -> レシピ json の数
    for d in sorted(src.iterdir()):
        if not d.is_dir() or not d.name.startswith("sorakaze-") or "." in d.name:
            continue
        modid = "sorakaze_" + d.name[len("sorakaze-"):]
        n = 0
        for sub in ("recipe", "recipes"):
            n += len(list((d / "src/main/resources/data" / modid / sub).glob("*.json")))
        found[d.name] = n

    if not found:
        raise SystemExit(
            f"ERROR: no sorakaze-* module directories found under {src}. That is not "
            f"'the suite has no modules' - it means this walk is looking in the wrong place, "
            f"and an empty roster would make every check below vacuously true.")

    listed = {mod_dir for mod_dir, _, _ in MODS}
    with_recipes = {name for name, n in found.items() if n > 0}

    missing = sorted(with_recipes - listed)
    if missing:
        raise SystemExit(
            "ERROR: %d module(s) ship craftable recipes but are not in MODS, so every one of "
            "their recipes would be silently absent from the sheet: %s"
            % (len(missing), ", ".join(f"{m} ({found[m]} recipe json)" for m in missing)))

    # 「レシピが無い」という主張のほうを検証する。増えていたら止まる。
    for name, why in sorted(NO_RECIPE_MODULES.items()):
        if name not in found:
            print(f"NOTE: NO_RECIPE_MODULES lists {name}, but it is not in mods-src any more "
                  f"(claim: {why}) - remove the entry once that is intentional")
            continue
        if found[name] > 0:
            raise SystemExit(
                "ERROR: %s is declared recipe-less (%s) but now has %d recipe json(s). "
                "The declaration is what switches off the missing-module detector, so it must "
                "not be allowed to go stale: add %s to MODS (with a category, a cat_order entry "
                "and a CATEGORY_TAB_ICON) instead."
                % (name, why, found[name], name))

    # 一覧に載っているのに mods-src に無いもの(名前の打ち間違い)も黙って通さない。
    ghosts = sorted(listed - set(found))
    if ghosts:
        raise SystemExit(
            "ERROR: MODS names %d directory(ies) that do not exist under mods-src: %s"
            % (len(ghosts), ", ".join(ghosts)))

    if len(found) < MODS_FLOOR:
        raise SystemExit(
            "ERROR: only %d sorakaze-* module(s) found under %s, below the floor of %d. "
            "A count that shrank means the walk broke, not that modules were deleted."
            % (len(found), src, MODS_FLOOR))

    unlisted = sorted(set(found) - listed)
    print("mods roster: %d module dir(s) in mods-src, %d in MODS, %d recipe json(s) total; "
          "recipe-less and declared: %s"
          % (len(found), len(listed), sum(found.values()), ", ".join(unlisted) or "(none)"))


DOOR_IDS = {"auto_door", "fusuma", "large_door_iron", "large_door_wood", "hatch",
            "camo_door", "roller_shutter", "sliding_glass_door", "jail_bar_door"}

# ===========================================================================
# 名前が無いまま出荷されているもの(v1.8.4 時点で判明した 17 件)
# ===========================================================================
# `display_name()` は lang に鍵が無いと **生の id をそのまま返す**。だから
# 「ミサイルランチャー」ではなく `missile_launcher` と書かれたカードが、
# **警告も出さずに**出てしまう(読みの検査も ASCII をローマ字として読めるので通る)。
# 実際に v1.8.4 のページで 17 枚がそうなっていた —— しかもこれは早見表だけの
# 問題ではなく、**ゲーム内でも翻訳鍵がそのまま名前として出る**(= jar の欠陥)。
#
# ⚠ この一覧は<b>減らすためだけにある</b>。
#   ・ここに無いものが新しく名前を失ったら **生成を止める**(退行を通さない)。
#   ・ここに載っているものが直ったら、やはり **生成を止めて** 削除を促す
#     (直ったのに載ったままだと、一覧が「まだ壊れている」と嘘をつく。
#      `USED_FACTS` の「使われない読み取りは死んでいる」と同じ規律)。
#
# 直しかた: 各 MOD の `lang/ja_jp.json` と `lang/en_us.json` に
#   `block.sorakaze_guns.missile_launcher` / `block.sorakaze_deco.<色>_reinforced_glass_pane`
# を足して **その MOD を再ビルドして dist に入れ直す**(lang だけ直しても jar は古いまま)。
KNOWN_UNNAMED = frozenset({
    # ⚠ `sorakaze_guns:missile_launcher` は 2026-08-09 に**直したので外した**。
    #    表示名・ツールチップ 4 行・パネルの 46 鍵をまとめて両言語に入れてある
    #    (所有者の「発射台はどこにあるんですか?」への対応)。この行を戻すと、
    #    上の規律どおり「直ったのに載っている」で生成が止まる。
    # ⚠ 建材 v1.7.7 の強化ガラスの窓 16 件(黒以外の全色 + 無色)は
    #    **2026-08-17 に直ったので外した**。同日の「遮光付き強化ガラス」作業で
    #    `block.sorakaze_deco.<色>_reinforced_glass_pane` が ja_jp / en_us の
    #    両方に入り、この生成器が自分から
    #      「ERROR: 16 id(s) in KNOWN_UNNAMED now have a proper name」
    #    と言って **exit 1 で生成を拒んだ**(上の規律どおり)。だから消したので
    #    あって、通すために消したのではない。1 件でも戻れば `regressions` 側で
    #    また止まる。
    #
    # ここが空になった = 「名前の無いまま出荷されているものは 0 件」。
    # 新しく名前を失ったものが出れば `regressions` で生成が止まる(空集合でも
    # 検査は空虚にならない: 引き算の向きが逆なので下の `fixed` 検査だけが無効化される)。
})

# レシピを持たない(=クラフト不可の)特別入手アイテム。早見表には「入手方法」カードとして掲載する
# (V1.3.0update.md §6.2: 強化ビーコンは「ボスドロップ」表記)。
SPECIAL_ITEMS = [
    # (modid, item_name, 入手方法テキスト, カテゴリ)
    ("sorakaze_boss", "enhanced_beacon", "スカルクゴーレム討伐のドロップ(クラフト不可)", "ボス"),
    ("sorakaze_boss", "excalibur", "ロックロック(ネザーのボス)討伐のドロップ(クラフト不可)", "ボス"),
    # v1.4 のボス 5 体の専用ツール(過剰エンチャント付き。クラフト不可)。
    ("sorakaze_boss", "runecore_pickaxe", "ルーンコア・コロッサス討伐のドロップ(クラフト不可)", "ボス"),
    ("sorakaze_boss", "ember_axe", "エンバーロード討伐のドロップ(クラフト不可)", "ボス"),
    ("sorakaze_boss", "treant_hoe", "エルダー・トレント討伐のドロップ(クラフト不可)", "ボス"),
    ("sorakaze_boss", "void_spear", "ヴォイド・ストーカー討伐のドロップ(クラフト不可)", "ボス"),
    ("sorakaze_boss", "frost_shovel", "フロスト・リッチ・キング討伐のドロップ(クラフト不可)", "ボス"),
    # V1.4.1: 巨大ボス 3 体の専用ドロップ。
    ("sorakaze_boss", "grim_reapers_scythe",
     "グレイブバウンド・リーパー討伐のドロップ(クラフト不可)。範囲攻撃つき", "ボス"),
    ("sorakaze_boss", "abyssal_trident",
     "アビサル・クラウン・クラーケン討伐のドロップ(クラフト不可)。水中で強化", "ボス"),
    ("sorakaze_boss", "thunder_spear",
     "テンペスト・タイタン討伐のドロップ(クラフト不可)。命中で落雷", "ボス"),
    # V1.4.1 §1.4: エンジェル装備は矢以外クラフト不可 — エンジェルから購入する。
    ("sorakaze_sky", "angels_sword", "天空都市のエンジェルから購入(30 エメラルド〜)", "天空"),
    ("sorakaze_sky", "angels_bow", "天空都市のエンジェルから購入(30 エメラルド〜)", "天空"),
    ("sorakaze_sky", "angels_shield", "天空都市のエンジェルから購入(30 エメラルド〜)", "天空"),
    ("sorakaze_sky", "angels_halo", "天空都市のエンジェルから購入(30 エメラルド〜)", "天空"),
    ("sorakaze_sky", "angels_plate", "天空都市のエンジェルから購入(30 エメラルド〜)", "天空"),
    ("sorakaze_sky", "angels_trousers", "天空都市のエンジェルから購入(30 エメラルド〜)", "天空"),
    ("sorakaze_sky", "angels_boots", "天空都市のエンジェルから購入(30 エメラルド〜)", "天空"),
    ("sorakaze_sky", "angels_wings",
     "天空都市のエンジェルから購入(30 エメラルド〜)。チェストプレートとは同時装備できない", "天空"),
    # v1.4.6 §7-2: 天空のボス(スカイ・アークエンジェル)の確定ドロップ。クラフト不可。
    ("sorakaze_sky", "angels_staff",
     "天空城のボス「スカイ・アークエンジェル」討伐の確定ドロップ(クラフト不可)。空中で威力1.5倍", "天空"),
    # v1.4.8 §2-6: クリスタル・ワイバーンの卵。討伐のドロップ・クラフト不可。
    # ※ v1.5.2 §4-3 でドロップ率 100% → 20% に変更。
    ("sorakaze_sky", "crystal_wyvern_egg",
     "クリスタル・ワイバーン討伐でまれにドロップ(20%・クラフト不可)。孵化装置に入れると、なつくワイバーンが孵る",
     "天空"),
    # v1.5.2 §4-2: 王族装備。矢だけがクラフト可能で、本体 6 種は王国商人からの購入限定
    # (宝箱にも入らない)。エンジェル装備と同じ「入手方法」カードで載せないと、
    # 早見表を見た人には「存在しないアイテム」に見えてしまう。
    ("sorakaze_sky", "royal_sword",
     "天空王国の王国商人から購入(クラフト不可)。エメラルドブロック 2 枠 = 1,000 エメラルド以上", "天空"),
    ("sorakaze_sky", "royal_bow",
     "天空王国の王国商人から購入(クラフト不可)。エメラルドブロック 2 枠 = 1,000 エメラルド以上", "天空"),
    ("sorakaze_sky", "royal_crown",
     "天空王国の王国商人から購入(クラフト不可)。エメラルドブロック 2 枠 = 1,000 エメラルド以上", "天空"),
    ("sorakaze_sky", "royal_chestplate",
     "天空王国の王国商人から購入(クラフト不可)。エメラルドブロック 2 枠 = 1,000 エメラルド以上", "天空"),
    ("sorakaze_sky", "royal_leggings",
     "天空王国の王国商人から購入(クラフト不可)。エメラルドブロック 2 枠 = 1,000 エメラルド以上", "天空"),
    ("sorakaze_sky", "royal_boots",
     "天空王国の王国商人から購入(クラフト不可)。エメラルドブロック 2 枠 = 1,000 エメラルド以上", "天空"),
    # v1.5.2 §4-3: REX の卵。討伐でまれにドロップ(30%)・クラフト不可。
    ("sorakaze_sky", "rex_egg",
     "野生の REX 討伐でまれにドロップ(30%・クラフト不可)。孵化装置に入れると、なつく REX が孵る", "天空"),
    # ---- V1.7.0 -------------------------------------------------------------
    # ここから下は v1.7.0 で増えた「レシピを持たないアイテム」。
    # **登録済みアイテムとレシピの差を機械的に取って洗い出した**(手で思い出したのではない)。
    # 載せ忘れると §29.6-11 の王族装備と同じで「早見表には存在しないアイテム」になる。
    ("sorakaze_boss", "universal_harvester",
     "ウィザーストーム討伐の確定ドロップ(クラフト不可)。壊したブロックをそのまま回収できる", "ボス"),
    # v1.9.0: ウィザーストーム全面刷新にともなう新しい確定ドロップ 2 種。
    ("sorakaze_boss", "universal_harvester_alpha",
     "ウィザーストーム討伐の確定ドロップ(クラフト不可)。金のツルハシと同じ耐久32・エンチャント不可。"
     "無印の万物採集器とは別アイテム", "ボス"),
    ("sorakaze_survival", "spark_doll_alpha",
     "ウィザーストーム討伐の確定ドロップ(クラフト不可)。トーテム・オブ・アンダイイングの2倍の効果を、"
     "回数無制限(発動後3分クールダウン)で発揮する花火人形の上位版", "サバイバル"),
    ("sorakaze_sky", "siege_maul",
     "「鎧の侵略者」(天空王国を襲う襲撃ボス)からの戦利品(クラフト不可)。遅いが一撃が重い", "天空"),
    ("sorakaze_deco", "special_atm",
     "シンガポール都市国家に置かれている金色の ATM(クラフト不可)。"
     "第 3 の「特別口座」を扱える(利息 6%/ゲーム内日・利息が付くのは 500 万エメラルドまで)", "建材"),
    ("sorakaze_sky", "estate_deed",
     "天空王国の物件を買うと受け取る記念の証書(クラフト不可)。所有権はサーバーの台帳が持っているので、失っても物件は失われない", "天空"),
    ("sorakaze_sky", "estate_ledger",
     "天空王国に置かれている物件売買の台帳(クラフト不可)。買いたい区画の上に立って素手で右クリック", "天空"),
    ("sorakaze_sky", "grocery_counter",
     "シンガポール都市国家の店にある食料品の棚(クラフト不可)。エメラルドを持って押すと食料品を買える", "天空"),
]

# V1.7.0: 食料品 300 種。レシピが無い(店で買う)ので、上の SPECIAL_ITEMS と同じ
# 「入手方法」カードとして載せる。**値段と品名は FoodCatalog.java(生成物の唯一の出典)から
# 直接読む**ので、あちらの表に行を足せば早見表も自動で追随する = 二重管理にならない。
FOOD_CATALOG_JAVA = (ROOT / "mods-src/sorakaze-sky/src/main/java/net/sorakaze"
                     "/sorakaze_sky/food/FoodCatalog.java")


def load_food_specials():
    """FoodCatalog.java の ENTRIES を読んで SPECIAL_ITEMS と同じ形のタプル列を返す。"""
    if not FOOD_CATALOG_JAVA.exists():
        raise SystemExit(f"ERROR: {FOOD_CATALOG_JAVA} が見つかりません。"
                         f"食料品のカードが黙って 0 枚になるので中断します。")
    text = FOOD_CATALOG_JAVA.read_text(encoding="utf-8")
    rows = re.findall(
        r'new Entry\(\s*"(\w+)"\s*,\s*"\w+"\s*,\s*Category\.\w+\s*,\s*(\d+)\s*,'
        r'\s*[\d.]+F?\s*,\s*(\d+)\s*,\s*\d+\s*\)', text)
    declared = re.search(r'COUNT\s*=\s*(\d+)', text)
    if declared and len(rows) != int(declared.group(1)):
        # 表と COUNT がずれたら黙って少ない枚数を出さずに落とす(§20.6-5 と同じ趣旨)。
        raise SystemExit(f"ERROR: FoodCatalog の COUNT={declared.group(1)} に対し "
                         f"実際に読めた行は {len(rows)} 件です。正規表現が古い可能性があります。")
    out = []
    for food_id, nutrition, price in rows:
        out.append((
            "sorakaze_sky", food_id,
            f"シンガポール都市国家のお店の棚で購入(1 個 {price} エメラルド・クラフト不可)。"
            f"満腹度 +{nutrition}",
            "天空"))
    return out

VANILLA_CLIENT_JAR = Path.home() / ".gradle/caches/fabric-loom/26.2/minecraft-client.jar"

VANILLA_JA_NAMES = {
    "furnace": "かまど",
    "glass": "ガラス",
    "glass_pane": "板ガラス",
    "glowstone": "グロウストーン",
    "gray_concrete": "灰色のコンクリート",
    "gunpowder": "火薬",
    "iron_block": "鉄ブロック",
    "iron_ingot": "鉄インゴット",
    "iron_nugget": "鉄塊",
    "oak_planks": "オークの板材",
    "paper": "紙",
    "redstone": "レッドストーン",
    "red_dye": "赤色の染料",
    "white_concrete": "白色のコンクリート",
    "yellow_concrete": "黄色のコンクリート",
    "chest": "チェスト",
    "ender_pearl": "エンダーパール",
    "iron_bars": "鉄格子",
    "leather": "革",
    "oak_door": "オークのドア",
    "spruce_planks": "トウヒの板材",
    "stick": "棒",
    "stone": "石",
    "amethyst_shard": "アメジストの欠片",
    "black_dye": "黒色の染料",
    "black_wool": "黒色の羊毛",
    "diamond": "ダイヤモンド",
    "gold_ingot": "金インゴット",
    "ladder": "はしご",
    "quartz_block": "クォーツブロック",
    "redstone_lamp": "レッドストーンランプ",
    "white_dye": "白色の染料",
    "yellow_dye": "黄色の染料",
}
# a handful of vanilla items don't have a simple flat "item/<name>.png" or
# "block/<name>.png" texture (multi-face blocks, pane models that borrow another
# block's texture) - map those to the closest single representative texture.
VANILLA_TEXTURE_OVERRIDE = {
    "furnace": "block/furnace_front",
    "glass_pane": "block/glass",
    "quartz_block": "block/quartz_block_side",
    # V1.4.1: 召喚石の素材。どちらも item/<name>.png を持たない(面ごとに別テクスチャの
    # ブロック)ので、代表的な側面を明示する。指定しないと空欄のカードになる。
    "ancient_debris": "block/ancient_debris_side",
    "sculk_catalyst": "block/sculk_catalyst_top",
    # マグマブロックのテクスチャ名は block/magma(block/magma_block ではない)。
    "magma_block": "block/magma",
    # v1.4.4(ドア 40 種の素材)。どちらも item/<name>.png も block/<name>.png も持たない。
    "bone_block": "block/bone_block_side",
    # ハーフブロックは専用テクスチャを持たず、元の板材テクスチャを流用して描かれる。
    "oak_slab": "block/oak_planks",
    "observer": "block/observer_front",
    # v1.5.0(列車 30 種・車両 100 種・サバイバルの新素材)。いずれも面ごとに別テクスチャの
    # ブロック、または実体モデルで描かれるアイテムで、item/<name>.png を持たない。
    "hay_block": "block/hay_block_side",
    "blast_furnace": "block/blast_furnace_front",
    # v1.7.7(ロケット弾のレシピ材料・強化ガラス系のレシピ材料候補)。TNT も面ごとに
    # 別テクスチャ(tnt_top/tnt_bottom/tnt_side)で、item/tnt.png も block/tnt.png も無い。
    "tnt": "block/tnt_side",
    # レシピブック UI の「すべて」タブのアイコン(作業台)。これも面ごとに別テクスチャ。
    "crafting_table": "block/crafting_table_front",
    # v1.8.0(自動仕分けブロック 9 種+フィルター記憶カードのレシピ材料)。
    # 時計は 64 コマのアニメーション(item/clock_00 〜 clock_63)なので、
    # 静止画の代表として 00 コマを使う。ピストンとドロッパーは面ごとに別テクスチャで、
    # item/<name>.png も block/<name>.png も持たない(furnace / observer と同じ扱い)。
    "clock": "item/clock_00",
    "piston": "block/piston_top",
    "dropper": "block/dropper_front",
    # v1.8.2(太陽光パネルのレシピ材料・「使い方」タブの感知器の図)。日照センサーも
    # 面ごとに別テクスチャ(daylight_detector_top / _side)で、item も block も持たない。
    "daylight_detector": "block/daylight_detector_top",
    # ※ 盾は 1 枚のテクスチャで表せないので compose_shield_icon() で合成する。
}

# MOD ブロックのうち、フラットな単一テクスチャもモデル texture マップ(models/block/<name>.json)も
# 持たないもの(マルチパートブロック等)の代表テクスチャを明示指定する。
MOD_TEXTURE_OVERRIDE = {
    "sorakaze_deco:table": "block/table_top",
    # ---- 自動仕分け 9 種(v1.8.1)------------------------------------------
    # ⚠ **指定しないと、9 枚とも同じ絵になる。**
    # この 9 種は平面の `item/<名前>.png` を持たず、下の解決順は最後に
    # `models/block/<名前>.json` の texture マップへ落ちる。そこで選ばれる鍵は
    # TEXTURE_KEY_PREFERENCE の先頭に近い "top" で、v1.8.0 の天面は 9 種で
    # **共有の 1 枚**だった。結果、v1.8.0 の早見表は 9 枚のカードが
    # **1 つのテクスチャ(t140)を指す**状態になっていた
    # (実際に出荷済みの HTML を読んで確認済み。所有者が仕分け機を覚えようとして
    #  開く当の資料で、9 種が同じ灰色の四角に見えていた)。
    #
    # ゲーム内のホットバーは `items/<名前>.json` の display_context セレクトにより
    # **`item/<名前>_icon`** を出す。早見表もそれに合わせる — 資料と画面で
    # 違う絵が出るほうが混乱するからである。
    # (v1.8.1 で天面も 9 種別々にしたので放っておいても重複はしないが、
    #  「たまたま違う」ではなく「ホットバーと同じ絵」を指す方が正しい。)
    "sorakaze_deco:sorting_filter": "item/sorting_filter_icon",
    "sorakaze_deco:category_sorter": "item/category_sorter_icon",
    "sorakaze_deco:round_robin_splitter": "item/round_robin_splitter_icon",
    "sorakaze_deco:overflow_valve": "item/overflow_valve_icon",
    "sorakaze_deco:void_trash": "item/void_trash_icon",
    "sorakaze_deco:item_pump": "item/item_pump_icon",
    "sorakaze_deco:item_counter": "item/item_counter_icon",
    "sorakaze_deco:stock_indicator": "item/stock_indicator_icon",
    "sorakaze_deco:item_collector": "item/item_collector_icon",
}


# ===========================================================================
# あいうえお順(五十音順)の並べ替え と 検索用の読みがな
# ===========================================================================
# アイテム名は「電車」「特急形電車」「スパークルの仮面」のように漢字・かな混じりである。
# 生の文字列をソートすると **Unicode のコードポイント順** になり、漢字は意味のない順に並ぶ
# (「あいうえお順」には絶対にならない)。五十音順に並べるには **読み(yomi)** が要る。
#
# この環境には日本語辞書が無いので、読みは下の YOMI 表(形態素・複合語の表)から
# **最長一致**で組み立てる。アイテム名はほぼ規則的な複合語(<素材>の<形状>)なので、
# 表に無い語が出たときだけ WARNING を出して検出できる(黙って間違った順に並べない)。
#
# 表に足すときの注意: 長い語を先に当てたいときは、長い語をそのまま登録すればよい
# (照合は常に「その位置で一致する最長のキー」を選ぶ)。
#   例) 「金庫」を入れておかないと「金」+「庫」に割れる。「格子戸」は「格子」に勝つ。
YOMI = {
    # --- 形状・共通の接尾語 -------------------------------------------------
    "円柱": "えんちゅう", "縦": "たて", "板材": "いたざい", "階段": "かいだん",
    "柱": "はしら", "扉": "とびら", "戸": "ど", "石": "いし", "盾": "たて",
    "剣": "けん", "弓": "ゆみ", "矢": "や", "槍": "やり", "斧": "おの",
    "杖": "つえ", "輪": "わ", "翼": "つばさ", "卵": "たまご", "弾": "だん",
    "機": "き", "車": "しゃ", "木": "き", "氷": "こおり", "森": "もり",
    "雲": "くも", "雷": "かみなり", "銀": "ぎん", "鉄": "てつ", "鋼": "はがね",
    "王": "おう", "骨": "ほね", "駅": "えき", "枚": "まい", "式": "しき",
    "軽": "けい", "手": "て", "口": "くち",
    # --- v1.8.1: 電力 MOD の語(複合語は音便のためまとめて登録)-----------------
    "原子力発電所": "げんしりょくはつでんしょ", "原子炉": "げんしろ",
    "発電機": "はつでんき", "発電": "はつでん", "分電盤": "ぶんでんばん",
    "変圧器": "へんあつき", "絶縁": "ぜつえん", "暖炉": "だんろ",
    "機械": "きかい", "筐体": "きょうたい", "遮蔽": "しゃへい",
    # --- v1.9.3: 蓄電池(発電機・原子力発電所の下流に新設)-------------------
    "蓄電池": "ちくでんち",
    # --- v1.8.2: 再生可能エネルギー 3 種。いずれも「発電機」の前に付く語で、
    #     1 文字ずつでは読めない(「水+流」「風+力」「太陽+光」)ので複合語で登録する。
    "太陽光": "たいようこう", "水流": "すいりゅう", "風力": "ふうりょく",
    # --- v1.8.4 -------------------------------------------------------------
    # 「太径」はケーブル業界の読みかたに合わせる(太径電線 = ふとけいでんせん)。
    # 「照明」「注入」は 1 文字ずつだと読みが割れる(入 = い / にゅう)ので複合語で登録。
    "太径": "ふとけい", "照明": "しょうめい", "注入": "ちゅうにゅう",
    "移動": "いどう", "水道管": "すいどうかん",
    # ギリシャ文字。かなに開いておかないと「読めない文字」として末尾に飛ばされ、
    # 強化ビーコンの 3 枚が離ればなれに並んでしまう。
    "α": "あるふぁ", "β": "べーた",
    # --- 建材の素材名 -------------------------------------------------------
    "安山岩": "あんざんがん", "磨かれた": "みがかれた", "滑らかな": "なめらかな",
    "深層岩": "しんそうがん", "砂岩": "さがん", "花崗岩": "かこうがん",
    "閃緑岩": "せんりょくがん", "丸石": "まるいし", "黒石": "くろいし",
    "白石": "しろいし", "雲石": "くもいし", "黒曜石縁取り": "こくようせきふちどり",
    "黒曜石": "こくようせき", "天空石": "てんくうせき", "天空": "てんくう",
    "真鍮": "しんちゅう", "赤い": "あかい", "屋根瓦": "やねがわら", "瑠璃": "るり",
    "光輝": "こうき", "金縁": "きんぶち", "金装飾": "きんそうしょく",
    "木製": "もくせい", "鉄製": "てつせい", "鋼製": "こうせい", "縞鋼板": "しまこうはん",
    "金網": "かなあみ", "金庫": "きんこ", "鉄格子": "てつごうし",
    # --- 色 -----------------------------------------------------------------
    "桃色": "ももいろ", "橙色": "だいだいいろ", "灰色": "はいいろ", "薄灰色": "うすはいいろ",
    "白色": "しろいろ", "空色": "そらいろ", "紫色": "むらさきいろ", "緑色": "みどりいろ",
    "茶色": "ちゃいろ", "赤色": "あかいろ", "赤紫色": "あかむらさきいろ",
    "青色": "あおいろ", "青緑色": "あおみどりいろ", "黄色": "きいろ", "黄緑色": "きみどりいろ",
    "黒色": "くろいろ", "赤": "あか",
    # --- 帯(列車の塗装)------------------------------------------------------
    "橙帯": "だいだいおび", "緑帯": "みどりおび", "赤帯": "あかおび",
    "青帯": "あおおび", "黄帯": "きおび",
    # --- 電車 ---------------------------------------------------------------
    "通勤形電車": "つうきんがたでんしゃ", "快速形電車": "かいそくがたでんしゃ",
    "特急形電車": "とっきゅうがたでんしゃ", "超高速列車": "ちょうこうそくれっしゃ",
    "超特急列車": "ちょうとっきゅうれっしゃ", "路面電車": "ろめんでんしゃ",
    "貨物機関車": "かもつきかんしゃ", "貨物車": "かもつしゃ", "客車": "きゃくしゃ",
    "電車": "でんしゃ", "先頭車": "せんとうしゃ", "中間車": "ちゅうかんしゃ",
    # --- v1.9.3: 架線(装飾用の設置アイテム)---------------------------------
    "架線": "かせん",
    # --- 2026-08-17: この日の作業で入った 67 枚のぶん ------------------------
    # ここに足さないと **64 枚が五十音順の外へ落ちる**(警告は出るが生成は通るので、
    # 黙って並びだけが壊れる形になる)。読みは複合語のまま登録する ——
    # 「遮光」+「付き」に割ると「つき」が「月」と同じ扱いになり、色ちがい 51 枚が
    # 「遮光付き〜」でまとまらなくなる。
    "遮光付き": "しゃこうつき",              # 建材: 遮光付き強化ガラス 51 種
    "防護服": "ぼうごふく",                   # 銃: Hazmat Suit
    "定義": "ていぎ",                         # 銃: データ定義銃(Data-Defined Firearm)
    "携行": "けいこう",                       # 乗り物: 携行缶(缶 は登録済み)
    # ⚠ 「空」は 2 通りに読む。「空の携行缶」= そら、「空気清浄機」= くう。
    #    1 文字の「空」を そら にしたうえで、**くう と読むほうを複合語で先に取る**。
    #    (「空色」= そらいろ は既に上で複合語として登録済みなので影響しない。)
    "空気清浄機": "くうきせいじょうき",        # 電力: Air Purifier(V2 §10)
    "空": "そら",
    "鍛冶": "かじ", "祭壇": "さいだん", "核": "かく",   # ボス: 鍛冶祭壇の核
    "霜": "しも",                             # ボス: 霜の祭壇
    "溶融": "ようゆう",                       # ボス: 溶融の王冠
    "原初": "げんしょ",                       # ボス: 原初の卵
    "心臓": "しんぞう",                       # ボス: スカルクの心臓
    "魂血": "こんけつ",                       # ボス: 魂血の祭壇(Soul Blood Altar)
    "冷蔵庫": "れいぞうこ",                    # サバイバル: Refrigerator
    "蛇口": "じゃぐち",                        # サバイバル: Water Tap(口 は くち で登録済み)
    # --- V2.1.0: この回で早見表に初めて出るぶん ------------------------------
    # ⚠ 足さないと **警告は出るが生成は通り、並びだけが黙って壊れる**。
    #    銃工作台は V2.0.0 の時点で jar に入っていたのに、MODS ではなく
    #    再生成をしていなかったせいで今まで表に出ていなかった。
    "工作台": "こうさくだい",                  # 銃: 銃工作台(銃 は じゅう で登録済み)
    # 二相楽園(Planarcadia)。ジャンル名そのものと、その 2 枚のカード。
    "二相楽園": "にそうらくえん",
    "次元": "じげん", "跳躍": "ちょうやく", "壁画": "へきが",  # 次元跳躍の壁画
    # --- 乗り物 -------------------------------------------------------------
    "大型旅客機": "おおがたりょかくき", "大型": "おおがた", "小型": "こがた",
    "平床": "ひらゆか", "箱型": "はこがた", "農業用": "のうぎょうよう",
    "救急車": "きゅうきゅうしゃ", "消防車": "しょうぼうしゃ", "収集車": "しゅうしゅうしゃ",
    # --- 銃 -----------------------------------------------------------------
    "機関部": "きかんぶ", "銃床": "じゅうしょう", "銃身": "じゅうしん",
    "散弾": "さんだん", "小口径弾": "しょうこうけいだん", "自動": "じどう",
    "撃退": "げきたい", "除け": "よけ",
    # --- 建材(設備)---------------------------------------------------------
    "点字": "てんじ", "誘導": "ゆうどう", "警告灯": "けいこくとう", "警告": "けいこく",
    "薄型": "うすがた", "航空障害灯": "こうくうしょうがいとう",
    "車両用信号機": "しゃりょうようしんごうき", "歩行者用信号機": "ほこうしゃようしんごうき",
    "電柱": "でんちゅう", "電線": "でんせん", "腕金付き": "うでがねつき",
    "受信機": "じゅしんき", "発信機": "はっしんき", "防犯": "ぼうはん",
    # --- 銃 v1.8.5(ミサイルランチャーに表示名が付き、弾頭 2 種にレシピが付いた) ---
    "核弾頭": "かくだんとう", "弾頭": "だんとう",
    # --- ドア ---------------------------------------------------------------
    "観音扉": "かんのんとびら", "鏡板": "かがみいた", "無地": "むじ",
    "装飾": "そうしょく", "格子戸": "こうしど", "落とし格子": "おとしごうし",
    "格子": "こうし", "入り": "いり", "山形": "やまがた", "彫り飾り": "ほりかざり",
    "彫刻": "ちょうこく", "鋲打ち": "びょううち", "筋交い": "すじかい",
    "二重扉": "にじゅうとびら", "大扉": "おおとびら", "高扉": "たかとびら",
    "気密扉": "きみつとびら", "隔壁扉": "かくへきとびら", "回転扉風": "かいてんとびらふう",
    "両開き": "りょうびらき", "吹き抜け": "ふきぬけ", "全面": "ぜんめん",
    "枠付き": "わくつき", "巻き上げ": "まきあげ", "片引き戸": "かたびきど",
    "引き戸": "ひきど", "欄間付き": "らんまつき", "板戸": "いたど", "雨戸": "あまど",
    "障子": "しょうじ", "にじり口": "にじりぐち", "隠し": "かくし", "錆びた": "さびた",
    "倉庫": "そうこ", "宝物庫": "ほうもつこ", "格納庫": "かくのうこ", "城門": "じょうもん",
    "教会": "きょうかい", "店舗入口": "てんぽいりぐち", "防火": "ぼうか",
    # --- 天空 ---------------------------------------------------------------
    "天使": "てんし", "王冠": "おうかん", "王族": "おうぞく", "胸当て": "むねあて",
    "脚当て": "あしあて", "孵化装置": "ふかそうち",
    # --- ボス ---------------------------------------------------------------
    "召喚石": "しょうかんせき", "召喚": "しょうかん", "強化": "きょうか",
    "死神": "しにがみ", "大鎌": "おおがま", "灼熱": "しゃくねつ", "虚無": "きょむ",
    "深淵": "しんえん", "墓縛り": "はかしばり", "刈り手": "かりて", "嵐帝": "らんてい",
    # v1.7.4: ペスト医師召喚石。「ペスト」はカタカナで自動変換されるので「医師」だけでよい。
    "医師": "いし",
    # v1.7.7: 列車自動停止ブロック(鉄道)・強化ガラスの窓(建材)・花火人形(サバイバル)。
    # 「列車」「停止」は音便・濁音化があるので 1 文字ずつではなく複合語として登録する
    # (列+車を単純結合すると「れつしゃ」になり「れっしゃ」の促音が抜ける)。
    "列車": "れっしゃ", "停止": "ていし", "窓": "まど",
    "花火": "はなび", "人形": "にんぎょう",
    # 2026-08-04: 建材の「色付きガラス板」17 色(並行作業ラウンドで追加されたレシピ)。
    "色付き": "いろつき",
    # --- サバイバル ---------------------------------------------------------
    "仮面": "かめん", "大盾": "おおだて", "水筒": "すいとう", "真珠": "しんじゅ",
    # --- ジャンル名(検索でジャンルごと絞り込めるように)----------------------
    "銃": "じゅう", "建材": "けんざい", "乗り物": "のりもの",
    # --- バニラの素材(3×3 のマスに出てくる材料。検索でも読みで引けるようにする)--------
    "欠片": "かけら", "原木": "げんぼく", "木材": "もくざい", "板": "いた",
    "棒": "ぼう", "火薬": "かやく", "染料": "せんりょう", "紙": "かみ", "金": "きん",
    "鉄塊": "てっかい", "金塊": "きんかい", "塊": "かたまり", "革": "かわ",
    "羊毛": "ようもう", "骨粉": "こっぷん", "石炭": "せきたん", "鉱石": "こうせき",
    "松明": "たいまつ", "感圧板": "かんあつばん", "羽根": "はね", "糸": "いと",
    "種": "たね", "砂": "すな", "土": "つち", "皮": "かわ", "鎖": "くさり",
    "額縁": "がくぶち", "本": "ほん", "樽": "たる", "旗": "はた", "網": "あみ",
    "銅": "どう", "玉": "たま", "水": "みず", "苔": "こけ", "泥": "どろ",
    # --- V1.7.0: 新規アイテム(ドロップ・購入・構造物内で見つかるもの)-----------
    # これらは「入手方法」カードとして SPECIAL_ITEMS に載る。読みが無いと
    # あいうえお順から外れて WARNING で名指しされるので、ここに足しておく。
    "襲撃": "しゅうげき", "角笛": "つのぶえ",
    "万物": "ばんぶつ", "採集器": "さいしゅうき",
    "特別": "とくべつ",
    "物件": "ぶっけん", "権利": "けんり", "証書": "しょうしょ",
    "不動産": "ふどうさん", "台帳": "だいちょう",
    "食料品": "しょくりょうひん", "棚": "たな",
    "攻城": "こうじょう", "大槌": "おおづち",
    # --- V1.7.0: 食料品 300 種(シンガポール都市国家の店で買う)-----------------
    # 下の表は「実際の ja_jp.json に現れる漢字の連なり」を機械的に洗い出して作った
    # (tools 側で正規表現で抽出 -> 全件に読みを付けた)。長い語から順に当たるので、
    # 複合語をそのまま登録してある = 1 文字ずつに割れて誤読になることがない。
    "乳酸菌飲料": "にゅうさんきんいんりょう", "冷凍白身魚": "れいとうしろみざかな",
    "低脂肪乳": "ていしぼうにゅう", "冷凍層状": "れいとうそうじょう",
    "冷凍春巻": "れいとうはるまき", "冷凍枝豆": "れいとうえだまめ",
    "冷凍餃子": "れいとうぎょうざ", "大麦飲料": "おおむぎいんりょう",
    "木綿豆腐": "もめんどうふ", "甘口醤油": "あまくちしょうゆ",
    "豆乳飲料": "とうにゅういんりょう", "五香粉": "ごこうふん",
    "全粒粉": "ぜんりゅうふん", "即席麺": "そくせきめん", "叉焼飯": "ちゃーしゅーはん",
    "大根餅": "だいこんもち", "大麦水": "おおむぎみず", "大麦茶": "おおむぎちゃ",
    "小豆氷": "あずきごおり", "手羽先": "てばさき", "料理用": "りょうりよう",
    "板菓子": "いたがし", "氷砂糖": "こおりざとう", "生姜茶": "しょうがちゃ",
    "生春巻": "なまはるまき", "空芯菜": "くうしんさい", "菊花茶": "きっかちゃ",
    "薄力粉": "はくりきこ", "車海老": "くるまえび", "酸梅湯": "さんばいとう",
    "下味": "したあじ", "丸鶏": "まるどり", "乾麺": "かんめん", "仙草": "せんそう",
    "冷凍": "れいとう", "加糖": "かとう", "卵麺": "たまごめん", "叉焼": "ちゃーしゅー",
    "味付": "あじつけ", "団子": "だんご", "塩卵": "しおたまご", "塩漬": "しおづけ",
    "小分": "こわけ", "小粒": "こつぶ", "層状": "そうじょう", "平打": "ひらうち",
    "惣菜": "そうざい", "果物": "くだもの", "椎茸": "しいたけ", "海苔": "のり",
    "涼茶": "りょうちゃ", "濃厚": "のうこう", "焼豚": "やきぶた", "煮干": "にぼし",
    "煮込": "にこみ", "牛乳": "ぎゅうにゅう", "牛肉": "ぎゅうにく", "玄米": "げんまい",
    "発酵": "はっこう", "白貝": "しろがい", "箱入": "はこいり", "米菓": "べいか",
    "米麺": "こめめん", "粗塩": "あらじお", "緑茶": "りょくちゃ", "缶入": "かんいり",
    "缶詰": "かんづめ", "腸粉": "ちょうふん", "菓子": "かし", "薬膳": "やくぜん",
    "角煮": "かくに", "豆乳": "とうにゅう", "豆入": "まめいり", "豆花": "とうふぁ",
    "豚肋": "ぶたあばら", "豚足": "とんそく", "貝柱": "かいばしら", "身入": "みいり",
    "身包": "みつつみ", "醤油": "しょうゆ", "野菜": "やさい", "風味": "ふうみ",
    "飲料": "いんりょう", "餃子": "ぎょうざ", "鴨飯": "かもめし", "鶏卵": "けいらん",
    "鶏飯": "けいはん", "麦芽": "ばくが",
    "串": "くし", "切": "きり", "合": "ごう", "和": "わ", "実": "み", "巻": "まき",
    "干": "ほし", "引": "ひき", "房": "ふさ", "折": "おり", "揚": "あげ", "板": "いた",
    "梅": "うめ", "油": "あぶら", "炊": "たき", "炒": "いため", "焼": "やき",
    "煎": "いり", "牛": "ぎゅう", "物": "もの", "甘": "あま", "生": "なま",
    "白": "しろ", "盛": "もり", "箱": "はこ", "米": "こめ", "粉": "こな",
    "粥": "かゆ", "缶": "かん", "肉": "にく", "茶": "ちゃ", "茹": "ゆで",
    "葉": "は", "蒸": "むし", "蓮": "はす", "豚": "ぶた", "身": "み", "込": "こみ",
    "青": "あお", "風": "かぜ", "食": "しょく", "飯": "めし", "飲": "のみ",
    "香": "こう", "魚": "さかな", "鶏": "とり", "麺": "めん",
    # --- v1.8.0: 建材の自動仕分けブロック 9 種+フィルター記憶カード ------------
    # 「振り分け」「仕分」は 1 文字ずつに割ると読みが崩れる(分 = ぶん/わけ の
    # どちらにもなる)ので、複合語のまま登録して最長一致に勝たせる。
    "振り分け": "ふりわけ", "仕分": "しわ", "分配": "ぶんぱい",
    "集荷": "しゅうか", "計数": "けいすう", "搬送": "はんそう",
    "在庫": "ざいこ", "表示": "ひょうじ", "廃棄": "はいき", "装置": "そうち",
    "記憶": "きおく", "防止": "ぼうし", "溢": "あふ", "弁": "べん", "器": "き",
}

# 最長一致のための索引(先頭文字 -> その文字で始まるキーを長い順に)。
_YOMI_INDEX = {}
for _k in YOMI:
    _YOMI_INDEX.setdefault(_k[0], []).append(_k)
for _v in _YOMI_INDEX.values():
    _v.sort(key=len, reverse=True)

# 五十音の基準列。「ん」は最後。
GOJUON = "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわゐゑをん"
_GOJUON_INDEX = {c: i for i, c in enumerate(GOJUON)}

# ひらがな -> (清音の基準文字, 濁点ランク, 小書きランク)
# 濁点ランク: 0=清音 1=濁音 2=半濁音 / 小書きランク: 0=直音 1=拗音・促音
_KANA_DECOMP = {c: (c, 0, 0) for c in GOJUON}
for _voiced, _plain in zip("がぎぐげござじずぜぞだぢづでどばびぶべぼゔ",
                           "かきくけこさしすせそたちつてとはひふへほう"):
    _KANA_DECOMP[_voiced] = (_plain, 1, 0)
for _p, _plain in zip("ぱぴぷぺぽ", "はひふへほ"):
    _KANA_DECOMP[_p] = (_plain, 2, 0)
for _small, _large in zip("ぁぃぅぇぉっゃゅょゎゕゖ", "あいうえおつやゆよわかけ"):
    _base, _voice, _ = _KANA_DECOMP[_large]
    _KANA_DECOMP[_small] = (_base, _voice, 1)

# 長音符「ー」を直前の音の母音に開くための表(国語辞典の慣例: カー = カア)。
_VOWEL_OF = {}
for _i, _c in enumerate("あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもらりるれろ"):
    _VOWEL_OF[_c] = "あいうえお"[_i % 5]
_VOWEL_OF.update({"や": "あ", "ゆ": "う", "よ": "お",
                  "わ": "あ", "ゐ": "い", "ゑ": "え", "を": "お", "ん": "ん"})


def kana_fold(s):
    """カタカナをひらがなに畳む(長音符「ー」はそのまま)。検索・読みの共通前処理。"""
    out = []
    for ch in s:
        o = ord(ch)
        if 0x30A1 <= o <= 0x30F6:          # ァ..ヶ
            out.append(chr(o - 0x60))
        else:
            out.append(ch)
    return "".join(out)


def search_norm(s):
    """検索用の正規化。JS 側の norm() と **同じ規則**でなければ検索が外れる。
    ①小文字化 ②全角 ASCII -> 半角 ③全角スペース -> 半角 ④カタカナ -> ひらがな。
    """
    s = s.lower()
    out = []
    for ch in s:
        o = ord(ch)
        if 0xFF01 <= o <= 0xFF5E:
            out.append(chr(o - 0xFEE0))
        elif o == 0x3000:
            out.append(" ")
        elif 0x30A1 <= o <= 0x30F6:
            out.append(chr(o - 0x60))
        else:
            out.append(ch)
    return "".join(out)


def reading_of(name):
    """表示名の読み(ひらがな)を返す。戻り値: (読み, 読めなかった文字のリスト)。

    かな・英数字・記号はそのまま(カタカナはひらがなへ)。漢字は YOMI 表の最長一致。
    表に無い漢字は **そのまま残したうえで報告する** ので、黙って間違った順に並ぶことはない。
    """
    out = []
    unknown = []
    i = 0
    n = len(name)
    while i < n:
        hit = None
        for key in _YOMI_INDEX.get(name[i], ()):
            if name.startswith(key, i):
                hit = key
                break
        if hit:
            out.append(YOMI[hit])
            i += len(hit)
            continue
        ch = name[i]
        o = ord(ch)
        if 0x30A1 <= o <= 0x30F6:            # カタカナ
            out.append(chr(o - 0x60))
        elif 0x3041 <= o <= 0x3096 or ch in "ー":
            out.append(ch)
        elif ch.isascii() or ch in "()（）×・、。〜 　":
            out.append(ch)
        else:                                 # 未登録の漢字など
            unknown.append(ch)
            out.append(ch)
        i += 1
    return "".join(out), unknown


def _expand_choon(yomi):
    """「ー」を直前の音の母音に開く(レーザー -> れえざあ)。辞書の並べ方に合わせる。"""
    out = []
    for ch in yomi:
        if ch == "ー":
            prev = out[-1] if out else ""
            base = _KANA_DECOMP.get(prev, (prev, 0, 0))[0]
            v = _VOWEL_OF.get(base)
            if v:
                out.append(v)
            continue
        out.append(ch)
    return "".join(out)


def gojuon_key(name):
    """五十音順の比較キーを作る。文字ごとに (種別, 位置, 濁点, 小書き) の組を並べる。

    種別: 0=記号・空白 / 1=数字 / 2=英字 / 3=かな / 4=読めなかった文字(最後に回す)
    → 数字・英字(ATM, SUV, REX ...)が先、次にかな。同じ音なら 清音 < 濁音 < 半濁音、
      直音 < 拗音。最後に元の文字列を足して同点を無くす(実行ごとに順が変わらない)。
    """
    yomi, _unknown = reading_of(name)
    key = []
    for ch in _expand_choon(kana_fold(yomi)):
        d = _KANA_DECOMP.get(ch)
        if d:
            base, voice, small = d
            key.append((3, _GOJUON_INDEX[base], voice, small))
        elif ch.isdigit() and ch.isascii():
            key.append((1, ord(ch), 0, 0))
        elif ch.isalpha() and ch.isascii():
            key.append((2, ord(ch.lower()), 0, 0))
        elif ch.isascii() or ch in "()（）×・、。〜　":
            key.append((0, ord(ch), 0, 0))
        else:
            key.append((4, ord(ch), 0, 0))
    return key, name


def compose_chest_icon(zf):
    """The chest has no flat texture (it's an entity-rendered block whose 64x64 UV
    atlas lives at entity/chest/normal.png). Compose a recognizable 16x16 front view
    from the atlas regions (lid front + body front + latch), script-reproducibly."""
    import io
    from PIL import Image
    atlas = Image.open(io.BytesIO(zf.read("assets/minecraft/textures/entity/chest/normal.png"))).convert("RGBA")
    icon = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    lid_front = atlas.crop((14, 15, 28, 20))    # 14x5
    body_front = atlas.crop((14, 33, 28, 43))   # 14x10
    icon.paste(lid_front, (1, 1))
    icon.paste(body_front, (1, 6))
    latch = atlas.crop((1, 1, 3, 5))            # 2x4 latch strip
    icon.paste(latch, (7, 4))
    buf = io.BytesIO()
    icon.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def load_vanilla_zip():
    if not VANILLA_CLIENT_JAR.exists():
        raise SystemExit(f"vanilla client jar not found at {VANILLA_CLIENT_JAR} - run a gradle build first")
    return zipfile.ZipFile(VANILLA_CLIENT_JAR)


def compose_skull_icon(zf, entity_texture):
    """頭部エンティティ(ウィザースケルトンの頭など)のアイコンを合成する。

    頭系のアイテムは item/*.png を持たない — ゲーム内ではエンティティモデルとして描かれるため。
    スキン画像の「頭の正面」(8,8)-(16,16) と、その上に重なる帽子レイヤー (40,8)-(48,8+8) を
    切り出して重ね、16px に拡大する。バニラのスキン UV 規約そのままで、推測値ではない。
    """
    from PIL import Image
    import io
    src = Image.open(io.BytesIO(zf.read(entity_texture))).convert("RGBA")
    face = src.crop((8, 8, 16, 16))
    hat = src.crop((40, 8, 48, 16))
    face.alpha_composite(hat)
    out = face.resize((16, 16), Image.NEAREST)
    buf = io.BytesIO()
    out.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def compose_shield_icon(zf):
    """バニラの盾のアイコンを合成する(v1.5.0: 大盾のレシピ素材)。

    盾は item/shield.png を持たない — 実体モデル(ShieldModel)として描かれるため。
    無地の盾のテクスチャ entity/shield/shield_base_nopattern.png から、盾板(12x22x1、
    texOffs(0,0))の<b>正面</b>にあたる矩形 (1,1)-(13,23) を切り出す。これはバニラの
    箱 UV 規約(正面 = u[d, d+w], v[d, d+h])そのままで、目分量ではない。
    16x16 のセルに縦横比を保って収める。
    """
    from PIL import Image
    import io
    src = Image.open(io.BytesIO(zf.read(
        "assets/minecraft/textures/entity/shield/shield_base_nopattern.png"))).convert("RGBA")
    plate = src.crop((1, 1, 13, 23))                      # 12x22 の盾板の正面
    scaled = plate.resize((9, 16), Image.NEAREST)         # 縦を 16 に合わせる(12:22 ≒ 9:16)
    out = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    out.paste(scaled, (4, 0))
    buf = io.BytesIO()
    out.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


# 頭系アイテム -> 元になるエンティティテクスチャ。
SKULL_ENTITY_TEXTURE = {
    "wither_skeleton_skull": "assets/minecraft/textures/entity/skeleton/wither_skeleton.png",
    "skeleton_skull": "assets/minecraft/textures/entity/skeleton/skeleton.png",
}


def vanilla_texture_b64(zf, name):
    if name == "chest":
        return compose_chest_icon(zf)
    if name == "shield":
        try:
            return compose_shield_icon(zf)
        except (KeyError, OSError) as exc:
            print(f"WARNING: could not compose shield icon: {exc}")
    skull = SKULL_ENTITY_TEXTURE.get(name)
    if skull:
        try:
            return compose_skull_icon(zf, skull)
        except (KeyError, OSError) as exc:
            print(f"WARNING: could not compose skull icon for {name}: {exc}")
    override = VANILLA_TEXTURE_OVERRIDE.get(name)
    candidates = [override] if override else [f"item/{name}", f"block/{name}"]
    for c in candidates:
        path = f"assets/minecraft/textures/{c}.png"
        try:
            data = zf.read(path)
            return base64.b64encode(data).decode()
        except KeyError:
            continue
    print(f"WARNING: no vanilla texture found for {name}")
    return None


TEXTURE_KEY_PREFERENCE = ["particle", "top", "front", "end", "wool", "north", "all", "side", "tex"]

_VANILLA_ZIP = None


def vanilla_zip():
    """公式クライアント jar を 1 回だけ開いて使い回す(カードごとに開き直さない)。"""
    global _VANILLA_ZIP
    if _VANILLA_ZIP is None:
        _VANILLA_ZIP = load_vanilla_zip()
    return _VANILLA_ZIP


_VANILLA_ITEM_TAG_CACHE = {}


def vanilla_item_tag(name, _seen=None):
    """`#minecraft:<name>` を **公式 jar の中のタグ定義**から実アイテム id の並びに開く。

    2026-08-17 に必要になった。`sorakaze_vehicles:gasoline` が材料に
    `#minecraft:coals` を使いはじめ、`register()` の「未知の名前空間」の枝に落ちて
    **カードの 4 マスが `#minecraft:coals` という生の文字とアイコン無しの空欄**になった
    (生成は WARNING だけで通る = 黙って劣化する形。あの枝の注記が
    「今は存在しないが、現れたら」と書いていた当のものが現れた)。

    出典は**バニラの jar 1 つだけ**である。ここにタグの中身を書き写さない ——
    写した瞬間に、Mojang がタグを変えた日に早見表だけが嘘になる。
    入れ子の `#...` 参照は再帰で開く。**取れなければ生成を止める**:
    材料の分からないレシピを出すより、生成を落としたほうがよい。
    """
    if name in _VANILLA_ITEM_TAG_CACHE:
        return _VANILLA_ITEM_TAG_CACHE[name]
    seen = _seen or set()
    if name in seen:
        raise SystemExit("ERROR: vanilla item tag #minecraft:%s refers to itself (cycle)" % name)
    seen.add(name)
    path = "data/minecraft/tags/item/%s.json" % name
    try:
        raw = vanilla_zip().read(path)
    except KeyError:
        raise SystemExit(
            "ERROR: a recipe uses the vanilla item tag #minecraft:%s, but %s is not in the "
            "client jar (%s). Either the tag was renamed in this Minecraft version or the "
            "recipe has a typo - a card with an unresolvable ingredient must not ship."
            % (name, path, VANILLA_CLIENT_JAR))
    out = []
    for v in json.loads(raw.decode("utf-8"))["values"]:
        vid = v["id"] if isinstance(v, dict) else v
        if vid.startswith("#"):
            out.extend(vanilla_item_tag(vid.split(":", 1)[1], seen))
        elif vid not in out:
            out.append(vid)
    if not out:
        raise SystemExit(
            "ERROR: vanilla item tag #minecraft:%s resolved to nothing - the card would show "
            "an empty slot where an ingredient belongs" % name)
    _VANILLA_ITEM_TAG_CACHE[name] = out
    return out


def crop_to_used_uv(assets, name, png_path):
    """アイテムモデルが**実際に使っている uv の範囲**にテクスチャを切り詰める。

    v1.5.4 の仮面 2 種は 128x128 の中に「顔のキャンバス + 裏面用の小さなパッチ +
    余白」が同居する UV アトラスである。そのまま貼ると早見表のアイコンに
    **未使用の暗い帯**が写り込む。ここではモデル JSON の north 面の uv を
    実際に走査して、絵がある矩形だけを切り出す(目分量の定数ではない)。

    16px の普通のアイテムは uv が 0..16 いっぱいなので、この関数は何もしない。
    """
    model_path = assets / "models/item" / f"{name}.json"
    if not model_path.exists():
        return None
    try:
        model = json.loads(model_path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None
    els = model.get("elements") or []
    if not els:
        return None
    u0 = v0 = 16.0
    u1 = v1 = 0.0
    for el in els:
        face = (el.get("faces") or {}).get("north")
        if not face or "uv" not in face:
            continue
        a, b, c, d = face["uv"]
        u0, u1 = min(u0, a, c), max(u1, a, c)
        v0, v1 = min(v0, b, d), max(v1, b, d)
    if u1 <= u0 or v1 <= v0 or (u0 <= 0.01 and v0 <= 0.01 and u1 >= 15.99 and v1 >= 15.99):
        return None
    from PIL import Image
    import io
    with Image.open(png_path) as img:
        w, h = img.size
        box = (int(u0 / 16.0 * w), int(v0 / 16.0 * h),
               max(int(u1 / 16.0 * w), int(u0 / 16.0 * w) + 1),
               max(int(v1 / 16.0 * h), int(v0 / 16.0 * h) + 1))
        out = img.convert("RGBA").crop(box)
    buf = io.BytesIO()
    out.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def _png_b64_for_ref(ref, default_ns):
    """`ns:textures/以下のパス` 1 個を base64 に。見つからなければ None。"""
    ns, path = ref.split(":", 1) if ":" in ref else (default_ns, ref)
    if ns == "minecraft":
        try:
            return base64.b64encode(vanilla_zip().read(
                f"assets/minecraft/textures/{path}.png")).decode()
        except KeyError:
            return None
    for mdir, mid, _ in MODS:
        if mid == ns:
            p = (ROOT / "mods-src" / mdir / "src/main/resources/assets" / mid
                 / "textures" / f"{path}.png")
            if p.exists():
                return base64.b64encode(p.read_bytes()).decode()
    return None


def _model_chain_texture(model_id, depth=0):
    """モデル id から代表テクスチャを 1 枚返す。**`parent` を辿る。**

    `#name` の参照(子モデルが埋めるつもりの変数)は素材ではないので飛ばす。
    """
    if depth > 8:
        return None
    ns, path = model_id.split(":", 1) if ":" in model_id else ("minecraft", model_id)
    data = None
    if ns == "minecraft":
        try:
            data = json.loads(vanilla_zip().read(f"assets/minecraft/models/{path}.json"))
        except KeyError:
            return None
    else:
        for mdir, mid, _ in MODS:
            if mid == ns:
                p = (ROOT / "mods-src" / mdir / "src/main/resources/assets" / mid
                     / "models" / f"{path}.json")
                if p.exists():
                    try:
                        data = json.loads(p.read_text(encoding="utf-8"))
                    except Exception:  # noqa: BLE001
                        data = None
                break
    if data is None:
        return None
    tex_map = {k: v for k, v in (data.get("textures") or {}).items()
               if isinstance(v, str) and not v.startswith("#")}
    chosen = None
    for key in ("layer0",) + tuple(TEXTURE_KEY_PREFERENCE):
        if key in tex_map:
            chosen = tex_map[key]
            break
    if chosen is None and tex_map:
        chosen = next(iter(tex_map.values()))
    if chosen:
        got = _png_b64_for_ref(chosen, ns)
        if got:
            return got
    parent = data.get("parent")
    return _model_chain_texture(parent, depth + 1) if parent else None


def _gui_model_of_item_definition(node, depth=0):
    """`items/<name>.json` の木から **GUI に出るモデル id** を選ぶ。

    26.2 の items 定義は `minecraft:select` などの木である。この MOD 群は
    「GUI・fixed・on_shelf = 2D アイコン / それ以外 = 3D」という分岐を多用しているので
    (§12・§14)、**`when` に "gui" を含む枝を最優先**で選ぶ。無ければ fallback、
    それも無ければ最初の枝。

    ⚠ ここを決め打ちの id 一覧にすると、§27.5-10(ドア 90 種)と同じ
    「手書きの表から外れた物が黙って絵を失う」失敗を作る。だから**構造で辿る**。
    """
    if depth > 8 or not isinstance(node, dict):
        return None
    if node.get("type") == "minecraft:model" and isinstance(node.get("model"), str):
        return node["model"]
    cases = node.get("cases")
    if isinstance(cases, list):
        for want_gui in (True, False):
            for case in cases:
                if not isinstance(case, dict):
                    continue
                when = case.get("when")
                whens = when if isinstance(when, list) else [when]
                if want_gui and "gui" not in whens:
                    continue
                got = _gui_model_of_item_definition(case.get("model"), depth + 1)
                if got:
                    return got
            if node.get("fallback") is not None:
                got = _gui_model_of_item_definition(node["fallback"], depth + 1)
                if got:
                    return got
    for key in ("fallback", "model", "on_false", "on_true"):
        got = _gui_model_of_item_definition(node.get(key), depth + 1)
        if got:
            return got
    return None


def mod_texture_b64(mod_dir, modid, name):
    assets = ROOT / "mods-src" / mod_dir / "src/main/resources/assets" / modid
    textures = assets / "textures"
    override = MOD_TEXTURE_OVERRIDE.get(f"{modid}:{name}")
    if override:
        p = textures / f"{override}.png"
        if p.exists():
            return base64.b64encode(p.read_bytes()).decode()
    for sub in ("item", "block"):
        p = textures / sub / f"{name}.png"
        if p.exists():
            cropped = crop_to_used_uv(assets, name, p) if sub == "item" else None
            return cropped if cropped else base64.b64encode(p.read_bytes()).decode()
    # V1.7.0: テクスチャが item/ 直下ではなく**サブフォルダ**に置かれていることがある
    # (食料品 300 種は textures/item/food/<name>.png)。ここを決め打ちのフォルダ名の
    # 一覧にすると、§27.5-10 のドア 90 種と同じ「手書きリストから外れた物が黙って
    # 消える」失敗をまた作ることになるので、**再帰的に探す**。
    # `<name>_3d.png`(UV アトラス)は名前が違うので、この検索には引っかからない。
    nested = sorted((q for q in textures.rglob(f"{name}.png") if q.is_file()),
                    key=lambda q: (len(q.parts), str(q)))
    if nested:
        return base64.b64encode(nested[0].read_bytes()).decode()
    # V1.4.1: 平面アイコンを持たず 3D モデルだけのアイテム(巨大ボス 3 体のドロップ)。
    # ゲーム内は items/<name>.json が 3D モデルを指すので正しく描かれる(§19.2 の方針どおり)が、
    # 早見表のサムネイル用の平面 PNG が無い。空欄にするよりは実物の絵を出す。
    # ※ これは UV アトラスなので見栄えは良くない。平面アイコンを作ったらこの分岐は不要になる。
    p3d = textures / "item" / f"{name}_3d.png"
    if p3d.exists():
        return base64.b64encode(p3d.read_bytes()).decode()
    # v1.7.7: 強化ガラスの窓(pane)17 種はどれも自分専用のテクスチャを持たない。
    # blockstate は "multipart"(post/side/side_alt の組)で単一の block/<name>.json を
    # 持たないため、下の block モデル経路では解決できず、17 枚とも WARNING で
    # 抜け落ちていた。実際に読まれる item モデル(parent: minecraft:item/generated)
    # 自身の layer0 が「同じ色の板ガラスブロックのテクスチャ」(例:
    # sorakaze_deco:block/white_reinforced_glass、"_pane" 抜き)を指しているので、
    # ここでそれを辿る。他 MOD のテクスチャや vanilla を指す場合にも対応しておく
    # (§20-5 が建材バリアント 414 枚で踏んだ「MOD 名前空間しか探さない」失敗の再演を防ぐ)。
    item_model_path = assets / "models/item" / f"{name}.json"
    if item_model_path.exists():
        try:
            item_model = json.loads(item_model_path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            item_model = {}
        tex_map = item_model.get("textures", {})
        for key in ("layer0", "layer1", "texture", "all", "particle"):
            ref = tex_map.get(key)
            if not ref:
                continue
            ref_ns, ref_path = ref.split(":", 1) if ":" in ref else (modid, ref)
            if ref_ns == "minecraft":
                try:
                    data = vanilla_zip().read(f"assets/minecraft/textures/{ref_path}.png")
                    return base64.b64encode(data).decode()
                except KeyError:
                    pass
            else:
                for mdir, mid, _ in MODS:
                    if mid == ref_ns:
                        p = (ROOT / "mods-src" / mdir / "src/main/resources/assets"
                             / mid / "textures" / f"{ref_path}.png")
                        if p.exists():
                            return base64.b64encode(p.read_bytes()).decode()
            break
    # No flat "<name>.png" - the item icon is a multi-texture block model (e.g. traffic
    # lights, poles, tactile paving). Read the block model's texture map and pick the
    # most representative single face, in the same spirit as Mojang's own "particle"
    # texture convention (the face used for break particles / inventory fallback icons).
    model_path = assets / "models/block" / f"{name}.json"
    if model_path.exists():
        model = json.loads(model_path.read_text(encoding="utf-8"))
        tex_map = model.get("textures", {})
        chosen = None
        for key in TEXTURE_KEY_PREFERENCE:
            if key in tex_map:
                chosen = tex_map[key]
                break
        if chosen is None and tex_map:
            chosen = next(iter(tex_map.values()))
        if chosen:
            chosen_ns, chosen_path = chosen.split(":", 1) if ":" in chosen else (modid, chosen)
            # V1.4.1: モデルがバニラのテクスチャを直接指している場合(建材バリアント 138 種は
            # すべてこの形 — 例 {"tex": "minecraft:block/stone"})、MOD の assets には存在しない。
            # 公式 jar から読む。これが無いと 400 枚以上のカードが絵の無いまま出力される。
            if chosen_ns == "minecraft":
                try:
                    data = vanilla_zip().read(f"assets/minecraft/textures/{chosen_path}.png")
                    return base64.b64encode(data).decode()
                except KeyError:
                    pass
            for mdir, mid, _ in MODS:
                if mid == chosen_ns:
                    p = ROOT / "mods-src" / mdir / "src/main/resources/assets" / mid / "textures" / f"{chosen_path}.png"
                    if p.exists():
                        return base64.b64encode(p.read_bytes()).decode()
    # v1.8.4: ここまでで解決できないのは、**平面テクスチャも block/<name>.json も持たず、
    # `items/<name>.json` の分岐から先にしか絵が無い**ブロックである(水道管がそれで、
    # 絵は item/water_pipe_icon にあった)。26.2 の items 定義を構造どおり辿って
    # 「GUI に出るモデル」を選び、そのモデル(と parent)のテクスチャを読む。
    #
    # ⚠ **わざと最後に置いてある。**上の経路で既に解決している 900 枚あまりの絵に
    # 1 枚も触れないためで、実際に生成前後で画像ハッシュを突き合わせて確認している。
    item_def_path = assets / "items" / f"{name}.json"
    if item_def_path.exists():
        try:
            item_def = json.loads(item_def_path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            item_def = {}
        gui_model = _gui_model_of_item_definition(item_def.get("model"))
        if gui_model:
            got = _model_chain_texture(gui_model)
            if got:
                return got
    print(f"WARNING: no texture found for {modid}:{name}")
    return None


def load_lang(mod_dir, modid, locale="ja_jp"):
    p = ROOT / "mods-src" / mod_dir / "src/main/resources/assets" / modid / f"lang/{locale}.json"
    return json.loads(p.read_text(encoding="utf-8"))


def display_name(lang, modid, name):
    for prefix in ("item", "block"):
        key = f"{prefix}.{modid}.{name}"
        if key in lang:
            return lang[key]
    return name


# ===========================================================================
# バニラの公式表示名(ja_jp / en_us)
# ===========================================================================
# 旧版はバニラ素材の名前を手書きの VANILLA_JA_NAMES(約 35 語)だけで引いていたため、
# 表に無い 111 種の素材(銅インゴット・石レンガなど)がツールチップに生 id
# ("copper_ingot")のまま出ていた。レシピブック化でツールチップが主役になるので、
# 実際のバニラ言語ファイルから正式名を引く。
#   ja: ランチャーの asset store(index の sha1 で検証してから読む。ローカルに実在する
#       Mojang 配布物で、テクスチャを公式クライアント jar から読むのと同じ正規ルート)
#   en: 公式クライアント jar 同梱の en_us.json
# どちらも見つからなければ従来の VANILLA_JA_NAMES → 生 id の順で落ちる(=今までと
# 同じ表示に戻るだけ)が、その劣化は黙って起きないよう WARNING で名指しする。
VANILLA_ASSET_BASES = [
    Path.home() / "Library/Application Support/minecraft/assets",
    Path.home() / ".gradle/caches/fabric-loom/assets",
]


def find_vanilla_asset(rel_path):
    """ランチャーの asset store から 1 ファイルを読む(index の sha1 で検証してから)。

    戻り値: (bytes, 使った index 名) / 見つからなければ (None, None)。
    ja_jp.json と UI クリック音がこの経路を共用する。
    """
    import hashlib
    indexes = []
    for base in VANILLA_ASSET_BASES:
        d = base / "indexes"
        if d.is_dir():
            indexes += list(d.glob("*.json"))
    indexes.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    objdirs = [b / "objects" for b in VANILLA_ASSET_BASES if (b / "objects").is_dir()]
    for idx_path in indexes:
        try:
            obj = json.loads(idx_path.read_text(encoding="utf-8"))["objects"][rel_path]
            h = obj["hash"]
        except Exception:  # noqa: BLE001 - 壊れた index / 未収載は次の候補へ
            continue
        for od in objdirs:
            f = od / h[:2] / h
            if not f.is_file():
                continue
            data = f.read_bytes()
            if hashlib.sha1(data).hexdigest() != h:
                continue
            return data, idx_path.name
    return None, None


def load_vanilla_ja():
    data, idx_name = find_vanilla_asset("minecraft/lang/ja_jp.json")
    if data is not None:
        lang = json.loads(data.decode("utf-8"))
        print(f"vanilla ja_jp.json: {idx_name} ({len(lang)} keys)")
        return lang
    print("WARNING: vanilla ja_jp.json not found in local asset stores - vanilla "
          "ingredient names fall back to VANILLA_JA_NAMES / raw ids")
    return {}


def load_click_wav_b64():
    """バニラの UI クリック音(random/click.ogg)を、ブラウザがどれでも復号できる
    小さな WAV(モノラル 16-bit・無音を刈り込み)にして base64 で返す。

    OGG のまま埋めないのは Safari の decodeAudioData が OGG Vorbis を読めないため。
    音源はテクスチャ・ja_jp.json と同じ正規ルート(所有者のランチャーの asset store、
    sha1 検証つき)。取り出せない/復号器が無いときは WARNING を出して None を返し、
    ページ側は合成ブリップ(WebAudio)に切りかわる = 黙って無音にはならない。
    """
    data, idx_name = find_vanilla_asset("minecraft/sounds/random/click.ogg")
    if data is None:
        print("WARNING: vanilla click.ogg not found in local asset stores - "
              "the page will fall back to a synthesized click, not the Minecraft one")
        return None
    import shutil
    import subprocess
    import tempfile
    import wave
    import array
    import io
    oggdec = shutil.which("oggdec")
    if not oggdec:
        print("WARNING: oggdec not found on PATH - cannot transcode click.ogg; "
              "the page will fall back to a synthesized click, not the Minecraft one")
        return None
    try:
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "click.ogg"
            dst = Path(td) / "click.wav"
            src.write_bytes(data)
            subprocess.run([oggdec, "-Q", "-o", str(dst), str(src)], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            with wave.open(str(dst), "rb") as wf:
                nch, sw, rate = wf.getnchannels(), wf.getsampwidth(), wf.getframerate()
                frames = wf.readframes(wf.getnframes())
        if sw != 2:
            raise ValueError(f"unexpected sample width {sw}")
        samples = array.array("h")
        samples.frombytes(frames)
        if nch == 2:                       # ステレオ -> モノラル(単純平均)
            samples = array.array(
                "h", ((samples[i] + samples[i + 1]) // 2 for i in range(0, len(samples), 2)))
        elif nch != 1:
            raise ValueError(f"unexpected channel count {nch}")
        peak = max(1, max(abs(v) for v in samples))
        thr = max(48, peak // 200)         # 約 -46dB を無音とみなす
        first = next((i for i, v in enumerate(samples) if abs(v) > thr), 0)
        last = next((i for i in range(len(samples) - 1, -1, -1) if abs(samples[i]) > thr),
                    len(samples) - 1)
        pad = rate // 400                  # 前後 2.5ms の余白
        first = max(0, first - pad)
        last = min(len(samples), last + 1 + pad)
        samples = samples[first:last]
        max_len = int(rate * 0.35)         # クリック音は 0.1〜0.2 秒。保険の上限
        if len(samples) > max_len:
            samples = samples[:max_len]
        buf = io.BytesIO()
        with wave.open(buf, "wb") as out:
            out.setnchannels(1)
            out.setsampwidth(2)
            out.setframerate(rate)
            out.writeframes(samples.tobytes())
        raw = buf.getvalue()
        if len(raw) > 65536:
            print(f"WARNING: transcoded click.wav is unexpectedly large ({len(raw)} bytes)")
        print(f"click sound: {idx_name} random/click.ogg ({len(data)} B) -> "
              f"mono WAV {len(samples) / rate * 1000:.0f} ms @ {rate} Hz ({len(raw)} B, "
              f"{len(base64.b64encode(raw))} B as base64)")
        return base64.b64encode(raw).decode()
    except Exception as exc:  # noqa: BLE001
        print(f"WARNING: could not transcode click.ogg ({exc}) - "
              f"the page will fall back to a synthesized click, not the Minecraft one")
        return None


def load_vanilla_en(zf):
    try:
        return json.loads(zf.read("assets/minecraft/lang/en_us.json").decode("utf-8"))
    except KeyError:
        print("WARNING: en_us.json not found in the vanilla client jar - "
              "English names fall back to title-cased ids")
        return {}


# ===========================================================================
# テクスチャの一意化(content-hash dedup)+ 可逆な再圧縮
# ===========================================================================
def recompress_png(data):
    """PNG をピクセル完全一致のまま小さくできたら小さい方を返す。

    候補は ①元のまま ②optimize 付き再エンコード ③256 色以下ならパレット化。
    どの候補も **デコードし直して RGBA が元とバイト一致することを検証してから**
    採用する(検証に落ちた候補は捨てる)ので、見た目が変わる事故は構造的に無い。
    """
    from PIL import Image
    import io
    try:
        src = Image.open(io.BytesIO(data))
        src.load()
        rgba = src.convert("RGBA")
    except Exception:  # noqa: BLE001 - 読めない PNG はそのまま出す
        return data
    ref = rgba.tobytes()
    best = data

    def consider(candidate):
        nonlocal best
        if len(candidate) >= len(best):
            return
        try:
            back = Image.open(io.BytesIO(candidate))
            back.load()
            if back.convert("RGBA").tobytes() == ref:
                best = candidate
        except Exception:  # noqa: BLE001
            pass

    buf = io.BytesIO()
    try:
        rgba.save(buf, format="PNG", optimize=True)
        consider(buf.getvalue())
    except Exception:  # noqa: BLE001
        pass
    if rgba.getcolors(256) is not None:
        try:
            pal = rgba.convert("P", palette=Image.ADAPTIVE, colors=256,
                               dither=Image.Dither.NONE)
            buf = io.BytesIO()
            pal.save(buf, format="PNG", optimize=True)
            consider(buf.getvalue())
        except Exception:  # noqa: BLE001
            pass
    return best


class ItemRegistry:
    """item id -> (日本語名, 英語名, テクスチャ key) を 1 回だけ解決して覚える。

    テクスチャは **中身(再圧縮後のバイト列)で一意化** する: 同じ絵を使う建材
    バリアント(石の縦ハーフ/円柱/スロープは全部 block/stone.png)や、何百回も
    出てくるバニラ素材が、ファイルに 1 回しか入らない。旧版はカードごとに同じ
    base64 を埋め直していた(建材だけで数 MB の重複)。
    """

    def __init__(self, van_ja, van_en, lang_by_modid, lang_en_by_modid):
        self.van_ja = van_ja
        self.van_en = van_en
        self.lang_by_modid = lang_by_modid
        self.lang_en_by_modid = lang_en_by_modid
        self.items = {}          # id -> [ja, en, tex_key or None]
        self.tex_payloads = {}   # b64 payload -> tex_key
        self.tex_order = []      # tex_key -> payload (emission order)
        self.raw_bytes = 0       # 再圧縮前の合計(統計用)

    def _tex_key(self, b64):
        if b64 is None:
            return None
        raw = base64.b64decode(b64)
        self.raw_bytes += len(raw)
        packed = recompress_png(raw)
        payload = base64.b64encode(packed).decode()
        key = self.tex_payloads.get(payload)
        if key is None:
            key = f"t{len(self.tex_order)}"
            self.tex_payloads[payload] = key
            self.tex_order.append(payload)
        return key

    def register(self, item_id):
        entry = self.items.get(item_id)
        if entry is not None:
            return entry
        ns, name = item_id.split(":", 1)
        if ns == "minecraft":
            ja = (self.van_ja.get(f"item.minecraft.{name}")
                  or self.van_ja.get(f"block.minecraft.{name}")
                  or VANILLA_JA_NAMES.get(name, name))
            en = (self.van_en.get(f"item.minecraft.{name}")
                  or self.van_en.get(f"block.minecraft.{name}")
                  or name.replace("_", " ").title())
            b64 = vanilla_texture_b64(vanilla_zip(), name)
        elif ns == "#minecraft":
            # バニラのアイテムタグ(`#minecraft:coals` など)。**中身は jar から読む。**
            # 見せかたは「代表 1 個のアイコン + どれでもよいことが分かる名前」。
            # アイコンを最初の 1 個にするのは、タグの並びが**バニラ側の宣言順**
            # だからで、こちらで選び直さない(選び直すと出典が 2 つになる)。
            members = vanilla_item_tag(name)
            mem_ja, mem_en = [], []
            for mid in members:
                mname = mid.split(":", 1)[1]
                mem_ja.append(self.van_ja.get(f"item.minecraft.{mname}")
                              or self.van_ja.get(f"block.minecraft.{mname}")
                              or VANILLA_JA_NAMES.get(mname, mname))
                mem_en.append(self.van_en.get(f"item.minecraft.{mname}")
                              or self.van_en.get(f"block.minecraft.{mname}")
                              or mname.replace("_", " ").title())
            # 長いタグは全部並べても読めないので、4 個まで挙げて残りは数で言う。
            # **黙って切らない** —— 「ほか N 種」と書けば、全部ではないことが分かる。
            if len(members) > 4:
                ja = "・".join(mem_ja[:4]) + f" ほか {len(members) - 4} 種のどれか"
                en = ", ".join(mem_en[:4]) + f" or {len(members) - 4} more"
            else:
                ja = "・".join(mem_ja) + " のどれか" if len(members) > 1 else mem_ja[0]
                en = " or ".join(mem_en)
            b64 = vanilla_texture_b64(vanilla_zip(), members[0].split(":", 1)[1])
        else:
            for mod_dir, modid, _cat in MODS:
                if modid == ns:
                    ja = display_name(self.lang_by_modid[modid], modid, name)
                    en = display_name(self.lang_en_by_modid[modid], modid, name)
                    b64 = mod_texture_b64(mod_dir, modid, name)
                    break
            else:
                # 未知の名前空間。バニラでない MOD のタグなど。現れたら黙って
                # 空欄にせず名指しする(§20.6 系の「静かな劣化」を作らない)。
                print(f"WARNING: unknown namespace in ingredient id {item_id}")
                ja = en = item_id
                b64 = None
        entry = [ja, en, self._tex_key(b64)]
        self.items[item_id] = entry
        return entry


# ===========================================================================
# ページ用のドット絵アセット(背景の土タイル・クラフト矢印)
# ===========================================================================
def gen_bg_tile_b64(zf):
    """バニラの dirt.png を 1/4 の明るさに落として 4 倍 NEAREST 拡大したタイル。
    (Minecraft のメニュー背景と同じ作法。CSS 拡大に頼らないのは、背景画像の
    image-rendering:pixelated 対応がブラウザでまちまちなため。)"""
    try:
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(zf.read("assets/minecraft/textures/block/dirt.png")))
        img = img.convert("RGB")
        img = Image.eval(img, lambda v: v // 4)
        img = img.resize((64, 64), Image.NEAREST)
        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        return base64.b64encode(buf.getvalue()).decode()
    except Exception as exc:  # noqa: BLE001
        print(f"WARNING: could not build the dirt background tile: {exc}")
        return None


def gen_arrow_b64():
    """クラフト画面の「→」矢印(26x17)を PIL で作図する(jar のスプライトパスは
    版で動くので推測しない。自作なので確実に存在し、ライセンスも問題にならない)。"""
    from PIL import Image
    import io
    body = (94, 94, 94, 255)
    img = Image.new("RGBA", (26, 17), (0, 0, 0, 0))
    px = img.load()
    for y in range(6, 11):          # 軸(高さ 5px)
        for x in range(2, 16):
            px[x, y] = body
    for i, x in enumerate(range(16, 25)):   # 鏃(半幅 8 -> 0)
        hw = 8 - i
        for y in range(8 - hw, 9 + hw):
            px[x, y] = body
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


# ジャンルタブのアイコン(そのジャンルの実在カードの id)。存在しない id を書いたら
# 黙って空タブにせず WARNING + そのジャンルの先頭カードで代用する。
CATEGORY_TAB_ICON = {
    "銃": "sorakaze_guns:assault_rifle",
    "電車": "sorakaze_rail:train",
    "建材": "sorakaze_deco:guardrail",
    "ドア": "sorakaze_deco:auto_door",
    "乗り物": "sorakaze_vehicles:compact_car_scarlet",
    "ボス": "sorakaze_boss:enhanced_beacon",
    "天空": "sorakaze_sky:angels_halo",
    "サバイバル": "sorakaze_survival:canteen",
    "電力": "sorakaze_power:breaker",
    "二相楽園": "sorakaze_planarcadia:portal_amethyst_block",
}
ALL_TAB_ICON = "minecraft:crafting_table"


def first(v):
    return v[0] if isinstance(v, list) else v


def parse_recipe(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    rtype = data.get("type", "")
    cells = [None] * 9
    if rtype == "minecraft:crafting_shaped":
        pattern = data["pattern"]
        key = data["key"]
        for row_i, row in enumerate(pattern):
            for col_i, ch in enumerate(row):
                if ch == " ":
                    continue
                cells[row_i * 3 + col_i] = first(key.get(ch))
    elif rtype == "minecraft:crafting_shapeless":
        for i, ing in enumerate(data["ingredients"][:9]):
            cells[i] = first(ing)
    else:
        return None  # skip non-crafting-table recipe types (none expected currently)
    result = data.get("result", {})
    return {"cells": cells, "result_id": result.get("id"), "count": result.get("count", 1)}


def cat_tokens(cat):
    """ジャンル名の検索語。漢字でもひらがなでも同じ結果になるように読みも入れる
    (「電車」で 35 件・「でんしゃ」で 21 件、のような食い違いを作らない)。"""
    return [cat, kana_fold(cat), reading_of(cat)[0]]


def search_blob(tokens):
    """検索用の索引文字列を作る。JS 側は正規化済みのクエリを indexOf するだけでよい。"""
    seen = []
    for t in tokens:
        if not t:
            continue
        t = search_norm(str(t))
        if t not in seen:
            seen.append(t)
    return " ".join(seen)


def item_tokens(item_id, ja_name):
    """1 アイテムぶんの検索語(日本語名・読み・かな畳み・英語 id)を返す。"""
    yomi, _ = reading_of(ja_name)
    local = item_id.split(":", 1)[1] if ":" in item_id else item_id
    return [ja_name, kana_fold(ja_name), yomi, _expand_choon(kana_fold(yomi)),
            item_id, local, local.replace("_", " ")]


def category_of(mod_cat, result_name):
    # v1.5.0: 建材 MOD のドアは 9 種 -> 98 種に増えた。DOOR_IDS の手書きリストだけで判定していると
    # v1.4.4 の 40 種と v1.5.0 の 50 種が 254 枚の建材カードに埋もれて探せない(実際そうなっていた)。
    # 命名規則(<素材>_<意匠>_door / *_grand_door)で機械的に振り分け、
    # 規則から外れる旧名(ふすま・ハッチ・シャッター・大型ドア)だけを DOOR_IDS で拾う。
    if mod_cat == "建材" and (result_name in DOOR_IDS
                              or result_name.endswith("_door")
                              or result_name.endswith("_hatch")
                              or result_name.endswith("_hatch_large")):
        return "ドア"
    return mod_cat


# ===========================================================================
# 「使い方」タブ(v1.8.1 で新設)
# ===========================================================================
#
# **レシピのカードは「何で作るか」しか答えない。「何ができるのか」は答えない。**
# v1.8.0 で自動仕分けの 10 種を出したが、早見表からは作り方しか分からず、
# 所有者が使い方に辿り着けなかった。ここはその穴を埋めるための場所である。
#
# 方針(発注): **絵で見せる。文章で説明しない。**
# 各例は「置きかた図 / 入るもの / 出るもの / 手順」の 4 つで構成する。
#
# 拡張のしかた: `GUIDES` に dict を 1 つ足すだけでタブの中に節が増える。
# 次のラウンドで来る「電源」「ブレーカー盤」も、この表に足すだけでよい。
#
# 図のセルの書きかた:
#   ("i", "<アイテム id>", "<下に出す短い説明>")   アイコン + 説明
#   ("a", "→")                                    矢印(→ ↓ ← ↑ が使える)
#   ("n", "文字")                                  文字だけのセル
#   None                                           空白
#
# ⚠ ここで使う id は**すべて実在しなければならない**。
# 存在しない id を書くと、ページ上は「?」の四角が出るだけで、生成は成功してしまう
# (§37 で 1 枚の「?」カードとして表に出た失敗と同じ形)。
# そうならないよう、main() が 3 つの検査を行い、1 つでも欠ければ**生成を止める**:
#   ① GUIDES が触れる id が全部 register() できてテクスチャを持つこと
#   ② SORTING_KIT の 10 種が全部カードとして実在すること
#   ③ SORTING_KIT の 10 種が全部どれかの図に登場すること(= 説明されていない部品が無い)

# 自動仕分け一式(sorakaze_deco の ModSorters と同じ 10 個)。
# ③ の検査に使う。ここを増やしたのに図に足さなければ、生成が落ちる。
SORTING_KIT = [
    "sorakaze_deco:sorting_filter",
    "sorakaze_deco:category_sorter",
    "sorakaze_deco:round_robin_splitter",
    "sorakaze_deco:overflow_valve",
    "sorakaze_deco:void_trash",
    "sorakaze_deco:item_pump",
    "sorakaze_deco:item_counter",
    "sorakaze_deco:stock_indicator",
    "sorakaze_deco:item_collector",
    "sorakaze_deco:filter_card",
]

# ===========================================================================
# 電力 MOD の数値を **実装から読む**(v1.8.2 で新設)
# ===========================================================================
#
# ⚠ **手引きに数字を打ち込んではならない。**
#
# 電力の数値は複数の作業が並行して動かしている最中の物である。手で書き写すと、
# 書いた瞬間は正しくても<b>出荷される頃には嘘になっている</b>。しかも早見表は
# 「本文だから」という理由で誰も検算しないので、その嘘は永久に残る。
#
# そこで食料品 300 種を `FoodCatalog.java` から直接読んでいるのと同じ方式にする:
# **出典は Java のソースと data の JSON だけ**で、ここには写しを置かない。
# 手引きの本文は `{fact}` の置換で数値を受け取る(→ `fill_facts`)。
#
# 検査(生成を止める側):
#   ⓐ 読もうとしたフィールドが 1 つでも消える/改名されると `SystemExit`。
#      —— §31.4 の「黙って落ちる」を作らないため、**欠落は必ずエラー**である。
#   ⓑ 手引きが使う `{fact}` が表に無ければ `SystemExit`。
#   ⓒ 逆に、表にあるのにどの手引きでも使われていない fact も `SystemExit`
#      (古い数字の残骸が「読まれているように見えて実は死んでいる」状態を作らない)。

POWER_JAVA = ROOT / "mods-src/sorakaze-power/src/main/java/net/sorakaze/sorakaze_power"
SURVIVAL_JAVA = ROOT / "mods-src/sorakaze-survival/src/main/java/net/sorakaze/sorakaze_survival"
POWER_TAGS = ROOT / "mods-src/sorakaze-power/src/main/resources/data/sorakaze_power/tags/block"

_JNUM = r"(-?\d+(?:_\d+)*(?:\.\d+)?(?:[eE][-+]?\d+)?[dDfFlL]?)"


def _java_number(tok):
    """Java の数値リテラル 1 個を Python の数に。"""
    t = tok.strip().rstrip("dDfFlL").replace("_", "")
    return int(t) if re.fullmatch(r"-?\d+", t) else float(t)


_CABLE_TIERS_CACHE = None


def cable_tiers():
    """`CableTier.java` の enum 宣言を読む -> [(定数名, ブロック名, 断面積, 絶縁階級)]。

    v1.8.4 でケーブルは 2 種類から 4 種類になり、同時に `PowerSpec` の既定の抵抗値が
    **リテラルをやめて enum から導く式**(`DEFAULT_STANDARD_OHMS_PER_BLOCK /
    tier.conductorAreaFactor()`)になった。だから早見表も同じ 1 個の出典から読む ——
    ここに断面積を書き写すと、`CableTier` を触った瞬間に手引きが嘘になる。

    **取れなければ生成を止める。**黙って 2 種類のままの手引きを出すほうが害が大きい。
    """
    global _CABLE_TIERS_CACHE
    if _CABLE_TIERS_CACHE is None:
        src = (POWER_JAVA / "grid/CableTier.java").read_text(encoding="utf-8")
        hits = re.findall(r'^\t([A-Z][A-Z0-9_]*)\("([a-z_]+)",\s*(\d+),\s*Voltage\.([A-Z0-9_]+)\)',
                          src, re.M)
        if not hits:
            raise SystemExit(
                "ERROR: the 使い方 tab could not read the CableTier enum constants - the shape "
                "of grid/CableTier.java changed.\n"
                "       Fix tools/gen_recipe_sheet.py rather than shipping a stale cable guide.")
        _CABLE_TIERS_CACHE = [(n, b, int(a), v) for n, b, a, v in hits]
    return _CABLE_TIERS_CACHE


def _expand_cable_tier_calls(raw):
    """`defaultOhmsPerBlock(CableTier.X)` を `(標準の抵抗 / 断面積)` に開く。

    断面積は {@link cable_tiers} = `CableTier.java` から読むので、この関数は
    **数を 1 つも持たない**。開いた先の `DEFAULT_STANDARD_OHMS_PER_BLOCK` は
    宣言順に先に解けているので、そのまま `_resolve_java_expr` が数にできる。
    """
    if "defaultOhmsPerBlock" not in raw:
        return raw
    factors = {name: area for name, _blk, area, _v in cable_tiers()}

    def sub(m):
        tier = m.group(1)
        if tier not in factors:
            raise SystemExit(
                "ERROR: the 使い方 tab found defaultOhmsPerBlock(CableTier.%s), but that tier "
                "is not declared in grid/CableTier.java" % tier)
        return "(DEFAULT_STANDARD_OHMS_PER_BLOCK / %d)" % factors[tier]

    return re.sub(r"(?:[A-Za-z_$][\w$]*\.)?defaultOhmsPerBlock\(\s*CableTier\.([A-Z0-9_]+)\s*\)",
                  sub, raw)


def java_field_defaults(path, names):
    """`public [static final] <型> <名> = <式>;` の右辺を名前 -> 文字列で返す。

    **宣言だけを拾う**(`public` と型トークンを要求する)ので、`validate()` の中の
    `this.x = this.xClamped();` のような代入には引っかからない。
    1 つでも見つからなければ **その場で生成を止める** —— 改名を黙って見逃すと、
    手引きは古い数字を出したまま「成功」してしまう。
    """
    src = path.read_text(encoding="utf-8")
    found = {}
    for name in names:
        m = re.search(r"public\s+(?:static\s+final\s+)?[A-Za-z_$][\w$<>\[\].]*\s+"
                      + re.escape(name) + r"\s*=\s*([^;]+);", src)
        if m:
            found[name] = m.group(1).strip()
    missing = [n for n in names if n not in found]
    if missing:
        raise SystemExit(
            "ERROR: the 使い方 tab reads %d field(s) that no longer exist in %s "
            "(renamed or deleted?): %s\n"
            "       Fix tools/gen_recipe_sheet.py rather than shipping a stale number."
            % (len(missing), path.relative_to(ROOT), ", ".join(missing)))
    return found


def _resolve_java_expr(raw, known):
    """リテラル / 既知の定数 / `A / 2.0` 程度の式を数に解く(eval は数式だけに限定)。"""
    raw = _expand_cable_tier_calls(raw.strip())
    if raw in ("true", "false"):
        return raw == "true"
    if re.fullmatch(_JNUM, raw):
        return _java_number(raw)
    if re.fullmatch(r'"[^"]*"', raw):
        return raw[1:-1]
    expr = re.sub(r"\b[A-Z][A-Za-z0-9_]*\.", "", raw)          # PowerSpec.X -> X
    for key, val in sorted(known.items(), key=lambda kv: -len(kv[0])):
        if isinstance(val, (int, float)) and not isinstance(val, bool):
            expr = re.sub(r"\b" + re.escape(key) + r"\b", repr(val), expr)
    expr = re.sub(r"(\d)[dDfFlL]\b", r"\1", expr)
    if not re.fullmatch(r"[-+*/(). 0-9eE]+", expr.strip()):
        raise SystemExit("ERROR: 使い方 tab cannot resolve the Java expression %r "
                         "(it stopped being a simple number)" % raw)
    return eval(expr, {"__builtins__": {}}, {})                # 数式のみ(上で検証済み)


def _java_regex(path, pattern, what, flags=0, many=False):
    """1 個の正規表現で読む。**取れなければ生成を止める。**"""
    src = path.read_text(encoding="utf-8")
    if many:
        hits = re.findall(pattern, src, flags)
        if not hits:
            raise SystemExit("ERROR: the 使い方 tab found no %s in %s - the shape of that "
                             "file changed" % (what, path.relative_to(ROOT)))
        return hits
    m = re.search(pattern, src, flags)
    if not m:
        raise SystemExit("ERROR: the 使い方 tab could not read %s from %s - the shape of that "
                         "file changed" % (what, path.relative_to(ROOT)))
    return m


def tag_block_ids(name):
    """`data/sorakaze_power/tags/block/<name>.json` の値を id の並びで返す。

    `{"id": ..., "required": false}` の形も素の文字列も同じに扱う。
    `#other:tag` の参照はそのまま返す(呼び出し側で除く)。
    """
    path = POWER_TAGS / (name + ".json")
    if not path.exists():
        raise SystemExit("ERROR: the 使い方 tab needs the block tag %s, which does not exist "
                         "(renamed or deleted?)" % path.relative_to(ROOT))
    out = []
    for v in json.loads(path.read_text(encoding="utf-8"))["values"]:
        out.append(v["id"] if isinstance(v, dict) else v)
    if not out:
        raise SystemExit("ERROR: block tag %s is empty - the 使い方 tab would silently "
                         "describe nothing" % name)
    return out


def _fmt(x, nd=0):
    """人が読む数(3 桁区切り。小数は必要なぶんだけ)。"""
    if isinstance(x, float) and not x.is_integer():
        return f"{x:,.{nd or 2}f}".rstrip("0").rstrip(".")
    return f"{int(x):,}"


_GATE_LANG_CACHE = {}


def ja_block_names(ids):
    """ブロック id の並び -> 「A・B・C」(日本語名を中黒でつないだ 1 つの文字列)。

    v1.8.4 で「通電すると止まる」装置が 17 → 3 になり、**数えるより名前で言うほうが
    親切な数**になったので用意した。名前は各 MOD の `ja_jp.json` から引く ——
    <b>ここに名前を書き写さない</b>。写した瞬間に 2 つ目の出典ができて、
    ブロックを改名した日に手引きだけが古くなる(このファイルが繰り返し防いできた失敗)。

    タグ参照(`#...`)は飛ばす。引けない id があれば **その場で生成を止める**:
    生の id を所有者に見せるくらいなら、生成を失敗させたほうがよい。
    """
    mod_dir_by_modid = {modid: mod_dir for mod_dir, modid, _ in MODS}
    names = []
    for iid in ids:
        if iid.startswith("#"):
            continue
        modid, name = iid.split(":", 1)
        if modid not in _GATE_LANG_CACHE:
            if modid not in mod_dir_by_modid:
                raise SystemExit(
                    "ERROR: the 使い方 tab cannot name %s - %r is not one of the MODS, so its "
                    "ja_jp.json is unknown" % (iid, modid))
            _GATE_LANG_CACHE[modid] = load_lang(mod_dir_by_modid[modid], modid)
        ja = _GATE_LANG_CACHE[modid].get("block.%s.%s" % (modid, name))
        if not ja:
            raise SystemExit(
                "ERROR: the 使い方 tab has no Japanese name for %s (block.%s.%s is missing from "
                "ja_jp.json) - the guide would print a raw id at the owner"
                % (iid, modid, name))
        names.append(ja)
    if not names:
        raise SystemExit("ERROR: the 使い方 tab was asked to name an empty set of blocks - "
                         "the guide would render a dangling sentence")
    return "・".join(names)


def read_power_facts():
    """電力の数値を実装から集める。**返る dict が手引きの唯一の数字の出典である。**"""
    cfg_path = POWER_JAVA / "config/PowerConfig.java"
    spec_path = POWER_JAVA / "grid/PowerSpec.java"

    spec_names = ["DEFAULT_STANDARD_OHMS_PER_BLOCK", "DEFAULT_INSULATED_OHMS_PER_BLOCK",
                  "DEFAULT_HEAVY_OHMS_PER_BLOCK", "DEFAULT_SHIELDED_OHMS_PER_BLOCK",
                  "DEFAULT_LOSS_BUDGET_FRACTION", "DEFAULT_REFERENCE_BRANCH_WATTS",
                  "DEFAULT_TRANSFORMER_CROSSOVER_BLOCKS", "DEFAULT_DEVICE_WATTS",
                  "DEFAULT_MAX_NODES"]
    raw_spec = java_field_defaults(spec_path, spec_names)
    spec = {}
    for n in spec_names:                       # 宣言順に解くので `A / 2.0` が解ける
        spec[n] = _resolve_java_expr(raw_spec[n], spec)

    # ⚠ v1.8.4: `hoppersRequirePower` を**読むのをやめた**。あのつまみは
    # `HopperPowerLockMixin` / `PowerFuelHoppers` ごと削除されており、
    # ここに残したままだと `java_field_defaults` が「そんなフィールドは無い」で
    # 生成を止める(実際に止まった)。**手引きの本文からも消してある** ——
    # 消えたつまみの名前を案内するのは、無い物を触らせることになるため。
    cfg_names = ["powerEnabled", "redstoneRequiresPower", "redstoneBlockDecaySeconds",
                 "redstoneBlockDecayDropsItem", "invertedConsumersRequirePower",
                 "ticksPerCoal", "reactorTicksPerCell", "reactorCellBuffer",
                 "baseOutputUnits", "poorMultiplier", "standardMultiplier",
                 "highMultiplier", "veryHighMultiplier", "energyCellMultiplier",
                 "energyCellBurnTicks", "breakerFuelEfficiency",
                 "solarOutputUnits", "windOutputUnits", "hydroOutputUnits",
                 "windBaseAltitude", "windFullAltitude", "hydroFacesForFullOutput",
                 "cellRuntimeTicks", "fireplaceTicksPerCoal",
                 "cableStandardOhmsPerBlock", "cableInsulatedOhmsPerBlock",
                 "lineLossBudgetFraction", "referenceBranchWatts",
                 "transformerCrossoverBlocks", "deviceWatts",
                 # V2 §9.2/§10(2026-08-17): 大気汚染と空気清浄機。
                 # `PowerConfig.PollutionSettings` の中の宣言だが、
                 # `java_field_defaults` はファイル全体から `public <型> <名> =` を拾うので
                 # 入れ子クラスでも同じに読める(名前はこのファイル内で一意であることを確認済み)。
                 # ⚠ ここに数を書き写さない。書き写した瞬間に config と手引きの 2 つの出典ができる。
                 "generatorRadiusBlocks", "purifierRadiusBlocks", "purifierClearSeconds",
                 "lightThreshold", "heavyThreshold", "severeThreshold", "maxLevel"]
    raw_cfg = java_field_defaults(cfg_path, cfg_names)
    cfg = {n: _resolve_java_expr(raw_cfg[n], spec) for n in cfg_names}

    # ---- enum・定数 ------------------------------------------------------
    #
    # v1.8.4: `Voltage` は「その段に要る最低ティア」を持たなくなった。持てなくなった、
    # と言うほうが正しい —— ケーブルが 4 種類になり、しかも
    # <b>ティアに全順序が無い</b>(太径は絶縁ケーブルより抵抗が小さいのに高圧を載せられない)
    # ので、「最低ティア」という 1 個の答えがそもそも存在しない。
    # いまは電圧どうしを比べる(`CableTier#supports`)ので、早見表も同じ規則で
    # <b>その段を載せられるティアを数え上げる</b>。
    volts = _java_regex(POWER_JAVA / "grid/Voltage.java",
                        r'^\t([A-Z0-9_]+)\("([a-z0-9]+)",\s*' + _JNUM +
                        r',\s*(true|false)\)',
                        "the Voltage steps", re.M, many=True)
    amp_path = POWER_JAVA / "breaker/AmpRating.java"
    steps = [int(x) for x in _java_regex(amp_path, r"int\[\]\s+STEPS\s*=\s*\{([^}]*)\}",
                                         "the amp ratings").group(1).replace("_", "").split(",")]
    headroom = _java_number(_java_regex(amp_path, r"double\s+HEADROOM\s*=\s*" + _JNUM,
                                        "the amp headroom").group(1))
    circuits = int(_java_regex(POWER_JAVA / "breaker/BreakerBlockEntity.java",
                               r"int\s+CIRCUITS\s*=\s*(\d+)", "the circuit count").group(1))
    fq = _java_regex(POWER_JAVA / "machine/FuelQuality.java",
                     r'^\t([A-Z_]+)\("([a-z_]+)",\s*' + _JNUM + r'\)',
                     "the fuel qualities", re.M, many=True)
    kinds = _java_regex(POWER_JAVA / "renewable/RenewableKind.java",
                        r'^\t([A-Z]+)\("([a-z_]+)"\)', "the renewable kinds", re.M, many=True)

    def _dim(rel, field):
        return int(_java_regex(POWER_JAVA / rel, r"int\s+%s\s*=\s*(\d+)" % field,
                               "%s of %s" % (field, rel)).group(1))

    # LED パネル照明(v1.8.4)。**光量と厚みだけを読む。**
    # 「たいまつの何倍」の実測値は Java の javadoc と ja_jp.json の説明文にしか無い散文なので、
    # ここに写すと<b>2 つ目の出典</b>ができて必ず食い違う。手引きは倍率を書かず、
    # アイテムの説明(翻訳済みで、実装と同じ場所で管理されている)へ送る。
    led_light = int(_java_regex(POWER_JAVA / "light/LedPanelBlock.java",
                                r"int\s+LIGHT_LEVEL\s*=\s*(\d+)",
                                "the LED panel light level").group(1))
    led_thickness = _java_number(_java_regex(POWER_JAVA / "light/LedPanelBlock.java",
                                             r"double\s+THICKNESS\s*=\s*" + _JNUM,
                                             "the LED panel thickness").group(1))

    mw, mh, md = (_dim("machine/MachineVolume.java", f) for f in ("WIDTH", "HEIGHT", "DEPTH"))
    aw, ah, ad = (_dim("appliance/AirConditionerVolume.java", f)
                  for f in ("WIDTH", "HEIGHT", "DEPTH"))

    # ---- 気温(数値の出典は sorakaze_survival 側)--------------------------
    #
    # v1.8.3: 「稼働中の機械がその空間を暖める」が入ったので、暖炉・エアコンだけでなく
    # 機械の熱もここから読む。**手引きに数字を打ち込まないこと**は §1263 の方針のとおり。
    #
    # ⚠ `DEFAULT_MACHINE_HEAT_CELSIUS` は数ではなく式である
    #   (`-DEFAULT_AIR_CONDITIONER_CELSIUS / MACHINES_PER_AIR_CONDITIONER`)。
    #   だから **宣言順に解く** —— 先に定数 3 つを解いてから config の項を解かないと、
    #   `_resolve_java_expr` が名前を数に置きかえられずに落ちる。
    temp_const_names = ["MACHINES_PER_AIR_CONDITIONER", "DEFAULT_AIR_CONDITIONER_CELSIUS",
                        "DEFAULT_MACHINE_HEAT_CELSIUS"]
    raw_tc = java_field_defaults(SURVIVAL_JAVA / "config/SurvivalConfig.java", temp_const_names)
    temp_const = {}
    for n in temp_const_names:
        temp_const[n] = _resolve_java_expr(raw_tc[n], temp_const)

    temp_names = ["temperatureFireplaceCelsius",
                  "temperatureAirConditionerCelsius",
                  "temperatureSourceRadiusBlocks",
                  "temperatureMachineHeatCelsius",
                  "temperatureReactorHeatMultiplier",
                  "temperatureRenewableHeatCelsius",
                  "temperatureMachineOpenAirFactor",
                  "temperatureMachineMaxSwingCelsius",
                  "temperatureComfortMaxCelsius",
                  "temperatureScorchingCelsius"]
    raw_temp = java_field_defaults(SURVIVAL_JAVA / "config/SurvivalConfig.java", temp_names)
    temp = {k: _resolve_java_expr(raw_temp[k], temp_const) for k in temp_names}

    # ---- 逆算(手で置いた数は 1 つも無い)---------------------------------
    f = cfg["lineLossBudgetFraction"]
    ref_w = cfg["referenceBranchWatts"]
    r_std = cfg["cableStandardOhmsPerBlock"]
    r_ins = cfg["cableInsulatedOhmsPerBlock"]
    dev_w = cfg["deviceWatts"]

    def reach(v, ohms):                       # L = f·V² / (P·r)
        return f * float(v) ** 2 / (ref_w * ohms)

    def devices_for(units):
        """供給 `units` 単位/tick で足りる機器の台数(需要 = 1 + floor(W / 基準W))。"""
        n = 0
        while 1 + int((n + 1) * dev_w / ref_w) <= units:
            n += 1
        return n

    volt_by_key = {k: (float(v), needs == "true") for _n, k, v, needs in volts}
    base = cfg["baseOutputUnits"]
    quality = {key: float(m) for _n, key, m in fq}

    # ---- ケーブルのティア(4 隅)------------------------------------------
    #
    # config のキー名はティアの名前から機械的に出す(`cableOhmsPerBlockClamped` の
    # switch と同じ対応)。**5 つ目を足したら `java_field_defaults` が
    # 「そんなフィールドは無い」で生成を止める**ので、手引きだけ 4 種類のまま、
    # ということが起こらない。
    tier_ja = load_lang(ROOT / "mods-src/sorakaze-power", "sorakaze_power")
    volt_const_key = {n: k for n, k, _v, _needs in volts}   # V200 -> "200v"
    tiers = []
    for const, block_name, area, insul in cable_tiers():
        key = "cable" + const.capitalize() + "OhmsPerBlock"
        ohms = _resolve_java_expr(java_field_defaults(cfg_path, [key])[key], spec)
        name = tier_ja.get("block.sorakaze_power." + block_name)
        if not name:
            raise SystemExit(
                "ERROR: the 使い方 tab has no Japanese name for the cable tier %r "
                "(block.sorakaze_power.%s missing from ja_jp.json)" % (const, block_name))
        if insul not in volt_const_key:
            raise SystemExit(
                "ERROR: cable tier %s declares insulation class Voltage.%s, which is not one "
                "of the Voltage steps" % (const, insul))
        tiers.append({"const": const, "id": "sorakaze_power:" + block_name, "name": name,
                      "area": area, "ohms": ohms,
                      "max_volts": volt_by_key[volt_const_key[insul]][0]})
    # 高圧を載せられるのはどれか。**序数ではなく電圧の比較**で決める
    # (`CableTier#supports` と同じ規則。太径は絶縁ケーブルより抵抗が小さいが高圧は不可)。
    high_v = volt_by_key["high"][0]
    high_tiers = [t for t in tiers if t["max_volts"] >= high_v]
    if not high_tiers:
        raise SystemExit("ERROR: no cable tier can carry the high-voltage step - the 使い方 tab "
                         "would tell the owner to use a cable that does not exist")
    std = next(t for t in tiers if t["const"] == "STANDARD")
    # 低圧のなかでいちばん太いもの / 全体でいちばん太いもの。**序数ではなく断面積で選ぶ**
    # (`CableTier` の javadoc が言うとおり、ティアに全順序は無い)。
    low_only = [t for t in tiers if t["max_volts"] < high_v]
    if not low_only:
        raise SystemExit("ERROR: every cable tier carries high voltage - the 使い方 tab's "
                         "「安いほうで足りる」 comparison would be meaningless")
    heavy = max(low_only, key=lambda t: t["area"])
    best = max(tiers, key=lambda t: t["area"])

    facts = {
        # --- 送電 ---
        "cable_reach_100": _fmt(reach(volt_by_key["100v"][0], r_std)),
        "cable_reach_200": _fmt(reach(volt_by_key["200v"][0], r_std)),
        "ins_reach_100": _fmt(reach(volt_by_key["100v"][0], r_ins)),
        "ins_reach_200": _fmt(reach(volt_by_key["200v"][0], r_ins)),
        "ins_ratio": _fmt(r_std / r_ins),
        "volts_100": _fmt(volt_by_key["100v"][0]),
        "volts_200": _fmt(volt_by_key["200v"][0]),
        "volts_high": _fmt(volt_by_key["high"][0]),
        # 高圧を載せられるケーブル。**1 種類とは限らない**ので数え上げて並べる。
        "high_tier": "か".join(t["name"] for t in high_tiers),
        "cable_kinds": _fmt(len(tiers)),
        # 低圧で最も太いもの / 全体で最も太いもの。名前も倍率も実装から出しているので、
        # ティアを組み替えても手引きが嘘にならない。
        "heavy_name": heavy["name"],
        "heavy_ratio": _fmt(std["ohms"] / heavy["ohms"]),
        "heavy_reach_100": _fmt(reach(volt_by_key["100v"][0], heavy["ohms"])),
        "heavy_reach_200": _fmt(reach(volt_by_key["200v"][0], heavy["ohms"])),
        "best_name": best["name"],
        "best_ratio": _fmt(std["ohms"] / best["ohms"]),
        "best_reach_100": _fmt(reach(volt_by_key["100v"][0], best["ohms"])),
        "best_reach_200": _fmt(reach(volt_by_key["200v"][0], best["ohms"])),
        "secondary_volts": _fmt(volt_by_key["200v"][0]),
        "loss_budget_pct": _fmt(f * 100),
        "crossover": _fmt(cfg["transformerCrossoverBlocks"]),
        "max_nodes": _fmt(spec["DEFAULT_MAX_NODES"]),
        # --- 分電盤 ---
        "circuits": _fmt(circuits),
        "voltage_steps": _fmt(len(volts)),
        "amp_steps": " / ".join("%dA" % a for a in steps),
        "amp_steps_count": _fmt(len(steps)),
        "amp_min": "%dA" % steps[0],
        "amp_max": "%dA" % steps[-1],
        "amp_headroom_pct": _fmt(100.0 / headroom),
        "device_watts": _fmt(dev_w),
        "branch_watts": _fmt(ref_w),
        "devices_per_branch": _fmt(ref_w / dev_w),
        "amp_min_devices_100": _fmt(int(volt_by_key["100v"][0] * steps[0] / dev_w)),
        "amp_min_devices_200": _fmt(int(volt_by_key["200v"][0] * steps[0] / dev_w)),
        "cell_minutes": _fmt(cfg["cellRuntimeTicks"] / 20.0 / 60.0),
        "breaker_fuel_pct": _fmt(cfg["breakerFuelEfficiency"] * 100),
        # --- 燃料 ---
        "coal_units": _fmt(quality["standard"] * base),
        "coal_devices": _fmt(devices_for(quality["standard"] * base)),
        "wood_units": _fmt(quality["poor"] * base),
        "wood_devices": _fmt(devices_for(quality["poor"] * base)),
        "blaze_units": _fmt(quality["high"] * base),
        "blaze_devices": _fmt(devices_for(quality["high"] * base)),
        "lava_units": _fmt(quality["very_high"] * base),
        "lava_devices": _fmt(devices_for(quality["very_high"] * base)),
        "cell_units": _fmt(quality["best"] * base),
        "cell_devices": _fmt(devices_for(quality["best"] * base)),
        "wood_ratio": _fmt(quality["standard"] / quality["poor"]),
        "coal_seconds": _fmt(cfg["ticksPerCoal"] / 20.0),
        "coal_total": _fmt(cfg["ticksPerCoal"] * quality["standard"] * base),
        "cell_seconds": _fmt(cfg["energyCellBurnTicks"] / 20.0),
        "reactor_seconds": _fmt(cfg["reactorTicksPerCell"] / 20.0),
        "reactor_buffer": _fmt(cfg["reactorCellBuffer"]),
        # --- 再生可能 ---
        "solar_units": _fmt(cfg["solarOutputUnits"]),
        "solar_devices": _fmt(devices_for(cfg["solarOutputUnits"])),
        "wind_units": _fmt(cfg["windOutputUnits"]),
        "wind_devices": _fmt(devices_for(cfg["windOutputUnits"])),
        "hydro_units": _fmt(cfg["hydroOutputUnits"]),
        "hydro_devices": _fmt(devices_for(cfg["hydroOutputUnits"])),
        "wind_base_y": _fmt(cfg["windBaseAltitude"]),
        "wind_full_y": _fmt(cfg["windFullAltitude"]),
        "hydro_faces": _fmt(cfg["hydroFacesForFullOutput"]),
        "renewable_count": _fmt(len(kinds)),
        # --- LED パネル照明 ---
        "led_light": _fmt(led_light),
        "led_thickness_px": _fmt(led_thickness),
        # --- 大きさ ---
        "machine_size": "%d×%d×%d" % (mw, md, mh),
        "aircon_size": "%d×%d×%d" % (aw, ad, ah),
        # --- 気温 ---
        "fireplace_c": _fmt(temp["temperatureFireplaceCelsius"]),
        "aircon_c": _fmt(abs(temp["temperatureAirConditionerCelsius"])),
        "temp_radius": _fmt(temp["temperatureSourceRadiusBlocks"]),
        "fireplace_seconds": _fmt(cfg["fireplaceTicksPerCoal"] / 20.0),
        # --- 機械の熱(v1.8.3)---
        # ⚠ どれも実装から読んだ値である。手で書いた数は 1 つも無い。
        "machine_heat_c": _fmt(temp["temperatureMachineHeatCelsius"]),
        "reactor_heat_c": _fmt(temp["temperatureMachineHeatCelsius"]
                               * temp["temperatureReactorHeatMultiplier"]),
        "renewable_heat_c": _fmt(temp["temperatureRenewableHeatCelsius"]),
        # エアコン 1 台が打ち消す発電機の台数(2.5 のような小数になりうる)。
        "machines_per_ac": _fmt(temp_const["MACHINES_PER_AIR_CONDITIONER"], 1),
        # 発電機 n 台を打ち消すのに要るエアコンの台数(切り上げ。買い物の答えなので整数)。
        "ac_for_four": _fmt(math.ceil(4 / temp_const["MACHINES_PER_AIR_CONDITIONER"])),
        "ac_for_eight": _fmt(math.ceil(8 / temp_const["MACHINES_PER_AIR_CONDITIONER"])),
        # 熱が飽和する台数(上限 °C ÷ 1 台ぶん)。
        "machine_cap_count": _fmt(temp["temperatureMachineMaxSwingCelsius"]
                                  / temp["temperatureMachineHeatCelsius"]),
        "machine_cap_c": _fmt(temp["temperatureMachineMaxSwingCelsius"]),
        "open_air_pct": _fmt(temp["temperatureMachineOpenAirFactor"] * 100),
        "comfort_max_c": _fmt(temp["temperatureComfortMaxCelsius"]),
        "scorching_c": _fmt(temp["temperatureScorchingCelsius"]),
        # 上がる幅(台数 × 1 台ぶん)。**絶対温度は出さない** ——
        # 拠点の元の気温は土地・高さ・屋根で変わるので、ここで 1 つの数に決めると嘘になる。
        # config が宣言しているのは「1 台が何 °C 上げるか」だけなので、幅だけを言う。
        "heat_2": _fmt(2 * temp["temperatureMachineHeatCelsius"]),
        "heat_4": _fmt(4 * temp["temperatureMachineHeatCelsius"]),
        "heat_8": _fmt(8 * temp["temperatureMachineHeatCelsius"]),
        # --- 大気汚染と空気清浄機(V2 §9.2/§10)---
        # ⚠ どれも `PowerConfig.PollutionSettings` から読んだ既定値である。
        #    手で書いた数は 1 つも無い。所有者が config を変えたら手引きも一緒に変わる。
        "pollution_radius": _fmt(cfg["generatorRadiusBlocks"]),
        "purifier_radius": _fmt(cfg["purifierRadiusBlocks"]),
        "purifier_seconds": _fmt(cfg["purifierClearSeconds"]),
        "pollution_light": _fmt(cfg["lightThreshold"]),
        "pollution_heavy": _fmt(cfg["heavyThreshold"]),
        "pollution_severe": _fmt(cfg["severeThreshold"]),
        "pollution_max": _fmt(cfg["maxLevel"]),
        # --- レッドストーン ---
        "decay_minutes": _fmt(cfg["redstoneBlockDecaySeconds"] / 60.0),
        "decay_drops": "アイテムとして落ちます" if cfg["redstoneBlockDecayDropsItem"]
                       else "そのまま消えます",
        "gated_count": _fmt(len(tag_block_ids("power_gated_source"))),
        "exempt_count": _fmt(len(tag_block_ids("power_gate_exempt_source"))),
        "inverted_count": _fmt(len(tag_block_ids("power_gate_inverted_consumer"))),
        # v1.8.4: 3 つに絞れたので **名前で言う**。「3 種」とだけ言われても、
        # 所有者は自分の拠点のどれが該当するのか分からない。
        "inverted_names": ja_block_names(tag_block_ids("power_gate_inverted_consumer")),
        # 対象から外して「電気が無くても動く」に戻したもの。**タグから数える** ——
        # 14 と書き込むと、次に 1 個戻したり外したりした日に手引きだけが嘘になる。
        # バニラのホッパーは同じタグに居るが MOD のブロックではないので別に数える。
        "freed_count": _fmt(len([i for i in tag_block_ids("power_gate_rewake")
                                 if not i.startswith("minecraft:")])),
    }
    return facts


POWER_FACTS = read_power_facts()

# 「電気が要る機器」の一覧。**タグを唯一の出典にする**ので、
# 相手の MOD に機器が増えたら(= タグに 1 行増えたら)検査⑥が生成を止める。
POWERED_DEVICE_IDS = [i for i in tag_block_ids("power_devices") if not i.startswith("#")]
# 送電網から見えるが `power_devices` には載っていない機器(建材側が自分の config で
# 判定しているもの)。ここも図に出ていなければ生成を止める。
POWERED_EXTRA_IDS = [i for i in tag_block_ids("cable_connectable")
                     if not i.startswith("#") and not i.startswith("sorakaze_power:")
                     and i not in POWERED_DEVICE_IDS]


def fill_facts(node):
    """手引きの文字列の `{fact}` を実装から読んだ値に置きかえる(再帰)。

    ⚠ 表に無い名前を書いたら **その場で生成を止める**。
       黙って `{typo}` を出力すると、所有者には「壊れた本文」としてしか見えない。
    """
    if isinstance(node, str):
        def sub(m):
            key = m.group(1)
            if key not in POWER_FACTS:
                raise SystemExit(
                    "ERROR: the 使い方 tab refers to the unknown value {%s} - either the "
                    "implementation stopped exposing it, or this is a typo. Known: %s"
                    % (key, ", ".join(sorted(POWER_FACTS))))
            USED_FACTS.add(key)
            return POWER_FACTS[key]
        return re.sub(r"\{([a-z_0-9]+)\}", sub, node)
    if isinstance(node, list):
        return [fill_facts(v) for v in node]
    if isinstance(node, tuple):
        return tuple(fill_facts(v) for v in node)
    if isinstance(node, dict):
        return {k: fill_facts(v) for k, v in node.items()}
    return node


USED_FACTS = set()


GUIDES = [
    {
        "id": "sorting",
        "icon": "sorakaze_deco:sorting_filter",
        "tab": "使い方",
        "title": "自動仕分けの使い方",
        "lede": "しまう場所を自分で決めてくれる倉庫を作ります。"
                "むずかしい配線はいりません。まずは①だけ作ってみてください。",
        "sections": [
            {
                "title": "① まず 1 台だけ置いてみる",
                "goal": "石炭だけが右の箱に入るようにします。ここが全部の基本です。",
                "diagram": {
                    "caption": "うしろの箱から取り出して、正面の箱へ入れます(横から見た図)",
                    "rows": [[
                        ("i", "minecraft:chest", "なんでも入れる箱"),
                        ("a", "→"),
                        ("i", "sorakaze_deco:sorting_filter", "仕分けフィルター"),
                        ("a", "→"),
                        ("i", "minecraft:chest", "石炭だけたまる箱"),
                    ]],
                },
                "io": {
                    "in": [("minecraft:coal", "石炭"), ("minecraft:iron_ingot", "鉄"),
                           ("minecraft:wheat", "小麦")],
                    "out": [("minecraft:coal", "石炭だけ通る")],
                },
                "steps": [
                    "箱・仕分けフィルター・箱を、この順で<b>くっつけて</b>置きます。",
                    "仕分けフィルターの<b>正面(色のついた面)が、入れたい箱の方</b>を向くように置きます。",
                    "<b>石炭を手に持って</b>仕分けフィルターを右クリックします。"
                    "これで「石炭を通す」と覚えます(<b>持っている石炭は減りません</b>)。",
                    "これで完成です。左の箱に何を入れても、石炭だけが右の箱へ移っていきます。",
                ],
                "notes": [
                    "見本を<b>何も登録していないと、何も通りません</b>(壊れているのではありません)。",
                    "登録を消すときは、同じアイテムを持ってもう一度右クリックします。"
                    "全部消すときはスニーク+右クリック。素手で右クリックすると今の一覧が出ます。",
                ],
            },
            {
                "title": "② 横に並べて「仕分け場」にする",
                "goal": "1 本の線から、種類ごとの箱へ振り分けます。倉庫らしくなるのはここからです。",
                "diagram": {
                    "caption": "上の線を流し、下へ落として仕分けます(横から見た図)",
                    "rows": [
                        [
                            ("i", "minecraft:chest", "入口の箱"),
                            ("a", "→"),
                            ("i", "sorakaze_deco:item_pump", "搬送ポンプ"),
                            ("a", "→"),
                            ("i", "sorakaze_deco:item_pump", "搬送ポンプ"),
                            ("a", "→"),
                            ("i", "sorakaze_deco:void_trash", "廃棄装置"),
                        ],
                        [
                            None, None, ("a", "↓"), None, ("a", "↓"), None,
                            ("n", "あふれた分"),
                        ],
                        [
                            None, None,
                            ("i", "sorakaze_deco:sorting_filter", "鉄を登録"),
                            None,
                            ("i", "sorakaze_deco:sorting_filter", "石炭を登録"),
                            None, None,
                        ],
                        [
                            None, None, ("a", "↓"), None, ("a", "↓"), None, None,
                        ],
                        [
                            None, None, ("i", "minecraft:chest", "鉄の箱"),
                            None, ("i", "minecraft:chest", "石炭の箱"), None, None,
                        ],
                    ],
                },
                "io": {
                    "in": [("minecraft:iron_ingot", "鉄"), ("minecraft:coal", "石炭"),
                           ("minecraft:cobblestone", "丸石")],
                    "out": [("minecraft:iron_ingot", "鉄の箱へ"), ("minecraft:coal", "石炭の箱へ"),
                            ("minecraft:cobblestone", "登録が無いので最後まで流れる")],
                },
                "steps": [
                    "<b>搬送ポンプ</b>で幹線(太い流れ)を作ります。ホッパーより速く、"
                    "1 回にひとかたまり運ぶので詰まりません。",
                    "仕分けたい種類のぶんだけ<b>仕分けフィルター</b>を下向きに置き、"
                    "それぞれに見本を登録します。",
                    "いちばん最後に<b>廃棄装置</b>を置くと、どの箱にも入らなかった物が消えます。"
                    "捨てたくない物があるなら、代わりにふつうの箱を置いてください。",
                ],
                "notes": [
                    "<b>廃棄装置も、見本に登録した物だけを消します。</b>"
                    "置いただけでは何も消えないので、先に置いてから設定しても安全です。",
                ],
            },
            {
                "title": "③ 種類が多すぎるときは、先に大きく分ける",
                "goal": "食べ物 40 種類を 1 台ずつ登録するのは大変です。まとめて分けます。",
                "diagram": {
                    "caption": "8 分類(食料・道具・鉱石・農業・レッドストーン・燃料・建材・その他)",
                    "rows": [[
                        ("i", "minecraft:chest", "なんでも入れる箱"),
                        ("a", "→"),
                        ("i", "sorakaze_deco:category_sorter", "「食料」に設定"),
                        ("a", "→"),
                        ("i", "minecraft:chest", "食べ物の箱"),
                    ]],
                },
                "io": {
                    "in": [("minecraft:bread", "パン"), ("minecraft:apple", "リンゴ"),
                           ("minecraft:iron_pickaxe", "ツルハシ")],
                    "out": [("minecraft:bread", "食料は通る"), ("minecraft:apple", "食料は通る")],
                },
                "steps": [
                    "カテゴリー仕分け機を置きます。置きかたは仕分けフィルターと同じです。",
                    "<b>素手で右クリック</b>すると分類が切りかわります。"
                    "出したい分類が出るまで押してください。",
                    "見本の登録はいりません。分類に当てはまる物が、まとめて通ります。",
                ],
                "notes": [
                    "こまかく分けたいときは、このうしろに<b>仕分けフィルター</b>を足します"
                    "(大きく分けてから、細かく分ける)。",
                ],
            },
            {
                "title": "④ かまどを何台も同時に動かす",
                "goal": "1 本の線から、かまど 5 台へ均等に配ります。",
                "diagram": {
                    "caption": "分配器にくっつけたコンテナへ、順番に 1 個ずつ配ります",
                    "rows": [
                        [None, None, ("i", "minecraft:chest", "原木の箱"), None, None],
                        [None, None, ("a", "↓"), None, None],
                        [None, None, ("i", "sorakaze_deco:round_robin_splitter", "振り分け分配器"), None, None],
                        [("a", "↓"), None, ("a", "↓"), None, ("a", "↓")],
                        [("i", "minecraft:furnace", "かまど"), None,
                         ("i", "minecraft:furnace", "かまど"), None,
                         ("i", "minecraft:furnace", "かまど")],
                    ],
                },
                "io": {
                    "in": [("minecraft:oak_log", "原木 64 個")],
                    "out": [("minecraft:oak_log", "3 台に 21〜22 個ずつ")],
                },
                "steps": [
                    "振り分け分配器のまわりに、かまど(や箱)をくっつけて置きます。",
                    "入ってきた側をのぞく<b>5 面すべて</b>が配り先になります。",
                    "見本の登録はいりません。入った物を順番に配るだけです。",
                ],
            },
            {
                "title": "⑤ 箱が満杯でも止まらないようにする",
                "goal": "行き先が満杯になると、ふつうは仕分け場ぜんぶが止まります。それを防ぎます。",
                "diagram": {
                    "caption": "正面が満杯のときだけ、横へ逃がします",
                    "rows": [
                        [None, ("i", "sorakaze_deco:overflow_valve", "溢れ防止弁"),
                         ("a", "→"), ("i", "minecraft:chest", "いつもの箱(満杯)")],
                        [None, ("a", "↓"), None, None],
                        [None, ("i", "minecraft:chest", "予備の箱"), None, None],
                    ],
                },
                "io": {
                    "in": [("minecraft:cobblestone", "丸石")],
                    "out": [("minecraft:cobblestone", "正面が空いていれば正面へ"),
                            ("minecraft:cobblestone", "満杯なら横・上下へ")],
                },
                "steps": [
                    "いつもの行き先の<b>手前</b>に溢れ防止弁を置きます。",
                    "横(または上下)に、あふれた分を受ける箱を置きます。",
                    "設定はいりません。正面が満杯のときだけ、自動で横へ逃がします。",
                ],
            },
            {
                "title": "⑥ 数える・残りを見る・設定を配る",
                "goal": "うまく動いているか確かめる道具と、同じ設定を何台にも配る道具です。",
                "diagram": {
                    "caption": "左: 通った数を数える / 中: 残量をレッドストーンに出す / 右: 設定を写して貼る",
                    "rows": [
                        [
                            ("i", "sorakaze_deco:item_counter", "アイテム計数器"),
                            ("a", "→"),
                            ("i", "minecraft:comparator", "64 個で 1 段"),
                            ("n", "　"),
                            ("i", "minecraft:chest", "見たい箱"),
                            ("a", "←"),
                            ("i", "sorakaze_deco:stock_indicator", "在庫表示ランプ"),
                        ],
                        [
                            None, None, None, None, None, None, ("a", "↓"),
                        ],
                        [
                            ("i", "sorakaze_deco:item_collector", "アイテム集荷器"),
                            ("a", "→"),
                            ("i", "minecraft:chest", "落ちものを拾って入れる"),
                            ("n", "　"),
                            ("i", "sorakaze_deco:filter_card", "フィルター記憶カード"),
                            None,
                            ("i", "minecraft:redstone_lamp", "ランプが光る"),
                        ],
                    ],
                },
                "io": {
                    "in": [("minecraft:wheat", "落ちている小麦")],
                    "out": [("minecraft:wheat", "箱の中へ")],
                },
                "steps": [
                    "<b>アイテム計数器</b>は流れの途中に置きます。素通しさせながら数を数え、"
                    "コンパレーターへ出します(右クリックで合計、スニーク+右クリックで 0 に戻る)。",
                    "<b>在庫表示ランプ</b>はアイテムを動かしません。"
                    "正面の箱の残りを読んで、しきい値を超えると光り、同じ値をコンパレーターへ出します。"
                    "遠くの倉庫の残量を配線に繋げます。",
                    "<b>アイテム集荷器</b>は、まわりに落ちているアイテムを吸い込んで正面の箱へ入れます。"
                    "畑の落し物拾いに使います。",
                    "<b>フィルター記憶カード</b>は、空のカードで仕分けフィルターを右クリックすると"
                    "設定を<b>写し</b>、中身のあるカードで右クリックすると<b>貼り</b>ます。"
                    "同じ設定を何台にも配れます(空中で右クリックすると消せます)。",
                ],
            },
        ],
    },
    # =======================================================================
    # 電力(v1.8.2 で追加)
    # =======================================================================
    # ⚠ **この節の数字はひとつも手で書いていない。**すべて `{fact}` で、
    #    実装(PowerConfig / PowerSpec / Voltage / AmpRating / FuelQuality /
    #    RenewableKind / 各 block タグ / SurvivalConfig)から読んだ値が入る。
    #    実装が変われば本文が変わり、実装から消えれば生成が止まる。
    {
        "id": "power",
        "icon": "sorakaze_power:breaker",
        "tab": "使い方",
        "title": "電気のつなぎかた",
        "lede": "電気は<b>「作る → 送る → 配る → 使う」</b>の 4 つだけです。"
                "まずは①の図のとおりに 4 個並べてみてください。"
                "分電盤は<b>置くだけで設定が済みます</b>(設定画面を開く必要はありません)。"
                "⚠ この MOD を入れると<b>レッドストーンにも電気が要ります</b> — ⑩を必ず読んでください。",
        "sections": [
            {
                "title": "① 電気のながれ(まずこれだけ)",
                "goal": "発電機・ケーブル・分電盤・機器の 4 つ。これが電気の全部です。",
                "diagram": {
                    "caption": "燃料 → 発電機 → ケーブル → 蓄電池 → エネルギーセル → 分電盤(燃料スロット)→ ケーブル → 機器"
                               "(横に長いので、指やマウスで横へずらせます)",
                    "rows": [
                        [
                            ("i", "minecraft:coal", "燃料を入れる"),
                            ("a", "→"),
                            ("i", "sorakaze_power:generator_controller", "発電機"),
                            ("a", "→"),
                            ("i", "sorakaze_power:cable", "ケーブル"),
                            ("a", "→"),
                            ("i", "sorakaze_power:battery", "蓄電池"),
                            ("a", "→"),
                            ("i", "sorakaze_guns:energy_cell", "エネルギーセル"),
                            ("a", "→"),
                            ("i", "sorakaze_power:breaker", "分電盤"),
                            ("a", "→"),
                            ("i", "sorakaze_power:cable", "ケーブル"),
                            ("a", "→"),
                            ("i", "sorakaze_deco:atm", "機器"),
                        ],
                        [
                            ("n", "▼ 使わない"),
                            None,
                            ("i", "sorakaze_power:machine_casing", "機械の筐体"),
                            None,
                            ("i", "sorakaze_power:reactor_casing", "原子炉の遮蔽ブロック"),
                            None,
                            ("n", "ただの飾りです"),
                            None, None, None, None, None, None,
                        ],
                    ],
                },
                "io": {
                    "in": [("minecraft:coal", "石炭(燃料)")],
                    "out": [("sorakaze_power:cable", "ケーブルが光ります"),
                            ("sorakaze_deco:atm", "機器が動きます")],
                },
                "steps": [
                    "<b>発電機</b>を置きます。アイテム 1 個を置くだけで、"
                    "{machine_size} の大きさの建物が自分で生えます(組み立ては要りません)。"
                    "せまい場所には置けないので、周りを空けてください。",
                    "発電機に<b>石炭を持って右クリック</b>で燃料を入れます。火が入ります。",
                    "発電機から<b>蓄電池</b>まで<b>ケーブル</b>をつなぎます。"
                    "発電機はどの面からでもつながります。"
                    "<b>⚠ 蓄電池を経由しない配線(発電機を直接ケーブルで分電盤につなぐだけ)では、電気は届きません。</b>",
                    "蓄電池に電気がたまると、自動で<b>エネルギーセル</b>ができます。"
                    "できたセルを取り出して(下からホッパーで自動化もできます。⑥を見てください)、"
                    "<b>分電盤の燃料スロット</b>に差し込みます。",
                    "分電盤から、動かしたい機器まで<b>ケーブル</b>をつなぎます。"
                    "<b>ここで設定はしません。</b>置いた時点で分電盤が系統・電圧・容量を自分で決めます。",
                    "ケーブルが<b>光ったら通電しています。</b>光らない場所には電気が届いていません。",
                ],
                "notes": [
                    "発電機は<b>電気を作るだけ</b>、蓄電池は<b>セルを作るだけ</b>、"
                    "分電盤は<b>セルを燃料にして配るだけ</b>です。どれか 1 つでも欠けると動きません。",
                    "うまくいかないときは、まず<b>ケーブルが光っているか</b>を目で追ってください。"
                    "光が途切れたところが原因の場所です。",
                    "<b>原子力発電所も同じしくみです。</b>以前は自分で作ったセルを直接ケーブルで"
                    "分電盤へ送っていましたが、いまは発電機と同じく<b>まず蓄電池へ出力を送り、"
                    "蓄電池がセルを作ります</b>(⑤を見てください)。"
                    "蓄電池が見つからないときだけ、原子炉は以前と同じやりかたで自分の中に少しだけセルをためて待ちます"
                    "(発電機にはこの仕組みが無いので、蓄電池が無いと発電機の電気はただ失われます)。",
                    "<b>「機械の筐体」と「原子炉の遮蔽ブロック」は、いまは組み立てに使いません。</b>"
                    "以前は機械を手で積む必要があったころの部品で、"
                    "いまは<b>ただの丈夫な飾りブロック</b>として残してあります"
                    "(前に建てた建物が消えないようにするためです)。買い足す必要はありません。",
                ],
            },
            {
                "title": "② ケーブルは {cable_kinds} 種類。どれを使う?",
                "goal": "選ぶ物差しは<b>2 つあります</b>。<b>太さ = 届く距離</b>、"
                        "<b>帯 = 高圧を載せられるか</b>。この 2 つは別々なので、"
                        "<b>「どれがいちばん偉い」という順番はありません</b>。",
                "diagram": {
                    "caption": "太いほど遠くへ届きます。継手に帯があるものだけが高圧を送れます"
                               "(既定値のとき)",
                    "rows": [
                        [
                            ("i", "sorakaze_power:cable", "普通のケーブル"),
                            ("n", "{volts_100}V で {cable_reach_100} ブロック"),
                            ("n", "{volts_200}V で {cable_reach_200} ブロック"),
                            ("n", "高圧は送れない"),
                        ],
                        [
                            ("i", "sorakaze_power:heavy_cable", "{heavy_name}"),
                            ("n", "{volts_100}V で {heavy_reach_100} ブロック"),
                            ("n", "{volts_200}V で {heavy_reach_200} ブロック"),
                            ("n", "高圧は送れない"),
                        ],
                        [
                            ("i", "sorakaze_power:insulated_cable", "絶縁ケーブル"),
                            ("n", "{volts_100}V で {ins_reach_100} ブロック"),
                            ("n", "{volts_200}V で {ins_reach_200} ブロック"),
                            ("n", "高圧を送れる"),
                        ],
                        [
                            ("i", "sorakaze_power:shielded_cable", "{best_name}"),
                            ("n", "{volts_100}V で {best_reach_100} ブロック"),
                            ("n", "{volts_200}V で {best_reach_200} ブロック"),
                            ("n", "高圧を送れる"),
                        ],
                    ],
                },
                "steps": [
                    "<b>まず普通のケーブルで引いてみてください。</b>光れば足りています。",
                    "途中で光が消えたら距離が足りていません。"
                    "<b>太いケーブルに替える</b>か、<b>電圧を上げる</b>(③)かのどちらかです。"
                    "普通のケーブルを 1 としたとき、届く距離は"
                    "絶縁ケーブルが <b>{ins_ratio} 倍</b>、"
                    "{heavy_name}が <b>{heavy_ratio} 倍</b>、"
                    "{best_name}が <b>{best_ratio} 倍</b>です。",
                    "<b>高圧({volts_high}V)だけは{high_tier}でないと送れません。</b>"
                    "普通のケーブルに高圧を設定すると、分電盤に「絶縁不足」と出て動きません"
                    "(黙って壊れたりはしません)。",
                ],
                "notes": [
                    "<b>⚠ {heavy_name}は絶縁ケーブルの「上位」ではありません。</b>"
                    "{heavy_name}のほうが導体は太い(= 低圧でより遠くへ届く)のに、"
                    "<b>高圧は載せられません</b>。逆に絶縁ケーブルは高圧を送れますが、"
                    "低圧での距離は{heavy_name}に負けます。"
                    "<b>両方が要るときだけ{best_name}を使ってください</b>"
                    "(いちばん高いので、それ以外の場面では買う必要がありません)。",
                    "<b>高圧に耐えるケーブルが要るのは、分電盤から変圧器までの区間だけです。</b>"
                    "変圧器から先は {secondary_volts}V に下がるので、"
                    "<b>そこから機器までは安い普通のケーブルで正解です</b>"
                    "(本物の電柱の上の変圧器と同じ考えかたです)。",
                    "1 台の分電盤がたどれるケーブルは <b>{max_nodes} 本まで</b>です。"
                    "それより広い拠点は、分電盤を 2 台に分けてください。",
                    "上の距離は「送る途中で失う電気が <b>{loss_budget_pct}%</b> になるところまで」"
                    "という決まりから出ています。そこから先はケーブルが光らず、機器も動きません。",
                ],
            },
            {
                "title": "③ 分電盤 — 系統・電圧・アンペア",
                "goal": "<b>電圧は「届く距離」を買います。アンペアは「同時に何台動かせるか」を買います。</b>"
                        "この 1 行が分電盤の全部です。",
                "diagram": {
                    "caption": "1 台の分電盤は {circuits} 系統。"
                               "ケーブルの枝ごとに自動で分かれます",
                    "rows": [
                        [
                            None,
                            ("i", "sorakaze_power:breaker", "分電盤"),
                            None, None, None,
                        ],
                        [
                            ("a", "←"), ("a", "↓"), ("a", "→"), None, None,
                        ],
                        [
                            ("i", "sorakaze_deco:atm", "系統 1"),
                            ("i", "sorakaze_guns:auto_turret", "系統 2"),
                            ("i", "sorakaze_power:air_conditioner", "系統 3"),
                            ("n", "…最大 {circuits} 系統"),
                            None,
                        ],
                    ],
                },
                "steps": [
                    "<b>ふだんは何もしなくて大丈夫です。</b>置いた時点で分電盤は"
                    "系統・名前・電圧・アンペアを自分で決めています。",
                    "<b>電圧は {voltage_steps} 段</b>({volts_100}V / {volts_200}V / 高圧 {volts_high}V)。"
                    "上げるほど遠くまで届きます — 損失は電圧の 2 乗に反比例するので、"
                    "電圧を 2 倍にすると距離はおよそ<b>4 倍</b>になります。",
                    "<b>アンペアは {amp_steps} の {amp_steps_count} 段</b>。"
                    "{volts_100}V の {amp_min} なら機器 {amp_min_devices_100} 台、"
                    "{volts_200}V の {amp_min} なら {amp_min_devices_200} 台が目安です"
                    "(機器 1 台 = {device_watts}W)。",
                    "容量を超えると<b>その系統だけが「遮断」されます</b>(他の系統は生きています)。"
                    "分電盤を開いてその行を<b>入れ直す</b>と復帰します。"
                    "同じことが続くなら、アンペアを上げるか(いちばん大きい段は {amp_max})、"
                    "機器を別の系統へ分けてください。",
                ],
                "notes": [
                    "<b>電圧を上げるとアンペアは下がります。</b>同じ機器でも "
                    "{volts_200}V にすれば電流は半分になり、遮断しにくくなります"
                    "(実際の電気工事と同じ理屈です)。",
                    "自動で決まるアンペアには余裕が入っています"
                    "(実際に使う電力が定格の {amp_headroom_pct}% までに収まる段を選びます)ので、"
                    "<b>置いた直後にいきなり落ちることはありません</b>。",
                    "分電盤の「主幹」を切ると<b>全系統がいっぺんに止まります</b>。工事のときに便利です。",
                ],
            },
            {
                "title": "④ 変圧器 — 遠いときだけ得をする",
                "goal": "高圧は遠くまで届きますが、<b>変圧器は何も使っていなくても電気を食べ続けます</b>。"
                        "だから短い配線ではかえって損です。",
                "diagram": {
                    "caption": "分電盤 →(高圧・絶縁)→ 変圧器 →({secondary_volts}V・普通のケーブル)→ 機器",
                    "rows": [[
                        ("i", "sorakaze_power:breaker", "分電盤(高圧)"),
                        ("a", "→"),
                        ("i", "sorakaze_power:insulated_cable", "絶縁ケーブル"),
                        ("a", "→"),
                        ("i", "sorakaze_power:transformer", "変圧器"),
                        ("a", "→"),
                        ("i", "sorakaze_power:cable", "普通のケーブル"),
                        ("a", "→"),
                        ("i", "sorakaze_deco:atm", "機器"),
                    ]],
                },
                "io": {
                    "in": [("sorakaze_power:insulated_cable", "高圧 {volts_high}V(絶縁が必須)")],
                    "out": [("sorakaze_power:cable", "{secondary_volts}V(安いケーブルでよい)")],
                },
                "steps": [
                    "<b>およそ {crossover} ブロックが分かれ目です。</b>"
                    "それより<b>短い</b>配線では {volts_100}V / {volts_200}V のほうが得、"
                    "<b>長い</b>配線では高圧のほうが得になります。",
                    "高圧にするときは、<b>機器の近くに変圧器</b>を置きます。"
                    "分電盤から変圧器までを<b>絶縁ケーブル</b>でつなぎます。",
                    "<b>変圧器から先は {secondary_volts}V に下がります。</b>"
                    "そこから機器までは<b>普通のケーブル</b>で構いません(そのほうが安いです)。",
                ],
                "notes": [
                    "変圧器を置き忘れて高圧にすると、分電盤に「変圧器なし」と出て動きません。",
                    "近くの拠点をつなぐだけなら<b>高圧は要りません</b>。"
                    "{volts_200}V で {cable_reach_200} ブロック届きます。",
                ],
            },
            {
                "title": "⑤ 燃料 — かまどで焼けるものは全部入ります",
                "goal": "何を入れても動きますが、<b>出る電気の量がまるで違います</b>。木はいちばん損です。",
                "diagram": {
                    "caption": "左ほど弱く、右ほど強い(1 tick あたりの出力 = 動かせる機器の数)",
                    "rows": [
                        [
                            ("i", "minecraft:oak_log", "木・板材"),
                            ("i", "minecraft:coal", "石炭・木炭"),
                            ("i", "minecraft:blaze_rod", "ブレイズロッド"),
                            ("i", "minecraft:lava_bucket", "溶岩バケツ"),
                            ("i", "sorakaze_guns:energy_cell", "エネルギーセル"),
                        ],
                        [
                            ("n", "{wood_units} 単位"),
                            ("n", "{coal_units} 単位"),
                            ("n", "{blaze_units} 単位"),
                            ("n", "{lava_units} 単位"),
                            ("n", "{cell_units} 単位"),
                        ],
                        [
                            ("n", "機器 {wood_devices} 台"),
                            ("n", "機器 {coal_devices} 台"),
                            ("n", "機器 {blaze_devices} 台"),
                            ("n", "機器 {lava_devices} 台"),
                            ("n", "機器 {cell_devices} 台"),
                        ],
                    ],
                },
                "io": {
                    "in": [("minecraft:coal", "石炭 1 個 = {coal_seconds} 秒"),
                           ("minecraft:charcoal", "木炭も木あつかいです"),
                           ("sorakaze_guns:energy_cell", "いちばん強い燃料")],
                    "out": [("sorakaze_power:cable", "電気")],
                },
                "steps": [
                    "燃料を<b>手に持って右クリック</b>で入れます。"
                    "発電機・原子力発電所・<b>分電盤</b>のどれにも入ります。",
                    "<b>木はやめたほうがいいです。</b>石炭の <b>{wood_ratio} 分の 1</b> の出力しか出ず、"
                    "しかも燃える時間も短いので、あっという間になくなります。",
                    "<b>エネルギーセルがいちばん強い燃料です</b>({cell_units} 単位 = 機器 {cell_devices} 台)。"
                    "<b>蓄電池</b>が、発電機・原子力発電所から届いた電気をためてセルを作ります(①を見てください)。"
                    "原子力発電所は、<b>蓄電池が見つからないときだけ</b>自分の中だけでセルを作る昔ながらの動きに"
                    "戻ります(1 個あたり約 {reactor_seconds} 秒、{reactor_buffer} 個たまると止まって"
                    "石炭を無駄にしません)。",
                    "<b>分電盤に直接セルを差す</b>こともできます。1 個で約 {cell_minutes} 分もちます"
                    "(たくさん電気を使っているほど早く減ります)。",
                ],
                "notes": [
                    "<b>分電盤で燃料を燃やすと、もちが {breaker_fuel_pct}% になります。</b>"
                    "非常用と考えてください。ちゃんと発電するなら発電機を建てるほうが得です。",
                    "石炭 1 個で <b>{coal_total} 単位</b>ぶんです。"
                    "機器 {coal_devices} 台を {coal_seconds} 秒動かせる計算になります。",
                    "セルは<b>燃料として燃やすと {cell_seconds} 秒</b>しかもちません"
                    "(分電盤に差して使うほうがずっと長もちします)。"
                    "原子力発電所が蓄電池なしで自分だけでセルを 1 個作るのに約 {reactor_seconds} 秒かかるので、"
                    "<b>セルを燃やしてセルを作っても増えません</b>"
                    "(蓄電池を使った場合の生産ペースは、つないだ発電機の出力によって変わります)。",
                ],
            },
            {
                "title": "⑥ ホッパーで燃料を自動で入れる",
                "goal": "毎回手で石炭を入れるのは大変です。ホッパーにつなげば自動になります。",
                "diagram": {
                    "caption": "上にホッパー = 入れる / 下にホッパー = 取り出す",
                    "rows": [
                        [None, ("i", "minecraft:chest", "石炭の箱"), None,
                         ("i", "minecraft:chest", "セルの箱")],
                        [None, ("a", "↓"), None, ("a", "↑")],
                        [None, ("i", "minecraft:hopper", "上から入れる"), None,
                         ("i", "minecraft:hopper", "下から出す")],
                        [None, ("a", "↓"), None, ("a", "↑")],
                        [None, ("i", "sorakaze_power:reactor_controller", "原子力発電所"),
                         ("a", "→"), ("n", "できたセル")],
                    ],
                },
                "io": {
                    "in": [("minecraft:coal", "石炭を上から")],
                    "out": [("sorakaze_guns:energy_cell", "セルを下から"),
                            ("minecraft:bucket", "溶岩バケツの空バケツも下から")],
                },
                "steps": [
                    "機械の<b>上か横</b>にホッパーを向けると、燃料が入ります。",
                    "機械の<b>下</b>にホッパーを置くと、できたエネルギーセルと"
                    "空バケツ(溶岩バケツを燃やしたとき)を取り出せます。",
                    "<b>{machine_size} のどのマスからでも構いません。</b>"
                    "建物のどこに当ててもホッパーは効きます。",
                    "暖炉と分電盤も同じです。暖炉は上と横から石炭を入れられます。",
                ],
                # ⚠ v1.8.4 でここは**まるごと書きかえた**。
                # v1.8.1〜v1.8.3 は「燃料を運ぶホッパーだけは例外で動く / それ以外は止まる」と
                # 書いていたが、**いまはどのホッパーも電気を要らない**(mixin ごと削除された)。
                # 例外の説明を残すと「では他のホッパーは止まるのか」と読めてしまうので消した。
                "notes": [
                    "<b>ホッパーに電気は要りません。</b>燃料を運ぶものも、そうでないものも、"
                    "いままでどおり動きます。",
                    "<b>v1.8.3 まではホッパーにも電気が要りました。</b>"
                    "そのせいで「燃料が届かない → 発電できない → ホッパーが動かない」という"
                    "抜け出せない状態になることがあったので、<b>やめました。</b>"
                    "止まっていたホッパーは、更新すると自分で動きだします。",
                ],
            },
            {
                "title": "⑦ 燃料の要らない発電({renewable_count} 種類)",
                "goal": "タダで発電できますが、<b>それぞれ条件があります</b>。"
                        "1 台では足りないので、並べて増やします。",
                "diagram": {
                    "caption": "条件を満たしていないと出力が落ちます / 止まります",
                    "rows": [
                        [
                            ("i", "sorakaze_power:solar_panel", "太陽光パネル"),
                            ("i", "sorakaze_power:wind_turbine", "風力発電機"),
                            ("i", "sorakaze_power:hydro_generator", "水流発電機"),
                        ],
                        [
                            ("n", "{solar_units} 単位(機器 {solar_devices} 台)"),
                            ("n", "{wind_units} 単位(機器 {wind_devices} 台)"),
                            ("n", "{hydro_units} 単位(機器 {hydro_devices} 台)"),
                        ],
                        [
                            ("n", "空が見えて、昼であること。夜は 0"),
                            ("n", "高いところ + 羽根の周りが開いていること"),
                            ("n", "流れている水に {hydro_faces} 面ふれていること"),
                        ],
                    ],
                },
                "io": {
                    "in": [("minecraft:water_bucket", "流れる水(水流発電機)")],
                    "out": [("sorakaze_power:cable", "燃料ゼロの電気")],
                },
                "steps": [
                    "どれも<b>ケーブルで分電盤につなぐ</b>だけです。燃料は要りません。",
                    "<b>太陽光パネル</b>は屋根の上に。空が見えないと発電しません。"
                    "<b>夜と雨は止まります。</b>",
                    "<b>風力発電機</b>は高い塔の上に。高さ Y{wind_base_y} 以下ではほとんど回らず、"
                    "Y{wind_full_y} で全力になります。羽根の周りをふさがないでください。"
                    "<b>夜も回ります。</b>",
                    "<b>水流発電機</b>は川の中に。<b>止まっている水では動きません</b>(流れている水が要ります)。"
                    "{hydro_faces} 面ふれていると全力です。昼も夜も一定です。",
                    "足りないときは<b>並べて増やしてください。</b>出力はそのまま足し算になります。",
                ],
                "notes": [
                    "<b>どれも石炭の発電機より弱いか、条件が厳しいかのどちらかです。</b>"
                    "太陽光は石炭の半分しか出ず、しかも 1 日の半分は 0 です。",
                    "素手で右クリックすると、いま何 % で発電しているか・止まっている理由が出ます。",
                ],
            },
            {
                "title": "⑧ ⚠ 発電機は部屋を暑くします(暖炉とエアコン)",
                "goal": "<b>動いている発電機は、その部屋を暑くします。</b>"
                        "台数が増えるほど暑くなり、放っておくと<b>体力が減ります。</b>"
                        "冷やす道具はエアコンだけです。",
                "diagram": {
                    "caption": "動いている機械 1 台ぶんの効果(止まっている機械は 0 °C です)",
                    "rows": [
                        [
                            ("i", "sorakaze_power:generator_controller", "発電機"),
                            ("i", "sorakaze_power:reactor_controller", "原子力発電所"),
                            ("i", "sorakaze_power:solar_panel", "太陽光・風力・水流"),
                            ("i", "sorakaze_power:air_conditioner", "エアコン"),
                        ],
                        [
                            ("n", "+{machine_heat_c}°C"),
                            ("n", "+{reactor_heat_c}°C"),
                            ("n", "+{renewable_heat_c}°C(出しません)"),
                            ("n", "−{aircon_c}°C"),
                        ],
                        [
                            ("n", "2 台で +{heat_2}°C"),
                            ("n", "4 台で +{heat_4}°C"),
                            ("n", "8 台で +{heat_8}°C"),
                            ("n", "エアコン 1 台 = 発電機 {machines_per_ac} 台ぶん"),
                        ],
                        [
                            ("i", "sorakaze_power:fireplace", "暖炉"),
                            ("n", "+{fireplace_c}°C"),
                            ("n", "寒さ対策 / 電気は要りません"),
                            ("n", "半径 {temp_radius} ブロック"),
                        ],
                    ],
                },
                "io": {
                    "in": [("sorakaze_power:generator_controller", "動かすと熱が出ます")],
                    "out": [("sorakaze_power:air_conditioner", "同じ部屋に置けば消えます")],
                },
                "steps": [
                    "<b>「その部屋」の空気がつながっている範囲で数えます。</b>"
                    "壁と閉じたドアで区切られていれば、向こう側の熱も冷房も届きません。"
                    "<b>だから機械室を分けて閉めるのがいちばん簡単な対策です。</b>",
                    "<b>エアコンは同じ部屋のどこに置いても同じだけ効きます</b>(距離は関係ありません)。"
                    "発電機のとなりに置く必要はありません。",
                    "必要なエアコンの数は<b>発電機 {machines_per_ac} 台につき 1 台</b>です。"
                    "発電機 4 台なら {ac_for_four} 台、8 台なら {ac_for_eight} 台に増やしてください。",
                    "<b>屋外では熱は {open_air_pct}% まで弱まります。</b>"
                    "どうしても冷やしきれないときは、屋根を外して露天にするのも手です。",
                    "<b>暖かくしたいときは暖炉です。</b>石炭を持って右クリックで入れるだけで"
                    "(上にホッパーでも入ります)、まわり半径 {temp_radius} ブロックが +{fireplace_c}°C になります。"
                    "電気は要りません。石炭 1 個で <b>{fireplace_seconds} 秒</b>もつので、"
                    "火が消えると暖まらなくなります。",
                ],
                "notes": [
                    "<b>{comfort_max_c}°C を超えると警告、{scorching_c}°C 以上で体力が減りはじめます。</b>"
                    "画面の温度計が赤くなったら、エアコンを増やすか発電機を止めてください。",
                    "<b>エアコンは冷やしすぎません。</b>{comfort_max_c}°C より下へは下げないので、"
                    "雪原に置いても凍えることはありません。",
                    "<b>エアコンには電気が要ります</b>(暖炉は要りません)。"
                    "ケーブルで分電盤につないでください。置くと {aircon_size} の大きさになります。"
                    "<b>スニーク + 右クリック</b>で入り切り、素手で右クリックすると状態が出ます。",
                    "熱は発電機 {machine_cap_count} 台(+{machine_cap_c}°C)で頭打ちになります。"
                    "それ以上増やしても暑くはなりませんが、<b>エアコンは 1 台ずつきちんと効きます。</b>",
                    "<b>暑くて困る心当たりがあるなら、</b>"
                    "<code>config/sorakaze_survival.json</code> の "
                    "<code>temperatureMachineHeatEnabled</code> を <code>false</code> にすれば"
                    "機械の熱だけを止められます(エアコンは止まりません)。",
                ],
            },
            {
                "title": "⑨ ⚠ 電気が要るようになったもの",
                "goal": "この MOD を入れると、<b>いままで動いていたものが止まります。</b>"
                        "配線すれば元どおり動きます。",
                "diagram": {
                    "caption": "この一覧の機器は、ケーブルで分電盤につながっていないと動きません",
                    "rows": [
                        [
                            ("i", "sorakaze_guns:auto_turret", "自動タレット"),
                            ("i", "sorakaze_guns:spider_turret", "クモ除けタレット"),
                            ("i", "sorakaze_guns:vex_turret", "ヴェックス除けタレット"),
                            ("i", "sorakaze_deco:atm", "ATM"),
                        ],
                        [
                            ("i", "sorakaze_deco:special_atm", "特別 ATM"),
                            ("i", "sorakaze_deco:security_camera", "防犯カメラ"),
                            ("i", "sorakaze_deco:teleport_elevator", "エレベーター"),
                            ("i", "sorakaze_deco:escalator", "エスカレーター"),
                        ],
                        [
                            ("i", "sorakaze_deco:auto_door", "自動ドア"),
                            ("i", "sorakaze_deco:auto_glass_door", "自動ガラスドア"),
                            ("i", "sorakaze_boss:enhanced_beacon", "強化ビーコン"),
                            ("i", "sorakaze_power:air_conditioner", "エアコン"),
                        ],
                    ],
                },
                "io": {
                    "in": [("sorakaze_power:cable", "ケーブルをつなぐ")],
                    "out": [("sorakaze_deco:auto_door", "また動くようになります")],
                },
                "steps": [
                    "動かなくなった機器の場所まで、分電盤から<b>ケーブル</b>を引いてください。",
                    "<b>ケーブルが光れば通電しています。</b>光っていなければ、"
                    "分電盤・発電機・燃料のどれかを確かめてください。",
                    "機器 1 台が使う電気は {device_watts}W です。"
                    "{branch_watts}W(= {devices_per_branch} 台)ごとに、必要な発電が 1 単位ずつ増えます。",
                ],
                "notes": [
                    "<b>強化ビーコン</b>だけは少し違い、となりのケーブルが光っているかどうかを見ます。",
                    "建材 MOD の機器(カメラ・エレベーター・エスカレーター・自動ドア・ATM)は、"
                    "<b>建材 MOD 側の設定で個別に電気を要らなくできます</b>"
                    "(<code>config/sorakaze_deco.json</code> の <code>…RequiresPower</code>)。",
                ],
            },
            {
                "title": "⑩ ⚠⚠ レッドストーンにも電気が要ります(いちばん大事)",
                "goal": "<b>ワールド中のレッドストーン回路が、電気の来ていない場所では止まります。</b>"
                        "いま動いている農場・駅・自動ドアも止まります。",
                "diagram": {
                    "caption": "左: 電気が要るもの({gated_count} 種) / "
                               "右: 電気が無くても必ず動くもの({exempt_count} 種)",
                    "rows": [
                        [
                            ("i", "minecraft:redstone", "粉"),
                            ("i", "minecraft:repeater", "反復装置"),
                            ("i", "minecraft:comparator", "比較装置"),
                            ("n", "　"),
                            ("i", "minecraft:lever", "レバー"),
                            ("i", "minecraft:tripwire_hook", "フック"),
                        ],
                        [
                            ("i", "minecraft:redstone_torch", "トーチ"),
                            ("i", "minecraft:redstone_block", "ブロック"),
                            ("n", "↑ 止まります"),
                            ("n", "　"),
                            ("i", "minecraft:daylight_detector", "日照センサー"),
                            ("i", "minecraft:observer", "オブザーバー"),
                        ],
                    ],
                },
                "io": {
                    "in": [("sorakaze_power:cable", "その場所にケーブルを引く")],
                    "out": [("minecraft:redstone", "また信号が出ます")],
                },
                "steps": [
                    "<b>直しかたは 1 つだけです。</b>その回路のある場所まで、"
                    "分電盤から<b>ケーブルを引いてください。</b>それだけで元どおり動きます。",
                    "<b>レバー・ボタン・感圧板・オブザーバー・日照センサーなどの「感知するもの」は、"
                    "電気が無くても必ず動きます</b>({exempt_count} 種類)。"
                    "電気が止まった拠点をゲームの中から直せなくなるのを防ぐためです。",
                    "<b>レッドストーンブロックは、電気の来ていない場所に置くと約 {decay_minutes} 分で崩れます。</b>"
                    "崩れたぶんは{decay_drops}(なくなりません)。"
                    "置くだけで電気がタダになってしまうのを防ぐためです。"
                    "<b>電気の来ている場所では崩れません</b>ので、配線済みの拠点では飾りに使えます。",
                    # ⚠ v1.8.4: 対象が 17 → {inverted_count} になった。数だけでなく
                    # **名前**も実装(タグ + 各 MOD の ja_jp.json)から読む。
                    "<b>「通電すると止まる」タイプの装置は、電気の無い場所では"
                    "止まったままになります。</b>ただし対象は "
                    "<b>{inverted_names}</b> の {inverted_count} つだけです。"
                    "廃棄装置が中身を消したり、レーザーやタレットが勝手に点いて"
                    "動物や村人を殺したりするのは<b>取り返しがつかない</b>ためです。",
                    # ⚠ 「{freed_count} 種類あった」とは書かない —— v1.8.3 の総数は 17 で、
                    #   14 はそのうち**外したぶん**である。総数は実装から読めない
                    #   (外した先のタグにしか残っていない)ので、**総数を主張しない**書き方にする。
                    "<b>v1.8.3 では、これにさらに {freed_count} 種類が入っていました。</b>"
                    "仕分け機・コンベア・信号機・列車自動停止ブロックなどが"
                    "「電気が無いと動かない」状態になっていたので、"
                    "<b>ぜんぶ対象から外しました。</b>いまは電気が無くても動きます"
                    "(止まっていたものは、更新すると自分で動きだします)。",
                ],
                "notes": [
                    "<b>全部いままでどおりに戻す方法があります。</b>"
                    "<code>config/sorakaze_power.json</code> の "
                    "<code>redstoneRequiresPower</code> を <code>false</code> にしてください。"
                    "レッドストーンはこの MOD が無かったときと同じに戻ります"
                    "(切りかえたあとサーバーを再起動してください)。",
                    "<b>電気のしくみそのものを全部止めたいとき</b>は、同じファイルの "
                    "<code>powerEnabled</code> を <code>false</code> にします。"
                    "機器もレッドストーンも電気を要らなくなり、置いたブロックは消えません。",
                    # ⚠ v1.8.4: ここには「ホッパーも止まります(hoppersRequirePower で切れます)」
                    # と書いてあった。**どちらも嘘になった** —— ホッパーは対象から外れ、
                    # そのつまみは config ごと消えた。消えたつまみを案内すると、
                    # 所有者は `sorakaze_power.json` に無い行を探すことになる。
                    "<b>ホッパー(バニラのもの)は対象ではありません。</b>"
                    "電気が無くても、いままでどおり動きます。",
                ],
            },
            {
                "title": "⑪ LED パネル照明 — 電気で光る、いちばん明るい灯り",
                "goal": "光量は <b>{led_light}</b>(バニラで出せる最大)。"
                        "<b>薄い板</b>なので天井に貼っても頭がつかえません。",
                "diagram": {
                    "caption": "厚さは {led_thickness_px}/16 ブロック。"
                               "面ならどこにでも貼れます(床・壁・天井)",
                    "rows": [
                        [
                            ("i", "sorakaze_power:cable", "電気が来ている"),
                            ("n", "→"),
                            ("i", "sorakaze_power:led_panel", "光量 {led_light}"),
                            ("n", "→"),
                            ("i", "minecraft:torch", "たいまつより広く明るい"),
                        ],
                    ],
                },
                "io": {
                    "in": [("sorakaze_power:cable", "ケーブルをつなぐ")],
                    "out": [("sorakaze_power:led_panel", "光量 {led_light} で点きます")],
                },
                "steps": [
                    "貼りたい面を右クリックで置いてください。<b>向きは貼った面で決まります。</b>",
                    "<b>ケーブルで分電盤につないでください。</b>電気が来ていないと点きません"
                    "(暗いままなのは壊れているのではなく、電気が来ていないからです)。",
                    "<b>すき間なく並べると、明るい範囲がさらに広がります。</b>"
                    "どれだけ広がるかは<b>アイテムの説明(持ったときに出る文)</b>に"
                    "実測値が書いてあります(3×3・5×5・7×7 のぶん)。",
                ],
                "notes": [
                    "<b>停電すると消えます。</b>湧きつぶしをこれだけに頼っていると、"
                    "燃料が切れた夜に拠点の中で湧きます。"
                    "<b>大事な場所にはたいまつも残しておいてください。</b>",
                    "水に沈めても使えます(水没させても消えません)。",
                ],
            },
            {
                # V2 §9.2/§10(2026-08-17 に出荷)。**空気清浄機を足したら、
                # ここに書かないと生成が止まる**(検査⑤「電力 MOD のカードが全部
                # どれかの図に出ていること」)。実際 2026-08-17 の再生成はここで止まった。
                "title": "⑫ ⚠ 原子力発電所は空気を汚します(空気清浄機)",
                "goal": "<b>動いている原子力発電所は、まわりの空気を汚します。</b>"
                        "汚れた空気の中に立っていると、遅くなり・弱くなり・最後は毒を受けます。"
                        "消す道具は<b>空気清浄機</b>だけです。",
                "diagram": {
                    "caption": "汚染度は 0 〜 {pollution_max}。{pollution_light} 未満なら何も起きません"
                               "(原子力発電所を止めれば、時間とともに自分で下がります)",
                    "rows": [
                        [
                            ("i", "sorakaze_power:reactor_controller", "原子力発電所"),
                            ("a", "→"),
                            ("n", "半径 {pollution_radius} ブロックが汚れる"),
                            ("a", "→"),
                            ("i", "sorakaze_power:air_purifier", "空気清浄機"),
                            ("a", "→"),
                            ("n", "半径 {purifier_radius} ブロックが {purifier_seconds} 秒で安全に"),
                        ],
                        [
                            ("n", "{pollution_light} 以上"),
                            ("n", "{pollution_heavy} 以上"),
                            ("n", "{pollution_severe} 以上"),
                            None, None, None, None,
                        ],
                        [
                            ("n", "移動速度低下 I"),
                            ("n", "+ 弱体化 I"),
                            ("n", "+ 毒 I"),
                            None, None, None, None,
                        ],
                    ],
                },
                "io": {
                    "in": [("sorakaze_power:reactor_controller", "動かすと空気が汚れます")],
                    "out": [("sorakaze_power:air_purifier", "通電しているあいだ消し続けます")],
                },
                "steps": [
                    "<b>汚れるのは原子力発電所だけです。</b>石炭の発電機・太陽光・風力・水流は"
                    "空気を汚しません(<b>暑くはします</b> —— ⑧を見てください)。",
                    "<b>空気清浄機を置いて、ケーブルで分電盤につないでください。</b>"
                    "ふつうの機器と同じで、<b>電気が来ていないと何もしません。</b>",
                    "1 台で<b>半径 {purifier_radius} ブロック</b>を"
                    "<b>{purifier_seconds} 秒</b>で安全なところまで下げます。"
                    "広い拠点は<b>並べて増やしてください</b> —— 重なった所は効き目が足し算になります。",
                    "素手で右クリックすると、<b>いまここの汚染度</b>と、"
                    "電気が来ているかどうかが出ます。数字が {pollution_light} 未満なら安全です。",
                ],
                "notes": [
                    "<b>いちばん重い段でも毒までです。</b>毒は体力を 1 未満にしないので、"
                    "どれだけ濃くても<b>歩いて出れば必ず助かります</b>。"
                    "効果は域外に出れば数秒で切れます(画面のアイコンで分かります)。",
                    "<b>清浄機が無くても、原子力発電所を止めれば汚染は時間で 0 に戻ります。</b>"
                    "上がりっぱなしにはなりません。清浄機はその減りを局所的に速くする道具です。",
                    "<b>屋内・屋外の区別はありません</b>(気温と違うところです)。"
                    "壁で囲っても汚れは入ってきます —— 距離だけが効きます。",
                    "<b>丸ごと止めたいときは</b> <code>config/sorakaze_power.json</code> の "
                    "<code>pollution.enabled</code> を <code>false</code> にしてください。"
                    "半径や秒数も同じところで変えられます(変えると上の数字も一緒に変わります)。",
                ],
            },
        ],
    },
]


# ===========================================================================
# ページの雛形(Minecraft レシピブック風 UI)
# ===========================================================================
# f-string ではなく @@TOKEN@@ 置換で埋める(CSS/JS の { } を全部二重化する事故を防ぐ)。
# 置換漏れは main() 末尾の残存トークン検査で必ず落ちる。
TEMPLATE = r"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Glimpse Alpha レシピ早見表</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0;}
  [hidden]{display:none !important;}
  html{height:100%;}
  body{
    height:100vh;height:100dvh;display:flex;flex-direction:column;overflow:hidden;
    font-family:"Hiragino Kaku Gothic ProN","Hiragino Sans","Yu Gothic","Meiryo",sans-serif;
    @@BODY_BG@@
    color:#fff;
  }
  img{image-rendering:pixelated;}
  /* ---- 見出し(暗い背景に MC 風の影付き白文字)---- */
  .top{flex:none;text-align:center;padding:10px 12px 7px;text-shadow:2px 2px 0 rgba(0,0,0,.65);}
  .top h1{font-size:clamp(17px,2.6vw,23px);letter-spacing:.05em;}
  .top .sub{font-size:12px;color:#e0e0e0;margin-top:3px;text-shadow:1px 1px 0 rgba(0,0,0,.65);}
  /* ---- 本(パネル)---- */
  .bookwrap{flex:1 1 auto;min-height:0;display:flex;justify-content:center;padding:0 10px;}
  .book{width:100%;max-width:1150px;min-height:0;display:flex;flex-direction:column;}
  .tabs{flex:none;display:flex;flex-wrap:wrap;gap:3px;align-items:flex-end;padding:0 8px;position:relative;z-index:2;}
  .tab{
    appearance:none;-webkit-appearance:none;font:inherit;cursor:pointer;
    display:flex;align-items:center;gap:6px;padding:6px 9px;
    background:#8f8f8f;color:#2f2f2f;
    border:3px solid;border-color:#dcdcdc #4a4a4a #4a4a4a #dcdcdc;border-bottom:0;
  }
  .tab img{width:22px;height:22px;display:block;}
  .tab-label{font-size:13px;font-weight:bold;}
  .tab-count{font-size:11px;color:#3d3d3d;background:rgba(0,0,0,.13);padding:0 5px;border-radius:7px;}
  .tab[aria-selected="true"]{
    background:#C6C6C6;position:relative;z-index:3;margin-bottom:-4px;padding-bottom:12px;
    border-color:#fdfdfd #3e3e3e transparent #fdfdfd;
  }
  .tab.dim{opacity:.4;}
  .tab:focus-visible{outline:2px solid #fff;}
  .panel{
    flex:1 1 auto;min-height:0;display:flex;flex-direction:column;
    background:#C6C6C6;
    border:4px solid;border-color:#fdfdfd #3e3e3e #3e3e3e #fdfdfd;
    box-shadow:0 0 0 2px rgba(0,0,0,.55),0 14px 34px rgba(0,0,0,.55);
    position:relative;z-index:1;
  }
  .phead{flex:none;padding:10px 12px 8px;border-bottom:2px solid #adadad;}
  .field{display:flex;align-items:center;gap:8px;background:#000;
    border:2px solid;border-color:#373737 #fff #fff #373737;padding:5px 10px;}
  .field svg{flex:0 0 auto;}
  .field input{flex:1 1 auto;min-width:0;background:transparent;border:0;outline:0;
    color:#fff;font:inherit;font-size:16px;}
  .field input::placeholder{color:#7c7c7c;}
  .field input::-webkit-search-cancel-button{display:none;}
  #clear{flex:none;width:28px;height:28px;padding:0;line-height:1;font-size:15px;visibility:hidden;}
  .searchrow{display:flex;gap:8px;align-items:stretch;}
  .searchrow .field{flex:1 1 auto;min-width:0;}
  #mute{flex:none;display:flex;align-items:center;gap:6px;padding:0 9px;line-height:1;}
  #mute-ico{font-size:16px;}
  .mute-label{font-size:12px;font-weight:bold;white-space:nowrap;}
  #mute[aria-pressed="true"]{opacity:.8;}
  .status{margin-top:7px;font-size:12.5px;color:#3F3F3F;min-height:1.3em;}
  .status b{color:#17307f;}
  .hint{color:#6a6a6a;font-size:11.5px;}
  /* ---- スロットグリッド ---- */
  .bookbody{flex:1 1 auto;min-height:0;overflow-y:auto;overflow-x:hidden;padding:0 8px 12px;}
  .bookbody::-webkit-scrollbar{width:14px;}
  .bookbody::-webkit-scrollbar-track{background:#000;border:1px solid #3e3e3e;}
  .bookbody::-webkit-scrollbar-thumb{background:#8b8b8b;border:2px solid #000;
    box-shadow:inset 2px 2px 0 #c5c5c5,inset -2px -2px 0 #555;}
  .cat-head{position:sticky;top:0;z-index:4;display:flex;align-items:center;gap:8px;
    padding:9px 4px 7px;background:#C6C6C6;color:#3F3F3F;font-weight:bold;font-size:14.5px;
    box-shadow:0 2px 0 rgba(0,0,0,.08);}
  .cat-head img{width:20px;height:20px;}
  .cat-count{font-weight:normal;font-size:12px;color:#5b5b5b;}
  .slotgrid{display:flex;flex-wrap:wrap;gap:2px;padding:2px 2px 10px;}
  .slot{width:40px;height:40px;flex:none;position:relative;cursor:pointer;padding:0;
    appearance:none;-webkit-appearance:none;border:2px solid;border-color:#373737 #fff #fff #373737;
    background:#8B8B8B;}
  .slot img{display:block;width:32px;height:32px;margin:2px;pointer-events:none;}
  .slot:hover::after,.slot:focus-visible::after{content:"";position:absolute;inset:0;
    background:rgba(255,255,255,.45);pointer-events:none;}
  .slot:focus-visible{outline:2px solid #fff;z-index:1;}
  .missing{color:#ff6a5e;font-weight:bold;display:flex;align-items:center;justify-content:center;
    width:100%;height:100%;font-size:14px;}
  #noresult{margin:26px auto;max-width:430px;text-align:center;padding:16px 18px;
    color:#ff8d80;font-size:13.5px;line-height:1.8;border:2px solid transparent;
    background:linear-gradient(rgba(16,0,16,.94),rgba(16,0,16,.94)) padding-box,
               linear-gradient(rgba(255,85,85,.6),rgba(127,20,20,.6)) border-box;}
  #noresult b{color:#fff;}
  /* ---- 「使い方」タブ(v1.8.1)----
     カードの一覧とは別の中身なので、#sections と入れかえて表示する。
     図は画像を焼かず、一覧と同じテクスチャ(TEX)を並べて組み立てる
     = 何枚並べてもファイルは太らない。 */
  /* ⚠ この面(.panel)の地色は <b>rgb(198,198,198) の明るい灰色</b>である。
     最初これを暗い面だと思って白い文字を置いたところ、実測コントラストが
     1.4:1(判読限界の 4.5:1 を大きく下回る)で、目標文にいたっては 1.15:1 だった。
     地の上に置く文字は暗く、絵を並べる箱は本当に暗くして中の文字を明るくする。 */
  #guide{padding:4px 2px 18px;color:#2b2b2b;font-size:13.5px;line-height:1.85;}
  .g-lede{max-width:760px;margin:6px 4px 18px;padding:11px 14px;font-size:13.5px;
    color:#232323;background:rgba(255,255,255,.52);
    border-left:4px solid #3f8c3f;border-radius:3px;}
  .g-sec{margin:0 0 26px;padding:0 0 20px;border-bottom:1px solid rgba(0,0,0,.18);}
  .g-sec:last-child{border-bottom:none;}
  .g-h{font-size:16px;font-weight:bold;color:#141414;margin:14px 2px 4px;}
  .g-goal{margin:0 2px 12px;color:#4d4d4d;}
  /* 置きかた図 — 中は暗い面。ドット絵は暗い地の上のほうが見分けやすい。 */
  .g-fig{display:inline-block;max-width:100%;overflow-x:auto;padding:12px 14px 10px;
    background:rgba(0,0,0,.72);border:2px solid rgba(0,0,0,.45);border-radius:4px;}
  .g-figcap{color:#cfcfcf;font-size:11.5px;margin:0 0 9px;}
  .g-row{display:flex;align-items:flex-start;gap:2px;}
  .g-cell{width:82px;min-height:64px;flex:none;display:flex;flex-direction:column;
    align-items:center;justify-content:flex-start;text-align:center;}
  .g-cell img{width:38px;height:38px;image-rendering:pixelated;}
  .g-cap{font-size:10.5px;line-height:1.35;color:#ececec;margin-top:3px;word-break:break-word;}
  .g-arrow{color:#7ee87e;font-size:22px;font-weight:bold;line-height:1;padding-top:9px;}
  .g-note-cell{font-size:10.5px;color:#cfcfcf;padding-top:12px;}
  /* 入る / 出る */
  .g-io{display:flex;flex-wrap:wrap;gap:10px;margin:14px 2px 0;}
  .g-iobox{flex:1 1 240px;min-width:0;padding:9px 12px;border-radius:4px;
    background:rgba(0,0,0,.70);border:1px solid rgba(0,0,0,.45);}
  .g-iohead{font-size:11.5px;font-weight:bold;letter-spacing:.04em;margin-bottom:6px;}
  .g-in .g-iohead{color:#8fc7ff;}
  .g-out .g-iohead{color:#9ee89e;}
  .g-chip{display:inline-flex;align-items:center;gap:5px;margin:3px 8px 3px 0;
    font-size:11.5px;color:#ececec;}
  .g-chip img{width:22px;height:22px;image-rendering:pixelated;}
  /* 手順 */
  .g-steps{margin:14px 0 0;padding-left:0;list-style:none;counter-reset:gstep;}
  .g-steps li{position:relative;margin:0 0 9px;padding-left:34px;counter-increment:gstep;}
  .g-steps li::before{content:counter(gstep);position:absolute;left:0;top:1px;
    width:22px;height:22px;border-radius:50%;background:#2f6b2f;color:#fff;
    font-size:12px;font-weight:bold;display:flex;align-items:center;justify-content:center;}
  /* ⚠ 手順の中の太字。地色 rgb(198,198,198) の上で **実測 4.5:1 以上** であること。
     v1.8.1 の #7a4a00 は実測 4.38:1 で、AA(4.5:1)をわずかに下回っていた
     (13.5px の太字は WCAG の「大きな文字」に当たらないので、4.5:1 が基準である)。
     #6b4000 は同じ色みのまま 5.21:1。**目分量で決めず、必ず測ってから変えること。** */
  .g-steps b{color:#6b4000;}
  .g-notes{margin:12px 0 0;padding:9px 12px;border-radius:4px;font-size:12.5px;
    color:#3d2f08;background:rgba(255,238,190,.80);border-left:4px solid #a8781a;}
  .g-notes div{margin:2px 0;}
  .g-notes b{color:#7a4a00;}
  @media (max-width:620px){
    .g-cell{width:64px;}
    .g-cell img{width:30px;height:30px;}
    .g-cap{font-size:9.5px;}
  }
  /* ---- ツールチップ(MC 風: 暗紫のふち)---- */
  .tip{position:fixed;left:0;top:0;z-index:90;pointer-events:none;max-width:330px;
    padding:6px 9px;font-size:13px;line-height:1.45;
    border:2px solid transparent;
    background:linear-gradient(rgba(16,0,16,.94),rgba(16,0,16,.94)) padding-box,
               linear-gradient(to bottom,rgba(80,0,255,.55),rgba(40,0,127,.55)) border-box;
    box-shadow:0 3px 10px rgba(0,0,0,.5);}
  .tip-ja{color:#fff;font-weight:bold;text-shadow:1px 1px 0 rgba(0,0,0,.8);}
  .tip-en{color:#a8a8a8;font-size:11.5px;}
  .tip-hint{font-size:11.5px;margin-top:2px;}
  /* ---- レシピのモーダル(クラフト台)---- */
  #ov{position:fixed;inset:0;z-index:60;background:rgba(0,0,0,.6);
    display:flex;align-items:center;justify-content:center;padding:14px;}
  .modal{width:min(470px,100%);max-height:92vh;max-height:92dvh;overflow-y:auto;background:#C6C6C6;
    border:4px solid;border-color:#fdfdfd #3e3e3e #3e3e3e #fdfdfd;
    box-shadow:0 0 0 2px rgba(0,0,0,.6),0 18px 44px rgba(0,0,0,.7);
    padding:13px 15px;color:#3F3F3F;}
  .m-head{display:flex;align-items:flex-start;gap:10px;}
  .m-icon{flex:none;width:44px;height:44px;background:#8B8B8B;border:2px solid;
    border-color:#373737 #fff #fff #373737;}
  .m-icon img{width:32px;height:32px;margin:4px;display:block;}
  .m-names{flex:1 1 auto;min-width:0;}
  .m-ja{font-size:16.5px;font-weight:bold;color:#2f2f2f;line-height:1.35;}
  .m-en{font-size:12px;color:#6a6a6a;margin-top:1px;}
  .m-cat{font-size:11px;color:#6a6a6a;margin-top:2px;}
  .m-close{flex:none;width:34px;height:34px;padding:0;font-size:16px;}
  .m-craftrow{display:flex;align-items:center;justify-content:center;gap:12px;margin:16px 0 8px;}
  .m-grid{display:grid;grid-template-columns:repeat(3,44px);grid-auto-rows:44px;gap:2px;flex:none;}
  .m-cell{width:44px;height:44px;background:#8B8B8B;border:2px solid;
    border-color:#373737 #fff #fff #373737;padding:0;position:relative;
    appearance:none;-webkit-appearance:none;font:inherit;}
  .m-cell img{display:block;width:32px;height:32px;margin:4px;pointer-events:none;}
  button.m-cell.link{cursor:pointer;}
  button.m-cell.link:hover::after,button.m-cell.link:focus-visible::after{
    content:"";position:absolute;inset:0;background:rgba(255,255,255,.4);pointer-events:none;}
  .m-arrow{flex:none;}
  .m-arrow img{display:block;width:52px;height:34px;}
  .m-result{flex:none;width:56px;height:56px;background:#8B8B8B;border:2px solid;
    border-color:#373737 #fff #fff #373737;position:relative;}
  .m-result img{display:block;width:48px;height:48px;margin:2px;}
  .m-count{position:absolute;right:2px;bottom:0;color:#fff;font-weight:bold;font-size:15px;
    text-shadow:1px 1px 0 #000;pointer-events:none;}
  .m-out{text-align:center;font-size:13px;color:#3F3F3F;margin-bottom:4px;}
  .m-how{margin:14px 2px 10px;padding:10px 12px;font-size:13px;line-height:1.75;color:#ffd75e;
    border:2px solid transparent;
    background:linear-gradient(rgba(16,0,16,.94),rgba(16,0,16,.94)) padding-box,
               linear-gradient(to bottom,rgba(255,170,0,.6),rgba(140,90,0,.6)) border-box;}
  .m-ings{margin-top:10px;border-top:2px solid #adadad;padding-top:8px;}
  .m-ings-h{font-size:12px;color:#5b5b5b;margin-bottom:4px;font-weight:bold;}
  .m-ing{display:flex;align-items:center;gap:8px;width:100%;padding:3px 2px;font:inherit;
    font-size:13px;color:#3F3F3F;background:none;border:0;text-align:left;}
  .m-ing img{width:24px;height:24px;flex:none;}
  button.m-ing.link{cursor:pointer;color:#17307f;}
  button.m-ing.link:hover span,button.m-ing.link:focus-visible span{text-decoration:underline;}
  .m-alts{margin-top:10px;font-size:12.5px;display:flex;gap:6px;align-items:center;flex-wrap:wrap;}
  .m-nav{margin-top:12px;display:flex;}
  .mcbtn{appearance:none;-webkit-appearance:none;font:inherit;cursor:pointer;color:#fff;
    background:#8b8b8b;border:2px solid;border-color:#cfcfcf #414141 #414141 #cfcfcf;
    text-shadow:1px 1px 0 rgba(0,0,0,.7);padding:4px 10px;font-size:13px;}
  .mcbtn:hover,.mcbtn:focus-visible{background:#8b95d8;border-color:#dfe3ff #2f3a70 #2f3a70 #dfe3ff;}
  .foot{flex:none;text-align:center;color:#c9c9c9;font-size:10.5px;padding:6px 10px 9px;
    text-shadow:1px 1px 0 rgba(0,0,0,.7);line-height:1.5;}
  @media (max-width:620px){
    .tab{padding:5px 7px;}
    .tab-label{display:none;}
    .mute-label{display:none;}
    #mute{padding:0;width:40px;justify-content:center;}
    .m-craftrow{gap:8px;}
    .m-grid{grid-template-columns:repeat(3,40px);grid-auto-rows:40px;}
    .m-cell{width:40px;height:40px;}
    .m-cell img{margin:2px;}
    .m-arrow img{width:26px;height:17px;}
    .m-result{width:48px;height:48px;}
    .m-result img{width:40px;height:40px;margin:2px;}
  }
  /* 印刷は補助扱い: いま表示中のスロット一覧だけでも切れずに出す。 */
  @media print{
    body{overflow:visible;height:auto;background:#fff;}
    .bookbody{overflow:visible;}
  }
</style>
</head>
<body>
<noscript><div style="background:#fff;color:#222;padding:20px;margin:20px;border-radius:8px;">
この早見表の表示には JavaScript が必要です(ファイルをそのままブラウザで開けば動きます。通信はいっさい行いません)。
</div></noscript>

<header class="top">
  <h1>Glimpse Alpha レシピ早見表</h1>
  <div class="sub">全 @@TOTAL@@ 種 - アイテムを<b>クリック</b>するとレシピ/入手方法がひらきます。カーソルを合わせると名前が出ます。</div>
</header>

<div class="bookwrap">
 <div class="book">
  <div class="tabs" id="tabs" role="tablist" aria-label="ジャンル"></div>
  <div class="panel">
    <div class="phead">
      <div class="searchrow">
        <label class="field" for="q">
          <svg viewBox="0 0 24 24" aria-hidden="true" width="16" height="16" fill="#8f8f8f"><path d="M15.5 14h-.79l-.28-.27A6.47 6.47 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/></svg>
          <input type="search" id="q" autocomplete="off" autocapitalize="off" spellcheck="false"
                 placeholder="なまえ・材料で検索(ひらがなでもOK 例: てつ / 電車 / どあ / iron)">
          <button type="button" id="clear" class="mcbtn" title="検索をやめる(Esc)" aria-label="検索をやめる">×</button>
        </label>
        <button type="button" id="mute" class="mcbtn"><span id="mute-ico">🔊</span><span class="mute-label" id="mute-label"></span></button>
      </div>
      <div class="status" id="status" aria-live="polite" role="status"></div>
    </div>
    <div class="bookbody" id="bookbody">
      <div id="sections"></div>
      <div id="guide" hidden></div>
      <div id="noresult" hidden><b>見つかりませんでした。</b><br>
      ちがう言葉で探してみてください(ひらがな・カタカナ・漢字・英語のどれでも探せます)。</div>
    </div>
  </div>
 </div>
</div>

<footer class="foot">Glimpse Alpha レシピ早見表 - tools/gen_recipe_sheet.py により自動生成(手動編集しないでください。レシピやテクスチャを変更したら、このスクリプトを再実行してください)。</footer>

<div class="tip" id="tip" hidden></div>
<div id="ov" hidden><div class="modal" id="modal" role="dialog" aria-modal="true" aria-labelledby="m-title"></div></div>

<script>
/* レシピブック UI。外部ライブラリ・通信は使わない(ファイルを直接ひらいても動く)。
   データはすべて下の 4 定数(生成時に埋め込み)。テクスチャは TEX に 1 回ずつだけ入り、
   何百回使われても参照は key 1 つ = ファイルが太らない。 */
var TEX=@@TEX@@;
var IT=@@IT@@;
var CARDS=@@CARDS@@;
var CATS=@@CATS@@;
var ALL_ICON=@@ALLICON@@;
var GUIDES=@@GUIDES@@;   /* 「使い方」タブ。空配列ならタブ自体を出さない */
(function () {
'use strict';
var ARROW_SRC='data:image/png;base64,@@ARROW@@';
function $(id){return document.getElementById(id);}
function jaOf(id){var e=IT[id];return e?e[0]:id;}
function enOf(id){var e=IT[id];return e?e[1]:'';}
function srcOf(id){var e=IT[id];return (e&&e[2])?('data:image/png;base64,'+TEX[e[2]]):null;}
function el(tag,cls,parent){var n=document.createElement(tag);if(cls)n.className=cls;
  if(parent)parent.appendChild(n);return n;}
function iconNode(id,size,withAlt){
  var s=srcOf(id);
  if(!s){var sp=document.createElement('span');sp.className='missing';sp.textContent='?';return sp;}
  var img=document.createElement('img');
  img.src=s;img.width=size;img.height=size;img.alt=withAlt?jaOf(id):'';
  img.loading='lazy';img.decoding='async';
  return img;
}
function escHtml(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;');}

/* ---------- クリック音(バニラの random/click.ogg 由来の WAV を同梱)----------
   ブラウザは操作(クリック)があるまで音を止めるので、AudioContext は最初の
   クリックの中で作り、suspended なら resume する。連打は毎回新しい
   BufferSource を作って鳴らす(1 つの要素を巻き戻さない)ので濁らない。
   40ms の最小間隔は同一操作の二重発火よけで、人間の連打(>80ms)は全部鳴る。 */
var SND='@@SND@@';                 /* base64 WAV。空文字なら生成時に取れなかった合図 */
var SND_IS_MC=@@SND_IS_MC@@;       /* true = 本物のマインクラフトのクリック音 */
var audio={ctx:null,buf:null,decoding:false,fallback:!SND,muted:false,plays:0,last:0};
try{audio.muted=(localStorage.getItem('recipeSheetSound')==='off');}catch(e){}
function audioCtx(){
  if(!audio.ctx){
    var AC=window.AudioContext||window.webkitAudioContext;
    if(!AC)return null;
    try{audio.ctx=new AC();}catch(e){return null;}
  }
  if(audio.ctx.state==='suspended'){try{audio.ctx.resume();}catch(e){}}
  return audio.ctx;
}
function sndBytes(){
  var s=atob(SND),a=new Uint8Array(s.length);
  for(var i=0;i<s.length;i++)a[i]=s.charCodeAt(i);
  return a.buffer;
}
function playBuf(){
  try{
    var src=audio.ctx.createBufferSource();
    src.buffer=audio.buf;
    var g=audio.ctx.createGain();
    g.gain.value=0.55;
    src.connect(g);g.connect(audio.ctx.destination);
    src.start(0);
    audio.plays++;
  }catch(e){}
}
function synthBlip(){
  /* click.ogg を使えない環境向けの短いブリップ(WebAudio 合成、0 バイト) */
  try{
    var t=audio.ctx.currentTime;
    var o=audio.ctx.createOscillator(),g=audio.ctx.createGain();
    o.type='square';
    o.frequency.setValueAtTime(2200,t);
    o.frequency.exponentialRampToValueAtTime(700,t+0.05);
    g.gain.setValueAtTime(0.16,t);
    g.gain.exponentialRampToValueAtTime(0.001,t+0.06);
    o.connect(g);g.connect(audio.ctx.destination);
    o.start(t);o.stop(t+0.07);
    audio.plays++;
  }catch(e){}
}
function clickSound(){
  if(audio.muted)return;
  var now=(window.performance&&performance.now)?performance.now():Date.now();
  if(now-audio.last<40)return;
  audio.last=now;
  if(!audioCtx())return;
  if(audio.buf){playBuf();return;}
  if(audio.fallback){synthBlip();return;}
  if(audio.decoding)return;        /* 初回デコード中の 2 発目だけは落とす(数 ms の窓) */
  audio.decoding=true;
  try{
    audio.ctx.decodeAudioData(sndBytes(),
      function(b){audio.buf=b;playBuf();},
      function(){audio.fallback=true;synthBlip();});
  }catch(e){audio.fallback=true;synthBlip();}
}
/* 鳴らす場所は 1 か所に集約: スロット・タブ・MC 風ボタン・材料リンクのどれかを
   押したら鳴る(本物のインベントリと同じく「押せる物は全部カチッと鳴る」)。
   ミュートボタン自身は、切り替え後にミュートなら鳴らさない(消した瞬間は静か)。 */
document.addEventListener('click',function(e){
  var t=(e.target&&e.target.closest)?e.target.closest('.slot,.tab,.mcbtn,[data-link]'):null;
  if(!t)return;
  clickSound();
});

/* 逆引き: このアイテムを作るカード(材料クリックでそのレシピへ飛ぶのに使う)。 */
var recipeByResult={};
for(var r0=0;r0<CARDS.length;r0++){
  var rid=CARDS[r0][1];
  (recipeByResult[rid]||(recipeByResult[rid]=[])).push(r0);
}

/* ---------- ブラウズグリッド(ジャンルごとの見出し + スロット)---------- */
var sectionsHost=$('sections');
var sections=[];
var slotOf=new Array(CARDS.length);
var builtSlots=0;
(function build(){
  var frag=document.createDocumentFragment();
  var curCat=-1,curGrid=null,curSlots=null;
  for(var i=0;i<CARDS.length;i++){
    var c=CARDS[i];
    if(c[0]!==curCat){
      curCat=c[0];
      var sec=el('section','cat-section',frag);
      sec.id='cat-'+CATS[curCat][0];
      var head=el('div','cat-head',sec);
      head.appendChild(iconNode(CATS[curCat][1],20,false));
      el('span','cat-name',head).textContent=CATS[curCat][0];
      var badge=el('span','cat-count',head);
      badge.textContent=CATS[curCat][2]+'件';
      curGrid=el('div','slotgrid',sec);
      curSlots=[];
      sections.push({cat:curCat,sec:sec,badge:badge,slots:curSlots,total:CATS[curCat][2]});
    }
    var b=document.createElement('button');
    b.type='button';b.className='slot';
    b.setAttribute('data-i',i);
    b.setAttribute('data-ti',c[1]);
    b.setAttribute('data-tk',c[4]?'h':'r');
    b.setAttribute('aria-label',jaOf(c[1]));
    b.appendChild(iconNode(c[1],32,false));
    curGrid.appendChild(b);
    curSlots.push({el:b,i:i});
    slotOf[i]=b;
    builtSlots++;
  }
  sectionsHost.appendChild(frag);
  if(builtSlots!==CARDS.length)console.error('slot/card count mismatch:',builtSlots,'vs',CARDS.length);
  window.__SHEET__={cards:CARDS.length,slots:builtSlots,tex:Object.keys(TEX).length,cats:CATS.length};
})();

/* ---------- ジャンルタブ ---------- */
var tabsHost=$('tabs');
var tabs=[];
var curTab=-1;
function makeTab(idx,iconId,label,total){
  var b=document.createElement('button');
  b.type='button';b.className='tab';b.setAttribute('role','tab');
  b.setAttribute('aria-selected',idx===curTab?'true':'false');
  b.title=label;
  b.appendChild(iconNode(iconId,22,false));
  el('span','tab-label',b).textContent=label;
  var ct=el('span','tab-count',b);
  ct.textContent=total;
  b.addEventListener('click',function(){setTab(idx);});
  tabsHost.appendChild(b);
  tabs.push({el:b,idx:idx,count:ct,total:total});
}
makeTab(-1,ALL_ICON,'すべて',CARDS.length);
for(var ci=0;ci<CATS.length;ci++)makeTab(ci,CATS[ci][1],CATS[ci][0],CATS[ci][2]);
/* 「使い方」タブ(idx=-2)。カードではなく手引きを出すので、ジャンルの並びの外側=最後に置く。 */
var GUIDE_TAB=-2;
if(GUIDES.length){
  var gsecs=0;
  for(var gi0=0;gi0<GUIDES.length;gi0++)gsecs+=GUIDES[gi0].sections.length;
  makeTab(GUIDE_TAB,GUIDES[0].icon,GUIDES[0].tab,gsecs);
}
function setTab(idx){
  curTab=idx;
  for(var i=0;i<tabs.length;i++)
    tabs[i].el.setAttribute('aria-selected',tabs[i].idx===idx?'true':'false');
  apply();
  $('bookbody').scrollTop=0;
}

/* ---------- 「使い方」タブの中身 ----------
   図は画像を焼かず、カード一覧と同じ TEX を並べて組み立てる。 */
var guideHost=$('guide');
function guideCell(c){
  var d=el('div','g-cell');
  if(!c)return d;                                   /* 空白 */
  if(c[0]==='a'){d.className='g-cell g-arrow';d.textContent=c[1];return d;}
  if(c[0]==='n'){d.className='g-cell g-note-cell';d.textContent=c[1];return d;}
  d.appendChild(iconNode(c[1],38,true));
  if(c[2])el('div','g-cap',d).textContent=c[2];
  return d;
}
function guideChip(parent,pair){
  var s=el('span','g-chip',parent);
  s.appendChild(iconNode(pair[0],22,true));
  var t=document.createElement('span');t.textContent=pair[1];s.appendChild(t);
}
function buildGuides(){
  var frag=document.createDocumentFragment();
  for(var g=0;g<GUIDES.length;g++){
    var G=GUIDES[g];
    var h=el('div','g-h',frag);h.style.fontSize='19px';h.textContent=G.title;
    if(G.lede)el('div','g-lede',frag).innerHTML=G.lede;
    for(var s=0;s<G.sections.length;s++){
      var S=G.sections[s],sec=el('div','g-sec',frag);
      el('div','g-h',sec).textContent=S.title;
      /* goal は節でいちばん大事な 1 行なので <b> を効かせる(lede・steps・notes と同じ)。
         図の caption / セルの文字は textContent のまま —— 生成側の検査がそこに
         タグを書かせない(main() の「HTML が素通しできない場所」の検査)。 */
      if(S.goal)el('div','g-goal',sec).innerHTML=S.goal;
      if(S.diagram){
        var fig=el('div','g-fig',sec);
        if(S.diagram.caption)el('div','g-figcap',fig).textContent=S.diagram.caption;
        for(var r=0;r<S.diagram.rows.length;r++){
          var row=el('div','g-row',fig),cells=S.diagram.rows[r];
          for(var c=0;c<cells.length;c++)row.appendChild(guideCell(cells[c]));
        }
      }
      if(S.io&&((S.io['in']&&S.io['in'].length)||(S.io.out&&S.io.out.length))){
        var io=el('div','g-io',sec);
        if(S.io['in']&&S.io['in'].length){
          var bi=el('div','g-iobox g-in',io);
          el('div','g-iohead',bi).textContent='入れるもの(例)';
          for(var i2=0;i2<S.io['in'].length;i2++)guideChip(bi,S.io['in'][i2]);
        }
        if(S.io.out&&S.io.out.length){
          var bo=el('div','g-iobox g-out',io);
          el('div','g-iohead',bo).textContent='出てくるもの';
          for(var o2=0;o2<S.io.out.length;o2++)guideChip(bo,S.io.out[o2]);
        }
      }
      if(S.steps&&S.steps.length){
        var ol=document.createElement('ol');ol.className='g-steps';
        for(var st=0;st<S.steps.length;st++){
          var li=document.createElement('li');li.innerHTML=S.steps[st];ol.appendChild(li);
        }
        sec.appendChild(ol);
      }
      if(S.notes&&S.notes.length){
        var nb=el('div','g-notes',sec);
        for(var n2=0;n2<S.notes.length;n2++){
          var nd=document.createElement('div');nd.innerHTML='※ '+S.notes[n2];nb.appendChild(nd);
        }
      }
    }
  }
  guideHost.appendChild(frag);
  window.__GUIDE__={topics:GUIDES.length,
                    imgs:guideHost.getElementsByTagName('img').length,
                    missing:guideHost.getElementsByClassName('missing').length};
}
if(GUIDES.length)buildGuides();

/* ---------- 検索 ---------- */
var input=$('q'),clearBtn=$('clear'),statusEl=$('status'),nores=$('noresult');
/* Python 側の search_norm() と同じ規則。ずれると検索が当たらなくなる。 */
function norm(s){
  s=s.toLowerCase();
  var out='';
  for(var i=0;i<s.length;i++){
    var c=s.charCodeAt(i);
    if(c>=0xFF01&&c<=0xFF5E)out+=String.fromCharCode(c-0xFEE0);
    else if(c===0x3000)out+=' ';
    else if(c>=0x30A1&&c<=0x30F6)out+=String.fromCharCode(c-0x60);
    else out+=s.charAt(i);
  }
  return out;
}
var hitFlags=new Array(CARDS.length);
function apply(){
  /* 「使い方」タブはカードではないので、検索の対象にならない。
     一覧と入れかえて出し、タブの件数表示は素の数に戻す。 */
  if(curTab===GUIDE_TAB){
    sectionsHost.hidden=true;guideHost.hidden=false;nores.hidden=true;
    clearBtn.style.visibility=input.value?'visible':'hidden';
    for(var gt=0;gt<tabs.length;gt++){
      tabs[gt].el.classList.remove('dim');
      if(tabs[gt].count.textContent!==''+tabs[gt].total)tabs[gt].count.textContent=''+tabs[gt].total;
    }
    statusEl.innerHTML='<b>使い方</b>: 絵のとおりに置けば動きます '
      +'<span class="hint">(検索したいときは他のジャンルをえらんでください)</span>';
    return;
  }
  guideHost.hidden=true;sectionsHost.hidden=false;
  var raw=input.value;
  var q=norm(raw).replace(/^\s+|\s+$/g,'');
  var terms=q?q.split(/\s+/):[];
  var filtering=terms.length>0;
  clearBtn.style.visibility=filtering?'visible':'hidden';
  var perCat=[];
  for(var pi=0;pi<CATS.length;pi++)perCat[pi]=0;
  var overall=0;
  for(var i=0;i<CARDS.length;i++){
    var ok=true,s=CARDS[i][5];
    for(var t=0;t<terms.length;t++){
      if(s.indexOf(terms[t])===-1){ok=false;break;}
    }
    hitFlags[i]=ok;
    if(ok){perCat[CARDS[i][0]]++;overall++;}
  }
  var shown=0;
  for(var gi=0;gi<sections.length;gi++){
    var g=sections[gi];
    var tabOk=(curTab===-1||curTab===g.cat);
    var vis=0;
    for(var si=0;si<g.slots.length;si++){
      var sl=g.slots[si];
      var v=tabOk&&hitFlags[sl.i];
      if(sl.el.hidden===v)sl.el.hidden=!v;
      if(v)vis++;
    }
    shown+=vis;
    if(g.sec.hidden!==(vis===0))g.sec.hidden=(vis===0);
    var label=(filtering&&perCat[g.cat]!==g.total)?(perCat[g.cat]+'/'+g.total+'件'):(g.total+'件');
    if(g.badge.textContent!==label)g.badge.textContent=label;
  }
  for(var ti=0;ti<tabs.length;ti++){
    var tb=tabs[ti];
    var n=(tb.idx===-1)?overall:perCat[tb.idx];
    var lbl=filtering?(n+'/'+tb.total):(''+tb.total);
    if(tb.count.textContent!==lbl)tb.count.textContent=lbl;
    if(filtering&&n===0)tb.el.classList.add('dim');else tb.el.classList.remove('dim');
  }
  nores.hidden=!(filtering&&shown===0);
  if(!filtering){
    statusEl.innerHTML=(curTab===-1)
      ?('全 <b>'+CARDS.length+'</b> 件を表示中 <span class="hint">(ジャンルの中はあいうえお順)</span>')
      :('<b>'+escHtml(CATS[curTab][0])+'</b>: '+CATS[curTab][2]+' 件を表示中');
  }else{
    var extra=(curTab!==-1&&overall>shown)
      ?(' <span class="hint">(他のジャンルに '+(overall-shown)+' 件 → 「すべて」タブ)</span>'):'';
    statusEl.innerHTML='「'+escHtml(raw)+'」 → <b>'+shown+'</b> 件 / 全 '+CARDS.length+' 件'+extra;
  }
}
/* 「使い方」を見ているときに検索を打ちはじめたら、黙って無視せず一覧へ戻す。 */
input.addEventListener('input',function(){
  if(curTab===GUIDE_TAB&&input.value){setTab(-1);return;}
  apply();
});
clearBtn.addEventListener('click',function(){input.value='';apply();input.focus();});

/* ---------- レシピのモーダル ---------- */
var ov=$('ov'),modal=$('modal');
var histStack=[],curCard=null,lastTrigger=null;
sectionsHost.addEventListener('click',function(e){
  var b=(e.target&&e.target.closest)?e.target.closest('.slot'):null;
  if(!b||!sectionsHost.contains(b))return;
  lastTrigger=b;
  openCard(parseInt(b.getAttribute('data-i'),10),false);
});
function openCard(i,push){
  hideTip();
  if(push&&curCard!==null)histStack.push(curCard);
  if(!push)histStack=[];
  curCard=i;
  renderModal(i);
  ov.hidden=false;
  var cb=$('m-close');
  if(cb)cb.focus();
}
function closeModal(){
  ov.hidden=true;histStack=[];curCard=null;hideTip();
  if(lastTrigger&&lastTrigger.focus)lastTrigger.focus();
}
ov.addEventListener('click',function(e){if(e.target===ov)closeModal();});
document.addEventListener('keydown',function(e){
  var k=e.key||e.keyCode;
  if(k==='Escape'||k===27){
    if(!ov.hidden)closeModal();
    else if(input.value){input.value='';apply();}
  }
});
function linkTo(node,cardIdx){
  node.setAttribute('data-link',cardIdx);
}
function renderModal(i){
  hideTip();
  var c=CARDS[i],id=c[1];
  modal.innerHTML='';
  var head=el('div','m-head',modal);
  el('div','m-icon',head).appendChild(iconNode(id,32,true));
  var names=el('div','m-names',head);
  var ja=el('div','m-ja',names);ja.id='m-title';ja.textContent=jaOf(id);
  var enn=enOf(id);
  if(enn&&enn!==jaOf(id))el('div','m-en',names).textContent=enn;
  el('div','m-cat',names).textContent='ジャンル: '+CATS[c[0]][0];
  var close=document.createElement('button');
  close.type='button';close.id='m-close';close.className='mcbtn m-close';
  close.textContent='×';close.setAttribute('aria-label','とじる');
  close.addEventListener('click',closeModal);
  head.appendChild(close);

  if(c[4]){ /* クラフト不可(入手方法カード) */
    var row0=el('div','m-craftrow',modal);
    var res0=el('div','m-result',row0);
    res0.setAttribute('data-ti',id);res0.setAttribute('data-tk','n');
    res0.appendChild(iconNode(id,48,false));
    el('div','m-how',modal).textContent='入手方法: '+c[4];
  }else{
    var row=el('div','m-craftrow',modal);
    var grid=el('div','m-grid',row);
    for(var k=0;k<9;k++){
      var cid=c[2][k];
      if(!cid){el('div','m-cell empty',grid);continue;}
      var linkable=!!recipeByResult[cid];
      var cell=document.createElement(linkable?'button':'div');
      if(linkable){cell.type='button';linkTo(cell,recipeByResult[cid][0]);}
      cell.className='m-cell'+(linkable?' link':'');
      cell.setAttribute('data-ti',cid);
      cell.setAttribute('data-tk',linkable?'l':'i');
      if(linkable)cell.setAttribute('aria-label',jaOf(cid)+' のレシピを表示');
      cell.appendChild(iconNode(cid,32,!linkable));
      grid.appendChild(cell);
    }
    var ar=el('div','m-arrow',row);
    var aimg=document.createElement('img');
    aimg.src=ARROW_SRC;aimg.alt='→';
    ar.appendChild(aimg);
    var res=el('div','m-result',row);
    res.setAttribute('data-ti',id);res.setAttribute('data-tk','n');
    res.appendChild(iconNode(id,48,false));
    if(c[3]>1)el('span','m-count',res).textContent=c[3];
    el('div','m-out',modal).textContent='できあがり: '+jaOf(id)+(c[3]>1?(' ×'+c[3]):'');
    /* 材料一覧(同じ材料はまとめて数える) */
    var counts={},order=[];
    for(var k2=0;k2<9;k2++){
      var cid2=c[2][k2];
      if(!cid2)continue;
      if(!(cid2 in counts)){counts[cid2]=0;order.push(cid2);}
      counts[cid2]++;
    }
    if(order.length){
      var box=el('div','m-ings',modal);
      el('div','m-ings-h',box).textContent='必要な材料';
      for(var oi=0;oi<order.length;oi++){
        var iid=order[oi];
        var lk=!!recipeByResult[iid];
        var rowb=document.createElement(lk?'button':'div');
        if(lk){rowb.type='button';linkTo(rowb,recipeByResult[iid][0]);}
        rowb.className='m-ing'+(lk?' link':'');
        rowb.setAttribute('data-ti',iid);rowb.setAttribute('data-tk',lk?'l':'i');
        rowb.appendChild(iconNode(iid,24,false));
        el('span','',rowb).textContent=jaOf(iid)+' ×'+counts[iid];
        box.appendChild(rowb);
      }
    }
  }
  /* 同じアイテムを作る別レシピ(現データでは 1 アイテム 1 レシピだが、増えても隠れない) */
  var alts=recipeByResult[id]||[];
  if(alts.length>1){
    var altbox=el('div','m-alts',modal);
    el('span','',altbox).textContent='別レシピ:';
    for(var ai=0;ai<alts.length;ai++){
      if(alts[ai]===i)continue;
      (function(target,no){
        var ab=document.createElement('button');
        ab.type='button';ab.className='mcbtn';ab.textContent='レシピ'+no;
        ab.addEventListener('click',function(){openCard(target,true);});
        altbox.appendChild(ab);
      })(alts[ai],ai+1);
    }
  }
  if(histStack.length){
    var nav=el('div','m-nav',modal);
    var back=document.createElement('button');
    back.type='button';back.className='mcbtn';back.textContent='← 戻る';
    back.addEventListener('click',function(){
      var prev=histStack.pop();
      curCard=prev;
      renderModal(prev);
    });
    nav.appendChild(back);
  }
}
modal.addEventListener('click',function(e){
  var lk=(e.target&&e.target.closest)?e.target.closest('[data-link]'):null;
  if(lk&&modal.contains(lk))openCard(parseInt(lk.getAttribute('data-link'),10),true);
});

/* ---------- ツールチップ ---------- */
var tip=$('tip');
var tipFor=null;
function hintFor(kind){
  if(kind==='r')return['クリックでレシピを表示','#9aa5ff'];
  if(kind==='h')return['クリックで入手方法を表示','#ffc34d'];
  if(kind==='l')return['クリックでこの材料のレシピを表示','#9aa5ff'];
  return null;
}
function showTip(t,x,y){
  var id=t.getAttribute('data-ti');
  var kind=t.getAttribute('data-tk');
  tip.innerHTML='';
  el('div','tip-ja',tip).textContent=jaOf(id);
  var enn=enOf(id);
  if(enn&&enn!==jaOf(id))el('div','tip-en',tip).textContent=enn;
  var h=hintFor(kind);
  if(h){
    var l3=el('div','tip-hint',tip);
    l3.textContent=h[0];l3.style.color=h[1];
  }
  tip.hidden=false;
  moveTipXY(x,y);
}
function moveTipXY(x,y){
  var w=tip.offsetWidth,hh=tip.offsetHeight;
  var vw=window.innerWidth,vh=window.innerHeight;
  var nx=x+14,ny=y-hh-8;
  if(nx+w>vw-4)nx=x-w-14;
  if(nx<4)nx=4;
  if(ny<4)ny=y+18;
  if(ny+hh>vh-4)ny=vh-hh-4;
  tip.style.left=nx+'px';
  tip.style.top=ny+'px';
}
function hideTip(){tip.hidden=true;tipFor=null;}
document.addEventListener('mouseover',function(e){
  var t=(e.target&&e.target.closest)?e.target.closest('[data-ti]'):null;
  if(t!==tipFor){
    tipFor=t;
    if(t)showTip(t,e.clientX,e.clientY);else hideTip();
  }
});
document.addEventListener('mousemove',function(e){
  if(tipFor)moveTipXY(e.clientX,e.clientY);
});
window.addEventListener('blur',hideTip);
document.documentElement.addEventListener('mouseleave',hideTip);

/* ---------- クリック音のオン/オフ(choice は localStorage に保存)---------- */
var muteBtn=$('mute');
function syncMute(){
  /* 状態が読めるトグル: アイコン(🔊/🔇)+日本語の状態ラベル。
     title / aria-label は日本語+英語の併記(スクリーンリーダー・英語話者向け)。 */
  $('mute-ico').textContent=audio.muted?'🔇':'🔊';
  $('mute-label').textContent=audio.muted?'音:オフ':'音:オン';
  muteBtn.setAttribute('aria-pressed',audio.muted?'true':'false');
  var label=audio.muted
    ?'クリック音はオフです。押すとオンになります / Click sound is OFF - press to turn it on'
    :'クリック音はオンです。押すとオフになります / Click sound is ON - press to turn it off';
  muteBtn.title=label;
  muteBtn.setAttribute('aria-label',label);
}
muteBtn.addEventListener('click',function(){
  /* この要素のリスナーは document のリスナーより先に走るので、
     ここで反転しておけば「消した瞬間は静か・点けた瞬間はカチッ」になる。 */
  audio.muted=!audio.muted;
  try{localStorage.setItem('recipeSheetSound',audio.muted?'off':'on');}catch(e){}
  syncMute();
});
syncMute();
if(window.__SHEET__)window.__SHEET__.audio=function(){
  return {state:audio.ctx?audio.ctx.state:null,decoded:!!audio.buf,
          fallback:audio.fallback,plays:audio.plays,muted:audio.muted,isMc:SND_IS_MC};
};

apply();
})();
</script>
</body>
</html>
"""


def main():
    # ⚠ いちばん先に走らせる。ここを通らないと「1 つのモジュールが丸ごと無い」ことに
    #    誰も気づけない —— 出力は正常に見え、終了コードは 0 のままだからである。
    check_mods_roster()
    zf = vanilla_zip()
    lang_by_modid = {modid: load_lang(mod_dir, modid) for mod_dir, modid, _ in MODS}
    lang_en_by_modid = {modid: load_lang(mod_dir, modid, "en_us") for mod_dir, modid, _ in MODS}
    van_ja = load_vanilla_ja()
    van_en = load_vanilla_en(zf)
    reg = ItemRegistry(van_ja, van_en, lang_by_modid, lang_en_by_modid)

    cards = []       # dict: cat / id / cells(9 個の id or None) / count / how / s
    no_yomi = []     # 読みを組み立てられなかったカード名(黙って捨てずに報告する)
    for mod_dir, modid, mod_cat in MODS:
        recipe_dir = ROOT / "mods-src" / mod_dir / "src/main/resources/data" / modid / "recipe"
        for path in sorted(recipe_dir.glob("*.json")):
            parsed = parse_recipe(path)
            if parsed is None:
                continue
            result_id = parsed["result_id"]
            _result_ns, result_name = result_id.split(":", 1)
            ja, en, _tex = reg.register(result_id)
            cat = category_of(mod_cat, result_name)
            _, unknown = reading_of(ja)
            if unknown:
                no_yomi.append((cat, ja, "".join(sorted(set(unknown)))))
            tokens = cat_tokens(cat) + item_tokens(result_id, ja)
            for cell_id in parsed["cells"]:
                if not cell_id:
                    continue
                cja, cen, _ = reg.register(cell_id)
                tokens += item_tokens(cell_id, cja)
                tokens.append(cen)
            tokens.append(en)
            cards.append({"cat": cat, "id": result_id, "cells": parsed["cells"],
                          "count": parsed["count"], "how": None,
                          "s": search_blob(tokens)})

    # クラフト不可の特別入手アイテム(強化ビーコン等)+食料品 300 種は「入手方法」カード。
    for modid, item_name, how_to_get, cat in SPECIAL_ITEMS + load_food_specials():
        item_id = f"{modid}:{item_name}"
        ja, en, _tex = reg.register(item_id)
        _, unknown = reading_of(ja)
        if unknown:
            no_yomi.append((cat, ja, "".join(sorted(set(unknown)))))
        blob = search_blob(cat_tokens(cat) + item_tokens(item_id, ja) + [en, how_to_get])
        cards.append({"cat": cat, "id": item_id, "cells": None, "count": None,
                      "how": how_to_get, "s": blob})

    # V1.4.1: 「天空」を追加。<b>この一覧に無いカテゴリのカードは黙って捨てられる。</b>
    # MODS に足すだけでは早見表に出ない(実際に天空 MOD が丸ごと欠落した)ので、
    # MOD を増やしたら必ずここにも足すこと。
    cat_order = ["銃", "電車", "建材", "ドア", "乗り物", "ボス", "天空", "サバイバル", "電力",
                 "二相楽園"]
    missing = {c["cat"] for c in cards} - set(cat_order)
    if missing:
        raise SystemExit(
            f"ERROR: these categories would be silently dropped from the sheet: {sorted(missing)}. "
            f"Add them to cat_order.")

    # 並びは **あいうえお順(五十音順)**。ジャンル(カテゴリ)とその順番は cat_order のまま。
    # 生の文字列で sorted() するとコードポイント順(=漢字がでたらめな順)になるので、
    # 必ず gojuon_key() を通すこと。読めなかった文字はかなより後ろに回り、
    # さらに実行時に WARNING で名指しされる(黙って間違った順に混ざることはない)。
    ordered = []
    for cat in cat_order:
        ordered += sorted((c for c in cards if c["cat"] == cat),
                          key=lambda c: gojuon_key(reg.items[c["id"]][0]))

    # ジャンルタブ(アイコンは実在カードから。無ければ WARNING + 先頭カードで代用)。
    ids_by_cat = {}
    for c in ordered:
        ids_by_cat.setdefault(c["cat"], []).append(c["id"])
    cats_meta = []
    for cat in cat_order:
        if cat not in ids_by_cat:
            continue
        icon = CATEGORY_TAB_ICON.get(cat)
        if icon not in ids_by_cat[cat]:
            print(f"WARNING: tab icon {icon!r} is not a card of ジャンル「{cat}」 - "
                  f"falling back to the first card of that ジャンル")
            icon = ids_by_cat[cat][0]
        cats_meta.append([cat, icon, len(ids_by_cat[cat])])
    reg.register(ALL_TAB_ICON)   # 「すべて」タブの作業台アイコン

    # 整合性の自己点検(構築上ここで落ちることは無いはずだが、黙って欠けさせない)。
    for c in ordered:
        assert c["id"] in reg.items, c["id"]
        for cell_id in (c["cells"] or []):
            assert cell_id is None or cell_id in reg.items, cell_id

    # ---- 名前が解決できているか(v1.8.4 で新設)---------------------------
    #
    # lang に鍵が無いと `display_name()` は **生の id をそのまま名前にする**。
    # 読みの検査は ASCII をローマ字として読めてしまうので通り、
    # テクスチャも在るので ①〜④ も通る —— **どこにも引っかからずに
    # `missile_launcher` と書かれたカードが出る**。実際に 17 枚出ていた。
    # 詳しくは KNOWN_UNNAMED の注記を参照。
    unnamed = set()
    for item_id, (ja, en, _tex) in reg.items.items():
        ns, raw = item_id.split(":", 1)
        if ns == "minecraft":
            continue                      # バニラは公式 lang から引くので対象外
        if ja == raw or en == raw:        # display_name() の素通し = 名前が無い
            unnamed.add(item_id)
    regressions = sorted(unnamed - KNOWN_UNNAMED)
    if regressions:
        raise SystemExit(
            "ERROR: %d item(s) have no display name in ja_jp.json / en_us.json, so the sheet "
            "would show a raw id where a name belongs (and the game shows the raw translation "
            "key in hand): %s\n"
            "       Add the lang entries and rebuild that module, or - only if this is "
            "deliberate - add the id to KNOWN_UNNAMED with a note saying why."
            % (len(regressions), ", ".join(regressions)))
    fixed = sorted(KNOWN_UNNAMED - unnamed)
    if fixed:
        raise SystemExit(
            "ERROR: %d id(s) in KNOWN_UNNAMED now have a proper name - remove them from that "
            "list so it keeps telling the truth about what is still broken: %s"
            % (len(fixed), ", ".join(fixed)))
    if unnamed:
        print(f"unnamed items: {len(unnamed)} still show a raw id "
              f"(known gap, listed in KNOWN_UNNAMED - fix lang + rebuild to clear)")

    # ---- 「使い方」タブ(v1.8.1)------------------------------------------
    #
    # ⚠ ここの 3 つの検査は「黙って劣化しない」ためにある。
    # 手引きが参照する id が 1 つでも解決できないと、ページ上は「?」の四角が
    # 出るだけで生成は成功してしまう(§31.4 で 309 個のアイテムが黙って表から
    # 落ちていたのと、§37 で「?」カード 1 枚として現れたのと同じ形)。
    # ⓪ 先に `{fact}` を実装から読んだ値へ置きかえる。**以降はこの GUIDES_FILLED を使う。**
    #    未知の名前があればここで生成が止まる(fill_facts)。
    guides_filled = fill_facts(GUIDES)
    unused = sorted(set(POWER_FACTS) - USED_FACTS)
    if unused:
        raise SystemExit(
            "ERROR: %d value(s) are read out of the implementation for the 使い方 tab but are "
            "used by no guide - a dead reading looks maintained while it is not. Either use "
            "them or stop reading them: %s" % (len(unused), ", ".join(unused)))

    guide_ids = []
    for g in guides_filled:
        guide_ids.append(g["icon"])
        for sec in g["sections"]:
            for row in (sec.get("diagram") or {}).get("rows", []):
                for cell in row:
                    if cell and cell[0] == "i":
                        guide_ids.append(cell[1])
            for side in ("in", "out"):
                for pair in (sec.get("io") or {}).get(side, []):
                    guide_ids.append(pair[0])

    # ① 手引きが触れる id は、全部テクスチャつきで解決できること。
    broken = []
    for iid in dict.fromkeys(guide_ids):
        ja, en, tex = reg.register(iid)
        if not tex:
            broken.append(iid)
    if broken:
        raise SystemExit(
            "ERROR: the 使い方 tab references %d item(s) with no texture - they would render "
            "as a '?' box while the build still 'succeeded': %s" % (len(broken), ", ".join(broken)))

    # ② 自動仕分け一式が、早見表のカードとして実在すること(改名・綴り違いの検出)。
    card_ids = {c["id"] for c in ordered}
    missing_cards = [i for i in SORTING_KIT if i not in card_ids]
    if missing_cards:
        raise SystemExit(
            "ERROR: SORTING_KIT lists %d id(s) that are not cards in this sheet (renamed or "
            "misspelled?): %s" % (len(missing_cards), ", ".join(missing_cards)))

    # ③ 一式の全部が、どれかの図に出ていること(= 説明されていない部品が無い)。
    #    部品を増やして手引きに足し忘れたら、ここで生成が止まる。
    shown = set(guide_ids)
    undocumented = [i for i in SORTING_KIT if i not in shown]
    if undocumented:
        raise SystemExit(
            "ERROR: %d sorting part(s) never appear in any 使い方 diagram - the owner would have "
            "no way to learn what they do: %s" % (len(undocumented), ", ".join(undocumented)))

    # ④ 一式の 10 枚が、**互いに違う絵**で出ていること。
    #
    # これは v1.8.0 で実際に起きた失敗そのものを二度と通さないための検査である。
    # あのとき 9 枚のカードは同じ texture key(t140 = 共有の天面)を指していて、
    # 早見表の上では見分けが付かなかった。カードは 9 枚あるので枚数の検査は通り、
    # WARNING も出ず、**誰も気付けなかった**。
    kit_tex = {}
    for iid in SORTING_KIT:
        tex = reg.items[iid][2]
        kit_tex.setdefault(tex, []).append(iid)
    dupes = {t: ids for t, ids in kit_tex.items() if len(ids) > 1}
    if dupes:
        raise SystemExit(
            "ERROR: sorting parts share a picture in this sheet - the owner could not tell them "
            "apart on the page (this is the v1.8.0 defect): "
            + "; ".join("%s <- %s" % (t, ", ".join(ids)) for t, ids in dupes.items()))

    # ④.5 **HTML が素通しできない場所にタグを書いていないこと。**
    #
    # 描画側は場所によって innerHTML と textContent を使い分けている:
    #   innerHTML  … lede / goal / steps / notes(強調を効かせたい文章)
    #   textContent … 図の caption / セルの下の説明 / 文字だけのセル
    # 後者に <b> を書くと、**画面に「<b>」という 3 文字がそのまま出る**。
    # 生成は成功し、警告も出ず、ブラウザで見るまで分からない —— 実際に一度そうなった。
    text_only = []
    for g in guides_filled:
        for sec in g["sections"]:
            dia = sec.get("diagram") or {}
            if dia.get("caption"):
                text_only.append(("diagram caption", dia["caption"]))
            for row in dia.get("rows", []):
                for cell in row:
                    if cell and cell[0] == "n":
                        text_only.append(("text cell", cell[1]))
                    elif cell and cell[0] == "i" and len(cell) > 2 and cell[2]:
                        text_only.append(("icon caption", cell[2]))
            for side in ("in", "out"):
                for pair in (sec.get("io") or {}).get(side, []):
                    text_only.append(("io chip", pair[1]))
    tagged = [(where, s) for where, s in text_only if re.search(r"<[a-zA-Z/]", s)]
    if tagged:
        raise SystemExit(
            "ERROR: %d 使い方 string(s) contain HTML in a place the page renders as plain text - "
            "the markup would be shown to the owner as literal characters: %s"
            % (len(tagged), "; ".join("%s %r" % (w, s[:60]) for w, s in tagged)))

    # ⑤ 電力 MOD のカードが全部どれかの図に出ていること。
    #    **ブロックを増やして手引きに足し忘れたら、ここで生成が止まる。**
    #    (§39 で「MODS に足し忘れて 10 レシピが丸ごと落ちた」のと同じ穴を、手引き側で塞ぐ。)
    power_cards = sorted(i for i in card_ids if i.startswith("sorakaze_power:"))
    if not power_cards:
        raise SystemExit(
            "ERROR: this sheet has no sorakaze_power cards at all - the 電力 guide would be "
            "describing blocks that do not exist (an empty set makes every check below "
            "vacuously true, which is exactly the CLAUDE.md section 30.4 failure)")
    undoc_power = [i for i in power_cards if i not in shown]
    if undoc_power:
        raise SystemExit(
            "ERROR: %d 電力 block(s) never appear in any 使い方 diagram - the owner would have "
            "no way to learn what they do: %s" % (len(undoc_power), ", ".join(undoc_power)))

    # ⑥ 「電気が要る機器」の一覧が、タグと 1 個ずれても止まること。
    #    出典は data の block タグなので、相手の MOD に機器が増えれば自動で効く。
    if not POWERED_DEVICE_IDS:
        raise SystemExit("ERROR: the power_devices block tag resolved to nothing - the "
                         "「電気が要る機器」 list would be vacuously complete")
    undoc_dev = [i for i in (POWERED_DEVICE_IDS + POWERED_EXTRA_IDS)
                 if i not in shown and not i.endswith("_part")]
    if undoc_dev:
        raise SystemExit(
            "ERROR: %d device(s) now need electricity but are not shown in the 使い方 tab - "
            "the owner would find them dead with no explanation: %s"
            % (len(undoc_dev), ", ".join(undoc_dev)))

    guides_json = guides_filled
    n_examples = sum(len(g["sections"]) for g in guides_filled)
    print(f"sorting kit: {len(SORTING_KIT)} parts -> {len(kit_tex)} distinct pictures")
    print(f"使い方 tab: {len(guides_filled)} topic(s), {n_examples} worked example(s), "
          f"{len(set(guide_ids))} distinct icons - all resolved")
    print(f"電力 guide: {len(POWER_FACTS)} value(s) read live out of the implementation "
          f"(none hand-typed); {len(power_cards)} 電力 block(s) and "
          f"{len(POWERED_DEVICE_IDS) + len(POWERED_EXTRA_IDS)} powered device(s) all documented")

    cat_index = {cat: i for i, (cat, _icon, _n) in enumerate(cats_meta)}
    cards_json = []
    for c in ordered:
        grid = None
        if c["cells"] is not None:
            grid = [(cid if cid else 0) for cid in c["cells"]]
        cards_json.append([cat_index[c["cat"]], c["id"], grid,
                           c["count"] if c["count"] else 0,
                           c["how"] if c["how"] else 0,
                           c["s"]])
    items_map = {iid: [ja, en, tex] for iid, (ja, en, tex) in reg.items.items()}
    total = len(ordered)

    # ---- Aurora Corvus adaptation ------------------------------------------
    # Everything above this point (data assembly, every validation check) is
    # byte-identical to the original generator's main(). From here down,
    # instead of splicing everything into one self-contained HTML page
    # (TEMPLATE, unused in this copy), we write the same data as JSON +
    # individual PNGs for this wiki's own multi-page, natively-styled
    # recipes/ section to fetch and render.
    OUT_IMG_DIR.mkdir(parents=True, exist_ok=True)
    for old in OUT_IMG_DIR.glob("t*.png"):
        old.unlink()
    for i, payload in enumerate(reg.tex_order):
        (OUT_IMG_DIR / f"t{i}.png").write_bytes(base64.b64decode(payload))

    OUT_DATA_DIR.mkdir(parents=True, exist_ok=True)
    recipes_data = {
        "total": total,
        "cats": cats_meta,       # [[name, icon_item_id, count], ...]
        "all_tab_icon": ALL_TAB_ICON,
        "items": items_map,      # id -> [ja, en, tex_key_or_null]
        "cards": cards_json,     # [cat_index, id, grid_or_null, count, how_or_0, search_blob]
        "guides": guides_json,
    }
    out_json = OUT_DATA_DIR / "recipes.json"
    out_json.write_text(
        json.dumps(recipes_data, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

    if no_yomi:
        print(f"WARNING: {len(no_yomi)} item name(s) have no reading in YOMI - "
              f"they will NOT be in correct あいうえお order:")
        for cat, name, chars in no_yomi:
            print(f"  WARNING: [{cat}] {name}  (未登録の文字: {chars})")
    print(f"reading coverage: {total - len(no_yomi)}/{total} card titles have a full yomi")
    packed_bytes = sum(len(base64.b64decode(p)) for p in reg.tex_order)
    print(f"textures: {len(reg.tex_order)} unique payloads "
          f"({reg.raw_bytes / 1048576:.2f} MiB source -> {packed_bytes / 1048576:.2f} MiB "
          f"written as individual PNGs, verified-lossless)")
    print(f"wrote {out_json} ({total} recipes, {out_json.stat().st_size / 1048576:.2f} MiB) "
          f"+ {len(reg.tex_order)} PNGs in {OUT_IMG_DIR}")


if __name__ == "__main__":
    main()
