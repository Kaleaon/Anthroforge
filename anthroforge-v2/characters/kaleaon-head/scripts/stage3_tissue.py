#!/usr/bin/env python3
"""Kaleaon head Phase 2 - Stage 3: tissue + jaw (spec S8.3).

Full builder tissue stack + whisker pads on TissueHead; jaw set +
chin mass on Jaw. THE LIP LINE IS ONE STRUCTURE: the v5 cage's rim is
shared by both shells, but the tissue and jaw field stacks move it
differently (measured tear up to 0.034 L at the front rim:
MuzzleLength -25 retracts the upper lip, JawLength 0 leaves the lower
lip behind). The jaw's cage verts are therefore recomputed as a blend
from their BASE positions - rim rows take the tissue transform
verbatim (the same composition the tissue cage received, pads
included, so coincident base pairs land coincident), grading to the
jaw-field position across the strip by base distance to the rim.
Then the smile-line path is shaped into the cage (rim pairs at their
midpoint + path lift, margins graded - the v5 cage's convention).

Fold reporting is split: the cage strip's tucked margins double back
on themselves BY DESIGN (the v5 base itself carries 244/227 adjacent
pairs below 0.01 inside that structure, 0 nonmanifold, 0 inconsistent)
- the fold gate is therefore reported for the EXTERIOR surface (pairs
involving no cage face) with the cage-zone counts alongside.

    blender -b --threads 2 --python stage3_tissue.py
In:  work/stage2.blend
Out: work/stage3.blend + work/stage3.json
"""
import json
import sys
from pathlib import Path

import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import kaleaon_fields as F
from kaleaon_io import fold_stats, group_weights, set_world, world_co

CHAR = Path(__file__).resolve().parents[1]
V = {k: float(v) for k, v in json.loads(
    (CHAR / "scripts" / "kaleaon_vector.json").read_text()).items()
    if isinstance(v, (int, float))}

bpy.ops.wm.open_mainfile(filepath=str(CHAR / "work" / "stage2.blend"))
objs = {o.name: o for o in bpy.data.objects if o.type == "MESH"}
tis, jaw = objs["TissueHead"], objs["Jaw"]

TW0, TM = world_co(tis)
JW0, JM = world_co(jaw)
EL, _ = world_co(objs["Eyeball_L"])
ER, _ = world_co(objs["Eyeball_R"])
TU, _ = world_co(objs["TeethUpper"])
LM = F.landmarks(TW0, EL, ER, np.array(jaw.matrix_world)[:3, 3], TU)
L = LM["L"]
report = {}

# rim pairs from the BASE cage (vertex indices are stable across stages)
tcage = np.where(group_weights(tis, "LipCage") > 0)[0]
jcage = np.where(group_weights(jaw, "LipCage") > 0)[0]
TP0, JP0 = TW0[tcage], JW0[jcage]
d0 = np.sqrt(((TP0[:, None, :] - JP0[None, :, :]) ** 2).sum(-1))
jmin0 = d0.argmin(axis=1)
rim_t = np.where(d0[np.arange(len(TP0)), jmin0] < 0.0005)[0]
rim_j = jmin0[rim_t]
report["rim_pairs_base"] = int(len(rim_t))
# jaw cage grading: base distance to the nearest jaw rim vert
rim_pts_j = JP0[rim_j]
dj = np.sqrt(((JP0[:, None, :] - rim_pts_j[None, :, :]) ** 2).sum(-1)).min(axis=1)
grade_j = np.exp(-((dj / (0.016 * L)) ** 2))

# ---- margin separation pass (v5's own construction discipline:
# the two margin strips keep >= 0.0035 clearance; the cage blend can
# shear jaw margins across the tuck gap - measured 33 crossings on the
# undeformed base with this counter, concentrated at the commissure
# poles). Jaw margins dive away from the tissue margins, capped steps.
from mathutils import Vector as _V
from mathutils.bvhtree import BVHTree as _BVH


def margin_faces(o, cage_idx, rim_set):
    keep = set(int(i) for i in cage_idx)
    tris = []
    for p in o.data.polygons:
        idx = list(p.vertices)
        if all(v in keep for v in idx) and not all(v in rim_set for v in idx):
            for k in range(1, len(idx) - 1):
                tris.append((idx[0], idx[k], idx[k + 1]))
    return tris


def margin_crossings():
    TWx, _ = world_co(tis)
    JWx, _ = world_co(jaw)
    rim_t_set = set(int(tcage[i]) for i in rim_t)
    rim_j_set = set(int(jcage[i]) for i in rim_j)
    TT = margin_faces(tis, tcage, rim_t_set)
    JT = margin_faces(jaw, jcage, rim_j_set)
    ta = _BVH.FromPolygons([_V(v) for v in TWx], TT, all_triangles=True)
    tb = _BVH.FromPolygons([_V(v) for v in JWx], JT, all_triangles=True)
    return len(ta.overlap(tb))




