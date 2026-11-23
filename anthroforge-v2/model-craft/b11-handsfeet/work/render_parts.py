#!/usr/bin/env python3
"""Render B11 parts: bind-pose views + posed grip check.
Run: blender -b --python render_parts.py (opens parts/b11_hands_feet.blend)"""
import math
import os

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, ".."))
REND = os.path.join(OUT, "renders")

bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT, "parts", "b11_hands_feet.blend"))
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.samples = 24
scene.cycles.device = "CPU"
scene.render.resolution_x = 512
scene.render.resolution_y = 512
scene.render.film_transparent = False
world = bpy.data.worlds.new("W")
scene.world = world
world.node_tree.nodes["Background"].inputs[0].default_value = (0.35, 0.35, 0.35, 1)
world.node_tree.nodes["Background"].inputs[1].default_value = 0.7
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
sun.data.energy = 3.0
sun.rotation_euler = (math.radians(50), 0, math.radians(30))
scene.collection.objects.link(sun)

for name in ("stub_forearm", "stub_shin"):
    if name in bpy.data.objects:
        bpy.data.objects[name].hide_render = True

def look_at(ob, target):
    ob.rotation_euler = (Vector(target) - ob.location).to_track_quat("-Z", "Y").to_euler()

def shot(name, cam_pos, target, objs):
    for o in bpy.data.objects:
        if o.type in ("MESH", "ARMATURE"):
            o.hide_render = o.name not in objs
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    scene.collection.objects.link(cam)
    cam.location = cam_pos
    look_at(cam, target)
    cam.data.lens = 50
    scene.camera = cam
    scene.render.filepath = os.path.join(REND, name + ".png")
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam, do_unlink=True)
    print("RENDERED", name)

HAND = ["paw_hand_armature", "paw_hand_main", "paw_hand_pads", "paw_hand_claws"]
FOOT = ["paw_foot_armature", "paw_foot_main", "paw_foot_pads", "paw_foot_claws"]

shot("hand_dorsal", (0.02, 0.10, 0.34), (0, 0.09, 0), HAND)
shot("hand_palmar", (0.02, 0.10, -0.34), (0, 0.09, 0), HAND)
shot("foot_side", (0.36, 0.04, 0.13), (0, 0.03, 0.12), FOOT)
shot("foot_plantar", (0.16, 0.17, -0.24), (0, 0.05, 0.02), FOOT)
shot("foot_front", (0, 0.44, 0.13), (0, 0.02, 0.10), FOOT)

# ---- posed grip: flex finger chains, render side view
arm = bpy.data.objects["paw_hand_armature"]
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode="POSE")
flex = {"1": -0.45, "2": -0.65, "3": -0.55}
for pb in arm.pose.bones:
    for suf, ang in flex.items():
        if pb.name.endswith(suf + "_R") and not pb.name.startswith(("Toe", "Dew")):
            pb.rotation_mode = "XYZ"
            pb.rotation_euler.x = ang
    if pb.name.startswith("Thumb"):
        pb.rotation_mode = "XYZ"
        pb.rotation_euler.x = -0.35
bpy.ops.object.mode_set(mode="OBJECT")
shot("hand_grip_pose", (0.36, 0.09, 0.03), (0, 0.09, -0.01), HAND)
print("RENDERS DONE")
