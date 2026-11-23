#!/usr/bin/env python3
"""Diagnostic: rim-pair separation + fold metric, base vs stage 3."""
import json
import sys
from pathlib import Path

import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from kaleaon_io import fold_stats, group_weights, world_co

CHAR = Path(__file__).resolve().parents[1]


def cage(o):
    W, _ = world_co(o)
    idx = np.where(group_weights(o, "LipCage") > 0)[0]
    return idx, W[idx]


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
