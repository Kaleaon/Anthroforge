#!/usr/bin/env python3
"""Blender end-to-end for belly v5.1 (v5 + terminal tissue).

Loads the v5 combined target and the v5.1 TERMINAL component as two
shape keys on a default-macro MPFB human; composed state = both at
1.0. Checks: evaluated-mesh flip gate over ALL body faces at the
composed +1; renders hand close-ups (dorsal + palmar, base and
composed), a foot close-up (composed), and the full-body front
(composed) for visual comparison against the v5 renders.

Run: HOME=/tmp/af_home xvfb-run blender -b --python test_belly_v51.py
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
TERM_TARGET = HERE / "body.belly.protrusion_terminal_v51.target"
BODY_END = 13380

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
k_tm = TargetService.load_target(human, str(TERM_TARGET))
blocks = human.data.shape_keys.key_blocks
M = np.array(human.matrix_world)

def evaluated():
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = human.evaluated_get(dg)
    co = np.empty(len(ev.data.vertices) * 3)
    ev.data.vertices.foreach_get("co", co)
    return co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]

def set_state(v5=0.0, tm=0.0):
    blocks[k_v5.name].value = float(v5)
    blocks[k_tm.name].value = float(tm)

set_state()
base = evaluated()
set_state(1.0, 1.0)
pos1 = evaluated()
tris = np.array([list(p.vertices) for p in human.data.polygons])
def fn(P, F):
    nn = np.cross(P[F[:, 1]] - P[F[:, 0]], P[F[:, 2]] - P[F[:, 0]])
    return nn / np.maximum(np.linalg.norm(nn, axis=1, keepdims=True), 1e-14)
body_sel = np.array([np.all(f < BODY_END) for f in tris])
fbb = tris[body_sel]
dots_b = np.einsum("ij,ij->i", fn(base, fbb), fn(pos1, fbb))
res = {"eval_all_body_faces_v51": {"faces": int(body_sel.sum()),
                                   "flips": int((dots_b < 0).sum()),
                                   "min_dot": float(dots_b.min())}}
print(f"R evaluated ALL body faces (v5.1 composed): flips "
      f"{(dots_b < 0).sum()}, min_dot {dots_b.min():.4f}")
(WORK / "blender_v51_numbers.json").write_text(json.dumps(res, indent=1))

# ------------------------------------------------------------- renders
# Canonical (x, y_front, z_up) -> Blender world (x, -y_front, z_up)
# for direction vectors; positions come from the evaluated mesh.
def can_dir(v):
    return np.array([v[0], -v[1], v[2]])
# right hand centroid from base verts (canonical hand region indices
# are the base.obj body indices; use the geometric gate x>0.40)
hand_idx = np.where((base[:, 0] > 0.40) & (np.abs(base[:, 2] - 0.85) < 0.75))[0]
# restrict to the distal cluster: keep verts within 9 cm of the
# extreme-x vert
x0 = base[np.argmax(base[:, 0])]
hand_idx = hand_idx[np.linalg.norm(base[hand_idx] - x0, axis=1) < 0.11]
hc = base[hand_idx].mean(axis=0)
foot_idx = np.where((base[:, 2] < base[:, 2].min() + 0.16) & (base[:, 0] > 0.03))[0]
fc = base[foot_idx].mean(axis=0)
print("hand centroid (Blender):", np.round(hc, 3), "foot:", np.round(fc, 3))
_frames = json.loads((WORK / "hand_frames_v51.json").read_text())
E_DP_R = can_dir(np.array(_frames["R"]["e_dp"]))     # dorsal, from build
E_LONG_R = can_dir(np.array(_frames["R"]["e_long"]))

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

def point_cam(loc, target):
    cam.location = tuple(loc)
    d = np.array(target) - np.array(loc)
    cam.rotation_euler = (math.atan2(d[2], math.hypot(d[0], d[1])) + math.pi / 2,
                          0, math.atan2(d[1], d[0]) - math.pi / 2)

def render(tag, loc, target, res=560):
    scene.render.resolution_x = res
    scene.render.resolution_y = res
    point_cam(loc, target)
    scene.render.filepath = str(RENDERS / f"belly_v51_{tag}.png")
    bpy.ops.render.render(write_still=True)
    print("rendered", tag)

# dorsal hand: camera along +dorsal from centroid
set_state(0.0, 0.0)
render("hand_dorsal_base", hc + E_DP_R * 0.17 + E_LONG_R * 0.02, hc)
set_state(1.0, 1.0)
render("hand_dorsal_w+1.0", hc + E_DP_R * 0.17 + E_LONG_R * 0.02, hc)
render("hand_palmar_w+1.0", hc - E_DP_R * 0.17 + E_LONG_R * 0.02, hc)
render("foot_w+1.0", fc + np.array([0.16, -0.20, 0.15]), fc)
# full-body front, same framing family as v5 front
scene.render.resolution_x = 640
scene.render.resolution_y = 800
render("w+1.0_front", np.array([0.0, -2.35, 0.90]), np.array([0.0, 0.0, 0.85]))
print("TEST V51 DONE")
