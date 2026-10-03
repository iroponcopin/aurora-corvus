import { type IUniform, Vector3 } from "three";

/**
 * Uniform objects shared by reference between materials: written once per frame, read by every
 * shader that declares them (time, tint, cursor light, scroll energy, RTL mirror).
 */
export interface SharedUniforms {
  uTime: IUniform<number>;
  uTint: IUniform<Vector3>;
  uLightPos: IUniform<Vector3>;
  uLightIntensity: IUniform<number>;
  uEnergy: IUniform<number>;
  uMirror: IUniform<number>;
}

export function createSharedUniforms(): SharedUniforms {
  return {
    uTime: { value: 0 },
    uTint: { value: new Vector3(0.36, 0.62, 1) },
    uLightPos: { value: new Vector3(3, 2.5, 7) },
    uLightIntensity: { value: 1 },
    uEnergy: { value: 0 },
    uMirror: { value: 1 },
  };
}
