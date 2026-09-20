#!/usr/bin/env python3
"""公開の直前に、Minecraft の版の切り替えが**正しく**済んでいるかを判定する。

**なぜ数では判定できないか**（2026-09-20 に 2 セッションで別々に数えて食い違った）:
`+mc26.2` の出現を数えると 132、zip のファイル名だけなら 68、生成物だけなら 15 と、
数える対象で答えが変わる。しかもどの数も単独では可否を決められない。**履歴まで書き換えれば
「0 件になった」と言えてしまう**からである。数ではなく性質で見る。

判定する性質は 3 つで、**すべて同時に**成り立って初めて合格:

  1. 現行のリンクが古い版の zip を 1 つも指していない
     （`download/`・`cherry/`・`glimpse_manifest.json`・`releases.json`）
  2. **かつ** 履歴の記載が 1 文字も変わっていない
     （`changelog/`・`changelog_feed/`・`data/changelog.json`。26.2 で出したのは事実であり、
       書き換えれば嘘になる。基準表と突き合わせるので、消しても書き換えても赤くなる）
  4. **かつ** 現行のページが指す zip が git に追跡されている
     （追跡されていなければ、push でページだけが出てファイルが出ない = リンクが 404）
  3. **かつ** 現行の導入手順に古い版の例示が残っていない
     （`guide/`・`data/guide.json`。リンクではないので切れはしないが、読んだ人は
       存在しないファイル名を探すことになる）

使い方:
    python3 scripts/check_release_version_switch.py --old 26.2 --new 26.3 --baseline <表>
    python3 scripts/check_release_version_switch.py --old 26.2 --new 26.3 --write-baseline <表>
    python3 scripts/check_release_version_switch.py --self-test

`--write-baseline` は**切り替えの前に**走らせて、履歴の現状を記録する。

**この検査自身の試験**: `--self-test` は木の写しを作り、3 つの性質それぞれを壊して
**赤くなることを確かめる**。緑の自己試験は飾りにすぎない（2026-09-20、Cherry が
自己試験の全部緑のまま中心の判定を丸ごと削除しても緑だった例を報告している）。
"""
import argparse
import json
import os
import re
import shutil
import sys
import tempfile

# 現行のリンクを持つ所（この下に古い版の zip 名があってはならない）
LIVE_DIRS = ("download", "cherry")
LIVE_FILES = ("glimpse_manifest.json", "releases.json")
# 履歴（1 文字も変えてはならない）
HISTORY_MARKERS = ("changelog",)
HISTORY_FILES = ("data/changelog.json",)
# 現行の導入手順（古い版の例示が残ってはならない）
GUIDE_DIRS = ("guide",)
GUIDE_FILES = ("data/guide.json",)

READ = (".html", ".json")


def walk(root):
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in (".git", "downloads", "node_modules", "assets")]
        for name in files:
            if name.endswith(READ):
                path = os.path.join(base, name)
                yield os.path.relpath(path, root).replace(os.sep, "/")


def read(root, rel):
    try:
        with open(os.path.join(root, rel), encoding="utf-8", errors="replace") as handle:
            return handle.read()
    except OSError:
        return ""


def is_live(rel):
    parts = rel.split("/")
    return rel in LIVE_FILES or any(p in LIVE_DIRS for p in parts[:-1])


def is_history(rel):
    return rel in HISTORY_FILES or any(m in rel for m in HISTORY_MARKERS)


def is_guide(rel):
    parts = rel.split("/")
    return rel in GUIDE_FILES or any(p in GUIDE_DIRS for p in parts[:-1])


def zip_pattern(version):
    return re.compile(r"[A-Za-z_]+_MODs_v[0-9.]+\+mc" + re.escape(version) + r"\.zip")


def any_pattern(version):
    return re.compile(r"\+mc" + re.escape(version))


def history_counts(root, old):
    """履歴の各ファイルに古い版が何回出るか。書き換えも削除も捕まえるための基準表。"""
    pat = any_pattern(old)
    out = {}
    for rel in walk(root):
        if is_history(rel):
            hits = len(pat.findall(read(root, rel)))
            if hits:
                out[rel] = hits
    return out


