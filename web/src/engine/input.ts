import { engine } from "./store";

/**
 * Pointer input for the world: one set of passive window listeners writing numbers into the
 * engine. Handlers allocate nothing; the frame loop smooths what they write.
 */
let installed = false;

function onMove(e: PointerEvent): void {
  const w = window.innerWidth;
  const h = window.innerHeight;
  engine.pointerX = e.clientX;
  engine.pointerY = e.clientY;
  engine.pointerNX = (e.clientX / w) * 2 - 1;
  engine.pointerNY = -((e.clientY / h) * 2 - 1);
  engine.pointerInside = 1;
  engine.pointerLastMove = engine.time;
}

function onLeave(e: PointerEvent): void {
  if (e.relatedTarget === null) engine.pointerInside = 0;
}

function onBlur(): void {
  engine.pointerInside = 0;
}

export function installInput(): () => void {
  if (installed) return () => undefined;
  installed = true;
  engine.pointerX = window.innerWidth / 2;
  engine.pointerY = window.innerHeight / 2;
  window.addEventListener("pointermove", onMove, { passive: true });
  window.addEventListener("pointerdown", onMove, { passive: true });
  document.addEventListener("pointerout", onLeave, { passive: true });
  window.addEventListener("blur", onBlur);
  return () => {
    installed = false;
    window.removeEventListener("pointermove", onMove);
    window.removeEventListener("pointerdown", onMove);
    document.removeEventListener("pointerout", onLeave);
    window.removeEventListener("blur", onBlur);
  };
}

/** Whether this device should get the WebGL world at all (and why not, for the fallback). */
export function webglVerdict(): { ok: boolean; reason: string } {
  try {
    const params = new URLSearchParams(window.location.search);
    if (params.get("webgl") === "off" || params.get("stage") === "off") return { ok: false, reason: "disabled" };
    const nav = navigator as Navigator & { connection?: { saveData?: boolean }; deviceMemory?: number };
    if (nav.connection?.saveData === true) return { ok: false, reason: "save-data" };
    if ((nav.deviceMemory ?? 8) <= 2 || (nav.hardwareConcurrency ?? 8) <= 2) return { ok: false, reason: "low-end" };
    const probe = document.createElement("canvas");
    const ctx = probe.getContext("webgl2");
    if (!ctx) return { ok: false, reason: "no-webgl2" };
    const lose = ctx.getExtension("WEBGL_lose_context");
    lose?.loseContext();
    return { ok: true, reason: "" };
  } catch {
    return { ok: false, reason: "error" };
  }
}
