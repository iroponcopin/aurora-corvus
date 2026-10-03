import { BufferAttribute, BufferGeometry, Float32BufferAttribute } from "three";

/** A (u, v) grid in [0,1]²; the ring shader turns it into any superellipse torus. */
export function ringGrid(segmentsU: number, segmentsV: number): BufferGeometry {
  const positions = new Float32Array((segmentsU + 1) * (segmentsV + 1) * 3);
  let k = 0;
  for (let j = 0; j <= segmentsV; j++) {
    for (let i = 0; i <= segmentsU; i++) {
      positions[k++] = i / segmentsU;
      positions[k++] = j / segmentsV;
      positions[k++] = 0;
    }
  }
  const index: number[] = [];
  const row = segmentsU + 1;
  for (let j = 0; j < segmentsV; j++) {
    for (let i = 0; i < segmentsU; i++) {
      const a = j * row + i;
      const b = a + 1;
      const c = a + row;
      const d = c + 1;
      index.push(a, c, b, b, c, d);
    }
  }
  const g = new BufferGeometry();
  g.setAttribute("position", new BufferAttribute(positions, 3));
  g.setIndex(index);
  return g;
}

/**
 * A round brilliant, after Tolkowsky's proportions: table 53 %, crown angle 34.5°,
 * pavilion angle 40.75°. Eight-fold: table, 8 bezels, 8 stars, 16 upper and 16 lower girdle
 * facets, 8 pavilion mains and the culet. Flat-shaded (each facet has its own normal).
 */
export function brilliantGeometry(): BufferGeometry {
  const n = 8;
  const girdleR = 1;
  const tableR = 0.53;
  const crownH = Math.tan((34.5 * Math.PI) / 180) * (girdleR - tableR);
  const pavilionH = Math.tan((40.75 * Math.PI) / 180) * girdleR;
  const girdleHalf = 0.012;
  const ring = (count: number, r: number, y: number, phase: number): [number, number, number][] =>
    Array.from({ length: count }, (_, i) => {
      const a = ((i + phase) / count) * Math.PI * 2;
      return [Math.cos(a) * r, y, Math.sin(a) * r];
    });

  const table = ring(n, tableR, crownH + girdleHalf, 0);
  const starTips = ring(n, (tableR + girdleR) * 0.5 + 0.06, crownH * 0.52 + girdleHalf, 0.5);
  const girdleTop = ring(n * 2, girdleR, girdleHalf, 0);
  const girdleBottom = ring(n * 2, girdleR, -girdleHalf, 0);
  const lowerTips = ring(n, girdleR * 0.52, -pavilionH * 0.55, 0.5);
  const culet: [number, number, number] = [0, -pavilionH, 0];
  const tableCenter: [number, number, number] = [0, crownH + girdleHalf, 0];

  const tris: number[] = [];
  const push = (a: number[], b: number[], c: number[]): void => {
    tris.push(a[0]!, a[1]!, a[2]!, b[0]!, b[1]!, b[2]!, c[0]!, c[1]!, c[2]!);
  };
  const at = <T,>(arr: T[], i: number): T => arr[((i % arr.length) + arr.length) % arr.length]!;

  for (let i = 0; i < n; i++) {
    // Table.
    push(tableCenter, at(table, i + 1), at(table, i));
    // Star facet: two table corners and the star tip between them.
    push(at(table, i), at(table, i + 1), at(starTips, i));
    // Bezel (kite): table corner, star tips either side, girdle point below the corner.
    push(at(table, i), at(starTips, i), at(girdleTop, 2 * i));
    push(at(table, i), at(girdleTop, 2 * i), at(starTips, i - 1));
    // Upper girdle facets: star tip to the girdle on either side of the midpoint.
    push(at(starTips, i), at(girdleTop, 2 * i + 1), at(girdleTop, 2 * i));
    push(at(starTips, i), at(girdleTop, 2 * i + 2), at(girdleTop, 2 * i + 1));
  }
  for (let i = 0; i < n * 2; i++) {
    // Girdle band.
    push(at(girdleTop, i), at(girdleTop, i + 1), at(girdleBottom, i));
    push(at(girdleBottom, i), at(girdleTop, i + 1), at(girdleBottom, i + 1));
  }
  for (let i = 0; i < n; i++) {
    // Lower girdle facets and pavilion mains.
    push(at(girdleBottom, 2 * i), at(girdleBottom, 2 * i + 1), at(lowerTips, i));
    push(at(girdleBottom, 2 * i + 1), at(girdleBottom, 2 * i + 2), at(lowerTips, i));
    push(at(girdleBottom, 2 * i), at(lowerTips, i), culet);
    push(at(lowerTips, i), at(girdleBottom, 2 * i + 2), culet);
  }

  // Every facet faces outwards: flip any triangle whose normal points at the stone's centre.
  const cy = (crownH - pavilionH) * 0.5;
  for (let t = 0; t < tris.length; t += 9) {
    const ax = tris[t]!, ay = tris[t + 1]!, az = tris[t + 2]!;
    const bx = tris[t + 3]!, by = tris[t + 4]!, bz = tris[t + 5]!;
    const qx = tris[t + 6]!, qy = tris[t + 7]!, qz = tris[t + 8]!;
    const ux = bx - ax, uy = by - ay, uz = bz - az;
    const vx = qx - ax, vy = qy - ay, vz = qz - az;
    const nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx;
    const mx = (ax + bx + qx) / 3, my = (ay + by + qy) / 3 - cy, mz = (az + bz + qz) / 3;
    if (nx * mx + ny * my + nz * mz < 0) {
      tris[t + 3] = qx;
      tris[t + 4] = qy;
      tris[t + 5] = qz;
      tris[t + 6] = bx;
      tris[t + 7] = by;
      tris[t + 8] = bz;
    }
  }
  const g = new BufferGeometry();
  g.setAttribute("position", new Float32BufferAttribute(tris, 3));
  g.computeVertexNormals();
  return g;
}

