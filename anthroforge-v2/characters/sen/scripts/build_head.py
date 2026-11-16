#!/usr/bin/env python3
"""SEN — bear head build on neutral base head v3.

Applies Sen's head vector (presets-titan-batch1.md section 4.1 = bear
species vector section 1.3 + 7 character deltas) to
base-head-v3/neutral_base_head_v3.glb as smooth-field deformations.

CONVENTION (documented, load-bearing): the spec's preset values are
deltas from the SPEC neutral (ratio = neutral + t*span). v3 is not
exactly the spec neutral (its BUILD_NOTES document deliberate
deviations — interorbital 0.112 vs 0.19, ZB 0.547 vs 0.58). Sliders are
therefore applied as PROPORTIONAL changes from neutral:
factor = (neutral + t*span) / neutral for ratio sliders, preserving
v3's deliberate deviations while moving every measure the right amount
in the right direction. Index sliders use documented [E] mappings.

Slider coverage is reported per slider in work/head_measure.json as
full / partial / none — the honest geometry-path accounting the brief
requires.

Also: tongue scaled x1.3 (Sen canon, section 4.3) with an approximate
clearance report; forehead mark NOT applied (shape undescribed in the
person file — a fur-zone record in the character record, no geometry).

Run: HOME=/tmp/af_home xvfb-run blender -b --python build_head.py
"""
import json
import math
from pathlib import Path

import bpy
import numpy as np

HERE = Path(__file__).resolve().parent
SEN = HERE.parent
V2 = SEN.parent.parent
SRC = V2 / "base-head-v3/neutral_base_head_v3.glb"
WORK = SEN / "work"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(SRC))

objs = {o.name: o for o in bpy.data.objects if o.type == "MESH"}
print("head objects:", sorted(objs))


def world_co(o):
    M = np.array(o.matrix_world)
    co = np.empty(len(o.data.vertices) * 3)
    o.data.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    return co @ M[:3, :3].T + M[:3, 3], M


def set_world(o, W, M):
    Minv = np.linalg.inv(M)
    local = W @ Minv[:3, :3].T + Minv[:3, 3]
    o.data.vertices.foreach_set("co", local.ravel())
    o.data.update()


