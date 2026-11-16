#!/usr/bin/env python3
"""Generic species head build on the neutral base head (v4 default).

Generalises characters/sen/scripts/build_head.py (the Sen pattern) to a
parameterised builder driven by a vector JSON, and adapts it to the v4
base: teeth are TWO arcades (TeethUpper skull-fixed, TeethLower on the
jaw pivot) instead of v3's fused slab, and the jaw-open clearance is
re-verified after deformation (BVH, upper vs lower, 0/-10/-20/-30 deg).

    blender -b --python build_head.py -- --char pyn \
        --vector <vector.json> --base <base_head.glb> --outdir <char dir>

BASE IS A PARAMETER: when base-head-v5 lands, re-run with --base
pointing at the v5 GLB and the same vector; nothing else changes.

CONVENTION (Sen's, load-bearing): spec preset values are deltas from
the SPEC neutral (ratio = neutral + t*span). The base head is not
exactly the spec neutral (deliberate deviations, e.g. interorbital
0.112 vs 0.19). Sliders are applied as PROPORTIONAL changes from
neutral: factor = (neutral + t*span)/neutral for ratio sliders,
preserving the base's deliberate deviations while moving every measure
the right amount in the right direction. Index sliders use documented
[E] maps, calibrated so Sen's values reproduce Sen's shipped fields
exactly (each map notes its Sen calibration point).

Divergences from Sen's script, both deliberate and documented:
  * Ear base detection runs against the DEFORMED tissue, and the ear
    is re-seated by the local skull-surface delta (Sen anchored to the
    pre-deformation skull; harmless at Sen's small cranium deltas, not
    at Brand's CraniumHeight -50 / Jorge's +35).
  * EarTilt gains a drop-fold extension for the strong-negative range
    (see inline note); Sen's -20 never left the pitch range.
  * Ear fix (Nov 16, 2026): EarHeight preserves the sub-base root
    (skull interface, same principle as the untouched NeckSocket —
    at f = 2.625 an unclamped root became a free-hanging spike beside
    the jaw), and a vector-driven EarFlare stage restores the fan
    profile / aspect / cup on high-length vectors, where the legacy
    absolute x-scale EarWidth cannot keep up with the axial stretch
    (Pyn's achieved W/L collapsed 0.67 -> 0.31). See inline notes.

Run: HOME=/tmp/af_home xvfb-run blender -b --threads 2 --python \
     build_head.py -- --char NAME --vector V.json --base BASE.glb \
     --outdir DIR
"""
import argparse
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index("--") + 1:]
ap = argparse.ArgumentParser()
ap.add_argument("--char", required=True)
ap.add_argument("--vector", required=True)
ap.add_argument("--base", required=True)
ap.add_argument("--outdir", required=True)
A = ap.parse_args(argv)

CHAR = A.char
OUT = Path(A.outdir)
WORK = OUT / "work"
WORK.mkdir(parents=True, exist_ok=True)
_raw = json.loads(Path(A.vector).read_text())
V = {k: float(v) for k, v in _raw.items() if isinstance(v, (int, float))}

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=A.base)

objs = {o.name: o for o in bpy.data.objects if o.type == "MESH"}
print("head objects:", sorted(objs))
REQUIRED = ["TissueHead", "Jaw", "TeethUpper", "TeethLower", "Throat",
            "Ear_L", "Ear_R", "NoseLeather", "Tongue"]
for r in REQUIRED:
    assert r in objs, f"base is missing {r} — wrong base file?"


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


def ratio_factor(neutral, span, val):
    return (neutral + (val / 100.0) * span) / neutral


# ------------------------------------------------------------ landmarks
tis = objs["TissueHead"]
TW, TM = world_co(tis)
L = float(TW[:, 1].max() - TW[:, 1].min())
nose_y = float(TW[:, 1].max())
eye_c = {}
for s in ("L", "R"):
    W0, _ = world_co(objs[f"Eyeball_{s}"])
    eye_c[s] = W0.mean(axis=0)
