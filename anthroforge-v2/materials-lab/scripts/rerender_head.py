#!/usr/bin/env python3
"""Fix-up: re-render ONLY the head tile from the saved swatch scene —
ground dropped to the head's own floor, camera tighter and higher."""
import bpy, mathutils, os

LAB = os.path.expanduser("~/workspace/anthroforge-v2/materials-lab")
bpy.ops.wm.open_mainfile(filepath=os.path.join(LAB, "swatch_scene.blend"))
scene = bpy.context.scene

head_objs = [o for o in scene.objects if o.type == "MESH" and o.name not in ("Sphere", "Sphere.001", "Plane")]
print("HEAD OBJS:", [o.name for o in head_objs])
mins = mathutils.Vector((1e9, 1e9, 1e9)); maxs = mathutils.Vector((-1e9, -1e9, -1e9))
for o in head_objs:
    for c in o.bound_box:
        w = o.matrix_world @ mathutils.Vector(c)
        mins = mathutils.Vector(map(min, mins, w)); maxs = mathutils.Vector(map(max, maxs, w))
centre = (mins + maxs) / 2
size = max((maxs - mins).x, (maxs - mins).y, (maxs - mins).z)
print("BBOX", tuple(centre), size)

ground = scene.objects.get("Plane")
if ground:
    ground.location.z = mins.z - size * 0.02

cam = scene.camera
target = centre + mathutils.Vector((0, 0, size * 0.05))
cam.location = target + mathutils.Vector((size * 0.62, -size * 1.25, size * 0.34))
direction = target - mathutils.Vector(cam.location)
cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

scene.render.resolution_x = 640; scene.render.resolution_y = 640
scene.render.filepath = os.path.join(LAB, "renders", "head_skin_smooth.png")
bpy.ops.render.render(write_still=True)
print("HEAD RENDER DONE")
