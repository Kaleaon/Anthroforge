"""Pixel stats for the A12 testbed renders (identical geometry, so mask
differences are pure shading). Regions: whole subject; silhouette band
(outer ~6 px of the subject mask); top undercoat control region (should
agree across setups -- the undercoat material never changes)."""
import numpy as np
from PIL import Image, ImageFilter
import json, sys

def lum(path):
    im = Image.open(path).convert("RGB")
    a = np.asarray(im, dtype=float)
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2], im

def stats(path):
    L, _ = lum(path)
    mask = L > 14
    mimg = Image.fromarray((mask * 255).astype(np.uint8))
    eroded = np.asarray(mimg.filter(ImageFilter.MinFilter(13))) > 0
    band = mask & ~eroded
    ctrl = np.zeros_like(mask); ctrl[60:150, 200:320] = True   # bare undercoat dome top
    band_crop = L[300:470, 150:360]
    gy, gx = np.gradient(band_crop)
    return {
        "subject_mean": round(float(L[mask].mean()), 2),
        "subject_p95": round(float(np.percentile(L[mask], 95)), 1),
        "silhouette_band_mean": round(float(L[band].mean()), 2),
        "silhouette_band_p95": round(float(np.percentile(L[band], 95)), 1),
        "control_top_mean": round(float(L[ctrl].mean()), 2),
        "cardband_grad_ratio_h_over_v": round(float(np.abs(gx).mean() / np.abs(gy).mean()), 3),
    }

out = {}
for name in sys.argv[1:]:
    out[name] = stats(f"/home/hatch/workspace/anthroforge-v2/fur-craft/a12-shading/renders/{name}.png")
print(json.dumps(out, indent=1))
