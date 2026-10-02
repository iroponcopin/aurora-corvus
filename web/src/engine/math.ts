import { Matrix4, Quaternion, Vector2, Vector3, Vector4 } from "three";

/**
 * Preallocated scratch objects for the frame loop. Each owner takes a named slot at module
 * load and reuses it every frame, so the loop itself never allocates. A slot is never shared
 * between two callers that can be live at the same time.
 */
export class Pool<T> {
  private readonly items: T[];
  private cursor = 0;

  constructor(make: () => T, size: number) {
    this.items = Array.from({ length: size }, make);
  }

  /** Reserve a permanent slot (call at module scope or in a constructor, never per frame). */
  take(): T {
    const item = this.items[this.cursor];
    if (item === undefined) throw new Error("Pool exhausted: raise its size");
    this.cursor += 1;
    return item;
  }
}

export const vec3Pool = new Pool(() => new Vector3(), 96);
export const vec2Pool = new Pool(() => new Vector2(), 16);
export const vec4Pool = new Pool(() => new Vector4(), 16);
export const quatPool = new Pool(() => new Quaternion(), 48);
export const mat4Pool = new Pool(() => new Matrix4(), 12);

/** Frame-rate independent exponential approach: the same feel at 30, 60 or 120 Hz. */
export function damp(current: number, target: number, lambda: number, dt: number): number {
  return current + (target - current) * (1 - Math.exp(-lambda * dt));
}

export function clamp(v: number, lo: number, hi: number): number {
  return v < lo ? lo : v > hi ? hi : v;
}

export function smoothstep(e0: number, e1: number, x: number): number {
  const t = clamp((x - e0) / (e1 - e0), 0, 1);
  return t * t * (3 - 2 * t);
}

export function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}

/** Critically damped spring (Unity's SmoothDamp), state kept by the caller in `vel[0]`. */
export function smoothDamp(
  current: number,
  target: number,
  vel: Float32Array,
  index: number,
  smoothTime: number,
  dt: number,
): number {
  const omega = 2 / Math.max(0.0001, smoothTime);
  const x = omega * dt;
  const exp = 1 / (1 + x + 0.48 * x * x + 0.235 * x * x * x);
  const change = current - target;
  const v = vel[index] ?? 0;
  const temp = (v + omega * change) * dt;
  vel[index] = (v - omega * temp) * exp;
  return target + (change + temp) * exp;
}

/**
 * Integrate an angular velocity (radians per second, world axes) into a quaternion in place:
 * q ← normalize(q + ½·dt·ω⊗q). No temporaries.
 */
export function integrateQuat(q: Quaternion, wx: number, wy: number, wz: number, dt: number): void {
  const h = 0.5 * dt;
  const qx = q.x;
  const qy = q.y;
  const qz = q.z;
  const qw = q.w;
  q.x = qx + h * (wx * qw + wy * qz - wz * qy);
  q.y = qy + h * (wy * qw + wz * qx - wx * qz);
  q.z = qz + h * (wz * qw + wx * qy - wy * qx);
  q.w = qw + h * (-wx * qx - wy * qy - wz * qz);
  q.normalize();
}

/** Deterministic hash in [0, 1) for build-time layout (not used per frame). */
export function hash01(n: number): number {
  const s = Math.sin(n * 127.1 + 311.7) * 43758.5453123;
  return s - Math.floor(s);
}
