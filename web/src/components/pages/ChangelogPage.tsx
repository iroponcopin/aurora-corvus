import { Formation } from "@/engine/store";
import { langData } from "@/lib/wiki";
import type { Lang } from "@/lib/wiki-types";
import { Changelog } from "../changelog/Changelog";
import { BRAND_COLOR, ChronoDriver } from "../ChronoDriver";
import { RealmAnchor } from "../RealmAnchor";

const CYAN: readonly [number, number, number] = [0.3, 0.75, 1];

export function ChangelogPage({ lang }: { lang: Lang }) {
  const d = langData(lang);
  const c = d.changelog;
  // Beacons along the path of time: every dated release, oldest nearest the start.
  const dated = c.brands
    .flatMap((b) => b.releases)
    .filter((r) => r.date !== null)
    .sort((a, b) => (a.date ?? "").localeCompare(b.date ?? ""));
  const nodes = dated.map((r, i) => ({ u: 0.04 + (i / Math.max(1, dated.length - 1)) * 0.46, color: BRAND_COLOR[r.brand] ?? "#2997ff" }));
  return (
    <RealmAnchor id="ac-changelog" config={{ formation: Formation.Chronology, x: 0.5, scale: 1, world: true, tint: CYAN }}>
      <ChronoDriver nodes={nodes} targetId="ac-changelog" from={0.02} to={0.5} weight={1} />
      <div className="ac-wrap ac-page-head">
        <h1 className="ac-h1">{c.title}</h1>
        <p className="ac-lead">{c.description}</p>
      </div>
      <div className="ac-wrap">
        <Changelog brands={c.brands} labels={c.labels} noteBrands={c.noteBrands} />
      </div>
    </RealmAnchor>
  );
}
