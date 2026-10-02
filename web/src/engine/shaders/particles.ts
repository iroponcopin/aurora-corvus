import { COMMON, NOISE, glsl } from "./chunks";

/**
 * The starlight simulation: 256 × 256 = 65,536 particles integrated on the GPU (two
 * ping-ponged float textures: position and velocity). Each particle is pulled by a spring
 * towards its place in the current formation, stirred by a curl-noise flow field, pushed by
 * the cursor ray and by starlight bursts. 22 % of the particles are the far star sphere and
 * ignore formations; the rest morph between them with a per-particle stagger.
 */

export const SIM_SIZE = 256;

/** Formation shapes, in formation space (≈ unit radius), as functions of the particle seed. */
const FORMATIONS = glsl`
uniform float uTime;
uniform float uMirror;
uniform int uFormA;
uniform int uFormB;
uniform float uMorph;
uniform vec3 uAnchorA;
uniform vec3 uAnchorB;
uniform float uScaleA;
uniform float uScaleB;

vec3 rotX(vec3 p, float a) { float c = cos(a), s = sin(a); return vec3(p.x, c * p.y - s * p.z, s * p.y + c * p.z); }
vec3 rotY(vec3 p, float a) { float c = cos(a), s = sin(a); return vec3(c * p.x + s * p.z, p.y, -s * p.x + c * p.z); }
vec3 rotZ(vec3 p, float a) { float c = cos(a), s = sin(a); return vec3(c * p.x - s * p.y, s * p.x + c * p.y, p.z); }

float gauss(float u, float v) {
  return sqrt(-2.0 * log(max(u, 1e-5))) * cos(TAU * v);
}

vec3 fHorizon(vec4 s, float t) {
  if (s.z < 0.6) {
    // Accretion disc: Keplerian shear, three logarithmic arms, flaring with radius.
    float r = 1.2 + pow(s.x, 1.55) * 3.4;
    float arm = floor(s.w * 3.0);
    float theta = s.y * TAU;
    float spiral = log(r) * 2.4 + arm * TAU / 3.0;
    theta = mix(theta, spiral + (s.y - 0.5) * 1.1, 0.5);
    theta += t * 0.62 * pow(1.2 / r, 1.5);
    float h = gauss(fract(s.w * 7.13), fract(s.y * 3.71)) * 0.035 * r;
    vec3 p = vec3(cos(theta) * r, h, sin(theta) * r);
    return rotZ(rotX(p, -0.3), 0.12);
  }
  if (s.z < 0.74) {
    // Photon ring: the lensed back of the disc, thrown up around the singularity.
    float theta = s.y * TAU + t * 0.9;
    float r = 1.06 + gauss(s.x, s.w) * 0.018;
    return vec3(cos(theta) * r, sin(theta) * r * 0.98, -0.05);
  }
  // Halo: a slow spherical cloud.
  float u = s.x * 2.0 - 1.0;
  float phi = s.y * TAU + t * 0.05;
  float rad = 1.7 + pow(s.w, 0.7) * 2.6;
  float k = sqrt(1.0 - u * u);
  return vec3(cos(phi) * k, u * 0.62, sin(phi) * k) * rad;
}

vec3 fCodex(vec4 s, float t) {
  vec3 p;
  if (s.z < 0.36) {
    // Concentric rings of the transmutation circle, alternating spin.
    float ring = floor(s.x * 4.0);
    float radius = 0.85 + ring * 0.42 + (fract(s.x * 4.0) - 0.5) * 0.035;
    float dir = mod(ring, 2.0) < 0.5 ? 1.0 : -1.0;
    float a = s.y * TAU + t * 0.12 * dir;
    p = vec3(cos(a) * radius, sin(a) * radius, (s.w - 0.5) * 0.04);
  } else if (s.z < 0.58) {
    // Hexagram: two triangles inscribed in the third ring.
    float seg = floor(s.x * 6.0);
    float f = fract(s.x * 6.0);
    float tri = mod(seg, 2.0);
    float k = floor(seg * 0.5);
    float a0 = (k * 2.0 / 3.0) * PI + tri * PI / 3.0 + PI * 0.5 + t * 0.06;
    float a1 = a0 + 2.0 * PI / 3.0;
    vec2 v0 = vec2(cos(a0), sin(a0)) * 1.69;
    vec2 v1 = vec2(cos(a1), sin(a1)) * 1.69;
    p = vec3(mix(v0, v1, f), (s.w - 0.5) * 0.03);
  } else if (s.z < 0.82) {
    // The crafting matrix: nine clusters on a 3 × 3 grid, breathing.
    float cell = floor(s.x * 9.0);
    vec2 g = vec2(mod(cell, 3.0), floor(cell / 3.0)) - 1.0;
    vec3 j = (vec3(s.y, s.w, fract(s.x * 9.0)) - 0.5) * 0.22;
    float breathe = 1.0 + 0.06 * sin(t * 1.4 + cell);
    p = vec3(g * 0.42 * breathe, 0.0) + j;
  } else {
    // A double helix through the centre: the codex spine.
    float strand = step(0.5, s.w) * PI;
    float y = (s.x - 0.5) * 4.6;
    float a = y * 2.2 + strand + t * 0.7;
    p = vec3(cos(a) * 0.32, y, sin(a) * 0.32) + (vec3(s.y, s.w, s.x) - 0.5) * 0.05;
  }
  return rotX(p, -0.32);
}

vec3 fShowroom(vec4 s, float t) {
  if (s.z < 0.42) {
    // Pedestal: an annulus and its engraved circles on the floor.
    float r = 1.0 + s.x * 0.85;
    r = mix(r, floor(r * 6.0) / 6.0, 0.55);
    float a = s.y * TAU + t * 0.08;
    return vec3(cos(a) * r, -1.62 + (s.w - 0.5) * 0.02, sin(a) * r);
  }
  if (s.z < 0.74) {
    // Light column rising through the model.
    float y = fract(s.x + t * 0.035) * 4.2 - 1.6;
    float a = s.y * TAU + y * 0.6;
    float r = 1.05 + (s.w - 0.5) * 0.18;
    return vec3(cos(a) * r, y, sin(a) * r);
  }
  // A tilted halo orbiting the model.
  float a = s.y * TAU + t * 0.4;
  vec3 p = vec3(cos(a) * 1.85, (s.x - 0.5) * 0.05, sin(a) * 1.85);
  return rotZ(rotX(p, 0.42), -0.18) + vec3(0.0, 0.55, 0.0);
}

vec3 fStore(vec4 s, float t) {
  if (s.z < 0.62) {
    // A holographic floor: grid lines that ripple outwards from the deck.
    float line = floor(s.x * 25.0) / 24.0 * 2.0 - 1.0;
    float along = s.y * 2.0 - 1.0;
    vec2 g = s.w < 0.5 ? vec2(line, along) : vec2(along, line);
    g *= vec2(4.2, 2.8);
    float d = length(g);
    float y = -1.35 + sin(d * 2.2 - t * 1.6) * 0.05 * smoothstep(4.0, 0.5, d);
    return vec3(g.x, y, g.y);
  }
  // The glow behind the deck: a flattened, slowly turning ellipsoid.
  float u = s.x * 2.0 - 1.0;
  float phi = s.y * TAU + t * 0.07;
  float k = sqrt(1.0 - u * u);
  float rad = pow(s.w, 0.5);
  return vec3(cos(phi) * k * 3.1, u * 1.75, sin(phi) * k * 0.6 - 1.1) * rad;
}

/** The orbital path of time; the JS camera rig evaluates the very same curve. */
vec3 chronoPath(float u) {
  float z = -u * 120.0;
  return vec3(sin(u * 7.0) * 4.2, sin(u * 11.0 + 1.3) * 1.6, z);
}

vec3 fChronology(vec4 s, float t) {
  float u = fract(s.x + t * 0.0045);
  vec3 c = chronoPath(u);
  vec3 tangent = normalize(chronoPath(u + 0.002) - c);
  vec3 n = normalize(cross(tangent, vec3(0.0, 1.0, 0.0)));
  vec3 b = cross(n, tangent);
  float a = s.y * TAU + u * 40.0;
  float r = 0.35 + pow(s.w, 2.2) * 2.4;
  return c + (n * cos(a) + b * sin(a)) * r;
}

vec3 fibonacci(float i, float n) {
  float y = 1.0 - (i + 0.5) / n * 2.0;
  float r = sqrt(max(0.0, 1.0 - y * y));
  float a = i * 2.399963229728653;
  return vec3(cos(a) * r, y, sin(a) * r);
}

vec3 fNexus(vec4 s, float t) {
  float spin = t * 0.09;
  if (s.z < 0.58) {
    vec3 p = fibonacci(floor(s.x * 900.0), 900.0) * 1.62;
    p += (vec3(s.y, s.w, fract(s.x * 900.0)) - 0.5) * 0.03;
    return rotY(p, spin);
  }
  if (s.z < 0.9) {
    // Packets flowing along great-circle arcs between two nodes.
    vec3 a = fibonacci(floor(s.y * 900.0), 900.0);
    vec3 b = fibonacci(floor(s.w * 900.0), 900.0);
    float speed = 0.12 + fract(s.x * 13.7) * 0.2;
    float u = fract(s.x + t * speed);
    vec3 m = normalize(mix(a, b, u) + 1e-4);
    float lift = 1.0 + sin(u * PI) * 0.22;
    return rotY(m * 1.62 * lift, spin);
  }
  float a = s.y * TAU - t * 0.25;
  return rotX(vec3(cos(a) * 2.25, (s.x - 0.5) * 0.03, sin(a) * 2.25), 0.38);
}

vec3 fBloom(vec4 s, float t) {
  if (s.z < 0.62) {
    // A five-petalled blossom, each petal notched at its tip like a sakura petal.
    float theta = s.y * TAU;
    float petal = abs(cos(theta * 2.5));
    float notch = 1.0 - 0.22 * smoothstep(0.86, 1.0, petal) * (1.0 - abs(sin(theta * 25.0)));
    float r = pow(petal, 0.6) * notch * sqrt(s.x) * 1.9;
    vec3 p = vec3(cos(theta) * r, sin(theta) * r, (s.w - 0.5) * 0.06 - r * r * 0.08);
    return rotX(rotZ(p, t * 0.05), -0.25);
  }
  // Drifting petals.
  float y = 2.6 - fract(s.x + t * 0.025) * 5.2;
  float a = s.y * TAU + t * 0.3 + y * 0.5;
  float r = 1.4 + s.w * 2.6;
  return vec3(cos(a) * r, y, sin(a) * r * 0.6);
}

vec3 fAurum(vec4 s, float t) {
  // A (2,3) torus knot of gold dust with a soft cloud around it.
  float u = s.x * TAU + t * 0.18;
  float pq = 2.0, qq = 3.0;
  float rr = cos(qq * u) + 2.2;
  vec3 c = vec3(rr * cos(pq * u), rr * sin(pq * u), -sin(qq * u)) * 0.62;
  vec3 j = (vec3(s.y, s.w, s.z) - 0.5);
  float spread = s.z < 0.75 ? 0.12 : 0.9;
  return rotX(c + j * spread, 0.55);
}

vec3 fEmber(vec4 s, float t) {
  float y = fract(s.x + t * 0.012) * 7.0 - 3.5;
  float a = s.y * TAU + t * 0.03;
  float r = 0.6 + s.w * 4.2;
  return vec3(cos(a) * r, y, sin(a) * r * 0.5);
}

vec3 formation(int id, vec4 s, float t) {
  if (id == 0) return fHorizon(s, t);
  if (id == 1) return fCodex(s, t);
  if (id == 2) return fShowroom(s, t);
  if (id == 3) return fStore(s, t);
  if (id == 4) return fChronology(s, t);
  if (id == 5) return fNexus(s, t);
  if (id == 6) return fBloom(s, t);
  if (id == 7) return fAurum(s, t);
  return fEmber(s, t);
}

/** World-space target of a particle: the A → B blend, staggered per particle. */
vec3 targetOf(vec4 s, out float isStar, out float m) {
  isStar = isStarSeed(s);
  if (isStar > 0.5) {
    // The far sphere: fixed stars, the sky turning very slowly.
    float u = s.y * 2.0 - 1.0;
    float phi = s.z * TAU + uTime * 0.004;
    float k = sqrt(1.0 - u * u);
    float rad = 70.0 + s.x * 90.0;
    m = 1.0;
    return vec3(cos(phi) * k, u, sin(phi) * k) * rad;
  }
  vec3 a = formation(uFormA, s, uTime);
  vec3 b = formation(uFormB, s, uTime);
  a.x *= uMirror;
  b.x *= uMirror;
  a = uAnchorA + a * uScaleA;
  b = uAnchorB + b * uScaleB;
  float delay = fract(s.w * 3.17) * 0.35;
  m = smoothstep(0.0, 1.0, clamp((uMorph - delay) / 0.65, 0.0, 1.0));
  return mix(a, b, m);
}

vec4 seedOf(vec2 uv) {
  return hash42(uv * 4096.0 + 17.0);
}
`;

