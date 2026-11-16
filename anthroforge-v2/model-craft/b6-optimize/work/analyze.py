#!/usr/bin/env python3
"""B6 offline analysis of pose_check dumps (pure numpy/scipy).

Per LOD: flipped-face counts (B17's 2D deformation-gradient metric,
det < 0), edge-strain stats, region vertex survival, silhouette IoU
vs LOD0 (front projection, 4 mm cells, 1-cell dilation), and
nearest-vertex deviation vs LOD0 in rest + elbow poses.

  python3 analyze.py <dumps_dir> <out_dir>
LOD0 file must be named bara_wolf_lod0_dumps.npz.
"""
import sys, os, json
import numpy as np
from scipy.spatial import cKDTree
from scipy import ndimage

DUMPS, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)

REGIONS = {
    "elbow": (["mixamorig:LeftArm", "mixamorig:LeftForeArm"], "elbow"),
    "twist": (["mixamorig:LeftForeArm", "mixamorig:LeftHand"], "twist"),
}

def load(tag):
    d = np.load(os.path.join(DUMPS, tag + "_dumps.npz"), allow_pickle=True)
    return {k: d[k] for k in d.files}

def face_metrics(rest, pos, faces, dom, region_idx):
    p0, p1, p2 = rest[faces[:, 0]], rest[faces[:, 1]], rest[faces[:, 2]]
    q0, q1, q2 = pos[faces[:, 0]], pos[faces[:, 1]], pos[faces[:, 2]]
    e1 = p1 - p0
    e1n = e1 / np.maximum(np.linalg.norm(e1, axis=1, keepdims=True), 1e-12)
    n = np.cross(e1, p2 - p0)
    n = n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    e2 = np.cross(n, e1n)
    detF = (((q1 - q0) * e1n).sum(1) * ((q2 - q0) * e2).sum(1)
            - ((q1 - q0) * e2).sum(1) * ((q2 - q0) * e1n).sum(1)) / \
        np.maximum(np.linalg.norm(e1, axis=1) * ((p2 - p0) * e2).sum(1),
                   1e-12)
    fmask = np.isin(dom[faces], list(region_idx)).any(axis=1)
    return dict(flips=int((detF < 0).sum()),
                flips_pct=round(100 * float((detF < 0).mean()), 2),
                region_flips=int((detF[fmask] < 0).sum()),
                region_tris=int(fmask.sum()))

def strain_metrics(rest, pos, edges, dom, region_idx):
    rl = np.linalg.norm(rest[edges[:, 0]] - rest[edges[:, 1]], axis=1)
    pl = np.linalg.norm(pos[edges[:, 0]] - pos[edges[:, 1]], axis=1)
    st = pl / np.maximum(rl, 1e-9)
    emask = np.isin(dom[edges], list(region_idx)).any(axis=1)
    rs = st[emask]
    return dict(strain_max=round(float(st.max()), 3),
                region_strain_p99=round(float(np.percentile(rs, 99)), 3),
                region_strain_max=round(float(rs.max()), 3))

def silhouette(verts, extent=(-1.1, 1.1, 0.0, 2.3), cell=0.004,
               fill=False):
    x0, x1, z0, z1 = extent
    H = int((z1 - z0) / cell); Wd = int((x1 - x0) / cell)
    ix = ((verts[:, 0] - x0) / cell).astype(int)
    iz = ((verts[:, 2] - z0) / cell).astype(int)
    ok = (ix >= 0) & (ix < Wd) & (iz >= 0) & (iz < H)
    m = np.zeros((H, Wd), dtype=bool)
    m[iz[ok], ix[ok]] = True
    m = ndimage.binary_dilation(m, iterations=1)
    if fill:
        # filled mask: outline fidelity only (interior point sparsity
        # from non-uniform decimation must not count as outline error)
        m = ndimage.binary_fill_holes(m)
    return m

def iou(a, b):
    return float((a & b).sum() / max((a | b).sum(), 1))

tags = ["bara_wolf_lod0", "bara_wolf_lod1_naive", "bara_wolf_lod1",
        "bara_wolf_lod2_naive", "bara_wolf_lod2"]
data = {t: load(t) for t in tags}
bones0 = [str(b) for b in data["bara_wolf_lod0"]["bones"]]
bidx = {n: i for i, n in enumerate(bones0)}
res = {}
sil0 = {pose: silhouette(data["bara_wolf_lod0"][pose])
        for pose in ("rest", "elbow")}
sil0f = {pose: silhouette(data["bara_wolf_lod0"][pose], fill=True)
         for pose in ("rest", "elbow")}
tree0 = {pose: cKDTree(data["bara_wolf_lod0"][pose])
         for pose in ("rest", "elbow")}
rng = np.random.default_rng(6)
for tag in tags:
    d = data[tag]
    bones = [str(b) for b in d["bones"]]
    entry = dict(verts=int(len(d["rest"])), faces=int(len(d["faces"])))
    for pose, (rbones, _) in REGIONS.items():
        ridx = [bones.index(b) for b in rbones if b in bones]
        fm = face_metrics(d["rest"], d[pose], d["faces"], d["dom"], ridx)
        sm = strain_metrics(d["rest"], d[pose], d["edges"], d["dom"], ridx)
        entry[pose] = {**fm, **sm}
        entry[pose]["region_verts"] = int(
            np.isin(d["dom"], ridx).sum())
    for pose in ("rest", "elbow"):
        m = silhouette(d[pose])
        entry[f"silhouette_iou_{pose}"] = round(iou(m, sil0[pose]), 4)
        mf = silhouette(d[pose], fill=True)
        entry[f"silhouette_iou_{pose}_filled"] = round(
            iou(mf, sil0f[pose]), 4)
        src = d[pose]
        if len(src) > 8000:
            src = src[rng.choice(len(src), 8000, replace=False)]
        dist, _ = tree0[pose].query(src)
        entry[f"dev_{pose}"] = dict(
            mean_mm=round(1000 * float(dist.mean()), 2),
            p95_mm=round(1000 * float(np.percentile(dist, 95)), 2),
            max_mm=round(1000 * float(dist.max()), 2))
    res[tag] = entry
    print(tag, json.dumps(entry))
json.dump(res, open(os.path.join(OUT, "measurements.json"), "w"), indent=1)

# ---- silhouette comparison figure ----------------------------------------
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
fig, axes = plt.subplots(2, 5, figsize=(15, 7))
for r, pose in enumerate(("rest", "elbow")):
    for c, tag in enumerate(tags):
        ax = axes[r][c]
        v = data[tag][pose]
        ax.scatter(v[:, 0], v[:, 2], s=0.15, c="#333333")
        ax.set_xlim(-1.1, 1.1); ax.set_ylim(0, 2.3)
        ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
        ax.set_title(f"{tag.replace('bara_wolf_', '')} {pose}\n"
                     f"IoU {res[tag][f'silhouette_iou_{pose}']:.3f}",
                     fontsize=8)
plt.tight_layout()
plt.savefig(os.path.join(OUT, "..", "renders", "silhouette_compare.png"),
            dpi=110)
print("ANALYZE DONE")
