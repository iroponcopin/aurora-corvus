"use client";

import { useEffect, useRef, useState } from "react";
import { Texture } from "three";
import { chime } from "@/engine/audio";
import { burst } from "@/engine/store";
import { Stage3D } from "@/engine/View";
import { openSealed, sha256Hex, WrongPin } from "@/realms/acsk";
import { type Pose, type Rig, SkinModel } from "@/realms/SkinModel";
import { asset, wikiFile } from "@/lib/site";
import type { SkinLabels } from "@/lib/wiki-types";
import { Icon } from "../Icon";
import { Rich } from "../Rich";

type Status = "locked" | "working" | "wrong" | "error" | "open";

export interface ShowroomFresh {
  lighting: string;
  rigs: Record<Rig, string>;
  motion: string;
  idle: string;
  combat: string;
  outerLayer: string;
  resetView: string;
  sealedModel: string;
}

async function textureFrom(png: Uint8Array): Promise<Texture> {
  const blob = new Blob([png.slice().buffer], { type: "image/png" });
  try {
    const bitmap = await createImageBitmap(blob, { imageOrientation: "flipY" });
    const t = new Texture(bitmap);
    t.flipY = false;
    t.needsUpdate = true;
    return t;
  } catch {
    // Browsers without ImageBitmap orientation: an <img> and three's own flip.
    const url = URL.createObjectURL(blob);
    const img = await new Promise<HTMLImageElement>((resolve, reject) => {
      const i = new Image();
      i.onload = () => resolve(i);
      i.onerror = reject;
      i.src = url;
    });
    const t = new Texture(img);
    t.needsUpdate = true;
    return t;
  }
}

/**
 * Sparxie's showroom. The skin is sealed on the server (downloads/sparxie-skin.acsk); the PIN,
 * which the owner hands out and which is written nowhere on this site, opens it in this
 * browser alone. Until then the model is a hologram of the skeleton; afterwards it wears the
 * skin, and the PNG can be saved.
 */
