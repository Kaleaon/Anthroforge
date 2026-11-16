#!/usr/bin/env python3
"""Blender end-to-end for the bara strongman proof.

Loads the three component targets (body.muscle core, body.chest.width,
body.tissue.strongman) plus the combined convenience target on a
default-macro MPFB human; verifies the combined target equals the sum
of the three component keys on the evaluated mesh; flip-checks ALL
body faces at the muscle-system and combined states; renders the
combined build (front / profile / three-quarter, v4's exact camera and
lighting so profiles composite against the earlier proofs), the
muscle-system profile, and the base profile, then composites
base-vs-build profile, then composites base-vs-build profile side by
side (the composite itself is a 6-line system-python post-step, since
Blender's bundled python has no PIL).

Run: HOME=/tmp/af_home xvfb-run blender -b --python test_bara.py
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
TARGETS = {"core": HERE / "body.muscle.target",
           "width": HERE / "body.chest.width.target",
           "tissue": HERE / "body.tissue.strongman.target",
           "combined": HERE / "body.bara.strongman.target"}
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


def set_state(core=0.0, width=0.0, tissue=0.0, combined=0.0):
    blocks[keys["core"].name].value = core
    blocks[keys["width"].name].value = width
    blocks[keys["tissue"].name].value = tissue
    blocks[keys["combined"].name].value = combined


set_state()
base = evaluated()
set_state(core=1.0, width=1.0)
pos_muscle = evaluated()
set_state(core=1.0, width=1.0, tissue=1.0)
pos_comb3 = evaluated()
set_state(combined=1.0)
pos_comb1 = evaluated()
set_state(core=1.0, width=1.0, tissue=1.0)

dev = np.linalg.norm(pos_comb3 - pos_comb1, axis=1)
print(f"combined target vs 3-key sum: max deviation "
      f"{dev.max()*100:.3f} cm, mean {dev.mean()*100:.3f} cm")

# ---- flip check over all body faces (loop triangles, body verts only)
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


res = {"combined_target_max_dev_cm": float(dev.max() * 100),
       "combined_target_mean_dev_cm": float(dev.mean() * 100),
       "body_triangles": int(len(tris))}
for tag, pos in (("muscle_system", pos_muscle), ("combined", pos_comb3)):
    dots = np.einsum("ij,ij->i", fn(base, tris), fn(pos, tris))
    res[f"eval_{tag}"] = {"faces": int(len(tris)),
                          "flips": int((dots < 0).sum()),
                          "min_dot": float(dots.min())}
    print(f"R evaluated {tag}: flips {(dots < 0).sum()}, "
          f"min_dot {dots.min():.3f}")
(WORK / "blender_bara_numbers.json").write_text(json.dumps(res, indent=1))

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
    cam.rotation_euler = (
        math.atan2(d[2], math.hypot(d[0], d[1])) + math.pi / 2,
        0, math.atan2(d[1], d[0]) - math.pi / 2)


centre = axis_at(0.95)
side = np.array([-fdir[1], fdir[0], 0.0])
front_loc = centre + fdir * 2.35
front_loc[2] = 1.02
tq_loc = centre + fdir * 1.75 + side * 1.55
tq_loc[2] = 1.06
target = tuple(centre)


def render(state_kwargs, loc, tag, tgt=(0, 0, 0.95)):
    set_state(**state_kwargs)
    bpy.context.view_layer.update()
    point_cam(loc, tgt)
    scene.render.filepath = str(RENDERS / f"bara_{tag}.png")
    bpy.ops.render.render(write_still=True)
    print("rendered", tag)


COMB = {"core": 1.0, "width": 1.0, "tissue": 1.0}
MUSC = {"core": 1.0, "width": 1.0}
render(COMB, tuple(front_loc), "combined_front", target)
render(COMB, (-2.1, -0.35, 1.02), "combined_profile")
render(COMB, tuple(tq_loc), "combined_threequarter", target)
render(MUSC, (-2.1, -0.35, 1.02), "muscle_profile")
render({}, (-2.1, -0.35, 1.02), "base_profile")
print("TEST BARA DONE")