eye_mid = 0.5 * (eye_c["L"] + eye_c["R"])
eye_y, eye_z = float(eye_mid[1]), float(eye_mid[2])
# palate line: stage-F ruler = max z of TeethUpper verts anterior of
# eye_y + 0.10 L (measure_v4.py's y > 0.18 in the L = 1 frame)
TU0, _ = world_co(objs["TeethUpper"])
ant = TU0[TU0[:, 1] > eye_y + 0.10 * L]
pal_z = float(ant[:, 2].max()) if len(ant) else eye_z - 0.172 * L
hinge = np.array(objs["Jaw"].matrix_world)[:3, 3]
print(f"L={L:.4f} nose_y={nose_y:.4f} eye_y={eye_y:.4f} eye_z={eye_z:.4f} "
      f"pal_z={pal_z:.4f} hinge={np.round(hinge, 4)}")

PATH = {}

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

# MuzzleLength: muzzle fraction .33, span .20 (proportional on the
# anterior block, pivoting at the orbit plane)
f_ml = ratio_factor(0.33, 0.20, V["MuzzleLength"])
W[:, 1] = eye_y + (y - eye_y) * (1.0 + (f_ml - 1.0) * muz)
PATH["MuzzleLength"] = "full"
# MuzzleWidth: rostrum W .17, span .08, canine-weighted
f_mw = ratio_factor(0.17, 0.08, V["MuzzleWidth"])
tipw = 0.55 + 0.45 * sstep(y, eye_y, nose_y)
W[:, 0] = x * (1.0 + (f_mw - 1.0) * muz * tipw)
PATH["MuzzleWidth"] = "full"
# MuzzleTaper: index slider — tip width scale 1 - 0.004*val at the tip
# [E map; Sen -40 -> +16% tip width (blunter) reproduces exactly]
tw = 1.0 + (-0.004 * V["MuzzleTaper"]) \
    * sstep(y, eye_y + 0.05 * L, nose_y - 0.02 * L) * muz
W[:, 0] = W[:, 0] * tw
PATH["MuzzleTaper"] = "partial — index slider, tip-width field [E map]"
# MuzzleDepth: rostrum depth .20, span .10, about the palatal line
f_md = ratio_factor(0.20, 0.10, V["MuzzleDepth"])
W[:, 2] = pal_z + (z - pal_z) * (1.0 + (f_md - 1.0) * muz)
PATH["MuzzleDepth"] = "full"
# CraniumWidth .36/.16 / Height .31/.12 / Length .62/.20
f = ratio_factor(0.36, 0.16, V["CraniumWidth"])
W[:, 0] = W[:, 0] * (1.0 + (f - 1.0) * cran * (1.0 - 0.5 * muz))
PATH["CraniumWidth"] = "full (proportional; dome-shell ruler mismatch noted in v3/v4)"
f = ratio_factor(0.31, 0.12, V["CraniumHeight"])
W[:, 2] = eye_z + (W[:, 2] - eye_z) * (1.0 + (f - 1.0) * dome)
PATH["CraniumHeight"] = "full"
f_cl = ratio_factor(0.62, 0.20, V["CraniumLength"])
W[:, 1] = np.where(W[:, 1] < eye_y,
                   eye_y + (W[:, 1] - eye_y) * (1.0 + (f_cl - 1.0) * cran),
                   W[:, 1])
PATH["CraniumLength"] = "full"
# ForeheadWidth: frontal W .24, span .12, forehead band
f = ratio_factor(0.24, 0.12, V["ForeheadWidth"])
fh = np.exp(-((y - (eye_y + 0.01 * L)) / (0.07 * L)) ** 2) \
    * sstep(z, eye_z, eye_z + 0.10 * L)
