#!/usr/bin/env python3
"""Kaleaon head Phase 2 - Stage 4: mouth machine (spec S8.4).

Teeth follow (builder's metric follow, verbatim), felid canine
emphasis (the v5 arcades are generic-plan: upper canine crowns read
0.019 L against 0.037 L premolars - felid plan wants canines dominant),
tongue re-proportioned to spec S5.3 (0.55 W wide, 0.98 W long; the
base tongue measures 0.66 W / 1.39 W), throat follow, then the
jaw-open battery: BVH teeth overlaps at -10/-20/-30 (S17), cage vs
teeth and cage vs cage, tongue containment. Poses are test-only; the
saved checkpoint stays at rest (v5 pattern).

    blender -b --threads 2 --python stage4_mouth.py
In:  work/stage3.blend (+ base landmarks from work/audit.json)
Out: work/stage4.blend + work/stage4.json
"""
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, str(Path(__file__).parent))
import kaleaon_fields as F
from kaleaon_io import world_co, set_world

CHAR = Path("/home/hatch/workspace/anthroforge-v2/characters/kaleaon-head")
V = {k: float(v) for k, v in json.loads(
    (CHAR / "scripts" / "kaleaon_vector.json").read_text()).items()
    if isinstance(v, (int, float))}
AUD = json.loads((CHAR / "work" / "audit.json").read_text())
LMb = AUD["landmarks"]
L = LMb["L"]
eye_y, eye_z, pal_z = LMb["eye_centre_mid"][1], LMb["eye_centre_mid"][2], LMb["pal_z"]
nose_y = LMb["nose_y"]
hinge = np.array(LMb["hinge"])

bpy.ops.wm.open_mainfile(filepath=str(CHAR / "work" / "stage3.blend"))
objs = {o.name: o for o in bpy.data.objects if o.type == "MESH"}
report = {}

f_ml = F.ratio_factor(0.33, 0.20, V["MuzzleLength"])
f_mw = F.ratio_factor(0.17, 0.08, V["MuzzleWidth"])
f_md = F.ratio_factor(0.20, 0.10, V["MuzzleDepth"])
f_jl = F.ratio_factor(0.74, 0.10, V["JawLength"])

# ---- TeethUpper: metric follow (builder, verbatim)
tu = objs["TeethUpper"]
EW, EM_tu = world_co(tu)
EM = EM_tu
ey0, ex0, ez0 = EW[:, 1].copy(), EW[:, 0].copy(), EW[:, 2].copy()
em = F.sstep(ey0, eye_y - 0.02 * L, eye_y + 0.10 * L)
EW[:, 1] = eye_y + (ey0 - eye_y) * (1.0 + (f_ml - 1.0) * em)
tpw_t = 0.55 + 0.45 * F.sstep(ey0, eye_y, nose_y)
EW[:, 0] = ex0 * (1.0 + (f_mw - 1.0) * em * tpw_t)
EW[:, 0] = EW[:, 0] * (1.0 + (-0.004 * V["MuzzleTaper"])
                       * F.sstep(ey0, eye_y + 0.05 * L, nose_y - 0.02 * L) * em)
EW[:, 2] = pal_z + (ez0 - pal_z) * (1.0 + (f_md - 1.0) * em)
set_world(tu, EW, EM)
report["teeth_follow"] = {"f_ml": f_ml, "f_mw": f_mw, "f_md": f_md,
                          "f_jl": f_jl}

# ---- TeethLower: JawLength about the hinge (builder)
tl = objs["TeethLower"]
EW, EM = world_co(tl)
EW[:, 1] = hinge[1] + (EW[:, 1] - hinge[1]) * f_jl
set_world(tl, EW, EM)

# ---- Throat: half-follow (builder)
th = objs["Throat"]
HW, HMx = world_co(th)
HW[:, 1] = hinge[1] + (HW[:, 1] - hinge[1]) * (1.0 + (f_jl - 1.0) * 0.5)
set_world(th, HW, HMx)


# ---- island analysis (topology is unchanged by the follows)
def islands(o):
    n = len(o.data.vertices)
    parent = list(range(n))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for e in o.data.edges:
        a, b = find(e.vertices[0]), find(e.vertices[1])
        if a != b:
            parent[a] = b
    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    return list(groups.values())


def mesh_tris(o, W=None):
    if W is None:
        W, _ = world_co(o)
    tris = []
    for p in o.data.polygons:
        idx = list(p.vertices)
        for k in range(1, len(idx) - 1):
            tris.append((idx[0], idx[k], idx[k + 1]))
    return W, tris


def bvh_of(W, tris):
    return BVHTree.FromPolygons([Vector(v) for v in W], tris,
                                all_triangles=True)


