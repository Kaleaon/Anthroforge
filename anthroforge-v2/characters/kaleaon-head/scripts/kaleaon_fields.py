#!/usr/bin/env python3
"""Kaleaon head Phase 2 - shared field machinery.

Ports characters/pyn/scripts/build_head.py (the corrected sona builder:
proportional-from-neutral convention, side from part position, metric
teeth follow, ear seat by material-point delta) into per-object field
functions so the staged Kaleaon build can apply layer-appropriate
subsets (spec S6/S8: skull = bone-layer sliders, muscles = muscle-layer
sliders, tissue = full stack) while keeping every layer registered -
all fields are world-space functions of position with shared landmarks,
and every mask is computed ONCE from the object's input coords (the
builder's exact convention) and threaded through the stack.

Kaleaon additions beyond the sona builder (all flagged in the build
doc): the S5.5 vertical family (OrbitHeight band, OrbitRise,
BraincaseRise, JawDepthProfile; StopDepth is 0 = neutral no-op),
whisker-pad swell, chin mass, smile-line cage path, felid canine
emphasis, tongue re-proportion per spec S5.3, nose seat-delta follow
(the sona builder leaves the nose in place; with MuzzleLength -25 the
muzzle retracts ~0.05 L under it, so the nose is carried by the same
material-point seat delta the builder already uses for ears).
"""
import math

import numpy as np