W[:, 0] = W[:, 0] * (1.0 + (f - 1.0) * fh)
PATH["ForeheadWidth"] = "full"
# CheekWidth: ZB .58, span .20, zygomatic band
f = ratio_factor(0.58, 0.20, V["CheekWidth"])
W[:, 0] = W[:, 0] * (1.0 + (f - 1.0) * zyg)
PATH["CheekWidth"] = "full"
# StopAngle: index slider — dorsal stop dip 0.0005*val*L + muzzle-block
# pitch -0.0625 deg/unit about the stop point [E map; Sen +40 ->
# 0.020 L dip and -2.5 deg pitch, reproducing his shipped field]
W[:, 2] = W[:, 2] - 0.0005 * V["StopAngle"] * L * stopb
pitch_ang = math.radians(-0.0625 * V["StopAngle"])
ang = pitch_ang
ca, sa = math.cos(ang), math.sin(ang)
yy = W[:, 1] - eye_y
zz = W[:, 2] - (eye_z + 0.10 * L)
rot = muz > 0.5
W[rot, 1] = eye_y + yy[rot] * ca - zz[rot] * sa
W[rot, 2] = (eye_z + 0.10 * L) + yy[rot] * sa + zz[rot] * ca
PATH["StopAngle"] = "partial — index slider, dip+pitch field [E map]"
# Brow vector (band fields on tissue; no separate skull-layer mesh in
# the GLB — same scope as Sen)
W[:, 1] = W[:, 1] + 0.0003 * V["BrowProjection"] * L * brow
PATH["BrowProjection"] = "partial — tissue-band field [E map: 0.0003 L/unit]"
W[:, 2] = eye_z + (W[:, 2] - eye_z) * (1.0 + 0.002 * V["BrowThickness"] * brow)
PATH["BrowThickness"] = "partial — band thinning field [E map: 0.002/unit]"
PATH["BrowContinuity"] = "none — no torus components exist on a non-hominin head to split/merge"
sulc = np.exp(-((W[:, 2] - (eye_z + 0.135 * L)) / (0.030 * L)) ** 2) \
    * np.exp(-((W[:, 1] - (eye_y + 0.015 * L)) / (0.055 * L)) ** 2) \
    * (np.abs(W[:, 0]) < 0.24 * L)
W[:, 2] = W[:, 2] - 0.00032 * V["BrowShelf"] * L * sulc
PATH["BrowShelf"] = "partial — sulcus dip field [E map: 0.00032 L/unit]"
W[:, 2] = W[:, 2] + 0.00028 * V["BrowPosition"] * L * brow
PATH["BrowPosition"] = "partial — brow-line shift field [E map: 0.00028 L/unit]"
W[:, 2] = W[:, 2] + 0.00016 * V["BrowPadding"] * L * brow
W[:, 1] = W[:, 1] + 0.00008 * V["BrowPadding"] * L * brow
PATH["BrowPadding"] = "partial — band swell field [E map]"
med = np.exp(-((np.abs(W[:, 0]) - 0.055 * L) / (0.045 * L)) ** 2) \
    * np.exp(-((W[:, 2] - (eye_z + 0.075 * L)) / (0.040 * L)) ** 2) \
    * np.exp(-((W[:, 1] - (eye_y + 0.02 * L)) / (0.05 * L)) ** 2)
W[:, 2] = W[:, 2] - 0.00024 * V["BrowScowl"] * L * med
W[:, 1] = W[:, 1] - 0.00012 * V["BrowScowl"] * L * med
PATH["BrowScowl"] = "partial — baked medial depression; expression system owns the live slider"
# RuffVolume: soft-tissue swell in the cheek/neck zone, radial
# [E map per unit; Sen +70 -> 0.030 L x / -0.018 L z reproduces]
rad = W[:, :2] - np.array([0.0, eye_y - 0.10 * L])
rad = rad / np.maximum(np.linalg.norm(rad, axis=1, keepdims=True), 1e-9)
W[:, 0] = W[:, 0] + 0.0004286 * V["RuffVolume"] * L * neckr * rad[:, 0]
W[:, 2] = W[:, 2] - 0.000257 * V["RuffVolume"] * L * neckr
PATH["RuffVolume"] = "partial — tissue swell only; the ruff proper is the head fur groom (not built)"
set_world(tis, W, TM)
TW2, _ = world_co(tis)   # deformed tissue (ear seating, below)

# ------------------------------------------------------------- jaw
jaw = objs["Jaw"]
JW, JM = world_co(jaw)
jy, jz, jx = JW[:, 1], JW[:, 2], JW[:, 0]
post = sstep(jy, eye_y - 0.05 * L, eye_y - 0.22 * L)   # posterior (ramus) weight
f_jd = ratio_factor(0.28, 0.12, V["JawDepth"])
JW[:, 2] = hinge[2] + (jz - hinge[2]) * (1.0 + (f_jd - 1.0) * post)
PATH["JawDepth"] = "full"
f = ratio_factor(0.40, 0.14, V["JawWidth"])
JW[:, 0] = jx * (1.0 + (f - 1.0) * (0.35 + 0.65 * post))
PATH["JawWidth"] = "full"
f_jl = ratio_factor(0.74, 0.10, V["JawLength"])
JW[:, 1] = hinge[1] + (jy - hinge[1]) * f_jl
PATH["JawLength"] = "full"
set_world(jaw, JW, JM)

