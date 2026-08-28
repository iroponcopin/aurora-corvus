#!/usr/bin/env python3
"""Builds the site-wide 404.html. GitHub Pages serves this file's *content*
at whatever URL the visitor actually hit (any path, any depth) while leaving
the browser's resolved base URL as that broken path -- so this page cannot
use normal depth-relative asset/nav paths like every other page does. It
passes absolute_base to page() to force every link to an absolute path
instead. Rendered once in Japanese (with a short English note): GitHub
Pages has no way to know which language subfolder the visitor came from."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from site_common import ROOT, page  # noqa: E402

ABS_BASE = "/aurora-corvus/"


def build():
    body = f"""
<div class="hero">
  <h1>ページが見つかりません</h1>
  <p class="lede">
    お探しのページは移動または削除された可能性があります。
    <br><span style="color:var(--text-muted);font-size:0.9em;">
    Page not found — it may have moved or been removed.</span>
  </p>
  <div class="tag-row" style="margin-top:20px;">
    <a class="btn" href="{ABS_BASE}">トップページへ</a>
    <a class="btn btn--ghost" href="{ABS_BASE}recipes/">レシピ集</a>
    <a class="btn btn--ghost" href="{ABS_BASE}changelog/">更新履歴</a>
  </div>
</div>
"""
    html = page(
        lang="ja",
        section="",
        title="ページが見つかりません",
        description="404 Not Found",
        active="",
        body=body,
        absolute_base=ABS_BASE,
    )
    (ROOT / "404.html").write_text(html, encoding="utf-8")
    print(f"wrote 404.html ({len(html):,} bytes)")


if __name__ == "__main__":
    build()
