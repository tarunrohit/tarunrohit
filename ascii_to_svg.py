#!/usr/bin/env python3
"""
ascii_to_svg.py
Converts a portrait photo into a stipple / dot-matrix "VISUAL.MAP" style
SVG portrait, in a dark-theme and light-theme color variant.

Usage:
    python3 ascii_to_svg.py headshot.jpg --cols 46 --rows 60
"""
import argparse
from PIL import Image, ImageOps, ImageFilter, ImageChops


def _auto_crop_to_subject(edge_strength, threshold=14, margin_frac=0.06):
    """Find the bounding box of foreground (high edge-strength) pixels and
    return a slightly-padded crop box around it, so the final portrait is
    framed tightly instead of carrying empty headroom."""
    w, h = edge_strength.size
    mask = edge_strength.point(lambda v: 255 if v > threshold else 0)
    bbox = mask.getbbox()
    if not bbox:
        return (0, 0, w, h)
    left, top, right, bottom = bbox
    mw = int((right - left) * margin_frac)
    mh = int((bottom - top) * margin_frac)
    left = max(0, left - mw)
    top = max(0, top - mh)
    right = min(w, right + mw)
    bottom = min(h, bottom + mh)
    return (left, top, right, bottom)


def build_portrait_grid(image_path, cols, rows, crop_box=None):
    """Separate subject from a (possibly gradient/vignette) studio backdrop
    using a high-pass filter: subtract a heavily-blurred version of the
    image (an estimate of the smooth lighting/backdrop) from the original.
    Wherever that difference is small, we're looking at smooth background;
    wherever it's large, we're looking at the subject's edges/features."""
    full_gray = Image.open(image_path).convert("L")
    w, h = full_gray.size

    # Large-radius blur approximates the smooth backdrop + lighting gradient,
    # since the subject's fine detail washes out at this radius while the
    # slowly-varying backdrop survives.
    big_blur_radius = max(w, h) / 6
    backdrop_estimate = full_gray.filter(ImageFilter.GaussianBlur(radius=big_blur_radius))
    edge_strength = ImageChops.difference(full_gray, backdrop_estimate)

    tone = full_gray.filter(ImageFilter.GaussianBlur(radius=1))

    if crop_box == "auto":
        crop_box = _auto_crop_to_subject(edge_strength)
    if crop_box:
        tone = tone.crop(crop_box)
        edge_strength = edge_strength.crop(crop_box)

    tone_small = tone.resize((cols, rows), Image.LANCZOS)
    edge_small = edge_strength.resize((cols, rows), Image.LANCZOS)

    tone_px = list(tone_small.getdata())
    edge_px = list(edge_small.getdata())

    grid = []
    for r in range(rows):
        row = list(zip(tone_px[r * cols:(r + 1) * cols], edge_px[r * cols:(r + 1) * cols]))
        grid.append(row)
    return grid


def grid_to_svg(grid, cell=10, dot_color="#67e8f9", bg=None,
                 edge_threshold=14, gamma=0.8):
    rows = len(grid)
    cols = len(grid[0])
    width = cols * cell
    height = rows * cell

    fg_tones = [tone for row in grid for (tone, edge) in row if edge > edge_threshold]
    if not fg_tones:
        fg_tones = [tone for row in grid for (tone, edge) in row]
    fg_min, fg_max = min(fg_tones), max(fg_tones)
    fg_range = max(fg_max - fg_min, 1)

    parts = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
                  f'viewBox="0 0 {width} {height}">')
    if bg:
        parts.append(f'<rect width="{width}" height="{height}" fill="{bg}"/>')

    max_r = cell * 0.48
    for r in range(rows):
        for c in range(cols):
            tone, edge = grid[r][c]
            if edge <= edge_threshold:
                continue  # smooth backdrop — leave empty

            # Normalize within the foreground's own tonal range, then invert
            # so darker foreground pixels (hair, suit, brows) get the
            # biggest dots.
            norm = (tone - fg_min) / fg_range  # 0..1, 0 = darkest foreground
            darkness = (1 - norm) ** gamma
            radius = max_r * darkness
            if radius < 0.4:
                continue
            cx = c * cell + cell / 2
            cy = r * cell + cell / 2
            parts.append(
                f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{radius:.2f}" fill="{dot_color}"/>'
            )
    parts.append("</svg>")
    return "\n".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--cols", type=int, default=46)
    ap.add_argument("--rows", type=int, default=60)
    ap.add_argument("--cell", type=int, default=10)
    ap.add_argument("--out-prefix", default="portrait")
    args = ap.parse_args()

    grid = build_portrait_grid(args.image, args.cols, args.rows, crop_box="auto")

    dark_svg = grid_to_svg(grid, cell=args.cell, dot_color="#5eead4", bg="#0b0f17")
    light_svg = grid_to_svg(grid, cell=args.cell, dot_color="#0f172a", bg="#f8fafc")

    with open(f"{args.out_prefix}-dark.svg", "w") as f:
        f.write(dark_svg)
    with open(f"{args.out_prefix}-light.svg", "w") as f:
        f.write(light_svg)

    print(f"Wrote {args.out_prefix}-dark.svg and {args.out_prefix}-light.svg "
          f"({args.cols}x{args.rows} grid, cell={args.cell}px)")


if __name__ == "__main__":
    main()
