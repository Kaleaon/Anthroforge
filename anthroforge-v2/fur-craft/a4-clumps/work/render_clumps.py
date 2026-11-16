#!/usr/bin/env python3
"""Render the A4 clump demo: head three-quarter/front/side + tail set."""
import bpy, math, os
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, "parts", "fur_clumps_demo.blend"))
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
sc.cycles.samples = 28
sc.cycles.device = 'CPU'
sc.render.resolution_x = 600
sc.render.resolution_y = 600
sc.world = bpy.data.worlds.new("W") if not sc.world else sc.world
sc.world.use_nodes = True
sc.world.node_tree.nodes["Background"].inputs[0].default_value = (0.16, 0.15, 0.14, 1)
sc.world.node_tree.nodes["Background"].inputs[1].default_value = 0.85

sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN'))
sun.data.energy = 3.0
sun.rotation_euler = (math.radians(50), 0, math.radians(35))
sc.collection.objects.link(sun)
fill = bpy.data.objects.new("Fill", bpy.data.lights.new("Fill", 'AREA'))
fill.data.energy = 260
fill.data.shape = 'DISK'; fill.data.size = 1.2
fill.location = (-0.9, 0.7, 0.5)
sc.collection.objects.link(fill)

cam_data = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_data)
sc.collection.objects.link(cam)
sc.camera = cam

def look(cam_ob, pos, target):
    cam_ob.location = Vector(pos)
    d = Vector(target) - Vector(pos)
    cam_ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()

def shot(name, pos, target, lens=42):
    cam_data.lens = lens
    look(cam, pos, target)
    sc.render.filepath = os.path.join(ROOT, "renders", name)
    bpy.ops.render.render(write_still=True)
    print("RENDERED", name)

HEAD_PARTS = {'fur_cheek_tufts', 'fur_ear_tufts', 'fur_chest_ruff'}
TAIL_OBJS = {'fur_tail_clumps', 'tail_core_proxy'}
for ob in bpy.data.objects:
    if ob.name in TAIL_OBJS:
        ob.hide_render = True
shot("head_threequarter.png", (0.82, 0.86, 0.34), (0, -0.02, -0.03))
shot("head_front.png", (0, 1.45, -0.02), (0, 0, -0.04))
shot("head_side.png", (1.45, -0.05, -0.02), (0, -0.02, -0.04))
for ob in bpy.data.objects:
    ob.hide_render = ob.name not in TAIL_OBJS
shot("tail_set.png", (0.72, -1.0, 0.42), (0, -0.26, -0.01), lens=38)
print("DONE")
