"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { chime } from "@/engine/audio";
import { addFrameHook } from "@/engine/loop";
import { clamp } from "@/engine/math";
import { engine } from "@/engine/store";
import { useWorld } from "@/engine/useWorld";
import { asset } from "@/lib/site";

export interface RingItem {
  id: string;
  icon: string;
  name: string;
  jp: string | null;
  badge: string | null;
  category: string;
  tagline: string;
  /** Shown for an archived brand: why it is archived. */
  about: string | null;
  status: string;
  available: boolean;
  archived: boolean;
  href: string;
}

/** Scroll progress through the hub as preallocated strings, so writing it never allocates. */
const STEPS = 400;
const PROGRESS = Array.from({ length: STEPS + 1 }, (_, i) => (i / STEPS).toFixed(4));

/**
 * The brand ring of the Store's hub: the six marks orbit the astrolabe, scrolling through the
 * hub brings each one to the details card in turn, and hovering or tapping a mark (or its
 * button below, which is also the whole ring without WebGL) reads it out of turn. The hub's
 * scroll progress is written to `--hub-p`, and its beat to `data-beat`: "hero" (the title),
 * "ring" (the brands), or "all" when everything is laid out at once (reduced motion, or a
 * viewport too short to hold a beat).
 */
export function BrandRing({
  hubId,
  items,
  title,
  hint,
  readMore,
}: {
  hubId: string;
  items: RingItem[];
  title: string;
  hint: string;
  readMore: string;
}) {
  const world = useWorld();
  const [step, setStep] = useState(0);
  const [hover, setHover] = useState<number | null>(null);
  const [tapped, setTapped] = useState<number | null>(null);
  const hit = useRef<HTMLDivElement>(null);
  const shown = hover ?? tapped ?? step;
  const item = items[shown] ?? items[0]!;
  const icons = items.map((m) => m.icon).join("|");

  useEffect(() => {
    if (world === null) return;
    world.marks.setIcons(icons.split("|").map((i) => asset(i)));
  }, [world, icons]);

  useEffect(() => {
    if (world === null) return;
    world.marks.hovered = shown;
    return () => {
      world.marks.hovered = -1;
    };
  }, [world, shown]);

  // Scroll through the hub: the CSS beats, and one brand per sixth of the ring's stretch.
  useEffect(() => {
    const hub = document.getElementById(hubId);
    if (hub === null) return;
    const motion = window.matchMedia("(prefers-reduced-motion: reduce)");
    let flat = false;
    let top = 0;
    let span = 1;
    let beat = "";
    const setBeat = (b: string): void => {
      if (b === beat) return;
      beat = b;
      hub.dataset.beat = b;
    };
    const measure = (): void => {
      flat = motion.matches || window.innerHeight < 620;
      if (flat) setBeat("all");
      const r = hub.getBoundingClientRect();
      top = r.top + window.scrollY;
      span = Math.max(1, r.height - window.innerHeight);
    };
    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(hub);
    window.addEventListener("resize", measure, { passive: true });
    motion.addEventListener("change", measure);
    let lastK = -1;
    let lastStep = -1;
    const n = items.length;
    const unhook = addFrameHook(() => {
      const p = flat ? 1 : clamp((engine.scrollY - top) / span, 0, 1);
      const k = Math.round(p * STEPS);
      if (k !== lastK) {
        lastK = k;
        hub.style.setProperty("--hub-p", PROGRESS[k]!);
      }
      if (!flat) setBeat(p < 0.24 ? "hero" : "ring");
      const s = flat ? 0 : Math.min(n - 1, Math.max(0, Math.floor(((p - 0.3) / 0.66) * n)));
      if (s !== lastStep) {
        lastStep = s;
        setStep(s);
      }
    });
    return () => {
      unhook();
      ro.disconnect();
      window.removeEventListener("resize", measure);
      motion.removeEventListener("change", measure);
      delete hub.dataset.beat;
    };
  }, [hubId, items.length]);

  // Pointer picking over the stage reads the marks' projected positions (no raycaster).
  useEffect(() => {
    const el = hit.current;
    if (el === null || world === null) return;
    let last = -1;
    const onMove = (e: PointerEvent): void => {
      if (e.pointerType === "touch") return;
      const i = world.marks.pick(e.clientX, e.clientY);
      if (i === last) return;
      last = i;
      el.style.cursor = i >= 0 ? "pointer" : "";
      setHover(i >= 0 ? i : null);
      if (i >= 0) chime("tick");
    };
    const onLeave = (): void => {
      last = -1;
      setHover(null);
    };
    const onClick = (e: MouseEvent): void => {
      const i = world.marks.pick(e.clientX, e.clientY);
      if (i < 0) return;
      setTapped(i);
      chime("get");
    };
    el.addEventListener("pointermove", onMove);
    el.addEventListener("pointerleave", onLeave);
    el.addEventListener("click", onClick);
    return () => {
      el.removeEventListener("pointermove", onMove);
      el.removeEventListener("pointerleave", onLeave);
      el.removeEventListener("click", onClick);
    };
  }, [world]);

  return (
    <>
      <div ref={hit} className="ac-hub-hit ac-requires-webgl" aria-hidden="true" />
      <div className="ac-hub-ring">
        <div className="ac-hub-ring-head">
          <h2 className="ac-h2">{title}</h2>
          <p className="ac-lead">{hint}</p>
        </div>
        <ul className="ac-hub-marks">
          {items.map((m, i) => (
            <li key={m.id}>
              <button
                type="button"
                className="ac-hub-mark"
                aria-pressed={shown === i}
                aria-label={m.name}
                title={m.name}
                data-dim={m.archived}
                onPointerEnter={(e) => {
                  if (e.pointerType !== "touch") setHover(i);
                }}
                onPointerLeave={() => setHover(null)}
                onFocus={() => setHover(i)}
                onBlur={() => setHover(null)}
                onClick={() => {
                  setTapped(i);
                  chime("tick");
                }}
              >
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={asset(m.icon)} alt="" width={44} height={44} />
              </button>
            </li>
          ))}
        </ul>
        <article className="ac-hub-card ac-card" aria-live="polite" aria-label={item.name} data-brand={item.id}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img className="ac-hub-card-icon" src={asset(item.icon)} alt="" width={64} height={64} data-dim={item.archived} />
          <div className="ac-hub-card-copy">
            <div className="ac-hub-card-name">
              <h3>{item.name}</h3>
              {item.jp ? <span lang="ja">{item.jp}</span> : null}
              {item.badge ? <span className="ac-hub-badge">{item.badge}</span> : null}
            </div>
            <p className="ac-hub-card-cat">{item.category}</p>
            <p className="ac-hub-card-tag">{item.tagline}</p>
            {item.archived && item.about ? <p className="ac-small">{item.about}</p> : null}
          </div>
          <div className="ac-hub-card-side">
            <span className="ac-hub-status" data-on={item.available}>
              {item.status}
            </span>
            <Link className="ac-link" href={item.href}>
              {item.name} <span className="ac-flip">{readMore}</span>
            </Link>
          </div>
        </article>
      </div>
    </>
  );
}
