#!/usr/bin/env python3
"""Builds sitemap.xml by walking every generated index.html. Run this LAST,
after scripts/build.py, since it just reflects whatever pages exist on disk.

SITE_URL must be filled in once the GitHub Pages URL is known (see README).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE_URL = "https://iroponcopin.github.io/aurora-corvus"


def build():
    pages = sorted(ROOT.rglob("index.html"))
    urls = []
    for p in pages:
        rel = p.relative_to(ROOT).parent
        rel_str = "" if str(rel) == "." else str(rel) + "/"
        urls.append(f"{SITE_URL}/{rel_str}")

    body = "\n".join(
        f"  <url><loc>{u}</loc></url>" for u in urls
    )
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{body}
</urlset>
"""
    (ROOT / "sitemap.xml").write_text(xml, encoding="utf-8")
    print(f"wrote sitemap.xml ({len(urls)} URLs)")

    robots = ROOT / "robots.txt"
    text = robots.read_text(encoding="utf-8")
    if "Sitemap:" not in text:
        robots.write_text(text.rstrip() + f"\nSitemap: {SITE_URL}/sitemap.xml\n", encoding="utf-8")
        print("appended Sitemap: line to robots.txt")


if __name__ == "__main__":
    build()
