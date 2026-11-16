#!/usr/bin/env python3
"""Sen head rebuild driver (2026-11-16) — corrected builder + Sen's
tongue direction.

Runs the batch's corrected generic builder
(characters/pyn/scripts/build_head.py — side taken from each part's
own position, base-head-v4, parameterised --base) with Sen's
UNCHANGED batch-1 vector (scripts/sen_vector.json), in one Blender
session, then applies the one character direction the generic builder
deliberately leaves out: Sen's tongue x1.3, carried over from the
original build (characters/sen/scripts/build_head.py, its section
4.3; SEN_BUILD.md S3: "Sen canon: huge tongue"). The scale is applied
exactly as the original did — uniformly about the tongue's posterior
base (mean of the 20 most posterior verts) — and the tongue report is
written into work/head_measure.json in the original's format. The
builder's own exports are then re-written so the shipped GLB/blend
carry the scaled tongue. Teeth verification is the builder's (the
tongue takes no part in the upper/lower BVH check).

The original 2026-11-12 script keyed left/right off object names
(side = +1 iff the name ends in "R"); in this head frame Ear_L /
Eyeball_L sit at +x, so Sen's EarSpread and EyeSpacing shifts ran
mirrored. That script is preserved untouched as the historical
record; this driver supersedes it.

Run: HOME=/tmp/af_home xvfb-run -a blender -b --threads 2 \
     --python build_sen_head.py
"""
import json
import sys
from pathlib import Path

import numpy as np

SEN = Path("/home/hatch/workspace/anthroforge-v2/characters/sen")
BUILDER = Path("/home/hatch/workspace/anthroforge-v2/characters/pyn"
               "/scripts/build_head.py")
BASE = Path("/home/hatch/workspace/anthroforge-v2/base-head-v4"
            "/neutral_base_head_v4.glb")

sys.argv = ["blender", "-b", "--python", str(BUILDER), "--",
            "--char", "sen",
            "--vector", str(SEN / "scripts" / "sen_vector.json"),
            "--base", str(BASE),
            "--outdir", str(SEN)]
g = {"__name__": "__main__", "__file__": str(BUILDER)}
exec(compile(BUILDER.read_text(), str(BUILDER), "exec"), g)

# ------------------------------------------------ Sen tongue x1.3
import bpy  # noqa: E402  (same module the builder imported)

world_co, set_world, objs = g["world_co"], g["set_world"], g["objs"]
L = g["L"]
tg = objs["Tongue"]
GW, GM = world_co(tg)
gbase = GW[np.argsort(GW[:, 1])[:20]].mean(axis=0)   # posterior base
GW = gbase + (GW - gbase) * 1.3
set_world(tg, GW, GM)
JW2, _ = world_co(objs["Jaw"])
tongue_report = {
    "scale": 1.3,
    "tongue_y_extent_L": float(np.ptp(GW[:, 1]) / L),
    "jaw_y_extent_L": float(np.ptp(JW2[:, 1]) / L),
    "tongue_max_forward_vs_jaw_front": float(
        (GW[:, 1].max() - JW2[:, 1].max()) / L),
    "note": "bbox-level clearance, as the original build reported; "
            "the v4 split arcades make a true teeth occlusion check "
            "possible and the builder's BVH verify covers the teeth "
            "(tongue not a party to it). Tongue direction carried "
            "from the original build, not a slider.",
}
mpath = SEN / "work" / "head_measure.json"
rep = json.loads(mpath.read_text())
rep["tongue"] = tongue_report
rep["build_driver"] = ("characters/sen/scripts/build_sen_head.py — "
                       "corrected batch builder (pyn/scripts/"
                       "build_head.py) + tongue x1.3 step")
mpath.write_text(json.dumps(rep, indent=1))
print("tongue report:", json.dumps(tongue_report, indent=1))

# re-export so the shipped files carry the scaled tongue (same calls
# as the builder's own export)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(filepath=str(SEN / "sen_head.glb"),
                          export_format="GLB", use_selection=True)
bpy.ops.wm.save_as_mainfile(filepath=str(SEN / "sen_head.blend"))
print("SEN HEAD REBUILD DONE (corrected builder + tongue x1.3)")
