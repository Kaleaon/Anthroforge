import bpy, json
bpy.ops.wm.open_mainfile(filepath="/home/hatch/workspace/anthroforge-v2/base-head-v2/neutral_base_head_v2.blend")
out={}
for ob in bpy.data.objects:
    if ob.type=='MESH':
        vs=[ob.matrix_world @ v.co for v in ob.data.vertices]
        out[ob.name]={"verts":len(vs),
          "bbox":[[round(min(v[i] for v in vs),3),round(max(v[i] for v in vs),3)] for i in range(3)],
          "centre":[round(sum(v[i] for v in vs)/len(vs),3) for i in range(3)],
          "mats":[m.name if m else None for m in ob.data.materials]}
print(json.dumps(out,indent=1))
