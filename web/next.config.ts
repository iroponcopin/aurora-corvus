import type { NextConfig } from "next";

/**
 * The portal is a static export laid over the repository root, which GitHub Pages
 * serves at https://iroponcopin.github.io/aurora-corvus/. Japanese is the primary
 * language and lives at the root without a prefix; the app routes it through the
 * `[lang]` segment as `ja`, and `scripts/finalize-export.mjs` moves `out/ja/**` to
 * `out/**` after the build. In development the same mapping is a rewrite.
 */
const BASE_PATH = "/aurora-corvus";
const PREFIXED = ["en", "es", "fr", "zh", "ko", "pt-br", "it", "ar", "ru", "id", "de", "tr", "ja"];

const isDev = process.env.NODE_ENV === "development";

const config: NextConfig = {
  basePath: BASE_PATH,
  trailingSlash: true,
  reactStrictMode: true,
  poweredByHeader: false,
  images: { unoptimized: true },
  env: { NEXT_PUBLIC_BASE_PATH: BASE_PATH },
  ...(isDev
    ? {
        async rewrites() {
          const notPrefixed = `(?!${PREFIXED.join("|")}|_next|portal|downloads|data|assets)`;
          return {
            beforeFiles: [
              { source: "/", destination: "/ja/" },
              { source: `/:first${notPrefixed}:rest*/`, destination: "/ja/:first:rest*/" },
            ],
            afterFiles: [],
            fallback: [],
          };
        },
      }
    : { output: "export" as const }),
};

export default config;
