import bpy, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

bpy.ops.wm.open_mainfile(filepath="/home/hatch/workspace/anthroforge-v2/parts-lab/kaleaon-anatomy/kaleaon_anatomy_parts.blend")
dg = bpy.context.evaluated_depsgraph_get()

def ev(name):
    ob = bpy.data.objects[name]; e = ob.evaluated_get(dg); me = e.to_mesh()
    V = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("co", V)
    V = V.reshape(-1, 3); M = np.array(e.matrix_world)
    W = (M[:3, :3] @ V.T).T + M[:3, 3]
    e.to_mesh_clear()
    tree = BVHTree.FromObject(ob, dg)
    return W, tree

def inside_count(a_name, b_name):
    W, _ = ev(a_name)
    _, tb = ev(b_name)
    inside = 0; mind = 1e9
    for v in W:
        loc, nrm, idx, dist = tb.find_nearest(Vector(v))
        mind = min(mind, dist)
        if (Vector(v) - loc) @ nrm < -1e-6:
            inside += 1
    return {"verts_of_A_inside_B": inside, "A_total": len(W), "min_dist_mm": round(mind * 1000, 3)}

pairs = [("Part_Shaft_1", "Part_Shaft_2"), ("Part_Shaft_2", "Part_Shaft_1"),
         ("Part_Shaft_1", "Part_Shaft_3"), ("Part_Shaft_1", "Part_SacUdder"),
         ("Part_Shaft_2", "Part_SacUdder"), ("Part_SacUdder", "Part_Shaft_1"),
         ("Part_SacUdder_Teat_1", "Part_SacUdder")]
out = {}
for a, b in pairs:
    out[f"{a} in {b}"] = inside_count(a, b)
    print(a, "in", b, out[f"{a} in {b}"], flush=True)
json.dump(out, open("/home/hatch/workspace/anthroforge-v2/parts-lab/kaleaon-anatomy/work/inside_check.json", "w"), indent=1)
