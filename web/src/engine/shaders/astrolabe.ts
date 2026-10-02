import { COMMON, ENVIRONMENT, glsl } from "./chunks";

/** Rings drawn by one instanced draw: their quaternions and shapes live in uniform arrays. */
export const RING_COUNT = 7;

/** Shared by every part of the astrolabe: the whole instrument's pose. */
const GROUP = glsl`
uniform vec4 uGroupQuat;
uniform vec3 uGroupPos;
uniform float uGroupScale;
vec3 toWorld(vec3 p) { return rotateByQuat(p, uGroupQuat) * uGroupScale + uGroupPos; }
vec3 toWorldDir(vec3 d) { return rotateByQuat(d, uGroupQuat); }
`;

/**
 * A ring is a superellipse swept around a circle: exponent 2 is a round tube, higher exponents
 * give the flat, chamfered bands of a real astrolabe. Position and normal are evaluated
 * analytically from (u, v), so one tiny grid serves every ring.
 */
export const RING_VERTEX = glsl`
${COMMON}
${GROUP}
attribute float aRing;
uniform vec4 uRingQuat[${RING_COUNT}];
uniform vec4 uRingShape[${RING_COUNT}];
uniform vec4 uRingLook[${RING_COUNT}];
varying vec3 vWorldPos;
varying vec3 vNormal;
varying vec3 vTangent;
varying vec2 vUv;
varying vec4 vLook;
varying float vFace;

void main() {
  int i = int(aRing + 0.5);
  vec4 q = uRingQuat[i];
  vec4 sh = uRingShape[i];
  float u = position.x * TAU;
  float v = position.y * TAU;
  float cu = cos(u), su = sin(u), cv = cos(v), sv = sin(v);
  float e = 2.0 / sh.w;
  float px = sign(cv) * pow(abs(cv), e);
  float py = sign(sv) * pow(abs(sv), e);
  float ne = 2.0 - e;
  float nx = sign(cv) * pow(abs(cv), ne) / sh.z;
  float ny = sign(sv) * pow(abs(sv), ne) / sh.y;
  vec3 radial = vec3(cu, 0.0, su);
  vec3 up = vec3(0.0, 1.0, 0.0);
  vec3 p = radial * (sh.x + px * sh.z) + up * (py * sh.y);
  vec3 n = normalize(radial * nx + up * ny + 1e-6);
  vec3 t = vec3(-su, 0.0, cu);
  p = rotateByQuat(p, q);
  n = rotateByQuat(n, q);
  t = rotateByQuat(t, q);
  vWorldPos = toWorld(p);
  vNormal = toWorldDir(n);
  vTangent = toWorldDir(t);
  vUv = position.xy;
  vLook = uRingLook[i];
  // Outer face of the band (where the graduation is engraved): v near 0.
  vFace = smoothstep(0.55, 0.95, cv);
  gl_Position = projectionMatrix * viewMatrix * vec4(vWorldPos, 1.0);
}
`;

/** Brushed titanium: anisotropic softbox reflections, a cursor-driven key light, engraving. */
export const TITANIUM_FRAGMENT = glsl`
${COMMON}
${ENVIRONMENT}
uniform vec3 uLightPos;
uniform float uLightIntensity;
uniform float uPresence;
varying vec3 vWorldPos;
varying vec3 vNormal;
varying vec3 vTangent;
varying vec2 vUv;
varying vec4 vLook;
varying float vFace;

void main() {
  vec3 N = normalize(vNormal);
  vec3 V = normalize(cameraPosition - vWorldPos);
  if (dot(N, V) < 0.0) N = -N;
  vec3 T = normalize(vTangent - N * dot(vTangent, N));

  // Graduation: a fine tick every degree, longer every 5 and 10, cut into the outer face.
  float deg = vUv.x * 360.0 * vLook.w;
  float w = fwidth(deg) * 1.2;
  float tick1 = 1.0 - smoothstep(0.06, 0.06 + w, abs(fract(deg) - 0.5));
  float d5 = deg / 5.0;
  float tick5 = 1.0 - smoothstep(0.03, 0.03 + w / 5.0, abs(fract(d5) - 0.5));
  float groove = vFace * max(tick1 * 0.55, tick5) * step(0.5, vLook.w);

  // Brushing: micro-scratches along the tangent tilt the normal across it.
  float scratch = hash12(vec2(floor(vUv.y * 900.0), floor(vUv.x * 9.0))) - 0.5;
  vec3 B = cross(N, T);
  vec3 Nb = normalize(N + B * scratch * 0.06 - B * groove * 0.5);

  vec3 R = reflect(-V, Nb);
  vec3 env = environment(R) * 0.5 + environment(normalize(R + T * 0.22)) * 0.25 + environment(normalize(R - T * 0.22)) * 0.25;
  vec3 F0 = vec3(0.542, 0.497, 0.449) * mix(vec3(1.0), vLook.rgb, 0.35);
  float NdV = max(dot(Nb, V), 1e-3);
  vec3 F = F0 + (1.0 - F0) * pow(1.0 - NdV, 5.0);

  vec3 L = normalize(uLightPos - vWorldPos);
  vec3 H = normalize(L + V);
  float TdH = dot(T, H);
  float aniso = pow(sqrt(max(0.0, 1.0 - TdH * TdH)), 220.0) * max(dot(Nb, L), 0.0);
  float broad = pow(max(dot(Nb, H), 0.0), 18.0) * 0.12;
  vec3 col = env * F + vec3(1.0, 0.97, 0.92) * (aniso * 4.0 + broad) * F * uLightIntensity;
  col *= mix(1.0, 0.18, groove);
  col += uTint * pow(1.0 - NdV, 3.0) * 0.08;

  vec3 outc = toSRGB(tonemap(col)) * uPresence;
  outc += (ign(gl_FragCoord.xy) - 0.5) / 255.0;
  gl_FragColor = vec4(outc, 1.0);
}
`;

