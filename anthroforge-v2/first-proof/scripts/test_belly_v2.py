#!/usr/bin/env python3
"""Blender end-to-end for belly v2 (sag-corrected), written against the
actually-installed MPFB 2.0.18 API (object-first TargetService).

Loads the combined v2 target and the coupled +0.5 field as shape keys on
a default-macro MPFB human, measures the navel displacement VECTOR
(forward + down) on the evaluated mesh, flip-checks belly-region faces
at +1 in Blender's own frame, and renders profile views at 0/+0.5/+1
with the v1 proof's exact camera/lighting so renders compare directly.

Run with an isolated HOME so the shared Blender config (which other
projects churn) is untouched:
  HOME=/tmp/af_home blender -b --python test_belly_v2.py
"""
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np

HERE = Path(__file__).resolve().parent.parent
V2 = HERE.parent
APP = V2.parent / "anthroforge-app"
for _p in (str(V2), str(APP)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from body_machinery import axis_at_3d  # noqa: E402
from core.geometry import face_normals as fn  # noqa: E402

WORK = HERE / "work"
RENDERS = HERE / "renders"
MPFB_ZIP = Path("/home/hatch/workspace/stick-figure-avatar/photoreal/tools/mpfb2.zip")
V2_TARGET = HERE / "body.belly.protrusion_v2.target"
COUPLED_TARGET = WORK / "target_coupled_w0.5.target"

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
k_v2 = TargetService.load_target(human, str(V2_TARGET))
k_cp = TargetService.load_target(human, str(COUPLED_TARGET))
print("shape keys:", k_v2.name, "|", k_cp.name)
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
    blocks[k_v2.name].value = 0.0
    blocks[k_cp.name].value = 0.0
    if which == "v2":
        blocks[k_v2.name].value = float(value)
    elif which == "coupled":
        blocks[k_cp.name].value = 1.0


set_state("v2", 0.0)
base = evaluated()
nz = base[NAVEL][2]
print(f"navel base pos {np.round(base[NAVEL], 3)} (z={nz:.3f})")

# torso axis: slice centroids around navel height (front = -Y or +Y is
# derived from geometry: the navel sits on the front of the section)
slices = []
for z in np.arange(nz - 0.06, nz + 0.061, 0.005):
    sel = np.where(np.abs(base[:, 2] - z) < 0.004)[0]
    sel = sel[np.abs(base[sel][:, 0] - base[NAVEL][0]) < 0.17]
    if len(sel) > 20:
        slices.append(base[sel].mean(axis=0))
slices = np.array(slices)
zg = slices[:, 2]


def axis_at(z):
    return axis_at_3d(zg, slices, z)


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
for tag, (w, v) in [("w+0.0", ("v2", 0.0)), ("w+0.5", ("coupled", 0.0)),
                    ("w+1.0", ("v2", 1.0))]:
    r = measure(w, v)
    res[tag] = r
    print(f"R {tag}: navel forward {r['forward_cm']:.2f} cm, down {r['down_cm']:.2f} cm")
err = abs(res["w+1.0"]["forward_cm"] - ANCHOR_CM) * 10
print(f"R anchor forward error at +1 (Blender): {err:.1f} mm (numpy v2: 1.3 mm)")

# belly-region flip cross-check in Blender's own frame at +1
set_state("v2", 1.0)
pos1 = evaluated()
tris = np.array([list(p.vertices) for p in human.data.polygons])
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
(WORK / "blender_v2_numbers.json").write_text(json.dumps(res, indent=1))

# ------------------------------------------------------------- renders
# measurements needed the unmasked mesh; renders need helpers hidden,
# exactly as MPFB's own "Hide helpers" mask does it
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


def render(which, value, tag):
    set_state(which, value)
    bpy.context.view_layer.update()
    point_cam((-2.1, -0.35, 1.02))
    scene.render.filepath = str(RENDERS / f"belly_v2_{tag}_profile.png")
    bpy.ops.render.render(write_still=True)
    print("rendered", tag)


render("v2", 0.0, "w+0.0")
render("coupled", 0.0, "w+0.5")
render("v2", 1.0, "w+1.0")
print("TEST V2 DONE")
