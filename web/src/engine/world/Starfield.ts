import {
  AdditiveBlending,
  BufferAttribute,
  BufferGeometry,
  FloatType,
  HalfFloatType,
  type IUniform,
  Points,
  ShaderMaterial,
  type Texture,
  Vector3,
  type WebGLRenderer,
} from "three";
import { GPUComputationRenderer, type Variable } from "three/addons/misc/GPUComputationRenderer.js";
import { SIM_POSITION, SIM_SIZE, SIM_VELOCITY, STAR_FRAGMENT, STAR_VERTEX } from "../shaders/particles";
import { engine } from "../store";
import type { SharedUniforms } from "./uniforms";

/** The particle count: one per texel of the simulation textures. */
export const PARTICLE_COUNT = SIM_SIZE * SIM_SIZE;

export interface FormationFrame {
  anchorA: Vector3;
  anchorB: Vector3;
  scaleA: number;
  scaleB: number;
  rayOrigin: Vector3;
  rayDir: Vector3;
  pointerForce: number;
  viewportHeight: number;
  fovScale: number;
}

/**
 * 65,536 particles simulated on the GPU and drawn as one `Points` call. The simulation is two
 * float render targets per variable (ping-pong); nothing of the particle state ever crosses
 * back to the CPU.
 */
export class Starfield {
  readonly points: Points;
  private readonly gpu: GPUComputationRenderer;
  private readonly velocity: Variable;
  private readonly position: Variable;
  private readonly material: ShaderMaterial;
  private readonly velUniforms: Record<string, IUniform>;
  private readonly posUniforms: Record<string, IUniform>;
  private initFrames = 2;
  readonly ok: boolean;

  constructor(gl: WebGLRenderer, shared: SharedUniforms) {
    this.gpu = new GPUComputationRenderer(SIM_SIZE, SIM_SIZE, gl);
    // Full float where the GPU can render to it; half float (iOS before 15) otherwise.
    this.gpu.setDataType(gl.extensions.has("EXT_color_buffer_float") ? FloatType : HalfFloatType);

    const pos0 = this.gpu.createTexture();
    const vel0 = this.gpu.createTexture();
    this.velocity = this.gpu.addVariable("textureVelocity", SIM_VELOCITY, vel0);
    this.position = this.gpu.addVariable("texturePosition", SIM_POSITION, pos0);
    this.gpu.setVariableDependencies(this.velocity, [this.velocity, this.position]);
    this.gpu.setVariableDependencies(this.position, [this.velocity, this.position]);

    const formationUniforms = (): Record<string, IUniform> => ({
      uTime: shared.uTime,
      uMirror: shared.uMirror,
      uFormA: { value: 0 },
      uFormB: { value: 0 },
      uMorph: { value: 1 },
      uAnchorA: { value: new Vector3() },
      uAnchorB: { value: new Vector3() },
      uScaleA: { value: 1 },
      uScaleB: { value: 1 },
      uDt: { value: 1 / 60 },
    });

    this.velUniforms = this.velocity.material.uniforms;
    Object.assign(this.velUniforms, formationUniforms(), {
      uEnergy: shared.uEnergy,
      uScrollDir: { value: 1 },
      uRayOrigin: { value: new Vector3(0, 0, 100) },
      uRayDir: { value: new Vector3(0, 0, -1) },
      uPointerForce: { value: 0 },
      uBurst: { value: new Vector3() },
      uBurstTime: { value: -100 },
      uBurstStrength: { value: 0 },
      uCalm: { value: 1 },
      uInit: { value: 1 },
    });
    this.posUniforms = this.position.material.uniforms;
    Object.assign(this.posUniforms, formationUniforms(), { uInit: { value: 1 } });

    const error = this.gpu.init();
    this.ok = error === null;
    if (error !== null) console.warn("Starfield simulation unavailable:", error);

    // Each vertex only carries the texel it reads its state from.
    const reference = new Float32Array(PARTICLE_COUNT * 2);
    const positions = new Float32Array(PARTICLE_COUNT * 3);
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      reference[i * 2] = ((i % SIM_SIZE) + 0.5) / SIM_SIZE;
      reference[i * 2 + 1] = (Math.floor(i / SIM_SIZE) + 0.5) / SIM_SIZE;
    }
    const geometry = new BufferGeometry();
    geometry.setAttribute("position", new BufferAttribute(positions, 3));
    geometry.setAttribute("reference", new BufferAttribute(reference, 2));

