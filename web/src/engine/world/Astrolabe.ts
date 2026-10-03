import {
  AdditiveBlending,
  BackSide,
  BoxGeometry,
  DoubleSide,
  FrontSide,
  Group,
  InstancedBufferAttribute,
  InstancedBufferGeometry,
  type IUniform,
  Mesh,
  Quaternion,
  ShaderMaterial,
  Vector2,
  Vector3,
  Vector4,
} from "three";
import {
  DIAMOND_FRAGMENT,
  GEM_FRAGMENT,
  GEM_VERTEX,
  GLOW_FRAGMENT,
  GLOW_VERTEX,
  RING_VERTEX,
  TEETH_FRAGMENT,
  TEETH_VERTEX,
  TESSERACT_FRAGMENT,
  TESSERACT_VERTEX,
  TITANIUM_FRAGMENT,
} from "../shaders/astrolabe";
import { damp, integrateQuat, quatPool, vec3Pool } from "../math";
import { engine } from "../store";
import { billboardQuad, brilliantGeometry, ribbonQuad, ringGrid, tesseractEdges } from "./geometry";
import type { SharedUniforms } from "./uniforms";

interface RingSpec {
  /** Major radius, axial half-height, radial half-thickness, superellipse exponent. */
  shape: [number, number, number, number];
  /** RGB tint (F0 tint for titanium, transmission tint for diamond), engraving/facet scale. */
  look: [number, number, number, number];
  diamond: boolean;
  /** Initial orientation as successive rotations about X then Z (radians). */
  tiltX: number;
  tiltZ: number;
  /** Angular velocity, radians per second about world axes. */
  omega: [number, number, number];
}

/**
 * Seven rings on three families of rotation axes. The limb faces the viewer and carries the
 * graduation and teeth; meridian and gimbals sweep around it; the three diamond bands cross
 * between them. Every ring's pose is a quaternion integrated from its own angular velocity.
 */
const RINGS: RingSpec[] = [
  { shape: [1.0, 0.07, 0.026, 8], look: [1, 1, 1, 1], diamond: false, tiltX: Math.PI / 2, tiltZ: 0, omega: [0, 0, 0.035] },
  { shape: [0.88, 0.034, 0.034, 4], look: [0.86, 0.93, 1, 1], diamond: true, tiltX: 1.16, tiltZ: 0.26, omega: [0, 0.11, 0] },
  { shape: [0.79, 0.05, 0.02, 6], look: [1, 0.97, 0.93, 1], diamond: false, tiltX: 0, tiltZ: Math.PI / 2, omega: [0, 0.19, 0] },
  { shape: [0.68, 0.028, 0.028, 3], look: [0.9, 0.86, 1, 1], diamond: true, tiltX: 0.18, tiltZ: 0, omega: [0.07, 0, 0.05] },
  { shape: [0.57, 0.04, 0.017, 8], look: [0.95, 0.97, 1, 0], diamond: false, tiltX: 0.87, tiltZ: 0.52, omega: [0.21, 0.13, 0] },
  { shape: [0.46, 0.022, 0.022, 2.6], look: [1, 0.9, 0.95, 1], diamond: true, tiltX: -1.05, tiltZ: 0.61, omega: [-0.1, 0.25, 0.17] },
  { shape: [0.35, 0.018, 0.011, 4], look: [1, 1, 1, 0], diamond: false, tiltX: Math.PI / 2, tiltZ: 0.3, omega: [0.3, -0.2, 0.4] },
];

const TEETH = 180;

export class Astrolabe {
  readonly group = new Group();
  private readonly ringQuats: Quaternion[] = [];
  private readonly ringQuatU: Vector4[] = [];
  private readonly groupQuat = new Quaternion();
  private readonly groupQuatU = new Vector4(0, 0, 0, 1);
  private readonly groupPosU = new Vector3();
  private readonly gemQuat = new Quaternion();
  private readonly gemQuatU = new Vector4(0, 0, 0, 1);
  private readonly rot4 = new Vector4();
  private readonly resolution = new Vector2(1, 1);
  private readonly presence: IUniform<number> = { value: 0 };
  private readonly pulse: IUniform<number> = { value: 0 };
  private readonly groupScale: IUniform<number> = { value: 1 };
  private readonly materials: ShaderMaterial[] = [];
  private readonly baseTilt = new Quaternion();
  private readonly target = quatPool.take();
  private readonly tmpQ = quatPool.take();
  private readonly tmpQ2 = quatPool.take();
  private readonly axisX = new Vector3(1, 0, 0);
  private readonly axisY = new Vector3(0, 1, 0);
  private readonly axisZ = new Vector3(0, 0, 1);
  private readonly center = vec3Pool.take();
  /** World-space centre and radius of the instrument (for the marks, picking and bursts). */
  readonly worldCenter = new Vector3();
  worldRadius = 1;

