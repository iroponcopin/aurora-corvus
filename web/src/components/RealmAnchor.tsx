"use client";

import { type ReactNode, useEffect, useRef } from "react";
import { type AnchorConfig, addAnchor, removeAnchor } from "@/engine/anchors";

/**
 * A page section that tells the WebGL world which particle formation to show, where on screen
 * and how big — the realm. It renders its children as the section itself; the world follows
 * the element's box as it scrolls (measured on layout changes only).
 */
export function RealmAnchor({
  config,
  children,
  className,
  as: Tag = "section",
  id,
  ...aria
}: {
  config: AnchorConfig;
  children?: ReactNode;
  className?: string;
  as?: "section" | "div" | "header";
  id?: string;
  "aria-labelledby"?: string;
  "aria-label"?: string;
}) {
  const ref = useRef<HTMLElement | null>(null);
  const key = JSON.stringify(config);
  useEffect(() => {
    const el = ref.current;
    if (el === null) return;
    const anchor = addAnchor(el, JSON.parse(key) as AnchorConfig);
    return () => removeAnchor(anchor);
  }, [key]);
  return (
    <Tag ref={ref as never} className={className} id={id} {...aria}>
      {children}
    </Tag>
  );
}
