#!/usr/bin/env python3
"""Blender end-to-end for belly v4 (whole-torso adiposity system).

Loads the combined v4 target (plus v3 for the record) on a default-macro
MPFB human, measures the navel displacement vector on the evaluated
mesh, flip-checks the belly region at +1, and renders: v4 profile at
+0.5 (coupled) and +1, v4 FRONT at +1, v4 THREE-QUARTER at +1. The
profile camera/lighting are the v1-v3 proofs' exact setup so the v4
profile composites directly against renders/belly_v3_w+1.0_profile.png.

Run: HOME=/tmp/af_home xvfb-run blender -b --python test_belly_v4.py
"""
import json
import math
from pathlib import Path

import bpy
import numpy as np

HERE = Path(__file__).resolve().parent.parent
WORK = HERE / "work"
RENDERS = HERE / "renders"
MPFB_ZIP = Path("/home/hatch/workspace/stick-figure-avatar/photoreal/tools/mpfb2.zip")
V4_TARGET = HERE / "body.belly.protrusion_v4.target"
V3_TARGET = HERE / "body.belly.protrusion_v3.target"
COUPLED4 = WORK / "target_coupled_v4_w0.5.target"

# --- write the coupled +0.5 fixture target from the shipped components
_v4 = np.load(WORK / "belly_v4.npz")
D05 = 0.5 * _v4["lin_v4_canonical_m"] + 0.25 * _v4["sag_v4_canonical_m"]
def fmt(v):
    s = f"{abs(v):.3f}".rstrip("0")
    if s.endswith("."): s += "0"
    if s in ("", "0."): s = "0"
    return ("-" + s) if v < 0 else s
d_obj = np.stack([D05[:, 0], D05[:, 2], D05[:, 1]], axis=1) / 0.1
moved = np.where(np.abs(d_obj).max(axis=1) > 0.001)[0]
with open(COUPLED4, "w") as fh:
    fh.write("# This is a target file for MakeHuman\n#\n# basemesh hm08\n"
             "# QA harness artefact: coupled v4 shape at w=+0.5 "
             "(0.5*LIN + 0.25*SAG).\n")
    for i in moved:
        fh.write(f"{i} {fmt(d_obj[i,0])} {fmt(d_obj[i,1])} {fmt(d_obj[i,2])}\n")
print(f"coupled +0.5 fixture: {len(moved)} moved verts")

qa1 = json.loads((WORK / "qa_numbers.json").read_text())
ANCHOR_CM = float(qa1["anchor_m"]) * 100
corr = np.load(WORK / "correspondence.npz")
NAVEL = int(corr["navel_mh"])

bpy.ops.wm.read_factory_settings(use_empty=True)
try:
    bpy.ops.extensions.package_install_files(filepath=str(MPFB_ZIP),
                                             repo="user_default",
                                             enable_on_install=True)
except RuntimeError:
    bpy.ops.preferences.addon_enable(module="bl_ext.user_default.mpfb")
import importlib  # noqa: E402
importlib.import_module("bl_ext.user_default.mpfb")
from bl_ext.user_default.mpfb.services.humanservice import HumanService  # noqa: E402
from bl_ext.user_default.mpfb.services.targetservice import TargetService  # noqa: E402

human = HumanService.create_human(mask_helpers=False)
assert len(human.data.vertices) == 19158, len(human.data.vertices)
k_v4 = TargetService.load_target(human, str(V4_TARGET))
k_cp = TargetService.load_target(human, str(COUPLED4))
print("shape keys:", k_v4.name, "|", k_cp.name)
blocks = human.data.shape_keys.key_blocks
M = np.array(human.matrix_world)

def evaluated():
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = human.evaluated_get(dg)
    co = np.empty(len(ev.data.vertices) * 3)
    ev.data.vertices.foreach_get("co", co)
    return co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]

def set_state(which, value=0.0):
    blocks[k_v4.name].value = 0.0
    blocks[k_cp.name].value = 0.0
    if which == "v4":
        blocks[k_v4.name].value = float(value)
    elif which == "coupled":
        blocks[k_cp.name].value = 1.0

set_state("v4", 0.0)
base = evaluated()
nz = base[NAVEL][2]
print(f"navel base pos {np.round(base[NAVEL], 3)} (z={nz:.3f})")
slices = []
for z in np.arange(nz - 0.06, nz + 0.061, 0.005):
    sel = np.where(np.abs(base[:, 2] - z) < 0.004)[0]
    sel = sel[np.abs(base[sel][:, 0] - base[NAVEL][0]) < 0.17]
    if len(sel) > 20:
        slices.append(base[sel].mean(axis=0))
slices = np.array(slices)
zg = slices[:, 2]
def axis_at(z):
    return np.array([np.interp(z, zg, slices[:, 0]),
                     np.interp(z, zg, slices[:, 1]), z])