  constructor(shared: SharedUniforms) {
    for (const spec of RINGS) {
      const q = new Quaternion().setFromAxisAngle(this.axisX, spec.tiltX);
      q.premultiply(this.tmpQ.setFromAxisAngle(this.axisZ, spec.tiltZ));
      this.ringQuats.push(q);
      this.ringQuatU.push(new Vector4(q.x, q.y, q.z, q.w));
    }
    this.baseTilt.setFromAxisAngle(this.axisX, -0.2);
    this.groupQuat.copy(this.baseTilt);

    const ringShape = RINGS.map((r) => new Vector4(...r.shape));
    const ringLook = RINGS.map((r) => new Vector4(...r.look));
    const common = {
      uGroupQuat: { value: this.groupQuatU },
      uGroupPos: { value: this.groupPosU },
      uGroupScale: this.groupScale,
      uPresence: this.presence,
      uTime: shared.uTime,
      uTint: shared.uTint,
      uLightPos: shared.uLightPos,
      uLightIntensity: shared.uLightIntensity,
    };
    const ringUniforms = {
      ...common,
      uRingQuat: { value: this.ringQuatU },
      uRingShape: { value: ringShape },
      uRingLook: { value: ringLook },
    };

    // Rings: one grid, two instanced draws (opaque titanium, then translucent diamond).
    const grid = ringGrid(384, 24);
    const makeRings = (indices: number[], fragment: string, diamond: boolean): Mesh => {
      const g = new InstancedBufferGeometry();
      g.index = grid.index;
      g.setAttribute("position", grid.getAttribute("position"));
      g.setAttribute("aRing", new InstancedBufferAttribute(new Float32Array(indices), 1));
      g.instanceCount = indices.length;
      const m = new ShaderMaterial({
        vertexShader: RING_VERTEX,
        fragmentShader: fragment,
        uniforms: ringUniforms,
        transparent: diamond,
        depthWrite: !diamond,
        side: DoubleSide,
      });
      this.materials.push(m);
      const mesh = new Mesh(g, m);
      mesh.frustumCulled = false;
      mesh.renderOrder = diamond ? 6 : 2;
      return mesh;
    };
    const titaniumIdx: number[] = [];
    const diamondIdx: number[] = [];
    RINGS.forEach((r, i) => (r.diamond ? diamondIdx : titaniumIdx).push(i));
    this.group.add(makeRings(titaniumIdx, TITANIUM_FRAGMENT, false));
    this.group.add(makeRings(diamondIdx, DIAMOND_FRAGMENT, true));

    // Teeth around the limb.
    const box = new BoxGeometry(1, 1, 1);
    const teeth = new InstancedBufferGeometry();
    teeth.index = box.index;
    teeth.setAttribute("position", box.getAttribute("position"));
    teeth.setAttribute("normal", box.getAttribute("normal"));
    const angles = new Float32Array(TEETH);
    const long = new Float32Array(TEETH);
    for (let i = 0; i < TEETH; i++) {
      angles[i] = (i / TEETH) * Math.PI * 2;
      long[i] = i % 10 === 0 ? 1 : i % 5 === 0 ? 0.5 : 0;
    }
    teeth.setAttribute("aAngle", new InstancedBufferAttribute(angles, 1));
    teeth.setAttribute("aLong", new InstancedBufferAttribute(long, 1));
    teeth.instanceCount = TEETH;
    const teethMat = new ShaderMaterial({
      vertexShader: TEETH_VERTEX,
      fragmentShader: TEETH_FRAGMENT,
      uniforms: ringUniforms,
    });
    this.materials.push(teethMat);
    const teethMesh = new Mesh(teeth, teethMat);
    teethMesh.frustumCulled = false;
    teethMesh.renderOrder = 2;
    this.group.add(teethMesh);

    // The brilliant at the centre: back faces first, then front faces.
    const gem = brilliantGeometry();
    const gemUniforms = { ...common, uGemQuat: { value: this.gemQuatU }, uGemScale: { value: 0.15 }, uPulse: this.pulse };
    const back = new ShaderMaterial({
      vertexShader: GEM_VERTEX,
      fragmentShader: GEM_FRAGMENT,
      uniforms: { ...gemUniforms, uBack: { value: 1 } },
      side: BackSide,
      transparent: true,
      depthWrite: false,
    });
    const front = new ShaderMaterial({
      vertexShader: GEM_VERTEX,
      fragmentShader: GEM_FRAGMENT,
      uniforms: { ...gemUniforms, uBack: { value: 0 } },
      side: FrontSide,
      transparent: true,
      depthWrite: false,
    });
    this.materials.push(back, front);
    const gemBack = new Mesh(gem, back);
    const gemFront = new Mesh(gem, front);
    gemBack.frustumCulled = false;
    gemFront.frustumCulled = false;
    gemBack.renderOrder = 4;
    gemFront.renderOrder = 5;
    this.group.add(gemBack, gemFront);

    // The tesseract around the stone.
    const edges = tesseractEdges();
    const quad = ribbonQuad();
    const tess = new InstancedBufferGeometry();
    tess.setAttribute("position", quad.getAttribute("position"));
    tess.setAttribute("aA", new InstancedBufferAttribute(edges.a, 4));
    tess.setAttribute("aB", new InstancedBufferAttribute(edges.b, 4));
    tess.instanceCount = edges.count;
    const tessMat = new ShaderMaterial({
      vertexShader: TESSERACT_VERTEX,
      fragmentShader: TESSERACT_FRAGMENT,
      uniforms: {
        ...common,
        uRot: { value: this.rot4 },
        uW: { value: 2.6 },
        uSize: { value: 0.135 },
        uResolution: { value: this.resolution },
        uWidth: { value: 1.6 },
      },
      transparent: true,
      depthWrite: false,
      blending: AdditiveBlending,
    });
    this.materials.push(tessMat);
    const tessMesh = new Mesh(tess, tessMat);
    tessMesh.frustumCulled = false;
    tessMesh.renderOrder = 7;
    this.group.add(tessMesh);

    // Glow of the singularity.
    const glowMat = new ShaderMaterial({
      vertexShader: GLOW_VERTEX,
      fragmentShader: GLOW_FRAGMENT,
      uniforms: { ...common, uGlowSize: { value: 0.62 }, uPulse: this.pulse },
      transparent: true,
      depthWrite: false,
      depthTest: false,
      blending: AdditiveBlending,
    });
    this.materials.push(glowMat);
    const glow = new Mesh(billboardQuad(), glowMat);
    glow.frustumCulled = false;
    glow.renderOrder = 8;
    this.group.add(glow);
  }