def sstep(x, a, b):
    t = np.clip((np.asarray(x, float) - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


# ------------------------------------------------------------ landmarks
tis = objs["TissueHead"]
TW, TM = world_co(tis)
L = float(TW[:, 1].max() - TW[:, 1].min())
nose_y = float(TW[:, 1].max())
occ_y = float(TW[:, 1].min())
eye_c = {}
for s in ("L", "R"):
    W, _ = world_co(objs[f"Eyeball_{s}"])
    eye_c[s] = W.mean(axis=0)
eye_mid = 0.5 * (eye_c["L"] + eye_c["R"])
eye_y, eye_z = float(eye_mid[1]), float(eye_mid[2])
eye_sep = float(abs(eye_c["L"][0] - eye_c["R"][0]))
orb_d = float(np.ptp(world_co(objs["Eyeball_L"])[0][:, 0]))
pal_z = eye_z - 0.172 * L        # OrbitHeight anchor from proportions.json
print(f"L={L:.3f} nose_y={nose_y:.3f} occ_y={occ_y:.3f} eye_y={eye_y:.3f} "
      f"eye_z={eye_z:.3f} eye_sep={eye_sep:.3f} orb_d={orb_d:.3f} "
      f"pal_z={pal_z:.3f}")

# Sen head vector (section 4.1; EarLength/EarBaseHeight are the section-5
# renames of EarHeight/EarPlacementHeight — EarLength values carry over,
# EarBaseHeight was re-anchored so its -25 is applied as a modest base
# lowering, flagged in the report)
V = {
    "MuzzleLength": 15, "MuzzleWidth": 40, "MuzzleTaper": -40,
    "MuzzleDepth": 40, "NoseSize": 35, "CraniumWidth": -10,
    "CraniumHeight": -20, "CraniumLength": 5, "StopAngle": 40,
    "ForeheadWidth": 25, "EarLength": -10, "EarWidth": 55,
    "EarBaseHeight": -25, "EarSpread": 40, "EarTilt": -20,
    "EarTipPoint": -80, "JawDepth": 25, "JawLength": -50,
    "JawWidth": 55, "CheekWidth": 10, "RuffVolume": 70,
    "EyeSize": -40, "EyeSpacing": 30, "EyeForwardness": 20,
    "BrowProjection": -20, "BrowThickness": -15, "BrowContinuity": -25,
    "BrowShelf": 25, "BrowPosition": -10, "BrowPadding": 25,
    "BrowScowl": 25,
}
PATH = {}


def ratio_factor(neutral, span, val):
    return (neutral + (val / 100.0) * span) / neutral


# ------------------------------------------------------- tissue fields
W = TW.copy()
y, z, x = W[:, 1], W[:, 2], W[:, 0]
muz = sstep(y, eye_y - 0.02 * L, eye_y + 0.10 * L)          # muzzle block
cran = 1.0 - sstep(y, eye_y - 0.16 * L, eye_y - 0.02 * L)   # posterior block
dome = sstep(z, eye_z + 0.02 * L, eye_z + 0.16 * L) * cran
zyg = np.exp(-((y - (eye_y - 0.02 * L)) / (0.10 * L)) ** 2) \
    * np.exp(-((z - (eye_z - 0.03 * L)) / (0.13 * L)) ** 2)  # zygomatic band
brow = np.exp(-((y - (eye_y + 0.015 * L)) / (0.055 * L)) ** 2) \
    * np.exp(-((z - (eye_z + 0.085 * L)) / (0.045 * L)) ** 2) \
    * (np.abs(x) < 0.24 * L)
stopb = np.exp(-((y - (eye_y - 0.01 * L)) / (0.045 * L)) ** 2) \
    * sstep(z, eye_z + 0.05 * L, eye_z + 0.14 * L)
neckr = (1.0 - sstep(z, pal_z + 0.10 * L, pal_z + 0.24 * L)) \
    * (1.0 - muz)                                            # cheek/neck ruff zone

# MuzzleLength +15: muzzle fraction .33 -> .36 (proportional +9.1% on
# the anterior block, pivoting at the orbit plane)
f = ratio_factor(0.33, 0.20, V["MuzzleLength"])
W[:, 1] = eye_y + (y - eye_y) * (1.0 + (f - 1.0) * muz)
PATH["MuzzleLength"] = "full"
# MuzzleWidth +40: rostrum W .17 -> .202 (+18.8%), canine-weighted
f = ratio_factor(0.17, 0.08, V["MuzzleWidth"])
tipw = 0.55 + 0.45 * sstep(y, eye_y, nose_y)
W[:, 0] = x * (1.0 + (f - 1.0) * muz * tipw)
PATH["MuzzleWidth"] = "full"
# MuzzleTaper -40: taper index .50 -> .34 = blunter tip: widen the tip
# relative to the base (+16% at the tip, fading to the stop)
tw = 1.0 + 0.16 * sstep(y, eye_y + 0.05 * L, nose_y - 0.02 * L) * muz
W[:, 0] = W[:, 0] * tw
PATH["MuzzleTaper"] = "partial — index slider, tip-widening field [E map]"
# MuzzleDepth +40: rostrum depth .20 -> .24 (+20%) about the palatal line
f = ratio_factor(0.20, 0.10, V["MuzzleDepth"])
W[:, 2] = pal_z + (z - pal_z) * (1.0 + (f - 1.0) * muz)
PATH["MuzzleDepth"] = "full"
# CraniumWidth -10 / Height -20 / Length +5
f = ratio_factor(0.36, 0.16, V["CraniumWidth"])
W[:, 0] = W[:, 0] * (1.0 + (f - 1.0) * cran * (1.0 - 0.5 * muz))
PATH["CraniumWidth"] = "full (proportional; dome-shell ruler mismatch noted in v3)"
f = ratio_factor(0.31, 0.12, V["CraniumHeight"])
W[:, 2] = eye_z + (W[:, 2] - eye_z) * (1.0 + (f - 1.0) * dome)
PATH["CraniumHeight"] = "full"
f = ratio_factor(0.62, 0.20, V["CraniumLength"])
W[:, 1] = np.where(W[:, 1] < eye_y,
                   eye_y + (W[:, 1] - eye_y) * (1.0 + (f - 1.0) * cran),
                   W[:, 1])
PATH["CraniumLength"] = "full"
# ForeheadWidth +25: frontal W .24 -> .27 (+12.5%) in the forehead band
f = ratio_factor(0.24, 0.12, V["ForeheadWidth"])
fh = np.exp(-((y - (eye_y + 0.01 * L)) / (0.07 * L)) ** 2) \
    * sstep(z, eye_z, eye_z + 0.10 * L)
W[:, 0] = W[:, 0] * (1.0 + (f - 1.0) * fh)
PATH["ForeheadWidth"] = "full"
# CheekWidth +10: ZB .58 -> .60 (+3.4%) on the zygomatic band
f = ratio_factor(0.58, 0.20, V["CheekWidth"])
W[:, 0] = W[:, 0] * (1.0 + (f - 1.0) * zyg)
PATH["CheekWidth"] = "full"
# StopAngle +40: stop index .30 -> .46: dip the dorsal stop band +
# pitch the muzzle block down 2.5 deg about the stop point [E map]
W[:, 2] = W[:, 2] - 0.020 * L * stopb
ang = math.radians(-2.5) * (V["StopAngle"] / 40.0)
ca, sa = math.cos(ang), math.sin(ang)
yy = W[:, 1] - eye_y
zz = W[:, 2] - (eye_z + 0.10 * L)
rot = muz > 0.5
W[rot, 1] = eye_y + yy[rot] * ca - zz[rot] * sa
W[rot, 2] = (eye_z + 0.10 * L) + yy[rot] * sa + zz[rot] * ca
PATH["StopAngle"] = "partial — index slider, dip+pitch field [E map]"
# Brow vector (band fields on tissue; skull layer does not exist as a
# separate mesh in the v3 GLB — the layer stack ships in the .blend,
# the GLB carries tissue only; noted in the report)
W[:, 1] = W[:, 1] + 0.0003 * V["BrowProjection"] * L * brow
# [E map: 0.0003 L per unit on the brow-study chord scale;
#  projection -20 -> brow band recedes 0.006 L]
PATH["BrowProjection"] = "partial — tissue-band recession; skull-layer torus N/A on a bear"
W[:, 2] = eye_z + (W[:, 2] - eye_z) * (1.0 - 0.03 * brow)
PATH["BrowThickness"] = "partial — band thinning field [E map]"
PATH["BrowContinuity"] = "none — no torus components exist on a non-hominin head to split/merge"
# BrowShelf +25: sulcus dip just above the brow line
sulc = np.exp(-((W[:, 2] - (eye_z + 0.135 * L)) / (0.030 * L)) ** 2) \
    * np.exp(-((W[:, 1] - (eye_y + 0.015 * L)) / (0.055 * L)) ** 2) \
    * (np.abs(W[:, 0]) < 0.24 * L)
W[:, 2] = W[:, 2] - 0.008 * L * sulc
PATH["BrowShelf"] = "partial — sulcus dip field [E map]"
W[:, 2] = W[:, 2] - 0.0028 * L * brow * (V["BrowPosition"] / -10.0) \
    * (1.0 if V["BrowPosition"] < 0 else -1.0)
PATH["BrowPosition"] = "partial — brow-line shift by the spec's mm anchor"
# BrowPadding +25: supraorbital tissue swell along +z/+y of the band
W[:, 2] = W[:, 2] + 0.004 * L * brow
W[:, 1] = W[:, 1] + 0.002 * L * brow
PATH["BrowPadding"] = "partial — band swell field [E map]"
# BrowScowl +25: medial brow depression (baked rest expression; the
# expression system owns this slider — baked approximation, flagged)
med = np.exp(-((np.abs(W[:, 0]) - 0.055 * L) / (0.045 * L)) ** 2) \
    * np.exp(-((W[:, 2] - (eye_z + 0.075 * L)) / (0.040 * L)) ** 2) \
    * np.exp(-((W[:, 1] - (eye_y + 0.02 * L)) / (0.05 * L)) ** 2)
W[:, 2] = W[:, 2] - 0.006 * L * med
W[:, 1] = W[:, 1] - 0.003 * L * med
PATH["BrowScowl"] = "partial — baked medial depression; expression system owns the live slider"
# RuffVolume +70: soft-tissue swell in the cheek/neck zone along the
# local radial direction (true ruff is fur; this is the under-fur mass)
rad = W[:, :2] - np.array([0.0, eye_y - 0.10 * L])
rad = rad / np.maximum(np.linalg.norm(rad, axis=1, keepdims=True), 1e-9)
W[:, 0] = W[:, 0] + 0.030 * L * neckr * rad[:, 0]
W[:, 2] = W[:, 2] - 0.018 * L * neckr
PATH["RuffVolume"] = "partial — tissue swell only; the ruff proper is the head fur groom (not built)"
set_world(tis, W, TM)

# ------------------------------------------------------------- jaw
jaw = objs["Jaw"]
JW, JM = world_co(jaw)
hinge = np.array(jaw.matrix_world)[:3, 3]
jy, jz, jx = JW[:, 1], JW[:, 2], JW[:, 0]
post = sstep(jy, eye_y - 0.05 * L, eye_y - 0.22 * L)   # posterior (ramus) weight
# JawDepth +25: ramus depth .28 -> .31 (+10.7%), posterior-weighted,
# downward from the hinge line
f = ratio_factor(0.28, 0.12, V["JawDepth"])
JW[:, 2] = hinge[2] + (jz - hinge[2]) * (1.0 + (f - 1.0) * post)
PATH["JawDepth"] = "full"
# JawWidth +55: jaw W .40 -> .477 (+19.3%), posterior-weighted
f = ratio_factor(0.40, 0.14, V["JawWidth"])
JW[:, 0] = jx * (1.0 + (f - 1.0) * (0.35 + 0.65 * post))
PATH["JawWidth"] = "full"
# JawLength -50: mandible .74 -> .69 (-6.8%) about the hinge
f = ratio_factor(0.74, 0.10, V["JawLength"])
JW[:, 1] = hinge[1] + (jy - hinge[1]) * f
PATH["JawLength"] = "full"
set_world(jaw, JW, JM)

# teeth slab: anterior follows muzzle length; lower follows jaw length
te = objs["TeethArcade"]
EW, EM = world_co(te)
em = sstep(EW[:, 1], eye_y - 0.02 * L, eye_y + 0.10 * L)
f = ratio_factor(0.33, 0.20, V["MuzzleLength"])
EW[:, 1] = eye_y + (EW[:, 1] - eye_y) * (1.0 + (f - 1.0) * em)
low = sstep(EW[:, 2], pal_z + 0.01 * L, pal_z - 0.05 * L)
fj = ratio_factor(0.74, 0.10, V["JawLength"])
EW[:, 1] = hinge[1] + (EW[:, 1] - hinge[1]) * (1.0 + (fj - 1.0) * low)
set_world(te, EW, EM)
PATH["TeethArcade_note"] = "fused slab (v3 limitation 1): follows both fields; cannot split"

# throat follows jaw length so it does not detach
th = objs["Throat"]
HW, HMx = world_co(th)
HW[:, 1] = hinge[1] + (HW[:, 1] - hinge[1]) * (1.0 + (fj - 1.0) * 0.5)
set_world(th, HW, HMx)

# ------------------------------------------------------------- ears
for sname in ("L", "R"):
    ear = objs[f"Ear_{sname}"]
    EW2, EM2 = world_co(ear)
    # base = ear verts nearest the skull surface (min dist to tissue;
    # brute force — Blender's python has no scipy, meshes are small)
    d = np.sqrt(((EW2[:, None, :] - TW[None, :, :]) ** 2).sum(-1)).min(axis=1)
    base = EW2[d < np.percentile(d, 25)].mean(axis=0)
    tip = EW2[np.argmax(np.linalg.norm(EW2 - base, axis=1))]
    axis = tip - base
    axis = axis / np.linalg.norm(axis)
    rel = EW2 - base
    t = rel @ axis                                   # along-ear coordinate
    tmax = float(t.max())
    side = 1.0 if sname == "R" else -1.0
    # EarLength -10: ear/L .40 -> .335 (proportional x0.84 along axis)
    f = ratio_factor(0.40, 0.65, V["EarLength"])
    rel = rel * 1.0
    rel = (rel - np.outer(t, axis)) + np.outer(t * f, axis)
    # EarWidth +55: ear W/len .55 -> .7425 (x1.35 across, in the ear
    # plane's lateral direction approx = head x from the ear midline)
    f = ratio_factor(0.55, 0.35, V["EarWidth"])
    mid = base[0]
    rel[:, 0] = rel[:, 0] * f
    # EarTipPoint -80: tip radius index .50 -> .14: pull the top 30%
    # toward the axis line (rounds the tip)
    tt = sstep(t / tmax, 0.70, 1.0)
    perp = rel - np.outer(rel @ axis, axis)
    rel = rel - perp * (0.55 * tt)[:, None]
    rel = rel - np.outer(t * 0.06 * tt, axis)
    PATH["EarTipPoint"] = "partial — tip pinch field; the round-ear silhouette variant is discrete (spec 1.4)"
    # EarSpread +40: base out +0.016 L and cant outward 6 deg
    base2 = base + np.array([side * 0.016 * L, 0, 0])
    ang = math.radians(-6.0 * side)
    ca, sa = math.cos(ang), math.sin(ang)
    zz = rel[:, 2].copy()
    rel[:, 2] = rel[:, 0] * sa + zz * ca
    rel[:, 0] = rel[:, 0] * ca - zz * sa
    # EarBaseHeight -25 (re-anchored rename; applied as -0.02 L drop)
    base2 = base2 + np.array([0, 0, -0.020 * L])
    # EarTilt -20: rotate back about head-x at the base by 7 deg
    ang = math.radians(-7.0)
    ca, sa = math.cos(ang), math.sin(ang)
    yy, zz = rel[:, 1].copy(), rel[:, 2].copy()
    rel[:, 1] = yy * ca - zz * sa
    rel[:, 2] = yy * sa + zz * ca
    set_world(ear, base2 + rel, EM2)
PATH["EarLength"] = "full"
PATH["EarWidth"] = "full"
PATH["EarSpread"] = "partial — index slider, shift+cant [E map]"
PATH["EarBaseHeight"] = "partial — re-anchored rename; -25 applied as a 0.02 L drop [E]"
PATH["EarTilt"] = "partial — index slider, rotation [E map]"

# ------------------------------------------------------------- eyes
d_eye = (V["EyeSpacing"] / 100.0) * 0.08 / 2.0 * L   # +0.012 L per side
f_eye = ratio_factor(0.15, 0.10, V["EyeSize"])       # 0.733
for sname in ("L", "R"):
    c = eye_c[sname].copy()
    side = 1.0 if sname == "R" else -1.0
    c[0] += side * d_eye
    for part in ("Eyeball", "Iris", "Pupil", "Eyelid", "LidMargin"):
        o = objs[f"{part}_{sname}"]
        W2, M2 = world_co(o)
        W2 = c + (W2 - eye_c[sname]) * f_eye
        set_world(o, W2, M2)
PATH["EyeSize"] = "full (eyeball + lid assembly scaled about the centre)"
PATH["EyeSpacing"] = "full (delta applied; v3's deliberate deviation preserved)"
PATH["EyeForwardness"] = "none — assemblies keep v3's 15 deg socket yaw; convergence is a socket-rig parameter, not a surface field [recorded]"

# ------------------------------------------------------------- nose
nose = objs["NoseLeather"]
NW, NM = world_co(nose)
nc = NW.mean(axis=0)
f = ratio_factor(0.55, 0.30, V["NoseSize"])
NW = nc + (NW - nc) * np.array([f, 1.0 + (f - 1.0) * 0.5,
                                1.0 + (f - 1.0) * 0.5])
set_world(nose, NW, NM)
PATH["NoseSize"] = "full"

# ------------------------------------------------------------- tongue
tg = objs["Tongue"]
GW, GM = world_co(tg)
gbase = GW[np.argsort(GW[:, 1])[:20]].mean(axis=0)   # posterior base
GW = gbase + (GW - gbase) * 1.3
set_world(tg, GW, GM)
# approximate clearance: tongue extent vs jaw length/depth
JW2, _ = world_co(objs["Jaw"])
tongue_report = {
    "scale": 1.3,
    "tongue_y_extent_L": float(np.ptp(GW[:, 1]) / L),
    "jaw_y_extent_L": float(np.ptp(JW2[:, 1]) / L),
    "tongue_max_forward_vs_jaw_front": float(
        (GW[:, 1].max() - JW2[:, 1].max()) / L),
    "note": "bbox-level clearance only; the fused teeth slab prevents a "
            "true occlusion check (v3 limitation 1)",
}

# ------------------------------------------------------- re-measure
TW2, _ = world_co(tis)
zb_band = TW2[(TW2[:, 2] > eye_z - 0.06 * L) & (TW2[:, 2] < eye_z + 0.10 * L)]
zb = float(np.ptp(zb_band[:, 0]))
can_y = eye_y + 0.55 * (nose_y - eye_y)
muz_band = TW2[(TW2[:, 1] > can_y - 0.03 * L) & (TW2[:, 1] < can_y + 0.03 * L)
               & (TW2[:, 2] < pal_z + 0.10 * L)]
muz_w = float(np.ptp(muz_band[:, 0]))
EWL, _ = world_co(objs["Ear_L"])
EWR, _ = world_co(objs["Ear_R"])
ear_len = float(max(np.ptp(EWL[:, 2]), np.ptp(EWR[:, 2])))
orb2 = float(np.ptp(world_co(objs["Eyeball_L"])[0][:, 0]))
jaw_w = float(np.ptp(JW2[:, 0]))
body_neck_w = 0.112     # from grade_sen.py (qa_sen_body.json)
meas = {
    "L": L, "ZB_after": zb, "ZB_before": 0.5466 * L,
    "muzzle_width_after": muz_w, "orbit_d_after": orb2,
    "orbit_d_before": orb_d, "jaw_width_after": jaw_w,
    "ear_height_extent_after": ear_len,
    "M1_final_neckW_over_bearZB": body_neck_w / zb,
    "head_L_base_scale_m": 0.42 / 1.74,
    "head_scale_factor_at_assembly": (0.42 / 1.74) / L,
}
report = {"vector": V, "paths": PATH, "landmarks": {
    "eye_y": eye_y, "eye_z": eye_z, "pal_z": pal_z, "nose_y": nose_y},
    "tongue": tongue_report, "measured": meas}
(WORK / "head_measure.json").write_text(json.dumps(report, indent=1))
print(json.dumps(meas, indent=1))
print(json.dumps(PATH, indent=1))

# ------------------------------------------------------------- export
bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(filepath=str(SEN / "sen_head.glb"),
                          export_format="GLB", use_selection=True)
bpy.ops.wm.save_as_mainfile(filepath=str(SEN / "sen_head.blend"))
print("HEAD BUILD DONE")
