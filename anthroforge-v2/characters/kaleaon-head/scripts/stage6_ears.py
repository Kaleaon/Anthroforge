#!/usr/bin/env python3
"""Kaleaon head Phase 2 - Stage 6: ears (spec S8.6).

The builder's ear machinery verbatim (seat by material-point delta
against the deformed tissue, side from the part's own position,
EarLength/EarWidth ratio factors, EarTipPoint pinch [E] map, EarTilt
pitch, EarSpread, EarBaseHeight shift), vector EarLength -30 /
EarWidth -20 / EarTipPoint -60 driving the ear_round read. Then the
EarTipHeight station: judged against the additive expectation
(base tip height + (species - neutral) = 0.6296 - 0.16 = 0.4696
absolute; the skull-frame absolute 0.14 and the proportional 0.294
are both reported in the build doc - see the frame note there), with
a bounded base-z nudge if the composed fields land outside +-6%.

    blender -b --threads 2 --python stage6_ears.py
In:  work/stage5.blend (+ stage2.blend for base tissue)
Out: work/stage6.blend + work/stage6.json
"""
import json
import math
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
pal_z = AUD["landmarks"]["pal_z"]

bpy.ops.wm.open_mainfile(filepath=str(CHAR / "work" / "stage5.blend"))
objs = {o.name: o for o in bpy.data.objects if o.type == "MESH"}
with bpy.data.libraries.load(str(CHAR / "work" / "stage2.blend")) as (src, dst):
    dst.objects = ["TissueHead"]
base_tissue_obj = dst.objects[0]
TW, _ = world_co(base_tissue_obj)          # pre-deformation tissue
bpy.data.objects.remove(base_tissue_obj, do_unlink=True)
TW2, _ = world_co(objs["TissueHead"])      # deformed tissue
L_now = float(TW2[:, 1].max() - TW2[:, 1].min())
report = {"L_built": L_now}

TIP_TARGET_ABS = 0.6295790523290634 - 0.16   # additive expectation


def ear_measure(ear, base_pt, tip_idx):
    """Measure with the TRACKED tip vertex: on this shell-shaped ear
    a post-hoc argmax-from-quartile picks a bottom corner once the
    ear is re-seated (measured failure), so the tip is the vertex the
    builder's axis was built from, followed by index."""
    EW, _ = world_co(ear)
    tip = EW[tip_idx]
    return {"base": base_pt, "tip": tip,
            "length": float(np.linalg.norm(tip - base_pt)),
            "tip_height_abs": float(tip[2] - pal_z),
            "tip_height_L": float((tip[2] - pal_z) / L_now),
            "bbox": np.round(np.ptp(EW, axis=0), 4).tolist()}


for sname in ("L", "R"):
    ear = objs[f"Ear_{sname}"]
    EW2, EM2 = world_co(ear)
    d = np.sqrt(((EW2[:, None, :] - TW2[None, :, :]) ** 2).sum(-1)).min(axis=1)
    base_mask = d < np.percentile(d, 25)
    base = EW2[base_mask].mean(axis=0)
    idx0 = int(np.argmin(np.linalg.norm(TW - base, axis=1)))
    seat_delta = TW2[idx0] - TW[idx0]
    tip_idx = int(np.argmax(np.linalg.norm(EW2 - base, axis=1)))
    tip = EW2[tip_idx]
    axis = tip - base
    axis = axis / np.linalg.norm(axis)
    rel = EW2 - base
    t = rel @ axis
    tmax = float(t.max())
    side = 1.0 if base[0] >= 0 else -1.0
    # EarLength (builder key EarHeight)
    f = F.ratio_factor(0.40, 0.65, V["EarHeight"])
    rel = (rel - np.outer(t, axis)) + np.outer(t * f, axis)
    # EarWidth
    f = F.ratio_factor(0.55, 0.35, V["EarWidth"])
    rel[:, 0] = rel[:, 0] * f
    # EarTipPoint
    tt = F.sstep(t / tmax, 0.70, 1.0)
    pinch = -0.006875 * V["EarTipPoint"]
    perp = rel - np.outer(rel @ axis, axis)
    rel = rel - perp * (pinch * tt)[:, None]
    if V["EarTipPoint"] < 0:
        rel = rel - np.outer(t * (-0.00075 * V["EarTipPoint"]) * tt, axis)
    # EarTilt pitch (builder map; -10 stays in the pitch range)
    pitch_val = max(V["EarTilt"], -30.0)
    ang = math.radians(0.35 * pitch_val)
    ca, sa = math.cos(ang), math.sin(ang)
    yy, zz = rel[:, 1].copy(), rel[:, 2].copy()
    rel[:, 1] = yy * ca - zz * sa
    rel[:, 2] = yy * sa + zz * ca
    # EarSpread
    base2 = base + seat_delta + np.array(
        [side * 0.0004 * V["EarSpread"] * 1.0, 0, 0])
    ang = math.radians(0.15 * V["EarSpread"] * side)
    ca, sa = math.cos(ang), math.sin(ang)
    xx, zz = rel[:, 0].copy(), rel[:, 2].copy()
    rel[:, 0] = xx * ca + zz * sa
    rel[:, 2] = -xx * sa + zz * ca
    # EarBaseHeight (builder key EarPlacementHeight)
    base2 = base2 + np.array([0, 0, 0.0008 * V["EarPlacementHeight"] * 1.0])
    set_world(ear, base2 + rel, EM2)
    m = ear_measure(ear, base2, tip_idx)
    # EarTipHeight bounded nudge (base-z shift, seat-checked)
    nudge = 0.0
    deficit = m["tip_height_abs"] - TIP_TARGET_ABS
    if abs(deficit) > 0.06 * TIP_TARGET_ABS:
        nudge = float(np.clip(-deficit, -0.02, 0.02))
        EW3, _ = world_co(ear)
        EW3[:, 2] = EW3[:, 2] + nudge
        set_world(ear, EW3, EM2)
        m = ear_measure(ear, base2 + np.array([0, 0, nudge]), tip_idx)
    m["nudge_L"] = nudge
    m["base"] = np.round(m["base"], 4).tolist()
    m["tip"] = np.round(m["tip"], 4).tolist()
    report[f"ear_{sname}"] = m

report["tip_target_abs_additive"] = TIP_TARGET_ABS
bpy.ops.wm.save_as_mainfile(filepath=str(CHAR / "work" / "stage6.blend"))
(CHAR / "work" / "stage6.json").write_text(json.dumps(report, indent=1))
print(json.dumps(report, indent=1))
print("STAGE 6 DONE")
