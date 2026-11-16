import bpy, sys

argv = sys.argv[sys.argv.index("--") + 1:]
mode, path = argv[0], argv[1]

bpy.ops.wm.read_factory_settings(use_empty=True)

try:
    if mode == "blend":
        bpy.ops.wm.open_mainfile(filepath=path)
    elif mode == "gltf":
        bpy.ops.import_scene.gltf(filepath=path)
    elif mode == "fbx":
        bpy.ops.import_scene.fbx(filepath=path)
except Exception as e:
    print("LOAD_ERROR:", repr(e))

print("=== PROBE", path)
for ob in bpy.data.objects:
    info = f"OBJ {ob.type:10s} {ob.name}"
    if ob.type == 'MESH':
        me = ob.data
        info += f" verts={len(me.vertices)} polys={len(me.polygons)} mats={len(me.materials)} vgroups={len(ob.vertex_groups)} shapekeys={len(me.shape_keys.key_blocks) if me.shape_keys else 0}"
        info += f" dims={tuple(round(d,3) for d in ob.dimensions)}"
    if ob.type == 'ARMATURE':
        info += f" bones={len(ob.data.bones)}"
    print(info)
print("=== END")
