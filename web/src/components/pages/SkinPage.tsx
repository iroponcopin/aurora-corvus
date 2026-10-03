import { Formation } from "@/engine/store";
import { FRESH } from "@/i18n/fresh";
import { recipeIcon } from "@/lib/site";
import { langData, wiki } from "@/lib/wiki";
import type { Lang } from "@/lib/wiki-types";
import { RealmAnchor } from "../RealmAnchor";
import { Showroom } from "../skin/Showroom";

const SPARXIE: readonly [number, number, number] = [0.98, 0.42, 0.5];

export function SkinPage({ lang }: { lang: Lang }) {
  const d = langData(lang);
  const w = wiki();
  const s = d.skin;
  const f = FRESH[lang].skin;
  // The blade she draws is ASTRAEA's Celestial Blade, from the recipe sheet's own icon.
  const blade = recipeIcon(w.recipes.items["astraea:celestial_blade"]?.icon ?? null);
  const pub = w.skinPublic;
  // Public: the PIN's strings stay out of the page (they would otherwise ride along, unseen, in the props).
  const labels =
    pub === null
      ? s.labels
      : { ...s.labels, lede: "", pinLabel: "", unlock: "", working: "", wrong: "", locked: "", lockedHint: "", unlocked: "", blobError: "" };
  return (
    <RealmAnchor config={{ formation: Formation.Showroom, x: 0.3, xNarrow: 0.5, y: 0.52, scale: 0.36, scaleNarrow: 0.3, tint: SPARXIE }}>
      <div className="ac-wrap ac-page-head">
        <h1 className="ac-h1">{s.title}</h1>
      </div>
      <div className="ac-wrap ac-sk-wrap">
        <Showroom
          labels={labels}
          fresh={f}
          preview={FRESH[lang].skinPreview}
          publicSkin={pub === null ? null : { file: pub.file, name: pub.name }}
          publicLede={FRESH[lang].skinPublic.lede}
          gate={{ blob: w.skinGate.blob, plainName: w.skinGate.plain_name, plainSha256: w.skinGate.plain_sha256, plainBytes: w.skinGate.plain_bytes }}
          bladeIcon={blade}
        />
      </div>
    </RealmAnchor>
  );
}
