import {
  CanvasTexture,
  InstancedBufferAttribute,
  InstancedMesh,
  type IUniform,
  LinearMipmapLinearFilter,
  Matrix4,
  type PerspectiveCamera,
  Quaternion,
  ShaderMaterial,
  SRGBColorSpace,
  Vector2,
  Vector3,
} from "three";
import { RoundedBoxGeometry } from "three/addons/geometries/RoundedBoxGeometry.js";
import { MARK_FRAGMENT, MARK_VERTEX } from "../shaders/nebula";
import { damp } from "../math";
import { engine } from "../store";
import type { SharedUniforms } from "./uniforms";

export const MAX_MARKS = 8;
const COLS = 4;
const ROWS = 2;
const CELL = 256;

/**
 * The brand marks orbiting the astrolabe: one instanced draw of rounded glass tiles, their
 * faces cut from a runtime atlas of the official icons. Each frame their screen positions are
 * written to `screen` so the DOM can pick them without a raycaster (and without allocating).
 */
export class Marks {
  readonly mesh: InstancedMesh;
  /** Per mark: screen x, y (CSS px), pick radius (px), depth (0 hidden). */
  readonly screen = new Float32Array(MAX_MARKS * 4);
  count = 0;
  hovered = -1;
  private readonly hover = new Float32Array(MAX_MARKS);
  private readonly hoverAttr: InstancedBufferAttribute;
  private readonly cellAttr: InstancedBufferAttribute;
  private readonly material: ShaderMaterial;
  private readonly atlas: CanvasTexture | null;
  private readonly canvas: HTMLCanvasElement | null;
  private readonly presence: IUniform<number> = { value: 0 };
  private readonly ready: IUniform<number> = { value: 0 };
  private readonly m = new Matrix4();
  private readonly q = new Quaternion();
  private readonly p = new Vector3();
  private readonly s = new Vector3();
  private readonly look = new Matrix4();
  private readonly up = new Vector3(0, 1, 0);
  private readonly proj = new Vector3();
  private loadToken = 0;

  constructor(shared: SharedUniforms) {
    const geometry = new RoundedBoxGeometry(1, 1, 0.14, 4, 0.2);
    this.canvas = typeof document !== "undefined" ? document.createElement("canvas") : null;
    if (this.canvas) {
      this.canvas.width = COLS * CELL;
      this.canvas.height = ROWS * CELL;
      this.atlas = new CanvasTexture(this.canvas);
      this.atlas.colorSpace = SRGBColorSpace;
      this.atlas.minFilter = LinearMipmapLinearFilter;
      this.atlas.anisotropy = 4;
    } else {
      this.atlas = null;
    }
    this.material = new ShaderMaterial({
      vertexShader: MARK_VERTEX,
      fragmentShader: MARK_FRAGMENT,
      uniforms: {
        uAtlas: { value: this.atlas },
        uAtlasGrid: { value: new Vector2(COLS, ROWS) },
        uTint: shared.uTint,
        uLightPos: shared.uLightPos,
        uPresence: this.presence,
        uReady: this.ready,
      },
      transparent: true,
    });
    this.mesh = new InstancedMesh(geometry, this.material, MAX_MARKS);
    this.mesh.count = 0;
    this.mesh.frustumCulled = false;
    this.mesh.renderOrder = 3;
    this.cellAttr = new InstancedBufferAttribute(new Float32Array(MAX_MARKS), 1);
    this.hoverAttr = new InstancedBufferAttribute(this.hover, 1);
    geometry.setAttribute("aCell", this.cellAttr);
    geometry.setAttribute("aHover", this.hoverAttr);
  }

