#!/usr/bin/env python3
"""SEN stage 2, renders-only pass (stage E of build_cards_renders.py).

Why this exists: the full stage-2 runner completed stage D (curtain
bake -> fur_card_texture_sen.png) and all three LOD card GLBs, then a
runtime restart killed the Blender process during the first beauty
render. Those outputs are verified on disk, so only stage E is re-run
here, from the pristine stage-1 sen_build.blend.

The stage E block below is copied byte-for-byte from
build_cards_renders.py except the final save_as_mainfile (see inline
note). Preamble divergences, all documented:
  * SEN resolved from __file__ (original used Path.home()).
  * neck_axis recomputed with stage 1's formula on the saved cut body;
    fdir from build_stage1.log ("forward dir: [ 0.067 -0.998  0. ]").
  * The stage-D Sun (energy 3.0, rotation (0.9, 0.2, 0.6)) is recreated:
    in the single-process design it persisted into stage E and lit the
    beauty renders together with the 0.12 grey world.
  * The leftover MPFB "Human" source object is render-hidden (stage 1
    baked SenBody from it but never hid it; it is unfurred and uncut).
  * Groom child_percent stays at the saved 50 (the full run set it to
    0 for strand extraction). Render children are governed by
    rendered_child_count (=3) either way; child_percent thins only
    the viewport display, which is why the original used it to keep
    extraction inside the VM's RAM.
  * SAMPLES 32 -> 12 (measured divergence): probe renders of the
    front view on this VM measured 39.4 s per sample at full frame
    (2 spp @ 320x400 = 23.7 s; 2 spp @ 640x800 = 82.8 s; fixed
    overhead ~4 s). The scripted 32 spp therefore costs ~21 min per
    frame, ~85 min for the set — the first attempt was killed by a
    runtime restart 15 min into frame 1 without a single frame
    landing. 12 spp (~8 min/frame) keeps resolution, cameras,
    lighting and geometry exactly as scripted; the noise level is
    recorded as a debit in SEN_BUILD.md.
"""
import math
from pathlib import Path
import numpy as np
import bpy

SEN = Path(__file__).resolve().parent.parent
REND = SEN / "renders"
bpy.ops.wm.open_mainfile(filepath=str(SEN / "sen_build.blend"))
sc = bpy.context.scene
scene = bpy.context.scene
FRONT = int(sc["af_front"]); CUT_Z = float(sc["af_cut_z"])
cut_z = CUT_Z
body = bpy.data.objects["SenBody"]
_P = np.empty(len(body.data.vertices) * 3)
body.data.vertices.foreach_get("co", _P)
_P = _P.reshape(-1, 3)
neck_axis = _P[np.abs(_P[:, 2] - CUT_Z) < 0.01].mean(axis=0)
fdir = np.array([0.067, -0.998, 0.0])
print("renders-only landmarks: neck_axis", np.round(neck_axis, 4))
bpy.data.objects["Human"].hide_render = True
sun_d = bpy.data.lights.new("Sun", "SUN")
sun_d.energy = 3.0
sun = bpy.data.objects.new("Sun", sun_d)
scene.collection.objects.link(sun)
sun.rotation_euler = (0.9, 0.2, 0.6)

# ------------------------------------------------------------ stage E
scene.render.engine = "CYCLES"
scene.cycles.samples = 12  # DIVERGENCE: scripted 32 -> 12, see header (measured ~21 min/frame at 32 spp on this VM)
scene.render.resolution_x = 640
scene.render.resolution_y = 800
scene.render.film_transparent = False
world = bpy.data.worlds.new("W") if not bpy.data.worlds \
    else bpy.data.worlds[0]
scene.world = world
world.node_tree.nodes["Background"].inputs[0].default_value = \
    (0.12, 0.12, 0.13, 1)
cam_d2 = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_d2)
scene.collection.objects.link(cam)
scene.camera = cam
centre = np.array([neck_axis[0], neck_axis[1], 0.0])


def point_cam(loc, target):
    cam.location = loc
    d = np.array(target) - np.array(loc)
    cam.rotation_euler = (
        math.atan2(d[2], math.hypot(d[0], d[1])) + math.pi / 2,
        0, math.atan2(d[1], d[0]) - math.pi / 2)


side = np.array([-fdir[1], fdir[0], 0.0])
tgt = tuple(centre + np.array([0, 0, 0.92]))
views = {
    "front": tuple(centre + fdir * 2.5 + np.array([0, 0, 1.02])),
    "profile": tuple(centre + side * 2.5 + np.array([0, 0, 1.02])),
    "threequarter": tuple(centre + fdir * 1.85 + side * 1.65
                          + np.array([0, 0, 1.06])),
}
for tag, loc in views.items():
    point_cam(loc, tgt)
    scene.render.filepath = str(REND / f"sen_{tag}.png")
    bpy.ops.render.render(write_still=True)
    print("rendered", tag)
# head close-up
head_c = (np.array([neck_axis[0], neck_axis[1], cut_z]) +
          fdir * 0.10 + np.array([0, 0, 0.13]))
point_cam(tuple(head_c + fdir * 0.62 + side * 0.18 +
                np.array([0, 0, 0.10])), tuple(head_c))
scene.render.filepath = str(REND / "sen_head_closeup.png")
bpy.ops.render.render(write_still=True)
print("rendered head close-up")
print("stage-2 scene state NOT saved back (divergence, see header)")
print("BODY+FUR DONE")
