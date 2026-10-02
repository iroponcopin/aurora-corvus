/**
 * The engine's live state: one plain, mutable object read and written from the frame loop.
 *
 * Nothing here is React state. A frame never causes a render, and nothing in the loop
 * allocates: every field is a number (or a preallocated typed array) written in place.
 */

/** Particle formations, in the order the simulation shader's `formation()` switch knows them. */
export const Formation = {
  Horizon: 0,
  Codex: 1,
  Showroom: 2,
  Store: 3,
  Chronology: 4,
  Nexus: 5,
  Bloom: 6,
  Aurum: 7,
  Ember: 8,
} as const;
export type FormationId = (typeof Formation)[keyof typeof Formation];

export const engine = {
  /** Seconds since the engine started (monotonic, frame-rate independent). */
  time: 0,
  /** Seconds since the previous frame, clamped to [1/240, 1/20]. */
  dt: 1 / 60,
  frame: 0,

  /** Lenis' animated scroll position, in CSS pixels, and its velocity (px per frame at 60 Hz). */
  scrollY: 0,
  scrollVelocity: 0,
  scrollLimit: 1,
  /** |velocity| through a critically damped follower, normalised to roughly 0..1. */
  energy: 0,

  /** Pointer in CSS pixels, in normalised device coordinates (-1..1, y up), and smoothed. */
  pointerX: 0,
  pointerY: 0,
  pointerNX: 0,
  pointerNY: 0,
  pointerSX: 0,
  pointerSY: 0,
  pointerInside: 0,
  /** Seconds of the last pointer movement; the cursor light fades after a while without one. */
  pointerLastMove: -10,

  /** Viewport in CSS pixels and the device pixel ratio actually used by the renderer. */
  width: 1,
  height: 1,
  dpr: 1,

  /** Particle formation blend: A → B by `morph` (0..1). `scrub` means scroll owns the morph. */
  formationA: Formation.Horizon as number,
  formationB: Formation.Horizon as number,
  morph: 1,
  morphTarget: 1,
  scrub: false,

  /** Where the active formation is anchored on screen (CSS px), and how deep in the scene. */
  anchorX: 0.5,
  anchorY: 0.5,
  anchorDepth: 0,
  anchorScale: 1,

  /** Hero astrolabe presence (0 hidden .. 1 fully present) and its screen anchor. */
  astrolabe: 1,
  astrolabeTarget: 1,

  /** Brand tint of the light (linear RGB), blended per page. */
  tintR: 0.36,
  tintG: 0.62,
  tintB: 1,
  tintTargetR: 0.36,
  tintTargetG: 0.62,
  tintTargetB: 1,

  /** Starlight burst (recipe fusion, unlock): origin in world space, start time, strength. */
  burstX: 0,
  burstY: 0,
  burstZ: 0,
  burstTime: -100,
  burstStrength: 0,

  /** Chronology camera: when `splineWeight` > 0 the camera rides the orbital spline at `splineT`. */
  splineT: 0,
  splineWeight: 0,
  splineWeightTarget: 0,

  /** Loudness of the music playing on the page (the OUKA theme), 0..1, smoothed. */
  music: 0,
  /** -1 when the document is right-to-left: X positions of paths and layouts are mirrored. */
  mirror: 1,
  reducedMotion: false,
  /** Adaptive quality: 1 = full. The particle draw range and DPR follow it. */
  quality: 1,
  /** Draw calls and triangles of the last frame (read by the debug overlay and the tests). */
  drawCalls: 0,
  triangles: 0,
  /** Frames whose CPU time exceeded the refresh budget; reset by the debug overlay. */
  longFrames: 0,
  /** Smoothed CPU milliseconds per frame spent in the engine (sim + render submission). */
  cpuMs: 0,
  /** Estimated display refresh interval in ms (8.3 on ProMotion, 16.7 at 60 Hz). */
  refreshMs: 16.7,
  /** 1 once the WebGL context is up and the first frame has been drawn. */
  ready: 0,
};

export type Engine = typeof engine;

/** Request a starlight burst at a world-space point (used by the synthesiser and the skin unlock). */
export function burst(x: number, y: number, z: number, strength = 1): void {
  engine.burstX = x;
  engine.burstY = y;
  engine.burstZ = z;
  engine.burstTime = engine.time;
  engine.burstStrength = strength;
}

/** Move the particles to a new formation with a timed (not scroll-scrubbed) morph. */
export function setFormation(next: number): void {
  if (engine.scrub) engine.scrub = false;
  if (next === engine.formationB && engine.morphTarget === 1) return;
  // Keep whichever formation dominates right now as the origin of the new transition.
  engine.formationA = engine.morph >= 0.5 ? engine.formationB : engine.formationA;
  engine.formationB = next;
  engine.morph = 0;
  engine.morphTarget = 1;
}

/** Let scroll own the morph between two formations (the home page's realms). */
export function scrubFormation(a: number, b: number, t: number): void {
  engine.scrub = true;
  engine.formationA = a;
  engine.formationB = b;
  engine.morph = t < 0 ? 0 : t > 1 ? 1 : t;
  engine.morphTarget = engine.morph;
}

export function setTint(r: number, g: number, b: number): void {
  engine.tintTargetR = r;
  engine.tintTargetG = g;
  engine.tintTargetB = b;
}
