#!/usr/bin/env python3
"""Card texture bake v3 (A8) — strand-cluster card textures, 512x512 RGBA + normal.

Method (the production recipe, see CARD_TEXTURES.md):
  * Strands are SIMULATED, not photographed: each strand is a tapered
    polyline grown root->tip with per-variant behaviour (sway, clump
    convergence, plume sweep). Colour is a root->tip ramp with per-strand
    hue/value jitter, agouti banding on a subset, pale guard hairs mixed in.
  * Rasterised at 2x supersample with PIL stroke drawing (C speed), strands
    drawn 3x in U (x, x+-W) so the texture tiles horizontally.
  * Alpha = stroke coverage with a contrast curve (opaque core, feathered
    edge); root 3% fades in; a root AO band darkens colour near the base.
  * RGB edge bleed: colour is iteratively diffused into transparent texels
    so mip levels don't fringe dark/transparent.
  * Normal map: height field = blurred coverage; tangent-space normal from
    its gradient (strength tuned per variant). Statistical across-strand
    shading -- the standard cheap card normal.
Deterministic: per-variant seeds.
"""
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT = Path(__file__).resolve().parent.parent
SS = 2                      # supersample
W = 512 * SS                # working size
FINAL = 512

# wolf-brown palette (linear-ish sRGB values as authored)
ROOT = np.array([26, 18, 13])      # near-black brown at root
MID = np.array([96, 68, 44])       # warm mid brown
TIP = np.array([178, 148, 112])    # pale tan tip
GUARD = np.array([196, 182, 160])  # pale guard-hair strand colour


def lerp(a, b, t):
    return a + (b - a) * t


def strand_colour(t, jit, guard, agouti, rng):
    """Colour at normalised length t for one strand."""
    if guard:
        c = lerp(ROOT * 1.4, GUARD, smooth(t))
    else:
        c = lerp(lerp(ROOT, MID, smooth(min(t * 1.6, 1.0))),
                 TIP, smooth(max(0.0, (t - 0.45) / 0.55)))
        if agouti:  # 2 dark bands over the pale ground (agouti ticking)
            band = (np.sin(t * math.pi * 3.2 + jit * 9.0) > 0.35)
            c = np.where(band, c * 0.58, c)
    c = c * (0.82 + 0.36 * jit)
    return tuple(int(max(0, min(255, v))) for v in c)


