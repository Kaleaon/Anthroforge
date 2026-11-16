import bpy, math
from mathutils import Vector

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath="/home/hatch/workspace/anthroforge-v2/autoskin-prototype/work/bust/scene.gltf")

scene = bpy.context.scene
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'RANDOM'
scene.render.resolution_x = 480; scene.render.resolution_y = 480
scene.render.film_transparent = False
world = bpy.data.worlds.new('W') if not bpy.data.worlds else bpy.data.worlds[0]
scene.world = world; world.color = (0.05,0.05,0.05)

cam_data = bpy.data.cameras.new('c'); cam = bpy.data.objects.new('c', cam_data)
scene.collection.objects.link(cam); scene.camera = cam
target = Vector((0, -0.2, -0.6))
views = {
 'front': Vector((0, -11, -0.4)),
 'side':  Vector((11, -0.2, -0.4)),
 'top':   Vector((0, -0.2, 9)),
 'back':  Vector((0, 11, -0.4)),
}
for name, pos in views.items():
    cam.location = pos
    d = target - pos
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = f"/home/hatch/workspace/anthroforge-v2/autoskin-prototype/work/rest_{name}.png"
    bpy.ops.render.render(write_still=True)
print("done")