export const SIM_VELOCITY = glsl`
${COMMON}
${NOISE}
${FORMATIONS}
uniform float uDt;
uniform float uEnergy;
uniform float uScrollDir;
uniform vec3 uRayOrigin;
uniform vec3 uRayDir;
uniform float uPointerForce;
uniform vec3 uBurst;
uniform float uBurstTime;
uniform float uBurstStrength;
uniform float uCalm;
uniform float uInit;

void main() {
  if (uInit > 0.5) {
    gl_FragColor = vec4(0.0);
    return;
  }
  vec2 uv = gl_FragCoord.xy / resolution.xy;
  vec4 pos = texture2D(texturePosition, uv);
  vec4 vel = texture2D(textureVelocity, uv);
  vec4 s = seedOf(uv);
  float isStar, m;
  vec3 target = targetOf(s, isStar, m);

  vec3 toTarget = target - pos.xyz;
  float stiffness = isStar > 0.5 ? 2.0 : 7.5 + s.y * 4.0;
  vec3 acc = toTarget * stiffness;

  if (isStar < 0.5) {
    // Flow field, louder when the page is scrolled fast and while a morph is in flight.
    float inFlight = sin(m * PI);
    float turbulence = (0.45 + uEnergy * 2.2 + inFlight * 3.5) * uCalm;
    acc += curlNoise(pos.xyz * 0.32 + vec3(0.0, uTime * 0.07, 0.0)) * turbulence;
    // Scroll leaves a wake: matter streams against the direction of travel.
    acc.y += uScrollDir * uEnergy * 3.0 * (0.5 + s.x);

    // The cursor ray stirs: repulsion from the ray plus a swirl around it.
    vec3 rel = pos.xyz - uRayOrigin;
    vec3 closest = uRayOrigin + uRayDir * dot(rel, uRayDir);
    vec3 away = pos.xyz - closest;
    float d2 = dot(away, away);
    float fall = exp(-d2 * 1.6);
    vec3 dirAway = away * inversesqrt(d2 + 1e-4);
    acc += (dirAway * 9.0 + cross(uRayDir, dirAway) * 6.0) * fall * uPointerForce;

    // Starlight burst: a radial shock that decays in time and distance.
    float bt = uTime - uBurstTime;
    if (bt >= 0.0 && bt < 3.0) {
      vec3 bd = pos.xyz - uBurst;
      float bl = length(bd) + 1e-3;
      float shock = exp(-bt * 2.6) * exp(-bl * 0.55) * uBurstStrength;
      acc += (bd / bl) * shock * (26.0 + s.x * 30.0);
      acc += cross(bd / bl, vec3(0.0, 1.0, 0.0)) * shock * 14.0;
      vel.w = min(vel.w + shock * 0.25, 1.5);
    }
  }

  // Semi-implicit Euler with exponential damping: stable from 30 Hz to 240 Hz.
  float damping = isStar > 0.5 ? 3.0 : 4.2;
  vel.xyz = (vel.xyz + acc * uDt) * exp(-damping * uDt);
  float speed = length(vel.xyz);
  float maxSpeed = 40.0;
  if (speed > maxSpeed) vel.xyz *= maxSpeed / speed;
  // Heat: glows after a shock or at high speed, then cools.
  vel.w = max(vel.w * exp(-1.4 * uDt), clamp(speed * 0.045, 0.0, 1.0));
  gl_FragColor = vel;
}
`;

