#!/usr/bin/env python3
"""Diagnostic: rim-pair separation + fold metric, base vs stage 3."""
import json
import sys
from collections import defaultdict
from pathlib import Path

import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from kaleaon_io import world_co, group_weights

CHAR = Path("/home/hatch/workspace/anthroforge-v2/characters/kaleaon-head")


def cage(o):
    W, _ = world_co(o)
    idx = np.where(group_weights(o, "LipCage") > 0)[0]
    return idx, W[idx]


def fold_stats(o):
    W, _ = world_co(o)
    tris = []
    for p in o.data.polygons:
        idx = list(p.vertices)
        for k in range(1, len(idx) - 1):
            tris.append((idx[0], idx[k], idx[k + 1]))
    tris = np.array(tris)
    A, B, C = W[tris[:, 0]], W[tris[:, 1]], W[tris[:, 2]]
    n = np.cross(B - A, C - A)
    area2 = np.linalg.norm(n, axis=1)
    degen = int((area2 < 1e-10).sum())
    n = n / np.maximum(area2, 1e-12)[:, None]
    edge_faces = defaultdict(list)
    for fi, t in enumerate(tris):
        for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            edge_faces[(min(a, b), max(a, b))].append(fi)
    dots, cents = [], []
    for (a, b), fs in edge_faces.items():
        if len(fs) == 2 and area2[fs[0]] > 1e-10 and area2[fs[1]] > 1e-10:
            dots.append(float(n[fs[0]] @ n[fs[1]]))
            cents.append(W[[a, b]].mean(axis=0))
    dots = np.array(dots)
    cents = np.array(cents)
    worst = np.argsort(dots)[:8]
    return {"pairs": len(dots), "degen_faces": degen,
            "min_dot": float(dots.min()),
            "n_below_0.01": int((dots < 0.01).sum()),
            "n_below_0": int((dots < 0).sum()),
            "n_below_-0.5": int((dots < -0.5).sum()),
            "worst": [{"dot": round(float(dots[i]), 4),
                       "at": np.round(cents[i], 3).tolist()}
                      for i in worst]}


out = {}
for tag, path in (("base", CHAR / "work" / "stage2.blend"),
                  ("stage3", CHAR / "work" / "stage3.blend")):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    objs = {o.name: o for o in bpy.data.objects if o.type == "MESH"}
    ti, TP = cage(objs["TissueHead"])
    ji, JP = cage(objs["Jaw"])
    d = np.sqrt(((TP[:, None, :] - JP[None, :, :]) ** 2).sum(-1))
    jmin = d.argmin(axis=1)
    dmin = d[np.arange(len(TP)), jmin]
    out[tag] = {
        "rim_pairs_under_0.0005": int((dmin < 0.0005).sum()),
        "rim_pairs_under_0.002": int((dmin < 0.002).sum()),
        "cage_nearest_dist_p50": float(np.percentile(dmin, 50)),
        "cage_nearest_dist_p90": float(np.percentile(dmin, 90)),
        "cage_nearest_dist_max": float(dmin.max()),
        "fold_TissueHead": fold_stats(objs["TissueHead"]),
        "fold_Jaw": fold_stats(objs["Jaw"]),
    }
    if tag == "base":
        rim_idx = np.where(dmin < 0.0005)[0]
        np.save(CHAR / "work" / "rim_tissue_idx.npy", ti[rim_idx])
        np.save(CHAR / "work" / "rim_jaw_idx.npy", ji[jmin[rim_idx]])
        out["rim_pair_count_saved"] = int(len(rim_idx))

print(json.dumps(out, indent=1))
print("DIAG DONE")