def sstep(x, a, b):
    t = np.clip((np.asarray(x, float) - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def ratio_factor(neutral, span, val):
    return (neutral + (val / 100.0) * span) / neutral


def landmarks(tissue_W, eye_L_W, eye_R_W, jaw_origin, teeth_upper_W):
    """Shared landmark set (builder convention), from world coords."""
    TW = tissue_W
    L = float(TW[:, 1].max() - TW[:, 1].min())
    nose_y = float(TW[:, 1].max())
    eye_c = {"L": eye_L_W.mean(axis=0), "R": eye_R_W.mean(axis=0)}
    eye_mid = 0.5 * (eye_c["L"] + eye_c["R"])
    eye_y, eye_z = float(eye_mid[1]), float(eye_mid[2])
    ant = teeth_upper_W[teeth_upper_W[:, 1] > eye_y + 0.10 * L]
    pal_z = float(ant[:, 2].max()) if len(ant) else eye_z - 0.172 * L
    orbit_height_base = (eye_z - pal_z) / L
    return {"L": L, "nose_y": nose_y, "eye_c": eye_c, "eye_mid": eye_mid,
            "eye_y": eye_y, "eye_z": eye_z, "pal_z": pal_z,
            "hinge": np.asarray(jaw_origin, float),
            "orbit_height_base": orbit_height_base}


def masks(W, LM):
    """The builder's masks, from W's input coords (call once, before
    any field touches W)."""
    L, eye_y, eye_z, pal_z = LM["L"], LM["eye_y"], LM["eye_z"], LM["pal_z"]
    y, z, x = W[:, 1], W[:, 2], W[:, 0]
    muz = sstep(y, eye_y - 0.02 * L, eye_y + 0.10 * L)
    cran = 1.0 - sstep(y, eye_y - 0.16 * L, eye_y - 0.02 * L)
    dome = sstep(z, eye_z + 0.02 * L, eye_z + 0.16 * L) * cran
    zyg = np.exp(-((y - (eye_y - 0.02 * L)) / (0.10 * L)) ** 2) \
        * np.exp(-((z - (eye_z - 0.03 * L)) / (0.13 * L)) ** 2)
    brow = np.exp(-((y - (eye_y + 0.015 * L)) / (0.055 * L)) ** 2) \
        * np.exp(-((z - (eye_z + 0.085 * L)) / (0.045 * L)) ** 2) \
        * (np.abs(x) < 0.24 * L)
    stopb = np.exp(-((y - (eye_y - 0.01 * L)) / (0.045 * L)) ** 2) \
        * sstep(z, eye_z + 0.05 * L, eye_z + 0.14 * L)
    neckr = (1.0 - sstep(z, pal_z + 0.10 * L, pal_z + 0.24 * L)) \
        * (1.0 - muz)
    return {"muz": muz, "cran": cran, "dome": dome, "zyg": zyg,
            "brow": brow, "stopb": stopb, "neckr": neckr}


def cranium_fields(W, V, LM, M):
    """CraniumWidth/Height/Length - builder formulas."""
    eye_y, eye_z = LM["eye_y"], LM["eye_z"]
    f = ratio_factor(0.36, 0.16, V["CraniumWidth"])
    W[:, 0] = W[:, 0] * (1.0 + (f - 1.0) * M["cran"] * (1.0 - 0.5 * M["muz"]))
    f = ratio_factor(0.31, 0.12, V["CraniumHeight"])
    W[:, 2] = eye_z + (W[:, 2] - eye_z) * (1.0 + (f - 1.0) * M["dome"])
    f_cl = ratio_factor(0.62, 0.20, V["CraniumLength"])
    W[:, 1] = np.where(W[:, 1] < eye_y,
                       eye_y + (W[:, 1] - eye_y) * (1.0 + (f_cl - 1.0)
                                                    * M["cran"]),
                       W[:, 1])
    return W


def brow_fields(W, V, LM, M):
    """The builder's brow band stack ([E] maps, verbatim rates). The
    band mask is the input mask; sulcus/medial masks read current W,
    exactly as the builder's sequential stack does."""
    L, eye_y, eye_z = LM["L"], LM["eye_y"], LM["eye_z"]
    brow = M["brow"]
    W[:, 1] = W[:, 1] + 0.0003 * V["BrowProjection"] * L * brow
    W[:, 2] = eye_z + (W[:, 2] - eye_z) * (1.0 + 0.002
                                           * V["BrowThickness"] * brow)
    sulc = np.exp(-((W[:, 2] - (eye_z + 0.135 * L)) / (0.030 * L)) ** 2) \
        * np.exp(-((W[:, 1] - (eye_y + 0.015 * L)) / (0.055 * L)) ** 2) \
        * (np.abs(W[:, 0]) < 0.24 * L)
    W[:, 2] = W[:, 2] - 0.00032 * V["BrowShelf"] * L * sulc
    W[:, 2] = W[:, 2] + 0.00028 * V["BrowPosition"] * L * brow
    W[:, 2] = W[:, 2] + 0.00016 * V["BrowPadding"] * L * brow
    W[:, 1] = W[:, 1] + 0.00008 * V["BrowPadding"] * L * brow
    med = np.exp(-((np.abs(W[:, 0]) - 0.055 * L) / (0.045 * L)) ** 2) \
        * np.exp(-((W[:, 2] - (eye_z + 0.075 * L)) / (0.040 * L)) ** 2) \
        * np.exp(-((W[:, 1] - (eye_y + 0.02 * L)) / (0.05 * L)) ** 2)
    W[:, 2] = W[:, 2] - 0.00024 * V["BrowScowl"] * L * med
    W[:, 1] = W[:, 1] - 0.00012 * V["BrowScowl"] * L * med
    return W


def orbit_height_delta(V, LM):
    """Pure z delta at the band peak (eye centre): proportional -
    measured base orbit height x (target/neutral - 1)."""
    target = 0.17 + (V["OrbitHeight"] / 100.0) * 0.12
    return LM["orbit_height_base"] * (target / 0.17 - 1.0) * LM["L"]


def orbit_height_field(W, V, LM):
    """OrbitHeight (S5.4 #32): orbit band shifts vertically vs the
    palatal line; Gaussian band peaking at the eye centre, so the eye
    assemblies take orbit_height_delta as a pure shift (stage 5)."""
    L, eye_y, eye_z = LM["L"], LM["eye_y"], LM["eye_z"]
    d = orbit_height_delta(V, LM)
    w = np.exp(-(((W[:, 1] - eye_y) / (0.10 * L)) ** 2
                 + ((W[:, 2] - eye_z) / (0.10 * L)) ** 2))
    W[:, 2] = W[:, 2] + d * w
    return W


def orbit_rise_field(W, V, LM):
    """OrbitRise (#33): frontal band lifts relative to the seated eye.
    Delta = (val/100) x span, additive [E] field."""
    L, eye_y, eye_z = LM["L"], LM["eye_y"], LM["eye_z"]
    d = (V["OrbitRise"] / 100.0) * 0.16 * L
    w = np.exp(-(((W[:, 1] - eye_y) / (0.07 * L)) ** 2
                 + ((W[:, 2] - (eye_z + 0.09 * L)) / (0.05 * L)) ** 2))
    W[:, 2] = W[:, 2] + d * w
    return W


def braincase_field(W, V, LM, M):
    """BraincaseRise (#35): cranium shell above the orbit line only.
    Delta = (val/100) x span, additive [E] field."""
    L, eye_z = LM["L"], LM["eye_z"]
    d = (V["BraincaseRise"] / 100.0) * 0.14 * L
    w = M["cran"] * sstep(W[:, 2], eye_z + 0.05 * L, eye_z + 0.15 * L)
    W[:, 2] = W[:, 2] + d * w
    return W


def tissue_fields(W, V, LM):
    """The builder's full tissue stack, verbatim order and rates, plus
    the Kaleaon verticals (appended; they act on their own bands)."""
    M = masks(W, LM)
    L = LM["L"]
    eye_y, eye_z, pal_z = LM["eye_y"], LM["eye_z"], LM["pal_z"]
    nose_y = LM["nose_y"]
    y, z, x = W[:, 1].copy(), W[:, 2].copy(), W[:, 0].copy()
    muz = M["muz"]
    zyg, stopb, neckr = M["zyg"], M["stopb"], M["neckr"]
    # MuzzleLength
    f_ml = ratio_factor(0.33, 0.20, V["MuzzleLength"])
    W[:, 1] = eye_y + (y - eye_y) * (1.0 + (f_ml - 1.0) * muz)
    # MuzzleWidth
    f_mw = ratio_factor(0.17, 0.08, V["MuzzleWidth"])
    tipw = 0.55 + 0.45 * sstep(y, eye_y, nose_y)
    W[:, 0] = x * (1.0 + (f_mw - 1.0) * muz * tipw)
    # MuzzleTaper
    tw = 1.0 + (-0.004 * V["MuzzleTaper"]) \
        * sstep(y, eye_y + 0.05 * L, nose_y - 0.02 * L) * muz
    W[:, 0] = W[:, 0] * tw
    # MuzzleDepth
    f_md = ratio_factor(0.20, 0.10, V["MuzzleDepth"])
    W[:, 2] = pal_z + (z - pal_z) * (1.0 + (f_md - 1.0) * muz)
    # Cranium
    W = cranium_fields(W, V, LM, M)
    # ForeheadWidth
    f = ratio_factor(0.24, 0.12, V["ForeheadWidth"])
    fh = np.exp(-((y - (eye_y + 0.01 * L)) / (0.07 * L)) ** 2) \
        * sstep(z, eye_z, eye_z + 0.10 * L)
    W[:, 0] = W[:, 0] * (1.0 + (f - 1.0) * fh)
    # CheekWidth
    f = ratio_factor(0.58, 0.20, V["CheekWidth"])
    W[:, 0] = W[:, 0] * (1.0 + (f - 1.0) * zyg)
    # StopAngle: dip + muzzle-block pitch (pitch reads current W)
    W[:, 2] = W[:, 2] - 0.0005 * V["StopAngle"] * L * stopb
    ang = math.radians(-0.0625 * V["StopAngle"])
    ca, sa = math.cos(ang), math.sin(ang)
    yy = W[:, 1] - eye_y
    zz = W[:, 2] - (eye_z + 0.10 * L)
    rot = muz > 0.5
    W[rot, 1] = eye_y + yy[rot] * ca - zz[rot] * sa
    W[rot, 2] = (eye_z + 0.10 * L) + yy[rot] * sa + zz[rot] * ca
    # Brow stack
    W = brow_fields(W, V, LM, M)
    # RuffVolume
    rad = W[:, :2] - np.array([0.0, eye_y - 0.10 * L])
    rad = rad / np.maximum(np.linalg.norm(rad, axis=1, keepdims=True), 1e-9)
    W[:, 0] = W[:, 0] + 0.0004286 * V["RuffVolume"] * L * neckr * rad[:, 0]
    W[:, 2] = W[:, 2] - 0.000257 * V["RuffVolume"] * L * neckr
    # Kaleaon verticals
    W = orbit_height_field(W, V, LM)
    W = orbit_rise_field(W, V, LM)
    W = braincase_field(W, V, LM, M)
    return W


def whisker_pads(W, LM, amp=0.012):
    """Build-level delta (spec S3): felid whisker-pad swells on the
    muzzle sides at the canine band. [E] field: +-x swell + slight
    rise, Gaussian in y/z, gated to the muzzle side surface."""
    L, pal_z, nose_y = LM["L"], LM["pal_z"], LM["nose_y"]
    cy = nose_y - 0.295 * L          # canine station (audit: y = 0.205)
    cz = pal_z + 0.05 * L
    w = np.exp(-(((W[:, 1] - cy) / (0.060 * L)) ** 2
                 + ((W[:, 2] - cz) / (0.055 * L)) ** 2)) \
        * sstep(np.abs(W[:, 0]), 0.04 * L, 0.12 * L)
    W[:, 0] = W[:, 0] + np.sign(W[:, 0]) * amp * L * w
    W[:, 2] = W[:, 2] + 0.004 * L * w
    return W


def jaw_fields(W, V, LM):
    """JawDepth / JawWidth / JawLength (builder) + JawDepthProfile
    (#37: coronoid rise above the tooth line, posterior scale)."""
    L, eye_y, pal_z = LM["L"], LM["eye_y"], LM["pal_z"]
    hinge = LM["hinge"]
    jy, jz, jx = W[:, 1].copy(), W[:, 2].copy(), W[:, 0].copy()
    post = sstep(jy, eye_y - 0.05 * L, eye_y - 0.22 * L)
    f_jd = ratio_factor(0.28, 0.12, V["JawDepth"])
    W[:, 2] = hinge[2] + (jz - hinge[2]) * (1.0 + (f_jd - 1.0) * post)
    f = ratio_factor(0.40, 0.14, V["JawWidth"])
    W[:, 0] = jx * (1.0 + (f - 1.0) * (0.35 + 0.65 * post))
    f_jl = ratio_factor(0.74, 0.10, V["JawLength"])
    W[:, 1] = hinge[1] + (jy - hinge[1]) * f_jl
    # JawDepthProfile: scale the above-palate posterior rise
    f_jdp = ratio_factor(0.17, 0.12, V["JawDepthProfile"])
    w = post * sstep(W[:, 2], pal_z + 0.01 * L, pal_z + 0.08 * L)
    W[:, 2] = pal_z + (W[:, 2] - pal_z) * (1.0 + (f_jdp - 1.0) * w)
    return W


def masseter_field(W, V, LM):
    """Muscles-layer masseter: the JawDepth posterior z-scale about
    the hinge, on the muscle layer's own coords (spec S6)."""
    L, eye_y = LM["L"], LM["eye_y"]
    hinge = LM["hinge"]
    post = sstep(W[:, 1], eye_y - 0.05 * L, eye_y - 0.22 * L)
    f_jd = ratio_factor(0.28, 0.12, V["JawDepth"])
    W[:, 2] = hinge[2] + (W[:, 2] - hinge[2]) * (1.0 + (f_jd - 1.0) * post)
    return W


def skull_fields(W, V, LM):
    """Bone-layer set: cranium + stop dip + the verticals that move
    the orbit/frontal bone (S5.4 layer column)."""
    M = masks(W, LM)
    W = cranium_fields(W, V, LM, M)
    W[:, 2] = W[:, 2] - 0.0005 * V["StopAngle"] * LM["L"] * M["stopb"]
    W = orbit_height_field(W, V, LM)
    W = orbit_rise_field(W, V, LM)
    W = braincase_field(W, V, LM, M)
    return W


def muscle_fields(W, V, LM):
    """Muscle-layer set: cranium registration + brow stack + orbit
    verticals + masseter."""
    M = masks(W, LM)
    W = cranium_fields(W, V, LM, M)
    W = brow_fields(W, V, LM, M)
    W = orbit_height_field(W, V, LM)
    W = orbit_rise_field(W, V, LM)
    W = masseter_field(W, V, LM)
    return W
