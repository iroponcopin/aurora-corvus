"use client";

import { useEffect, useState } from "react";
import { installSoundLifecycle, isSoundOn, onSound, setSound, soundRemembered } from "@/engine/audio";
import { Icon } from "./Icon";

/**
 * The one switch for the page's sound. Off until pressed (browsers allow audio only after a
 * gesture); a visitor who left it on last time sees it armed and one tap brings it back.
 */
export function SoundToggle({ label, on, off }: { label: string; on: string; off: string }) {
  const [active, setActive] = useState(false);
  const [armed, setArmed] = useState(false);

  useEffect(() => {
    setActive(isSoundOn());
    setArmed(soundRemembered());
    const unsub = onSound(setActive);
    const uninstall = installSoundLifecycle();
    return () => {
      unsub();
      uninstall();
    };
  }, []);

  return (
    <button
      type="button"
      className="ac-iconbtn ac-sound"
      aria-pressed={active}
      aria-label={active ? off : on}
      title={label}
      data-armed={armed && !active ? "true" : "false"}
      onClick={() => setSound(!active)}
    >
      <Icon name={active ? "volume" : "mute"} size={17} />
      <span className="ac-sound-bars" aria-hidden="true" data-on={active}>
        <i />
        <i />
        <i />
      </span>
    </button>
  );
}