  /**
   * One frame: integrate every ring's rotation, follow the pointer with the whole instrument,
   * turn the tesseract through the fourth dimension. `presenceTarget` fades it in and out.
   */
  update(
    dt: number,
    center: Vector3,
    scale: number,
    presenceTarget: number,
    viewportW: number,
    viewportH: number,
  ): void {
    const p = this.presence;
    p.value = damp(p.value, presenceTarget, 3.2, dt);
    this.group.visible = p.value > 0.002;
    this.center.copy(center);
    this.worldCenter.copy(center);
    this.worldRadius = scale;
    if (!this.group.visible) return;

    const calm = engine.reducedMotion ? 0.12 : 1;
    const spin = (1 + engine.energy * 5.5) * calm;
    for (let i = 0; i < RINGS.length; i++) {
      const spec = RINGS[i]!;
      const q = this.ringQuats[i]!;
      integrateQuat(q, spec.omega[0] * spin, spec.omega[1] * spin, spec.omega[2] * spin, dt);
      this.ringQuatU[i]!.set(q.x, q.y, q.z, q.w);
    }

    // The instrument leans towards the pointer (critically damped through slerp).
    this.tmpQ.setFromAxisAngle(this.axisY, engine.pointerSX * 0.38 * engine.mirror);
    this.tmpQ2.setFromAxisAngle(this.axisX, -engine.pointerSY * 0.26);
    this.target.copy(this.baseTilt).premultiply(this.tmpQ2).premultiply(this.tmpQ);
    this.groupQuat.slerp(this.target, 1 - Math.exp(-4 * dt));
    this.groupQuatU.set(this.groupQuat.x, this.groupQuat.y, this.groupQuat.z, this.groupQuat.w);
    this.groupPosU.copy(this.center);
    this.groupScale.value = scale;

    // The stone turns on its own axis, table towards the viewer.
    const t = engine.time;
    this.tmpQ.setFromAxisAngle(this.axisX, 1.18 + Math.sin(t * 0.4) * 0.08);
    this.tmpQ2.setFromAxisAngle(this.axisY, t * 0.32 * calm);
    this.gemQuat.copy(this.tmpQ).multiply(this.tmpQ2);
    this.gemQuatU.set(this.gemQuat.x, this.gemQuat.y, this.gemQuat.z, this.gemQuat.w);

    const w = t * calm;
    this.rot4.set(w * 0.31, w * 0.23 + 0.6, w * 0.17 + 1.1, w * 0.11);
    this.resolution.set(viewportW, viewportH);
    this.pulse.value = 0.5 + 0.5 * Math.sin(t * 1.3) * (0.6 + engine.energy);
  }

  get presenceValue(): number {
    return this.presence.value;
  }

  dispose(): void {
    for (const m of this.materials) m.dispose();
    this.group.traverse((o) => {
      if (o instanceof Mesh) o.geometry.dispose();
    });
  }
}
