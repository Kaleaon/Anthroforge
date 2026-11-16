#!/usr/bin/env python3
"""Where is the mane surface around the ear tip now? Nearest mane
verts to the tip + a fan of rays from the ear base."""
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, str(Path(__file__).parent))
from kaleaon_io import world_co

CHAR = Path("/home/hatch/workspace/anthroforge-v2/characters/kaleaon-head")
bpy.ops.wm.open_mainfile(filepath=str(CHAR / "kaleaon_head.blend"))
objs = {o.name: o for o in bpy.data.objects if o.type == "MESH"}
MW, _ = world_co(objs["ManeShell"])
tis, _ = world_co(objs["TissueHead"])
E, _ = world_co(objs["Ear_L"])
tip = np.array([0.3057, -0.1371, 0.3161])
d = np.linalg.norm(MW - tip, axis=1)
idx = np.argsort(d)[:6]
print("nearest mane verts to tip:")
for i in idx:
    print("   ", np.round(MW[i], 3), "dist", round(float(d[i]), 4))
tris = []
for p in objs["ManeShell"].data.polygons:
    v = list(p.vertices)
    for k in range(1, len(v) - 1):
        tris.append((v[0], v[k], v[k + 1]))
tree = BVHTree.FromPolygons([Vector(v) for v in MW], tris,
                            all_triangles=True)
dd = np.sqrt(((E[:, None, :] - tis[None, :, :]) ** 2).sum(-1)).min(axis=1)
qb = E[dd < np.percentile(dd, 25)].mean(axis=0)
print("quartile base:", np.round(qb, 3))
base_dir = (tip - qb) / np.linalg.norm(tip - qb)
rng = np.random.default_rng(0)
hits = 0
for k in range(25):
    jitter = rng.normal(0, 0.06, 3)
    direc = base_dir + jitter
    direc = direc / np.linalg.norm(direc)
    hit = tree.ray_cast(Vector(qb), Vector(direc), 0.6)
    if hit is not None and hit[0] is not None:
        hits += 1
        if k < 8:
            print("   fan hit dist", round(float(hit[3]), 4),
                  "at", np.round(np.array(hit[0]), 3))
print("fan hits:", hits, "/25; tip distance:",
      round(float(np.linalg.norm(tip - qb)), 4))
print("TIP FAN DONE")
