"use client";

import { useEffect, useState } from "react";
import { getWorld, type World } from "./world/World";

/** The live WebGL world once the canvas is up (null before, or forever without WebGL). */
export function useWorld(): World | null {
  const [world, setWorld] = useState<World | null>(() => getWorld());
  useEffect(() => {
    if (world !== null) return;
    let raf = 0;
    let tries = 0;
    const poll = (): void => {
      const w = getWorld();
      if (w !== null) {
        setWorld(w);
        return;
      }
      // Give up quietly after ~20 s (no WebGL, or the device opted out).
      if (++tries < 1200 && document.documentElement.dataset.webgl !== "off") raf = requestAnimationFrame(poll);
    };
    raf = requestAnimationFrame(poll);
    return () => cancelAnimationFrame(raf);
  }, [world]);
  return world;
}
