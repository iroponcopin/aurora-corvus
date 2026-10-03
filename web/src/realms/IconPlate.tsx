"use client";

import { useEffect, useMemo, useRef } from "react";
import { type Mesh, ShaderMaterial, SRGBColorSpace, TextureLoader, Vector2, Vector3, LinearMipmapLinearFilter } from "three";
import { RoundedBoxGeometry } from "three/addons/geometries/RoundedBoxGeometry.js";
import { COMMON, ENVIRONMENT, glsl } from "@/engine/shaders/chunks";
import { damp } from "@/engine/math";
import { engine } from "@/engine/store";
import { useViewApi, useViewFrame } from "@/engine/View";

const VERT = glsl`
varying vec3 vNormal;
varying vec3 vWorld;
varying vec2 vFace;
varying float vFront;
void main() {
  vec4 w = modelMatrix * vec4(position, 1.0);
  vWorld = w.xyz;
  vNormal = normalize(mat3(modelMatrix) * normal);
  vFace = position.xy / 2.0 + 0.5;
  vFront = smoothstep(0.55, 0.9, normal.z);
  gl_Position = projectionMatrix * viewMatrix * w;
}
`;

const FRAG = glsl`
${COMMON}
${ENVIRONMENT}
uniform sampler2D uMap;
uniform float uReady;
uniform float uSweep;
uniform float uDim;
uniform vec3 uLight;
varying vec3 vNormal;
varying vec3 vWorld;
varying vec2 vFace;
varying float vFront;

float squircle(vec2 uv) {
  vec2 q = abs(uv - 0.5) * 2.0;
  float d = pow(pow(q.x, 5.0) + pow(q.y, 5.0), 0.2);
  return 1.0 - smoothstep(0.985, 1.0, d);
}

void main() {
  vec3 N = normalize(vNormal);
  vec3 V = normalize(cameraPosition - vWorld);
  float NdV = max(dot(N, V), 0.0);
  vec3 R = reflect(-V, N);
  vec3 icon = texture2D(uMap, clamp(vFace, 0.0, 1.0)).rgb * uReady;
  float grey = dot(icon, vec3(0.299, 0.587, 0.114));
  icon = mix(icon, vec3(grey), uDim * 0.75) * mix(1.0, 0.62, uDim);
  vec3 metal = vec3(0.227, 0.227, 0.247) * 0.35 + environment(R) * vec3(0.5, 0.5, 0.53) * 0.6;
  float mask = squircle(vFace) * vFront;
  vec3 col = mix(metal, icon, mask);
  // A band of light that sweeps the face once after the plate arrives.
  float band = exp(-pow((vFace.x + vFace.y * 0.6 - uSweep * 2.6 + 0.5) * 7.0, 2.0)) * mask;
  col += vec3(0.9, 0.95, 1.0) * band * 0.35;
  vec3 L = normalize(uLight - vWorld);
  float sp = pow(max(dot(reflect(-L, N), V), 0.0), 60.0);
  col += vec3(sp) * (0.25 + 0.5 * (1.0 - mask)) + uTint * pow(1.0 - NdV, 3.0) * 0.35;
  gl_FragColor = vec4(toSRGB(tonemap(col)), 1.0);
}
`;

/**
 * A brand's app icon as a physical object: a squircle plate of dark metal with the icon on its
 * face. It spins in, a light sweeps it, and it leans towards the pointer.
 */
export function IconPlate({ src, dim = false, scale = 1 }: { src: string; dim?: boolean; scale?: number }) {
  const mesh = useRef<Mesh>(null);
  const api = useViewApi();
  const geometry = useMemo(() => new RoundedBoxGeometry(2, 2, 0.34, 6, 0.44), []);
  const lightTmp = useMemo(() => new Vector3(), []);
  const pointer = useMemo(() => new Vector2(), []);
  const state = useRef({ t: 0, rx: 0.06, ry: -0.28, intro: 0 });
  const material = useMemo(
    () =>
      new ShaderMaterial({
        vertexShader: VERT,
        fragmentShader: FRAG,
        uniforms: {
          uMap: { value: null },
          uReady: { value: 0 },
          uSweep: { value: -1 },
          uDim: { value: dim ? 1 : 0 },
          uLight: { value: new Vector3(3, 4, 6) },
          uTint: { value: new Vector3(0.36, 0.62, 1) },
          uTime: { value: 0 },
        },
      }),
    [dim],
  );

  useEffect(() => {
    let alive = true;
    new TextureLoader().load(src, (tex) => {
      if (!alive) return;
      tex.colorSpace = SRGBColorSpace;
      tex.minFilter = LinearMipmapLinearFilter;
      tex.anisotropy = 4;
      material.uniforms.uMap!.value = tex;
      material.uniforms.uReady!.value = 1;
    });
    return () => {
      alive = false;
      (material.uniforms.uMap!.value as { dispose?: () => void } | null)?.dispose?.();
      material.dispose();
    };
  }, [src, material]);

  useEffect(() => () => geometry.dispose(), [geometry]);

  useViewFrame((dt, view) => {
    const m = mesh.current;
    if (m === null) return;
    const s = state.current;
    s.t += dt;
    const calm = engine.reducedMotion;
    // Pointer relative to this element's centre, in -1..1.
    const t = view.tracked;
    pointer.set(
      ((engine.pointerX - (t.screenLeft + t.width / 2)) / Math.max(1, t.width)) * 2,
      ((engine.pointerY - (t.screenTop + t.height / 2)) / Math.max(1, t.height)) * 2,
    );
    const px = Math.max(-1.5, Math.min(1.5, pointer.x));
    const py = Math.max(-1.5, Math.min(1.5, pointer.y));
    const intro = calm ? 1 : Math.min(1, s.t / 1.6);
    const ease = 1 - Math.pow(1 - intro, 4);
    const targetY = -0.28 + px * 0.32 * engine.pointerInside;
    const targetX = 0.06 + py * 0.22 * engine.pointerInside;
    s.ry = damp(s.ry, targetY, 5, dt);
    s.rx = damp(s.rx, targetX, 5, dt);
    m.rotation.set(s.rx, s.ry + (1 - ease) * -Math.PI * 1.25 * engine.mirror, 0);
    m.position.y = Math.sin(s.t * 0.8) * 0.04;
    const sweep = material.uniforms.uSweep!;
    sweep.value = calm ? -1 : Math.min(1.2, Math.max(-1, (s.t - 0.9) / 1.1));
    api.camera.updateMatrixWorld();
    lightTmp.set(px * 4, -py * 3 + 2, 6);
    (material.uniforms.uLight!.value as Vector3).copy(lightTmp);
    material.uniforms.uTint!.value.set(engine.tintR, engine.tintG, engine.tintB);
  });

  return <mesh ref={mesh} geometry={geometry} material={material} scale={scale} />;
}
