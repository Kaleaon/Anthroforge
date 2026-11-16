"""Body->garment poke-through with opening exclusion: samples whose closest
garment point lies within 20 mm of a garment boundary vertex (armhole, scoop,
hem openings -- exposed skin by design) are excluded, same mask logic per state."""
import json
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
import importlib.util
spec = importlib.util.spec_from_file_location("mf", Path(__file__).with_name("measure_final.py"))

OUT = Path.home() / "workspace/anthroforge-v2/model-craft/b15-clothing"
d = np.load(OUT/"scripts/garment_data.npz")
base, faces = d["base"], d["faces"]
g_idx, gq = d["g_idx"], d["g_faces"]
g_faces = np.vstack([gq[:, [0,1,2]], gq[:, [0,2,3]]])
BODY_END = 13380
tris = faces[np.all(faces < BODY_END, axis=1)]
src = np.zeros(len(base), bool); src[g_idx] = True
sample_faces = tris[np.all(src[tris], axis=1)]

# boundary verts of the patch (edges used by exactly one face)
edges = np.vstack([g_faces[:, [0,1]], g_faces[:, [1,2]], g_faces[:, [2,0]]])
es = np.sort(edges, axis=1)
uniq, counts = np.unique(es, axis=0, return_counts=True)
bnd_verts = np.unique(uniq[counts == 1])
print("boundary verts:", len(bnd_verts))

# reuse signed_dist machinery by exec'ing the module's function defs only
import re
code = Path(__file__).with_name("measure_final.py").read_text()
fn = code[code.index("def cand_array"):code.index("results = {}")]
ns = {"np": np, "cKDTree": cKDTree, "PAD": 72}
exec(fn, ns)
signed_dist = ns["signed_dist"]

results = {}
for state in ["neutral", "strongman", "fat_v51", "gachidebu"]:
    delta = d[f"delta_{state}"]
    deformed = base + delta
    samples = np.concatenate([deformed[src], deformed[sample_faces].mean(axis=1)])
    entry = {}
    for m in ["A", "B", "C"]:
        gpos = d[f"{state}_{m}"] if m != "C" else np.load(OUT/f"scripts/garmentC_{state}.npy")
        btree = cKDTree(gpos[bnd_verts])
        dbnd, _ = btree.query(samples)
        keep = dbnd > 0.020
        bout = signed_dist(samples[keep], gpos, g_faces)
        entry[m] = {"samples_kept": int(keep.sum()),
                    "body_samples_poking_pct": round(float((bout > 0).mean()*100), 2),
                    "body_max_poke_mm": round(float(bout.max()*1000), 2) if (bout > 0).any() else 0.0,
                    "body_mean_poke_mm_when_out": round(float(bout[bout > 0].mean()*1000), 2) if (bout > 0).any() else 0.0}
    results[state] = entry
    print(state, json.dumps(entry), flush=True)

prev = json.loads((OUT/"metrics.json").read_text())
prev["body_poke_openings_excluded"] = results
(OUT/"metrics.json").write_text(json.dumps(prev, indent=1))
print("written")
