"""Scripted artist repaint: rev 1 -> rev 2.

Stands in for a human paint session (this VM has no interactive
Blender session an artist can drive). Every operation below is a
named brush action with a falloff, written against the same layers a
human would paint, and logged into FURP_NOTES -- the converter cannot
tell the difference, which is the point of the exercise.

Ops:
  1. mane_grow    FURP_length/density up along ruff+spine
  2. shave_patch  FURP_density -> ~0, disc on the character's left shoulder
  3. chest_comb   FURP_direction rotated -65 deg on the chest, lift lowered
  4. zone_silver  FURP_zone_*: silvered belly, cream ruff tips

Run: blender -b --python apply_repaint.py
"""
import sys
from pathlib import Path

import bpy
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import furp_common as fc  # noqa: E402

SRC = str(HERE / "fur_paintable_rev1.blend")
OUT = str(HERE / "fur_paintable_rev2.blend")

bpy.ops.wm.open_mainfile(filepath=SRC)
ob = bpy.data.objects["BaraWolfBody"]
me = ob.data
N = len(me.vertices)

pos, nrm, tan, bit, tris = fc.mesh_arrays(ob)
reg = {r: fc.read_group(ob, "FUR_" + r, N) for r in fc.REGION_ORDER}
density = fc.read_group(ob, "FURP_density", N)
length = fc.read_group(ob, "FURP_length", N)
clump = fc.read_group(ob, "FURP_clump", N)
dir_rgba = fc.read_color_attr(me, "FURP_direction", N)
root_rgba = fc.read_color_attr(me, "FURP_zone_root", N)
tip_rgba = fc.read_color_attr(me, "FURP_zone_tip", N)
d, lift = fc.decode_direction(dir_rgba, tan, bit)
z = pos[:, 2]

# ---- 1. mane_grow ------------------------------------------------------
w = np.maximum(reg["ruff"], reg["back"]) * fc.ss(0.80, 1.05, z)
length = fc.clamp01(length + 0.38 * w)
density = fc.clamp01(density + 0.18 * w)
clump = fc.clamp01(clump + 0.10 * w)

# ---- 2. shave_patch ----------------------------------------------------
C = np.array([0.33, 0.0, 1.42])          # left shoulder (character faces -Y)
dist = np.linalg.norm(pos - C[None, :], axis=1)
fall = 1.0 - fc.ss(0.09, 0.15, dist)
density = density * (1.0 - 0.97 * fall)
print(f"shave_patch: {int((fall > 0.5).sum())} verts in patch core, "
      f"min density now {density[fall > 0.5].min() if (fall > 0.5).any() else -1:.3f}")

# ---- 3. chest_comb -----------------------------------------------------
w = fc.clamp01(reg["belly"] + 0.6 * reg["bodyhair"])
ang = np.radians(-65.0) * w
ca, sa = np.cos(ang), np.sin(ang)
# Rodrigues rotation of d around each vertex normal
d_rot = (d * ca[:, None]
         + np.cross(nrm, d) * sa[:, None]
         + nrm * (np.einsum("ij,ij->i", nrm, d) * (1.0 - ca))[:, None])
ln = np.linalg.norm(d_rot, axis=1, keepdims=True)
d = d_rot / np.maximum(ln, 1e-12)
lift = lift * (1.0 - w) + 0.16 * w  # settle toward 0.16 inside the mask

# ---- 4. zone_silver ----------------------------------------------------
wb = fc.clamp01(reg["belly"] * 1.4)
root_rgba[:, :3] = (root_rgba[:, :3] * (1.0 - 0.85 * wb[:, None])
                    + np.array([0.045, 0.042, 0.038])[None, :] * (0.85 * wb[:, None]))
tip_rgba[:, :3] = (tip_rgba[:, :3] * (1.0 - 0.90 * wb[:, None])
                   + np.array([0.52, 0.52, 0.50])[None, :] * (0.90 * wb[:, None]))
wr = fc.clamp01(reg["ruff"] * 1.3)
tip_rgba[:, :3] = (tip_rgba[:, :3] * (1.0 - 0.85 * wr[:, None])
                   + np.array([0.60, 0.53, 0.40])[None, :] * (0.85 * wr[:, None]))

# ---- write back ---------------------------------------------------------
fc.write_group(ob, "FURP_density", density)
fc.write_group(ob, "FURP_length", length)
fc.write_group(ob, "FURP_clump", clump)
fc.write_color_attr(me, "FURP_direction", fc.encode_direction(d, lift, tan, bit))
fc.write_color_attr(me, "FURP_zone_root", root_rgba)
fc.write_color_attr(me, "FURP_zone_tip", tip_rgba)
viz = np.zeros((N, 4))
viz[:, 0] = density
viz[:, 1] = 0.15
viz[:, 2] = 1.0 - density
viz[:, 3] = 1.0
fc.write_color_attr(me, "FURP_viz", viz)

me["FURP_revision"] = 2
me["FURP_author"] = "scripted-repaint (artist-session stand-in)"
txt = bpy.data.texts["FURP_NOTES"]
txt.write(
    "  rev 2  repaint: mane_grow (length/density, ruff+spine), "
    "shave_patch (density->0, L shoulder),\n"
    "         chest_comb (direction -65 deg, lift->0.16, chest), "
    "zone_silver (belly silvered, ruff tips cream)\n"
)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("repaint stats: length mean", round(float(length.mean()), 3),
      "| density mean", round(float(density.mean()), 3),
      "| lift chest mean", round(float(lift[reg['belly'] > 0.4].mean()), 3))
print("SAVED", OUT)
