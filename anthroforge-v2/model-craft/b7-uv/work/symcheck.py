import bpy, json
import numpy as np
from mathutils import kdtree

def per_vertex_uv(me):
    uv_layer = me.uv_layers.active
    if uv_layer is None: return None
    vuv = {}
    for loop in me.loops:
        if loop.vertex_index not in vuv:
            vuv[loop.vertex_index] = uv_layer.data[loop.index].uv
    return vuv

def symcheck(ob):
    """For each vertex, find its sagittal mirror partner (KD-tree on x*-1).
    Test BOTH mirror conventions:
      shared-texel (S): partner UV == own UV
      centre-mirror (P): partner UV == (1-u, v)
    """
    me = ob.data
    vuv = per_vertex_uv(me)
    if vuv is None: return {"object": ob.name, "uv": None}
    P = np.empty((len(me.vertices), 3)); me.vertices.foreach_get("co", P.ravel())
    kd = kdtree.KDTree(len(P))
    for i, p in enumerate(P): kd.insert(p, i)
    kd.balance()
    idxs = np.array(sorted(vuv.keys()))
    rng = np.random.default_rng(0)
    sample = idxs if len(idxs) <= 4000 else rng.choice(idxs, 4000, replace=False)
    scale = np.linalg.norm(P.max(0) - P.min(0))
    tot = 0; goodS = 0; goodP = 0; errS = []; errP = []
    for i in sample:
        mir = P[i].copy(); mir[0] *= -1
        _, j, d = kd.find(mir)
        if d < 0.01 * scale and j in vuv:
            tot += 1
            ui, vi = float(vuv[i].x), float(vuv[i].y)
            uj, vj = float(vuv[j].x), float(vuv[j].y)
            eS = (abs(ui - uj), abs(vi - vj))
            eP = (abs(ui - (1.0 - uj)), abs(vi - vj))
            errS.append(eS); errP.append(eP)
            if eS[0] < 0.02 and eS[1] < 0.02: goodS += 1
            if eP[0] < 0.02 and eP[1] < 0.02: goodP += 1
    if tot < 20: return {"object": ob.name, "pairs": tot, "note": "too few pairs"}
    errS = np.array(errS); errP = np.array(errP)
    return {"object": ob.name, "pairs": tot,
            "shared_texel_within_0.02_pct": round(100 * goodS / tot, 1),
            "shared_mean_abs_du": round(float(errS[:, 0].mean()), 4),
            "shared_mean_abs_dv": round(float(errS[:, 1].mean()), 4),
            "centre_mirror_within_0.02_pct": round(100 * goodP / tot, 1),
            "centre_mean_abs_du": round(float(errP[:, 0].mean()), 4),
            "centre_mean_abs_dv": round(float(errP[:, 1].mean()), 4)}

jobs = [
 ("glb", "/home/hatch/workspace/stick-figure-avatar/furry-lineup/threejs-lineup/models/border_collie.glb", "0"),
 ("glb", "/home/hatch/workspace/bodies-3d/parts-library/sketchfab/anthro-fennec-rigged-codaj/anthro_fennec_rigged.glb", "Object_113"),
 ("glb", "/home/hatch/workspace/anthroforge-v2/base-head-v3/neutral_base_head_v3.glb", "TissueHead"),
 ("blend", "/home/hatch/workspace/anthroforge-v2/model-craft/b7-uv/work/head_reunwrap.blend", "TissueHead"),
]
out = {}
for kind, path, nm in jobs:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if kind == "glb":
        bpy.ops.import_scene.gltf(filepath=path)
    else:
        bpy.ops.wm.open_mainfile(filepath=path)
    ob = bpy.context.scene.objects.get(nm)
    key = path.split("/")[-1] + ":" + nm
    out[key] = symcheck(ob) if ob else {"error": "object not found"}
    print("SYMCHECK", key, json.dumps(out[key]))
with open("/home/hatch/workspace/anthroforge-v2/model-craft/b7-uv/work/symcheck.json", "w") as f:
    json.dump(out, f, indent=1)
print("DONE")
