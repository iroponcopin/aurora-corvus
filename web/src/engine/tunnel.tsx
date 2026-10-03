"use client";

import { Fragment, type ReactNode, useEffect, useId, useSyncExternalStore } from "react";

/**
 * A tunnel from the page's DOM tree into the one persistent <Canvas>: a page component
 * declares 3D children with <SceneIn>, and <SceneOut> (inside the canvas) renders them with
 * React Three Fiber's reconciler. The canvas — and the WebGL context — survive navigation;
 * only the tunnelled scenes come and go with the page.
 */

const entries = new Map<string, ReactNode>();
const listeners = new Set<() => void>();
let snapshot: ReactNode[] = [];

function emit(): void {
  const next: ReactNode[] = [];
  for (const [id, node] of entries) next.push(<Fragment key={id}>{node}</Fragment>);
  snapshot = next;
  for (const l of listeners) l();
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

function getSnapshot(): ReactNode[] {
  return snapshot;
}

const EMPTY: ReactNode[] = [];
function getServerSnapshot(): ReactNode[] {
  return EMPTY;
}

export function SceneIn({ children }: { children: ReactNode }): null {
  const id = useId();
  useEffect(() => {
    entries.set(id, children);
    emit();
  }, [id, children]);
  useEffect(
    () => () => {
      entries.delete(id);
      emit();
    },
    [id],
  );
  return null;
}

export function SceneOut(): ReactNode {
  const nodes = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
  return <>{nodes}</>;
}
