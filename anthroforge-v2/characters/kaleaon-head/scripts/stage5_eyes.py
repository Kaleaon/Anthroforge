#!/usr/bin/env python3
"""Kaleaon head Phase 2 - Stage 5: eyes + nose (spec S8.5).

EyeSize/EyeSpacing (builder machinery, side from position) + the
OrbitHeight assembly shift (the band field's peak delta, applied to
the assemblies as a pure z shift - skull/muscles/tissue took the same
field as a band in stages 2/3). Lid rest coverage measured before and
after by anterior projection. Nose: carried to the deformed muzzle by
the material-point seat delta (builder's ear method; base tissue read
from the stage-2 checkpoint), then the builder's NoseSize scale.

    blender -b --threads 2 --python stage5_eyes.py
In:  work/stage4.blend (+ stage2.blend for base tissue)
Out: work/stage5.blend + work/stage5.json
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
V = {k: float(v) for k, v in json.loads(
    (CHAR / "scripts" / "kaleaon_vector.json").read_text()).items()
    if isinstance(v, (int, float))}
AUD = json.loads((CHAR / "work" / "audit.json").read_text())
L = AUD["landmarks"]["L"]

bpy.ops.wm.open_mainfile(filepath=str(CHAR / "work" / "stage4.blend"))
objs = {o.name: o for o in bpy.data.objects if o.type == "MESH"}
report = {}

# base tissue (for the nose seat delta) from the stage-2 checkpoint
with bpy.data.libraries.load(str(CHAR / "work" / "stage2.blend")) as (src, dst):
    dst.objects = ["TissueHead"]
base_tissue_obj = dst.objects[0]
TW_base, _ = world_co(base_tissue_obj)
bpy.data.objects.remove(base_tissue_obj, do_unlink=True)
TW_cur, _ = world_co(objs["TissueHead"])


def lid_coverage(s):
    IR, _ = world_co(objs[f"Iris_{s}"])
    LD, _ = world_co(objs[f"Eyelid_{s}"])
    cov = 0
    for p in IR:
        d2 = (LD[:, 0] - p[0]) ** 2 + (LD[:, 2] - p[2]) ** 2
        j = int(np.argmin(d2))
        if d2[j] < (0.015 * L) ** 2 and LD[j, 1] > p[1] - 0.005 * L:
            cov += 1
    return cov / len(IR)


report["lid_coverage_before"] = {s: lid_coverage(s) for s in ("L", "R")}

# ---- eyes
eye_c = {}
for s in ("L", "R"):
    W0, _ = world_co(objs[f"Eyeball_{s}"])
    eye_c[s] = W0.mean(axis=0)
LM = {"L": L, "orbit_height_base": AUD["landmarks"]["orbit_height_L"]}
d_oh = F.orbit_height_delta(V, LM)
report["orbit_height_delta_L"] = float(d_oh)
d_eye = (V["EyeSpacing"] / 100.0) * 0.08 / 2.0 * L
f_eye = F.ratio_factor(0.15, 0.10, V["EyeSize"])
for s in ("L", "R"):
    c = eye_c[s].copy()
    side = 1.0 if eye_c[s][0] >= 0 else -1.0
    c[0] += side * d_eye
    c[2] += d_oh
    for part in ("Eyeball", "Iris", "Pupil", "Eyelid", "LidMargin"):
        o = objs[f"{part}_{s}"]
        W2, M2 = world_co(o)
        W2 = c + (W2 - eye_c[s]) * f_eye
        set_world(o, W2, M2)
report["eye"] = {"spacing_delta_per_side_L": float(d_eye),
                 "size_factor": float(f_eye)}
report["lid_coverage_after"] = {s: lid_coverage(s) for s in ("L", "R")}

# closure budget: upper margin lowest point vs lower margin highest
for s in ("L", "R"):
    MG, _ = world_co(objs[f"LidMargin_{s}"])
    IR, _ = world_co(objs[f"Iris_{s}"])
    cx = IR[:, 0].mean()
    near = MG[np.abs(MG[:, 0] - cx) < 0.35 * np.ptp(IR[:, 0])]
    upper = near[near[:, 2] > IR[:, 2].mean()]
    lower = near[near[:, 2] <= IR[:, 2].mean()]
    report.setdefault("closure", {})[s] = {
        "upper_margin_min_z": float(upper[:, 2].min()) if len(upper) else None,
        "lower_margin_max_z": float(lower[:, 2].max()) if len(lower) else None,
        "gap_to_close_L": (float(upper[:, 2].min() - lower[:, 2].max())
                           if len(upper) and len(lower) else None),
        "iris_diameter_L": float(np.ptp(IR[:, 2])),
    }

# ---- nose: seat delta then builder scale
nose = objs["NoseLeather"]
NW, NM = world_co(nose)
nc = NW.mean(axis=0)
idx0 = int(np.argmin(np.linalg.norm(TW_base - nc, axis=1)))
seat_delta = TW_cur[idx0] - TW_base[idx0]
NW = NW + seat_delta
nc = NW.mean(axis=0)
f = F.ratio_factor(0.55, 0.30, V["NoseSize"])
NW = nc + (NW - nc) * np.array([f, 1.0 + (f - 1.0) * 0.5,
                                1.0 + (f - 1.0) * 0.5])
set_world(nose, NW, NM)
report["nose"] = {"seat_delta": np.round(seat_delta, 4).tolist(),
                  "size_factor": float(f)}

bpy.ops.wm.save_as_mainfile(filepath=str(CHAR / "work" / "stage5.blend"))
(CHAR / "work" / "stage5.json").write_text(json.dumps(report, indent=1))
print(json.dumps(report, indent=1))
print("STAGE 5 DONE")
