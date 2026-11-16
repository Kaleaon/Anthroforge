#!/usr/bin/env python3
"""
AnthroForge markings-lab: procedural marking texture generators.

Reference implementation for MARKINGS.md section 6.3 / section 8.
Generators take exactly the parameter dicts the character record stores
(MARKINGS.md section 3: generator.kind + generator.params + seed) and
resolve them to grayscale strength masks in base-UV space (0 = no marking,
255 = full marking colour).

Kinds:
  stripes  -- tiger-style branching, tapered bands from a dorsal spine
  rosettes -- broken-ring clusters (leopard/lion-cub), weaker centre
  spots    -- solid discs; tiles seamlessly (wrap-around drawing)

Deps: PIL + numpy only. Run: python3 generate_markings.py
Outputs land in ./out/
"""
import json
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
SIZE = 1024

BASE_COAT = (200, 155, 106)     # tawny ground coat
MARK_DARK = (36, 20, 7)         # near-black brown marking colour
PAPER = (24, 24, 28)            # preview sheet background


# ---------------------------------------------------------------- helpers

def ellipse_poly(cx, cy, rx, ry, rot_deg=0.0, n=14):
    """Polygon points approximating a rotated ellipse."""
    a = np.linspace(0, 2 * math.pi, n, endpoint=False)
    x = rx * np.cos(a)
    y = ry * np.sin(a)
    r = math.radians(rot_deg)
    xr = x * math.cos(r) - y * math.sin(r) + cx
    yr = x * math.sin(r) + y * math.cos(r) + cy
    return list(zip(xr.tolist(), yr.tolist()))


def composite(mask_img, base=BASE_COAT, mark=MARK_DARK):
    """Blend base coat -> marking colour by mask strength."""
    m = np.asarray(mask_img).astype(np.float32) / 255.0
    out = np.zeros((*m.shape, 3), dtype=np.float32)
    for c in range(3):
        out[..., c] = base[c] * (1 - m) + mark[c] * m
    return Image.fromarray(out.astype(np.uint8), "RGB")


# ---------------------------------------------------------------- stripes

