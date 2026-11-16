import bpy, sys, os
from mathutils import Vector

def clean():
    bpy.ops.wm.read_factory_settings(use_empty=True)

for path in sys.argv[sys.argv.index("--")+1:]:
    clean()
    bpy.ops.import_scene.gltf(filepath=path)
    print("="*70)
    print("FILE:", os.path.basename(path))
    for ob in bpy.data.objects:
        if ob.type == 'ARMATURE':
            print(f" ARMATURE {ob.name}: {len(ob.data.bones)} bones, scale={tuple(round(s,3) for s in ob.scale)}")
            tot = 0.0
            for b in ob.data.bones:
                L = (b.tail_local - b.head_local).length
                tot += L
            print(f"  total bone length (local): {tot:.3f}")
            for b in ob.data.bones:
                L = (b.tail_local - b.head_local).length
                print(f"   {b.name:35s} len={L:.3f} head={tuple(round(v,3) for v in b.head_local)}")
    for a in bpy.data.actions:
        print(f" ACTION {a.name}: frames {a.frame_range[0]:.0f}-{a.frame_range[1]:.0f}")
    print(" meshes:", [o.name for o in bpy.data.objects if o.type=='MESH'])
