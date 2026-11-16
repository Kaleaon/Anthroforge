import bpy, sys
from collections import Counter

def report(tag):
    print(f"===== {tag} =====")
    for ob in bpy.data.objects:
        if ob.type == 'MESH':
            me = ob.data
            hist = Counter(len(p.vertices) for p in me.polygons)
            print(f"MESH {ob.name}: verts={len(me.vertices)} polys={len(me.polygons)} hist={dict(hist)} vgroups={len(ob.vertex_groups)}")
        elif ob.type == 'ARMATURE':
            print(f"ARMATURE {ob.name}: bones={len(ob.data.bones)}")

mode = sys.argv[sys.argv.index('--')+1]
if mode == 'glb':
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath='/home/hatch/workspace/bodies-3d/parts-library/sketchfab/border-collie-scientist-akm/border_collie_scientist.glb')
    report('COLLIE GLB')
else:
    bpy.ops.wm.open_mainfile(filepath='/home/hatch/workspace/stick-figure-avatar/furry/bara_wolf_avatar.blend')
    report('BARA WOLF BLEND')
