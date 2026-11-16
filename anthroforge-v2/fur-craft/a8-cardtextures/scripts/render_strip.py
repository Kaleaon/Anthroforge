#!/usr/bin/env python3
"""Test strip: clumped card texture on crossed-plane clusters at 3 distances.
Run: blender -b -noaudio --python render_strip.py (Cycles; Eevee needs EGL)."""
import math
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent.parent
TEX = str(HERE / "card_clumped_diffuse.png")
NRM = str(HERE / "card_clumped_normal.png")
OUTP = str(HERE / "test_strip_raw.png")

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"
sc.display.shading.light = "STUDIO"
sc.display.shading.color_type = "TEXTURE"
sc.display.shading.show_shadows = True
sc.display.shading.show_cavity = True
sc.render.resolution_x, sc.render.resolution_y = 1500, 540
sc.render.filepath = OUTP
sc.render.film_transparent = False

# world: near-black studio
w = bpy.data.worlds.new("W"); sc.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.012, 0.012, 0.016, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 1.0


def mat_card():
    m = bpy.data.materials.new("card")
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = bpy.data.images.load(TEX)
    nrm = nt.nodes.new("ShaderNodeTexImage"); nrm.image = bpy.data.images.load(NRM)
    nrm.image.colorspace_settings.name = "Non-Color"
    nm = nt.nodes.new("ShaderNodeNormalMap"); nm.inputs[0].default_value = 0.7
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
    nt.links.new(nrm.outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Roughness"].default_value = 0.92
    m.surface_render_method = "DITHERED"
    return m


CARD_MAT = mat_card()


def cluster(x, dist, scale=1.0):
    """3 crossed planes + 1 tilted, roots on the ground, tips up."""
    import random
    random.seed(int(dist * 10))
    for i, ry in enumerate((0.0, math.pi / 3, 2 * math.pi / 3)):
        bpy.ops.mesh.primitive_plane_add(size=1, location=(x, dist, 0.17 * scale))
        o = bpy.context.active_object
        o.rotation_euler = (math.pi / 2, 0, ry)
        o.scale = (0.30 * scale, 0.34 * scale, 1)
        bpy.ops.object.transform_apply(scale=True)
        # move pivot so plane stands on ground (plane was centred at z .17)
        o.data.materials.append(CARD_MAT)
    for _ in range(3):  # filler cards, slight offsets/tilts
        bpy.ops.mesh.primitive_plane_add(
            size=1, location=(x + random.uniform(-0.13, 0.13), dist +
                              random.uniform(-0.1, 0.1), 0.15 * scale))
        o = bpy.context.active_object
        o.rotation_euler = (math.pi / 2 + random.uniform(-0.16, 0.16), 0,
                            random.uniform(0, math.pi))
        o.scale = (0.26 * scale, 0.30 * scale, 1)
        bpy.ops.object.transform_apply(scale=True)
        o.data.materials.append(CARD_MAT)


# ground + backdrop
bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 6, 0))
g = bpy.context.active_object
gm = bpy.data.materials.new("ground"); gm.use_nodes = True
gm.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0.05, 0.05, 0.06, 1)
gm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 1.0
g.data.materials.append(gm)

cluster(-1.15, 1.6)          # close
cluster(0.05, 3.4)           # mid
cluster(1.05, 6.8)           # far

bpy.ops.object.light_add(type="AREA", location=(0, 1.5, 4.2))
key = bpy.context.active_object
key.data.energy = 900; key.data.shape = "DISK"; key.data.size = 3.0
key.rotation_euler = (math.radians(38), 0, 0)
bpy.ops.object.light_add(type="POINT", location=(-3.5, 2.0, 1.6))
rim = bpy.context.active_object
rim.data.energy = 260
rim.data.color = (0.65, 0.75, 1.0)

bpy.ops.object.camera_add(location=(0, -1.4, 0.55))
cam = bpy.context.active_object
cam.rotation_euler = (math.radians(86), 0, 0)
cam.data.lens = 38
sc.camera = cam

bpy.ops.render.render(write_still=True)
print("strip rendered ->", OUTP)