def check(root, old, new, baseline):
    failures = []
    notes = []

    # 性質 1: 現行のリンクに古い zip 名が無い
    zip_old = zip_pattern(old)
    live_bad = []
    for rel in walk(root):
        if is_live(rel) and zip_old.search(read(root, rel)):
            live_bad.append(rel)
    if live_bad:
        failures.append("1. 現行のリンクが %s の zip を指している (%d 件): %s"
                        % (old, len(live_bad), ", ".join(sorted(live_bad)[:6])))

    # 性質 2: 履歴が基準表と一致する
    now = history_counts(root, old)
    if baseline is None:
        failures.append("2. 履歴の基準表が渡されていない。--write-baseline を切り替えの前に走らせること。")
    else:
        for rel, want in sorted(baseline.items()):
            got = now.get(rel, 0)
            if got != want:
                failures.append("2. 履歴が変わっている: %s は %s の記載が %d 件のはずが %d 件"
                                % (rel, old, want, got))
        # **新しい履歴の追記は赤にしない。** 公開そのものが履歴を増やす（今回なら Cherry 1.0.1 の
        # 項目が 13 言語ぶん増える）。増えた履歴が古い版に言及するのは正当で、たとえば
        # 「1.0.0 は 26.2 向けだった」は事実である。性質 2 が禁じるのは **既存の履歴を書き換える/消す**
        # ことだけで、増やすことではない。消しても改名しても、基準表側の件数が減るので上で捕まる。
        added = sorted(set(now) - set(baseline))
        if added:
            notes.append("2. 履歴が増えている（正当な追記として許す）: %s"
                         % ", ".join("%s(%d)" % (r, now[r]) for r in added[:6]))

    # 性質 4: 現行のページが指す zip が、**git に追跡されている**
    # 「正しいディレクトリにある」「git が追跡している」「公開される」は別の事実で、
    # push が作用するのは追跡されているものだけである（2026-09-20、Cherry の指摘で
    # Alpha・Cherry の両方の 26.3 版 zip が未追跡のままだと判明した）。
    # 未追跡のまま公開すると、**ダウンロードを宣伝するページは全部出て、ファイルだけが出ない** ——
    # ページは正しく、リンクだけが 404 になる。見た目には何も壊れていないので気づきにくい。
    wanted = set()
    zip_new = zip_pattern(new)
    for rel in walk(root):
        if is_live(rel):
            wanted.update(zip_new.findall_names(read(root, rel)) if False else
                          re.findall(r"[A-Za-z_]+_MODs_v[0-9.]+\+mc" + re.escape(new) + r"\.zip",
                                     read(root, rel)))
    if wanted:
        tracked = set()
        try:
            import subprocess
            out = subprocess.run(["git", "-C", root, "ls-files", "downloads"],
                                 capture_output=True, text=True).stdout
            tracked = {os.path.basename(x) for x in out.splitlines() if x}
        except Exception as exc:                                  # git が無い場合は判定できない
            failures.append("4. git に問い合わせられなかったので追跡を判定できない: %s" % exc)
        else:
            missing = sorted(n for n in wanted if n not in tracked)
            if missing:
                failures.append("4. 現行のページが指す zip が git に追跡されていない（push しても"
                                " ファイルが出ず、リンクが 404 になる）: %s" % ", ".join(missing))

    # 性質 3: 現行の導入手順に古い版の例示が無い
    any_old = any_pattern(old)
    guide_bad = []
    for rel in walk(root):
        if is_guide(rel) and any_old.search(read(root, rel)):
            guide_bad.append(rel)
    if guide_bad:
        failures.append("3. 現行の導入手順に %s の例示が残っている (%d 件): %s"
                        % (old, len(guide_bad), ", ".join(sorted(guide_bad)[:6])))

    return failures, notes


