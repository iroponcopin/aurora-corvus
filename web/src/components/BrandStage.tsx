"use client";

import { Stage3D } from "@/engine/View";
import { IconPlate } from "@/realms/IconPlate";
import { asset } from "@/lib/site";

/** A brand's icon as a 3D plate (or, without WebGL, the icon itself). */
export function BrandStage({
  icon,
  label,
  dim = false,
  className,
}: {
  icon: string;
  label: string;
  dim?: boolean;
  className?: string;
}) {
  return (
    <Stage3D
      className={`ac-brand-stage ${className ?? ""}`}
      label={label || undefined}
      fov={30}
      position={[0, 0, 8]}
      fallback={
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={asset(icon)}
          alt=""
          width={256}
          height={256}
          style={{ width: "62%", borderRadius: "22.37%", ...(dim ? { filter: "grayscale(0.75)", opacity: 0.62 } : {}) }}
        />
      }
    >
      <IconPlate src={asset(icon)} dim={dim} />
    </Stage3D>
  );
}
