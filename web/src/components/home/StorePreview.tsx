"use client";

import { useEffect, useState } from "react";
import { chime } from "@/engine/audio";
import { asset } from "@/lib/site";
import type { Product, StoreText } from "@/lib/wiki-types";
import { DownloadClock } from "../store/clock";
import { ActionButton, type AppState, DOWNLOAD_SECONDS, DownloadLine, fill, speedText } from "../store/StoreSim";

/**
 * The store realm on the home page: Discover's lead card, with the real GET → ring → OPEN
 * flow and Perch playing above it. The full Store is one click away.
 */
export function StorePreview({
  product,
  text,
  jar,
  speed,
  timeLeft,
  nowPlaying,
  track,
}: {
  product: Product;
  text: StoreText;
  jar: Record<string, string>;
  speed: string;
  timeLeft: string;
  nowPlaying: string;
  track: string;
}) {
  const [state, setState] = useState<AppState>({ phase: "get", target: null });
  const [note, setNote] = useState("");
  const [clock] = useState(() => new DownloadClock(1, DOWNLOAD_SECONDS));

  useEffect(() => {
    clock.setLeftTemplate(timeLeft);
    clock.onDone = () => {
      setState({ phase: "open", target: null });
      setNote(fill(text.announce.done, product.name));
      chime("done");
    };
    return () => clock.dispose();
  }, [clock, timeLeft, text.announce.done, product.name]);

  const press = (): void => {
    if (state.phase === "get") {
      clock.start(0);
      setState({ phase: "downloading", target: "get" });
      setNote(fill(text.announce.started, product.name));
      chime("get");
    } else if (state.phase === "downloading") {
      clock.stop(0);
      setState({ phase: "get", target: null });
      setNote(fill(text.announce.stopped, product.name));
    } else if (state.phase === "open") {
      setNote(fill(text.demoOpen, product.name));
      chime("tick");
    }
  };

  return (
    <div className="ac-preview ac-store-preview" lang={text.lang} dir={text.dir}>
      <div className="ac-perch ac-perch--static" aria-label={`${nowPlaying} — ${track}`} role="img">
        <span className="ac-perch-pill">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={asset("icons/ouka.png")} alt="" width={18} height={18} />
          <span className="ac-perch-eq" data-on="true" aria-hidden="true">
            <i />
            <i />
            <i />
          </span>
        </span>
      </div>
      <article className="ac-st-card ac-st-card--big ac-store-preview-card" data-brand={product.id}>
        <div className="ac-st-card-art">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={asset(product.art ?? product.icon)} alt="" loading="lazy" />
        </div>
        <div className="ac-st-card-copy">
          <span className="ac-st-eyebrow">{text.featured}</span>
          <h3>{product.headline}</h3>
        </div>
        <div className="ac-st-card-foot">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={asset(product.icon)} alt="" width={34} height={34} />
          <span>
            <b>{product.name}</b>
            <small>{product.tagline}</small>
          </span>
          <ActionButton product={product} index={0} state={state} t={text} jar={jar} clock={clock} onPress={press} small />
        </div>
      </article>
      {state.phase === "downloading" ? <DownloadLine speed={speedText(speed, product.id)} index={0} clock={clock} /> : null}
      <p className="ac-small ac-store-preview-note">{text.demoNote}</p>
      <p className="sr-only" role="status" aria-live="polite">
        {note}
      </p>
    </div>
  );
}