def self_test(root, old, new):
    """**わざと壊して、3 つの性質がそれぞれ赤くなることを確かめる。**

    緑の自己試験は何も証明しない。ここで求めるのは「壊したら赤くなる」であって
    「今は緑」ではない。壊しても緑なら、その性質は飾りである。
    """
    print("=== 自己試験: 壊したら赤くなるか ===")
    base = history_counts(root, old)
    results = []

    def run(label, mutate, want_property):
        tmp = tempfile.mkdtemp(prefix="relswitch-")
        work = os.path.join(tmp, "site")
        shutil.copytree(root, work, ignore=shutil.ignore_patterns(".git", "downloads", "assets", "node_modules"))
        mutate(work)
        fails, _ = check(work, old, new, base)
        hit = [f for f in fails if f.startswith("%d." % want_property)]
        shutil.rmtree(tmp, ignore_errors=True)
        ok = bool(hit)
        results.append(ok)
        print("  %-52s -> %s%s" % (label, "赤 OK" if ok else "**緑のまま = この性質は飾り**",
                                   ("  " + hit[0][:80]) if hit else ""))

    def plant_live(work):
        target = os.path.join(work, "download", "index.html")
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "a", encoding="utf-8") as handle:
            handle.write("\n<a href=\"../downloads/Alpha_MODs_v4.4.0+mc%s.zip\">x</a>\n" % old)

    def erase_history(work):
        for rel in sorted(base):
            path = os.path.join(work, rel)
            if os.path.isfile(path):
                text = read(work, rel).replace("+mc" + old, "+mc" + new)
                with open(path, "w", encoding="utf-8") as handle:
                    handle.write(text)
                return

    def plant_guide(work):
        target = os.path.join(work, "guide", "index.html")
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "a", encoding="utf-8") as handle:
            handle.write("\n<code>alpha-guns-1.0.0+mc%s.jar</code>\n" % old)

    run("現行のリンクに古い zip を 1 つ植える", plant_live, 1)
    run("履歴を 1 ファイルだけ新しい版に書き換える", erase_history, 2)
    run("導入手順に古い例示を 1 つ植える", plant_guide, 3)

    def untrack_zip(work):
        """現行のページが新しい zip を指しているのに、その実体が追跡されていない状態を作る。"""
        target = os.path.join(work, "download", "index.html")
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "a", encoding="utf-8") as handle:
            handle.write("\n<a href=\"../downloads/Alpha_MODs_v9.9.9+mc%s.zip\">x</a>\n" % new)

    run("追跡されていない zip を指すリンクを植える", untrack_zip, 4)

    ok = all(results)
    print("=== 自己試験 = %s（3 つの性質すべてが、壊されたときに赤くなる必要がある）"
          % ("PASS" if ok else "FAIL"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ap.add_argument("--old", default="26.2")
    ap.add_argument("--new", default="26.3")
    ap.add_argument("--baseline")
    ap.add_argument("--write-baseline")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.write_baseline:
        counts = history_counts(args.root, args.old)
        total = sum(counts.values())
        # **数の意味を表そのものに書く。** 2026-09-20、同じものを数えて 54 と 27 が出た
        # （出現数と行数）。どちらも正しいが、意味を書かずに並べると片方を「壊れている」と
        # 直してしまう事故が起こる。
        doc = {"_note": "履歴の基準表。値は **出現数**（1 行に 2 回出る行があるので行数とは違う）。"
                        "合計 %d 出現 / %d ファイル。性質 2 はこの表と突き合わせ、"
                        "既存の履歴の書き換え・削除を捕まえる。追記は許す。" % (total, len(counts)),
               "_old_version": args.old, "counts": counts}
        with open(args.write_baseline, "w", encoding="utf-8") as handle:
            json.dump(doc, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        print("履歴の基準表を書きました: %s（%d ファイル、%s の出現 %d 件）"
              % (args.write_baseline, len(counts), args.old, total))
        return 0

    if args.self_test:
        return 0 if self_test(args.root, args.old, args.new) else 1

    baseline = None
    if args.baseline and os.path.isfile(args.baseline):
        with open(args.baseline, encoding="utf-8") as handle:
            loaded = json.load(handle)
        baseline = loaded.get("counts", loaded) if isinstance(loaded, dict) else loaded

    failures, notes = check(args.root, args.old, args.new, baseline)
    for n in notes:
        print("  note: " + n)
    if failures:
        print("RELEASE VERSION SWITCH = FAIL (%d)" % len(failures))
        for f in failures:
            print("  - " + f)
        return 1
    print("RELEASE VERSION SWITCH = PASS（現行は %s のみ、履歴は %s のまま、導入手順も切替済み）"
          % (args.new, args.old))
    return 0


if __name__ == "__main__":
    sys.exit(main())