def gen_stripes(params, size=SIZE):
    """Tiger-style branching stripes from a dorsal spine (vertical centre).

    The canvas stands in for a torso-back UV region: spine down the middle,
    stripes emanate sideways and droop toward the belly edge, tapering
    root->tip, ~branch_prob of them fork mid-length.
    """
    rng = np.random.default_rng(params.get("seed", 1))
    count = params.get("count", 46)
    width = params.get("width_px", 15)
    branch_prob = params.get("branch_prob", 0.4)
    img = Image.new("L", (size, size), 0)
    dr = ImageDraw.Draw(img)

    def spine_x(y):
        return size * 0.5 + size * 0.012 * math.sin(y / size * math.pi)

    def draw_band(x0, y0, side, length, w0, droop):
        """One tapered, wavy band as a filled polygon."""
        steps = 16
        pts, widths = [], []
        phase = rng.uniform(0, 2 * math.pi)
        for i in range(steps + 1):
            t = i / steps
            x = x0 + side * length * (t ** 0.92)
            y = y0 + droop * size * 0.10 * (t ** 1.6) \
                + math.sin(t * 3.1 + phase) * size * 0.006
            pts.append((x, y))
            widths.append(max(1.2, w0 * (1 - t) ** 0.72))
        left, right = [], []
        for i, (x, y) in enumerate(pts):
            if i < len(pts) - 1:
                dx, dy = pts[i + 1][0] - x, pts[i + 1][1] - y
            else:
                dx, dy = x - pts[i - 1][0], y - pts[i - 1][1]
            n = math.hypot(dx, dy) or 1.0
            nx, ny = -dy / n, dx / n
            left.append((x + nx * widths[i] / 2, y + ny * widths[i] / 2))
            right.append((x - nx * widths[i] / 2, y - ny * widths[i] / 2))
        dr.polygon(left + right[::-1], fill=255)
        return pts, widths

    ys = np.linspace(size * 0.04, size * 0.96, count)
    for y0 in ys:
        y0 = float(y0 + rng.normal(0, size * 0.008))
        for side in (-1, 1):
            if rng.random() < 0.08:            # occasional missing stripe
                continue
            length = size * rng.uniform(0.26, 0.40)
            w0 = width * rng.uniform(0.75, 1.3)
            pts, _ = draw_band(spine_x(y0), y0, side, length, w0,
                               droop=rng.uniform(0.5, 1.0))
            if rng.random() < branch_prob:     # fork
                bx, by = pts[len(pts) // 2]
                draw_band(bx, by, side, length * rng.uniform(0.35, 0.55),
                          w0 * 0.55, droop=rng.uniform(1.4, 2.1))
    soft = params.get("softness", 0.35)
    if soft > 0:
        img = img.filter(ImageFilter.GaussianBlur(soft * 4))
    return img


# ---------------------------------------------------------------- spots / rosettes

def gen_spots(params, size=SIZE, rosettes=False):
    """Jittered-grid spots or rosettes. Wrap-around drawing => seamless tile.

    Rosette: broken ring of 5-7 blobs around a weaker centre (~0.35 mask),
    the leopard/lion-cub pattern. Spot: solid disc at full strength.
    """
    rng = np.random.default_rng(params.get("seed", 1))
    cols = params.get("cols", 8)
    radius = params.get("radius_px", size / cols * 0.30)
    density = params.get("density", 0.92)
    img = Image.new("L", (size, size), 0)
    dr = ImageDraw.Draw(img)
    cell = size / cols

    def draw_one(cx, cy):
        R = radius * rng.uniform(0.8, 1.25)
        if not rosettes:
            dr.polygon(ellipse_poly(cx, cy, R, R * rng.uniform(0.85, 1.0)),
                       fill=255)
            return
        # weaker centre (ground-colour heart of the rosette)
        dr.polygon(ellipse_poly(cx, cy, R * 0.46, R * 0.46), fill=89)
        n = int(rng.integers(5, 8))
        a0 = rng.uniform(0, 2 * math.pi)
        for j in range(n):
            if rng.random() < 0.15:            # the ring is broken
                continue
            a = a0 + 2 * math.pi * j / n + rng.normal(0, 0.12)
            bx, by = cx + 0.74 * R * math.cos(a), cy + 0.74 * R * math.sin(a)
            dr.polygon(ellipse_poly(bx, by, R * 0.36, R * 0.22,
                                    rot_deg=math.degrees(a) + 90), fill=255)

    for gy in range(cols):
        for gx in range(cols):
            if rng.random() > density:
                continue
            cx = (gx + 0.5) * cell + rng.normal(0, cell * 0.16)
            cy = (gy + 0.5) * cell + rng.normal(0, cell * 0.16)
            for dx in (-size, 0, size):        # wrap => seamless tiling
                for dy in (-size, 0, size):
                    draw_one(cx + dx, cy + dy)
    soft = params.get("softness", 0.3)
    if soft > 0:
        img = img.filter(ImageFilter.GaussianBlur(soft * 3))
    return img


# ---------------------------------------------------------------- previews

def silhouette(size=SIZE):
    """Crude side-profile animal silhouette (placement proof only)."""
    img = Image.new("L", (size, size), 0)
    dr = ImageDraw.Draw(img)
    W = H = size
    dr.ellipse([0.20 * W, 0.33 * H, 0.76 * W, 0.65 * H], fill=255)  # torso
    dr.polygon([(0.62 * W, 0.38 * H), (0.86 * W, 0.22 * H),
                (0.90 * W, 0.34 * H), (0.70 * W, 0.50 * H)],
               fill=255)                                            # neck
    dr.ellipse([0.78 * W, 0.14 * H, 0.94 * W, 0.32 * H], fill=255)  # head
    dr.polygon([(0.88 * W, 0.24 * H), (1.00 * W, 0.30 * H),
                (0.90 * W, 0.34 * H)], fill=255)                    # muzzle
    dr.polygon([(0.80 * W, 0.16 * H), (0.83 * W, 0.05 * H),
                (0.86 * W, 0.15 * H)], fill=255)                    # ear
    for lx in (0.27, 0.35, 0.60, 0.68):                             # legs
        dr.rectangle([lx * W, 0.58 * H, (lx + 0.05) * W, 0.93 * H],
                     fill=255)
    for t in np.linspace(0, 1, 24):                                 # tail
        x = 0.20 * W - 0.13 * W * t
        y = 0.40 * H - 0.16 * H * math.sin(t * math.pi * 0.8)
        r = 0.020 * W
        dr.ellipse([x - r, y - r, x + r, y + r], fill=255)
    return img


def preview_sheet(stripes_mask, rosettes_mask, spots_mask):
    P = 512
    sheet = Image.new("RGB", (P * 3 + 32, P * 2 + 76), PAPER)
    dr = ImageDraw.Draw(sheet)

    def panel(img, col, row, label):
        x, y = 8 + col * (P + 8), 8 + row * (P + 30)
        sheet.paste(img.resize((P, P)), (x, y))
        dr.text((x + 6, y + P + 8), label, fill=(230, 230, 230))

    sil = silhouette()
    on_animal = Image.composite(composite(stripes_mask),
                                Image.new("RGB", (SIZE, SIZE), PAPER), sil)
    tiled = Image.new("L", (SIZE, SIZE))
    small = spots_mask.resize((SIZE // 2, SIZE // 2))
    for dx in (0, SIZE // 2):
        for dy in (0, SIZE // 2):
            tiled.paste(small, (dx, dy))

    panel(stripes_mask.convert("RGB"), 0, 0, "1 stripes mask (generator: stripes)")
    panel(composite(stripes_mask), 1, 0, "2 stripes over tawny base coat")
    panel(on_animal, 2, 0, "3 stripes placed through silhouette")
    panel(rosettes_mask.convert("RGB"), 0, 1, "4 rosettes mask (generator: rosettes)")
    panel(composite(rosettes_mask), 1, 1, "5 rosettes over tawny base coat")
    panel(tiled.convert("RGB"), 2, 1, "6 spots mask tiled 2x2 (seamless)")
    return sheet


# ---------------------------------------------------------------- main

def main():
    os.makedirs(OUT, exist_ok=True)
    stripe_params = {"seed": 4177, "count": 46, "width_px": 15,
                     "branch_prob": 0.4, "softness": 0.35,
                     "colour": "#241407"}
    rosette_params = {"seed": 903, "cols": 8, "radius_px": 38,
                      "density": 0.92, "softness": 0.3}
    spot_params = {"seed": 51, "cols": 9, "radius_px": 26,
                   "density": 0.9, "softness": 0.25}

    stripes = gen_stripes(stripe_params)
    rosettes = gen_spots(rosette_params, rosettes=True)
    spots = gen_spots(spot_params, rosettes=False)

    stripes.save(os.path.join(OUT, "stripes_mask.png"))
    rosettes.save(os.path.join(OUT, "rosettes_mask.png"))
    spots.save(os.path.join(OUT, "spots_mask.png"))
    preview_sheet(stripes, rosettes, spots).save(
        os.path.join(OUT, "preview_sheet.png"))
    with open(os.path.join(OUT, "params.json"), "w") as f:
        json.dump({"stripes": stripe_params, "rosettes": rosette_params,
                   "spots": spot_params}, f, indent=2)

    for name, img in (("stripes", stripes), ("rosettes", rosettes),
                      ("spots", spots)):
        a = np.asarray(img)
        print(f"{name}: coverage={100 * (a > 32).mean():.1f}%  "
              f"mean_strength={a.mean() / 255:.3f}")
    print("wrote:", sorted(os.listdir(OUT)))


if __name__ == "__main__":
    main()
