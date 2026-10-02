import { advance, type RootState } from "@react-three/fiber";
import { gsap } from "gsap";
import type Lenis from "lenis";
import { updateMusic, updateSound } from "./audio";
import { clamp, damp } from "./math";
import { engine } from "./store";

/**
 * The one frame loop of the site. GSAP's ticker owns requestAnimationFrame; on each tick it
 * advances Lenis (which fires ScrollTrigger.update through its scroll event), then the engine
 * clock, then renders the WebGL root by hand (`frameloop="never"`). One rAF, one order, every
 * frame: scroll, triggers and pixels can never drift apart. Nothing in `tick` allocates.
 */

let root: RootState | null = null;
/** DOM-side per-frame work (scroll-driven parameters), run after Lenis and before the render. */
const hooks: ((dt: number) => void)[] = [];

export function addFrameHook(fn: (dt: number) => void): () => void {
  hooks.push(fn);
  install();
  return () => {
    const i = hooks.indexOf(fn);
    if (i >= 0) hooks.splice(i, 1);
  };
}
let lenis: Lenis | null = null;
let installed = false;
let lastTickMs = 0;

function tick(_time: number, deltaMs: number): void {
  const start = performance.now();
  // Lenis first: its scroll event updates ScrollTrigger before anything reads scroll.
  if (lenis !== null) lenis.raf(start);

  // Display refresh estimate (ignores hitches so a dropped frame doesn't lower the target).
  if (deltaMs > 2 && deltaMs < 40) engine.refreshMs = damp(engine.refreshMs, deltaMs, 2.5, deltaMs / 1000);

  engine.dt = clamp(deltaMs / 1000, 1 / 240, 1 / 20);
  engine.time += engine.dt;
  engine.frame += 1;
  // Backwards, so a hook may remove itself while the list is being walked.
  for (let i = hooks.length - 1; i >= 0; i--) hooks[i]?.(engine.dt);

  if (root !== null) {
    advance(engine.time, false, root);
    const spent = performance.now() - start;
    engine.cpuMs = damp(engine.cpuMs, spent, 4, engine.dt);
    if (spent > engine.refreshMs) engine.longFrames += 1;
  }
  updateSound();
  updateMusic();
  lastTickMs = start;
}

function install(): void {
  if (installed) return;
  installed = true;
  // A long pause (a background tab) must not turn into one giant step on return.
  gsap.ticker.lagSmoothing(0);
  gsap.ticker.add(tick);
}

export function attachRoot(state: RootState): void {
  root = state;
  install();
}

export function detachRoot(state: RootState): void {
  if (root === state) root = null;
}

export function attachLenis(instance: Lenis): void {
  lenis = instance;
  install();
}

export function detachLenis(instance: Lenis): void {
  if (lenis === instance) lenis = null;
}

/** For the debug overlay: the timestamp of the last tick (ms, performance.now()). */
export function lastTick(): number {
  return lastTickMs;
}

export function ensureLoop(): void {
  install();
}
