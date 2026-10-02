"use client";

import { usePathname } from "next/navigation";
import { splitPath } from "@/lib/paths";
import { BASE_PATH, LANGUAGES, pathOf } from "@/lib/site";
import type { Lang } from "@/lib/wiki-types";

/** The footer's language list: the same page in each language (plain links, no query). */
export function FooterLanguages({ lang, label }: { lang: Lang; label: string }) {
  const { section } = splitPath(usePathname());
  return (
    <nav aria-label={label} className="ac-footer-langs">
      <ul>
        {LANGUAGES.map((l) => (
          <li key={l.code}>
            <a
              href={`${BASE_PATH}${pathOf(l.code, section)}`}
              lang={l.code}
              hrefLang={l.code}
              data-lang={l.code}
              aria-current={l.code === lang ? "true" : undefined}
            >
              {l.name}
            </a>
          </li>
        ))}
      </ul>
    </nav>
  );
}