def teeth_check():
    UW, UT = mesh_tris(objs["TeethUpper"])
    LW, LT = mesh_tris(objs["TeethLower"])
    tu_tree = bvh_of(UW, UT)
    out = {}
    for deg in (0, -10, -20, -30):
        th = math.radians(deg)
        R = np.array([[1, 0, 0],
                      [0, math.cos(th), -math.sin(th)],
                      [0, math.sin(th), math.cos(th)]])
        lv = (LW - hinge) @ R.T + hinge
        tl_tree = bvh_of(lv, LT)
        ov = tu_tree.overlap(tl_tree)
        dmin = 1e9
        for p in lv:
            hit = tu_tree.find_nearest(Vector(p))
            if hit and hit[3] < dmin:
                dmin = hit[3]
        out[str(deg)] = {"overlap_pairs": len(ov),
                         "min_clearance_L": round(float(dmin), 5)}
    return out


report["teeth_before_canine"] = teeth_check()

# ---- felid canine emphasis
UW, _ = world_co(tu)
isl = islands(tu)
canine_idx = []
for idxs in isl:
    P = UW[idxs]
    if len(idxs) == 20 and abs(P[:, 0].mean()) > 0.05:
        canine_idx.append(idxs)
report["canine_islands"] = [len(i) for i in canine_idx]
assert len(canine_idx) == 2, "expected the two 20-vert canine islands"

shipped = None
for stretch in (1.9, 1.6, 1.35):
    UW2 = UW.copy()
    for idxs in canine_idx:
        P = UW2[idxs]
        ztop = P[:, 2].max()
        c = P.mean(axis=0)
        P[:, 2] = ztop - (ztop - P[:, 2]) * stretch
        P[:, 0] = c[0] + (P[:, 0] - c[0]) * 1.08
        P[:, 1] = c[1] + (P[:, 1] - c[1]) * 1.08
        UW2[idxs] = P
    set_world(tu, UW2, EM_tu)
    chk = teeth_check()
    ok = all(chk[str(d)]["overlap_pairs"] == 0 for d in (-10, -20, -30))
    report[f"canine_stretch_{stretch}"] = chk
    if ok:
        shipped = stretch
        break
report["canine_stretch_shipped"] = shipped
UW3, _ = world_co(tu)
can_h = []
for idxs in canine_idx:
    P = UW3[idxs]
    can_h.append(float(P[:, 2].max() - P[:, 2].min()))
report["canine_height_after_L"] = can_h

# lower canines: crown-lift field on the fused front island region
LW, LMtx = world_co(tl)
w = F.sstep(np.abs(LW[:, 0]), 0.05 * L, 0.08 * L) \
    * (1.0 - F.sstep(np.abs(LW[:, 0]), 0.14 * L, 0.17 * L)) \
    * F.sstep(LW[:, 1], 0.23 * L, 0.27 * L) \
    * (1.0 - F.sstep(LW[:, 1], 0.34 * L, 0.38 * L)) \
    * F.sstep(LW[:, 2], -0.315 * L, -0.29 * L)
LW[:, 2] = LW[:, 2] + 0.014 * L * w
set_world(tl, LW, LMtx)
report["lower_canine_lift"] = {"verts_moved": int((w > 0.01).sum()),
                               "amp_L": 0.014}
report["teeth_after_canine"] = teeth_check()

def pose(W, deg):
    th = math.radians(deg)
    R = np.array([[1, 0, 0],
                  [0, math.cos(th), -math.sin(th)],
                  [0, math.sin(th), math.cos(th)]])
    return (W - hinge) @ R.T + hinge


# ---- tongue re-proportion (spec S5.3: 0.55 W x 0.98 W) + seating
# The base tongue crosses the lower arcade's inner wall (measured on
# the undeformed v5 base below as the inheritance baseline). After
# re-proportioning, search a small (width, drop) neighbourhood of the
# spec point for a seat with 0 tongue/teeth crossings at all angles;
# ship the closest-to-spec seat that clears, and report the search.
tg = objs["Tongue"]
TG, TMtx = world_co(tg)
UW4, _ = world_co(tu)
arcade_W = float(np.ptp(UW4[:, 0]))
before = {"width_over_W": float(np.ptp(TG[:, 0]) / arcade_W),
          "length_over_W": float(np.ptp(TG[:, 1]) / arcade_W)}
anchor = np.array([TG[:, 0].mean(), np.percentile(TG[:, 1], 15),
                   TG[:, 2].mean()])
sy = (0.98 * arcade_W) / np.ptp(TG[:, 1])


def tongue_teeth_pairs(TGv):
    LWt, LTt = mesh_tris(objs["TeethLower"])
    UWt, UTt = mesh_tris(objs["TeethUpper"])
    _, TGt = mesh_tris(tg, TGv)
    tl_tree0 = bvh_of(LWt, LTt)
    tu_tree0 = bvh_of(UWt, UTt)
    tot = 0
    for deg in (0, -10, -20, -30):
        tgp = pose(TGv, deg) if deg else TGv
        tg_tree = bvh_of(tgp, TGt)
        tot += len(tg_tree.overlap(tl_tree0)) \
            + len(tg_tree.overlap(tu_tree0))
    return tot


