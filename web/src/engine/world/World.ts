import { Group, type PerspectiveCamera, type Vector3, type WebGLRenderer } from "three";
import { direct, direction } from "../anchors";
import { clamp, damp, vec3Pool } from "../math";
import { engine } from "../store";
import { updateTracked } from "../tracked";
import { Astrolabe } from "./Astrolabe";
import { Chrono, chronoPath } from "./Chrono";
import { Marks } from "./Marks";
import { Nebula } from "./Nebula";
import { Starfield } from "./Starfield";
import { createSharedUniforms, type SharedUniforms } from "./uniforms";

/** The fixed camera rig: where the world is seen from when no realm asks for a flight. */
const REST = { x: 0, y: 0, z: 16, fov: 38 };

/**
 * Everything the persistent canvas draws behind the page, and the order it is updated in:
 * layout → direction → camera → anchors → simulation → instruments. All per-frame state lives
 * in preallocated objects; `frame()` allocates nothing.
 */
export class World {
  readonly root = new Group();
  readonly shared: SharedUniforms;
  readonly nebula: Nebula;
  readonly starfield: Starfield;
  readonly astrolabe: Astrolabe;
  readonly marks: Marks;
  readonly chrono: Chrono;

  private readonly anchorA = vec3Pool.take();
  private readonly anchorB = vec3Pool.take();
  private readonly astroCenter = vec3Pool.take();
  private readonly rayOrigin = vec3Pool.take();
  private readonly rayDir = vec3Pool.take();
  private readonly tmp = vec3Pool.take();
  private readonly camPos = vec3Pool.take();
  private readonly camLook = vec3Pool.take();
  private readonly splinePos = vec3Pool.take();
  private readonly splineLook = vec3Pool.take();
  private readonly light = vec3Pool.take();
  private readonly frameData = {
    anchorA: this.anchorA,
    anchorB: this.anchorB,
    scaleA: 3,
    scaleB: 3,
    rayOrigin: this.rayOrigin,
    rayDir: this.rayDir,
    pointerForce: 0,
    viewportHeight: 800,
    fovScale: 1,
  };
  private astroScaleSmoothed = 3;
  private astroReady = false;
  private pointerForce = 0;

  constructor(gl: WebGLRenderer) {
    this.shared = createSharedUniforms();
    this.nebula = new Nebula(this.shared);
    this.starfield = new Starfield(gl, this.shared);
    this.astrolabe = new Astrolabe(this.shared);
    this.marks = new Marks(this.shared);
    this.chrono = new Chrono(this.shared);
    this.root.add(this.nebula.mesh, this.starfield.points, this.astrolabe.group, this.marks.mesh, this.chrono.mesh);
  }

  /** World point under a screen point (CSS px) on the plane z = depth. Writes into `out`. */
  screenToPlane(camera: PerspectiveCamera, x: number, y: number, depth: number, w: number, h: number, out: Vector3): Vector3 {
    out.set((x / w) * 2 - 1, -(y / h) * 2 + 1, 0.5).unproject(camera);
    out.sub(camera.position).normalize();
    const t = Math.abs(out.z) < 1e-5 ? 0 : (depth - camera.position.z) / out.z;
    return out.multiplyScalar(t).add(camera.position);
  }

  /** The visible world size at the rest distance this frame (for fitScale, without a closure). */
  private fitH = 1;
  private fitW = 1;

  /** A formation radius given as a fraction of the visible height, kept inside the width too. */
  private fitScale(frac: number): number {
    return Math.min(frac * this.fitH, frac * this.fitW * 1.25);
  }

  /** Visible world height at a distance from the camera. */
  private visibleHeight(camera: PerspectiveCamera, distance: number): number {
    return 2 * Math.abs(distance) * Math.tan((camera.fov * Math.PI) / 360);
  }

