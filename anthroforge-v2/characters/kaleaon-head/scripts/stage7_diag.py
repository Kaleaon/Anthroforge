#!/usr/bin/env python3
"""S14 grid test: for each ear vertex, compare |x| against the mane
shell's max |x| in the same (y,z) bin - who pokes out, and where?"""
import sys
from collections import defaultdict
from pathlib import Path

import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from kaleaon_io import world_co

CHAR = Path("/home/hatch/workspace/anthroforge-v2/characters/kaleaon-head")
bpy.ops.wm.open_mainfile(filepath=str(CHAR / "work" / "stage7.blend"))
objs = {o.name: o for o in bpy.data.objects if o.type == "MESH"}
MW, _ = world_co(objs["ManeShell"])
BIN = 0.02
grid = defaultdict(float)
for p in MW:
    key = (int(np.floor(p[1] / BIN)), int(np.floor(p[2] / BIN)))
    grid[key] = max(grid[key], abs(p[0]))

for s in ("L", "R"):
    EW, _ = world_co(objs[f"Ear_{s}"])
    proud = []
    for p in EW:
        best = 0.0
        ky, kz = int(np.floor(p[1] / BIN)), int(np.floor(p[2] / BIN))
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                best = max(best, grid.get((ky + dy, kz + dz), 0.0))
        if abs(p[0]) > best + 0.005:
            proud.append((abs(p[0]) - best, p))
    proud.sort(reverse=True)
    print(f"Ear_{s}: {len(proud)}/{len(EW)} verts proud of the mane")
    for d, p in proud[:6]:
        print("   protrusion", round(float(d), 4), "at", np.round(p, 3))
print("S14 GRID DONE")
