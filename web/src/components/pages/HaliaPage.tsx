import Link from "next/link";
import { FRESH } from "@/i18n/fresh";
import { pathOf } from "@/lib/site";
import { langData } from "@/lib/wiki";
import type { Lang } from "@/lib/wiki-types";
import { HaliaFrame } from "../halia/HaliaScene";

/**
 * Halia: the coming-soon page for the framework that succeeds Astraea. A bald eagle, pinned to the page,
 * follows the reader down the sections: it glides, dives, spreads its wings to brake, takes hold of
 * Astraea's remnants and perches. Nothing here describes a feature that is not released.
 */
export function HaliaPage({ lang }: { lang: Lang }) {
  const d = langData(lang);
  const f = FRESH[lang].halia;
  const en = FRESH.en.halia;
  const astraea = d.products.astraea?.name ?? "ASTRAEA";
  const manifesto = f.manifesto ?? en.manifesto!;
  const specs = f.specs ?? en.specs!;
  const timeline = f.timeline ?? en.timeline!;
  return (
    <HaliaFrame label={f.sceneLabel} fallback={f.fallback}>
      <section className="ac-halia-hero" aria-labelledby="halia-title">
        <div className="ac-wrap ac-halia-copy">
          <p className="ac-halia-badge">COMING SOON</p>
          <p className="ac-halia-stmt">
            <span>BEATS</span> <span className="ac-halia-old">{astraea}</span>
          </p>
          <h1 id="halia-title" className="ac-halia-name" data-text="HALIA">
            HALIA
          </h1>
          <p className="ac-halia-sub">HALIA // ABSOLUTE SOVEREIGNTY</p>
          <p className="ac-eyebrow">{f.eyebrow}</p>
          <p className="ac-halia-line">{f.line}</p>
          <p className="ac-lead ac-halia-lede">{f.lede}</p>
          <p className="ac-halia-beats">{f.beatsLine}</p>
          <p className="ac-halia-scroll" aria-hidden="true">
            SCROLL TO OBSERVE ASCENSION ↓
          </p>
        </div>
      </section>

      <section className="ac-halia-sec" aria-labelledby="halia-manifesto">
        <div className="ac-wrap">
          <div className="ac-halia-panel">
            <h2 id="halia-manifesto" className="ac-halia-h2">
              {manifesto.heading}
            </h2>
            {manifesto.body.map((p) => (
              <p key={p}>{p}</p>
            ))}
          </div>
        </div>
      </section>

      <section className="ac-halia-sec" aria-labelledby="halia-specs">
        <div className="ac-wrap">
          <h2 id="halia-specs" className="ac-halia-h2">
            {specs.heading}
          </h2>
          <ul className="ac-halia-cards">
            {specs.items.map(([code, title, detail]) => (
              <li key={code} className="ac-halia-panel ac-halia-card">
                <span className="ac-halia-code">{code}</span>
                <b>{title}</b>
                <p>{detail}</p>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="ac-halia-sec" aria-labelledby="halia-timeline">
        <div className="ac-wrap">
          <div className="ac-halia-panel">
            <h2 id="halia-timeline" className="ac-halia-h2">
              {timeline.heading}
            </h2>
            <dl className="ac-halia-facts">
              {timeline.items.map(([k, v]) => (
                <div key={k}>
                  <dt>{k}</dt>
                  <dd>{v}</dd>
                </div>
              ))}
            </dl>
            <p className="ac-halia-actions">
              <Link className="ac-link" href={pathOf(lang, "astraea/")}>
                {f.back} <span className="ac-flip">{d.chrome.arrow}</span>
              </Link>
            </p>
            <p className="ac-small">{f.next}</p>
            <p className="ac-small ac-halia-hint">{f.hint}</p>
          </div>
        </div>
      </section>
    </HaliaFrame>
  );
}