/**
 * Diamond-refractive rings: Schlick fresnel at diamond's F0, refraction through the procedural
 * world at three wavelengths (IOR 2.40 / 2.42 / 2.46 → dispersion 0.044 like real diamond) and
 * spectral "fire" where the cursor light grazes the facets.
 */
export const DIAMOND_FRAGMENT = glsl`
${COMMON}
${ENVIRONMENT}
uniform vec3 uLightPos;
uniform float uLightIntensity;
uniform float uPresence;
varying vec3 vWorldPos;
varying vec3 vNormal;
varying vec3 vTangent;
varying vec2 vUv;
varying vec4 vLook;
varying float vFace;

void main() {
  vec3 N = normalize(vNormal);
  vec3 V = normalize(cameraPosition - vWorldPos);
  float facing = dot(N, V);
  if (facing < 0.0) N = -N;
  float NdV = abs(facing);
  // Facets: quantise the normal around the ring so the band reads as cut, not moulded.
  float facet = floor(vUv.x * 96.0 * vLook.w) / (96.0 * vLook.w);
  vec3 Nf = normalize(N + vTangent * (hash11(facet * 91.0) - 0.5) * 0.18);

  float F = 0.17 + 0.83 * pow(1.0 - NdV, 5.0);
  vec3 refl = environment(reflect(-V, Nf));
  vec3 rr = refract(-V, Nf, 1.0 / 2.40);
  vec3 rg = refract(-V, Nf, 1.0 / 2.42);
  vec3 rb = refract(-V, Nf, 1.0 / 2.46);
  vec3 refr = vec3(environment(rr).r, environment(rg).g, environment(rb).b);

  vec3 L = normalize(uLightPos - vWorldPos);
  float sp = pow(max(dot(reflect(-L, Nf), V), 0.0), 70.0);
  float glint = pow(max(dot(reflect(-L, Nf), V), 0.0), 900.0);
  vec3 fire = spectral(fract(dot(Nf, L) * 2.6 + facet * 3.0)) * sp * 2.6 * uLightIntensity;

  vec3 col = mix(refr * vLook.rgb, refl, F) + fire + vec3(glint * 6.0 * uLightIntensity);
  col += uTint * pow(1.0 - NdV, 4.0) * 0.35;
  float alpha = clamp(0.22 + F * 0.95 + sp * 0.6 + glint, 0.0, 1.0) * uPresence;
  gl_FragColor = vec4(toSRGB(tonemap(col)), alpha);
}
`;

