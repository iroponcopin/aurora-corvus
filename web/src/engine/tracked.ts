/**
 * DOM boxes the WebGL world follows: viewports (a 3D scene drawn exactly inside an element)
 * and formation anchors (where the particles gather). Their document-space rectangles are
 * measured when layout changes — never per frame — and turned into screen rectangles each
 * frame from the scroll offset alone, so following the page costs no layout and no garbage.
 *
 * A box inside a `position: sticky` container does not move with the document while the
 * container is stuck, so for those the container's sticky geometry is measured too (its normal
 * position, its `top`, how far its parent lets it travel) and the frame replays the sticky rule
 * itself: the same clamp the browser applies, from the scroll offset alone.
 */

export interface Sticky {
  /** The sticky container's normal-flow document top, its `top` inset, and its travel limit. */
  natural: number;
  inset: number;
  travel: number;
  /** The tracked box's top relative to the container's top. */
  offset: number;
}

export interface Tracked {
  el: HTMLElement;
  /** Document-space box in CSS pixels (measured on layout changes); for a sticky box, its unstuck position. */
  top: number;
  left: number;
  width: number;
  height: number;
  /** Screen-space box for the current frame. */
  screenTop: number;
  screenLeft: number;
  visible: boolean;
  /** Element sits in a fixed-position container: its screen box ignores scroll. */
  fixed: boolean;
  /** Present while the element sits inside a sticky container. */
  sticky: Sticky | null;
}

const all: Tracked[] = [];
let observer: ResizeObserver | null = null;
let dirty = true;
let installed = false;

function stickyAncestor(el: HTMLElement): HTMLElement | null {
  for (let a = el.parentElement; a !== null && a !== document.body; a = a.parentElement) {
    if (getComputedStyle(a).position === "sticky") return a;
  }
  return null;
}

/** A sticky container's geometry, measured with stickiness briefly lifted (dirty frames only). */
function stickyGeometry(a: HTMLElement, scrollY: number, cache: Map<HTMLElement, Omit<Sticky, "offset">>): Omit<Sticky, "offset"> {
  const known = cache.get(a);
  if (known !== undefined) return known;
  const cs = getComputedStyle(a);
  const inset = parseFloat(cs.top) || 0;
  const marginBottom = parseFloat(cs.marginBottom) || 0;
  const previous = a.style.position;
  a.style.position = "relative";
  const natural = a.getBoundingClientRect();
  a.style.position = previous;
  const parent = a.parentElement;
  let limit = Infinity;
  if (parent !== null) {
    const pr = parent.getBoundingClientRect();
    const ps = getComputedStyle(parent);
    limit = pr.bottom + scrollY - (parseFloat(ps.paddingBottom) || 0) - (parseFloat(ps.borderBottomWidth) || 0);
  }
  const top = natural.top + scrollY;
  const geometry = { natural: top, inset, travel: Math.max(0, limit - marginBottom - natural.height - top) };
  cache.set(a, geometry);
  return geometry;
}

function measure(t: Tracked, scrollY: number, cache: Map<HTMLElement, Omit<Sticky, "offset">>): void {
  const r = t.el.getBoundingClientRect();
  t.left = r.left;
  t.width = r.width;
  t.height = r.height;
  const a = t.fixed ? null : stickyAncestor(t.el);
  if (a === null) {
    t.sticky = null;
    t.top = r.top + (t.fixed ? 0 : scrollY);
    return;
  }
  const g = stickyGeometry(a, scrollY, cache);
  const offset = r.top - a.getBoundingClientRect().top;
  t.sticky = { ...g, offset };
  t.top = g.natural + offset;
}

function markDirty(): void {
  dirty = true;
}

function install(): void {
  if (installed || typeof window === "undefined") return;
  installed = true;
  observer = new ResizeObserver(markDirty);
  observer.observe(document.documentElement);
  window.addEventListener("resize", markDirty, { passive: true });
  window.addEventListener("load", markDirty, { passive: true });
  document.fonts?.addEventListener?.("loadingdone", markDirty);
}

export function track(el: HTMLElement, fixed = false): Tracked {
  install();
  const t: Tracked = {
    el,
    top: 0,
    left: 0,
    width: 0,
    height: 0,
    screenTop: 0,
    screenLeft: 0,
    visible: false,
    fixed,
    sticky: null,
  };
  all.push(t);
  observer?.observe(el);
  dirty = true;
  return t;
}

export function untrack(t: Tracked): void {
  const i = all.indexOf(t);
  if (i >= 0) all.splice(i, 1);
  observer?.unobserve(t.el);
}

/** Force a re-measure on the next frame (after a route change or a layout animation). */
export function invalidateLayout(): void {
  dirty = true;
}

/** Called once per frame by the pipeline, before anything reads a tracked box. */
export function updateTracked(scrollY: number, viewportW: number, viewportH: number): void {
  if (dirty) {
    dirty = false;
    // Measured against the real scroll position at this instant.
    const sy = window.scrollY;
    const cache = new Map<HTMLElement, Omit<Sticky, "offset">>();
    for (let i = 0; i < all.length; i++) measure(all[i]!, sy, cache);
  }
  for (let i = 0; i < all.length; i++) {
    const t = all[i]!;
    const s = t.sticky;
    if (s !== null) {
      // The browser's sticky rule: pushed down to `top` once its normal place scrolls above it,
      // never further than its parent allows.
      const normal = s.natural - scrollY;
      const shift = Math.min(Math.max(s.inset - normal, 0), s.travel);
      t.screenTop = normal + shift + s.offset;
    } else {
      t.screenTop = t.fixed ? t.top : t.top - scrollY;
    }
    t.screenLeft = t.left;
    t.visible =
      t.width > 0 &&
      t.height > 0 &&
      t.screenTop < viewportH &&
      t.screenTop + t.height > 0 &&
      t.screenLeft < viewportW &&
      t.screenLeft + t.width > 0;
  }
}
