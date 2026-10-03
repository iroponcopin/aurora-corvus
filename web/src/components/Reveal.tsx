"use client";

import { usePathname } from "next/navigation";
import { useEffect } from "react";

/**
 * One IntersectionObserver for the page: every `.ac-reveal` fades up once when it enters the
 * viewport (CSS does the motion; this only flips `data-in`). Re-scans after each navigation.
 */
export function Reveal() {
  const pathname = usePathname();
  useEffect(() => {
    const els = Array.from(document.querySelectorAll<HTMLElement>(".ac-reveal:not([data-in='true'])"));
    if (!("IntersectionObserver" in window)) {
      for (const el of els) el.dataset.in = "true";
      return;
    }
    const io = new IntersectionObserver(
      (entries) => {
        for (const e of entries) {
          if (e.isIntersecting) {
            (e.target as HTMLElement).dataset.in = "true";
            io.unobserve(e.target);
          }
        }
      },
      { rootMargin: "0px 0px -8% 0px", threshold: 0.12 },
    );
    for (const el of els) io.observe(el);
    return () => io.disconnect();
  }, [pathname]);
  return null;
}
