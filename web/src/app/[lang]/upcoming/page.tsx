import type { Metadata } from "next";
import { UpcomingPage } from "@/components/pages/UpcomingPage";
import { pageMeta } from "@/lib/meta";
import { type LangParams, langOf } from "@/lib/route";
import { langData } from "@/lib/wiki";

export async function generateMetadata({ params }: LangParams): Promise<Metadata> {
  const lang = await langOf(params);
  const d = langData(lang);
  return pageMeta(lang, "upcoming/", d.upcoming.title, d.upcoming.description);
}

export default async function Page({ params }: LangParams) {
  return <UpcomingPage lang={await langOf(params)} />;
}