# teeth — v4 split arcades (replaces Sen's fused-slab handling):
# TeethUpper is skull-fixed and EMBEDDED in the muzzle block: it rides
# the muzzle's METRIC fields (length, width, taper, depth) with the
# muzzle mask, in the tissue's own order. Sen's slab followed length
# only — safe for Sen (his muzzle only grew), wrong in general: Pyn's
# muzzle NARROWS (MuzzleWidth -25 / Depth -15) and the un-narrowed
# arcade poked through the tissue (85 verts outside, measured; the
# metric follow reduces that to one posterior root vertex at the mask
# edge, pulled proud by the CheekWidth band — documented per build).
# The stop PITCH is deliberately NOT followed: it is a profile-posture
# fiction pivoting above the arcade, and following it drove Jorge's
# upper teeth down into the lowers at rest (rest overlap pairs
# 27 -> 322, measured; the base itself carries 27 at rest and the
# certified criterion is the open angles, 0 pairs everywhere).
# The dorsal stop DIP is likewise not applied (dorsal band; the
# arcade sits far below it).
# TeethLower rides the jaw pivot: it follows JawLength about the hinge.
tu = objs["TeethUpper"]
EW, EM = world_co(tu)
ey0, ex0, ez0 = EW[:, 1].copy(), EW[:, 0].copy(), EW[:, 2].copy()
em = sstep(ey0, eye_y - 0.02 * L, eye_y + 0.10 * L)
EW[:, 1] = eye_y + (ey0 - eye_y) * (1.0 + (f_ml - 1.0) * em)
tpw_t = 0.55 + 0.45 * sstep(ey0, eye_y, nose_y)
EW[:, 0] = ex0 * (1.0 + (f_mw - 1.0) * em * tpw_t)
EW[:, 0] = EW[:, 0] * (1.0 + (-0.004 * V["MuzzleTaper"])
                       * sstep(ey0, eye_y + 0.05 * L, nose_y - 0.02 * L) * em)
EW[:, 2] = pal_z + (ez0 - pal_z) * (1.0 + (f_md - 1.0) * em)
set_world(tu, EW, EM)
PATH["TeethUpper_note"] = "skull-fixed arcade; rides the muzzle metric fields (length/width/taper/depth); stop pitch/dip not followed (see comment)"
tl = objs["TeethLower"]
EW, EM = world_co(tl)
EW[:, 1] = hinge[1] + (EW[:, 1] - hinge[1]) * f_jl
set_world(tl, EW, EM)
PATH["TeethLower_note"] = "jaw-pivot arcade; follows JawLength about the hinge"

# throat follows jaw length so it does not detach
th = objs["Throat"]
HW, HMx = world_co(th)
HW[:, 1] = hinge[1] + (HW[:, 1] - hinge[1]) * (1.0 + (f_jl - 1.0) * 0.5)
set_world(th, HW, HMx)

# NeckSocket / NeckSocketDisc deliberately untouched: they are the
# body interface, not head shape (recorded).

