#!/usr/bin/env python3
"""Render one view from the saved legs_digitigrade.blend.
Usage: blender -b legs_digitigrade.blend --python render_one.py -- <mode> <outfile>
mode: standing | stride ; camera chosen by outfile suffix _side/_threequarter."""
import math
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
MODE, OUT = argv[0], argv[1]

for name in ("leg_digitigrade_R", "leg_digitigrade_L"):
    o = bpy.data.objects[name]
    if not o.data.materials:
        mat = bpy.data.materials.new("leg_mat")
        b = mat.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (0.55, 0.47, 0.42, 1)
        b.inputs["Roughness"].default_value = 0.85
        o.data.materials.append(mat)

# pelvis stub (matches build script; canonical -> blender (x,-y,z))
import math as m
def uv_sphere(centre, radii, nu=20, nv=12):
    verts, faces = [], []
    for j in range(nv + 1):
        phi = m.pi * j / nv
        for i in range(nu):
            th = 2 * m.pi * i / nu
            verts.append((centre[0] + radii[0] * m.sin(phi) * m.cos(th),
                          -(centre[1] + radii[1] * m.sin(phi) * m.sin(th)),
                          centre[2] + radii[2] * m.cos(phi)))
    for j in range(nv):
        for i in range(nu):
            a = j * nu + i; b2 = j * nu + (i + 1) % nu
            c2 = (j + 1) * nu + (i + 1) % nu; d2 = (j + 1) * nu + i
            faces.append((a, b2, c2, d2))
    return verts, faces

if "pelvis_stub" not in bpy.data.objects:
    pv, pf = uv_sphere((0, 0.002, 0.875), (0.191, 0.118, 0.145))
    me = bpy.data.meshes.new("pelvis_stub")
    me.from_pydata(pv, [], pf); me.update()
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new("pelvis_stub", me)
    bpy.context.collection.objects.link(ob)
    mat = bpy.data.materials.new("stub_mat")
    bb = mat.node_tree.nodes["Principled BSDF"]
    bb.inputs["Base Color"].default_value = (0.42, 0.36, 0.33, 1)
    bb.inputs["Roughness"].default_value = 0.9
    ob.data.materials.append(mat)

bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 0, 0))
gnd = bpy.context.active_object
gm = bpy.data.materials.new("ground_mat")
gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.16, 0.16, 0.17, 1)
gnd.data.materials.append(gm)

ld = bpy.data.lights.new("sun", "SUN"); ld.energy = 3.0
lo = bpy.data.objects.new("sun", ld); bpy.context.collection.objects.link(lo)
lo.rotation_euler = (math.radians(55), 0, math.radians(35))
ld2 = bpy.data.lights.new("fill", "AREA"); ld2.energy = 250
lo2 = bpy.data.objects.new("fill", ld2); bpy.context.collection.objects.link(lo2)
lo2.location = (-1.6, -1.4, 1.2); lo2.rotation_euler = (math.radians(70), 0, math.radians(-50))

sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.samples = 32
sc.cycles.use_denoising = False
sc.render.resolution_x = 640
sc.render.resolution_y = 800
if not sc.world:
    sc.world = bpy.data.worlds.new("w")
sc.world.node_tree.nodes["Background"].inputs[0].default_value = (0.05, 0.05, 0.06, 1)
sc.world.node_tree.nodes["Background"].inputs[1].default_value = 0.6

if MODE == "stride":
    def setrot(arm_name, bone, deg):
        pb = bpy.data.objects[arm_name].pose.bones[bone]
        pb.rotation_mode = "XYZ"
        pb.rotation_euler = (math.radians(deg), 0, 0)
    setrot("DigitigradeLeg_L", "Hip_L", -24); setrot("DigitigradeLeg_L", "Knee_L", 30)
    setrot("DigitigradeLeg_L", "Ankle_L", -18); setrot("DigitigradeLeg_L", "Hock_L", -6)
    setrot("DigitigradeLeg_L", "Foot_L", 22)
    setrot("DigitigradeLeg_R", "Hip_R", 16); setrot("DigitigradeLeg_R", "Knee_R", 8)
    setrot("DigitigradeLeg_R", "Ankle_R", 12); setrot("DigitigradeLeg_R", "Hock_R", 14)
    setrot("DigitigradeLeg_R", "Foot_R", -28)
    bpy.context.view_layer.update()

side = "side" in OUT
cd = bpy.data.cameras.new("cam")
cam = bpy.data.objects.new("cam", cd)
bpy.context.collection.objects.link(cam)
cam.location = (1.7, -0.25, 0.55) if side else (1.3, -1.45, 0.72)
tgt = Vector((0, 0.02 if MODE == "stride" else 0, 0.45))
cam.rotation_euler = (tgt - Vector(cam.location)).to_track_quat("-Z", "Y").to_euler()
cd.lens = 42
sc.camera = cam
sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("RENDERED", OUT)
