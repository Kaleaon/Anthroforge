"""Finisher add-on (B15): extend the clothing-fit study to the belly hyper
segment at slider 2.0, composed per the hyper record semantics
(hyper/body.belly.protrusion.hyper_record.json): delta = shipped v5.1 field
+ hyper segment delta (incremental over 1x). The v5.2/hyper contact
correctives are thigh-zone fields, outside this torso garment's patch, and
the original B15 fat_v51 state likewise used the belly field alone, so the
composition stays comparable. Cross-checks the composition against the
pre-summed body.belly.hyper2_full.target. Metrics use the same
point-to-triangle signed distance as measure_final.py / measure_masked.py."""
import json
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
import scipy.sparse as sp

WS = Path.home() / "workspace"
OUT = WS / "anthroforge-v2/model-craft/b15-clothing"
HYP = WS / "anthroforge-v2/hyper"
DM_M = 0.1
BODY_END = 13380

d = np.load(OUT / "scripts/garment_data.npz")
base, faces = d["base"], d["faces"]
g_idx, gq = d["g_idx"], d["g_faces"]
g_faces = np.vstack([gq[:, [0, 1, 2]], gq[:, [0, 2, 3]]])
body_mask = np.zeros(len(base), bool); body_mask[:BODY_END] = True
tris = faces[np.all(faces < BODY_END, axis=1)]
src = np.zeros(len(base), bool); src[g_idx] = True
sample_faces = tris[np.all(src[tris], axis=1)]
CLEAR = 0.008

def load_target(path):
    delta = np.zeros_like(base)
    for line in Path(path).read_text().splitlines():
        if not line or line.startswith("#"):
            continue
        p = line.split()
        i = int(p[0]); v = np.array([float(p[1]), float(p[2]), float(p[3])])
        delta[i] = np.array([v[0], v[2], v[1]]) * DM_M
    return delta

def vert_normals(pos, tris_):
    n = np.cross(pos[tris_[:, 1]] - pos[tris_[:, 0]], pos[tris_[:, 2]] - pos[tris_[:, 0]])
    vn = np.zeros_like(pos)
    for c in range(3):
        np.add.at(vn, tris_[:, c], n)
    return vn / np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-12)

# ---- compose the 2.0 state and cross-check against the pre-summed file
seg = load_target(HYP / "body.belly.protrusion.hyper2.target")
delta_h2 = d["delta_fat_v51"] + seg
full = load_target(HYP / "body.belly.hyper2_full.target")
diff = np.linalg.norm(delta_h2 - full, axis=1)
print(f"composition vs hyper2_full: max diff {diff.max()*1000:.2f} mm, "
      f"max diff on garment source verts {diff[g_idx].max()*1000:.2f} mm")

deformed = base + delta_h2
bn = vert_normals(deformed, tris)
g_base = d["g_base"]
gA = g_base + delta_h2[g_idx]                       # A: static offset, delta transfer
gB = deformed[g_idx] + bn[g_idx] * CLEAR            # B: offset re-maintained per state

# ---- Method C: A + iterative push-out with graph relax (as method_c.py)
edges = np.vstack([gq[:, [0, 1]], gq[:, [1, 2]], gq[:, [2, 0]]])
edges = np.unique(np.sort(edges, axis=1), axis=0)
A_ = sp.coo_matrix((np.ones(len(edges)), (edges[:, 0], edges[:, 1])), shape=(len(g_idx), len(g_idx)))
A_ = A_ + A_.T
deg = np.asarray(A_.sum(axis=1)).ravel()
Lop = sp.diags(1.0 / np.maximum(deg, 1)) @ A_

def garment_in_nn(gpos):
    tree = cKDTree(deformed[body_mask])
    _, nn = tree.query(gpos)
    near = np.where(body_mask)[0][nn]
    return np.einsum("ij,ij->i", gpos - deformed[near], bn[near])

gC = gA.copy()
for _ in range(4):
    signed = garment_in_nn(gC)
    deficit = np.clip(0.006 - signed, 0, None)
    if (deficit > 0).sum() == 0:
        break
    gC = gC + bn[g_idx] * deficit[:, None]
    gC = 0.5 * gC + 0.5 * (Lop @ gC)
np.save(OUT / "scripts/garmentC_hyper2.npy", gC)
print("method C hyper2 built")

# ---- point-to-triangle signed distance (machinery from measure_final.py)
code = (OUT / "scripts/measure_final.py").read_text()
fn = code[code.index("def cand_array"):code.index("results = {}")]
ns = {"np": np, "cKDTree": cKDTree, "PAD": 72}
exec(fn, ns)
signed_dist = ns["signed_dist"]

samples = np.concatenate([deformed[src], deformed[sample_faces].mean(axis=1)])
# openings exclusion mask (as measure_masked.py): drop samples within 20 mm of a boundary vert
e2 = np.vstack([g_faces[:, [0, 1]], g_faces[:, [1, 2]], g_faces[:, [2, 0]]])
es = np.sort(e2, axis=1)
uniq, counts = np.unique(es, axis=0, return_counts=True)
bnd_verts = np.unique(uniq[counts == 1])

entry = {"composition_check": {
    "vs_hyper2_full_max_diff_mm": round(float(diff.max() * 1000), 2),
    "vs_hyper2_full_max_diff_on_garment_verts_mm": round(float(diff[g_idx].max() * 1000), 2),
    "note": "hyper2_full additionally carries the re-solved 2.0 contact field (inner-thigh zone); the garment patch is torso-only, so the difference does not touch the garment source verts beyond the figure above."}}
for m, gpos in {"A": gA, "B": gB, "C": gC}.items():
    gin = signed_dist(gpos, deformed, tris)
    bout = signed_dist(samples, gpos, g_faces)
    btree = cKDTree(gpos[bnd_verts])
    dbnd, _ = btree.query(samples)
    bout_masked = signed_dist(samples[dbnd > 0.020], gpos, g_faces)
    entry[m] = {
        "garment_verts_penetrating_pct": round(float((gin < 0).mean() * 100), 2),
        "garment_max_penetration_mm": round(float(-gin.min() * 1000), 2) if (gin < 0).any() else 0.0,
        "garment_mean_clearance_mm": round(float(gin.mean() * 1000), 2),
        "body_samples_poking_pct": round(float((bout > 0).mean() * 100), 2),
        "body_max_poke_mm": round(float(bout.max() * 1000), 2) if (bout > 0).any() else 0.0,
        "body_poking_openings_excluded_pct": round(float((bout_masked > 0).mean() * 100), 2),
        "body_max_poke_openings_excluded_mm": round(float(bout_masked.max() * 1000), 2) if (bout_masked > 0).any() else 0.0,
        "body_mean_poke_openings_excluded_mm": round(float(bout_masked[bout_masked > 0].mean() * 1000), 2) if (bout_masked > 0).any() else 0.0,
    }
    print(m, json.dumps(entry[m]), flush=True)

prev = json.loads((OUT / "metrics.json").read_text())
prev["hyper2_extension"] = {"state": "belly slider 2.0 = v5.1 field + hyper segment delta (contact corrective excluded, as in the original fat_v51 state)", **entry}
(OUT / "metrics.json").write_text(json.dumps(prev, indent=1))
print("metrics.json updated with hyper2_extension")
