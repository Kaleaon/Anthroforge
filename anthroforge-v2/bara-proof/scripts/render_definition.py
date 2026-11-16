#!/usr/bin/env python3
"""Blender renders + evaluated flip check for the definition
instances (DEFINITION_GEOMETRY.md).

States (the attenuation table made visible): the full definition
set (flat_abs + traps_valleys + pecs_crease + back) at authored
value 1.0 over the muscle system (tissue 0); at the evaluator's
EFFECTIVE values over the strongman build; and at the effective
values over the gachidebu build (the shipped coupling target).
Torso close-ups, front and back, Workbench cavity shading (the
relief shading), v4/bara camera discipline.

Run: HOME=/tmp/af_home xvfb-run blender -b --python render_definition.py
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
NUM = json.loads((WORK / "definition_numbers.json").read_text())
EFF = {tag: {d: NUM["evaluator"][tag]["effective_at_raw_1.0"][d]
             for d in ("body.definition.flat_abs",
                       "body.definition.traps_valleys",
                       "body.definition.pecs_crease",
                       "body.definition.back")}
       for tag in ("strongman", "gachidebu")}
TARGETS = {"core": HERE / "body.muscle.target",
           "width": HERE / "body.chest.width.target",
           "tissue": HERE / "body.tissue.strongman.target",
           "gachi": HERE / "body.coupling.gachidebu.target",
           "flat_abs": HERE / "body.definition.flat_abs.target",
           "valleys": HERE / "body.definition.traps_valleys.target",
           "crease": HERE / "body.definition.pecs_crease.target",
           "back": HERE / "body.definition.back.target"}
DEFKEY = {"body.definition.flat_abs": "flat_abs",
          "body.definition.traps_valleys": "valleys",
          "body.definition.pecs_crease": "crease",
          "body.definition.back": "back"}
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


def set_state(core=0.0, width=0.0, tissue=0.0, gachi=0.0, defs=None):
    blocks[keys["core"].name].value = core
    blocks[keys["width"].name].value = width
    blocks[keys["tissue"].name].value = tissue
    blocks[keys["gachi"].name].value = gachi
    for d, k in DEFKEY.items():
        blocks[keys[k].name].value = (defs or {}).get(d, 0.0)


STATES = {
    "tissue0": dict(core=1.0, width=1.0,
                    defs={d: 1.0 for d in DEFKEY}),
    "strongman": dict(core=1.0, width=1.0, tissue=1.0,
                      defs=EFF["strongman"]),
    "gachidebu": dict(gachi=1.0, defs=EFF["gachidebu"]),
}

set_state()
base = evaluated()
dg = bpy.context.evaluated_depsgraph_get()
ev = human.evaluated_get(dg)
ev.data.calc_loop_triangles()
tris = np.array([[v for v in t.vertices]
                 for t in ev.data.loop_triangles], dtype=np.int64)
tris = tris[np.all(tris < BODY_END, axis=1)]


def fn(P, F):
    nn = np.cross(P[F[:, 1]] - P[F[:, 0]], P[F[:, 2]] - P[F[:, 0]])
    return nn / np.maximum(np.linalg.norm(nn, axis=1, keepdims=True),
                           1e-14)


res = {"body_triangles": int(len(tris)), "states": {}}
for tag, st in STATES.items():
    set_state(**st)
    pos = evaluated()
    dots = np.einsum("ij,ij->i", fn(base, tris), fn(pos, tris))
    res["states"][tag] = {"flips": int((dots < 0).sum()),
                          "min_dot": float(dots.min())}
    print(f"R evaluated {tag}: flips {(dots < 0).sum()}, "
          f"min_dot {dots.min():.3f}")
(WORK / "blender_definition_numbers.json").write_text(
    json.dumps(res, indent=1))

# ---- cameras (v4 method: forward from the navel slices)
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
side = np.array([-fdir[1], fdir[0], 0.0])

mask_mod = human.modifiers.new("Hide helpers", "MASK")
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
scene.render.resolution_x = 700
scene.render.resolution_y = 760
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


def point_cam(loc, target):
    cam.location = loc
    d = np.array(target) - np.array(loc)
    cam.rotation_euler = (
        math.atan2(d[2], math.hypot(d[0], d[1])) + math.pi / 2,
        0, math.atan2(d[1], d[0]) - math.pi / 2)


centre = axis_at(1.04)
front_loc = tuple(centre + fdir * 1.30 + np.array([0, 0, 0.06]))
back_loc = tuple(centre - fdir * 1.30 + side * 0.22
                 + np.array([0, 0, 0.08]))
target = tuple(centre)


def render(state_tag, loc, view):
    set_state(**STATES[state_tag])
    bpy.context.view_layer.update()
    point_cam(loc, target)
    scene.render.filepath = str(
        RENDERS / f"def_{state_tag}_{view}.png")
    bpy.ops.render.render(write_still=True)
    print("rendered", state_tag, view)


for tag in ("tissue0", "strongman", "gachidebu"):
    render(tag, front_loc, "front")
    render(tag, back_loc, "back")
print("RENDER DEFINITION DONE")
