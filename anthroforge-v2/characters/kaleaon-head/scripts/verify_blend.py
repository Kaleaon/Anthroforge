#!/usr/bin/env python3
"""Blend-side S10 + S14: locate the stage-6 tracked tip vertex in the
final blend (nearest vert to the recorded position), measure its
height above the palate (rulers definition), and cast the growth ray
from the ear's quartile base through it against the mane BVH."""
import json
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
rep = {}

tis, _ = world_co(objs["TissueHead"])
tu, _ = world_co(objs["TeethUpper"])
balls = np.vstack([world_co(objs["Eyeball_L"])[0],
                   world_co(objs["Eyeball_R"])[0]])
ec = balls.mean(axis=0)
L = float(tis[:, 1].max() - tis[:, 1].min())
ant = tu[tu[:, 1] > ec[1] + 0.10 * L]
pal = float(ant[:, 2].max())
rep["pal_z_rulers_def"] = pal
rep["L_built"] = L

MW, _ = world_co(objs["ManeShell"])
tris = []
for p in objs["ManeShell"].data.polygons:
    idx = list(p.vertices)
    for k in range(1, len(idx) - 1):
        tris.append((idx[0], idx[k], idx[k + 1]))
tree = BVHTree.FromPolygons([Vector(v) for v in MW], tris,
                            all_triangles=True)

stage6 = json.loads((CHAR / "work" / "stage6.json").read_text())
for s in ("L", "R"):
    E, _ = world_co(objs[f"Ear_{s}"])
    recorded = np.array(stage6[f"ear_{s}"]["tip"])
    j = int(np.argmin(np.linalg.norm(E - recorded, axis=1)))
    tip = E[j]
    # quartile base (verify definition), numpy distance field
    d = np.sqrt(((E[:, None, :] - tis[None, :, :]) ** 2).sum(-1)).min(axis=1)
    qb = E[d < np.percentile(d, 25)].mean(axis=0)
    direction = tip - qb
    dist = float(np.linalg.norm(direction))
    hit = tree.ray_cast(Vector(qb), Vector(direction / dist), dist * 3)
    surf = None if hit is None or hit[0] is None else float(hit[3])
    # also the max-z vert
    tipz = E[int(np.argmax(E[:, 2]))]
    rep[f"S10_S14_{s}"] = {
        "tip_vert_found_dist": float(np.linalg.norm(tip - recorded)),
        "tip_pos": tip.tolist(),
        "tip_height_L": float((tip[2] - pal) / L),
        "maxz_height_L": float((tipz[2] - pal) / L),
        "growth_ray": {"tip_dist": dist, "mane_surface_dist": surf,
                       "buried": bool(surf is not None
                                      and surf >= dist - 0.005)},
    }
print(json.dumps(rep, indent=1, default=str))
(CHAR / "work" / "verify_blend.json").write_text(json.dumps(rep, indent=1,
                                                           default=str))
print("BLEND VERIFY DONE")