  frame(camera: PerspectiveCamera, w: number, h: number): void {
    const dt = engine.dt;
    const s = this.shared;

    // Layout, then the realms' decision for this frame.
    updateTracked(engine.scrollY, w, h);
    direct(w, h);

    // Smoothed inputs.
    engine.pointerSX = damp(engine.pointerSX, engine.pointerNX, 4.5, dt);
    engine.pointerSY = damp(engine.pointerSY, engine.pointerNY, 4.5, dt);
    const speed = Math.min(1, Math.abs(engine.scrollVelocity) / 45);
    engine.energy = damp(engine.energy, speed, speed > engine.energy ? 8 : 2.2, dt);
    if (!engine.scrub) engine.morph = damp(engine.morph, engine.morphTarget, 1.1, dt);
    if (!engine.scrub && engine.morph > 0.999) engine.morph = 1;
    engine.tintR = damp(engine.tintR, engine.tintTargetR, 2, dt);
    engine.tintG = damp(engine.tintG, engine.tintTargetG, 2, dt);
    engine.tintB = damp(engine.tintB, engine.tintTargetB, 2, dt);
    engine.splineWeight = damp(engine.splineWeight, engine.splineWeightTarget, 3.5, dt);
    s.uTime.value = engine.time;
    s.uTint.value.set(engine.tintR, engine.tintG, engine.tintB);
    // Music on the page (the OUKA theme) drives the same energy the scroll does.
    s.uEnergy.value = Math.max(engine.energy, engine.music * 0.9);
    s.uMirror.value = engine.mirror;

    // Camera: the rest pose with parallax, blended with the flight along the path of time.
    const calm = engine.reducedMotion ? 0.2 : 1;
    this.camPos.set(REST.x + engine.pointerSX * 0.55 * calm, REST.y + engine.pointerSY * 0.32 * calm, REST.z - engine.energy * 0.9 * calm);
    this.camLook.set(0, 0, 0);
    const sw = engine.splineWeight;
    if (sw > 0.001) {
      const u = clamp(engine.splineT, 0, 0.98);
      chronoPath(u, this.splinePos);
      chronoPath(u + 0.03, this.splineLook);
      this.splinePos.x *= engine.mirror;
      this.splineLook.x *= engine.mirror;
      this.splinePos.y += 1.1;
      this.splinePos.x += 0.6 * engine.mirror + engine.pointerSX * 0.4;
      this.splinePos.z += 4.2;
      this.camPos.lerp(this.splinePos, sw);
      this.camLook.lerp(this.splineLook, sw);
    }
    camera.position.copy(this.camPos);
    camera.lookAt(this.camLook);
    if (camera.fov !== REST.fov) {
      camera.fov = REST.fov;
      camera.updateProjectionMatrix();
    }
    camera.updateMatrixWorld();

    // Formation anchors: where on screen (and how big) each realm's matter gathers.
    const dist = REST.z;
    const vh = this.visibleHeight(camera, dist);
    const vw = vh * (w / Math.max(1, h));
    this.fitH = vh;
    this.fitW = vw;
    const d = direction;
    if (d.aIndex >= 0) {
      if (d.aWorld) this.anchorA.set(0, 0, 0);
      else this.screenToPlane(camera, d.ax, d.ay, d.aDepth, w, h, this.anchorA);
      if (d.bWorld) this.anchorB.set(0, 0, 0);
      else this.screenToPlane(camera, d.bx, d.by, d.bDepth, w, h, this.anchorB);
      this.frameData.scaleA = d.aWorld ? 1 : this.fitScale(d.aScale);
      this.frameData.scaleB = d.bWorld ? 1 : this.fitScale(d.bScale);
    }

    // The cursor: a ray for the particles and a light for the metal and the stones.
    this.rayOrigin.copy(camera.position);
    this.screenToPlane(camera, engine.pointerX, engine.pointerY, 0, w, h, this.tmp);
    this.rayDir.copy(this.tmp).sub(camera.position).normalize();
    const idle = engine.time - engine.pointerLastMove;
    const live = engine.pointerInside > 0 && idle < 2.5 ? 1 : 0;
    this.pointerForce = damp(this.pointerForce, live, live ? 6 : 1.5, dt);
    this.frameData.pointerForce = this.pointerForce * (engine.reducedMotion ? 0.3 : 1);
    // Light: at the cursor in front of the instrument; orbiting by itself when the cursor rests.
    this.screenToPlane(camera, engine.pointerX, engine.pointerY, 4.5, w, h, this.tmp);
    const t = engine.time;
    this.light.set(Math.cos(t * 0.31) * 6, 3.2 + Math.sin(t * 0.23) * 1.5, 7);
    this.light.lerp(this.tmp, this.pointerForce);
    s.uLightPos.value.lerp(this.light, 1 - Math.exp(-6 * dt));

    // Simulation.
    this.frameData.viewportHeight = h;
    this.frameData.fovScale = 1 / (2 * Math.tan((camera.fov * Math.PI) / 360));
    this.starfield.step(this.frameData, dt);

    // Instruments.
    if (d.astrolabe > 0 || this.astrolabe.presenceValue > 0.002) {
      this.screenToPlane(camera, d.astroX, d.astroY, 0, w, h, this.tmp);
      const target = this.fitScale(d.astroScale);
      if (!this.astroReady) {
        this.astroCenter.copy(this.tmp);
        this.astroScaleSmoothed = target;
        this.astroReady = true;
      }
      // Follow the hero exactly (it is glued to the DOM); scale eases to the breakpoint.
      this.astroCenter.copy(this.tmp);
      this.astroScaleSmoothed = damp(this.astroScaleSmoothed, target, 6, dt);
    }
    this.astrolabe.update(dt, this.astroCenter, this.astroScaleSmoothed, d.astrolabe, w, h);
    this.marks.update(dt, this.astroCenter, this.astroScaleSmoothed, d.astrolabe, camera, w, h);
    this.chrono.update(dt);
    this.nebula.update(dt, w, h);
  }

  dispose(): void {
    this.nebula.dispose();
    this.starfield.dispose();
    this.astrolabe.dispose();
    this.marks.dispose();
    this.chrono.dispose();
  }
}

let current: World | null = null;

export function setWorld(w: World | null): void {
  current = w;
}

/** The live world (null before the canvas is up, or without WebGL). For DOM-side picking. */
export function getWorld(): World | null {
  return current;
}

