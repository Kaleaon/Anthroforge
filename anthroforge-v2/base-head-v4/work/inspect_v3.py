import bpy, json
bpy.ops.wm.open_mainfile(filepath="/home/hatch/workspace/anthroforge-v2/base-head-v3/neutral_base_head_v3.blend")
out=[]
for ob in bpy.data.objects:
    d={"name":ob.name,"type":ob.type,"loc":[round(v,4) for v in ob.location],"rot":[round(v,4) for v in ob.rotation_euler],"parent":ob.parent.name if ob.parent else None}
    if ob.type=='MESH':
        m=ob.data
        d["verts"]=len(m.vertices); d["polys"]=len(m.polygons); d["edges"]=len(m.edges)
        d["vgroups"]=[g.name for g in ob.vertex_groups]
        d["materials"]=[s.material.name if s and s.material else None for s in ob.material_slots]
        d["modifiers"]=[(md.name,md.type) for md in ob.modifiers]
        ws=[ob.matrix_world @ v.co for v in m.vertices]
        if ws:
            d["bbox_min"]=[round(min(v[i] for v in ws),3) for i in range(3)]
            d["bbox_max"]=[round(max(v[i] for v in ws),3) for i in range(3)]
    out.append(d)
print("INSPECT_JSON_BEGIN")
print(json.dumps(out,indent=1))
print("INSPECT_JSON_END")
