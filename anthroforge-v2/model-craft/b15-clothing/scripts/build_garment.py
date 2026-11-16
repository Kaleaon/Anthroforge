"""B15 clothing-fit prototype: tank top derived from the hm08 torso patch,
deformed by delta transfer across slider extremes; poke-through measured for
(A) static-offset delta transfer (BodySlide-style conform) and
(B) delta transfer + per-state normal-offset maintenance (shrinkwrap-equivalent).
"""
import json, zipfile
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree

WS = Path.home() / "workspace"
FP = WS / "anthroforge-v2/first-proof"
BP = WS / "anthroforge-v2/bara-proof"
OUT = WS / "anthroforge-v2/model-craft/b15-clothing"
MPFB_ZIP = WS / "stick-figure-avatar/photoreal/tools/mpfb2.zip"
DM_M = 0.1
BODY_END = 13380
CLEAR = 0.008  # 8 mm garment clearance

# ---------- load base (canonical frame: x right, y front, z up, metres)
with zipfile.ZipFile(MPFB_ZIP) as z:
    lines = z.read("mpfb/data/3dobjs/base.obj").decode().splitlines()
obj = np.array([[float(x) for x in l.split()[1:4]] for l in lines if l.startswith("v ")])
faces = []
for l in lines:
    if l.startswith("f "):
        faces.append([int(t.split("/")[0]) - 1 for t in l.split()[1:]])
faces = np.array(faces)
base = np.stack([obj[:, 0], obj[:, 2], obj[:, 1]], axis=1) * DM_M  # (x, z_up->y?) canonical per first-proof
# first-proof canonical: pos = (obj_x, obj_z, obj_y); z (index2) is up
body = np.zeros(len(base), bool); body[:BODY_END] = True
tris = faces[np.all(faces < BODY_END, axis=1)]  # body-only faces for normals/metrics

def load_target(path):
    d = np.zeros_like(base)
    for line in Path(path).read_text().splitlines():
        if not line or line.startswith("#"):
            continue
        p = line.split()
        i = int(p[0]); v = np.array([float(p[1]), float(p[2]), float(p[3])])
        d[i] = np.array([v[0], v[2], v[1]]) * DM_M  # obj-frame -> canonical
    return d

states = {
    "neutral":   np.zeros_like(base),
    "strongman": load_target(BP/"body.muscle.target") + load_target(BP/"body.chest.width.target") + load_target(BP/"body.tissue.strongman.target"),
    "fat_v51":   load_target(FP/"body.belly.protrusion_v5.1.target"),
    "gachidebu": load_target(BP/"body.coupling.gachidebu.target"),
}
# sanity: fat navel delta should be ~ +0.11 front (y), ~ -0.07 down (z)
corr = np.load(FP/"work/correspondence.npz")
navel = int(corr["navel_mh"])
print("fat_v51 navel delta (x,y_front,z_up):", np.round(states["fat_v51"][navel], 3))

# ---------- torso frame (axis, h, theta, r) as in first-proof
def compute_axis(pos, gate):
    hgt = pos[:, 2]; lo, hi = hgt[gate].min(), hgt[gate].max()
    edges = np.linspace(lo, hi, 81); ctr = 0.5*(edges[:-1]+edges[1:])
    axis = np.full((len(ctr), 2), np.nan)
    for i, (a, b) in enumerate(zip(edges[:-1], edges[1:])):
        m = gate & (hgt >= a) & (hgt < b) & (np.abs(pos[:, 0]) < 0.23)
        if m.sum() >= 4:
            axis[i] = [0.5*(pos[m,0].min()+pos[m,0].max()), 0.5*(pos[m,1].min()+pos[m,1].max())]
    ok = ~np.isnan(axis[:, 0])
    for c in range(2):
        axis[:, c] = np.interp(ctr, ctr[ok], axis[ok, c])
        axis[:, c] = np.convolve(np.pad(axis[:, c], 2, mode="edge"), np.ones(5)/5, "valid")
    return ctr, axis

