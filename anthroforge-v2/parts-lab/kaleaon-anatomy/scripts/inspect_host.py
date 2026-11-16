import bpy, json, sys, bmesh
from mathutils import Vector

def mesh_volume(me):
    bm = bmesh.new(); bm.from_mesh(me)
    v = bm.calc_volume(); bm.free()
    return v

bpy.ops.wm.open_mainfile(filepath="/home/hatch/workspace/bodies-3d/kaleaon-sacdrape/kaleaon_sacdrape.blend")

out = {"objects": [], "armatures": []}
for ob in bpy.data.objects:
    info = {"name": ob.name, "type": ob.type}
    if ob.type == 'MESH':
        info["verts"] = len(ob.data.vertices)
        info["polys"] = len(ob.data.polygons)
        info["shape_keys"] = [kb.name for kb in ob.data.shape_keys.key_blocks] if ob.data.shape_keys else []
        info["vgroups"] = [g.name for g in ob.vertex_groups]
        info["parent"] = ob.parent.name if ob.parent else None
        deps = bpy.context.evaluated_depsgraph_get()
        ev = ob.evaluated_get(deps)
        bb = [ev.matrix_world @ Vector(c) for c in ev.bound_box]
        info["bbox_min"] = [round(min(v[i] for v in bb), 4) for i in range(3)]
        info["bbox_max"] = [round(max(v[i] for v in bb), 4) for i in range(3)]
        try:
            info["volume_m3"] = round(mesh_volume(ev.data), 5)
        except Exception as e:
            info["volume_m3"] = f"ERR {e}"
    if ob.type == 'ARMATURE':
        info["bones"] = [b.name for b in ob.data.bones]
        out["armatures"].append(info)
    out["objects"].append(info)

with open("/home/hatch/workspace/anthroforge-v2/parts-lab/kaleaon-anatomy/work/host_inspect.json", "w") as f:
    json.dump(out, f, indent=1)
print("WROTE host_inspect.json")
