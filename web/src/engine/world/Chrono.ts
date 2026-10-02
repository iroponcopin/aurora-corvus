import {
  AdditiveBlending,
  Color,
  InstancedBufferAttribute,
  InstancedMesh,
  type IUniform,
  Matrix4,
  PlaneGeometry,
  Quaternion,
  ShaderMaterial,
  Vector3,
} from "three";
import { COMMON, glsl } from "../shaders/chunks";
import { damp } from "../math";
import { engine } from "../store";
import type { SharedUniforms } from "./uniforms";

/** The orbital path of time. Must stay identical to `chronoPath` in shaders/particles.ts. */
export function chronoPath(u: number, out: Vector3): Vector3 {
  return out.set(Math.sin(u * 7) * 4.2, Math.sin(u * 11 + 1.3) * 1.6, -u * 120);
}

export const MAX_NODES = 48;

const NODE_VERTEX = glsl`
attribute vec3 aColor;
attribute float aFocus;
varying vec2 vUv;
varying vec3 vColor;
varying float vFocus;
varying float vFade;
void main() {
  // A camera-facing glint: the quad is laid out in view space around the beacon's centre.
  vec4 centre = modelViewMatrix * instanceMatrix * vec4(0.0, 0.0, 0.0, 1.0);
  float size = length(instanceMatrix[0].xyz);
  // Fade out as the camera flies through a beacon, so one never fills the screen.
  vFade = smoothstep(0.7, 3.4, -centre.z);
  vUv = position.xy;
  vColor = aColor;
  vFocus = aFocus;
  gl_Position = projectionMatrix * (centre + vec4(position.xy * size, 0.0, 0.0));
}
`;

const NODE_FRAGMENT = glsl`
${COMMON}
uniform float uPresence;
uniform float uTime;
varying vec2 vUv;
varying vec3 vColor;
varying float vFocus;
varying float vFade;
void main() {
  float r = length(vUv) * 2.0;
  if (r > 1.0) discard;
  float core = exp(-r * r * 60.0);
  float glow = exp(-r * r * 7.0) * 0.55;
  // Four diffraction spikes, longer on the beacon the camera is passing.
  float sx = exp(-abs(vUv.y) * 90.0) * exp(-abs(vUv.x) * (7.0 - vFocus * 3.0));
  float sy = exp(-abs(vUv.x) * 90.0) * exp(-abs(vUv.y) * (7.0 - vFocus * 3.0));
  float spikes = (sx + sy) * (0.35 + vFocus * 0.5);
  // The focused beacon wears a slow ring.
  float ring = smoothstep(0.035, 0.0, abs(r - 0.42 - 0.04 * sin(uTime * 2.2))) * vFocus * 0.7;
  float edge = 1.0 - smoothstep(0.75, 1.0, r);
  vec3 c = vColor * (glow + spikes + ring) * (0.7 + vFocus * 0.9) + vec3(core) * (1.0 + vFocus);
  gl_FragColor = vec4(toSRGB(tonemap(c * edge)) * uPresence * vFade, 1.0);
}
`;

/** Milestone beacons along the path of time: camera-facing glints, one instanced, additive draw. */
export class Chrono {
  readonly mesh: InstancedMesh;
  private readonly colorAttr: InstancedBufferAttribute;
  private readonly focusAttr: InstancedBufferAttribute;
  private readonly focus = new Float32Array(MAX_NODES);
  private readonly us = new Float32Array(MAX_NODES);
  private readonly presence: IUniform<number> = { value: 0 };
  private readonly m = new Matrix4();
  private readonly q = new Quaternion();
  private readonly p = new Vector3();
  private readonly s = new Vector3();
  private readonly color = new Color();
  private count = 0;
  /** Index of the node nearest the camera along the path (-1 when hidden). */
  active = -1;

  constructor(shared: SharedUniforms) {
    const geometry = new PlaneGeometry(1, 1);
    this.colorAttr = new InstancedBufferAttribute(new Float32Array(MAX_NODES * 3), 3);
    this.focusAttr = new InstancedBufferAttribute(this.focus, 1);
    geometry.setAttribute("aColor", this.colorAttr);
    geometry.setAttribute("aFocus", this.focusAttr);
    const material = new ShaderMaterial({
      vertexShader: NODE_VERTEX,
      fragmentShader: NODE_FRAGMENT,
      uniforms: { uTime: shared.uTime, uPresence: this.presence },
      transparent: true,
      depthWrite: false,
      blending: AdditiveBlending,
    });
    this.mesh = new InstancedMesh(geometry, material, MAX_NODES);
    this.mesh.count = 0;
    this.mesh.frustumCulled = false;
    this.mesh.renderOrder = 9;
  }

  /** Place the milestones: path parameters (0..1) and their brand colours (hex). */
  setNodes(us: readonly number[], colors: readonly string[]): void {
    const n = Math.min(us.length, MAX_NODES);
    this.count = n;
    this.mesh.count = n;
    for (let i = 0; i < n; i++) {
      this.us[i] = us[i] ?? 0;
      this.color.set(colors[i] ?? "#0071e3");
      this.colorAttr.setXYZ(i, this.color.r, this.color.g, this.color.b);
    }
    this.colorAttr.needsUpdate = true;
  }

  update(dt: number): void {
    const want = Math.max(engine.splineWeight, engine.formationB === 4 ? engine.morph : 0, engine.formationA === 4 ? 1 - engine.morph : 0);
    this.presence.value = damp(this.presence.value, want, 3, dt);
    this.mesh.visible = this.presence.value > 0.002 && this.count > 0;
    if (!this.mesh.visible) {
      this.active = -1;
      return;
    }
    let nearest = -1;
    let nearestD = Infinity;
    for (let i = 0; i < this.count; i++) {
      const u = this.us[i] ?? 0;
      const d = Math.abs(u - engine.splineT);
      if (d < nearestD) {
        nearestD = d;
        nearest = i;
      }
    }
    this.active = nearestD < 0.06 ? nearest : -1;
    for (let i = 0; i < this.count; i++) {
      const target = i === this.active ? 1 : 0;
      this.focus[i] = damp(this.focus[i] ?? 0, target, 6, dt);
      chronoPath(this.us[i] ?? 0, this.p);
      this.p.x *= engine.mirror;
      const pulse = 1 + Math.sin(engine.time * 2 + i) * 0.06;
      const size = (1.5 + (this.focus[i] ?? 0) * 1.1) * pulse;
      this.s.set(size, size, size);
      this.m.compose(this.p, this.q, this.s);
      this.mesh.setMatrixAt(i, this.m);
    }
    this.mesh.instanceMatrix.needsUpdate = true;
    this.focusAttr.needsUpdate = true;
  }

  dispose(): void {
    this.mesh.geometry.dispose();
    (this.mesh.material as ShaderMaterial).dispose();
  }
}