export function Showroom({
  labels,
  fresh,
  preview,
  gate,
  bladeIcon,
}: {
  labels: SkinLabels;
  fresh: ShowroomFresh;
  /** Sparxie's two public renders (front, three-quarter): what she looks like, for everyone. */
  preview: { title: string; note: string; front: string; side: string };
  gate: { blob: string; plainName: string; plainSha256: string; plainBytes: number };
  bladeIcon: string | null;
}) {
  const [status, setStatus] = useState<Status>("locked");
  const [pin, setPin] = useState("");
  const [texture, setTexture] = useState<Texture | null>(null);
  const [href, setHref] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const [pose, setPose] = useState<Pose>("stand");
  const [walk, setWalk] = useState(false);
  const [breathe, setBreathe] = useState(true);
  const [rig, setRig] = useState<Rig>("studio");
  const [outer, setOuter] = useState(true);
  const yaw = useRef(0.5);
  const pitch = useRef(0.05);
  const drag = useRef<{ x: number; y: number; id: number } | null>(null);

  useEffect(
    () => () => {
      if (href !== null) URL.revokeObjectURL(href);
    },
    [href],
  );

  const unlock = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    if (pin === "" || status === "working") return;
    setStatus("working");
    try {
      const res = await fetch(wikiFile(gate.blob), { cache: "no-cache" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const sealed = new Uint8Array(await res.arrayBuffer());
      const plain = await openSealed(sealed, pin);
      if (plain.length !== gate.plainBytes || (await sha256Hex(plain)) !== gate.plainSha256) throw new Error("checksum");
      setPin("");
      setTexture(await textureFrom(plain));
      setHref(URL.createObjectURL(new Blob([plain.slice().buffer], { type: "image/png" })));
      setStatus("open");
      chime("unlock");
      burst(0, 0, 0, 1.2);
    } catch (err) {
      setStatus(err instanceof WrongPin ? "wrong" : "error");
      chime("error");
    }
  };

  const choosePose = (p: Pose): void => {
    setPose(p);
    setWalk(false);
    chime("tick");
  };

  const message =
    status === "working" ? labels.working : status === "wrong" ? labels.wrong : status === "error" ? labels.blobError : labels.lockedHint;

  return (
    <div className="ac-sk">
      <div className="ac-sk-stage-col">
        <div
          className="ac-sk-stage"
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
            className="ac-sk-canvas"
            fov={30}
            position={[0, 0.15, 7.2]}
            fallback={
              <>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img className="ac-sk-poster" src={asset("wiki/skin/sparxie-front.png")} alt="Sparxie" />
                <p className="ac-small ac-sk-nogl">{labels.noWebgl}</p>
              </>
            }
          >
            <SkinModel
              texture={texture}
              pose={pose}
              walk={walk}
              breathe={breathe}
              rig={rig}
              outer={outer}
              bladeIcon={bladeIcon}
              yaw={yaw}
              pitch={pitch}
            />
          </Stage3D>
          <div className="ac-sk-badge" data-open={status === "open"}>
            <Icon name={status === "open" ? "unlock" : "lock"} size={14} />
            <span>{status === "open" ? labels.unlocked : labels.locked}</span>
          </div>
          <button
            type="button"
            className="ac-iconbtn ac-sk-reset"
            aria-label={fresh.resetView}
            title={fresh.resetView}
            onClick={() => {
              yaw.current = 0.5;
              pitch.current = 0.05;
            }}
          >
            <Icon name="rotate" size={15} />
          </button>
        </div>
        <p className="ac-small ac-sk-drag">{labels.drag}</p>
      </div>

      <div className="ac-sk-side">
        <p className="ac-lead">
          <Rich text={labels.lede} />
        </p>

        <figure className="ac-sk-preview">
          <div className="ac-sk-preview-row">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={asset("wiki/skin/sparxie-front.png")} alt={`Sparxie — ${preview.front}`} width={321} height={722} />
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={asset("wiki/skin/sparxie-model.png")} alt={`Sparxie — ${preview.side}`} width={332} height={750} />
          </div>
          <figcaption>
            <b>{preview.title}</b>
            <span className="ac-small">{preview.note}</span>
          </figcaption>
        </figure>

        <div className="ac-sk-controls" role="group" aria-label={labels.pose}>
          <span className="ac-small">{labels.pose}</span>
          {(["stand", "wave", "t", "sit"] as const).map((p) => (
            <button key={p} type="button" className="ac-chip" aria-pressed={pose === p && !walk} onClick={() => choosePose(p)}>
              {labels.poses[p]}
            </button>
          ))}
          <button
            type="button"
            className="ac-chip"
            aria-pressed={walk}
            onClick={() => {
              setWalk((w) => !w);
              setPose("stand");
              chime("tick");
            }}
          >
            {labels.walk}
          </button>
        </div>

        <div className="ac-sk-controls" role="group" aria-label={fresh.motion}>
          <span className="ac-small">{fresh.motion}</span>
          <button type="button" className="ac-chip" aria-pressed={breathe} onClick={() => setBreathe((b) => !b)}>
            {fresh.idle}
          </button>
          <button type="button" className="ac-chip" aria-pressed={pose === "draw"} onClick={() => choosePose(pose === "draw" ? "stand" : "draw")}>
            {fresh.combat}
          </button>
          <button type="button" className="ac-chip" aria-pressed={outer} onClick={() => setOuter((o) => !o)}>
            {fresh.outerLayer}
          </button>
        </div>

        <div className="ac-sk-controls" role="group" aria-label={fresh.lighting}>
          <span className="ac-small">{fresh.lighting}</span>
          {(["studio", "rim", "neon", "dusk"] as const).map((r) => (
            <button
              key={r}
              type="button"
              className="ac-chip"
              aria-pressed={rig === r}
              onClick={() => {
                setRig(r);
                chime("tick");
              }}
            >
              <span className={`ac-rig-dot ac-rig-dot--${r}`} aria-hidden="true" />
              {fresh.rigs[r]}
            </button>
          ))}
        </div>

        {status !== "open" ? (
          <form className="ac-sk-pin ac-card" autoComplete="off" onSubmit={(e) => void unlock(e)}>
            <label htmlFor="sk-pin" className="ac-small">
              {labels.pinLabel}
            </label>
            <div className="ac-sk-pin-row">
              <input
                id="sk-pin"
                className="ac-input ac-pin-input"
                type="password"
                inputMode="numeric"
                autoComplete="off"
                autoCorrect="off"
                spellCheck={false}
                name="access-code"
                aria-describedby="sk-msg"
                aria-invalid={status === "wrong" ? true : undefined}
                value={pin}
                onChange={(e) => setPin(e.target.value)}
              />
              <button type="submit" className="ac-btn" disabled={pin === "" || status === "working"}>
                {status === "working" ? labels.working : labels.unlock}
              </button>
            </div>
            <p id="sk-msg" className="ac-small ac-sk-msg" role="status" data-bad={status === "wrong" || status === "error"}>
              {message}
            </p>
            <button type="button" className="ac-btn ac-btn--ghost ac-btn--small" disabled aria-disabled="true">
              <Icon name="download" size={14} />
              {labels.downloadPng}
            </button>
          </form>
        ) : (
          <div className="ac-sk-open ac-card">
            <p className="ac-small">{labels.locked === "" ? "" : labels.unlocked}</p>
            {href !== null ? (
              <a className="ac-btn ac-sk-download" href={href} download={gate.plainName} onClick={() => setSaved(true)}>
                <Icon name="download" size={16} />
                {labels.downloadPng}
              </a>
            ) : null}
            {saved ? (
              <p className="ac-small" role="status">
                {labels.done}
              </p>
            ) : null}
          </div>
        )}

        <p className="ac-small">
          <Rich text={labels.note} />
        </p>
        <p className="ac-small">{labels.slim}</p>
      </div>
    </div>
  );
}
