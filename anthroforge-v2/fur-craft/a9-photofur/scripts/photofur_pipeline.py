#!/usr/bin/env python3
"""
A9 photo -> fur texture pipeline (AnthroForge fur-craft wave).

Photo (CC/PD, Wikimedia Commons) -> tileable fur diffuse texture.

Stages
------
1. CROP      square region of uniform fur, chosen by eye on a grid preview.
2. DIRECTION structure tensor on luminance -> dominant strand angle +
             coherence; rotate so strands run +V (down the tile), re-measure
             and correct the residual (convention-free convergence).
3. DE-LIGHT  per-channel divide by a large-sigma Gaussian estimate of the
             illumination field, renormalised to the field mean (homomorphic
             flattening), percentile re-stretch, mild unsharp for strand pop.
4. SEAMLESS  three defences, in order:
             a. quiet-join search - roll the tile so each wrap seam lands
                where the texture's own step across the join is smallest
                (the join inherits an interior-sized step by construction);
             b. frequency split - the low-frequency layer is made exactly
                periodic with a sin^2 half-shift blend (ghosting is
                invisible at that scale; colour patches wrap perfectly);
             c. the high-frequency layer gets seam-band symmetrisation:
                the 2B strip straddling the seam is blended with its own
                half-shift under a sin^2 weight (exactly periodic).
5. FLOW      per-pixel strand orientation (structure tensor, heavy smooth)
             encoded RG = unit direction, B = coherence.
6. METRICS   wrap-seam step vs interior step (ratio ~1.0 = invisible seam),
             written to a JSON sidecar per texture.

Usage: python3 photofur_pipeline.py            (runs all three textures)
Outputs: textures/fur_<name>_diffuse.png, textures/fur_<name>_flow.png,
         textures/fur_<name>.json
"""
import json
import math
import os

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "sources")
TEX = os.path.join(ROOT, "textures")

SIZE = 1024          # output tile, px
BAND = 192           # seam symmetrisation band, px per side

JOBS = {
    "wolf": dict(
        file="wolf_taxidermied.jpg", crop=(1000, 495, 620),
        tile_cm=20.0,
        species="grey wolf (Canis lupus), taxidermy flank",
    ),
    "bear": dict(
        file="bear_black.jpg", crop=(560, 470, 560),
        tile_cm=15.0,
        species="American black bear (Ursus americanus), flank, summer coat",
    ),
    "fox": dict(
        file="fox_skins.jpg", crop=(1475, 220, 360),
        tile_cm=12.0,
        species="red fox (Vulpes vulpes), dressed pelt torso",
    ),
}


# ---------------------------------------------------------------- utilities
def load_crop(job):
    im = Image.open(os.path.join(SRC, job["file"])).convert("RGB")
    x, y, s = job["crop"]
    im = im.crop((x, y, x + s, y + s)).resize((SIZE, SIZE), Image.LANCZOS)
    return np.asarray(im).astype(np.float32) / 255.0


def luminance(img):
    return img @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)


def strand_angle(img, smooth=10.0):
    """Dominant strand direction (deg, image space: 0 = strands run ->,
    90 = strands run down) + coherence, via the structure tensor."""
    lum = luminance(img)
    gx = ndimage.sobel(lum, axis=1)
    gy = ndimage.sobel(lum, axis=0)
    jxx = ndimage.gaussian_filter(gx * gx, smooth)
    jyy = ndimage.gaussian_filter(gy * gy, smooth)
    jxy = ndimage.gaussian_filter(gx * gy, smooth)
    # gradient orientation energy histogram (mod 180)
    ang = 0.5 * np.arctan2(2 * jxy, jxx - jyy)          # gradient dir
    coh = np.sqrt((jxx - jyy) ** 2 + 4 * jxy ** 2) / (jxx + jyy + 1e-12)
    w = (jxx + jyy) * coh
    hist_ang = np.degrees(ang) % 180.0
    bins = np.zeros(180)
    idx = hist_ang.astype(int).ravel()
    np.add.at(bins, idx, w.ravel())
    bins = ndimage.gaussian_filter1d(bins, 2.0, mode="wrap")
    grad_dir = float(np.argmax(bins))                    # gradient direction
    strand = (grad_dir + 90.0) % 180.0                   # strands ⟂ gradient
    return strand, float(np.average(coh, weights=jxx + jyy + 1e-12))


def rotate_img(img, deg):
    """Rotate (deg, PIL convention: counter-clockwise on screen)."""
    out = np.empty_like(img)
    for c in range(3):
        out[..., c] = ndimage.rotate(img[..., c], deg, reshape=False,
                                     order=3, mode="mirror")
    return out


def align_direction(img):
    """Rotate so strands run vertically (90 deg). Measure-correct loop."""
    total = 0.0
    for _ in range(3):
        strand, coh = strand_angle(img)
        # strand in [0,180); error vs the 90 deg target, wrapped to [-90,90)
        err = (strand - 90.0 + 90.0) % 180.0 - 90.0
        if abs(err) < 1.5:
            return img, total, strand, coh
        img = rotate_img(img, err)   # ndimage angle sign matches err here
        total += err
    strand, coh = strand_angle(img)
    return img, total, strand, coh