report["tongue_base_inheritance"] = tongue_teeth_pairs(TG)
seat = None
for wfrac, drop in ((0.55, 0.0), (0.55, 0.008), (0.52, 0.008),
                    (0.52, 0.016), (0.50, 0.016), (0.48, 0.024)):
    sx = (wfrac * arcade_W) / np.ptp(TG[:, 0])
    TG2 = anchor + (TG - anchor) * np.array([sx, sy, 1.0])
    TG2[:, 2] = TG2[:, 2] - drop * L
    pairs = tongue_teeth_pairs(TG2)
    report.setdefault("tongue_seat_search", []).append(
        {"width_over_W": wfrac, "drop_L": drop, "pairs_all_angles": pairs})
    if pairs == 0 and seat is None:
        seat = (wfrac, drop, TG2)
if seat is None:
    wfrac, drop = 0.55, 0.0
    sx = (wfrac * arcade_W) / np.ptp(TG[:, 0])
    TG2 = anchor + (TG - anchor) * np.array([sx, sy, 1.0])
    seat = (wfrac, drop, TG2)
set_world(tg, seat[2], TMtx)
TG3, _ = world_co(tg)
report["tongue"] = {"arcade_W_L": arcade_W / L, "before": before,
                    "after": {"width_over_W": float(np.ptp(TG3[:, 0]) / arcade_W),
                              "length_over_W": float(np.ptp(TG3[:, 1]) / arcade_W)},
                    "seat_width_frac": seat[0], "seat_drop_L": seat[1]}

# ---- full mouth battery at angles
from kaleaon_io import group_weights


def submesh(o, vert_idx):
    """Faces whose verts all lie in vert_idx, with those verts."""
    keep = set(int(i) for i in vert_idx)
    W, _ = world_co(o)
    tris = []
    for p in o.data.polygons:
        idx = list(p.vertices)
        if all(v in keep for v in idx):
            for k in range(1, len(idx) - 1):
                tris.append((idx[0], idx[k], idx[k + 1]))
    return W, tris


def pose(W, deg):
    th = math.radians(deg)
    R = np.array([[1, 0, 0],
                  [0, math.cos(th), -math.sin(th)],
                  [0, math.sin(th), math.cos(th)]])
    return (W - hinge) @ R.T + hinge


tis, jaw = objs["TissueHead"], objs["Jaw"]
tcage = np.where(group_weights(tis, "LipCage") > 0)[0]
jcage = np.where(group_weights(jaw, "LipCage") > 0)[0]


def margin_submesh(o, cage_idx):
    """Cage faces excluding the all-rim faces: the rim rows are exact
    duplicates across the shells at rest, so their triangles trivially
    'overlap' - v5's margin tests excluded them, and so does this one.
    Rim verts are identified by their base coincidence (stage 3)."""
    import numpy as _np
    rim = set()
    W0, _ = world_co(o)
    other = objs["Jaw"] if o is tis else objs["TissueHead"]
    ocage = _np.where(group_weights(other, "LipCage") > 0)[0]
    OW, _ = world_co(other)
    OP = OW[ocage]
    P = W0[cage_idx]
    d = _np.sqrt(((P[:, None, :] - OP[None, :, :]) ** 2).sum(-1)).min(axis=1)
    rim = set(int(cage_idx[i]) for i in _np.where(d < 0.0005)[0])
    keep = set(int(i) for i in cage_idx)
    tris = []
    for p in o.data.polygons:
        idx = list(p.vertices)
        if all(v in keep for v in idx) and not all(v in rim for v in idx):
            for k in range(1, len(idx) - 1):
                tris.append((idx[0], idx[k], idx[k + 1]))
    return W0, tris


TCW, TCT = margin_submesh(tis, tcage)
JCW, JCT = margin_submesh(jaw, jcage)
UW5, UT5 = mesh_tris(tu)
LW5, LT5 = mesh_tris(tl)
TGW, TGT = mesh_tris(tg)
TIW, TIT = mesh_tris(tis)
JAW_W, JAW_T = mesh_tris(jaw)
battery = {}
for deg in (0, -10, -20, -30):
    tc_tree = bvh_of(TCW, TCT)
    jc_tree = bvh_of(pose(JCW, deg), JCT)
    tu_tree = bvh_of(UW5, UT5)
    tl_tree = bvh_of(pose(LW5, deg), LT5)
    tg_tree = bvh_of(pose(TGW, deg), TGT)
    ti_tree = bvh_of(TIW, TIT)
    jw_tree = bvh_of(pose(JAW_W, deg), JAW_T)
    battery[str(deg)] = {
        "tissueCage_vs_teethLower": len(tc_tree.overlap(tl_tree)),
        "jawCage_vs_teethUpper": len(jc_tree.overlap(tu_tree)),
        "cage_vs_cage": len(tc_tree.overlap(jc_tree)),
        "tongue_vs_tissue": len(tg_tree.overlap(ti_tree)),
        "tongue_vs_jaw": len(tg_tree.overlap(jw_tree)),
        "tongue_vs_teethUpper": len(tg_tree.overlap(tu_tree)),
        "tongue_vs_teethLower": len(tg_tree.overlap(tl_tree)),
    }
report["mouth_battery"] = battery

bpy.ops.wm.save_as_mainfile(filepath=str(CHAR / "work" / "stage4.blend"))
(CHAR / "work" / "stage4.json").write_text(json.dumps(report, indent=1))
print(json.dumps(report, indent=1))
print("STAGE 4 DONE")
