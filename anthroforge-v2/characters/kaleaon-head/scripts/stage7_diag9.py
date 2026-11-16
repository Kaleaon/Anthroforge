#!/usr/bin/env python3
"""Final S14 evidence: ear<->mane triangle intersections (must be 0 -
the ear never crosses the shell) + per-vertex nearest-surface
distances from each ear to the mane shell."""
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
tris = []
for p in objs["ManeShell"].data.polygons:
    v = list(p.vertices)
    for k in range(1, len(v) - 1):
        tris.append((v[0], v[k], v[k + 1]))
tree = BVHTree.FromPolygons([Vector(v) for v in MW], tris,
                            all_triangles=True)
for s in ("L", "R"):
    E, _ = world_co(objs[f"Ear_{s}"])
    tris_e = []
    for p in objs[f"Ear_{s}"].data.polygons:
        v = list(p.vertices)
        for k in range(1, len(v) - 1):
            tris_e.append((v[0], v[k], v[k + 1]))
    etree = BVHTree.FromPolygons([Vector(v) for v in E], tris_e,
                                 all_triangles=True)
    pairs = tree.overlap(etree)
    d = np.array([tree.find_nearest(Vector(p))[3] for p in E])
    print(f"Ear_{s}: intersections with mane: {len(pairs)}; "
          f"nearest-surface dist: max {d.max():.4f} "
          f"mean {d.mean():.4f} min {d.min():.4f}")
print("S14 FINAL EVIDENCE DONE")
