import type { Metadata } from "next";
import { HomePage } from "@/components/home/HomePage";
import { pageMeta } from "@/lib/meta";
import { isLang } from "@/lib/site";
import { langData } from "@/lib/wiki";
import type { Lang } from "@/lib/wiki-types";

type Params = { params: Promise<{ lang: string }> };

export async function generateMetadata({ params }: Params): Promise<Metadata> {
  const { lang } = await params;
  const d = langData(lang as Lang);
  return pageMeta(lang as Lang, "", null, d.home.description);
}

export default async function Page({ params }: Params) {
  const { lang } = await params;
  if (!isLang(lang)) return null;
  return <HomePage lang={lang} />;
}
