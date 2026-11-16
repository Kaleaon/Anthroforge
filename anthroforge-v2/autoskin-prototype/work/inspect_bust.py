import bpy, sys
from mathutils import Vector

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath="/home/hatch/workspace/anthroforge-v2/autoskin-prototype/work/bust/scene.gltf")

for ob in bpy.context.scene.objects:
    if ob.type == 'MESH':
        me = ob.data
        # world bounds
        corners = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
        xs = [c.x for c in corners]; ys = [c.y for c in corners]; zs = [c.z for c in corners]
        # non-manifold check: edges not shared by exactly 2 faces
        from collections import Counter
        ec = Counter()
        for p in me.polygons:
            vs = list(p.vertices)
            for i in range(len(vs)):
                a, b = vs[i], vs[(i+1) % len(vs)]
                ec[(min(a,b), max(a,b))] += 1
        bad = sum(1 for v in ec.values() if v != 2)
        print(f"OBJ {ob.name}: verts={len(me.vertices)} faces={len(me.polygons)} "
              f"X[{min(xs):.3f},{max(xs):.3f}] Y[{min(ys):.3f},{max(ys):.3f}] Z[{min(zs):.3f},{max(zs):.3f}] "
              f"nonmanifold_edges={bad}/{len(ec)} loc={tuple(round(v,3) for v in ob.location)} scale={tuple(round(v,3) for v in ob.scale)}")
