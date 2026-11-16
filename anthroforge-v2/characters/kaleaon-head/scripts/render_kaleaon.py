#!/usr/bin/env python3
"""Clay renders for the Kaleaon head: front / three-quarter / profile
+ jaw-open three-quarter (-25 deg). Cycles CPU, flat studio world,
two-tone clay (face clay + slightly darker mane clay so the authored
masses read). Does not save the blend."""
import math
import os

import bpy
from mathutils import Vector

CHAR = "/home/hatch/workspace/anthroforge-v2/characters/kaleaon-head"
bpy.ops.wm.open_mainfile(filepath=CHAR + "/kaleaon_head.blend")
REF = ["Skull", "SkullMandible", "Muscles"]
O = {o.name: o for o in bpy.data.objects}
FINAL = [n for n, o in O.items() if o.type == "MESH" and n not in REF]
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.samples = 32
scene.cycles.use_denoising = True
scene.cycles.device = "CPU"
scene.render.resolution_x = 950
scene.render.resolution_y = 950
world = bpy.data.worlds.new("W")
scene.world = world
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.16, 0.16, 0.17, 1.0)
bg.inputs["Strength"].default_value = 1.15


def sun(name, rot, energy, color=(1, 1, 1)):
    d = bpy.data.lights.new(name, "SUN")
    d.energy = energy
    d.color = color
    o = bpy.data.objects.new(name, d)
    o.rotation_euler = rot
    scene.collection.objects.link(o)


sun("KeySun", (math.radians(55), math.radians(10), math.radians(35)), 3.2)
sun("FillSun", (math.radians(70), math.radians(-15), math.radians(-120)),
    1.1, (0.9, 0.95, 1.0))
sun("BackSun", (math.radians(100), math.radians(20), math.radians(160)),
    1.6, (1.0, 0.98, 0.92))
# Up-fill: the mane is an open shell (groom under-structure); without a
# bounce the interior reads as black slots through the face opening.
sun("UpFill", (math.radians(160), math.radians(0), math.radians(20)),
    0.55, (0.95, 0.97, 1.0))


def claymat(rgb):
    m = bpy.data.materials.new("Clay")
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*rgb, 1)
    bsdf.inputs["Roughness"].default_value = 0.62
    return m


clay = claymat((0.72, 0.70, 0.68))
mane_clay = claymat((0.52, 0.50, 0.49))
MANE_PARTS = {"ManeShell", "CheekTuft_L", "CheekTuft_R", "ChinTuft",
              "CrestStrip"}
for n in FINAL:
    o = O[n]
    o.hide_render = False
    o.data.materials.clear()
    o.data.materials.append(mane_clay if n in MANE_PARTS else clay)
for n in REF:
    if n in O:
        O[n].hide_render = True

cam_data = bpy.data.cameras.new("Cam")
cam_data.lens = 82
cam = bpy.data.objects.new("Cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam


def look_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def shoot(name, pos, target):
    cam.location = pos
    look_at(cam, target)
    scene.render.filepath = os.path.join(CHAR, "renders", name)
    bpy.ops.render.render(write_still=True)


JAW_TRAIN = ["Jaw", "TeethLower", "Tongue", "SkullMandible"]


def pose_jaw(deg):
    for n in JAW_TRAIN:
        O[n].rotation_euler = (math.radians(deg), 0, 0)
    bpy.context.view_layer.update()


def unpose():
    for n in JAW_TRAIN:
        O[n].rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()


T = Vector((0, -0.05, 0.05))
shoot("head_front.png", Vector((0, 2.2, 0.12)), T)
shoot("head_threequarter.png", Vector((1.45, 1.55, 0.68)), T)
shoot("head_profile.png", Vector((2.2, -0.05, 0.08)), T)
pose_jaw(-25)
shoot("head_jawopen_threequarter.png", Vector((1.45, 1.55, 0.68)), T)
unpose()
print("KALEAON RENDERS DONE", len(FINAL))