def smooth(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


VARIANTS = {
    # name: dict of behaviour params
    "straight": dict(n=950, width=(2.6, 0.7), sway=0.012, clumps=0,
                     lean=0.05, len_jit=0.16, guard_p=0.06, agouti_p=0.30,
                     envelope=0.42, nrm=1.6),
    "wavy": dict(n=880, width=(2.8, 0.7), sway=0.075, clumps=0,
                 lean=0.04, len_jit=0.18, guard_p=0.06, agouti_p=0.30,
                 envelope=0.46, nrm=1.7),
    "clumped": dict(n=1050, width=(2.7, 0.7), sway=0.03, clumps=15,
                    lean=0.05, len_jit=0.20, guard_p=0.08, agouti_p=0.35,
                    envelope=0.40, nrm=2.0),
    "tail_plume": dict(n=760, width=(3.0, 0.8), sway=0.05, clumps=5,
                       lean=0.30, len_jit=0.12, guard_p=0.10, agouti_p=0.20,
                       envelope=0.30, nrm=1.5),
    "guard_ruff": dict(n=520, width=(4.4, 1.0), sway=0.035, clumps=11,
                       lean=0.06, len_jit=0.24, guard_p=0.16, agouti_p=0.40,
                       envelope=0.36, nrm=2.2),
}


def gen_strands(name, p, rng):
    """Yield strand dicts: pts [(x,y)...] in working px (y down, root at
    bottom), per-point t, base width in px, jit, guard, agouti flags."""
    clump_tips = []
    if p["clumps"]:
        clump_tips = sorted(rng.uniform(0.06, 0.94) for _ in range(p["clumps"]))
    for _ in range(p["n"]):
        x0 = rng.uniform(0.0, 1.0)
        length = 1.0 - (rng.random() ** 1.5) * p["len_jit"] * 1.7 - 0.03
        phase = rng.uniform(0, math.tau)
        sway_f = rng.uniform(0.7, 1.3)
        lean = rng.normal(0, p["lean"] * 0.4) + (p["lean"] * 0.35
                                                 if name == "tail_plume" else 0)
        jit = rng.random()
        guard = rng.random() < p["guard_p"]
        agouti = (not guard) and rng.random() < p["agouti_p"]
        clump_tip = None
        if clump_tips:
            clump_tip = min(clump_tips, key=lambda c: abs(c - x0))
        steps = 18
        pts, ts = [], []
        for i in range(steps + 1):
            t = i / steps
            # envelope: lateral spread narrows toward the tip
            env = 1.0 - p["envelope"] * (t ** 1.4)
            x = x0 + lean * t + math.sin(phase + t * math.tau * sway_f) \
                * p["sway"] * t
            if clump_tip is not None:
                pull = smooth(max(0.0, (t - 0.25) / 0.75)) * 0.58
                x = lerp(x, clump_tip + (x0 - clump_tip) * 0.12, pull)
            pts.append((x * W, (1.0 - t * length) * W))
            ts.append(t)
        # apply envelope by compressing x toward card centre as t rises
        cx = pts[0][0]
        pts = [(cx + (x - cx) * (1.0 - p["envelope"] * (t ** 1.4)), y)
               for (x, y), t in zip(pts, ts)]
        w0 = rng.uniform(p["width"][0] * 0.75, p["width"][0] * 1.25) * SS
        yield dict(pts=pts, ts=ts, w0=w0, jit=float(jit), guard=guard,
                   agouti=agouti)


def bake(name, p, seed):
    rng = np.random.default_rng(seed)
    alpha = Image.new("L", (W, W), 0)
    colour = Image.new("RGB", (W, W), (0, 0, 0))
    da, dc = ImageDraw.Draw(alpha), ImageDraw.Draw(colour)
    strands = list(gen_strands(name, p, rng))
    # short strands first, long guard hairs last (they sit on top)
    strands.sort(key=lambda s: (s["guard"], max(s["ts"])))
    for s in strands:
        pts, ts = s["pts"], s["ts"]
        for i in range(len(pts) - 1):
            t = 0.5 * (ts[i] + ts[i + 1])
            wdt = max(1.0, s["w0"] * (1.0 - 0.82 * t))
            col = strand_colour(t, s["jit"], s["guard"], s["agouti"], rng)
            for dx in (-W, 0, W):  # U wrap copies
                seg = [(pts[i][0] + dx, pts[i][1]),
                       (pts[i + 1][0] + dx, pts[i + 1][1])]
                da.line(seg, fill=235, width=int(round(wdt)))
                dc.line(seg, fill=col, width=int(round(wdt)))
    alpha = alpha.filter(ImageFilter.GaussianBlur(0.7 * SS))
    colour = colour.filter(ImageFilter.GaussianBlur(0.5 * SS))
    a = np.asarray(alpha).astype(np.float32) / 255.0
    # Root fade: image y=0 is the TIP, y=W the ROOT (bottom edge). Soften
    # the root edge over the bottom 4% so cards don't end in a hard line.
    ry = np.linspace(0, 1, W)[:, None]          # 0 top -> 1 bottom(root)
    a *= 0.45 + 0.55 * np.clip((1.0 - ry) / 0.04, 0, 1)
    # Alpha contrast: opaque core, feathered silhouette edge.
    a = np.clip((a - 0.18) / 0.62, 0, 1) ** 0.8
    a_img = Image.fromarray((a * 255).astype(np.uint8)).resize(
        (FINAL, FINAL), Image.LANCZOS)
    c_img = colour.resize((FINAL, FINAL), Image.LANCZOS)
    # root AO: darken colour toward the root (bottom of image)
    c = np.asarray(c_img).astype(np.float32)
    ry = np.linspace(0, 1, FINAL)[:, None, None]  # 0 top(tip) -> 1 bottom(root)
    ao = 1.0 - 0.45 * np.clip((ry - 0.72) / 0.28, 0, 1) ** 1.5
    c *= ao
    c_img = Image.fromarray(np.clip(c, 0, 255).astype(np.uint8))
    # --- RGB edge bleed: diffuse colour into transparent texels (mip safety)
    a_fin = np.asarray(a_img).astype(np.float32) / 255.0
    rgb = np.asarray(c_img).astype(np.float32)
    for _ in range(14):
        blur = np.asarray(c_img.filter(
            ImageFilter.GaussianBlur(2.0))).astype(np.float32)
        m = a_fin < 0.03
        rgb[m] = blur[m]
        c_img = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8))
    out = c_img.convert("RGBA")
    out.putalpha(a_img)
    out.save(OUT / f"card_{name}_diffuse.png")
    # --- normal from height (blurred coverage), tangent space
    h = np.asarray(a_img).astype(np.float32) / 255.0
    hb = np.asarray(Image.fromarray((h * 255).astype(np.uint8)).filter(
        ImageFilter.GaussianBlur(1.6))).astype(np.float32) / 255.0
    gy, gx = np.gradient(hb)
    s = p["nrm"]
    n = np.stack([-gx * s, gy * s, np.ones_like(h)], axis=-1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    n_img = Image.fromarray(((n * 0.5 + 0.5) * 255).astype(np.uint8))
    n_img.save(OUT / f"card_{name}_normal.png")
    cov = float((a_fin > 0.5).mean())
    return dict(variant=name, strands=len(strands),
                alpha_coverage_gt_0_5=round(cov, 3),
                alpha_mean=round(float(a_fin.mean()), 3))


def main():
    stats = []
    for i, (name, p) in enumerate(VARIANTS.items()):
        st = bake(name, p, seed=1200 + i)
        stats.append(st)
        print(st)
    (OUT / "bake_stats.json").write_text(json.dumps(stats, indent=1))


if __name__ == "__main__":
    main()
