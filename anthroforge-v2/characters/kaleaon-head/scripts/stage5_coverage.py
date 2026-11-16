#!/usr/bin/env python3
"""Centre-column lid coverage: at the iris centre column, how far
down does the upper lid margin reach over the iris? (Base vs built.)"""
import sys
from pathlib import Path

import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from kaleaon_io import world_co

CHAR = Path("/home/hatch/workspace/anthroforge-v2/characters/kaleaon-head")

for tag, path in (("v5base", "/home/hatch/workspace/anthroforge-v2/base-head-v5/neutral_base_head_v5.blend"),
                  ("stage5", str(CHAR / "work" / "stage5.blend"))):
    bpy.ops.wm.open_mainfile(filepath=path)
    objs = {o.name: o for o in bpy.data.objects if o.type == "MESH"}
    for s in ("L",):
        IR, _ = world_co(objs[f"Iris_{s}"])
        MG, _ = world_co(objs[f"LidMargin_{s}"])
        LD, _ = world_co(objs[f"Eyelid_{s}"])
        cx, cz = IR[:, 0].mean(), IR[:, 2].mean()
        top, bot = IR[:, 2].max(), IR[:, 2].min()
        d = top - bot
        # centre column of the margin: verts within 12% of d of centre x,
        # upper half; the margin's z there = the lid edge over the pupil
        col = MG[(np.abs(MG[:, 0] - cx) < 0.12 * d) & (MG[:, 2] > cz)]
        edge_z = float(col[:, 2].min()) if len(col) else None
        # also the eyelid shell's own lowest anterior point at centre col
        col2 = LD[(np.abs(LD[:, 0] - cx) < 0.12 * d) & (LD[:, 2] > cz)]
        edge2_z = float(col2[:, 2].min()) if len(col2) else None
        print(f"{tag} {s}: iris d={d:.4f} top={top:.4f} centre={cz:.4f} "
              f"margin_edge_z={edge_z} coverage="
              f"{(top - edge_z) / d if edge_z else None} "
              f"lid_edge_z={edge2_z} coverage2="
              f"{(top - edge2_z) / d if edge2_z else None}")
print("COVERAGE PROBE DONE")
