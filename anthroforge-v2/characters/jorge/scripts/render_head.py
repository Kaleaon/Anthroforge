#!/usr/bin/env python3
"""Clay renders of a built species head — front / three-quarter /
profile, for face judging. Flat studio world (no HDRI), one key sun +
one fill, EEVEE, matte clay materials with the eyes/nose/teeth kept
tonally distinct so the face reads. No fur.

    blender -b --threads 2 --python render_head.py -- \
        --glb CHAR_head.glb --outdir renders/

Framing is computed from the head's own bbox (ears included — Pyn's
pinnae define the frame). NeckSocketDisc is render-hidden: it is a
body-interface cap plate, not head shape.
"""
import argparse
import math
import sys
from pathlib import Path

import bpy
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:]
ap = argparse.ArgumentParser()
ap.add_argument("--glb", required=True)
ap.add_argument("--outdir", required=True)
A = ap.parse_args(argv)
OUT = Path(A.outdir)
OUT.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=A.glb)


def clay(name, rgb, rough=0.85):
    m = bpy.data.materials.new(name)
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    return m


MATS = {
    "clay": clay("clay", (0.52, 0.50, 0.48)),
    "eye": clay("eye", (0.92, 0.92, 0.90), 0.35),
    "iris": clay("iris", (0.16, 0.11, 0.08), 0.40),
    "pupil": clay("pupil", (0.02, 0.02, 0.02), 0.40),
    "nose": clay("nose", (0.23, 0.20, 0.19), 0.60),
    "teeth": clay("teeth", (0.88, 0.85, 0.78), 0.50),
    "tongue": clay("tongue", (0.45, 0.28, 0.28), 0.70),
}
for o in bpy.data.objects:
    if o.type != "MESH":
        continue
    n = o.name
    if n == "NeckSocketDisc":
        o.hide_render = True
        continue
    if n.startswith("Eyeball"):
        m = MATS["eye"]
    elif n.startswith("Iris"):
        m = MATS["iris"]
    elif n.startswith("Pupil"):
        m = MATS["pupil"]
    elif n == "NoseLeather":
        m = MATS["nose"]
    elif n.startswith("Teeth"):
        m = MATS["teeth"]
    elif n == "Tongue":
        m = MATS["tongue"]
    else:
        m = MATS["clay"]
    o.data.materials.clear()
    o.data.materials.append(m)

# frame from the full bbox (all mesh objects, render-visible or not —
# the disc is small and central, including it changes nothing)
lo = np.full(3, 1e9)
hi = np.full(3, -1e9)
for o in bpy.data.objects:
    if o.type != "MESH":
        continue
    M = np.array(o.matrix_world)
    co = np.empty(len(o.data.vertices) * 3)
    o.data.vertices.foreach_get("co", co)
    W = co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]
    lo = np.minimum(lo, W.min(axis=0))
    hi = np.maximum(hi, W.max(axis=0))
centre = 0.5 * (lo + hi)
radius = 0.5 * float(np.linalg.norm(hi - lo))
print("bbox lo", np.round(lo, 3), "hi", np.round(hi, 3),
      "centre", np.round(centre, 3), "radius", round(radius, 3))

sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE"
sc.render.resolution_x = 640
sc.render.resolution_y = 800
world = bpy.data.worlds.new("W")
sc.world = world
world.node_tree.nodes["Background"].inputs[0].default_value = \
    (0.35, 0.35, 0.36, 1.0)

for name, energy, rot in (("Key", 3.0, (0.9, 0.2, 0.6)),
                          ("Fill", 0.8, (1.1, -0.4, -2.4))):
    d = bpy.data.lights.new(name, "SUN")
    d.energy = energy
    o = bpy.data.objects.new(name, d)
    sc.collection.objects.link(o)
    o.rotation_euler = rot

cam_d = bpy.data.cameras.new("Cam")
cam_d.lens = 50.0
cam = bpy.data.objects.new("Cam", cam_d)
sc.collection.objects.link(cam)
sc.camera = cam
fov_v = 2 * math.atan(12.0 / cam_d.lens)          # 24 mm sensor height
fov_h = 2 * math.atan(18.0 / cam_d.lens)          # 36 mm sensor width
corners = np.array([[x, y, z] for x in (lo[0], hi[0])
                    for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])


def fit_dist(dirv):
    """Exact bbox-corner fit: smallest camera distance along dirv at
    which every bbox corner is inside both frustum half-angles
    (replaces the bounding-sphere fit, which framed Pyn's face at
    ~25% of frame height)."""
    zc = dirv / np.linalg.norm(dirv)
    up = np.array([0.0, 0.0, 1.0])
    if abs(float(zc @ up)) > 0.95:
        up = np.array([0.0, 1.0, 0.0])
    xc = np.cross(up, zc)
    xc = xc / np.linalg.norm(xc)
    yc = np.cross(zc, xc)
    rel = corners - centre
    cx, cy, cz = rel @ xc, rel @ yc, rel @ zc
    need = np.maximum(cz + np.abs(cx) / math.tan(fov_h / 2),
                      cz + np.abs(cy) / math.tan(fov_v / 2))
    return float(need.max()) * 1.05


def point_cam(loc, target):
    cam.location = loc
    d = np.array(target, float) - np.array(loc, float)
    cam.rotation_euler = (
        math.atan2(d[2], math.hypot(d[0], d[1])) + math.pi / 2,
        0, math.atan2(d[1], d[0]) - math.pi / 2)


views = {
    "front": np.array([0.0, 1.0, 0.10]),
    "threequarter": np.array([0.55, 0.80, 0.24]),
    "profile": np.array([1.0, 0.0, 0.06]),
}
for tag, dirv in views.items():
    dirv = dirv / np.linalg.norm(dirv)
    point_cam(tuple(centre + dirv * fit_dist(dirv)), tuple(centre))
    sc.render.filepath = str(OUT / f"head_{tag}.png")
    bpy.ops.render.render(write_still=True)
    print("rendered", tag)
print("HEAD RENDERS DONE")
