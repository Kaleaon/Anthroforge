# B8 analysis: in-island map stats (diffuse alpha = true coverage mask) +
# render comparison (silhouette IoU + foreground MAE) + side-by-side composite.
import json
import numpy as np
from PIL import Image

B8 = "/home/hatch/workspace/anthroforge-v2/model-craft/b8-baking"
out = {}

# ---------- map stats, masked to real UV coverage ----------
col = np.asarray(Image.open(f"{B8}/maps/orc_head_color.png")).astype(np.float32) / 255.0
mask = col[..., 3] > 0.0                     # diffuse bake keeps honest alpha
out["uv_coverage_fraction"] = round(float(mask.mean()), 4)

def masked_stats(name, rescale_mask=None):
    im = np.asarray(Image.open(f"{B8}/maps/orc_head_{name}.png")).astype(np.float32) / 255.0
    m = mask
    if rescale_mask is not None:
        m = np.asarray(Image.fromarray((mask * 255).astype(np.uint8)).resize(
            (im.shape[1], im.shape[0]), Image.NEAREST)) > 0
    px = im[m][:, :3]
    return {"mean": [round(float(v), 4) for v in px.mean(axis=0)],
            "std": [round(float(v), 4) for v in px.std(axis=0)],
            "min": [round(float(v), 4) for v in px.min(axis=0)],
            "max": [round(float(v), 4) for v in px.max(axis=0)]}

out["normal_in_island"] = masked_stats("normal")
out["color_in_island"] = masked_stats("color")
out["curvature_in_island"] = masked_stats("curvature")
out["ao_in_island"] = masked_stats("ao", rescale_mask=True)

# normal-map validity: fraction of island texels whose vector length is ~1
nrm = np.asarray(Image.open(f"{B8}/maps/orc_head_normal.png")).astype(np.float32) / 255.0
vec = nrm[mask][:, :3] * 2.0 - 1.0
lengths = np.linalg.norm(vec, axis=1)
out["normal_vector_length"] = {
    "mean": round(float(lengths.mean()), 4),
    "frac_within_0.9_1.1": round(float(((lengths > 0.9) & (lengths < 1.1)).mean()), 4)}

# ---------- render comparison ----------
hi = Image.open(f"{B8}/renders/render_high.png").convert("RGB")
lo = Image.open(f"{B8}/renders/render_low_baked.png").convert("RGB")
a = np.asarray(hi).astype(np.float32) / 255.0
b = np.asarray(lo).astype(np.float32) / 255.0
bg = a[0, 0]                                  # flat world colour, top-left corner
def fg(x):
    return np.abs(x - bg).max(axis=-1) > 0.03
fa, fb = fg(a), fg(b)
union = fa | fb
inter = fa & fb
out["render"] = {
    "silhouette_iou": round(float(inter.sum() / union.sum()), 4),
    "foreground_mae_0_1": round(float(np.abs(a - b)[union].mean()), 4),
    "foreground_mae_255": round(float(np.abs(a - b)[union].mean() * 255), 2),
    "foreground_frac_of_frame": round(float(union.mean()), 4)}

comp = Image.new("RGB", (hi.width + lo.width + 8, hi.height), (255, 255, 255))
comp.paste(hi, (0, 0))
comp.paste(lo, (hi.width + 8, 0))
comp.save(f"{B8}/renders/comparison.png")
out["comparison_file"] = "renders/comparison.png"

with open(f"{B8}/work/analysis.json", "w") as f:
    json.dump(out, f, indent=2)
print(json.dumps(out, indent=2))