# ------------------------------------------------------------- ears
ear_report = {}
for sname in ("L", "R"):
    ear = objs[f"Ear_{sname}"]
    EW2, EM2 = world_co(ear)
    # base = ear verts nearest the DEFORMED skull surface (divergence
    # from Sen, see header); re-seat by the local surface delta so the
    # ear keeps its original offset from the skull
    d = np.sqrt(((EW2[:, None, :] - TW2[None, :, :]) ** 2).sum(-1)).min(axis=1)
    base_mask = d < np.percentile(d, 25)
    base = EW2[base_mask].mean(axis=0)
    # material-point delta: the tissue vertex nearest the ear base
    # BEFORE deformation, followed to its deformed position (nearest-
    # point identity must not be re-picked after deformation — the
    # argmin can jump to a different vertex and displace the ear)
    idx0 = int(np.argmin(np.linalg.norm(TW - base, axis=1)))
    seat_delta = TW2[idx0] - TW[idx0]
    tip = EW2[np.argmax(np.linalg.norm(EW2 - base, axis=1))]
    axis = tip - base
    axis = axis / np.linalg.norm(axis)
    rel = EW2 - base
    t = rel @ axis                                   # along-ear coordinate
    tmax = float(t.max())
    # SIDE CONVENTION: in this head frame Ear_L / Eyeball_L sit at +x
    # (verified on the v4 base: Eyeball_L mean x = +0.1311). Sen's
    # script keyed side off the name (R = +1), which moves the +x parts
    # the wrong way. Side is therefore taken from the part's own
    # position — convention-proof for future bases.
    side = 1.0 if base[0] >= 0 else -1.0
    flare_info = {}
    # EarHeight (spec name; Sen's EarLength): ear/L .40, span .65,
    # along the ear axis. ROOT PRESERVATION (ear fix, Nov 16, 2026):
    # the sub-base root (t < 0; a third of the base ear's along-axis
    # length) is skull interface — in the base it ends inside the
    # skull silhouette (root tip z = +0.026). Scaling it with the
    # blade at f = 2.625 drove it to z = -0.203, clear of Pyn's
    # narrower skull: a pointed spike hanging beside the jaw, the
    # single biggest contributor to the "upside-down ear" read.
    # Stretch weight ramps 0 at t/tmax <= -0.02 to 1 at >= +0.25, so
    # the root keeps its base length at any f and only the blade
    # takes the factor (same principle as the untouched NeckSocket).
    f_len = ratio_factor(0.40, 0.65, V["EarHeight"])
    sw = sstep(t / tmax, -0.02, 0.25)
    rel = (rel - np.outer(t, axis)) \
        + np.outer(t * (1.0 + (f_len - 1.0) * sw), axis)
    # EarWidth: ear W/len .55, span .35, across in head x
    f = ratio_factor(0.55, 0.35, V["EarWidth"])
    rel[:, 0] = rel[:, 0] * f
    # EarFlare [E — long-ear fan stage, ear fix Nov 16, 2026]:
    # EarWidth is a width/LENGTH ratio in the spec but an absolute
    # x-scale here, so at high EarHeight the achieved ratio collapses
    # (Pyn: length x2.94 vs width x1.35 -> W/L 0.67 -> 0.31, a narrow
    # ribbon instead of a fennec fan) and the cup, which no slider
    # scales, flattens proportionally. This stage remaps the blade's
    # width envelope onto a fan profile (base ~0.40 of max, peak at
    # u ~0.72, rounded tip), restores the fan aspect (W/L -> 0.58 at
    # full flare) and deepens the cup (depth x1.55 at full flare),
    # all blended by k = sstep(f_len, 1.15, 2.20): ordinary ears
    # (k = 0) keep the calibrated legacy behaviour exactly, and any
    # long-ear species picks the fan up from its vector alone.
    # Root verts (u < 0) are skull interface and are not flared.
    k_flare = float(sstep(f_len, 1.15, 2.20))
    if k_flare > 0.0:
        wdir = np.array([1.0, 0.0, 0.0])
        wdir = wdir - (wdir @ axis) * axis
        wdir = wdir / np.linalg.norm(wdir)
        ddir = np.cross(axis, wdir)
        ta = rel @ axis
        tb = rel @ wdir
        tc = rel @ ddir
        tmax_a = float(ta.max())
        u = ta / tmax_a
        nb = 20
        edges = np.linspace(0.0, 1.0, nb + 1)
        bcen = np.zeros(nb)
        bhalf = np.zeros(nb)
        for i in range(nb):
            if i < nb - 1:
                m = (u >= edges[i]) & (u < edges[i + 1])
            else:
                m = (u >= edges[i]) & (u <= 1.0)
            if m.sum() >= 3:
                bcen[i] = 0.5 * (tb[m].max() + tb[m].min())
                bhalf[i] = 0.5 * (tb[m].max() - tb[m].min())
        ok = bhalf > 0
        if ok.sum() >= 2:
            ctr = 0.5 * (edges[:-1] + edges[1:])
            bcen = np.interp(ctr, ctr[ok], bcen[ok])
            bhalf = np.interp(ctr, ctr[ok], bhalf[ok])
            hmax = float(bhalf.max())
            p0 = bhalf / hmax
            fan_u = np.array([0.00, 0.10, 0.25, 0.45, 0.65, 0.72,
                              0.85, 0.93, 1.00])
            fan_p = np.array([0.40, 0.50, 0.66, 0.84, 0.97, 1.00,
                              0.95, 0.78, 0.45])
            prof = (1.0 - k_flare) * p0 \
                + k_flare * np.interp(ctr, fan_u, fan_p)
            prof = prof / prof.max()
            w_cur = 2.0 * hmax
            w_tar = tmax_a * ((1.0 - k_flare) * (w_cur / tmax_a)
                              + k_flare * 0.58)
            cen_v = np.interp(u, ctr, bcen)
            half_v = np.maximum(np.interp(u, ctr, bhalf), 1e-6)
            prof_v = np.interp(u, ctr, prof)
            scale = np.clip((0.5 * w_tar * prof_v) / half_v, 0.45, 2.60)
            scale = 1.0 + (scale - 1.0) * sstep(u, 0.0, 0.10)
            tb = cen_v + (tb - cen_v) * scale
            tc = tc * (1.0 + 0.55 * k_flare * sstep(u, 0.12, 0.35))
            rel = np.outer(ta, axis) + np.outer(tb, wdir) \
                + np.outer(tc, ddir)
            flare_info = {"flare_k": round(k_flare, 3),
                          "width_before": round(float(w_cur), 4),
                          "width_target": round(float(w_tar), 4)}
    # EarTipPoint: tip radius index — pinch the top 30% toward the axis
    # and shorten slightly [E map; Sen -80 -> 0.55 pinch / 0.06 shorten]
    tt = sstep(t / tmax, 0.70, 1.0)
    pinch = -0.006875 * V["EarTipPoint"]
    perp = rel - np.outer(rel @ axis, axis)
    rel = rel - perp * (pinch * tt)[:, None]
    if V["EarTipPoint"] < 0:
        rel = rel - np.outer(t * (-0.00075 * V["EarTipPoint"]) * tt, axis)
    # EarTilt: pitch about head-x at the base [Sen's map: 0.35 deg/unit;
    # Sen -20 -> -7 deg]. DROP EXTENSION [E]: below -30 the pitch holds
    # at the -30 value and the excess folds the ear outward-down about
    # the head-y axis (2.4 deg/unit of excess) — a St. Bernard-class
    # drop ear lies against the cheek, which a pure x-pitch cannot
    # express; Jorge -75 is the only vector in this batch in the fold
    # range. Flagged in the build report. (Rate raised 1.5 -> 2.4 after
    # the first Jorge render: at 67.5 deg total fold the tips still sat
    # ABOVE the base and read as wings, not a drop; 108 deg puts the
    # tip below base height.)
    pitch_val = max(V["EarTilt"], -30.0)
    ang = math.radians(0.35 * pitch_val)
    ca, sa = math.cos(ang), math.sin(ang)
    yy, zz = rel[:, 1].copy(), rel[:, 2].copy()
    rel[:, 1] = yy * ca - zz * sa
    rel[:, 2] = yy * sa + zz * ca
    if V["EarTilt"] < -30.0:
        fold = math.radians(2.4 * (-V["EarTilt"] - 30.0)) * side
        cf, sf = math.cos(fold), math.sin(fold)
        xx, zz = rel[:, 0].copy(), rel[:, 2].copy()
        rel[:, 0] = xx * cf + zz * sf
        rel[:, 2] = -xx * sf + zz * cf
        PATH["EarTilt"] = ("partial — pitch [Sen map] + drop-fold "
                           "extension [E] for the sub--30 range")
    # EarSpread: base out 0.0004 L/unit + outward cant 0.15 deg/unit
    # [E map; Sen +40 -> 0.016 L / 6 deg reproduces]
    base2 = base + seat_delta + np.array([side * 0.0004 * V["EarSpread"] * L,
                                          0, 0])
    ang = math.radians(0.15 * V["EarSpread"] * side)
    ca, sa = math.cos(ang), math.sin(ang)
    xx, zz = rel[:, 0].copy(), rel[:, 2].copy()
    rel[:, 0] = xx * ca + zz * sa
    rel[:, 2] = -xx * sa + zz * ca
    # EarPlacementHeight (spec name; Sen's EarBaseHeight): base up/down
    # [E map; Sen -25 -> -0.02 L reproduces]
    base2 = base2 + np.array([0, 0, 0.0008 * V["EarPlacementHeight"] * L])
    set_world(ear, base2 + rel, EM2)
    EW3, _ = world_co(ear)
    ear_report[sname] = {
        **flare_info,
        "base_tip_len_after": float(np.linalg.norm(EW3 - base2, axis=1).max()),
        "seat_delta_L": np.round(seat_delta / L, 4).tolist(),
    }
