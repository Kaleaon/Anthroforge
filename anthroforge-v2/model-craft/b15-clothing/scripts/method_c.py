"""Diagnose B's fat-extreme poke-through by region, then Method C:
A (delta transfer, static neutral offset) + iterative push-out along deformed
body normals wherever signed clearance < target, with graph smoothing between
rounds (collision-resolve pass, Outfit-Studio style)."""
import json
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
import scipy.sparse as sp

OUT = Path.home() / "workspace/anthroforge-v2/model-craft/b15-clothing"
d = np.load(OUT/"scripts/garment_data.npz")
base, faces = d["base"], d["faces"]
g_idx, g_faces = d["g_idx"], d["g_faces"]
BODY_END = 13380
body_mask = np.zeros(len(base), bool); body_mask[:BODY_END] = True
tris = faces[np.all(faces < BODY_END, axis=1)]
corr = np.load(Path.home()/"workspace/anthroforge-v2/first-proof/work/correspondence.npz")
crotch, neck = [float(x) for x in corr["mh_landmarks"]]

def vert_normals(pos, tris_):
    n = np.cross(pos[tris_[:,1]]-pos[tris_[:,0]], pos[tris_[:,2]]-pos[tris_[:,0]])
    vn = np.zeros_like(pos)
    for c in range(3):
        np.add.at(vn, tris_[:, c], n)
    return vn / np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-12)

src = np.zeros(len(base), bool); src[g_idx] = True
sample_faces = tris[np.all(src[tris], axis=1)]

def body_through(gpos, deformed):
    samples = np.concatenate([deformed[src], deformed[sample_faces].mean(axis=1)])
    gn = vert_normals(gpos, g_faces)
    tree = cKDTree(gpos)
    _, nn = tree.query(samples)
    signed = np.einsum("ij,ij->i", samples - gpos[nn], gn[nn])
    return signed, samples

def garment_in(gpos, deformed, bn):
    tree = cKDTree(deformed[body_mask])
    _, nn = tree.query(gpos)
    near = np.where(body_mask)[0][nn]
    return np.einsum("ij,ij->i", gpos - deformed[near], bn[near])

# garment graph Laplacian (local indices)
edges = np.vstack([g_faces[:, [0,1]], g_faces[:, [1,2]], g_faces[:, [2,0]]])
edges = np.unique(np.sort(edges, axis=1), axis=0)
A = sp.coo_matrix((np.ones(len(edges)), (edges[:,0], edges[:,1])), shape=(len(g_idx), len(g_idx)))
A = A + A.T
deg = np.asarray(A.sum(axis=1)).ravel()
Lop = sp.diags(1.0/np.maximum(deg,1)) @ A

def method_c(state, target=0.006, rounds=4):
    delta = d[f"delta_{state}"]
    deformed = base + delta
    bn = vert_normals(deformed, tris)
    gpos = d[f"{state}_A"].copy()
    for it in range(rounds):
        signed = garment_in(gpos, deformed, bn)
        deficit = np.clip(target - signed, 0, None)
        if (deficit > 0).sum() == 0:
            break
        # push along the SOURCE body vertex's deformed normal (garment vert i == source g_idx[i])
        gpos = gpos + bn[g_idx] * deficit[:, None]
        gpos = 0.5*gpos + 0.5*(Lop @ gpos)  # relax to avoid spikes
    return gpos

report = {}
for state in ["neutral", "strongman", "fat_v51", "gachidebu"]:
    delta = d[f"delta_{state}"]
    deformed = base + delta
    bn = vert_normals(deformed, tris)
    entry = {}
    # diagnose B poke location on fat state
    for method in ["A", "B"]:
        signed, samples = body_through(d[f"{state}_{method}"], deformed)
        out = signed > 0
        hh = (samples[:, 2] - crotch) / (neck - crotch)
        entry[method] = {"pokethrough_pct": round(float(out.mean()*100), 2),
                         "max_poke_mm": round(float(signed.max()*1000), 2),
                         "worst_h": round(float(hh[np.argmax(signed)]), 2) if out.any() else None}
    gC = method_c(state)
    signedC, _ = body_through(gC, deformed)
    ginC = garment_in(gC, deformed, bn)
    entry["C"] = {"pokethrough_pct": round(float((signedC > 0).mean()*100), 2),
                  "max_poke_mm": round(float(signedC.max()*1000), 2),
                  "garment_in_penetrating_pct": round(float((ginC < 0).mean()*100), 2),
                  "mean_clearance_mm": round(float(ginC.mean()*1000), 2),
                  "min_clearance_mm": round(float(ginC.min()*1000), 2)}
    np.save(OUT/f"scripts/garmentC_{state}.npy", gC)
    report[state] = entry
    print(state, json.dumps(entry))

prev = json.loads((OUT/"metrics.json").read_text())
prev["method_c_and_diagnosis"] = report
(OUT/"metrics.json").write_text(json.dumps(prev, indent=1))
print("done")