/** Sixteen vertices and thirty-two edges of the tesseract, as 4D endpoint pairs. */
export function tesseractEdges(): { a: Float32Array; b: Float32Array; count: number } {
  const verts: number[][] = [];
  for (let i = 0; i < 16; i++) {
    verts.push([i & 1 ? 1 : -1, i & 2 ? 1 : -1, i & 4 ? 1 : -1, i & 8 ? 1 : -1]);
  }
  const a: number[] = [];
  const b: number[] = [];
  for (let i = 0; i < 16; i++) {
    for (let bit = 0; bit < 4; bit++) {
      const j = i ^ (1 << bit);
      if (j > i) {
        a.push(...verts[i]!);
        b.push(...verts[j]!);
      }
    }
  }
  return { a: new Float32Array(a), b: new Float32Array(b), count: a.length / 4 };
}

/** A unit quad strip for ribbons: x along the edge (0..1), y across it (-1..1). */
export function ribbonQuad(): BufferGeometry {
  const g = new BufferGeometry();
  g.setAttribute(
    "position",
    new Float32BufferAttribute([0, -1, 0, 1, -1, 0, 1, 1, 0, 0, -1, 0, 1, 1, 0, 0, 1, 0], 3),
  );
  return g;
}

/** One triangle covering the viewport (no seam down the diagonal, unlike a quad). */
export function fullscreenTriangle(): BufferGeometry {
  const g = new BufferGeometry();
  g.setAttribute("position", new Float32BufferAttribute([-1, -1, 0, 3, -1, 0, -1, 3, 0], 3));
  return g;
}

/** A centred quad in [-1,1]² for billboards. */
export function billboardQuad(): BufferGeometry {
  const g = new BufferGeometry();
  g.setAttribute(
    "position",
    new Float32BufferAttribute([-1, -1, 0, 1, -1, 0, 1, 1, 0, -1, -1, 0, 1, 1, 0, -1, 1, 0], 3),
  );
  return g;
}
