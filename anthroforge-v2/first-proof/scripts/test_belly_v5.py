#!/usr/bin/env python3
"""Blender end-to-end for belly v5 (whole-body adiposity: v4 torso
system extended into the limbs).

Loads the combined v5 target on a default-macro MPFB human, measures
the navel displacement on the evaluated mesh (must reproduce v4's
Blender numbers -- the navel vert is outside the limb region, so v5
inherits v4's torso exactly there), flip-checks the evaluated mesh
at +1 over (a) the v4 belly region and (b) ALL body faces (the
evaluated counterpart of the numpy hard gate), and renders: v5
profile at +0.5 (coupled) and +1, FRONT and THREE-QUARTER at +1.
Cameras/lighting identical to the v1-v4 proofs (profile camera
(-2.1, -0.35, 1.02)) so renders composite against v4's.

Run: HOME=/tmp/af_home xvfb-run blender -b --python test_belly_v5.py
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
V5_TARGET = HERE / "body.belly.protrusion_v5.target"
COUPLED5 = WORK / "target_coupled_v5_w0.5.target"
BODY_END = 13380

# --- write the coupled +0.5 fixture target from the shipped components
_v5 = np.load(WORK / "belly_v5.npz")
GAMMA = float(_v5["gamma"])
D05 = 0.5 * _v5["lin_v5_canonical_m"] + (0.5 ** GAMMA) * _v5["sag_v5_canonical_m"]
def fmt(v):
    s = f"{abs(v):.3f}".rstrip("0")
    if s.endswith("."): s += "0"
    if s in ("", "0."): s = "0"
    return ("-" + s) if v < 0 else s
d_obj = np.stack([D05[:, 0], D05[:, 2], D05[:, 1]], axis=1) / 0.1
moved = np.where(np.abs(d_obj).max(axis=1) > 0.001)[0]
with open(COUPLED5, "w") as fh:
    fh.write("# This is a target file for MakeHuman\n#\n# basemesh hm08\n"
             "# QA harness artefact: coupled v5 shape at w=+0.5 "
             "(0.5*LIN5 + 0.5^gamma*SAG).\n")
    for i in moved:
        fh.write(f"{i} {fmt(d_obj[i,0])} {fmt(d_obj[i,1])} {fmt(d_obj[i,2])}\n")
print(f"coupled +0.5 fixture: {len(moved)} moved verts")

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
k_v5 = TargetService.load_target(human, str(V5_TARGET))
k_cp = TargetService.load_target(human, str(COUPLED5))
print("shape keys:", k_v5.name, "|", k_cp.name)
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
    blocks[k_v5.name].value = 0.0
    blocks[k_cp.name].value = 0.0
    if which == "v5":
        blocks[k_v5.name].value = float(value)
    elif which == "coupled":
        blocks[k_cp.name].value = 1.0

set_state("v5", 0.0)
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
for tag, (w, v) in [("w+0.5", ("coupled", 0.0)), ("w+1.0", ("v5", 1.0))]:
    r = measure(w, v)
    res[tag] = r
    print(f"R {tag}: navel forward {r['forward_cm']:.2f} cm, down {r['down_cm']:.2f} cm")

set_state("v5", 1.0)
pos1 = evaluated()
tris = np.array([list(p.vertices) for p in human.data.polygons])
def fn(P, F):
    nn = np.cross(P[F[:, 1]] - P[F[:, 0]], P[F[:, 2]] - P[F[:, 0]])
    return nn / np.maximum(np.linalg.norm(nn, axis=1, keepdims=True), 1e-14)
# (a) v4 belly region, identical selection
cen = base[tris].mean(axis=1)
front = (cen - np.array([axis_at(z) for z in cen[:, 2]])) @ fdir
belly_sel = (np.abs(cen[:, 2] - nz) < 0.20) & (front > 0.03) & (np.abs(cen[:, 0]) < 0.17)
fb = tris[belly_sel]
dots = np.einsum("ij,ij->i", fn(base, fb), fn(pos1, fb))
res["eval_belly_region"] = {"faces": int(belly_sel.sum()),
                            "flips": int((dots < 0).sum()),
                            "min_dot": float(dots.min())}
print(f"R evaluated belly-region faces {belly_sel.sum()}: flips {(dots < 0).sum()}, "
      f"min_dot {dots.min():.3f}")
# (b) ALL body faces (every vert < BODY_END): the evaluated hard gate
body_sel = np.array([np.all(f < BODY_END) for f in tris])
fbb = tris[body_sel]
dots_b = np.einsum("ij,ij->i", fn(base, fbb), fn(pos1, fbb))
res["eval_all_body_faces"] = {"faces": int(body_sel.sum()),
                              "flips": int((dots_b < 0).sum()),
                              "min_dot": float(dots_b.min())}
print(f"R evaluated ALL body faces {body_sel.sum()}: flips {(dots_b < 0).sum()}, "
      f"min_dot {dots_b.min():.4f}")
(WORK / "blender_v5_numbers.json").write_text(json.dumps(res, indent=1))

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
front_loc = (centre + fdir * 2.35); front_loc[2] = 1.02
tq_loc = (centre + fdir * 1.75 + side * 1.55); tq_loc[2] = 1.06
target = tuple(centre)

def render(which, value, loc, tag, tgt=(0, 0, 0.95)):
    set_state(which, value)
    bpy.context.view_layer.update()
    point_cam(loc, tgt)
    scene.render.filepath = str(RENDERS / f"belly_v5_{tag}.png")
    bpy.ops.render.render(write_still=True)
    print("rendered", tag)

render("coupled", 0.0, (-2.1, -0.35, 1.02), "w+0.5_profile")
render("v5", 1.0, (-2.1, -0.35, 1.02), "w+1.0_profile")
render("v5", 1.0, tuple(front_loc), "w+1.0_front", target)
render("v5", 1.0, tuple(tq_loc), "w+1.0_threequarter", target)
print("TEST V5 DONE")
