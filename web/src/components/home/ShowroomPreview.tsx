"use client";

import { useEffect, useRef, useState } from "react";
import { chime } from "@/engine/audio";
import { addFrameHook } from "@/engine/loop";
import { engine } from "@/engine/store";
import { Stage3D } from "@/engine/View";
import { type Pose, SkinModel } from "@/realms/SkinModel";
import { asset } from "@/lib/site";
import { Icon } from "../Icon";

type Motion = "idle" | "walk" | "combat";

/**
 * The showroom realm on the home page: Sparxie's skeleton as a hologram (the skin itself stays
 * sealed until the skin page opens it with the PIN), turning slowly by itself, with the three
 * motions. Drag turns her.
 */
export function ShowroomPreview({
  bladeIcon,
  labels,
}: {
  bladeIcon: string | null;
  labels: { idle: string; walk: string; combat: string; motion: string; drag: string; sealed: string; noWebgl: string; portrait: string };
}) {
  const [motion, setMotion] = useState<Motion>("idle");
  const yaw = useRef(0.5);
  const pitch = useRef(0.05);
  const drag = useRef<{ x: number; y: number; id: number } | null>(null);

  // A slow turntable while nobody is dragging (none with reduced motion).
  useEffect(
    () =>
      addFrameHook((dt) => {
        if (drag.current === null && !engine.reducedMotion) yaw.current += dt * 0.35;
      }),
    [],
  );

  const pose: Pose = motion === "combat" ? "draw" : "stand";
  const choose = (m: Motion): void => {
    setMotion(m);
    chime("tick");
  };

  return (
    <div className="ac-preview ac-showroom-preview">
      <div
        className="ac-preview-stage"
        tabIndex={0}
        role="group"
        aria-label={`Sparxie: ${labels.drag}`}
        onPointerDown={(e) => {
          drag.current = { x: e.clientX, y: e.clientY, id: e.pointerId };
          e.currentTarget.setPointerCapture(e.pointerId);
        }}
        onPointerMove={(e) => {
          const d = drag.current;
          if (d === null || d.id !== e.pointerId) return;
          yaw.current += (e.clientX - d.x) * 0.012;
          pitch.current = Math.max(-0.5, Math.min(0.5, pitch.current + (e.clientY - d.y) * 0.004));
          d.x = e.clientX;
          d.y = e.clientY;
        }}
        onPointerUp={() => {
          drag.current = null;
        }}
        onPointerCancel={() => {
          drag.current = null;
        }}
        onKeyDown={(e) => {
          if (e.key === "ArrowLeft") yaw.current -= 0.3;
          if (e.key === "ArrowRight") yaw.current += 0.3;
        }}
      >
        <Stage3D
          className="ac-preview-canvas ac-preview-canvas--tall"
          fov={30}
          position={[0, 0.1, 6.4]}
          fallback={
            <>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img className="ac-sk-poster" src={asset("wiki/skin/sparxie-front.png")} alt="Sparxie" />
              <p className="ac-small">{labels.noWebgl}</p>
            </>
          }
        >
          <SkinModel
            texture={null}
            pose={pose}
            walk={motion === "walk"}
            breathe={motion === "idle"}
            rig="studio"
            outer
            bladeIcon={bladeIcon}
            yaw={yaw}
            pitch={pitch}
          />
        </Stage3D>
        <figure className="ac-sr-portrait">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={asset("wiki/skin/sparxie-front.png")} alt={labels.portrait} width={321} height={722} loading="lazy" />
        </figure>
        <p className="ac-preview-caption">
          <Icon name="lock" size={13} />
          <span className="ac-small">{labels.sealed}</span>
        </p>
      </div>
      <div className="ac-preview-controls">
        <span className="ac-small">{labels.motion}</span>
        <div className="ac-chips" role="group" aria-label={labels.motion}>
          {(["idle", "walk", "combat"] as const).map((m) => (
            <button key={m} type="button" className="ac-chip" aria-pressed={motion === m} onClick={() => choose(m)}>
              {labels[m]}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
