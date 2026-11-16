import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.open_mainfile(filepath="/home/hatch/workspace/stick-figure-avatar/furry/bara_wolf_base.blend")
arm = bpy.data.objects["BaraWolf"]
mw = arm.matrix_world
for b in arm.data.bones:
    h = mw @ b.head_local
    t = mw @ b.tail_local
    print(f"BONE {b.name:28s} head=({h.x:+.3f},{h.y:+.3f},{h.z:+.3f}) tail=({t.x:+.3f},{t.y:+.3f},{t.z:+.3f})")