/** The limb's teeth: small chamfered blocks standing on the outer ring, one instanced draw. */
export const TEETH_VERTEX = glsl`
${COMMON}
${GROUP}
attribute float aAngle;
attribute float aLong;
uniform vec4 uRingQuat[${RING_COUNT}];
uniform vec4 uRingShape[${RING_COUNT}];
varying vec3 vWorldPos;
varying vec3 vNormal;
varying float vLong;

void main() {
  vec4 q = uRingQuat[0];
  vec4 sh = uRingShape[0];
  float c = cos(aAngle), s = sin(aAngle);
  vec3 radial = vec3(c, 0.0, s);
  vec3 tangent = vec3(-s, 0.0, c);
  vec3 up = vec3(0.0, 1.0, 0.0);
  float len = mix(0.05, 0.12, aLong);
  vec3 local = position * vec3(0.012, len, 0.026);
  vec3 p = radial * (sh.x + sh.z + local.y * 0.5 + len * 0.5) + tangent * local.x + up * local.z;
  vec3 n = normalize(radial * normal.y + tangent * normal.x + up * normal.z);
  p = rotateByQuat(p, q);
  n = rotateByQuat(n, q);
  vWorldPos = toWorld(p);
  vNormal = toWorldDir(n);
  vLong = aLong;
  gl_Position = projectionMatrix * viewMatrix * vec4(vWorldPos, 1.0);
}
`;

export const TEETH_FRAGMENT = glsl`
${COMMON}
${ENVIRONMENT}
uniform vec3 uLightPos;
uniform float uLightIntensity;
uniform float uPresence;
varying vec3 vWorldPos;
varying vec3 vNormal;
varying float vLong;
void main() {
  vec3 N = normalize(vNormal);
  vec3 V = normalize(cameraPosition - vWorldPos);
  vec3 R = reflect(-V, N);
  vec3 F0 = vec3(0.56, 0.52, 0.48);
  float NdV = max(dot(N, V), 1e-3);
  vec3 F = F0 + (1.0 - F0) * pow(1.0 - NdV, 5.0);
  vec3 L = normalize(uLightPos - vWorldPos);
  float spec = pow(max(dot(reflect(-L, N), V), 0.0), 40.0) * uLightIntensity;
  vec3 col = environment(R) * F + F * spec * 2.0 + uTint * vLong * 0.05;
  gl_FragColor = vec4(toSRGB(tonemap(col)) * uPresence, 1.0);
}
`;

/** The central brilliant: drawn twice, back faces (internal fire) then front faces. */
export const GEM_VERTEX = glsl`
${COMMON}
${GROUP}
uniform vec4 uGemQuat;
uniform float uGemScale;
varying vec3 vWorldPos;
varying vec3 vNormal;
varying vec3 vLocal;
void main() {
  vec3 p = rotateByQuat(position * uGemScale, uGemQuat);
  vec3 n = rotateByQuat(normal, uGemQuat);
  vWorldPos = toWorld(p);
  vNormal = toWorldDir(n);
  vLocal = position;
  gl_Position = projectionMatrix * viewMatrix * vec4(vWorldPos, 1.0);
}
`;

export const GEM_FRAGMENT = glsl`
${COMMON}
${ENVIRONMENT}
uniform vec3 uLightPos;
uniform float uLightIntensity;
uniform float uPresence;
uniform float uBack;
uniform float uPulse;
varying vec3 vWorldPos;
varying vec3 vNormal;
varying vec3 vLocal;

void main() {
  vec3 N = normalize(vNormal);
  vec3 V = normalize(cameraPosition - vWorldPos);
  vec3 L = normalize(uLightPos - vWorldPos);
  vec3 col;
  float alpha;
  if (uBack > 0.5) {
    // Inside the stone: the ray has refracted in and bounces off a back facet.
    vec3 inward = refract(-V, -N, 1.0 / 2.42);
    vec3 bounce = reflect(inward, N);
    vec3 e = vec3(
      environment(bounce + vec3(0.03, 0.0, 0.0)).r,
      environment(bounce).g,
      environment(bounce - vec3(0.03, 0.0, 0.0)).b
    );
    float fire = pow(max(dot(bounce, L), 0.0), 24.0);
    col = e * 1.6 + spectral(fract(dot(N, L) * 3.0 + vLocal.y * 2.0)) * fire * 3.0 * uLightIntensity;
    col += uTint * (0.25 + uPulse * 0.6);
    alpha = 0.92;
  } else {
    float NdV = max(dot(N, V), 0.0);
    float F = 0.17 + 0.83 * pow(1.0 - NdV, 5.0);
    vec3 refl = environment(reflect(-V, N));
    vec3 rr = refract(-V, N, 1.0 / 2.40);
    vec3 rb = refract(-V, N, 1.0 / 2.46);
    vec3 refr = vec3(environment(rr).r, environment(normalize(rr + rb)).g, environment(rb).b);
    float sp = pow(max(dot(reflect(-L, N), V), 0.0), 120.0);
    col = mix(refr, refl, F) + vec3(sp * 5.0 * uLightIntensity) + spectral(fract(NdV * 3.0 + uTime * 0.05)) * sp * 2.0;
    alpha = clamp(0.35 + F + sp, 0.0, 1.0);
  }
  gl_FragColor = vec4(toSRGB(tonemap(col)), alpha * uPresence);
}
`;

