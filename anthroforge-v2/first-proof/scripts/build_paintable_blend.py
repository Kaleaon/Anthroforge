#!/usr/bin/env python3
"""Build the paintable mobility deliverable: the hm08 base mesh carrying
the belly mobility field as real Blender paint targets --

  vertex groups   AF_mobility (paint this: flesh freedom per vertex)
                  AF_anchor   (1 - mobility inside the mask)
  colour layer    mobility_viz (heat ramp of the same field)
  shape keys      Basis / protrusion_v1 / sag_component / protrusion_v2
  text block      MOBILITY_NOTES (brush semantics for the app)

Canonical (x right, y forward, z up) -> Blender via rotation (-x, -y, z):
a proper rotation (det +1), canonical front (+Y) lands on Blender -Y.

Run: HOME=/tmp/af_home xvfb-run -a blender -b --python build_paintable_blend.py
"""
from pathlib import Path

import bpy
import numpy as np

HERE = Path(__file__).resolve().parent.parent
WORK = HERE / "work"

corr = np.load(WORK / "correspondence.npz")
v2 = np.load(WORK / "belly_v2.npz")
import zipfile
with zipfile.ZipFile("/home/hatch/workspace/stick-figure-avatar/photoreal/tools/mpfb2.zip") as z:
    lines = z.read("mpfb/data/3dobjs/base.obj").decode().splitlines()
o = np.array([[float(x) for x in l.split()[1:4]] for l in lines if l.startswith("v ")])
base_can = np.stack([o[:, 0], o[:, 2], o[:, 1]], axis=1) * 0.1   # canonical m
tris = corr["mh_tris"].astype(np.int64)
D1 = corr["mh_delta_canonical_m"]
mask = corr["mh_mask"]
mob = v2["mobility"]
sag = v2["sag_canonical_m"]
D2 = v2["delta_v2_canonical_m"]


def to_blender(P):
    return np.stack([-P[:, 0], -P[:, 1], P[:, 2]], axis=1)


bpy.ops.wm.read_factory_settings(use_empty=True)
mesh = bpy.data.meshes.new("hm08_base")
mesh.from_pydata([tuple(p) for p in to_blender(base_can)], [],
                 [tuple(f) for f in tris])
mesh.update()
obj = bpy.data.objects.new("hm08_belly_paintable", mesh)
bpy.context.collection.objects.link(obj)
bpy.context.view_layer.objects.active = obj

g_mob = obj.vertex_groups.new(name="AF_mobility")
g_anc = obj.vertex_groups.new(name="AF_anchor")
for i in np.where(mob > 0.0)[0]:
    g_mob.add([int(i)], float(mob[i]), "REPLACE")
for i in np.where(mask > 0.003)[0]:
    g_anc.add([int(i)], float(1.0 - mob[i]), "REPLACE")

ca = mesh.color_attributes.new(name="mobility_viz", type="FLOAT_COLOR", domain="POINT")
cols = np.zeros((len(base_can), 4), dtype=np.float32)
cols[:, 0] = mob
cols[:, 1] = 0.15
cols[:, 2] = 1.0 - mob
cols[:, 3] = 1.0
ca.data.foreach_set("color", cols.ravel().tolist())

obj.shape_key_add(name="Basis")
for name, D in [("protrusion_v1", D1), ("sag_component", sag),
                ("protrusion_v2", D2)]:
    sk = obj.shape_key_add(name=name)
    tgt = to_blender(base_can + D)
    co = np.empty(len(base_can) * 3, dtype=np.float32)
    co[:] = tgt.ravel()
    sk.data.foreach_set("co", co.tolist())
    sk.value = 0.0
mesh.shape_keys.key_blocks["protrusion_v2"].value = 1.0

txt = bpy.data.texts.new("MOBILITY_NOTES")
txt.write(
    "AF mobility field -- belly protrusion (hm08 instance)\n"
    "====================================================\n"
    "AF_mobility : per-vertex flesh freedom, 0 = anchored to skeleton\n"
    "  (ribcage brim, spine, pelvis brim), 1 = fully mobile tissue.\n"
    "  Paint it in Weight Paint mode (or Vertex Paint via mobility_viz).\n"
    "  Brush semantics for the app: PAINT MOBILITY raises local sag\n"
    "  response; PAINT ANCHOR (AF_anchor) pins tissue; SMOOTH and\n"
    "  FLOOD FILL operate on the field as a whole.\n"
    "AF_anchor : 1 - mobility inside the morph mask (the complement).\n"
    "mobility_viz : heat view of AF_mobility (red = mobile, blue = fixed).\n"
    "\n"
    "Shape keys: protrusion_v1 = transferred morph (no gravity),\n"
    "sag_component = the gravity pass alone, protrusion_v2 = v1 + sag\n"
    "(the shipped +1 shape). Runtime coupling: at slider weight w the\n"
    "host applies w * protrusion_v1 + sign(w)*|w|^1.7 * sag_component.\n"
    "\n"
    "Procedural seed (before repainting): mobility = morph mask x\n"
    "angular profile x vertical profile (peak just below the navel,\n"
    "tapered at ribcage and pelvis) x tissue-mass factor, graph-\n"
    "smoothed. Max 0.90, navel 0.59 on this seed.\n")
bpy.ops.wm.save_as_mainfile(filepath=str(HERE / "body.belly.protrusion_paintable.blend"))
print("PAINTABLE BLEND SAVED")
