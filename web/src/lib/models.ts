/**
 * The Models menu of the header and the footer, in the owner's order: the id (its icon is
 * icons/<id>.png and its availability the Store's), the name, and its page relative to the
 * language root. ASTRAEA, Tsubomi and Noctua have no page of their own; their card in the Store does.
 */
export const MODELS: readonly (readonly [id: string, name: string, href: string])[] = [
  ["astraea", "ASTRAEA", "launcher/#astraea"],
  ["ouka", "OUKA", "ouka/"],
  ["cherry", "Cherry", "cherry/"],
  ["tsubomi", "Tsubomi", "launcher/#tsubomi"],
  ["aureum", "Aureum", "aureum/"],
  ["noctua", "Noctua", "launcher/#noctua"],
];
