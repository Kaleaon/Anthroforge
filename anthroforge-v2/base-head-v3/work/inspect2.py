import bpy, json
from collections import Counter
try:
    bpy.ops.wm.open_mainfile(filepath="/home/hatch/workspace/bodies-3d/parts-library/sketchfab/cougar-galileogb/source/FemaleCougar_ForSale.blend")
except RuntimeError as e:
    print("load warning:", e)
out={}
for ob in bpy.data.objects:
    if ob.type!='MESH': continue
    d={}
    d["modifiers"]=[(m.name,m.type,getattr(m,'levels',None),getattr(m,'use_mirror_merge',None)) for m in ob.modifiers]
    # dominant vertex groups by total weight
    w=Counter()
    for v in ob.data.vertices:
        for g in v.groups:
            w[ob.vertex_groups[g.group].name]+=g.weight
    d["top_groups"]=w.most_common(8)
    # evaluated vert count
    dg=bpy.context.evaluated_depsgraph_get()
    ev=ob.evaluated_get(dg)
    d["eval_verts"]=len(ev.data.vertices)
    out[ob.name]=d
# armature head bones positions
arm=bpy.data.objects.get("Armature")
if arm:
    out["bones_head"]={b.name:{"head":list(b.head_local),"tail":list(b.tail_local)} for b in arm.data.bones if any(k in b.name for k in ("Head","Neck","Ear","Eye","Jaw"))}
with open("/home/hatch/workspace/anthroforge-v2/base-head-v3/work/cougar_inspect2.json","w") as f:
    json.dump(out,f,indent=1)
