#!/usr/bin/env python3
"""Ear diagnostic: seat delta anatomy + ear clouds base vs stage 6."""
import sys
from pathlib import Path

import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from kaleaon_io import world_co

CHAR = Path("/home/hatch/workspace/anthroforge-v2/characters/kaleaon-head")

# base tissue from stage2, deformed tissue + ear from stage5 (pre-ear ops)
bpy.ops.wm.open_mainfile(filepath=str(CHAR / "work" / "stage5.blend"))
objs5 = {o.name: o for o in bpy.data.objects if o.type == "MESH"}
TW2, _ = world_co(objs5["TissueHead"])
E5, _ = world_co(objs5["Ear_L"])
with bpy.data.libraries.load(str(CHAR / "work" / "stage2.blend")) as (src, dst):
    dst.objects = ["TissueHead"]
bt = dst.objects[0]
TW, _ = world_co(bt)
bpy.data.objects.remove(bt, do_unlink=True)

d = np.sqrt(((E5[:, None, :] - TW2[None, :, :]) ** 2).sum(-1)).min(axis=1)
base = E5[d < np.percentile(d, 25)].mean(axis=0)
print("ear base (vs deformed tissue):", np.round(base, 4))
idx0 = int(np.argmin(np.linalg.norm(TW - base, axis=1)))
print("material point idx0:", idx0, "base pos", np.round(TW[idx0], 4),
      "deformed pos", np.round(TW2[idx0], 4),
      "delta", np.round(TW2[idx0] - TW[idx0], 4))
# what tissue region is idx0 in? neighbours
print("tissue vert count:", len(TW))
# ear cloud at stage 5
print("stage5 ear bbox min", np.round(E5.min(axis=0), 3),
      "max", np.round(E5.max(axis=0), 3))
tip5 = E5[np.argmax(np.linalg.norm(E5 - base, axis=1))]
print("stage5 ear tip (max dist from base):", np.round(tip5, 4))

bpy.ops.wm.open_mainfile(filepath=str(CHAR / "work" / "stage6.blend"))
objs6 = {o.name: o for o in bpy.data.objects if o.type == "MESH"}
E6, _ = world_co(objs6["Ear_L"])
print("stage6 ear bbox min", np.round(E6.min(axis=0), 3),
      "max", np.round(E6.max(axis=0), 3))
# where did the stage-5 tip vertex go? vertex order is stable
ti = int(np.argmax(np.linalg.norm(E5 - base, axis=1)))
print("stage5 tip vert now at:", np.round(E6[ti], 4))
print("EAR DIAG DONE")
