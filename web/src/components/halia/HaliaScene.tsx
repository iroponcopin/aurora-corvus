"use client";

import { type ReactNode, type RefObject, useEffect, useMemo, useRef, useState } from "react";
import {
  AdditiveBlending,
  type BufferAttribute,
  type BufferGeometry,
  Color,
  DoubleSide,
  ExtrudeGeometry,
  type Group,
  type MeshStandardMaterial,
  type PointsMaterial,
  Shape,
} from "three";
import { damp } from "@/engine/math";
import { engine } from "@/engine/store";
import { Stage3D, useViewApi, useViewFrame } from "@/engine/View";

/** Halia's palette: feather white, sovereign gold, obsidian, crimson apex; Astraea's broken blue. */
const WHITE = "#F4F6FB";
const GOLD = "#FFB300";
const OBSIDIAN = "#16151D";
const OBSIDIAN_DEEP = "#0D0C10";
const CRIMSON = "#D90429";
const BROKEN_BLUE = "#3A506B";

const DEBRIS = 1600;
const SHELL = 1.7;
const FAR = 7.5;

/** What the scrollytelling and the pointer share between the page and the 3D view. */
export interface HaliaState {
  /** 0 at the top of the page, 1 when the end of the page is reached. */
  progress: number;
  /** Pointer position in -1..1 on both axes. */
  pointer: { x: number; y: number };
}

const clamp01 = (x: number): number => Math.min(1, Math.max(0, x));
const smooth = (a: number, b: number, x: number): number => {
  const t = clamp01((x - a) / (b - a));
  return t * t * (3 - 2 * t);
};