fdir = base[NAVEL] - axis_at(nz)
fdir[2] = 0.0
fdir = fdir / np.linalg.norm(fdir)
print("forward dir (Blender world):", np.round(fdir, 3))

def measure(which, value=0.0):
    set_state(which, value)
    pos = evaluated()
    d = pos[NAVEL] - base[NAVEL]
    return {"forward_cm": float(d @ fdir * 100), "down_cm": float(-d[2] * 100),
            "delta_cm": [float(x * 100) for x in d]}
res = {}
for tag, (w, v) in [("w+0.5", ("coupled", 0.0)), ("w+1.0", ("v4", 1.0))]:
    r = measure(w, v)
    res[tag] = r
    print(f"R {tag}: navel forward {r['forward_cm']:.2f} cm, down {r['down_cm']:.2f} cm")

set_state("v4", 1.0)
pos1 = evaluated()
tris = np.array([list(p.vertices) for p in human.data.polygons])
cen = base[tris].mean(axis=1)
front = (cen - np.array([axis_at(z) for z in cen[:, 2]])) @ fdir
belly_sel = (np.abs(cen[:, 2] - nz) < 0.20) & (front > 0.03) & (np.abs(cen[:, 0]) < 0.17)
fb = tris[belly_sel]
def fn(P, F):
    nn = np.cross(P[F[:, 1]] - P[F[:, 0]], P[F[:, 2]] - P[F[:, 0]])
    return nn / np.maximum(np.linalg.norm(nn, axis=1, keepdims=True), 1e-14)
dots = np.einsum("ij,ij->i", fn(base, fb), fn(pos1, fb))
res["eval_belly_region"] = {"faces": int(belly_sel.sum()),
                            "flips": int((dots < 0).sum()),
                            "min_dot": float(dots.min())}
print(f"R evaluated belly-region faces {belly_sel.sum()}: flips {(dots < 0).sum()}, "
      f"min_dot {dots.min():.3f}")
(WORK / "blender_v4_numbers.json").write_text(json.dumps(res, indent=1))

# ------------------------------------------------------------- renders
mask_mod = human.modifiers.new("Hide helpers", 'MASK')
mask_mod.vertex_group = "body"
scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "SINGLE"
scene.display.shading.single_color = (0.75, 0.72, 0.70)
scene.display.shading.show_cavity = True
scene.display.shading.cavity_type = "BOTH"
scene.display.shading.curvature_ridge_factor = 1.2
scene.display.shading.curvature_valley_factor = 0.8
scene.render.resolution_x = 640
scene.render.resolution_y = 800
world = bpy.data.worlds.new("W") if not bpy.data.worlds else bpy.data.worlds[0]
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (0.12, 0.12, 0.13, 1)
bg.inputs[1].default_value = 1.0
sun_data = bpy.data.lights.new("Sun", "SUN")
sun = bpy.data.objects.new("Sun", sun_data)
scene.collection.objects.link(sun)
sun.rotation_euler = (0.9, 0.2, 0.6)
cam_data = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam

def point_cam(loc, target=(0, 0, 0.95)):
    cam.location = loc
    d = np.array(target) - np.array(loc)
    cam.rotation_euler = (math.atan2(d[2], math.hypot(d[0], d[1])) + math.pi / 2,
                          0, math.atan2(d[1], d[0]) - math.pi / 2)

centre = axis_at(0.95)
side = np.array([-fdir[1], fdir[0], 0.0])
# NOTE: the character faces along +fdir; cameras sit at centre + fdir*d.
# (First run had the sign flipped and produced back views -- kept on
# disk as belly_v4_w+1.0_back.png / _back_threequarter.png; they turned
# out to be useful evidence for the back-mass rule R8.)
front_loc = (centre + fdir * 2.35); front_loc[2] = 1.02
tq_loc = (centre + fdir * 1.75 + side * 1.55); tq_loc[2] = 1.06
back_loc = (centre - fdir * 2.35); back_loc[2] = 1.02
target = tuple(centre)

def render(which, value, loc, tag, tgt=(0, 0, 0.95)):
    set_state(which, value)
    bpy.context.view_layer.update()
    point_cam(loc, tgt)
    scene.render.filepath = str(RENDERS / f"belly_v4_{tag}.png")
    bpy.ops.render.render(write_still=True)
    print("rendered", tag)

render("coupled", 0.0, (-2.1, -0.35, 1.02), "w+0.5_profile")
render("v4", 1.0, (-2.1, -0.35, 1.02), "w+1.0_profile")
render("v4", 1.0, tuple(front_loc), "w+1.0_front", target)
render("v4", 1.0, tuple(tq_loc), "w+1.0_threequarter", target)
render("v4", 1.0, tuple(back_loc), "w+1.0_back", target)
print("TEST V4 DONE")
