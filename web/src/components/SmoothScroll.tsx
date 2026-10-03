"use client";

import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import Lenis from "lenis";
import { usePathname } from "next/navigation";
import { useEffect } from "react";
import { attachLenis, detachLenis, ensureLoop } from "@/engine/loop";
import { engine } from "@/engine/store";
import { invalidateLayout } from "@/engine/tracked";

let lenis: Lenis | null = null;
let lastNativeY = 0;

function onLenisScroll(l: Lenis): void {
  engine.scrollY = l.animatedScroll;
  engine.scrollVelocity = l.velocity;
  engine.scrollLimit = l.limit;
  ScrollTrigger.update();
}

function onNativeScroll(): void {
  const y = window.scrollY;
  engine.scrollVelocity = y - lastNativeY;
  engine.scrollY = y;
  lastNativeY = y;
}

/** Scroll the page (smoothly unless the visitor prefers reduced motion). */
export function scrollToY(y: number, immediate = false): void {
  if (lenis !== null) lenis.scrollTo(y, { immediate, force: true });
  else window.scrollTo({ top: y, behavior: immediate ? "auto" : "smooth" });
}

export function getLenis(): Lenis | null {
  return lenis;
}

/**
 * Lenis smooth scrolling synced 1:1 with GSAP ScrollTrigger: Lenis is advanced by the shared
 * frame loop (GSAP's ticker) and its scroll event drives ScrollTrigger.update(), so triggers,
 * scrubbed timelines and the WebGL world all read the same scroll value in the same frame.
 * With prefers-reduced-motion the page scrolls natively and nothing is smoothed.
 */
export function SmoothScroll() {
  const pathname = usePathname();

  useEffect(() => {
    gsap.registerPlugin(ScrollTrigger);
    ensureLoop();
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    window.addEventListener("scroll", onNativeScroll, { passive: true });
    onNativeScroll();
    if (reduce) {
      return () => window.removeEventListener("scroll", onNativeScroll);
    }
    const instance = new Lenis({
      autoRaf: false,
      lerp: 0.085,
      smoothWheel: true,
      syncTouch: false,
      wheelMultiplier: 1,
      anchors: { offset: -72 },
      prevent: (node: HTMLElement) => node.closest("[data-lenis-prevent]") !== null,
    });
    lenis = instance;
    instance.on("scroll", onLenisScroll);
    attachLenis(instance);
    return () => {
      window.removeEventListener("scroll", onNativeScroll);
      detachLenis(instance);
      instance.destroy();
      if (lenis === instance) lenis = null;
    };
  }, []);

  useEffect(() => {
    // A new page: start at its top (or its #hash), re-measure everything the world follows.
    const hash = window.location.hash;
    if (lenis !== null && hash === "") lenis.scrollTo(0, { immediate: true, force: true });
    invalidateLayout();
    const id = window.requestAnimationFrame(() => {
      ScrollTrigger.refresh();
      invalidateLayout();
      lenis?.resize();
    });
    return () => window.cancelAnimationFrame(id);
  }, [pathname]);

  return null;
}
