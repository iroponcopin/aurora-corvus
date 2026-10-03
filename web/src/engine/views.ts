import type { PerspectiveCamera, Scene } from "three";
import type { Tracked } from "./tracked";

/**
 * Viewports: a scene drawn by the shared renderer exactly inside a DOM element's box (scissor
 * test), so a page can embed live 3D (the skin showroom, the synthesiser) without a second
 * WebGL context. The canvas sits behind the page; the element above it stays transparent.
 */
export interface ViewEntry {
  tracked: Tracked;
  scene: Scene;
  camera: PerspectiveCamera;
  order: number;
  /** Last aspect the camera's projection was built for. */
  aspect: number;
  /** Called by the pipeline right before the view is drawn (only when visible). */
  beforeRender: ((dt: number, view: ViewEntry) => void) | null;
}

export const views: ViewEntry[] = [];

export function addView(v: ViewEntry): void {
  views.push(v);
  // Insertion by order (registration time only).
  views.sort((a, b) => a.order - b.order);
}

export function removeView(v: ViewEntry): void {
  const i = views.indexOf(v);
  if (i >= 0) views.splice(i, 1);
}
