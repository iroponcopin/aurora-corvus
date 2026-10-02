import { notFound } from "next/navigation";
import { isLang } from "./site";
import type { Lang } from "./wiki-types";

export type LangParams = { params: Promise<{ lang: string }> };

/** The route's language (the segment is generated for the 13 languages only). */
export async function langOf(params: LangParams["params"]): Promise<Lang> {
  const { lang } = await params;
  if (!isLang(lang)) notFound();
  return lang;
}
