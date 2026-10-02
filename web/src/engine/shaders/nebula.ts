import { COMMON, NOISE, glsl } from "./chunks";

/**
 * The backdrop, one full-screen triangle: OLED black with a faint aurora (the site's name) and a
 * gravitational-lens shimmer around the cursor. Most pixels stay at true #000000 — the colour
 * only breathes where the aurora lives, so an OLED panel keeps those pixels off.
 */
export const NEBULA_VERTEX = glsl`
varying vec2 vUv;
void main() {
  vUv = position.xy * 0.5 + 0.5;
  gl_Position = vec4(position.xy, 0.0, 1.0);
}
`;

export const NEBULA_FRAGMENT = glsl`
${COMMON}
${NOISE}
uniform float uTime;
uniform vec3 uTint;
uniform float uEnergy;
uniform vec2 uPointer;
uniform float uAspect;
uniform float uIntensity;
uniform float uScroll;
uniform float uMirror;
varying vec2 vUv;

float fbm(vec3 p) {
  float a = 0.5, s = 0.0;
  for (int i = 0; i < 4; i++) {
    s += a * snoise(p);
    p = p * 2.03 + vec3(1.7, 9.2, 3.1);
    a *= 0.5;
  }
  return s;
}

void main() {
  vec2 uv = vUv;
  vec2 p = (uv - 0.5) * vec2(uAspect, 1.0);
  p.x *= uMirror;
  float t = uTime * 0.035;
  float drift = uScroll * 0.00012;

  // Aurora curtains: vertical folds whose height follows a slow fbm, brightest near the top.
  float x = p.x * 1.4 + fbm(vec3(p.x * 0.8, drift, t)) * 0.6;
  float folds = 0.5 + 0.5 * sin(x * 6.0 + fbm(vec3(p.x * 2.0, p.y, t * 1.7)) * 3.0);
  float height = 0.25 + fbm(vec3(p.x * 0.6 + 4.0, t * 0.6, drift)) * 0.22;
  float curtain = smoothstep(height - 0.35, height + 0.05, p.y) * smoothstep(height + 0.7, height + 0.08, p.y);
  float aurora = pow(folds, 3.0) * curtain;

  vec3 green = vec3(0.12, 0.85, 0.62);
  vec3 col = mix(green, uTint, 0.55) * aurora * 0.045;
  col += uTint * 0.6 * aurora * pow(folds, 6.0) * 0.035;

  // A whisper of depth at the bottom so the black has a floor.
  col += uTint * 0.012 * smoothstep(0.1, -0.6, p.y) * (0.6 + 0.4 * fbm(vec3(p * 1.3, t)));

  // Cursor lens: a faint Einstein ring that follows the pointer.
  vec2 q = p - uPointer * vec2(uAspect * 0.5, 0.5);
  float rq = length(q);
  col += uTint * smoothstep(0.09, 0.0, abs(rq - 0.16)) * 0.01 * (1.0 + uEnergy * 3.0);

  col *= uIntensity * (1.0 + uEnergy * 0.8);
  vec3 outc = toSRGB(col);
  // Dither only where there is colour, so true black stays true black.
  outc += (ign(gl_FragCoord.xy) - 0.5) / 255.0 * step(0.0005, dot(col, vec3(1.0)));
  gl_FragColor = vec4(max(outc, vec3(0.0)), 1.0);
}
`;

/** Brand marks orbiting the astrolabe: rounded glass tiles, each face showing its icon. */
export const MARK_VERTEX = glsl`
${COMMON}
attribute float aCell;
attribute float aHover;
varying vec3 vWorldPos;
varying vec3 vNormal;
varying vec2 vFaceUv;
varying float vFront;
varying float vCell;
varying float vHover;
void main() {
  vec4 world = modelMatrix * instanceMatrix * vec4(position, 1.0);
  vWorldPos = world.xyz;
  vNormal = normalize(mat3(modelMatrix * instanceMatrix) * normal);
  vFaceUv = position.xy + 0.5;
  vFront = smoothstep(0.6, 0.9, normal.z);
  vCell = aCell;
  vHover = aHover;
  gl_Position = projectionMatrix * viewMatrix * world;
}
`;

export const MARK_FRAGMENT = glsl`
${COMMON}
uniform sampler2D uAtlas;
uniform vec2 uAtlasGrid;
uniform vec3 uTint;
uniform vec3 uLightPos;
uniform float uPresence;
uniform float uReady;
varying vec3 vWorldPos;
varying vec3 vNormal;
varying vec2 vFaceUv;
varying float vFront;
varying float vCell;
varying float vHover;

float roundedMask(vec2 uv, float r) {
  vec2 q = abs(uv - 0.5) - (0.5 - r);
  return 1.0 - smoothstep(0.0, 0.01, length(max(q, 0.0)) + min(max(q.x, q.y), 0.0) - r);
}

void main() {
  vec3 N = normalize(vNormal);
  vec3 V = normalize(cameraPosition - vWorldPos);
  float NdV = max(dot(N, V), 0.0);
  float F = 0.04 + 0.96 * pow(1.0 - NdV, 5.0);
  vec2 cell = vec2(mod(vCell, uAtlasGrid.x), floor(vCell / uAtlasGrid.x));
  vec2 uv = (cell + clamp(vFaceUv, 0.0, 1.0)) / uAtlasGrid;
  uv.y = 1.0 - uv.y;
  // The atlas is an sRGB texture: the GPU hands us linear values already.
  vec3 icon = texture2D(uAtlas, uv).rgb * uReady;
  float mask = roundedMask(vFaceUv, 0.22);
  vec3 L = normalize(uLightPos - vWorldPos);
  float sp = pow(max(dot(reflect(-L, N), V), 0.0), 80.0);
  vec3 side = vec3(0.04, 0.045, 0.05) + uTint * 0.05;
  vec3 col = mix(side, icon * (1.0 + vHover * 0.25), vFront * mask);
  col += vec3(sp * 1.5) + uTint * F * 0.35 + vec3(F * 0.25);
  col += uTint * vHover * 0.06;
  gl_FragColor = vec4(toSRGB(tonemap(col)) * uPresence, uPresence);
}
`;
