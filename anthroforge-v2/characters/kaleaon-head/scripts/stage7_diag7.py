#!/usr/bin/env python3
"""Mane symmetry in the final blend + object transform audit."""
import sys
from pathlib import Path

import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from kaleaon_io import world_co

CHAR = Path("/home/hatch/workspace/anthroforge-v2/characters/kaleaon-head")
bpy.ops.wm.open_mainfile(filepath=str(CHAR / "kaleaon_head.blend"))
o = bpy.data.objects["ManeShell"]
print("matrix_world:\n", np.round(np.array(o.matrix_world), 4))
print("location", tuple(np.round(o.location, 4)),
      "rotation", tuple(np.round(o.rotation_euler, 4)),
      "scale", tuple(np.round(o.scale, 4)))
W, _ = world_co(o)
print("bbox x:", W[:, 0].min(), W[:, 0].max(),
      " y:", W[:, 1].min(), W[:, 1].max(),
      " z:", W[:, 2].min(), W[:, 2].max())
src = W[W[:, 0] > 0.002]
mir = src * np.array([-1.0, 1.0, 1.0])
# chunked nearest
best = np.full(len(src), 1e9)
for i in range(0, len(W), 1024):
    chunk = W[i:i + 1024]
    d = np.sqrt(((mir[:, None, :] - chunk[None, :, :]) ** 2).sum(-1)).min(axis=1)
    best = np.minimum(best, d)
print("blend mane mirrored-nearest: max", round(float(best.max()), 4),
      "mean", round(float(best.mean()), 5),
      "pct>0.01:", round(float((best > 0.01).mean()) * 100, 1))
print("MANE SYM BLEND DONE")
