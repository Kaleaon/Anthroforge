import bpy, sys
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=sys.argv[sys.argv.index("--")+1])
print("ACTIONS:", [(a.name, tuple(round(v) for v in a.frame_range)) for a in bpy.data.actions])
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
print("ARM:", arm.name, "world identity:", arm.matrix_world == bpy.data.objects[0].matrix_world if bpy.data.objects else "")
for n in ("Hips_01","Spine_02","Chest_001_03","Chest_06","Neck_07","Head_08","Shouder_L_020","Left leg_068","Foot1_L_070"):
    b = arm.data.bones.get(n)
    if b: print(f"  {n}: parent={b.parent.name if b.parent else None}")
print("meshes:", [(o.name, o.parent.name if o.parent else None) for o in bpy.data.objects if o.type=='MESH'])
print("fps:", bpy.context.scene.render.fps, bpy.context.scene.render.fps_base)
