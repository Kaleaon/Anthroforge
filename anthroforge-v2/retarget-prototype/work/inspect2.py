import bpy, sys
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=sys.argv[sys.argv.index("--")+1])
for ob in bpy.data.objects:
    if ob.type == 'ARMATURE':
        print("ARMATURE", ob.name)
        for b in ob.data.bones:
            L = (b.tail_local - b.head_local).length
            par = b.parent.name if b.parent else "-"
            print(f"  {b.name!r:30s} len={L:.3f} parent={par!r} head={tuple(round(v,3) for v in b.head_local)} tail={tuple(round(v,3) for v in b.tail_local)}")
