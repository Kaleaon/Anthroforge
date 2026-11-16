#!/usr/bin/env python3
"""What's beside the ear? Mane/tissue verts in the ear's (y,z) box."""
import sys
from pathlib import Path

import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from kaleaon_io import world_co

CHAR = Path("/home/hatch/workspace/anthroforge-v2/characters/kaleaon-head")
bpy.ops.wm.open_mainfile(filepath=str(CHAR / "work" / "stage7.blend"))
objs = {o.name: o for o in bpy.data.objects if o.type == "MESH"}

for name in ("TissueHead", "ManeShell"):
    W, _ = world_co(objs[name])
    box = W[(W[:, 1] > -0.24) & (W[:, 1] < -0.12)
            & (W[:, 2] > 0.20) & (W[:, 2] < 0.32) & (W[:, 0] > 0)]
    print(f"{name}: {len(box)} verts in ear box (y -0.24..-0.12, z 0.20..0.32, x>0)")
    if len(box):
        print("   x range", np.round([box[:, 0].min(), box[:, 0].max()], 3),
              " y range", np.round([box[:, 1].min(), box[:, 1].max()], 3),
              " z range", np.round([box[:, 2].min(), box[:, 2].max()], 3))
EW, _ = world_co(objs["Ear_L"])
print("Ear_L total verts", len(EW), "x max", EW[:, 0].max())
# nearest mane verts to the ear's outer rim point
target = np.array([0.368, -0.1806, 0.2639])
MW, _ = world_co(objs["ManeShell"])
d = np.linalg.norm(MW - target, axis=1)
idx = np.argsort(d)[:5]
for i in idx:
    print("   mane near rim:", np.round(MW[i], 3), "dist", round(float(d[i]), 3))
print("MANE PROBE DONE")
