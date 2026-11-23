#!/usr/bin/env python3
"""Blender end-to-end for the coupling validation builds.

Loads the three shipped character targets (gachidebu / pear /
big-chest) as shape keys on a default-macro MPFB human; flip-checks
ALL body faces on the evaluated mesh at each character state; renders
front + profile per character with the bara proof's exact camera and
lighting (Workbench, studio light) so profiles composite against the
earlier proofs.

Run: HOME=<scratch home> xvfb-run blender -b --python \
    test_coupling_validation.py
(the MPFB zip installs into HOME on first run)
"""
import json
import math
from pathlib import Path

import bpy
import numpy as np

HERE = Path(__file__).resolve().parent.parent
WORK = HERE / "work"
RENDERS = HERE / "renders"
FP_WORK = HERE.parent / "first-proof" / "work"
MPFB_ZIP = Path("/home/hatch/workspace/stick-figure-avatar/photoreal/"
                "tools/mpfb2.zip")
TARGETS = {"gachidebu": HERE / "body.coupling.gachidebu.target",
           "pear": HERE / "body.coupling.pear.target",
           "bigchest": HERE / "body.coupling.bigchest.target"}
BODY_END = 13380

corr = np.load(FP_WORK / "correspondence.npz")
NAVEL = int(corr["navel_mh"])

bpy.ops.wm.read_factory_settings(use_empty=True)
try:
    bpy.ops.extensions.package_install_files(
        filepath=str(MPFB_ZIP), repo="user_default",
        enable_on_install=True)
except RuntimeError:
    bpy.ops.preferences.addon_enable(module="bl_ext.user_default.mpfb")
import importlib  # noqa: E402
importlib.import_module("bl_ext.user_default.mpfb")
from bl_ext.user_default.mpfb.services.humanservice import HumanService  # noqa: E402
from bl_ext.user_default.mpfb.services.targetservice import TargetService  # noqa: E402

human = HumanService.create_human(mask_helpers=False)
assert len(human.data.vertices) == 19158, len(human.data.vertices)
keys = {tag: TargetService.load_target(human, str(p))
        for tag, p in TARGETS.items()}
blocks = human.data.shape_keys.key_blocks
M = np.array(human.matrix_world)


def evaluated():
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = human.evaluated_get(dg)
    co = np.empty(len(ev.data.vertices) * 3)
    ev.data.vertices.foreach_get("co", co)
    return co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]


def set_state(active=None):
    for tag, key in keys.items():
        blocks[key.name].value = 1.0 if tag == active else 0.0


set_state()
base = evaluated()

dg = bpy.context.evaluated_depsgraph_get()
ev = human.evaluated_get(dg)
ev.data.calc_loop_triangles()
tris = np.array([[v for v in t.vertices]
                 for t in ev.data.loop_triangles], dtype=np.int64)
tris = tris[np.all(tris < BODY_END, axis=1)]
print(f"body triangles for flip check: {len(tris)}")


def fn(P, F):
    nn = np.cross(P[F[:, 1]] - P[F[:, 0]], P[F[:, 2]] - P[F[:, 0]])
    return nn / np.maximum(np.linalg.norm(nn, axis=1, keepdims=True),
                           1e-14)


res = {"body_triangles": int(len(tris))}
positions = {}
for tag in TARGETS:
    set_state(tag)
    pos = evaluated()
    positions[tag] = pos
    dots = np.einsum("ij,ij->i", fn(base, tris), fn(pos, tris))
    res[tag] = {"flips": int((dots < 0).sum()),
                "min_dot": float(dots.min())}
    print(f"R evaluated {tag}: flips {(dots < 0).sum()}, "
          f"min_dot {dots.min():.3f}")
(WORK / "blender_coupling_validation_numbers.json").write_text(
    json.dumps(res, indent=1))

# ---- axis / forward direction (v4 method, from the navel slices)
nz = base[NAVEL][2]
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

# ------------------------------------------------------------- renders
mask_mod = human.modifiers.new("Hide helpers", "MASK")
mask_mod.vertex_group = "body"
scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "SINGLE"
scene.display.shading.single_color = (0.75, 0.72, 70 / 100)
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
    cam.rotation_euler = (
        math.atan2(d[2], math.hypot(d[0], d[1])) + math.pi / 2,
        0, math.atan2(d[1], d[0]) - math.pi / 2)


centre = axis_at(0.95)
front_loc = centre + fdir * 2.35
front_loc[2] = 1.02
target = tuple(centre)


def render(tag, loc, view, tgt=(0, 0, 0.95)):
    set_state(tag)
    bpy.context.view_layer.update()
    point_cam(loc, tgt)
    scene.render.filepath = str(RENDERS / f"coupling_{tag}_{view}.png")
    bpy.ops.render.render(write_still=True)
    print("rendered", tag, view)


for tag in TARGETS:
    render(tag, tuple(front_loc), "front", target)
    render(tag, (-2.1, -0.35, 1.02), "profile")
print("TEST COUPLING VALIDATION DONE")