export const SIM_POSITION = glsl`
${COMMON}
${FORMATIONS}
uniform float uDt;
uniform float uInit;

void main() {
  vec2 uv = gl_FragCoord.xy / resolution.xy;
  vec4 pos = texture2D(texturePosition, uv);
  vec4 vel = texture2D(textureVelocity, uv);
  if (uInit > 0.5) {
    vec4 s = seedOf(uv);
    float isStar, m;
    vec3 target = targetOf(s, isStar, m);
    gl_FragColor = vec4(target, 1.0);
    return;
  }
  gl_FragColor = vec4(pos.xyz + vel.xyz * uDt, 1.0);
}
`;

/** Draws the particles as soft points: a core, a halo and, for the brightest, diffraction spikes. */
export const STAR_VERTEX = glsl`
${COMMON}
attribute vec2 reference;
uniform sampler2D uPosition;
uniform sampler2D uVelocity;
uniform float uTime;
uniform float uPixelRatio;
uniform float uViewportHeight;
uniform float uFovScale;
uniform float uSize;
uniform int uFormA;
uniform int uFormB;
uniform float uMorph;
uniform vec3 uTint;
uniform float uEnergy;
uniform float uFade;
uniform float uFormDim;
varying vec3 vColor;
varying float vSpikes;

vec3 palette(int id, vec4 s, float heat) {
  vec3 white = vec3(1.0, 0.97, 0.94);
  if (id == 0) return mix(mix(vec3(0.62, 0.78, 1.0), vec3(0.0, 0.44, 0.89), s.x), white, pow(1.0 - s.x, 4.0) * 0.8);
  if (id == 1) return mix(vec3(1.0, 0.78, 0.42), white, s.y * 0.6);
  if (id == 2) return mix(vec3(0.96, 0.9, 0.82), vec3(0.86, 0.22, 0.3), step(0.8, s.y));
  if (id == 3) return mix(vec3(0.0, 0.44, 0.89), white, s.y * 0.5);
  if (id == 4) return mix(vec3(0.28, 0.86, 1.0), vec3(0.62, 0.42, 1.0), s.x);
  if (id == 5) return mix(vec3(0.35, 0.4, 0.95), white, s.y * 0.55);
  if (id == 6) return mix(vec3(1.0, 0.72, 0.82), white, s.y * 0.6);
  if (id == 7) return mix(vec3(1.0, 0.76, 0.32), vec3(1.0, 0.92, 0.7), s.y);
  return mix(vec3(0.9, 0.48, 0.25), vec3(0.6, 0.6, 0.62), s.y);
}

void main() {
  vec4 p = texture2D(uPosition, reference);
  vec4 v = texture2D(uVelocity, reference);
  vec4 s = hash42(reference * 4096.0 + 17.0);
  float isStar = isStarSeed(s);
  vec4 mv = modelViewMatrix * vec4(p.xyz, 1.0);
  gl_Position = projectionMatrix * mv;

  float bright = pow(fract(s.y * 7.31 + s.z), 9.0);
  float twinkle = 0.62 + 0.38 * sin(uTime * (0.8 + s.x * 2.6) + s.z * 60.0);
  float heat = v.w;
  float worldSize = isStar > 0.5 ? (0.09 + bright * 0.75) : (0.018 + bright * 0.11);
  worldSize *= mix(1.0, twinkle, 0.7) * (1.0 + heat * 1.4) * uSize;
  float px = worldSize * uFovScale * uViewportHeight / max(-mv.z, 0.05);
  gl_PointSize = clamp(px, 0.0, 64.0) * uPixelRatio;

  float m = smoothstep(0.0, 1.0, clamp((uMorph - fract(s.w * 3.17) * 0.35) / 0.65, 0.0, 1.0));
  vec3 base = isStar > 0.5
    ? mix(vec3(0.72, 0.82, 1.0), vec3(1.0, 0.9, 0.78), s.x)
    : mix(palette(uFormA, s, heat), palette(uFormB, s, heat), m);
  base = mix(base, base * uTint * 1.6, 0.18);
  base = mix(base, vec3(1.0), clamp(heat * 0.8, 0.0, 0.85));
  float intensity = (isStar > 0.5 ? 0.55 : 0.85 * uFormDim) * (0.35 + bright * 2.6) * mix(1.0, twinkle, 0.5);
  intensity *= 1.0 + uEnergy * 0.6;
  // Sub-pixel points fade instead of popping.
  intensity *= clamp(px * uPixelRatio * 0.6, 0.0, 1.0);
  vColor = base * intensity * uFade;
  vSpikes = bright * step(2.0, px);
}
`;

export const STAR_FRAGMENT = glsl`
varying vec3 vColor;
varying float vSpikes;
void main() {
  vec2 c = gl_PointCoord * 2.0 - 1.0;
  float d = dot(c, c);
  if (d > 1.0) discard;
  float core = exp(-d * 14.0);
  float halo = exp(-d * 3.2) * 0.22;
  float spikes = (exp(-abs(c.x) * 28.0) * exp(-abs(c.y) * 2.2) + exp(-abs(c.y) * 28.0) * exp(-abs(c.x) * 2.2)) * vSpikes * 0.55;
  float a = core + halo + spikes;
  gl_FragColor = vec4(vColor * a, 1.0);
}
`;
