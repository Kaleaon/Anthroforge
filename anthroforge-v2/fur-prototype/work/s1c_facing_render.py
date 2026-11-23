import bpy
from mathutils import Vector

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.open_mainfile(filepath="/home/hatch/workspace/anthroforge-v2/fur-prototype/work/fur_stage1.blend")
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
sc.cycles.samples = 16
sc.cycles.use_denoising = False
sc.cycles.device = 'CPU'
sc.render.resolution_x = 420
sc.render.resolution_y = 520

sun_data = bpy.data.lights.new("Sun", 'SUN')
sun_data.energy = 3.0
sun = bpy.data.objects.new("Sun", sun_data)
sc.collection.objects.link(sun)
sun.rotation_euler = (0.9, 0.2, 0.4)
sc.world = bpy.data.worlds.new("W")
sc.world.node_tree.nodes["Background"].inputs[0].default_value = (0.04, 0.04, 0.05, 1)
sc.world.node_tree.nodes["Background"].inputs[1].default_value = 1.0

cam_data = bpy.data.cameras.new("C")
cam = bpy.data.objects.new("C", cam_data)
sc.collection.objects.link(cam)
sc.camera = cam
target = Vector((0, 0, 1.25))

for name, pos in (("plusY", Vector((0.0, 3.4, 1.35))), ("minusY", Vector((0.0, -3.4, 1.35)))):
    cam.location = pos
    d = target - pos
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f"/home/hatch/workspace/anthroforge-v2/fur-prototype/work/face_{name}.png"
    bpy.ops.render.render(write_still=True)
    print("RENDERED", name, flush=True)
