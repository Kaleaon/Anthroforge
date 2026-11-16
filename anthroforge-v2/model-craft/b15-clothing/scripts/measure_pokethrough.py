"""Pass 2: body-through-garment sampling. Sample the deformed BODY surface
(face centroids + verts of the covered torso region) and test each sample
against the garment mesh (nearest garment vertex, signed by garment normal).
Positive = body outside the garment = poke-through. Also garment-face
centroids tested against the body (garment dipping in)."""
import json
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree

OUT = Path.home() / "workspace/anthroforge-v2/model-craft/b15-clothing"
d = np.load(OUT/"scripts/garment_data.npz")
base, faces = d["base"], d["faces"]
g_idx, g_faces = d["g_idx"], d["g_faces"]
BODY_END = 13380
body_mask = np.zeros(len(base), bool); body_mask[:BODY_END] = True
tris = faces[np.all(faces < BODY_END, axis=1)]

def vert_normals(pos, tris_):
    n = np.cross(pos[tris_[:,1]]-pos[tris_[:,0]], pos[tris_[:,2]]-pos[tris_[:,0]])
    vn = np.zeros_like(pos)
    for c in range(3):
        np.add.at(vn, tris_[:, c], n)
    return vn / np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-12)

# body sample faces: body-mesh faces whose verts are all garment sources or neighbours
src = np.zeros(len(base), bool); src[g_idx] = True
sample_faces = tris[np.all(src[tris], axis=1)]
print("body sample faces:", len(sample_faces))

results = {}
for state in ["neutral", "strongman", "fat_v51", "gachidebu"]:
    delta = d[f"delta_{state}"]
    deformed = base + delta
    bn = vert_normals(deformed, tris)
    samples = np.concatenate([deformed[src],
                              deformed[sample_faces].mean(axis=1)])
    entry = {}
    for method in ["A", "B"]:
        gpos = d[f"{state}_{method}"]
        # garment normals in garment-local indexing
        gf = g_faces
        gn_full = vert_normals(gpos, gf)
        tree = cKDTree(gpos)
        dist, nn = tree.query(samples)
        signed = np.einsum("ij,ij->i", samples - gpos[nn], gn_full[nn])
        out = signed > 0
        entry[method] = {
            "body_samples": int(len(samples)),
            "pokethrough_pct": round(float(out.mean()*100), 2),
            "max_poke_mm": round(float(signed.max()*1000), 2),
            "mean_poke_mm_when_out": round(float(signed[out].mean()*1000), 2) if out.any() else 0.0,
        }
    results[state] = entry
    print(state, json.dumps(entry))

prev = json.loads((OUT/"metrics.json").read_text())
prev["body_through_garment"] = results
(OUT/"metrics.json").write_text(json.dumps(prev, indent=1))
print("metrics.json updated")
