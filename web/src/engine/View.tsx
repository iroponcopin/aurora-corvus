"use client";

import { createPortal } from "@react-three/fiber";
import {
  createContext,
  type ReactNode,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { PerspectiveCamera, Scene } from "three";
import { track, untrack } from "./tracked";
import { SceneIn } from "./tunnel";
import { addView, removeView, type ViewEntry } from "./views";

type FrameCb = (dt: number, view: ViewEntry) => void;

interface ViewApi {
  /** Register a per-frame callback that runs only while the view is on screen. */
  subscribe: (cb: FrameCb) => () => void;
  el: HTMLElement;
  camera: PerspectiveCamera;
}

const ViewContext = createContext<ViewApi | null>(null);

export function useViewApi(): ViewApi {
  const api = useContext(ViewContext);
  if (api === null) throw new Error("useViewApi outside a <Stage3D>");
  return api;
}

/** Like useFrame, but only called while the view's element is visible. */
export function useViewFrame(cb: FrameCb): void {
  const api = useViewApi();
  const ref = useRef(cb);
  ref.current = cb;
  useEffect(() => {
    const stable: FrameCb = (dt, v) => ref.current(dt, v);
    return api.subscribe(stable);
  }, [api]);
}

function ViewScene({
  el,
  fov,
  position,
  order,
  children,
}: {
  el: HTMLElement;
  fov: number;
  position: readonly [number, number, number];
  order: number;
  children: ReactNode;
}) {
  const scene = useMemo(() => new Scene(), []);
  const camera = useMemo(() => {
    const c = new PerspectiveCamera(fov, 1, 0.1, 200);
    c.position.set(position[0], position[1], position[2]);
    c.lookAt(0, 0, 0);
    return c;
    // The camera is created once per view; later prop changes move it through `useViewApi`.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  const callbacks = useRef<FrameCb[]>([]);
  const api = useMemo<ViewApi>(
    () => ({
      el,
      camera,
      subscribe: (cb) => {
        callbacks.current.push(cb);
        return () => {
          const i = callbacks.current.indexOf(cb);
          if (i >= 0) callbacks.current.splice(i, 1);
        };
      },
    }),
    [el, camera],
  );

  useEffect(() => {
    const tracked = track(el);
    const list = callbacks.current;
    const entry: ViewEntry = {
      tracked,
      scene,
      camera,
      order,
      aspect: 0,
      beforeRender: (dt, v) => {
        for (let i = 0; i < list.length; i++) list[i]!(dt, v);
      },
    };
    addView(entry);
    return () => {
      removeView(entry);
      untrack(tracked);
    };
  }, [el, scene, camera, order]);

  return createPortal(<ViewContext.Provider value={api}>{children}</ViewContext.Provider>, scene, { camera });
}

/**
 * A DOM box with live 3D inside it, drawn by the page's one WebGL context (scissored to the
 * box). Without WebGL the fallback (a poster) shows instead; with it the box stays transparent
 * and the scene renders behind the page, exactly where the box is.
 */
export function Stage3D({
  children,
  fallback,
  className,
  label,
  fov = 30,
  position = [0, 0, 8],
  order = 0,
  style,
}: {
  children: ReactNode;
  fallback?: ReactNode;
  className?: string;
  label?: string;
  fov?: number;
  position?: readonly [number, number, number];
  order?: number;
  style?: React.CSSProperties;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [el, setEl] = useState<HTMLDivElement | null>(null);
  useEffect(() => setEl(ref.current), []);
  return (
    <div
      ref={ref}
      className={`ac-stage ${className ?? ""}`}
      role={label ? "img" : undefined}
      aria-label={label}
      aria-hidden={label ? undefined : true}
      style={style}
    >
      {fallback ? <div className="ac-stage-poster ac-only-fallback">{fallback}</div> : null}
      {el !== null ? (
        <SceneIn>
          <ViewScene el={el} fov={fov} position={position} order={order}>
            {children}
          </ViewScene>
        </SceneIn>
      ) : null}
    </div>
  );
}
