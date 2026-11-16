#!/usr/bin/env python3
"""Head-on-body context render: the built head (L = 0.42 m) seated on
the r3 rig body, hinge exactly on CC_Base_JawRoot's pivot
(0, +0.055, 1.800). Old placeholder head objects hidden; everything
clay for a clean proportion read. Assembly: scale s = 0.42 / L_built,
rotation build (x,y,z) -> body (-x,-y,z) (rig faces -Y, its L = -X),
translation seating the build hinge on the rig pivot."""
import math
import os

import bpy
import numpy as np
from mathutils import Matrix, Vector

CHAR = "/home/hatch/workspace/anthroforge-v2/characters/kaleaon-head"
RIG = "/home/hatch/workspace/bodies-3d/kaleaon-rigged3/kaleaon_rigged3.blend"
bpy.ops.wm.open_mainfile(filepath=RIG)
HIDE = ["HEAD_UPPER", "JAW", "TEETH_UPPER", "TEETH_LOWER", "TONGUE",
        "MOUTH_INTERIOR", "LipLine", "Philtrum", "Nose_Leather",
        "Nostril_L", "Nostril_R", "Eye_Cornea_L", "Eye_Cornea_R",
        "Eye_Iris_L", "Eye_Iris_R", "Lid_L", "Lid_R", "LidLow_L",
        "LidLow_R", "Mane_Cap", "Mane_Locks", "Sideburn_L", "Sideburn_R",
        "Braid"] + [f"Glasses_{i}" for i in range(1, 8)]
for name in HIDE:
    o = bpy.data.objects.get(name)
    if o:
        o.hide_render = True
        o.hide_viewport = True

before = set(bpy.data.objects.keys())
bpy.ops.import_scene.gltf(filepath=CHAR + "/kaleaon_head.glb")
new = [o for n, o in bpy.data.objects.items()
       if n not in before and o.type == "MESH"]
print("imported head objects:", [o.name for o in new])

# measure L_built + hinge from the imported head (importer restores
# the Blender build frame)
tis = next(o for o in new if o.name.startswith("TissueHead"))
jaw = next(o for o in new if o.name == "Jaw" or o.name.startswith("Jaw."))
mw = tis.matrix_world
V = np.empty(len(tis.data.vertices) * 3)
tis.data.vertices.foreach_get("co", V)
W = np.array([mw @ Vector(v) for v in V.reshape(-1, 3)])
L_built = float(W[:, 1].max() - W[:, 1].min())
H = np.array(jaw.matrix_world.translation)
print("L_built:", L_built, "imported hinge:", H)

s = 0.42 / L_built
P = np.array([0.0, 0.055, 1.800])
R = np.diag([-1.0, -1.0, 1.0])
t = P - R @ (s * H)
T4 = Matrix.Identity(4)
for i in range(3):
    for j in range(3):
        T4[i][j] = R[i, j] * s
T4.translation = Vector(t)
for o in new:
    o.matrix_world = T4 @ o.matrix_world
bpy.context.view_layer.update()

H_after = np.array(jaw.matrix_world.translation)
print("hinge after assembly:", H_after,
      "error:", float(np.linalg.norm(H_after - P)))
# face height + head top after assembly
W2 = np.array([tis.matrix_world @ Vector(v) for v in V.reshape(-1, 3)])
tu = next(o for o in new if o.name.startswith("TeethUpper"))
Vt = np.empty(len(tu.data.vertices) * 3)
tu.data.vertices.foreach_get("co", Vt)
Wt = np.array([tu.matrix_world @ Vector(v)
               for v in Vt.reshape(-1, 3)])
pal = float(Wt[:, 2].max())
mane = next(o for o in new if o.name.startswith("ManeShell"))
Vm = np.empty(len(mane.data.vertices) * 3)
mane.data.vertices.foreach_get("co", Vm)
Wm = np.array([mane.matrix_world @ Vector(v) for v in Vm.reshape(-1, 3)])
print("face height (palate->crown, m):", float(W2[:, 2].max() - pal),
      "head top z:", float(W2[:, 2].max()),
      "mane: top z", float(Wm[:, 2].max()),
      "width m", float(Wm[:, 0].max() - Wm[:, 0].min()),
      "back y", float(Wm[:, 1].max()))

scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.samples = 32
scene.cycles.use_denoising = True
scene.cycles.device = "CPU"
scene.render.resolution_x = 900
scene.render.resolution_y = 1100
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
sun("UpFill", (math.radians(160), math.radians(0), math.radians(20)),
    0.55, (0.95, 0.97, 1.0))
clay = bpy.data.materials.new("Clay")
bsdf = clay.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.72, 0.70, 0.68, 1)
bsdf.inputs["Roughness"].default_value = 0.6
mane_clay = bpy.data.materials.new("ManeClay")
b2 = mane_clay.node_tree.nodes["Principled BSDF"]
b2.inputs["Base Color"].default_value = (0.52, 0.50, 0.49, 1)
b2.inputs["Roughness"].default_value = 0.62
MANE_PARTS = ("ManeShell", "CheekTuft", "ChinTuft", "CrestStrip")
for o in bpy.data.objects:
    if o.type == "MESH" and not o.hide_render:
        o.data.materials.clear()
        o.data.materials.append(
            mane_clay if o.name.startswith(MANE_PARTS) else clay)

cam_data = bpy.data.cameras.new("Cam")
cam_data.lens = 60
cam = bpy.data.objects.new("Cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam


def shoot(name, pos, target):
    cam.location = pos
    cam.rotation_euler = (Vector(target) - cam.location).to_track_quat(
        "-Z", "Y").to_euler()
    scene.render.filepath = os.path.join(CHAR, "renders", name)
    bpy.ops.render.render(write_still=True)


shoot("head_on_body_full.png", Vector((2.4, -3.6, 1.7)),
      Vector((0, 0, 1.12)))
shoot("head_on_body_closeup.png", Vector((0.85, -1.25, 2.1)),
      Vector((0, 0.02, 1.84)))
print("CONTEXT RENDER DONE")
