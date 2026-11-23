#!/usr/bin/env python3
"""Stage 8 - final assembly: re-pivot Tongue and SkullMandible onto
the jaw hinge (world geometry byte-identical - the rig-pass interface
per spec 5.4: everything on the jaw train shares the hinge origin),
verify cage integrity on the blend (S20), export the GLB + final
blend. Gate numbers -> work/stage8.json."""
import json
import sys
from pathlib import Path

import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from kaleaon_io import world_co

CHAR = Path("/home/hatch/workspace/anthroforge-v2/characters/kaleaon-head")
bpy.ops.wm.open_mainfile(filepath=str(CHAR / "work" / "stage7.blend"))
objs = {o.name: o for o in bpy.data.objects if o.type == "MESH"}
HINGE = np.array([0.0, -0.2167, -0.1249])

rep = {}

# --- re-pivot: set origin to HINGE, shift local coords opposite ----
for name in ("Tongue", "SkullMandible"):
    o = objs[name]
    W0, _ = world_co(o)
    sum0 = W0.sum(axis=0)
    bb0 = (W0.min(axis=0), W0.max(axis=0))
    import mathutils
    o.matrix_world = mathutils.Matrix.Translation(
        mathutils.Vector(HINGE)) @ mathutils.Matrix.Identity(4)
    # local coords = world - hinge (matrix is a pure translation)
    V = np.empty(len(o.data.vertices) * 3)
    o.data.vertices.foreach_get("co", V)
    V = V.reshape(-1, 3)
    V[:] = W0 - HINGE
    o.data.vertices.foreach_set("co", V.ravel())
    o.data.update()
    W1, _ = world_co(o)
    rep[f"repivot_{name}"] = {
        "origin": list(np.round(HINGE, 4)),
        "world_sum_delta": float(np.abs(W1.sum(axis=0) - sum0).max()),
        "bbox_same": bool(np.allclose(W1.min(axis=0), bb0[0], atol=1e-7)
                          and np.allclose(W1.max(axis=0), bb0[1], atol=1e-7)),
    }

# --- origins audit --------------------------------------------------
rep["origins"] = {n: list(np.round(np.array(o.location), 4))
                  for n, o in objs.items()}

# --- S20 cage integrity (blend level) -------------------------------
def group_count(obj, gname):
    gi = obj.vertex_groups.find(gname)
    if gi < 0:
        return -1
    cnt = 0
    for v in obj.data.vertices:
        for g in v.groups:
            if g.group == gi and g.weight > 0.001:
                cnt += 1
                break
    return cnt

rep["cage_groups"] = {
    "TissueHead_LipCage": group_count(objs["TissueHead"], "LipCage"),
    "TissueHead_Philtrum": group_count(objs["TissueHead"], "Philtrum"),
    "Jaw_LipCage": group_count(objs["Jaw"], "LipCage"),
    "Jaw_Philtrum": group_count(objs["Jaw"], "Philtrum"),
    "CommissureL": group_count(objs["TissueHead"], "CommissureL")
    + group_count(objs["Jaw"], "CommissureL"),
    "CommissureR": group_count(objs["TissueHead"], "CommissureR")
    + group_count(objs["Jaw"], "CommissureR"),
    "Jaw_Chin": group_count(objs["Jaw"], "Chin"),
}
rep["object_counts"] = {n: (len(o.data.vertices), len(o.data.polygons))
                        for n, o in sorted(objs.items())}

# --- export ---------------------------------------------------------
REF = ["Skull", "SkullMandible", "Muscles"]
final = [o for n, o in objs.items() if n not in REF]
bpy.ops.object.select_all(action="DESELECT")
for o in final:
    o.select_set(True)
bpy.context.view_layer.objects.active = final[0]
bpy.ops.export_scene.gltf(
    filepath=str(CHAR / "kaleaon_head.glb"), export_format="GLB",
    use_selection=True, export_apply=True, export_yup=True)
for o in final:
    o.select_set(False)
bpy.ops.wm.save_as_mainfile(filepath=str(CHAR / "kaleaon_head.blend"))
print(json.dumps(rep, indent=1, default=str))
(CHAR / "work" / "stage8.json").write_text(json.dumps(rep, indent=1,
                                                      default=str))
print("STAGE 8 EXPORT DONE")
