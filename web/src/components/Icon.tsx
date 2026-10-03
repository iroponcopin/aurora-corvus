import type { SVGProps } from "react";

/** A handful of 24-unit stroke icons (Lucide geometry), drawn inline so they inherit colour. */
const PATHS = {
  chevronDown: "M6 9l6 6 6-6",
  globe:
    "M12 2a10 10 0 1 0 0 20a10 10 0 1 0 0-20zM2 12h20M12 2a15.3 15.3 0 0 1 4 10a15.3 15.3 0 0 1-4 10a15.3 15.3 0 0 1-4-10a15.3 15.3 0 0 1 4-10z",
  menu: "M4 6h16M4 12h16M4 18h16",
  x: "M18 6L6 18M6 6l12 12",
  copy: "M9 9h11v11H9zM5 15H4a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v1",
  check: "M20 6L9 17l-5-5",
  download: "M12 3v12M7 10l5 5 5-5M5 21h14",
  play: "M7 4l13 8-13 8z",
  pause: "M7 4h4v16H7zM15 4h4v16h-4z",
  search: "M11 4a7 7 0 1 0 0 14a7 7 0 1 0 0-14zM21 21l-4.3-4.3",
  volume: "M11 5L6 9H2v6h4l5 4zM15.5 8.5a5 5 0 0 1 0 7M19 5a10 10 0 0 1 0 14",
  mute: "M11 5L6 9H2v6h4l5 4zM22 9l-6 6M16 9l6 6",
  lock: "M5 11h14v10H5zM8 11V7a4 4 0 0 1 8 0v4",
  unlock: "M5 11h14v10H5zM8 11V7a4 4 0 0 1 7.5-2",
  arrowRight: "M5 12h14M13 6l6 6-6 6",
  external: "M14 4h6v6M10 14L20 4M19 13v7H4V5h7",
  rotate: "M3 12a9 9 0 1 0 3-6.7L3 8M3 3v5h5",
  sparkle: "M12 3l1.8 5.6L19.5 10l-5.7 1.6L12 17l-1.8-5.4L4.5 10l5.7-1.4z",
  terminal: "M4 17l6-6-6-6M12 19h8",
  skipBack: "M19 20L9 12l10-8zM5 19V5",
  skipForward: "M5 4l10 8-10 8zM19 5v14",
  heart: "M19 14c1.5-1.5 3-3.2 3-5.5A5.5 5.5 0 0 0 12 5a5.5 5.5 0 0 0-10 3.5c0 2.3 1.5 4 3 5.5l7 7z",
  speaker: "M4 4h16v16H4zM12 14a2 2 0 1 0 0-4a2 2 0 0 0 0 4zM12 7h.01",
  compass: "M12 2a10 10 0 1 0 0 20a10 10 0 1 0 0-20zM16 8l-2 6-6 2 2-6z",
  blocks: "M3 3h8v8H3zM13 3h8v8h-8zM3 13h8v8H3zM13 17h8M17 13v8",
  library: "M4 4v16M8 4v16M12 4l4 16M17 4h3v16h-3",
  refresh: "M3 12a9 9 0 0 1 15-6.7L21 8M21 3v5h-5M21 12a9 9 0 0 1-15 6.7L3 16M3 21v-5h5",
  user: "M12 12a4 4 0 1 0 0-8a4 4 0 0 0 0 8zM4 21a8 8 0 0 1 16 0",
  stop: "M7 7h10v10H7z",
  shuffle: "M16 3h5v5M4 20L21 3M21 16v5h-5M15 15l6 6M4 4l5 5",
  repeat: "M17 2l4 4-4 4M3 11V10a4 4 0 0 1 4-4h14M7 22l-4-4 4-4M21 13v1a4 4 0 0 1-4 4H3",
  airplay: "M5 17H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2h-1M12 15l5 6H7z",
} as const;

export type IconName = keyof typeof PATHS;

export function Icon({
  name,
  size = 18,
  strokeWidth = 1.7,
  ...rest
}: { name: IconName; size?: number; strokeWidth?: number } & Omit<SVGProps<SVGSVGElement>, "name">) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
      {...rest}
    >
      <path d={PATHS[name]} />
    </svg>
  );
}
