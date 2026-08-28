#!/usr/bin/env python3
"""Turn the owner's Aurora Corvus logo (black mark on a white JPEG) into the
brand assets this site actually uses: the header mark, the favicon set, and
the Open Graph share card.

Run it only when the source artwork changes:

    python3 scripts/make_brand_assets.py

It is NOT part of scripts/build.py — the outputs are committed binaries, and
regenerating them on every page build would churn the repo for nothing.

Source of truth: assets/img/brand/corvus-source.jpg, committed next to this
script so the whole set is reproducible instead of being a pile of mystery
binaries. Requires Pillow (`pip install Pillow`); if it is missing this
script says so and exits, it does not silently skip outputs.

Key technique: the source is a clean black-on-white silhouette, so the
INVERTED luminance is already a perfect alpha channel — black (lum 0)
becomes fully opaque, white (lum 255) fully transparent, and the JPEG's
antialiased edges survive as partial alpha instead of being thresholded
into jaggies. No tracing or upscaling guesswork needed.

Honest caveat baked into the output choices: the bare mark's trailing wing
wisps are only a pixel or two wide once you are down at 16px, where they
smear into an unreadable smudge. The favicons therefore use the dark rounded
TILE (mark on an aurora ground), which keeps a legible silhouette when tiny;
only the header mark ships as the bare transparent silhouette.
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

# Aurora Corvus palette, taken from the live site's dark theme (style.css).
INK = (10, 12, 16)          # near-black page ground
TILE_TOP = (18, 24, 33)
TILE_BOTTOM = (9, 12, 17)
AURORA = (140, 240, 205)    # --accent-strong
AURORA_VIOLET = (139, 123, 255)

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


def tinted(mark, rgb):
    solid = Image.new("RGBA", mark.size, rgb + (255,))
    solid.putalpha(mark.getchannel("A"))
    return solid


def fit_into(mark, box_w, box_h):
    w, h = mark.size
    scale = min(box_w / w, box_h / h)
    return mark.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.LANCZOS)


def rounded_mask(size, radius):
    m = Image.new("L", (size, size), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    return m


def app_icon(mark, size=1024, bird_scale=0.66):
    """macOS-style tile: inset rounded rectangle, dark aurora ground, white mark.

    bird_scale is raised for the tiny favicon sizes: the mark's trailing wing
    wisps are only a couple of pixels wide once the icon is 16px, so at normal
    padding it degrades into an unreadable smudge. Filling more of the tile
    buys back just enough resolution for the bird to stay a bird.
    """
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    inset = round(size * 0.098)             # Apple leaves the art inset in the 1024 canvas
    tile_size = size - inset * 2
    radius = round(tile_size * 0.225)       # Big Sur-era corner radius

    tile = Image.new("RGBA", (tile_size, tile_size))
    d = ImageDraw.Draw(tile)
    for y in range(tile_size):
        t = y / max(1, tile_size - 1)
        d.line([(0, y), (tile_size, y)],
               fill=tuple(round(a + (b - a) * t) for a, b in zip(TILE_TOP, TILE_BOTTOM)) + (255,))

    glow = Image.new("L", (tile_size, tile_size), 0)
    gd = ImageDraw.Draw(glow)
    cx, cy = tile_size * 0.30, tile_size * 0.22
    r = tile_size * 0.62
    steps = 64
    for i in range(steps, 0, -1):
        rr = r * i / steps
        gd.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=round(88 * (1 - i / steps) ** 1.6))
    glow = glow.filter(ImageFilter.GaussianBlur(tile_size * 0.05))
    tile = Image.composite(Image.new("RGBA", tile.size, AURORA + (255,)), tile, glow)

    hl = Image.new("L", (tile_size, tile_size), 0)
    ImageDraw.Draw(hl).rounded_rectangle(
        [0, 0, tile_size - 1, tile_size - 1], radius=radius, outline=255,
        width=max(1, round(tile_size * 0.004)))
    hl = hl.filter(ImageFilter.GaussianBlur(tile_size * 0.003))
    hl = Image.composite(hl, Image.new("L", hl.size, 0),
                         Image.linear_gradient("L").resize(hl.size).transpose(Image.FLIP_TOP_BOTTOM))
    tile = Image.composite(Image.new("RGBA", tile.size, (255, 255, 255, 255)), tile,
                           hl.point(lambda v: v // 3))

    tile.putalpha(rounded_mask(tile_size, radius))

    bird = fit_into(tinted(mark, (255, 255, 255)),
                    round(tile_size * bird_scale), round(tile_size * bird_scale))
    tile.alpha_composite(bird, ((tile_size - bird.width) // 2,
                                (tile_size - bird.height) // 2))

    canvas.alpha_composite(tile, (inset, inset))
    return canvas


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


def og_card(mark, width=1200, height=630):
    """The 1200x630 Open Graph share card: the site's own dark aurora ground,
    the mark, and the wordmark. Same recipe as the page background in
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

    # Mark, left of the wordmark, optically centred as a pair.
    bird = fit_into(tinted(mark, (255, 255, 255)), round(width * 0.30), round(height * 0.34))

    font, font_name = _load_font(round(height * 0.155))
    text = "Aurora Corvus"
    if font is not None:
        d = ImageDraw.Draw(card)
        bbox = d.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        gap = round(width * 0.035)
        total = bird.width + gap + tw
        x = (width - total) // 2
        card.alpha_composite(bird, (x, (height - bird.height) // 2 - round(height * 0.03)))
        d.text((x + bird.width + gap - bbox[0],
                (height - th) // 2 - bbox[1] - round(height * 0.03)),
               text, font=font, fill=(242, 245, 250, 255))
    else:
        print("  NOTE: no wordmark font found on this machine "
              f"(tried {len(_WORDMARK_FONTS)} paths) - share card rendered with the mark only.")
        card.alpha_composite(bird, ((width - bird.width) // 2,
                                    (height - bird.height) // 2 - round(height * 0.03)))
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

    # 2. Favicons, from the tile (see the module docstring for why not the
    #    bare mark).
    icon = app_icon(mark, 1024)
    compact = app_icon(mark, 1024, bird_scale=0.84)
    icon.resize((180, 180), Image.LANCZOS).save(BRAND / "apple-touch-icon.png")
    compact.resize((32, 32), Image.LANCZOS).save(BRAND / "favicon-32.png")
    compact.resize((16, 16), Image.LANCZOS).save(BRAND / "favicon-16.png")
    _ico(BRAND / "favicon.ico", icon, compact, [16, 32, 48, 64, 128, 256])

    # 3. Open Graph / Twitter share card.
    og_card(mark).save(BRAND / "og-image.png", optimize=True)

    for p in sorted(BRAND.iterdir()):
        print(f"  {p.name:28} {p.stat().st_size:>9,} bytes")


if __name__ == "__main__":
    sys.exit(main())
