"use client";

import { useEffect, useRef, useState } from "react";
import { chime } from "@/engine/audio";
import { Icon } from "./Icon";

/**
 * Copies a value to the clipboard; the icon becomes a check and the label "Copied" for two
 * seconds. A refused clipboard changes nothing (as before), so a failure is never reported as
 * a success.
 */
export function CopyButton({ text, label, done, className }: { text: string; label: string; done: string; className?: string }) {
  const [copied, setCopied] = useState(false);
  const timer = useRef<number | null>(null);
  useEffect(
    () => () => {
      if (timer.current !== null) window.clearTimeout(timer.current);
    },
    [],
  );
  return (
    <button
      type="button"
      className={`ac-copy ${className ?? ""}`}
      aria-label={label}
      title={label}
      data-copied={copied}
      onClick={async () => {
        try {
          await navigator.clipboard.writeText(text);
        } catch {
          return;
        }
        chime("tick");
        setCopied(true);
        if (timer.current !== null) window.clearTimeout(timer.current);
        timer.current = window.setTimeout(() => setCopied(false), 2000);
      }}
    >
      <Icon name={copied ? "check" : "copy"} size={14} />
      <span aria-live="polite">{copied ? done : label}</span>
    </button>
  );
}
