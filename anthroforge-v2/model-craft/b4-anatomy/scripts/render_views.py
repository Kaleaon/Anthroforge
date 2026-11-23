#!/usr/bin/env python3
"""Corrected re-render of the B4 pass OBJs (finisher pass, Nov 12 2026).

The original render_passes.py renders are unusable as evidence: Blender's
OBJ importer assumes Y-up, but build_passes.py writes Z-up OBJs, so the
torso was laid on its side (length along +Y) and the fixed camera framed
a horizontal tube in the corner of the frame.

Fix applied here, and nothing else: clear the rotation the OBJ importer
stamps on the object. The importer copies the vertex data verbatim AND
sets object rotation +90 deg about X (its Y-up assumption), which tips
an already-Z-up file over onto -Y. Setting rotation to zero leaves the
verbatim data standing as written: +Z up, +Y front. Camera position,
resolution and sample count are copied from the original script. One
further change, also evidence-driven: the original light energies
(900/260 W area disks ~2.5 m away) blow the clay out to flat white, so
no surface relief is readable in any frame; key/fill are reduced to
150/45 W and the clay albedo to 0.55 so the pass relief actually reads.
Outputs go to renders/passN_view.png; the original renders are kept.

Run: blender -b --threads 2 --python render_views.py
"""
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "work"
REND = ROOT / "renders"

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
    for loc, energy, size in (((1.6, 1.8, 2.4), 150, 2.0), ((-1.8, 0.6, 1.2), 45, 2.5)):
        ld = bpy.data.lights.new("L", "AREA")
        ld.energy = energy; ld.shape = "DISK"; ld.size = size
        lo = bpy.data.objects.new("L", ld)
        lo.location = loc
        sc.collection.objects.link(lo)
        look_at(lo, (0, 0, 0.66))
    mat = bpy.data.materials.new("Clay")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.55, 0.51, 0.48, 1)
    bsdf.inputs["Roughness"].default_value = 0.62
    return mat

MAT = setup()
for name in ("pass0_blockout", "pass1", "pass2", "pass3", "pass4"):
    for ob in list(bpy.context.scene.objects):
        if ob.type == "MESH":
            bpy.data.objects.remove(ob, do_unlink=True)
    bpy.ops.wm.obj_import(filepath=str(WORK / f"{name}.obj"))
    ob = bpy.context.active_object
    # THE FIX: OBJ data is already Z-up verbatim; the importer additionally
    # stamped rotation +90 deg about X (Y-up assumption), tipping the torso
    # onto -Y. Clear it and the mesh stands as authored.
    ob.rotation_euler = (0, 0, 0)
    ob.data.materials.append(MAT)
    if name != "pass0_blockout":
        for poly in ob.data.polygons:
            poly.use_smooth = True
    bpy.context.scene.render.filepath = str(REND / f"{name}_view.png")
    bpy.ops.render.render(write_still=True)
    print("rendered", name)
print("done")
