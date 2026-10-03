import { Texture } from "three";

/**
 * A 64×64 skin PNG as a texture for SkinModel, upright in GL's convention (ImageBitmap flipped at
 * decode where the browser can, three's own flip otherwise). Used by the skin page and the home
 * showroom, for the public skin and for one opened from the sealed blob alike.
 */
export async function skinTexture(png: Uint8Array): Promise<Texture> {
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
