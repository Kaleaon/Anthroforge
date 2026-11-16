#!/usr/bin/env python3
"""Base (stage2 = undeformed v5 layers) exterior/cage fold split."""
import sys
from collections import defaultdict
from pathlib import Path

import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from kaleaon_io import world_co, group_weights

CHAR = Path("/home/hatch/workspace/anthroforge-v2/characters/kaleaon-head")
bpy.ops.wm.open_mainfile(filepath=str(CHAR / "work" / "stage2.blend"))
objs = {o.name: o for o in bpy.data.objects if o.type == "MESH"}


def fold_stats(o, cage_idx):
    W5, _ = world_co(o)
    cage_set = set(int(i) for i in cage_idx)
    tris, cage_face = [], []
    for p in o.data.polygons:
        idx = list(p.vertices)
        for k in range(1, len(idx) - 1):
            t = (idx[0], idx[k], idx[k + 1])
            tris.append(t)
            cage_face.append(all(v in cage_set for v in t))
    tris = np.array(tris)
    cage_face = np.array(cage_face)
    A, B, C = W5[tris[:, 0]], W5[tris[:, 1]], W5[tris[:, 2]]
    n = np.cross(B - A, C - A)
    ln = np.linalg.norm(n, axis=1)
    n = n / np.maximum(ln, 1e-12)[:, None]
    edge_faces = defaultdict(list)
    for fi, t in enumerate(tris):
        for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            edge_faces[(min(a, b), max(a, b))].append(fi)
    ext, cage, ext_worst = [], [], []
    for (a, b), fs in edge_faces.items():
        if len(fs) == 2 and ln[fs[0]] > 1e-10 and ln[fs[1]] > 1e-10:
            dot = float(n[fs[0]] @ n[fs[1]])
            if cage_face[fs[0]] or cage_face[fs[1]]:
                cage.append(dot)
            else:
                ext.append(dot)
                if dot < 0.01:
                    ext_worst.append((dot, np.round(W5[[a, b]].mean(axis=0), 3).tolist()))
    ext = np.array(ext)
    cage = np.array(cage)
    ext_worst.sort()
    return {"exterior_pairs": len(ext),
            "exterior_min_dot": float(ext.min()),
            "exterior_below_0.01": int((ext < 0.01).sum()),
            "cage_pairs": len(cage),
            "cage_below_0.01": int((cage < 0.01).sum()),
            "exterior_worst": ext_worst[:6]}


for name in ("TissueHead", "Jaw"):
    o = objs[name]
    idx = np.where(group_weights(o, "LipCage") > 0)[0]
    print(name, fold_stats(o, idx))
print("BASE FOLD SPLIT DONE")