PATH.setdefault("EarTilt", "partial — index slider, pitch rotation [E map: 0.35 deg/unit]")
PATH["EarHeight"] = "full — blade only; sub-base root preserved at base length (skull interface, ear fix Nov 16, 2026)"
PATH["EarWidth"] = "full"
PATH["EarFlare"] = "partial — long-ear fan stage [E]: envelope remap + aspect -> 0.58 + cup deepening, k = sstep(f_len, 1.15, 2.20); inert (k = 0) at ordinary length factors (ear fix Nov 16, 2026)"
PATH["EarTipPoint"] = "partial — tip pinch field; a discrete round-ear silhouette variant is separate (spec 1.4/2.4)"
PATH["EarSpread"] = "partial — index slider, shift+cant [E map]"
PATH["EarPlacementHeight"] = "partial — index slider, base shift [E map: 0.0008 L/unit]"

# ------------------------------------------------------------- eyes
d_eye = (V["EyeSpacing"] / 100.0) * 0.08 / 2.0 * L
f_eye = ratio_factor(0.15, 0.10, V["EyeSize"])
for sname in ("L", "R"):
    c = eye_c[sname].copy()
    side = 1.0 if eye_c[sname][0] >= 0 else -1.0   # see ear note: +x side
    c[0] += side * d_eye
    for part in ("Eyeball", "Iris", "Pupil", "Eyelid", "LidMargin"):
        o = objs[f"{part}_{sname}"]
        W2, M2 = world_co(o)
        W2 = c + (W2 - eye_c[sname]) * f_eye
        set_world(o, W2, M2)
