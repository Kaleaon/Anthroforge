#!/usr/bin/env python3
"""SEN stage 2 fix - curtain bake re-run (stage D of
build_cards_renders.py with TWO repairs, both measured).

The first bake rendered nothing: the shipped fur_card_texture_sen.png
measured alpha mean 0.000 / RGB mean 0.000 (PIL census, 2026-11-13).
Diagnosis with world_to_camera_view found two independent defects,
either sufficient to empty the bake:
  1. The scripted camera rotation (pi/2, 0, pi) faces the camera -Y
     (forward measured (0,-1,0)); the curtain sits at +Y. FIX 2 drops
     the pi: forward (0,+1,0), up +Z.
  2. The curtain's 75-degree tilt pivoted on the world origin (verts
     authored at y=5.0 in mesh space), throwing the plane to about
     (0, 0, 5.2), NDC y ~3.0. FIX 1 centres the verts on the plane
     centre (0, 5.0, 1.35) and locates the object there.
Everything else - plane size, 800 parents, hair length 0.42, the
Hair_coat material slot, 512x1024 @ 24 spp, transparent film - is
exactly as scripted. The blend is NOT saved.
"""
import json, math, random
from pathlib import Path
import numpy as np
import bpy
from mathutils import Vector

SEN = Path(__file__).resolve().parent.parent
bpy.ops.wm.open_mainfile(filepath=str(SEN / "sen_build.blend"))
sc = bpy.context.scene
FRONT = int(sc["af_front"]); CUT_Z = float(sc["af_cut_z"])
cut_z = CUT_Z
body = bpy.data.objects["SenBody"]
random.seed(11)

# ------------------------------------------------------------ stage D
# curtain bake for the card alpha texture (Sen's own hair, dark coat)
cur = bpy.data.objects.new("Curtain",
                           bpy.data.meshes.new("CurtainMesh"))
bpy.context.scene.collection.objects.link(cur)
cur.location = (0, 5.0, 1.35)  # FIX 1
import bmesh as _bm
bm2 = _bm.new()
bm2.from_mesh(cur.data)
# FIX 1 (pivot): verts centred on the plane centre (0, 5.0, 1.35) and
# the object located there below, so the scripted 75 deg tilt pivots
# in place. As written, the tilt pivoted on the world origin and threw
# the curtain to about (0, 0, 5.2).
vs = [bm2.verts.new(v) for v in ((-0.15, 0.0, 0.25), (0.15, 0.0, 0.25),
                                 (0.15, 0.0, -0.25), (-0.15, 0.0, -0.25))]
bm2.faces.new(vs)
bm2.to_mesh(cur.data)
bm2.free()
vg = cur.vertex_groups.new(name="all")
vg.add(list(range(len(cur.data.vertices))), 1.0, "REPLACE")
mat_clear = bpy.data.materials.new("Clear")
mat_clear.node_tree.nodes.remove(
    mat_clear.node_tree.nodes["Principled BSDF"])
tr = mat_clear.node_tree.nodes.new("ShaderNodeBsdfTransparent")
mat_clear.node_tree.links.new(
    tr.outputs["BSDF"],
    mat_clear.node_tree.nodes["Material Output"].inputs["Surface"])
cur.data.materials.append(mat_clear)                    # slot 1: faces
cur.data.materials.append(bpy.data.materials["Hair_coat"])  # slot 2: hair
cur.rotation_euler = (math.radians(75), 0, 0)  # strands read as streaks
ps = cur.modifiers.new("curtain", "PARTICLE_SYSTEM").particle_system
st = ps.settings
st.type = "HAIR"
st.count = 800
st.hair_length = 0.42
st.use_advanced_hair = True
st.child_type = "INTERPOLATED"
st.rendered_child_count = 4
st.child_percent = 50
ps.vertex_group_density = "all"
st.material = 2
st.emit_from = "FACE"

scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.samples = 24
scene.render.resolution_x = 512
scene.render.resolution_y = 1024
scene.render.film_transparent = True
scene.render.image_settings.file_format = "PNG"
cam_d = bpy.data.cameras.new("TCam")
tcam = bpy.data.objects.new("TCam", cam_d)
scene.collection.objects.link(tcam)
tcam.location = (0, 3.6, 1.35)
tcam.rotation_euler = (math.pi / 2, 0, 0)  # FIX 2: scripted (pi/2, 0, pi) faces the camera -Y (measured forward (0,-1,0)); the curtain sits at +Y. Dropping the pi gives forward (0,+1,0), up +Z.
scene.camera = tcam
sun_d = bpy.data.lights.new("Sun", "SUN")
sun_d.energy = 3.0
sun = bpy.data.objects.new("Sun", sun_d)
scene.collection.objects.link(sun)
sun.rotation_euler = (0.9, 0.2, 0.6)
# only curtain visible for this render
for o in bpy.data.objects:
    o.hide_render = o not in (cur, tcam, sun)
scene.render.filepath = str(SEN / "fur_card_texture_sen.png")
bpy.ops.render.render(write_still=True)
for o in bpy.data.objects:
    o.hide_render = False
bpy.data.objects.remove(cur, do_unlink=True)
print("card texture baked")
