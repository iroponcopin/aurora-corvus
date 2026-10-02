"use client";

import { useEffect, useState } from "react";
import { engine } from "@/engine/store";

/**
 * With `?debug` in the address: the frame rate the page actually reaches and the draw calls of
 * the last frame, read twice a second from the engine (never from the frame loop itself).
 */
export function DebugHud({ labels }: { labels: { fps: string; drawCalls: string } }) {
  const [on, setOn] = useState(false);
  const [stats, setStats] = useState({ fps: 0, drawCalls: 0, dpr: 1 });

  useEffect(() => {
    if (!new URLSearchParams(window.location.search).has("debug")) return;
    setOn(true);
    let frame = engine.frame;
    let at = performance.now();
    const id = window.setInterval(() => {
      const now = performance.now();
      const fps = ((engine.frame - frame) * 1000) / Math.max(1, now - at);
      frame = engine.frame;
      at = now;
      setStats({ fps: Math.round(fps), drawCalls: engine.drawCalls, dpr: engine.dpr });
    }, 500);
    return () => window.clearInterval(id);
  }, []);

  if (!on) return null;
  return (
    <div className="ac-debug" role="status" aria-live="off" dir="ltr">
      <span>
        {labels.fps} <b>{stats.fps}</b>
      </span>
      <span>
        {labels.drawCalls} <b>{stats.drawCalls}</b>
      </span>
      <span>
        DPR <b>{stats.dpr.toFixed(2)}</b>
      </span>
    </div>
  );
}