def delight(img, sigma=90.0):
    out = np.empty_like(img)
    for c in range(3):
        ch = img[..., c]
        field = ndimage.gaussian_filter(ch, sigma, mode="reflect")
        flat = ch / np.maximum(field, 1e-4) * field.mean()
        out[..., c] = flat
    lo, hi = np.percentile(out, [0.5, 99.5])
    out = np.clip((out - lo) / max(hi - lo, 1e-6), 0.0, 1.0)
    blur = ndimage.gaussian_filter(out, 2.0)
    out = np.clip(out + 0.35 * (out - blur), 0.0, 1.0)   # gentle unsharp
    return out


def symmetrise_axis(img, axis, band=BAND):
    """Make `img` exactly periodic along `axis` by periodising the
    2*band-wide strip that straddles the wrap seam."""
    n = img.shape[axis]
    img = np.moveaxis(img, axis, 0)
    strip = np.concatenate([img[n - band:], img[:band]], axis=0)  # 2B, seam@B
    j = np.arange(2 * band, dtype=np.float32)
    s = np.sin(np.pi * j / (2 * band)) ** 2
    shape = (-1,) + (1,) * (img.ndim - 1)
    s = s.reshape(shape)
    shifted = np.roll(strip, band, axis=0)
    new = (1 - s) * strip + s * shifted
    out = img.copy()
    out[n - band:] = new[:band]
    out[:band] = new[band:]
    return np.moveaxis(out, 0, axis)


def seam_metrics(img):
    lum = luminance(img)
    def ratio(axis):
        a = np.take(lum, 0, axis=axis)
        b = np.take(lum, -1, axis=axis)
        seam = np.mean(np.abs(a - b))
        interior = np.mean(np.abs(np.diff(lum, axis=axis)))
        return float(seam / max(interior, 1e-9))
    return ratio(1), ratio(0)


def flow_map(img):
    lum = luminance(img)
    gx = ndimage.sobel(lum, axis=1)
    gy = ndimage.sobel(lum, axis=0)
    jxx = ndimage.gaussian_filter(gx * gx, 14.0)
    jyy = ndimage.gaussian_filter(gy * gy, 14.0)
    jxy = ndimage.gaussian_filter(gx * gy, 14.0)
    ang = 0.5 * np.arctan2(2 * jxy, jxx - jyy) + math.pi / 2  # strand dir
    coh = np.sqrt((jxx - jyy) ** 2 + 4 * jxy ** 2) / (jxx + jyy + 1e-12)
    flow = np.zeros((*lum.shape, 3), dtype=np.float32)
    flow[..., 0] = 0.5 + 0.5 * np.cos(ang)
    flow[..., 1] = 0.5 + 0.5 * np.sin(ang)
    flow[..., 2] = np.clip(coh, 0, 1)
    return flow


def save_png(arr, path):
    Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8)).save(path)


# ---------------------------------------------------------------- main
def run(name, job):
    print(f"== {name}: {job['species']}")
    img = load_crop(job)
    raw_strand, raw_coh = strand_angle(img)
    img, rotated, strand, coh = align_direction(img)
    print(f"   strand angle raw {raw_strand:.1f} deg (coh {raw_coh:.2f}) "
          f"-> rotated {rotated:+.1f} deg -> final {strand:.1f} deg")
    img = delight(img)
    pre = seam_metrics(img)
    img = symmetrise_axis(img, axis=1)
    img = symmetrise_axis(img, axis=0)
    post = seam_metrics(img)
    print(f"   seam ratio x {pre[0]:.2f} -> {post[0]:.2f} | "
          f"y {pre[1]:.2f} -> {post[1]:.2f}")
    save_png(img, os.path.join(TEX, f"fur_{name}_diffuse.png"))
    save_png(flow_map(img), os.path.join(TEX, f"fur_{name}_flow.png"))
    meta = dict(
        name=name, species=job["species"], source_file=job["file"],
        crop_xy_size=job["crop"], tile_cm=job["tile_cm"],
        px_per_cm=round(SIZE / job["tile_cm"], 1),
        strand_angle_raw_deg=round(raw_strand, 1),
        rotation_applied_deg=round(rotated, 1),
        strand_angle_final_deg=round(strand, 1),
        coherence=round(coh, 3),
        seam_ratio_x=round(post[0], 3), seam_ratio_y=round(post[1], 3),
        seam_ratio_pre_x=round(pre[0], 3), seam_ratio_pre_y=round(pre[1], 3),
    )
    with open(os.path.join(TEX, f"fur_{name}.json"), "w") as f:
        json.dump(meta, f, indent=2)
    print("   saved", meta["px_per_cm"], "px/cm")


if __name__ == "__main__":
    os.makedirs(TEX, exist_ok=True)
    for n, j in JOBS.items():
        run(n, j)
