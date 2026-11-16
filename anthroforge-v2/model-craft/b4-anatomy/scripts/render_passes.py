#!/usr/bin/env python3
"""Render each demo pass with Cycles (headless; Workbench/Eevee abort
on this VM for lack of libEGL). Run:
  blender -b --python render_passes.py
Fixed camera/light/material across passes so only the sculpt changes."""
import math
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "work"
REND = ROOT / "renders"
REND.mkdir(exist_ok=True)

def look_at(obj, target):
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()

def setup():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.samples = 48
    sc.cycles.device = "CPU"
    sc.render.resolution_x = 460
    sc.render.resolution_y = 580
    sc.render.film_transparent = False
    sc.world = bpy.data.worlds.new("W")
    sc.world.use_nodes = True
    sc.world.node_tree.nodes["Background"].inputs[0].default_value = (0.16, 0.16, 0.17, 1)
    sc.world.node_tree.nodes["Background"].inputs[1].default_value = 0.7
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
    sc.collection.objects.link(cam)
    cam.location = (1.02, 1.72, 1.06)
    look_at(cam, (0, 0, 0.66))
    sc.camera = cam
    for loc, energy, size in (((1.6, 1.8, 2.4), 900, 2.0), ((-1.8, 0.6, 1.2), 260, 2.5)):
        ld = bpy.data.lights.new("L", "AREA")
        ld.energy = energy; ld.shape = "DISK"; ld.size = size
        lo = bpy.data.objects.new("L", ld)
        lo.location = loc
        sc.collection.objects.link(lo)
        look_at(lo, (0, 0, 0.66))
    mat = bpy.data.materials.new("Clay")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.62, 0.58, 0.55, 1)
    bsdf.inputs["Roughness"].default_value = 0.62
    return mat

MAT = setup()
for name in ("pass4",):
    for ob in list(bpy.context.scene.objects):
        if ob.type == "MESH":
            bpy.data.objects.remove(ob, do_unlink=True)
    bpy.ops.wm.obj_import(filepath=str(WORK / f"{name}.obj"))
    ob = bpy.context.active_object
    ob.data.materials.append(MAT)
    if name != "pass0_blockout":
        for poly in ob.data.polygons:
            poly.use_smooth = True
    bpy.context.scene.render.filepath = str(REND / f"{name}.png")
    bpy.ops.render.render(write_still=True)
    print("rendered", name)
print("done")