/** A small deterministic generator, so the particle field is the same on every visit. */
function seeded(seed: number): () => number {
  let s = seed;
  return () => {
    s = (s + 0x6d2b79f5) | 0;
    let t = Math.imul(s ^ (s >>> 15), 1 | s);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/**
 * Astraea's remnants: particles that were the shell of the old form leave it outward, cooling from pale
 * blue to the broken blue. The eagle's grasp at the end crushes them, so they fade out there.
 */
function AstraeaDebris({ state }: { state: RefObject<HaliaState> }) {
  const geo = useRef<BufferGeometry>(null);
  const mat = useRef<PointsMaterial>(null);
  const hot = useMemo(() => new Color("#9fb8d6"), []);
  const deep = useMemo(() => new Color(BROKEN_BLUE), []);
  const data = useMemo(() => {
    const rand = seeded(20261010);
    const pos = new Float32Array(DEBRIS * 3);
    const col = new Float32Array(DEBRIS * 3);
    const dir = new Float32Array(DEBRIS * 3);
    const dist = new Float32Array(DEBRIS);
    const speed = new Float32Array(DEBRIS);
    const aim = (i: number): void => {
      const u = rand() * 2 - 1;
      const a = rand() * Math.PI * 2;
      const s = Math.sqrt(1 - u * u);
      dir[i * 3] = s * Math.cos(a);
      dir[i * 3 + 1] = u;
      dir[i * 3 + 2] = s * Math.sin(a);
      dist[i] = SHELL + rand() * 0.5;
    };
    for (let i = 0; i < DEBRIS; i++) {
      aim(i);
      speed[i] = 0.25 + rand() * 0.9;
      const d = dist[i]!;
      pos[i * 3] = dir[i * 3]! * d;
      pos[i * 3 + 1] = dir[i * 3 + 1]! * d;
      pos[i * 3 + 2] = dir[i * 3 + 2]! * d;
      col[i * 3] = hot.r;
      col[i * 3 + 1] = hot.g;
      col[i * 3 + 2] = hot.b;
    }
    return { pos, col, dir, dist, speed, aim };
  }, [hot]);

  useViewFrame((dt) => {
    const g = geo.current;
    if (g === null) return;
    const k = engine.reducedMotion ? 0 : 1;
    const step = Math.min(dt, 0.05) * k;
    const { pos, col, dir, dist, speed, aim } = data;
    for (let i = 0; i < DEBRIS; i++) {
      if (step > 0) {
        dist[i] = dist[i]! + speed[i]! * step;
        if (dist[i]! > FAR) aim(i);
      }
      const d = dist[i]!;
      pos[i * 3] = dir[i * 3]! * d;
      pos[i * 3 + 1] = dir[i * 3 + 1]! * d;
      pos[i * 3 + 2] = dir[i * 3 + 2]! * d;
      const t = clamp01((d - SHELL) / (FAR - SHELL));
      const fade = 1 - t * t;
      col[i * 3] = (hot.r + (deep.r - hot.r) * t) * fade;
      col[i * 3 + 1] = (hot.g + (deep.g - hot.g) * t) * fade;
      col[i * 3 + 2] = (hot.b + (deep.b - hot.b) * t) * fade;
    }
    (g.attributes.position as BufferAttribute).needsUpdate = true;
    (g.attributes.color as BufferAttribute).needsUpdate = true;
    if (mat.current) mat.current.opacity = 0.9 * (1 - smooth(0.82, 0.98, state.current.progress));
  });

  return (
    <points>
      <bufferGeometry ref={geo}>
        <bufferAttribute attach="attributes-position" args={[data.pos, 3]} />
        <bufferAttribute attach="attributes-color" args={[data.col, 3]} />
      </bufferGeometry>
      <pointsMaterial
        ref={mat}
        size={0.04}
        vertexColors
        transparent
        opacity={0.9}
        sizeAttenuation
        depthWrite={false}
        blending={AdditiveBlending}
      />
    </points>
  );
}

/**
 * The bald eagle's poses along the scroll: where it is, how it is tilted, how far its wings are raised
 * (radians) and how far its talons open (0 closed, 1 open).
 * 0.0 gliding at the zenith · 0.3 the dive · 0.6 the spread wings that brake · 0.9 the grasp · 1.0 perched.
 */
interface Pose {
  p: number;
  pos: readonly [number, number, number];
  rot: readonly [number, number, number];
  spread: number;
  talon: number;
}

const POSES: readonly Pose[] = [
  { p: 0.0, pos: [-0.3, 1.0, 0], rot: [0.1, 0.5, -0.45], spread: 0.5, talon: 0 },
  { p: 0.3, pos: [0.2, -0.3, 0.9], rot: [2.2, 0, 0.25], spread: -0.2, talon: 0 },
  { p: 0.6, pos: [0, 0.3, 0.8], rot: [0, 0, 0], spread: 1.05, talon: 0.3 },
  { p: 0.9, pos: [0.4, -0.6, 0.6], rot: [0, 0, -0.15], spread: 0.7, talon: 1 },
  { p: 1.0, pos: [0, 0.5, 0.2], rot: [0, 0.25, 0], spread: 0.12, talon: 0.6 },
];

function poseAt(p: number): Pose {
  const first = POSES[0]!;
  const last = POSES[POSES.length - 1]!;
  if (p <= first.p) return first;
  if (p >= last.p) return last;
  let i = 0;
  while (POSES[i + 1]!.p < p) i++;
  const a = POSES[i]!;
  const b = POSES[i + 1]!;
  const u = (p - a.p) / (b.p - a.p);
  const e = u * u * (3 - 2 * u);
  const L = (x: number, y: number): number => x + (y - x) * e;
  return {
    p,
    pos: [L(a.pos[0], b.pos[0]), L(a.pos[1], b.pos[1]), L(a.pos[2], b.pos[2])],
    rot: [L(a.rot[0], b.rot[0]), L(a.rot[1], b.rot[1]), L(a.rot[2], b.rot[2])],
    spread: L(a.spread, b.spread),
    talon: L(a.talon, b.talon),
  };
}

/** A feather-serrated wing, drawn outward from the shoulder; `mirror` gives the other side. */
const WING: readonly (readonly [number, number])[] = [
  [0, 0.25], [4.0, 0.35], [4.4, -0.2], [3.6, -0.1], [3.4, -0.7], [2.8, -0.2],
  [2.4, -0.9], [1.8, -0.3], [1.2, -0.6], [0.6, -0.2], [0, -0.3],
];
const TAIL: readonly (readonly [number, number])[] = [
  [-0.7, 0], [0.7, 0], [1.1, -1.5], [0.6, -1.9], [0, -1.55], [-0.6, -1.9], [-1.1, -1.5],
];

function flatPanel(points: readonly (readonly [number, number])[], mirror: 1 | -1): ExtrudeGeometry {
  const s = new Shape();
  points.forEach(([x, y], i) => (i === 0 ? s.moveTo(mirror * x, y) : s.lineTo(mirror * x, y)));
  s.closePath();
  return new ExtrudeGeometry(s, { depth: 0.1, bevelEnabled: false });
}

/**
 * The bald eagle, modelled procedurally in low poly: an obsidian body, a white head, a gold hooked beak
 * and eyes, serrated wings on shoulder pivots, a white fan tail and gold talons. Its pose follows the
 * scroll, its head follows the pointer, and its wings beat gently until the grasp.
 */
function Eagle({ state }: { state: RefObject<HaliaState> }) {
  const root = useRef<Group>(null);
  const wingL = useRef<Group>(null);
  const wingR = useRef<Group>(null);
  const footL = useRef<Group>(null);
  const footR = useRef<Group>(null);
  const head = useRef<Group>(null);
  const perch = useRef<MeshStandardMaterial>(null);
  const clock = useRef(0);
  const wingGeoL = useMemo(() => flatPanel(WING, 1), []);
  const wingGeoR = useMemo(() => flatPanel(WING, -1), []);
  const tailGeo = useMemo(() => flatPanel(TAIL, 1), []);

  useViewFrame((dt) => {
    const s = state.current;
    const r = root.current;
    if (r === null) return;
    const k = engine.reducedMotion ? 0 : 1;
    const step = Math.min(dt, 0.05);
    clock.current += step * k;
    const pose = poseAt(s.progress);
    const beat = Math.sin(clock.current * 2.5) * 0.08 * k * (s.progress < 0.9 ? 1 : 0.3);

    r.position.set(pose.pos[0], pose.pos[1], pose.pos[2]);
    r.rotation.set(pose.rot[0] + Math.sin(clock.current * 0.6) * 0.03 * k, pose.rot[1], pose.rot[2]);
    if (wingL.current) wingL.current.rotation.z = pose.spread + beat;
    if (wingR.current) wingR.current.rotation.z = -(pose.spread + beat);
    if (footL.current) footL.current.rotation.x = pose.talon * 0.9;
    if (footR.current) footR.current.rotation.x = pose.talon * 0.9;
    if (head.current) {
      head.current.rotation.y = damp(head.current.rotation.y, s.pointer.x * 0.5 * k, 6, step);
      head.current.rotation.x = damp(head.current.rotation.x, s.pointer.y * 0.3 * k, 6, step);
    }
    if (perch.current) perch.current.opacity = smooth(0.82, 0.98, s.progress);
  });

  return (
    <>
      <group ref={root} scale={0.62}>
        {/* body */}
        <mesh>
          <cylinderGeometry args={[0.42, 0.7, 2.4, 7]} />
          <meshStandardMaterial color={OBSIDIAN} flatShading roughness={0.6} metalness={0.2} />
        </mesh>

        {/* head, beak and eyes */}
        <group ref={head} position={[0, 1.5, 0]}>
          <mesh scale={[0.9, 1, 1.05]}>
            <dodecahedronGeometry args={[0.55, 0]} />
            <meshStandardMaterial color={WHITE} flatShading roughness={0.35} />
          </mesh>
          <mesh position={[0, -0.05, 0.55]} rotation={[Math.PI / 2 + 0.35, 0, 0]}>
            <coneGeometry args={[0.16, 0.5, 4]} />
            <meshStandardMaterial color={GOLD} flatShading metalness={0.7} roughness={0.25} />
          </mesh>
          <mesh position={[0.22, 0.12, 0.42]}>
            <sphereGeometry args={[0.07, 8, 8]} />
            <meshBasicMaterial color={GOLD} />
          </mesh>
          <mesh position={[-0.22, 0.12, 0.42]}>
            <sphereGeometry args={[0.07, 8, 8]} />
            <meshBasicMaterial color={GOLD} />
          </mesh>
        </group>

        {/* wings, on shoulder pivots */}
        <group ref={wingL} position={[0.45, 0.55, 0]}>
          <mesh geometry={wingGeoL}>
            <meshStandardMaterial color={OBSIDIAN} flatShading side={DoubleSide} roughness={0.6} metalness={0.2} />
          </mesh>
        </group>
        <group ref={wingR} position={[-0.45, 0.55, 0]}>
          <mesh geometry={wingGeoR}>
            <meshStandardMaterial color={OBSIDIAN} flatShading side={DoubleSide} roughness={0.6} metalness={0.2} />
          </mesh>
        </group>

        {/* fan tail */}
        <mesh geometry={tailGeo} position={[0, -1.1, -0.05]}>
          <meshStandardMaterial color={WHITE} flatShading side={DoubleSide} roughness={0.35} />
        </mesh>

        {/* talons: three toes each, opening with the grasp */}
        <group ref={footL} position={[0.3, -1.25, 0.15]}>
          {[-0.12, 0, 0.12].map((tx) => (
            <mesh key={tx} position={[tx, -0.25, 0.05]} rotation={[0.2, 0, -tx * 2]}>
              <coneGeometry args={[0.07, 0.5, 4]} />
              <meshStandardMaterial color={GOLD} flatShading metalness={0.7} roughness={0.25} />
            </mesh>
          ))}
        </group>
        <group ref={footR} position={[-0.3, -1.25, 0.15]}>
          {[-0.12, 0, 0.12].map((tx) => (
            <mesh key={tx} position={[tx, -0.25, 0.05]} rotation={[0.2, 0, -tx * 2]}>
              <coneGeometry args={[0.07, 0.5, 4]} />
              <meshStandardMaterial color={GOLD} flatShading metalness={0.7} roughness={0.25} />
            </mesh>
          ))}
        </group>
      </group>

      {/* the perch, which appears once the eagle has taken it */}
      <mesh position={[0, -0.3, 0.1]} rotation={[0, 0, Math.PI / 2]}>
        <cylinderGeometry args={[0.07, 0.07, 4.6, 8]} />
        <meshStandardMaterial ref={perch} color={OBSIDIAN_DEEP} flatShading transparent opacity={0} />
      </mesh>
    </>
  );
}

/** The eagle's aura: a faint crimson halo behind it. */
function Halo() {
  return (
    <mesh>
      <sphereGeometry args={[3.2, 24, 24]} />
      <meshBasicMaterial color={CRIMSON} transparent opacity={0.06} blending={AdditiveBlending} depthWrite={false} />
    </mesh>
  );
}

/** Lights for the eagle's view: a gold key from above and in front, a crimson rim from behind. */
function Lights() {
  return (
    <>
      <ambientLight intensity={0.55} />
      <directionalLight color={GOLD} intensity={2.2} position={[4, 6, 6]} />
      <directionalLight color={CRIMSON} intensity={2.5} position={[-5, -2, -4]} />
    </>
  );
}

/**
 * Each frame: reads how far the page has been scrolled (0 at the top, 1 at the end of the page) and moves
 * the camera towards the pointer for the parallax.
 */
function ScrollSync({ root, state }: { root: RefObject<HTMLElement | null>; state: RefObject<HaliaState> }) {
  const api = useViewApi();

  useEffect(() => {
    const move = (e: PointerEvent): void => {
      state.current.pointer.x = (e.clientX / window.innerWidth) * 2 - 1;
      state.current.pointer.y = (e.clientY / window.innerHeight) * 2 - 1;
    };
    window.addEventListener("pointermove", move, { passive: true });
    return () => window.removeEventListener("pointermove", move);
  }, [state]);

  useViewFrame((dt) => {
    const el = root.current;
    const s = state.current;
    if (el !== null) {
      const r = el.getBoundingClientRect();
      s.progress = clamp01(-r.top / Math.max(1, r.height - window.innerHeight));
    }
    const cam = api.camera;
    const k = engine.reducedMotion ? 0 : 1;
    const step = Math.min(dt, 0.05);
    cam.position.x = damp(cam.position.x, s.pointer.x * 1.1 * k, 3, step);
    cam.position.y = damp(cam.position.y, 0.1 - s.pointer.y * 0.6 * k, 3, step);
    cam.lookAt(0, 0, 0);
  });
  return null;
}

/** Moves the whole scene to the right of the copy on wide screens, and above it on narrow ones. */
function SceneOffset({ children }: { children: ReactNode }) {
  const group = useRef<Group>(null);
  useViewFrame((dt) => {
    const g = group.current;
    if (g === null) return;
    const narrow = window.innerWidth < 760;
    const step = Math.min(dt, 0.05);
    g.position.x = damp(g.position.x, narrow ? 0 : 3.3, 4, step);
    g.position.y = damp(g.position.y, narrow ? 2.0 : 0, 4, step);
    g.scale.setScalar(damp(g.scale.x, narrow ? 0.7 : 1, 4, step));
  });
  return <group ref={group}>{children}</group>;
}

/**
 * The Halia view: the bald eagle, scroll-linked, over Astraea's remnants. Without WebGL, the fallback
 * sentence stands in for it.
 */
export function HaliaScene({
  label,
  fallback,
  root,
  state,
}: {
  label: string;
  fallback: string;
  root: RefObject<HTMLElement | null>;
  state: RefObject<HaliaState>;
}) {
  return (
    <Stage3D
      className="ac-halia-stage"
      label={label}
      fov={34}
      position={[0, 0.1, 13]}
      fallback={<p className="ac-halia-nogl">{fallback}</p>}
    >
      <Lights />
      <ScrollSync root={root} state={state} />
      <SceneOffset>
        <Halo />
        <Eagle state={state} />
        <AstraeaDebris state={state} />
      </SceneOffset>
    </Stage3D>
  );
}

const TELEMETRY = [
  "FABRIC // MINECRAFT 26.3",
  "VOLUMETRIC CARVING ACTIVE",
  "ASTRAEA // OVERRIDDEN",
  "APEX // SOVEREIGN",
  "STATUS // PRE-RELEASE",
];

/** The HUD readout in the corner: fixed lines, and a clock counting from the moment the page opened. */
export function HaliaTelemetry() {
  const [sec, setSec] = useState(0);
  useEffect(() => {
    const start = performance.now();
    const id = window.setInterval(() => setSec(Math.floor((performance.now() - start) / 1000)), 1000);
    return () => window.clearInterval(id);
  }, []);
  const pad = (n: number): string => String(n).padStart(2, "0");
  const clock = `T+ ${pad(Math.floor(sec / 3600))}:${pad(Math.floor((sec % 3600) / 60))}:${pad(sec % 60)}`;
  return (
    <ul className="ac-halia-hud" aria-hidden="true">
      {TELEMETRY.map((line) => (
        <li key={line}>{line}</li>
      ))}
      <li className="ac-halia-clock">{clock}</li>
    </ul>
  );
}

/**
 * The Halia page's frame. A sticky stage holds the eagle for the whole page, and the sections scroll over
 * it, so the eagle's pose follows how far the reader has come.
 */
export function HaliaFrame({ label, fallback, children }: { label: string; fallback: string; children: ReactNode }) {
  const root = useRef<HTMLDivElement>(null);
  const state = useRef<HaliaState>({ progress: 0, pointer: { x: 0, y: 0 } });
  return (
    <div className="ac-halia" ref={root}>
      <div className="ac-halia-sticky">
        <div className="ac-halia-shatter" aria-hidden="true">
          <span className="ac-halia-shard" />
          <span className="ac-halia-shard" />
          <span className="ac-halia-shard" />
        </div>
        <HaliaScene label={label} fallback={fallback} root={root} state={state} />
        <HaliaTelemetry />
      </div>
      <div className="ac-halia-flow">{children}</div>
    </div>
  );
}
