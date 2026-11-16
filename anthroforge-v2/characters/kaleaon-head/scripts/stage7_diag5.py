#!/usr/bin/env python3
"""Definitive S14: rasterise the mane's triangles into a (y,z) grid
(0.005 cells, coverage = any triangle covering the cell), then test
every ear vertex's (y,z) against the raster + the surface |x| from
the covering triangles' interpolated x-extent (max |x| per cell)."""
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
tris = []
for p in objs["ManeShell"].data.polygons:
    idx = list(p.vertices)
    for k in range(1, len(idx) - 1):
        tris.append((idx[0], idx[k], idx[k + 1]))
tris = np.array(tris)
CELL = 0.005
cover = defaultdict(float)   # (iy, iz) -> max |x| of surface covering cell


def raster(P):
    iy = int(np.floor(P[1] / CELL))
    iz = int(np.floor(P[2] / CELL))
    return iy, iz


for t in tris:
    A, B, C = MW[t[0]], MW[t[1]], MW[t[2]]
    ys = [A[1], B[1], C[1]]
    zs = [A[2], B[2], C[2]]
    iy0, iy1 = int(np.floor(min(ys) / CELL)), int(np.floor(max(ys) / CELL))
    iz0, iz1 = int(np.floor(min(zs) / CELL)), int(np.floor(max(zs) / CELL))
    # barycentric coverage via signed areas (orientation-proof)
    def area2(P, Q, R):
        return (Q[1] - P[1]) * (R[2] - P[2]) - (R[1] - P[1]) * (Q[2] - P[2])

    den = area2(A, B, C)
    if abs(den) < 1e-12:
        continue
    for iy in range(iy0, iy1 + 1):
        for iz in range(iz0, iz1 + 1):
            P = (0.0, (iy + 0.5) * CELL, (iz + 0.5) * CELL)
            w0 = area2(P, B, C) / den
            w1 = area2(A, P, C) / den
            w2 = 1.0 - w0 - w1
            if w0 >= -0.01 and w1 >= -0.01 and w2 >= -0.01:
                x = w0 * A[0] + w1 * B[0] + w2 * C[0]
                key = (iy, iz)
                if abs(x) > cover[key]:
                    cover[key] = abs(x)

for s in ("L", "R"):
    EW, _ = world_co(objs[f"Ear_{s}"])
    inside = proud = outside = 0
    worst = (0.0, None)
    out_pts = []
    for p in EW:
        iy, iz = raster(p)
        best = 0.0
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                best = max(best, cover.get((iy + dy, iz + dz), 0.0))
        if best == 0.0:
            outside += 1
            out_pts.append(p)
        elif abs(p[0]) <= best + 0.005:
            inside += 1
        else:
            proud += 1
            if abs(p[0]) - best > worst[0]:
                worst = (abs(p[0]) - best, p)
    print(f"Ear_{s}: inside-mane {inside}, proud {proud} "
          f"(worst {worst[0]:.4f} at {np.round(worst[1],3) if worst[1] is not None else None}), "
          f"outside-profile {outside}")
    if out_pts:
        op = np.array(out_pts)
        print("   outside y", np.round([op[:, 1].min(), op[:, 1].max()], 3),
              "z", np.round([op[:, 2].min(), op[:, 2].max()], 3))
print("S14 RASTER DONE")