PATH["EyeSize"] = "full (eyeball + lid assembly scaled about the centre)"
PATH["EyeSpacing"] = "full (delta applied; the base's deliberate deviation preserved)"
PATH["EyeForwardness"] = "none — assemblies keep the base's socket yaw; convergence is a socket-rig parameter, not a surface field [recorded, Sen precedent]"

# ------------------------------------------------------------- nose
nose = objs["NoseLeather"]
NW, NM = world_co(nose)
nc = NW.mean(axis=0)
f = ratio_factor(0.55, 0.30, V["NoseSize"])
NW = nc + (NW - nc) * np.array([f, 1.0 + (f - 1.0) * 0.5,
                                1.0 + (f - 1.0) * 0.5])
set_world(nose, NW, NM)
PATH["NoseSize"] = "full"

# tongue: no character direction for this batch — left at base scale
PATH["Tongue_note"] = "not scaled — no tongue direction in the batch-1 vectors for this character"

# --------------------------------------- jaw-open teeth verification
def mesh_tris(o):
    W3, _ = world_co(o)
    tris = []
    for p in o.data.polygons:
        idx = list(p.vertices)
        for k in range(1, len(idx) - 1):
            tris.append((idx[0], idx[k], idx[k + 1]))
    return W3, tris


def bvh_of(W3, tris):
    return BVHTree.FromPolygons([Vector(v) for v in W3], tris,
                                all_triangles=True)


UW, UT = mesh_tris(objs["TeethUpper"])
LW, LT = mesh_tris(objs["TeethLower"])
tu_tree = bvh_of(UW, UT)
teeth_verify = {}
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
    teeth_verify[str(deg)] = {"overlap_pairs": len(ov),
                              "min_clearance_L": round(float(dmin), 5)}
print("teeth verify:", json.dumps(teeth_verify))

report = {"character": CHAR, "base": A.base, "vector": V, "paths": PATH,
          "landmarks": {"L": L, "eye_y": eye_y, "eye_z": eye_z,
                        "pal_z": pal_z, "nose_y": nose_y,
                        "hinge": hinge.tolist()},
          "ears": ear_report, "teeth_verify": teeth_verify}
(WORK / "head_measure.json").write_text(json.dumps(report, indent=1))

# ------------------------------------------------------------- export
bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(filepath=str(OUT / f"{CHAR}_head.glb"),
                          export_format="GLB", use_selection=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / f"{CHAR}_head.blend"))
print("HEAD BUILD DONE", CHAR)
