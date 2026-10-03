import { type IUniform, Mesh, ShaderMaterial, Vector2 } from "three";
import { NEBULA_FRAGMENT, NEBULA_VERTEX } from "../shaders/nebula";
import { damp } from "../math";
import { engine } from "../store";
import { fullscreenTriangle } from "./geometry";
import type { SharedUniforms } from "./uniforms";

/** The backdrop: one full-screen triangle drawn first, with depth off. */
export class Nebula {
  readonly mesh: Mesh;
  private readonly pointer = new Vector2();
  private readonly aspect: IUniform<number> = { value: 1 };
  private readonly intensity: IUniform<number> = { value: 0 };
  private readonly scroll: IUniform<number> = { value: 0 };
  private readonly material: ShaderMaterial;

  constructor(shared: SharedUniforms) {
    this.material = new ShaderMaterial({
      vertexShader: NEBULA_VERTEX,
      fragmentShader: NEBULA_FRAGMENT,
      uniforms: {
        uTime: shared.uTime,
        uTint: shared.uTint,
        uEnergy: shared.uEnergy,
        uMirror: shared.uMirror,
        uPointer: { value: this.pointer },
        uAspect: this.aspect,
        uIntensity: this.intensity,
        uScroll: this.scroll,
      },
      depthTest: false,
      depthWrite: false,
    });
    this.mesh = new Mesh(fullscreenTriangle(), this.material);
    this.mesh.frustumCulled = false;
    this.mesh.renderOrder = -100;
  }

  update(dt: number, width: number, height: number): void {
    this.pointer.set(engine.pointerSX, engine.pointerSY);
    this.aspect.value = width / Math.max(1, height);
    this.intensity.value = damp(this.intensity.value, 1, 1.2, dt);
    this.scroll.value = engine.scrollY;
  }

  dispose(): void {
    this.mesh.geometry.dispose();
    this.material.dispose();
  }
}
