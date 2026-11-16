"""Measure A2 patch renders (system python3): front coverage and grazing
silhouette behaviour from colour-classified masks.
Backdrop = magenta (camera-only), dome/undercoat = blue, fur = the rest.
"""
import json, os
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REND = os.path.join(os.path.dirname(HERE), "renders")
FAMS = ["ribbon_flat", "ribbon_bent", "ribbon_fork", "cross_pair",
        "tri_fan", "quad_shingle"]


def masks(path):
    im = np.asarray(Image.open(path).convert("RGB")).astype(float) / 255.0
    R, G, B = im[:, :, 0], im[:, :, 1], im[:, :, 2]
    magenta = (R > 0.6) & (G < 0.35) & (B > 0.6)
    blue = (B > 0.4) & (B > R + 0.2) & (B > G + 0.2)
    fur = ~magenta & ~blue
    return fur, blue


def profile_stats(fur, blue):
    H, W = fur.shape
    cols = np.where((fur | blue).any(axis=0))[0]
    lifts, tops = [], []
    for c in cols:
        frows = np.where(fur[:, c])[0]
        if len(frows) == 0:
            continue
        ft = frows.min()
        tops.append(ft)
        brows = np.where(blue[:, c])[0]
        if len(brows):
            lifts.append(brows.min() - ft)
    tops = np.array(tops, dtype=float)
    rough = float(np.mean(np.abs(np.diff(tops)))) if len(tops) > 2 else 0.0
    return dict(mean_lift_px=round(float(np.mean(lifts)), 1) if lifts else 0.0,
                max_lift_px=int(np.max(lifts)) if lifts else 0,
                continuity=round(len(lifts) / max(len(cols), 1), 3),
                silhouette_roughness_px=round(rough, 2))


out = {}
for fam in FAMS:
    fur_f, blue_f = masks(os.path.join(REND, f"patch_{fam}_front.png"))
    region = fur_f | blue_f
    cov = float(fur_f.sum() / max(region.sum(), 1))
    fur_g, blue_g = masks(os.path.join(REND, f"patch_{fam}_grazing.png"))
    g = profile_stats(fur_g, blue_g)
    out[fam] = dict(front_coverage=round(cov, 3), **g)
    print(fam, out[fam])

json.dump(out, open(os.path.join(HERE, "render_stats.json"), "w"), indent=1)
print("WROTE render_stats.json")
