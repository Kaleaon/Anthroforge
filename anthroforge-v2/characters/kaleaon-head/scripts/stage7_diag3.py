#!/usr/bin/env python3
"""S14 ray test: at each ear vertex's (y,z), cast along -x from
outside; the first mane hit gives the shell's surface |x| there.
Buried: surface |x| >= ear |x| - 0.005. No hit: outside the mane's
(y,z) footprint entirely (emergence zone - judged by location)."""
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
tris = []
for p in objs["ManeShell"].data.polygons:
    idx = list(p.vertices)
    for k in range(1, len(idx) - 1):
        tris.append((idx[0], idx[k], idx[k + 1]))
tree = BVHTree.FromPolygons([Vector(v) for v in MW], tris,
                            all_triangles=True)
for s in ("L", "R"):
    EW, _ = world_co(objs[f"Ear_{s}"])
    side = 1.0 if EW[:, 0].mean() >= 0 else -1.0
    buried = proud = nofoot = 0
    worst = (0.0, None)
    nofoot_pts = []
    for p in EW:
        hit = tree.ray_cast(Vector((side * 2.0, p[1], p[2])),
                            Vector((-side, 0, 0)), 10.0)
        if hit is None or hit[0] is None:
            nofoot += 1
            nofoot_pts.append(p)
            continue
        surf_x = abs(float(hit[0][0]))
        excess = abs(p[0]) - surf_x
        if excess <= 0.005:
            buried += 1
        else:
            proud += 1
            if excess > worst[0]:
                worst = (excess, p)
    print(f"Ear_{s}: buried {buried}, proud {proud} "
          f"(worst excess {worst[0]:.4f} at {np.round(worst[1],3) if worst[1] is not None else None}), "
          f"no-footprint {nofoot}")
    if nofoot_pts:
        nf = np.array(nofoot_pts)
        print("   no-footprint y range", np.round([nf[:, 1].min(), nf[:, 1].max()], 3),
              "z range", np.round([nf[:, 2].min(), nf[:, 2].max()], 3),
              "|x| range", np.round([np.abs(nf[:, 0]).min(), np.abs(nf[:, 0]).max()], 3))
print("S14 RAY DONE")
