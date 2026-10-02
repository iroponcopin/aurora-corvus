import { addFrameHook } from "@/engine/loop";

/** The download ring's geometry (an r = 11 circle in a 28 × 28 box). */
export const RING_R = 11;
export const RING_C = 2 * Math.PI * RING_R;

const DASH_STEPS = 240;
/** Every dash offset the ring can show, as strings made once: a frame never formats a number. */
const DASH = Array.from({ length: DASH_STEPS + 1 }, (_, k) => (RING_C * (1 - k / DASH_STEPS)).toFixed(2));
const SLOTS = 4;

export function dashFor(progress: number): string {
  return DASH[Math.max(0, Math.min(DASH_STEPS, Math.round(progress * DASH_STEPS)))]!;
}

/**
 * The simulated downloads' clock. Progress lives here, not in React state: while a download
 * runs, one frame hook (in the site's single loop) moves the rings and the "seconds left" text
 * of whichever buttons show it, by writing preformatted strings into the elements registered
 * for that product. Nothing is allocated per frame; React renders only when a phase changes.
 */
export class DownloadClock {
  private readonly started: Float64Array;
  private readonly active: Uint8Array;
  private readonly lastDash: Int16Array;
  private readonly lastLeft: Int16Array;
  private readonly rings: (SVGCircleElement | null)[];
  private readonly clocks: (HTMLElement | null)[];
  private readonly ms: number;
  private left: string[] = [];
  private unhook: (() => void) | null = null;
  /** Called (outside any React updater) when a download completes. */
  onDone: (index: number) => void = () => {};

  constructor(
    private readonly n: number,
    seconds: number,
  ) {
    this.ms = seconds * 1000;
    this.started = new Float64Array(n);
    this.active = new Uint8Array(n);
    this.lastDash = new Int16Array(n).fill(-1);
    this.lastLeft = new Int16Array(n).fill(-1);
    this.rings = new Array<SVGCircleElement | null>(n * SLOTS).fill(null);
    this.clocks = new Array<HTMLElement | null>(n * SLOTS).fill(null);
    this.setLeftTemplate("{0}", seconds);
  }

  /** "{0} s left" in the page's language, preformatted for every tenth of a second. */
  setLeftTemplate(template: string, seconds = this.ms / 1000): void {
    const tenths = Math.ceil(seconds * 10);
    this.left = Array.from({ length: tenths + 1 }, (_, k) => template.replace("{0}", (k / 10).toFixed(1)));
  }

  progress(i: number): number {
    if (this.active[i] !== 1) return 0;
    return Math.min(1, (performance.now() - (this.started[i] ?? 0)) / this.ms);
  }

  leftText(i: number): string {
    const p = this.progress(i);
    return this.left[Math.max(0, Math.ceil((1 - p) * (this.left.length - 1)))] ?? "";
  }

  start(i: number): void {
    this.started[i] = performance.now();
    this.active[i] = 1;
    this.lastDash[i] = -1;
    this.lastLeft[i] = -1;
    if (this.unhook === null) this.unhook = addFrameHook(this.frame);
  }

  stop(i: number): void {
    this.active[i] = 0;
  }

  reset(): void {
    this.active.fill(0);
  }

  /** Registers an element showing product i's ring; returns its unregister function. */
  attachRing(i: number, el: SVGCircleElement): () => void {
    return this.attach(this.rings, i, el, () => el.setAttribute("stroke-dashoffset", dashFor(this.progress(i))));
  }

  attachClock(i: number, el: HTMLElement): () => void {
    return this.attach(this.clocks, i, el, () => {
      el.textContent = this.leftText(i);
    });
  }

  private attach<T extends Element>(slots: (T | null)[], i: number, el: T, paint: () => void): () => void {
    for (let s = 0; s < SLOTS; s++) {
      const k = i * SLOTS + s;
      if (slots[k] === null) {
        slots[k] = el;
        paint();
        return () => {
          if (slots[k] === el) slots[k] = null;
        };
      }
    }
    return () => {};
  }

  private readonly frame = (): void => {
    const now = performance.now();
    let running = 0;
    for (let i = 0; i < this.n; i++) {
      if (this.active[i] !== 1) continue;
      const p = (now - (this.started[i] ?? 0)) / this.ms;
      if (p >= 1) {
        this.active[i] = 0;
        this.onDone(i);
        continue;
      }
      running += 1;
      const dk = Math.round(p * DASH_STEPS);
      if (dk !== this.lastDash[i]) {
        this.lastDash[i] = dk;
        const d = DASH[dk]!;
        for (let s = 0; s < SLOTS; s++) this.rings[i * SLOTS + s]?.setAttribute("stroke-dashoffset", d);
      }
      const lk = Math.max(0, Math.ceil((1 - p) * (this.left.length - 1)));
      if (lk !== this.lastLeft[i]) {
        this.lastLeft[i] = lk;
        const text = this.left[lk] ?? "";
        for (let s = 0; s < SLOTS; s++) {
          const el = this.clocks[i * SLOTS + s];
          if (el) el.textContent = text;
        }
      }
    }
    if (running === 0 && this.unhook !== null) {
      this.unhook();
      this.unhook = null;
    }
  };

  dispose(): void {
    this.unhook?.();
    this.unhook = null;
    this.active.fill(0);
  }
}
