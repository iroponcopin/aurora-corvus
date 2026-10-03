import Link from "next/link";
import { Formation } from "@/engine/store";
import { asset, pathOf } from "@/lib/site";
import { langData } from "@/lib/wiki";
import type { Lang } from "@/lib/wiki-types";
import { BRAND_COLOR, ChronoDriver } from "../ChronoDriver";
import { RealmAnchor } from "../RealmAnchor";
import { Rich } from "../Rich";

const AMBER: readonly [number, number, number] = [1, 0.7, 0.32];

/**
 * Coming next: what the Store lists as "soon" (today, Noctua), told before it is settled. The
 * camera rides the path of time from the latest releases to the next one.
 */
export function UpcomingPage({ lang }: { lang: Lang }) {
  const d = langData(lang);
  const u = d.upcoming;
  const recent = d.changelog.brands
    .flatMap((b) => b.releases)
    .filter((r) => r.date !== null)
    .sort((a, b) => (a.date ?? "").localeCompare(b.date ?? ""))
    .slice(-8);
  const nodes = [
    ...recent.map((r, i) => ({ u: 0.04 + i * 0.035, color: BRAND_COLOR[r.brand] ?? "#2997ff" })),
    ...u.nodes.map((n, i) => ({ u: 0.04 + recent.length * 0.035 + 0.06 + i * 0.05, color: BRAND_COLOR[n.id] ?? "#ffb340" })),
  ];
  const last = nodes[nodes.length - 1]?.u ?? 0.4;
  return (
    <RealmAnchor id="ac-upcoming" config={{ formation: Formation.Chronology, x: 0.5, scale: 1, world: true, tint: AMBER }}>
      <ChronoDriver nodes={nodes} targetId="ac-upcoming" from={0.02} to={last} weight={1} />
      <div className="ac-wrap ac-page-head">
        <h1 className="ac-h1">{u.title}</h1>
        <p className="ac-lead">{u.intro}</p>
      </div>
      <div className="ac-wrap ac-up-cards">
        {u.nodes.map((n, i) => (
          <article key={n.id} id={n.id} className="ac-up-card ac-card ac-reveal" data-side={i % 2 === 0 ? "a" : "b"} data-kind={n.kind} data-status={n.status}>
            <div className="ac-up-row">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={asset(n.icon)} alt="" width={88} height={88} />
              <div>
                <h2 className="ac-h2">{n.headline}</h2>
                <p className="ac-up-body">
                  <Rich text={n.body} />
                </p>
                <p>
                  <Link className="ac-link" href={pathOf(lang, n.href)}>
                    {n.linkName} <span className="ac-flip">{u.more}</span>
                  </Link>
                </p>
              </div>
            </div>
          </article>
        ))}
      </div>
      <div className="ac-wrap ac-up-foot">
        <p className="ac-small">{u.disclaimer}</p>
      </div>
    </RealmAnchor>
  );
}
