#!/usr/bin/env python3
"""Turn the owner's Aurora Corvus artwork into the brand assets this site
actually uses: the header mark, the favicon set, and the Open Graph share card.

Since 2026-10-03 the favicon set and the share card are the owner's raven icon
(assets/img/brand/corvus-tile.png: the black-metal raven with the cyan edge,
cut from their artwork on its own rounded tile). The bird silhouette below
(corvus-source.jpg) now makes only the header mark the old stylesheet masks.

Run it only when the source artwork changes:

    python3 scripts/make_brand_assets.py

It is NOT part of scripts/build.py — the outputs are committed binaries, and
regenerating them on every page build would churn the repo for nothing.

Sources of truth: assets/img/brand/corvus-tile.png (the icon) and
corvus-source.jpg (the silhouette), committed next to this script so the whole
set is reproducible instead of being a pile of mystery binaries. Requires
Pillow (`pip install Pillow`); if it is missing this script says so and exits,
it does not silently skip outputs.

Key technique: the source is a clean black-on-white silhouette, so the
INVERTED luminance is already a perfect alpha channel — black (lum 0)
becomes fully opaque, white (lum 255) fully transparent, and the JPEG's
antialiased edges survive as partial alpha instead of being thresholded
into jaggies. No tracing or upscaling guesswork needed.

Honest caveat: the raven icon is black on black with one cyan edge, so at
16px a favicon is mostly a dark tile with a cyan arc. It is the owner's design
and ships as drawn; a lifted small-size variant is a choice for them to make.
"""
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps
except ImportError:  # pragma: no cover - environment problem, not a code path
    raise SystemExit(
        "ERROR: Pillow is not installed, so the brand assets cannot be regenerated. "
        "Install it with `python3 -m pip install Pillow` and re-run. (The committed "
        "assets in assets/img/brand/ are still valid - you only need this to rebuild them.)")

ROOT = Path(__file__).resolve().parent.parent
BRAND = ROOT / "assets" / "img" / "brand"
SRC = BRAND / "corvus-source.jpg"
TILE = BRAND / "corvus-tile.png"
RAVEN_EDGE = (64, 196, 255)   # the cyan of the raven's edge, for the share card's halo

# Corvus palette, taken from the live site's dark theme (style.css).
# 2026-09-10: the aurora mint (140,240,205) and violet (139,123,255) became the
# sky-blue family the site moved to — the old tile's glow and the share card were
# the last two surfaces still carrying the old colours. The names are kept so the
# call sites below read the same; the values are what changed.
INK = (10, 12, 16)          # near-black page ground
AURORA = (90, 200, 250)     # --accent  (#5ac8fa)
AURORA_VIOLET = (10, 132, 255)   # Apple system blue, the deep end of the band

