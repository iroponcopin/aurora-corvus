import type { Metadata } from "next";
import { asset, BASE_URL, LANGUAGES, urlOf } from "./site";
import { wiki } from "./wiki";
import type { Lang } from "./wiki-types";

const OG_IMAGE = new URL(asset("wiki/corvus/og-image.png"), BASE_URL).href;

let checked = false;

/** The site's language table must agree with the wiki's (scripts/site_common.py LANGUAGES). */
function checkLanguages(): void {
  if (checked) return;
  const theirs = wiki().site.languages.map((l) => `${l.code}:${l.dir}:${l.hreflang}`).join(" ");
  const ours = LANGUAGES.map((l) => `${l.code}:${l.dir}:${l.hreflang}`).join(" ");
  if (theirs !== ours) throw new Error(`language tables disagree:\n wiki: ${theirs}\n site: ${ours}`);
  checked = true;
}

/**
 * The head every page carries, as the pre-4.0 portal wrote it: "<title> | Corvus" (the home page
 * is just "Corvus"), the description, the canonical URL, 13 hreflang alternates plus x-default
 * (the Japanese URL), Open Graph and Twitter cards with the shared image, and the favicons.
 */
export function pageMeta(lang: Lang, section: string, title: string | null, description: string): Metadata {
  checkLanguages();
  const site = wiki().site.title;
  const full = title === null ? site : `${title} | ${site}`;
  const languages: Record<string, string> = {};
  for (const l of LANGUAGES) languages[l.hreflang] = urlOf(l.code, section);
  languages["x-default"] = urlOf("ja", section);
  const url = urlOf(lang, section);
  const image = { url: OG_IMAGE, width: 1200, height: 630, alt: site };
  return {
    metadataBase: new URL(BASE_URL + "/"),
    title: full,
    description,
    alternates: { canonical: url, languages },
    openGraph: {
      title: full,
      description,
      url,
      siteName: site,
      locale: lang,
      images: [image],
      type: "website",
    },
    twitter: { card: "summary_large_image", title: full, description, images: [image] },
    icons: {
      icon: [
        { url: asset("wiki/corvus/favicon.ico"), sizes: "any" },
        { url: asset("wiki/corvus/favicon-32.png"), sizes: "32x32", type: "image/png" },
        { url: asset("wiki/corvus/favicon-16.png"), sizes: "16x16", type: "image/png" },
      ],
      apple: [{ url: asset("wiki/corvus/apple-touch-icon.png") }],
    },
  };
}
