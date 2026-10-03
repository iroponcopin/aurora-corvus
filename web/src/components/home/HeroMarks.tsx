"use client";

import { useRouter } from "next/navigation";
import { useEffect, useRef } from "react";
import { chime } from "@/engine/audio";
import { useWorld } from "@/engine/useWorld";
import { asset } from "@/lib/site";

export interface MarkLink {
  id: string;
  icon: string;
  href: string;
  label: string;
}

/**
 * The hit area over the astrolabe: hovering a brand mark lights it (and its card below),
 * clicking opens it. Picking reads the marks' projected screen positions, which the world
 * writes every frame, so it needs no raycaster.
 */
export function HeroMarks({ marks, hint }: { marks: MarkLink[]; hint: string }) {
  const world = useWorld();
  const router = useRouter();
  const ref = useRef<HTMLDivElement>(null);
  const hoverRef = useRef(-1);

  useEffect(() => {
    if (world === null) return;
    world.marks.setIcons(marks.map((m) => asset(m.icon)));
  }, [world, marks]);

  useEffect(() => {
    const el = ref.current;
    if (el === null || world === null) return;
    const setHover = (i: number): void => {
      if (i === hoverRef.current) return;
      hoverRef.current = i;
      world.marks.hovered = i;
      el.style.cursor = i >= 0 ? "pointer" : "";
      document.querySelectorAll<HTMLElement>("[data-mark]").forEach((card) => {
        card.dataset.active = card.dataset.mark === String(i) ? "true" : "false";
      });
      if (i >= 0) chime("tick");
    };
    const onMove = (e: PointerEvent): void => {
      if (e.pointerType === "touch") return;
      setHover(world.marks.pick(e.clientX, e.clientY));
    };
    const onLeave = (): void => setHover(-1);
    const onClick = (e: MouseEvent): void => {
      const i = world.marks.pick(e.clientX, e.clientY);
      const m = marks[i];
      if (m === undefined) return;
      chime("get");
      router.push(m.href);
    };
    el.addEventListener("pointermove", onMove);
    el.addEventListener("pointerleave", onLeave);
    el.addEventListener("click", onClick);
    return () => {
      el.removeEventListener("pointermove", onMove);
      el.removeEventListener("pointerleave", onLeave);
      el.removeEventListener("click", onClick);
      world.marks.hovered = -1;
    };
  }, [world, marks, router]);

  return (
    <>
      <div ref={ref} className="ac-hero-hit" aria-hidden="true" />
      <p className="ac-hero-hint ac-small" aria-hidden={world === null ? "true" : "false"} data-ready={world !== null}>
        {hint}
      </p>
    </>
  );
}