# Candidate faces for the share card's wordmark, best first. Every entry is
# optional: if none of them resolve the card is still rendered, just without
# the wordmark, and the script says so rather than dying or faking a font.
_WORDMARK_FONTS = [
    "/System/Library/Fonts/SFNSDisplay.ttf",
    "/System/Library/Fonts/SFNS.ttf",
    "/System/Library/Fonts/HelveticaNeue.ttc",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


def load_mark():
    """RGBA image of just the bird, transparent background, cropped tight."""
    if not SRC.exists():
        raise SystemExit(
            f"ERROR: {SRC} is missing. The brand assets are generated from the owner's "
            f"original artwork, which is committed alongside this script - restore it "
            f"before regenerating, rather than editing the PNGs by hand.")
    im = Image.open(SRC).convert("L")
    alpha = ImageOps.invert(im)     # alpha = how dark the pixel is

    # The source is a JPEG, so its "white" background is really 250-254 with
    # compression noise scattered through it. Without this clamp every stray
    # speck counts as content, getbbox() returns almost the whole canvas, and
    # the mark never gets cropped. Linear ramp between the two knees so the
    # antialiased edges survive instead of turning into jaggies.
    LO, HI = 45, 205
    alpha = alpha.point(lambda v: 0 if v <= LO else (255 if v >= HI else
                                                     round((v - LO) * 255 / (HI - LO))))
    alpha = alpha.crop(alpha.getbbox())
    mark = Image.new("RGBA", alpha.size, (0, 0, 0, 255))
    mark.putalpha(alpha)
    return mark


def load_tile():
    """The owner's raven icon: RGBA, the rounded tile opaque, transparent round it."""
    if not TILE.exists():
        raise SystemExit(
            f"ERROR: {TILE} is missing. The favicons and the share card are the owner's "
            f"raven icon, committed alongside this script - restore it before regenerating.")
    tile = Image.open(TILE).convert("RGBA")
    return tile.crop(tile.getchannel("A").getbbox())


def icon_square(tile, size, ground=None):
    """The tile, its aspect kept, centred on a square: transparent, or on an opaque
    `ground` where the platform wants one (Apple's touch icon masks its own corners)."""
    t = fit_into(tile, size, size)
    canvas = Image.new("RGBA", (size, size), ground + (255,) if ground else (0, 0, 0, 0))
    canvas.alpha_composite(t, ((size - t.width) // 2, (size - t.height) // 2))
    return canvas


def tinted(mark, rgb):
    solid = Image.new("RGBA", mark.size, rgb + (255,))
    solid.putalpha(mark.getchannel("A"))
    return solid


def fit_into(mark, box_w, box_h):
    w, h = mark.size
    scale = min(box_w / w, box_h / h)
    return mark.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.LANCZOS)


def _ico(path, roomy, compact, sizes):
    """Write a multi-size .ico, choosing the right art variant per size.

    PIL's own ICO writer takes one image and downsamples it for every entry,
    which would force a single bird_scale across the whole ladder. Writing the
    container by hand lets 16/32px use the compact variant while 128/256px
    keep the roomy one. Each entry is stored as a PNG, which every Windows
    since Vista and every browser reads.
    """
    import struct
    from io import BytesIO

    blobs = []
    for s in sizes:
        buf = BytesIO()
        (compact if s <= 48 else roomy).resize((s, s), Image.LANCZOS).save(buf, format="PNG")
        blobs.append((s, buf.getvalue()))

    header = struct.pack("<HHH", 0, 1, len(blobs))          # reserved, type=icon, count
    offset = len(header) + 16 * len(blobs)
    entries, payload = b"", b""
    for s, blob in blobs:
        # 256 is stored as 0 in the single-byte width/height fields.
        entries += struct.pack("<BBBBHHII", s if s < 256 else 0, s if s < 256 else 0,
                               0, 0, 1, 32, len(blob), offset)
        payload += blob
        offset += len(blob)
    path.write_bytes(header + entries + payload)


def _load_font(size):
    for path in _WORDMARK_FONTS:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size), Path(path).name
            except OSError:
                continue
    return None, None


def og_card(tile, width=1200, height=630):
    """The 1200x630 Open Graph share card: the site's own dark aurora ground,
    the raven icon, and the wordmark. Same recipe as the page background in
    style.css (soft radial washes over near-black), composed here so link
    previews look like the site rather than like a blank rectangle."""
    card = Image.new("RGBA", (width, height), INK + (255,))

    # Two soft aurora washes, matching .sky__aurora's green + violet.
    for (cx, cy, rad, rgb, peak) in (
        (0.24 * width, 0.20 * height, 0.62 * width, AURORA, 46),
        (0.80 * width, 0.16 * height, 0.55 * width, AURORA_VIOLET, 40),
        (0.55 * width, 0.92 * height, 0.60 * width, (70, 168, 255), 26),
    ):
        layer = Image.new("L", (width, height), 0)
        d = ImageDraw.Draw(layer)
        steps = 72
        for i in range(steps, 0, -1):
            rr = rad * i / steps
            d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr],
                      fill=round(peak * (1 - i / steps) ** 1.5))
        layer = layer.filter(ImageFilter.GaussianBlur(width * 0.03))
        card = Image.composite(Image.new("RGBA", card.size, rgb + (255,)), card, layer)

    # The icon, left of the wordmark, optically centred as a pair. It is black on a
    # near-black ground, so a faint halo in its own cyan and a soft shadow lift it off.
    side = round(height * 0.375)
    bird = fit_into(tile, side, side)

    def place(x, y):
        nonlocal card
        r = round(bird.width * 0.22)
        halo = Image.new("L", card.size, 0)
        ImageDraw.Draw(halo).rounded_rectangle([x - 6, y - 6, x + bird.width + 6, y + bird.height + 6],
                                               radius=r, fill=round(255 * 0.22))
        halo = halo.filter(ImageFilter.GaussianBlur(bird.width * 0.12))
        card = Image.composite(Image.new("RGBA", card.size, RAVEN_EDGE + (255,)), card, halo)
        shadow = Image.new("L", card.size, 0)
        ImageDraw.Draw(shadow).rounded_rectangle([x + 4, y + 14, x + bird.width - 4, y + bird.height + 10],
                                                 radius=r, fill=150)
        shadow = shadow.filter(ImageFilter.GaussianBlur(14))
        card = Image.composite(Image.new("RGBA", card.size, (0, 0, 0, 255)), card, shadow)
        card.alpha_composite(bird, (x, y))

    font, font_name = _load_font(round(height * 0.155))
    text = "Corvus"
    if font is not None:
        d = ImageDraw.Draw(card)
        bbox = d.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        gap = round(width * 0.035)
        total = bird.width + gap + tw
        x = (width - total) // 2
        place(x, (height - bird.height) // 2 - round(height * 0.03))
        d = ImageDraw.Draw(card)
        d.text((x + bird.width + gap - bbox[0],
                (height - th) // 2 - bbox[1] - round(height * 0.03)),
               text, font=font, fill=(242, 245, 250, 255))
    else:
        print("  NOTE: no wordmark font found on this machine "
              f"(tried {len(_WORDMARK_FONTS)} paths) - share card rendered with the mark only.")
        place((width - bird.width) // 2, (height - bird.height) // 2 - round(height * 0.03))
        font_name = None

    # Standfirst line.
    small, _ = _load_font(round(height * 0.045))
    if small is not None:
        d = ImageDraw.Draw(card)
        # Brand line, not a disclaimer. The "unofficial" wording lives in the
        # site footer where a disclaimer belongs; a share card that leads with
        # what the site ISN'T reads as apologetic in every feed it appears in.
        sub = "Sorakazekarasu Server — Mod Reference"
        bb = d.textbbox((0, 0), sub, font=small)
        d.text(((width - (bb[2] - bb[0])) // 2 - bb[0], round(height * 0.74)),
               sub, font=small, fill=(170, 180, 198, 255))

    if font_name:
        print(f"  share card wordmark set in {font_name}")
    return card.convert("RGB")


def main():
    BRAND.mkdir(parents=True, exist_ok=True)
    mark = load_mark()
    print(f"source mark cropped to {mark.size} ({mark.size[0] / mark.size[1]:.3f}:1)")

    # 1. The header mark. Only ONE file ships: style.css uses it as a
    #    mask-image filled with currentColor, so the same silhouette comes out
    #    white on the dark theme and ink on the light one. Its alpha channel is
    #    the payload; the white fill is just so it is viewable on its own.
    tinted(mark, (255, 255, 255)).save(BRAND / "corvus-mark.png")

    # 2. Favicons: the owner's raven icon, as drawn.
    tile = load_tile()
    icon = icon_square(tile, 1024)
    icon_square(tile, 180, ground=(0, 0, 0)).save(BRAND / "apple-touch-icon.png")
    icon.resize((32, 32), Image.LANCZOS).save(BRAND / "favicon-32.png")
    icon.resize((16, 16), Image.LANCZOS).save(BRAND / "favicon-16.png")
    _ico(BRAND / "favicon.ico", icon, icon, [16, 32, 48, 64, 128, 256])

    # 3. Open Graph / Twitter share card.
    og_card(tile).save(BRAND / "og-image.png", optimize=True)

    for p in sorted(BRAND.iterdir()):
        print(f"  {p.name:28} {p.stat().st_size:>9,} bytes")


if __name__ == "__main__":
    sys.exit(main())