    this.material = new ShaderMaterial({
      vertexShader: STAR_VERTEX,
      fragmentShader: STAR_FRAGMENT,
      uniforms: {
        uPosition: { value: null },
        uVelocity: { value: null },
        uTime: shared.uTime,
        uPixelRatio: { value: 1 },
        uViewportHeight: { value: 800 },
        uFovScale: { value: 1 },
        uSize: { value: 1 },
        uFormA: { value: 0 },
        uFormB: { value: 0 },
        uMorph: { value: 1 },
        uTint: shared.uTint,
        uEnergy: shared.uEnergy,
        uFade: { value: 0 },
        uFormDim: { value: 1 },
      },
      transparent: true,
      depthWrite: false,
      depthTest: true,
      blending: AdditiveBlending,
    });
    this.points = new Points(geometry, this.material);
    this.points.frustumCulled = false;
    this.points.renderOrder = 10;
  }

  /** Advance the simulation one frame. Allocation-free. */
  step(f: FormationFrame, dt: number): void {
    if (!this.ok) return;
    const v = this.velUniforms;
    const p = this.posUniforms;
    const a = engine.formationA;
    const b = engine.formationB;
    const morph = engine.morph;
    (v.uFormA as IUniform<number>).value = a;
    (v.uFormB as IUniform<number>).value = b;
    (v.uMorph as IUniform<number>).value = morph;
    (p.uFormA as IUniform<number>).value = a;
    (p.uFormB as IUniform<number>).value = b;
    (p.uMorph as IUniform<number>).value = morph;
    (v.uAnchorA as IUniform<Vector3>).value.copy(f.anchorA);
    (v.uAnchorB as IUniform<Vector3>).value.copy(f.anchorB);
    (p.uAnchorA as IUniform<Vector3>).value.copy(f.anchorA);
    (p.uAnchorB as IUniform<Vector3>).value.copy(f.anchorB);
    (v.uScaleA as IUniform<number>).value = f.scaleA;
    (v.uScaleB as IUniform<number>).value = f.scaleB;
    (p.uScaleA as IUniform<number>).value = f.scaleA;
    (p.uScaleB as IUniform<number>).value = f.scaleB;
    (v.uDt as IUniform<number>).value = dt;
    (p.uDt as IUniform<number>).value = dt;
    (v.uScrollDir as IUniform<number>).value = engine.scrollVelocity >= 0 ? 1 : -1;
    (v.uRayOrigin as IUniform<Vector3>).value.copy(f.rayOrigin);
    (v.uRayDir as IUniform<Vector3>).value.copy(f.rayDir);
    (v.uPointerForce as IUniform<number>).value = f.pointerForce;
    (v.uBurst as IUniform<Vector3>).value.set(engine.burstX, engine.burstY, engine.burstZ);
    (v.uBurstTime as IUniform<number>).value = engine.burstTime;
    (v.uBurstStrength as IUniform<number>).value = engine.burstStrength;
    (v.uCalm as IUniform<number>).value = engine.reducedMotion ? 0.15 : 1;
    (p.uInit as IUniform<number>).value = this.initFrames > 0 ? 1 : 0;
    (v.uInit as IUniform<number>).value = this.initFrames > 0 ? 1 : 0;
    if (this.initFrames > 0) this.initFrames -= 1;

    this.gpu.compute();

    const m = this.material.uniforms;
    (m.uPosition as IUniform<Texture>).value = this.gpu.getCurrentRenderTarget(this.position).texture;
    (m.uVelocity as IUniform<Texture>).value = this.gpu.getCurrentRenderTarget(this.velocity).texture;
    (m.uFormA as IUniform<number>).value = a;
    (m.uFormB as IUniform<number>).value = b;
    (m.uMorph as IUniform<number>).value = morph;
    (m.uPixelRatio as IUniform<number>).value = engine.dpr;
    (m.uViewportHeight as IUniform<number>).value = f.viewportHeight;
    (m.uFovScale as IUniform<number>).value = f.fovScale;
    const fade = m.uFade as IUniform<number>;
    fade.value = Math.min(1, fade.value + dt * 0.8);
    // On a phone the formation sits behind the text it frames: quieter, so the words stay legible.
    (m.uFormDim as IUniform<number>).value = engine.width < 700 ? 0.5 : 1;
    // Fewer particles on a struggling GPU: the draw range follows the adaptive quality.
    this.points.geometry.setDrawRange(0, engine.quality < 0.6 ? PARTICLE_COUNT / 2 : PARTICLE_COUNT);
  }

  /** Snap every particle to its target again (after a context restore or a long pause). */
  reseed(): void {
    this.initFrames = 2;
  }

  dispose(): void {
    this.gpu.dispose();
    this.points.geometry.dispose();
    this.material.dispose();
  }
}
