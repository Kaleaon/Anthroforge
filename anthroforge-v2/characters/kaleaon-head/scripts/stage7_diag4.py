#!/usr/bin/env python3
"""Mane (y,z) silhouette coverage by z row + spot rays."""
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, str(Path(__file__).parent))
from kaleaon_io import world_co

CHAR = Path("/home/hatch/workspace/anthroforge-v2/characters/kaleaon-head")
bpy.ops.wm.open_mainfile(filepath=str(CHAR / "work" / "stage7.blend"))
objs = {o.name: o for o in bpy.data.objects if o.type == "MESH"}
MW, _ = world_co(objs["ManeShell"])
print("mane verts:", len(MW))
for z0 in (0.10, 0.16, 0.22, 0.28, 0.32):
    row = MW[np.abs(MW[:, 2] - z0) < 0.02]
    if len(row):
        print(f" z~{z0}: n={len(row)} y [{row[:,1].min():.3f},{row[:,1].max():.3f}] "
              f"|x|max {np.abs(row[:,0]).max():.3f}")
    else:
        print(f" z~{z0}: no verts")
tris = []
for p in objs["ManeShell"].data.polygons:
    idx = list(p.vertices)
    for k in range(1, len(idx) - 1):
        tris.append((idx[0], idx[k], idx[k + 1]))
tree = BVHTree.FromPolygons([Vector(v) for v in MW], tris, all_triangles=True)
for (yy, zz) in ((-0.137, 0.316), (-0.18, 0.26), (-0.18, 0.15), (0.0, 0.2)):
    hit = tree.ray_cast(Vector((2.0, yy, zz)), Vector((-1, 0, 0)), 10.0)
    print(f" ray at y={yy} z={zz}:",
          None if hit is None or hit[0] is None else np.round(np.array(hit[0]), 3))
print("SILHOUETTE PROBE DONE")
