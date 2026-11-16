import bpy, json
from collections import Counter

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath='/home/hatch/workspace/bodies-3d/parts-library/sketchfab/border-collie-scientist-akm/border_collie_scientist.glb')

out = {"meshes": {}}
for ob in list(bpy.data.objects):
    if ob.type!='MESH' or len(ob.vertex_groups)==0: continue
    me = ob.data
    ntris_before = len(me.polygons)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.tris_convert_to_quads(face_threshold=1.15, shape_threshold=1.15)
    bpy.ops.object.mode_set(mode='OBJECT')
    ob.select_set(False)
    me = ob.data
    hist = Counter(len(p.vertices) for p in me.polygons)
    edges = set()
    for p in me.polygons:
        vs = list(p.vertices)
        for i in range(len(vs)):
            a,b = vs[i], vs[(i+1)%len(vs)]
            edges.add((min(a,b),max(a,b)))
    valence = Counter()
    for a,b in edges: valence[a]+=1; valence[b]+=1
    mw = ob.matrix_world
    pos = []
    for v in me.vertices:
        w = mw @ v.co; pos.append([w.x,w.y,w.z])
    out["meshes"][ob.name] = {"verts": len(pos), "tris_before": ntris_before,
        "face_hist_after": {str(k):v for k,v in hist.items()},
        "valence": [valence[i] for i in range(len(pos))], "positions": pos}
    print(f"MESH {ob.name}: tris_before={ntris_before} after={dict(hist)}")

json.dump(out, open('/home/hatch/workspace/anthroforge-v2/model-craft/b1-topology/work/quad_dump.json','w'))
print("QUAD DUMPED")
