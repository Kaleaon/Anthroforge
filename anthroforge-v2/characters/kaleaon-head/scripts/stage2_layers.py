#!/usr/bin/env python3
"""Kaleaon head Phase 2 - Stage 2: skull + muscle layers (spec S8.2).

Bone-layer sliders on Skull, jaw set on SkullMandible, muscle-layer
set on Muscles; sagittal crest strip authored on the deformed cranium
(large-male lion variant, species spec S3.4). Tissue is NOT touched in
this stage, so the landmarks stay base-true for stage 3.

    blender -b --threads 2 --python stage2_layers.py
In:  base-head-v5/neutral_base_head_v5.blend
Out: work/stage2.blend + work/stage2.json
"""
import json
import sys
from pathlib import Path

import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import kaleaon_fields as F
from kaleaon_io import world_co, set_world

CHAR = Path("/home/hatch/workspace/anthroforge-v2/characters/kaleaon-head")
V5 = "/home/hatch/workspace/anthroforge-v2/base-head-v5/neutral_base_head_v5.blend"
V = {k: float(v) for k, v in json.loads(
    (CHAR / "scripts" / "kaleaon_vector.json").read_text()).items()
    if isinstance(v, (int, float))}

bpy.ops.wm.open_mainfile(filepath=V5)
objs = {o.name: o for o in bpy.data.objects if o.type == "MESH"}

TW, _ = world_co(objs["TissueHead"])
EL, _ = world_co(objs["Eyeball_L"])
ER, _ = world_co(objs["Eyeball_R"])
TU, _ = world_co(objs["TeethUpper"])
LM = F.landmarks(TW, EL, ER, np.array(objs["Jaw"].matrix_world)[:3, 3], TU)
print("LM:", {k: (np.round(v, 4).tolist() if isinstance(v, np.ndarray)
                  else round(v, 4) if isinstance(v, float) else v)
              for k, v in LM.items() if k != "eye_c"})


def nearest_dist(A, B, chunk=512):
    out = np.empty(len(A))
    for i in range(0, len(A), chunk):
        c = A[i:i + chunk]
        out[i:i + chunk] = np.sqrt(
            ((c[:, None, :] - B[None, :, :]) ** 2).sum(-1)).min(axis=1)
    return out


report = {}
# registration baseline: layer-to-tissue nearest distances BEFORE
base_dist = {}
for name in ("Skull", "Muscles"):
    W0, _ = world_co(objs[name])
    base_dist[name] = nearest_dist(W0, TW)

# ---- Skull (bone layer)
o = objs["Skull"]
W, M = world_co(o)
set_world(o, F.skull_fields(W.copy(), V, LM), M)
# ---- SkullMandible (jaw set)
o = objs["SkullMandible"]
W, M = world_co(o)
set_world(o, F.jaw_fields(W.copy(), V, LM), M)
# ---- Muscles (muscle layer)
o = objs["Muscles"]
W, M = world_co(o)
set_world(o, F.muscle_fields(W.copy(), V, LM), M)

for name in ("Skull", "Muscles"):
    W1, _ = world_co(objs[name])
    d1 = nearest_dist(W1, TW)
    report[name] = {
        "dist_to_tissue_before_mean": float(base_dist[name].mean()),
        "dist_to_tissue_after_mean": float(d1.mean()),
        "dist_to_tissue_after_max": float(d1.max()),
    }

# ---- Crest strip on the deformed cranium
L = LM["L"]
SK, _ = world_co(objs["Skull"])
TW2, _ = world_co(objs["TissueHead"])
ys = np.arange(LM["eye_y"] + 0.02 * L, -0.46 * L, -0.04 * L)
prof = []
for yy in ys:
    sel = SK[(np.abs(SK[:, 0]) < 0.012 * L) & (np.abs(SK[:, 1] - yy) < 0.02 * L)]
    tsel = TW2[(np.abs(TW2[:, 0]) < 0.012 * L)
               & (np.abs(TW2[:, 1] - yy) < 0.02 * L)]
    if len(sel) and len(tsel):
        prof.append((float(yy), float(sel[:, 2].max()),
                     float(tsel[:, 2].max())))
prof = np.array(prof)
# smooth the skull profile (3-tap)
zsm = prof[:, 1].copy()
zsm[1:-1] = 0.25 * prof[:-2, 1] + 0.5 * prof[1:-1, 1] + 0.25 * prof[2:, 1]
prof[:, 1] = zsm
RAISE = 0.0055 * L
verts, faces = [], []
for i, (yy, zt, tt) in enumerate(prof):
    # clamp: strip top must stay under the tissue surface
    raise_i = min(RAISE, max(0.0015 * L, (tt - 0.002 * L) - zt))
    if i > 0:
        dzdy = (prof[i, 1] - prof[i - 1, 1]) / (prof[i, 0] - prof[i - 1, 0])
    else:
        dzdy = (prof[1, 1] - prof[0, 1]) / (prof[1, 0] - prof[0, 0])
    n = np.array([0.0, -dzdy, 1.0])
    n = n / np.linalg.norm(n)
    c = np.array([0.0, yy, zt]) + n * raise_i
    side = np.array([0.016 * L, 0.0, 0.0])
    low = n * (0.0025 * L)
    row = [c - side + low, c + n * 0.0, c + side + low]
    # underside row (thickness, tucked toward the skull)
    under = [p - n * 0.004 * L for p in row]
    verts.extend(row + under)
    if i > 0:
        b = i * 6
        a = (i - 1) * 6
        for k in range(2):
            faces.append((a + k, b + k, b + k + 1, a + k + 1))       # top
            faces.append((a + k + 3, a + k + 4, b + k + 4, b + k + 3))  # under
        faces.append((a, a + 3, b + 3, b))                            # left wall
        faces.append((a + 2, b + 2, b + 5, a + 5))                    # right wall
# end caps
faces.append((0, 1, 4, 3))
faces.append((1, 2, 5, 4))
b = (len(prof) - 1) * 6
faces.append((b, b + 3, b + 4, b + 1))
faces.append((b + 1, b + 4, b + 5, b + 2))

mesh = bpy.data.meshes.new("CrestStrip")
mesh.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
mesh.update()
crest = bpy.data.objects.new("CrestStrip", mesh)
bpy.context.scene.collection.objects.link(crest)
CW, _ = world_co(crest)
d_skull = nearest_dist(CW, SK)
d_tissue = nearest_dist(CW, TW2)
report["CrestStrip"] = {
    "verts": len(verts), "stations": len(prof),
    "raise_L": RAISE,
    "min_dist_to_skull": float(d_skull.min()),
    "min_dist_to_tissue": float(d_tissue.min()),
    "profile": np.round(prof, 4).tolist(),
}

bpy.ops.wm.save_as_mainfile(filepath=str(CHAR / "work" / "stage2.blend"))
(CHAR / "work" / "stage2.json").write_text(json.dumps(report, indent=1))
print(json.dumps(report, indent=1))
print("STAGE 2 DONE")
