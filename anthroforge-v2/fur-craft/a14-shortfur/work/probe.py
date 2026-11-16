import bpy, json
bpy.ops.wm.open_mainfile(filepath="/home/hatch/workspace/anthroforge-v2/base-head-v3/neutral_base_head_v3.blend")
info = {}
for ob in bpy.data.objects:
    d = {"type": ob.type, "loc": [round(v,3) for v in ob.location]}
    if ob.type == 'MESH':
        d["verts"] = len(ob.data.vertices)
        d["mats"] = [m.name if m else None for m in ob.data.materials]
        d["vgroups"] = [g.name for g in ob.vertex_groups]
        ws = [ob.matrix_world @ v.co for v in ob.data.vertices]
        mn = [min(w[i] for w in ws) for i in range(3)]
        mx = [max(w[i] for w in ws) for i in range(3)]
        d["bbox_min"] = [round(v,3) for v in mn]
        d["bbox_max"] = [round(v,3) for v in mx]
        d["has_uv"] = len(ob.data.uv_layers) > 0
    info[ob.name] = d
info["_engine"] = bpy.context.scene.render.engine
info["_cams"] = [o.name for o in bpy.data.objects if o.type=='CAMERA']
info["_lights"] = [(o.name, o.data.type, o.data.energy) for o in bpy.data.objects if o.type=='LIGHT']
with open("/home/hatch/workspace/anthroforge-v2/fur-craft/a14-shortfur/work/probe.json","w") as f:
    json.dump(info, f, indent=1)
