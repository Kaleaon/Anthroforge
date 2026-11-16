import bpy, json
try:
    bpy.ops.wm.open_mainfile(filepath="/home/hatch/workspace/bodies-3d/parts-library/sketchfab/cougar-galileogb/source/FemaleCougar_ForSale.blend")
except RuntimeError as e:
    print("load warning:", e)
out=[]
for ob in bpy.data.objects:
    d={"name":ob.name,"type":ob.type}
    if ob.type=='MESH':
        d["verts"]=len(ob.data.vertices); d["polys"]=len(ob.data.polygons)
        d["groups"]=[g.name for g in ob.vertex_groups]
        d["shapekeys"]=[kb.name for kb in (ob.data.shape_keys.key_blocks if ob.data.shape_keys else [])]
        d["materials"]=[m.name if m else None for m in ob.data.materials]
        ws=[ob.matrix_world @ v.co for v in ob.data.vertices]
        if ws:
            xs=[w.x for w in ws]; ys=[w.y for w in ws]; zs=[w.z for w in ws]
            d["bbox"]={"x":[round(min(xs),3),round(max(xs),3)],"y":[round(min(ys),3),round(max(ys),3)],"z":[round(min(zs),3),round(max(zs),3)]}
    if ob.type=='ARMATURE':
        d["bones"]=[b.name for b in ob.data.bones]
    d["loc"]=[round(v,3) for v in ob.location]; d["parent"]=ob.parent.name if ob.parent else None
    out.append(d)
with open("/home/hatch/workspace/anthroforge-v2/base-head-v3/work/cougar_inspect.json","w") as f:
    json.dump(out,f,indent=1)