def separation_pass(rounds=8):  # TRIED, NOT SHIPPED - see KALEAON_HEAD_BUILD.md (both this and a vertex-distance version failed to reduce crossings; reverted)
    """Signed-distance pass: jaw margin verts are placed >= 0.0035
    from the tissue margin SURFACE (BVH nearest triangle + normal),
    on the side the majority of them already occupy. (A vertex-to-
    vertex version of this pass measured no improvement - crossings
    are triangle-level, so the correction has to be too.)"""
    rim_j_set = set(int(jcage[i]) for i in rim_j)
    rim_t_set = set(int(tcage[i]) for i in rim_t)
    movers = np.array([int(jcage[i]) for i in range(len(jcage))
                       if int(jcage[i]) not in rim_j_set])
    TWx, _ = world_co(tis)
    TT = margin_faces(tis, tcage, rim_t_set)
    tree = _BVH.FromPolygons([_V(v) for v in TWx], TT, all_triangles=True)
    JWx, JMx = world_co(jaw)
    # reference side from the current (pre-pass) configuration
    signs = []
    for vi in movers:
        hit = tree.find_nearest(_V(JWx[vi]))
        if hit and hit[3] > 0.002:
            signs.append(float(np.sign(np.dot(
                JWx[vi] - np.array(hit[0]), np.array(hit[1])))))
    S = 1.0 if np.median(signs) >= 0 else -1.0
    for _ in range(rounds):
        JWx, JMx = world_co(jaw)
        moved = 0
        for vi in movers:
            hit = tree.find_nearest(_V(JWx[vi]))
            if not hit:
                continue
            loc = np.array(hit[0])
            nrm = np.array(hit[1])
            sd = S * float(np.dot(JWx[vi] - loc, nrm))
            if sd < 0.0035:
                step = min(0.0035 - sd, 0.004)
                JWx[vi] = JWx[vi] + S * step * nrm
                moved += 1
        set_world(jaw, JWx, JMx)
        if not moved:
            break



report["margin_crossings_base"] = margin_crossings()

# ---- tissue: full stack + whisker pads
W = F.tissue_fields(TW0.copy(), V, LM)
W = F.whisker_pads(W, LM)
set_world(tis, W, TM)

# ---- jaw: jaw set + chin mass
W = F.jaw_fields(JW0.copy(), V, LM)
chin_w = group_weights(jaw, "Chin")
ant = F.sstep(W[:, 1], 0.05 * L, 0.30 * L)
W[:, 2] = W[:, 2] - 0.010 * L * chin_w * ant
W[:, 1] = W[:, 1] + 0.003 * L * chin_w * ant
report["chin_mass"] = {"group_verts": int((chin_w > 0).sum()),
                       "max_drop_L": 0.010}
# ---- jaw cage: blend toward the tissue transform (lip line unity)
JC_tissue = F.whisker_pads(F.tissue_fields(JW0[jcage].copy(), V, LM), LM)
W[jcage] = grade_j[:, None] * JC_tissue + (1.0 - grade_j)[:, None] * W[jcage]
set_world(jaw, W, JM)
report["jaw_cage_blend"] = {
    "rim_grade_1.0_count": int((grade_j > 0.999).sum()),
    "cage_verts": int(len(jcage))}

report["margin_crossings_after_blend"] = margin_crossings()

# ---- smile-line path
TW2, _ = world_co(tis)
JW2, _ = world_co(jaw)
TP, JP = TW2[tcage], JW2[jcage]
d = np.sqrt(((TP[:, None, :] - JP[None, :, :]) ** 2).sum(-1))
pair_d = d[rim_t, rim_j]
report["smile"] = {"rim_gap_before_max": float(pair_d.max()),
                   "rim_gap_before_mean": float(pair_d.mean())}


def smile_dz(x):
    return 0.010 * L * F.sstep(np.abs(x), 0.10 * L, 0.2285 * L) ** 2


TPn, JPn = TP.copy(), JP.copy()
for k in range(len(rim_t)):
    i, j = rim_t[k], rim_j[k]
    mid = 0.5 * (TP[i] + JP[j]) + np.array([0.0, 0.0,
                                           smile_dz(TP[i][0])])
    TPn[i] = mid
    JPn[j] = mid
rim_pts = TPn[rim_t]
for P, Pn in ((TP, TPn), (JP, JPn)):
    dd = np.sqrt(((P[:, None, :] - rim_pts[None, :, :]) ** 2).sum(-1)).min(axis=1)
    grade = 0.35 + 0.65 * np.exp(-((dd / (0.012 * L)) ** 2))
    Pn[:, 2] = Pn[:, 2] + smile_dz(P[:, 0]) * grade
TW3, JW3 = TW2.copy(), JW2.copy()
TW3[tcage] = TPn
JW3[jcage] = JPn
set_world(tis, TW3, TM)
set_world(jaw, JW3, JM)
TW4, _ = world_co(tis)
JW4, _ = world_co(jaw)
d2 = np.sqrt(((TW4[tcage][:, None, :] - JW4[jcage][None, :, :]) ** 2).sum(-1))
report["smile"]["rim_gap_after_max"] = float(
    d2[rim_t, rim_j].max())
report["smile"]["max_lift_L"] = 0.010
report["margin_crossings_final"] = margin_crossings()


# ---- fold stats, split exterior / cage-zone
report["fold"] = {"TissueHead": fold_stats(tis, tcage),
                  "Jaw": fold_stats(jaw, jcage)}

bpy.ops.wm.save_as_mainfile(filepath=str(CHAR / "work" / "stage3.blend"))
(CHAR / "work" / "stage3.json").write_text(json.dumps(report, indent=1))
print(json.dumps(report, indent=1))
print("STAGE 3 DONE")