  /** Load the icons (absolute URLs) into the atlas. Called when the page's marks change. */
  setIcons(urls: readonly string[]): void {
    const n = Math.min(urls.length, MAX_MARKS);
    this.count = n;
    this.mesh.count = n;
    for (let i = 0; i < n; i++) this.cellAttr.setX(i, i);
    this.cellAttr.needsUpdate = true;
    const ctx = this.canvas?.getContext("2d");
    if (!ctx || !this.atlas) return;
    const token = ++this.loadToken;
    this.ready.value = 0;
    let pending = n;
    ctx.clearRect(0, 0, COLS * CELL, ROWS * CELL);
    urls.slice(0, n).forEach((url, i) => {
      const img = new Image();
      img.decoding = "async";
      img.onload = () => {
        if (token !== this.loadToken) return;
        ctx.drawImage(img, (i % COLS) * CELL, Math.floor(i / COLS) * CELL, CELL, CELL);
        pending -= 1;
        if (pending === 0 && this.atlas) {
          this.atlas.needsUpdate = true;
          this.ready.value = 1;
        }
      };
      img.onerror = () => {
        pending -= 1;
      };
      img.src = url;
    });
  }

  update(
    dt: number,
    center: Vector3,
    radius: number,
    presenceTarget: number,
    camera: PerspectiveCamera,
    viewportW: number,
    viewportH: number,
  ): void {
    this.presence.value = damp(this.presence.value, presenceTarget, 3, dt);
    this.mesh.visible = this.presence.value > 0.002 && this.count > 0;
    if (!this.mesh.visible) {
      for (let i = 0; i < MAX_MARKS; i++) this.screen[i * 4 + 3] = 0;
      return;
    }
    const t = engine.time * (engine.reducedMotion ? 0.15 : 1);
    const n = this.count;
    for (let i = 0; i < n; i++) {
      const target = i === this.hovered ? 1 : 0;
      this.hover[i] = damp(this.hover[i] ?? 0, target, 10, dt);
      const a = (i / n) * Math.PI * 2 + t * 0.07;
      // An inclined orbit just outside the limb.
      const ox = Math.cos(a) * 1.42;
      const oz = Math.sin(a) * 1.42;
      const oy = Math.sin(a * 2 + 0.6) * 0.06;
      const tilt = 0.34;
      const y = oy * Math.cos(tilt) - oz * Math.sin(tilt);
      const z = oy * Math.sin(tilt) + oz * Math.cos(tilt);
      this.p.set(center.x + ox * radius * engine.mirror, center.y + y * radius, center.z + z * radius);
      // Face the viewer, with a slow sway so the glass edges catch the light.
      this.look.lookAt(camera.position, this.p, this.up);
      this.q.setFromRotationMatrix(this.look);
      const size = radius * 0.22 * (1 + (this.hover[i] ?? 0) * 0.16);
      this.s.set(size, size, size);
      this.m.compose(this.p, this.q, this.s);
      this.mesh.setMatrixAt(i, this.m);

      this.proj.copy(this.p).project(camera);
      const k = i * 4;
      this.screen[k] = (this.proj.x * 0.5 + 0.5) * viewportW;
      this.screen[k + 1] = (-this.proj.y * 0.5 + 0.5) * viewportH;
      // Pick radius: the tile's half size in pixels at its depth.
      const dist = camera.position.distanceTo(this.p);
      const pxPerUnit = viewportH / (2 * Math.tan((camera.fov * Math.PI) / 360) * dist);
      this.screen[k + 2] = size * 0.6 * pxPerUnit;
      this.screen[k + 3] = this.proj.z < 1 ? this.presence.value : 0;
    }
    this.mesh.instanceMatrix.needsUpdate = true;
    this.hoverAttr.needsUpdate = true;
  }

  /** The mark under a screen point (CSS px), or -1. */
  pick(x: number, y: number): number {
    let best = -1;
    let bestD = Infinity;
    for (let i = 0; i < this.count; i++) {
      const k = i * 4;
      if ((this.screen[k + 3] ?? 0) < 0.5) continue;
      const dx = x - (this.screen[k] ?? 0);
      const dy = y - (this.screen[k + 1] ?? 0);
      const d = dx * dx + dy * dy;
      const r = this.screen[k + 2] ?? 0;
      if (d < r * r && d < bestD) {
        best = i;
        bestD = d;
      }
    }
    return best;
  }

  dispose(): void {
    this.mesh.geometry.dispose();
    this.material.dispose();
    this.atlas?.dispose();
  }
}
