import bpy, json
from collections import Counter, defaultdict

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath='/home/hatch/workspace/bodies-3d/parts-library/sketchfab/border-collie-scientist-akm/border_collie_scientist.glb')

arm = next(o for o in bpy.data.objects if o.type=='ARMATURE')
bones = {}
for b in arm.data.bones:
    hw = arm.matrix_world @ b.head_local
    tw = arm.matrix_world @ b.tail_local
    bones[b.name] = {"head":[hw.x,hw.y,hw.z], "tail":[tw.x,tw.y,tw.z], "len": b.length, "parent": b.parent.name if b.parent else None}
print("BONES:", len(bones))

out = {"bones": bones, "meshes": {}}
for ob in bpy.data.objects:
    if ob.type!='MESH' or len(ob.vertex_groups)==0: continue
    me = ob.data
    mw = ob.matrix_world
    pos = []
    for v in me.vertices:
        w = mw @ v.co
        pos.append([w.x,w.y,w.z])
    edges = set()
    for p in me.polygons:
        vs = list(p.vertices)
        for i in range(len(vs)):
            a,b = vs[i], vs[(i+1)%len(vs)]
            edges.add((min(a,b),max(a,b)))
    edges = sorted(edges)
    valence = Counter()
    for a,b in edges: valence[a]+=1; valence[b]+=1
    gnames = [g.name for g in ob.vertex_groups]
    dom, blend, wcount = [], [], []
    for v in me.vertices:
        ws = sorted(((g.weight, gnames[g.group]) for g in v.groups), reverse=True)
        dom.append(ws[0][1] if ws else None)
        blend.append([n for w,n in ws if w>=0.25])
        wcount.append(sum(1 for w,_ in ws if w>0.05))
    domc = Counter(dom)
    out["meshes"][ob.name] = {
        "verts": len(pos), "tris": len(me.polygons), "edges": len(edges),
        "positions": pos, "edge_list": edges,
        "valence": [valence[i] for i in range(len(pos))],
        "dominant_bone": dom, "blend_bones": blend, "weight_count": wcount,
        "dominant_hist": domc.most_common(8),
    }
    print(f"MESH {ob.name}: verts={len(pos)} top_groups={domc.most_common(3)}")

with open('/home/hatch/workspace/anthroforge-v2/model-craft/b1-topology/work/static_dump.json','w') as f:
    json.dump(out, f)
print("DUMPED")
