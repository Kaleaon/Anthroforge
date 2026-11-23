"""Seed the FURP paint-map set on the bara wolf body (revision 1).

Procedural seed only -- the same authority level as the gravity
pipeline's mobility seed: anatomy rules produce a starting field that
a human then repaints (see apply_repaint.py for a scripted repaint).

Run: blender -b --python seed_paintmaps.py
Out: fur_paintable_rev1.blend next to this script.
"""
import sys
from pathlib import Path

import bpy
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import furp_common as fc  # noqa: E402

SRC = "/home/hatch/workspace/stick-figure-avatar/furry/bara_wolf_base.blend"
OUT = str(HERE / "fur_paintable_rev1.blend")

bpy.ops.wm.open_mainfile(filepath=SRC)
ob = bpy.data.objects["BaraWolfBody"]
me = ob.data
N = len(me.vertices)

pos, nrm, tan, bit, tris = fc.mesh_arrays(ob)
reg = fc.region_fields(pos, nrm)
W = np.stack([reg[r] for r in fc.REGION_ORDER])          # (5, N)
wsum = np.maximum(W.sum(axis=0), 1e-6)

# ---- scalar maps: region-weighted blends of the prototype groom table
length_map = np.zeros(N)
clump_map = np.zeros(N)
curl_map = np.zeros(N)
density_map = np.zeros(N)
for k, r in enumerate(fc.REGION_ORDER):
    p = fc.REGION_REF[r]
    length_map += W[k] * (p["length_m"] / fc.LENGTH_REF_M)
    clump_map += W[k] * p["clump"]
    curl_map += W[k] * p["curl"]
    density_map += W[k] * p["density"]
length_map = fc.clamp01(length_map / wsum)
clump_map = fc.clamp01(clump_map / wsum)
curl_map = fc.clamp01(curl_map / wsum)
density_map = fc.clamp01(density_map / wsum)
# bare muzzle + lighter paws, as in the prototype's look
density_map *= (1.0 - 0.80 * reg["muzzle"])
density_map *= np.where(pos[:, 2] < 0.30,
                        0.55 + 0.45 * fc.ss(0.05, 0.30, pos[:, 2]), 1.0)

# ---- direction: canonical slick flow; ruff stands up more
d = fc.flow_seed(pos, nrm)
lift = 0.30 + 0.25 * reg["ruff"] + 0.10 * reg["back"]
dir_rgba = fc.encode_direction(d, lift, tan, bit)

# ---- colour zones: region blends of the seed palette
root = np.zeros((N, 3))
tip = np.zeros((N, 3))
for k, r in enumerate(fc.REGION_ORDER):
    root += W[k][:, None] * np.array(fc.ZONE_SEED[r]["root"])[None, :]
    tip += W[k][:, None] * np.array(fc.ZONE_SEED[r]["tip"])[None, :]
root /= wsum[:, None]
tip /= wsum[:, None]
root_rgba = np.concatenate([root, np.ones((N, 1))], axis=1)
tip_rgba = np.concatenate([tip, np.ones((N, 1))], axis=1)

# ---- write layers
for r in fc.REGION_ORDER:
    fc.write_group(ob, "FUR_" + r, reg[r], thresh=0.01)
fc.write_group(ob, "FURP_density", density_map)
fc.write_group(ob, "FURP_length", length_map)
fc.write_group(ob, "FURP_clump", clump_map)
fc.write_group(ob, "FURP_curl", curl_map)
fc.write_color_attr(me, "FURP_direction", dir_rgba)
fc.write_color_attr(me, "FURP_zone_root", root_rgba)
fc.write_color_attr(me, "FURP_zone_tip", tip_rgba)
viz = np.zeros((N, 4))
viz[:, 0] = density_map
viz[:, 1] = 0.15
viz[:, 2] = 1.0 - density_map
viz[:, 3] = 1.0
fc.write_color_attr(me, "FURP_viz", viz)

# clay material so the paintable file renders standalone (from s2)
mat = bpy.data.materials.get("BodyClay") or bpy.data.materials.new("BodyClay")
mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.16, 0.13, 0.11, 1.0)
mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.9
if mat.name not in [m.name for m in me.materials]:
    me.materials.append(mat)

me["FURP_set_id"] = "furp.wolf.bara"
me["FURP_revision"] = 1
me["FURP_author"] = "procedural-seed"

txt = bpy.data.texts.get("FURP_NOTES") or bpy.data.texts.new("FURP_NOTES")
txt.clear()
txt.write(
    "FURP paint maps -- bara wolf (set furp.wolf.bara, rev 1, procedural seed)\n"
    "\n"
    "Paint targets (Weight Paint mode):\n"
    "  FURP_density  strand density [0,1]        (0 = bare skin)\n"
    "  FURP_length   strand length  [0,1]        (x 0.20 m reference)\n"
    "  FURP_clump    clumping       [0,1]\n"
    "  FURP_curl     curl/kink      [0,1]\n"
    "Colour layers (Vertex Paint mode):\n"
    "  FURP_direction  RG = flow in UV tangent frame, B = lift\n"
    "  FURP_zone_root / FURP_zone_tip  coat colours at root and tip\n"
    "FURP_viz is a derived heat view of density -- do not paint it.\n"
    "\n"
    "Convert to a groom:  blender -b --python fur_paint_convert.py --\n"
    "  --input <this file> --outdir out --tag rev1\n"
    "\n"
    "Edit log:\n"
    "  rev 1  procedural seed (region fields, fur prototype table)\n"
)

bpy.ops.wm.save_as_mainfile(filepath=OUT)
for name, arr in [("density", density_map), ("length", length_map),
                  ("clump", clump_map), ("curl", curl_map)]:
    print(f"FURP_{name}: mean={arr.mean():.3f} max={arr.max():.3f} "
          f"verts>0.5={int((arr > 0.5).sum())}/{N}")
print("lift mean", float(lift.mean()), "SAVED", OUT)
