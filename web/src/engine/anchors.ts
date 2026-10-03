import { clamp, smoothstep } from "./math";
import { engine, setFormation } from "./store";
import { type Tracked, track, untrack } from "./tracked";

/**
 * Realm anchors: page sections that tell the particles which formation to take and where.
 * With one anchor the formation is set once (a timed morph); with several (the home page's
 * six realms) scroll position scrubs the morph from one realm to the next. Each anchor behaves
 * like a sticky element inside its section, so a formation stays on screen while its section
 * is being read and travels with the section's edges as it enters and leaves.
 */

export interface AnchorConfig {
  formation: number;
  /** Horizontal centre as a fraction of the viewport width (left-to-right; mirrored in RTL). */
  x: number;
  /** The same below 900 px, where layouts stack. */
  xNarrow?: number;
  /** Vertical centre as a fraction of the viewport while the section covers it. */
  y?: number;
  /** Formation radius as a fraction of the visible world height at the anchor's depth. */
  scale: number;
  scaleNarrow?: number;
  /** Formation lives in world space (the chronology river) instead of on screen. */
  world?: boolean;
  /** Astrolabe and brand-mark presence (0..1) while this realm dominates. */
  astrolabe?: number;
  /** Brand tint (linear RGB). */
  tint?: readonly [number, number, number];
  /** Depth of the formation's plane (world z). */
  depth?: number;
}

export interface Anchor {
  tracked: Tracked;
  config: AnchorConfig;
  /** Screen-space centre for this frame (CSS px) and radius fraction. */
  cx: number;
  cy: number;
  scale: number;
}

export const anchors: Anchor[] = [];

export function addAnchor(el: HTMLElement, config: AnchorConfig): Anchor {
  const a: Anchor = { tracked: track(el), config, cx: 0, cy: 0, scale: config.scale };
  anchors.push(a);
  return a;
}

export function removeAnchor(a: Anchor): void {
  const i = anchors.indexOf(a);
  if (i >= 0) anchors.splice(i, 1);
  untrack(a.tracked);
}

/** Result of `direct()`: what the particles and the astrolabe should do this frame. */
export const direction = {
  aIndex: -1,
  bIndex: -1,
  /** Screen centres (CSS px) and radius fractions of formations A and B. */
  ax: 0,
  ay: 0,
  aScale: 0.3,
  aWorld: false,
  aDepth: 0,
  bx: 0,
  by: 0,
  bScale: 0.3,
  bWorld: false,
  bDepth: 0,
  /** Astrolabe presence target and its screen centre. */
  astrolabe: 0,
  astroX: 0,
  astroY: 0,
  astroScale: 0.3,
};

function sortByTop(): void {
  // Insertion sort in place: a handful of anchors, no temporary arrays.
  for (let i = 1; i < anchors.length; i++) {
    const a = anchors[i]!;
    let j = i - 1;
    while (j >= 0 && anchors[j]!.tracked.top > a.tracked.top) {
      anchors[j + 1] = anchors[j]!;
      j -= 1;
    }
    anchors[j + 1] = a;
  }
}

/** Decide formations, anchors, astrolabe presence and tint for this frame. Allocation-free. */
export function direct(w: number, h: number): void {
  const n = anchors.length;
  const d = direction;
  if (n === 0) {
    d.aIndex = -1;
    d.bIndex = -1;
    d.astrolabe = 0;
    return;
  }
  sortByTop();
  // Each anchor's screen centre and radius, written in the loop itself: as a helper used once,
  // the minifier turns it into an immediately-invoked function here, a closure per anchor per frame.
  const narrow = w < 900;
  for (let i = 0; i < n; i++) {
    const a = anchors[i]!;
    const t = a.tracked;
    const c = a.config;
    const yf = c.y ?? 0.5;
    const top = t.screenTop;
    const height = t.height;
    a.cy = height >= h ? clamp(h * yf, top + h * yf, top + height - h * (1 - yf)) : top + height * yf;
    const xf = narrow ? (c.xNarrow ?? 0.5) : c.x;
    a.cx = (engine.mirror < 0 ? 1 - xf : xf) * w;
    a.scale = narrow ? (c.scaleNarrow ?? c.scale) : c.scale;
  }

  let ia = 0;
  let ib = 0;
  let morph = 1;
  if (n > 1) {
    // The realm whose section has reached the top of the viewport, and the one after it.
    ia = 0;
    for (let i = 0; i < n; i++) if (anchors[i]!.tracked.screenTop <= 0) ia = i;
    const first = anchors[0]!;
    if (ia === 0 && first.tracked.screenTop > 0) {
      ib = 0;
      morph = 1;
    } else if (ia >= n - 1) {
      ib = ia;
      morph = 1;
    } else {
      ib = ia + 1;
      const next = anchors[ib]!;
      morph = smoothstep(0.15, 0.85, (h - next.tracked.screenTop) / h);
    }
    const A = anchors[ia]!;
    const B = anchors[ib]!;
    if (!engine.scrub || engine.formationA !== A.config.formation || engine.formationB !== B.config.formation || engine.morph !== morph) {
      engine.scrub = true;
      engine.formationA = A.config.formation;
      engine.formationB = B.config.formation;
      engine.morph = morph;
      engine.morphTarget = morph;
    }
  } else {
    const only = anchors[0]!;
    if (engine.scrub || engine.formationB !== only.config.formation) setFormation(only.config.formation);
    ia = 0;
    ib = 0;
  }

  const A = anchors[ia]!;
  const B = anchors[ib]!;
  d.aIndex = ia;
  d.bIndex = ib;
  d.ax = A.cx;
  d.ay = A.cy;
  d.aScale = A.scale;
  d.aWorld = A.config.world === true;
  d.aDepth = A.config.depth ?? 0;
  d.bx = B.cx;
  d.by = B.cy;
  d.bScale = B.scale;
  d.bWorld = B.config.world === true;
  d.bDepth = B.config.depth ?? 0;

  // Tint and astrolabe follow the blend of the two realms.
  const m = n > 1 ? morph : 1;
  const ta = A.config.tint;
  const tb = B.config.tint;
  if (ta !== undefined && tb !== undefined) {
    engine.tintTargetR = ta[0] + (tb[0] - ta[0]) * m;
    engine.tintTargetG = ta[1] + (tb[1] - ta[1]) * m;
    engine.tintTargetB = ta[2] + (tb[2] - ta[2]) * m;
  }
  const pa = A.config.astrolabe ?? 0;
  const pb = B.config.astrolabe ?? 0;
  d.astrolabe = pa + (pb - pa) * m;
  // The astrolabe rides the first realm that carries it.
  for (let i = 0; i < n; i++) {
    const a = anchors[i]!;
    if ((a.config.astrolabe ?? 0) > 0) {
      d.astroX = a.cx;
      d.astroY = a.cy;
      d.astroScale = a.scale;
      // Leaving the hero, the instrument fades with its section's visibility.
      if (!a.tracked.visible) d.astrolabe = 0;
      break;
    }
  }
}
