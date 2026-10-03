import Link from "next/link";
import { FooterLanguages } from "./FooterLanguages";
import { pathOf } from "@/lib/site";
import type { Lang, LangData } from "@/lib/wiki-types";

/**
 * The footer the pre-4.0 portal carried, column for column: Brands, Get started, Reference,
 * Status; the thirteen languages; the legal block.
 */
export function Footer({ lang, d }: { lang: Lang; d: LangData }) {
  const c = d.chrome;
  const cols: { heading: string; links: { label: string; href: string }[] }[] = [
    {
      heading: c.footerBrands,
      links: [
        { label: "OUKA", href: pathOf(lang, "ouka/") },
        { label: "Cherry", href: pathOf(lang, "cherry/") },
        { label: "Aureum", href: pathOf(lang, "aureum/") },
      ],
    },
    {
      heading: c.footerGetStarted,
      links: [
        { label: c.download, href: pathOf(lang, "download/") },
        { label: c.launcher, href: pathOf(lang, "launcher/") },
        { label: c.skin, href: pathOf(lang, "skin/") },
      ],
    },
    { heading: c.footerReference, links: [{ label: c.recipes, href: pathOf(lang, "recipes/") }] },
    {
      heading: c.footerStatus,
      links: [
        { label: c.changelog, href: pathOf(lang, "changelog/") },
        { label: c.upcoming, href: pathOf(lang, "upcoming/") },
        { label: c.discord, href: pathOf(lang, "discord/") },
      ],
    },
  ];
  return (
    <footer className="ac-footer">
      <div className="ac-wrap">
        <div className="ac-footer-cols">
          {cols.map((col) => (
            <div key={col.heading}>
              <h2>{col.heading}</h2>
              <ul>
                {col.links.map((l) => (
                  <li key={l.href}>
                    <Link href={l.href}>{l.label}</Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <FooterLanguages lang={lang} label={c.language} />
        <div className="ac-footer-legal">
          <p className="ac-footer-title">{c.legalTitle}</p>
          <p>{c.tagline}</p>
          <p>{c.footerNote}</p>
        </div>
      </div>
    </footer>
  );
}
