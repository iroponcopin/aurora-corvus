import type { Metadata } from "next";
import { HaliaPage } from "@/components/pages/HaliaPage";
import { FRESH } from "@/i18n/fresh";
import { pageMeta } from "@/lib/meta";
import { type LangParams, langOf } from "@/lib/route";

export async function generateMetadata({ params }: LangParams): Promise<Metadata> {
  const lang = await langOf(params);
  const t = FRESH[lang].halia;
  return pageMeta(lang, "halia/", t.title, t.description);
}

export default async function Page({ params }: LangParams) {
  return <HaliaPage lang={await langOf(params)} />;
}