/**
 * The fourth dimension: a tesseract's 32 edges, rotated in the XW, YW and ZW planes and
 * projected into 3D by perspective along W, then drawn as screen-space ribbons.
 */
export const TESSERACT_VERTEX = glsl`
${COMMON}
${GROUP}
attribute vec4 aA;
attribute vec4 aB;
uniform vec4 uRot;
uniform float uW;
uniform float uSize;
uniform vec2 uResolution;
uniform float uWidth;
varying float vAlong;
varying float vSide;
varying float vDepth;

vec4 rot4(vec4 p) {
  float c, s;
  c = cos(uRot.x); s = sin(uRot.x); p = vec4(c * p.x - s * p.w, p.y, p.z, s * p.x + c * p.w);
  c = cos(uRot.y); s = sin(uRot.y); p = vec4(p.x, c * p.y - s * p.w, p.z, s * p.y + c * p.w);
  c = cos(uRot.z); s = sin(uRot.z); p = vec4(p.x, p.y, c * p.z - s * p.w, s * p.z + c * p.w);
  c = cos(uRot.w); s = sin(uRot.w); p = vec4(c * p.x - s * p.z, p.y, s * p.x + c * p.z, p.w);
  return p;
}

void main() {
  vec4 a4 = rot4(aA);
  vec4 b4 = rot4(aB);
  vec3 a = toWorld(a4.xyz * (uW / (uW - a4.w)) * uSize);
  vec3 b = toWorld(b4.xyz * (uW / (uW - b4.w)) * uSize);
  vec4 ca = projectionMatrix * viewMatrix * vec4(a, 1.0);
  vec4 cb = projectionMatrix * viewMatrix * vec4(b, 1.0);
  vec2 sa = ca.xy / ca.w;
  vec2 sb = cb.xy / cb.w;
  vec2 dir = (sb - sa) * uResolution;
  dir = dir / (length(dir) + 1e-6);
  vec2 nrm = vec2(-dir.y, dir.x);
  vec4 c = mix(ca, cb, position.x);
  float wDepth = mix(a4.w, b4.w, position.x);
  float width = uWidth * (1.0 + wDepth * 0.35);
  c.xy += nrm * position.y * width / uResolution * c.w;
  gl_Position = c;
  vAlong = position.x;
  vSide = position.y;
  vDepth = wDepth;
}
`;

export const TESSERACT_FRAGMENT = glsl`
${COMMON}
uniform vec3 uTint;
uniform float uPresence;
varying float vAlong;
varying float vSide;
varying float vDepth;
void main() {
  float core = exp(-vSide * vSide * 6.0);
  float ends = smoothstep(0.0, 0.08, vAlong) * smoothstep(1.0, 0.92, vAlong);
  vec3 c = mix(uTint, vec3(1.0), 0.55 + vDepth * 0.25) * core * (0.55 + 0.45 * ends);
  gl_FragColor = vec4(c * uPresence * (0.9 + vDepth * 0.3), 1.0);
}
`;

/** Billboarded glow: the singularity's light and an anamorphic streak (additive, one quad). */
export const GLOW_VERTEX = glsl`
${COMMON}
${GROUP}
uniform float uGlowSize;
varying vec2 vUv;
void main() {
  vec3 center = toWorld(vec3(0.0));
  vec4 mv = viewMatrix * vec4(center, 1.0);
  mv.xy += position.xy * uGlowSize * uGroupScale * vec2(2.4, 1.0);
  vUv = position.xy;
  gl_Position = projectionMatrix * mv;
}
`;

export const GLOW_FRAGMENT = glsl`
${COMMON}
uniform vec3 uTint;
uniform float uPresence;
uniform float uPulse;
varying vec2 vUv;
void main() {
  vec2 p = vUv * vec2(2.4, 1.0);
  float r = length(p);
  float glow = exp(-r * 3.4) * 0.55 + exp(-r * 9.0) * 0.9;
  float streak = exp(-abs(p.y) * 46.0) * exp(-abs(p.x) * 1.1) * 0.35;
  vec3 c = mix(uTint, vec3(1.0), 0.6) * (glow + streak) * (0.75 + uPulse * 0.5);
  gl_FragColor = vec4(c * uPresence, 1.0);
}
`;
