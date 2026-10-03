import { LANG_CODES } from "./site";
import type { Lang } from "./wiki-types";

/**
 * Split an app path (without the basePath, as usePathname() returns it) into its language and
 * section tail. Japanese has no segment; in development the rewrite may still show `/ja/`.
 */
export function splitPath(pathname: string): { lang: Lang; section: string } {
  let p = pathname.replace(/index\.html$/, "");
  if (!p.endsWith("/")) p += "/";
  const parts = p.replace(/^\/+/, "").split("/");
  const head = parts[0] ?? "";
  if (head !== "" && (LANG_CODES as readonly string[]).includes(head)) {
    return { lang: head as Lang, section: parts.slice(1).join("/") };
  }
  return { lang: "ja", section: parts.join("/") };
}

/** The first path segment of the section ("" for home): "launcher", "ouka", ... */
export function sectionKey(section: string): string {
  return section.split("/")[0] ?? "";
}
