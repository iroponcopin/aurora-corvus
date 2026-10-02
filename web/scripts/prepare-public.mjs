#!/usr/bin/env node
/**
 * Lays out web/public/portal/ before a build or a dev server: the portal's own brand art
 * (web/brand/, committed here because it has no other source) and byte copies of the wiki's
 * shared assets the pages use (favicons, OG image, recipe icons, the OUKA theme, the Sparxie
 * preview, the language detector). public/ is generated and git-ignored; the wiki's own files
 * stay the only originals.
 */
import { cpSync, existsSync, mkdirSync, rmSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const WEB = join(dirname(fileURLToPath(import.meta.url)), "..");
const WIKI = process.env.WIKI_DIR ?? join(WEB, "..");
const OUT = join(WEB, "public", "portal");

const copies = [
  [join(WEB, "brand", "logo.png"), "logo.png"],
  [join(WEB, "brand", "icons"), "icons"],
  [join(WEB, "brand", "art"), "art"],
  [join(WIKI, "assets", "js", "lang.js"), "lang.js"],
  [join(WIKI, "assets", "img", "brand", "favicon.ico"), "wiki/brand/favicon.ico"],
  [join(WIKI, "assets", "img", "brand", "favicon-16.png"), "wiki/brand/favicon-16.png"],
  [join(WIKI, "assets", "img", "brand", "favicon-32.png"), "wiki/brand/favicon-32.png"],
  [join(WIKI, "assets", "img", "brand", "apple-touch-icon.png"), "wiki/brand/apple-touch-icon.png"],
  [join(WIKI, "assets", "img", "brand", "og-image.png"), "wiki/brand/og-image.png"],
  [join(WIKI, "assets", "img", "brand", "corvus-mark.png"), "wiki/brand/corvus-mark.png"],
  [join(WIKI, "assets", "audio", "ouka", "silver-and-petals.m4a"), "wiki/audio/silver-and-petals.m4a"],
  [join(WIKI, "assets", "audio", "ouka", "silver-and-petals.mp3"), "wiki/audio/silver-and-petals.mp3"],
  [join(WIKI, "assets", "img", "recipes"), "wiki/recipes"],
  [join(WIKI, "assets", "img", "sparxie-front.png"), "wiki/skin/sparxie-front.png"],
  [join(WIKI, "assets", "img", "sparxie-model.png"), "wiki/skin/sparxie-model.png"],
];

rmSync(OUT, { recursive: true, force: true });
for (const [from, to] of copies) {
  if (!existsSync(from)) {
    console.error(`prepare-public: missing ${from}`);
    process.exit(1);
  }
  const dest = join(OUT, to);
  mkdirSync(dirname(dest), { recursive: true });
  cpSync(from, dest, { recursive: true });
}
console.log(`prepare-public: ${copies.length} entries -> public/portal/`);