ctr, axis = compute_axis(base, body)
ax = np.stack([np.interp(base[:,2], ctr, axis[:,0]), np.interp(base[:,2], ctr, axis[:,1])], axis=1)
rel = base[:, :2] - ax
r = np.linalg.norm(rel, axis=1)
theta = np.arctan2(rel[:, 0], rel[:, 1])  # 0 = front, +-pi/2 = sides, pi = back
zmin = base[body, 2].min()
# crotch / neck landmarks from correspondence (canonical z)
crotch, neck = [float(x) for x in corr["mh_landmarks"]]
h = (base[:, 2] - crotch) / (neck - crotch)
print(f"crotch {crotch:.3f} neck {neck:.3f} navel h {h[navel]:.3f}")

# ---------- vertex normals
def vert_normals(pos, tris_):
    n = np.cross(pos[tris_[:,1]]-pos[tris_[:,0]], pos[tris_[:,2]]-pos[tris_[:,0]])
    vn = np.zeros_like(pos)
    for c in range(3):
        np.add.at(vn, tris_[:, c], n)
    vn /= np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-12)
    return vn

# ---------- tank-top patch selection
torso = body & (r < 0.215)
sel = torso & (h > -0.06) & (h < 0.985)
sel &= ~((h > 0.90) & (np.abs(theta) < 0.75))                    # front neck scoop
sel &= ~((h > 0.955) & (np.abs(theta) > 2.2))                    # back neckline
sel &= ~((h > 0.70) & (np.abs(np.abs(theta) - np.pi/2) < 0.45))  # armholes (lateral band)
g_idx = np.where(sel)[0]
g_faces = faces[np.all(np.isin(faces, g_idx), axis=1)]
remap = -np.ones(len(base), dtype=int); remap[g_idx] = np.arange(len(g_idx))
g_faces_r = remap[g_faces]
print(f"garment: {len(g_idx)} verts, {len(g_faces_r)} faces")

n0 = vert_normals(base, tris)
g_base = base[g_idx] + n0[g_idx] * CLEAR

def measure(garment_pos, state_delta):
    """Signed clearance of garment verts vs deformed body (nearest-vertex approx)."""
    deformed = base + state_delta
    nd = vert_normals(deformed, tris)
    tree = cKDTree(deformed[body])
    dist, nn = tree.query(garment_pos)
    nearest = np.where(body)[0][nn]
    signed = np.einsum("ij,ij->i", garment_pos - deformed[nearest], nd[nearest])
    pen = signed < 0
    return {
        "verts": int(len(garment_pos)),
        "penetrating_pct": round(float(pen.mean()*100), 2),
        "max_penetration_mm": round(float(-signed.min()*1000), 2) if pen.any() else 0.0,
        "mean_clearance_mm": round(float(signed.mean()*1000), 2),
        "min_clearance_mm": round(float(signed.min()*1000), 2),
        "p5_clearance_mm": round(float(np.percentile(signed, 5)*1000), 2),
    }

results = {}
export = {"g_idx": g_idx, "g_faces": g_faces_r, "g_base": g_base, "states": {}}
for name, delta in states.items():
    deformed = base + delta
    nd = vert_normals(deformed, tris)
    gA = g_base + delta[g_idx]                       # static offset baked at neutral
    gB = deformed[g_idx] + nd[g_idx] * CLEAR         # offset re-maintained per state
    results[name] = {"A_static_offset": measure(gA, delta), "B_offset_maintained": measure(gB, delta)}
    export["states"][name] = {"A": gA, "B": gB}
    print(name, json.dumps(results[name]))

np.savez(OUT/"scripts/garment_data.npz",
         base=base, faces=faces, g_idx=g_idx, g_faces=g_faces_r, g_base=g_base,
         **{f"{k}_{m}": export["states"][k][m] for k in export["states"] for m in ("A","B")},
         **{f"delta_{k}": v for k, v in states.items()})
(OUT/"metrics.json").write_text(json.dumps(results, indent=1))
print("saved garment_data.npz + metrics.json")
