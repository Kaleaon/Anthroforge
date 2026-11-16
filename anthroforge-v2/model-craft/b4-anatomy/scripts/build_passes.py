#!/usr/bin/env python3
"""Anatomy sculpt demo: one torso region through the passes.

Headless stand-in for brush work: each sculpt pass is a set of smooth
displacement fields on a parametric torso (rings x angle), cumulative,
exactly the way a sculptor's passes accumulate on one mesh.
  pass0 blockout   - crude low-res profile, flat facets (merged primitives)
  pass1 primary    - smooth big-form profile: pelvis/waist/ribcage planes
  pass2 secondary  - muscle masses: pecs, delts, serratus, abs, obliques
  pass3 tertiary   - clavicle/sternum grooves, fold crease, mm-scale noise
  pass4 asymmetry  - right pec fuller, left shoulder dropped, slight twist
Front = +Y, character right = +X, Z up. Units: metres.
"""
import json
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parent.parent / "work"
OUT.mkdir(parents=True, exist_ok=True)

def gauss(x, c, w):
    return np.exp(-0.5 * ((x - c) / w) ** 2)

def angdiff(a, b):
    return (a - b + np.pi) % (2 * np.pi) - np.pi

# ---------------------------------------------------------------- profile
# control points (z, rx, ry): the primary-form skeleton of the region
CTRL = np.array([
    [0.00, 0.148, 0.104],
    [0.18, 0.158, 0.110],   # pelvis mass
    [0.40, 0.138, 0.096],
    [0.56, 0.127, 0.089],   # waist pinch
    [0.74, 0.146, 0.100],
    [0.95, 0.170, 0.113],   # ribcage / chest
    [1.12, 0.163, 0.106],
    [1.24, 0.138, 0.090],   # shoulder slope
    [1.35, 0.064, 0.058],   # neck base
])

def profile(z, ctrl):
    rx = np.interp(z, ctrl[:, 0], ctrl[:, 1])
    ry = np.interp(z, ctrl[:, 0], ctrl[:, 2])
    # smooth the interpolation (moving average over the ring axis)
    k = np.ones(9) / 9
    rx = np.convolve(np.pad(rx, 4, mode="edge"), k, "valid")
    ry = np.convolve(np.pad(ry, 4, mode="edge"), k, "valid")
    return rx, ry

def build(nth, nz, passes):
    th = np.linspace(0, 2 * np.pi, nth, endpoint=False)
    z = np.linspace(0.0, 1.35, nz)
    TH, Z = np.meshgrid(th, z)
    rx, ry = profile(z, CTRL)
    RX = np.repeat(rx[:, None], nth, axis=1)
    RY = np.repeat(ry[:, None], nth, axis=1)
    # chest front slightly flattened, back slightly fuller (planes, pass1)
    flat = 1.0 - 0.10 * np.exp(-((np.cos(TH) - 1) ** 2) / 0.5) * gauss(Z, 0.98, 0.22)
    X = np.sin(TH) * RX
    Y = np.cos(TH) * RY * flat
    ZZ = Z.copy()
    radial = np.stack([np.sin(TH), np.cos(TH)], axis=-1)  # in xy-plane

    def displace(amp_field):
        nonlocal X, Y
        X = X + amp_field * radial[..., 0]
        Y = Y + amp_field * radial[..., 1]

    if passes >= 2:
        front = np.cos(TH)  # 1 at front
        # pectorals: two masses split by the sternum groove
        for sgn in (+1, -1):
            d = angdiff(TH, sgn * 0.58)
            displace(0.016 * np.exp(-(d ** 2) / (2 * 0.42 ** 2)) * gauss(Z, 0.99, 0.115)
                     * np.clip(front, 0, 1))
        displace(-0.006 * np.exp(-(angdiff(TH, 0) ** 2) / (2 * 0.10 ** 2))
                 * gauss(Z, 0.99, 0.13))  # sternum groove
        # deltoid caps
        for sgn in (+1, -1):
            d = angdiff(TH, sgn * np.pi / 2)
            displace(0.013 * np.exp(-(d ** 2) / (2 * 0.38 ** 2)) * gauss(Z, 1.19, 0.10))
        # serratus fingers (front-lateral, 3 per side)
        for sgn in (+1, -1):
            for zz in (0.78, 0.845, 0.91):
                d = angdiff(TH, sgn * 1.02)
                displace(0.0042 * np.exp(-(d ** 2) / (2 * 0.16 ** 2)) * gauss(Z, zz, 0.028))
        # abdominal columns + two transverse grooves
        for sgn in (+1, -1):
            d = angdiff(TH, sgn * 0.30)
            displace(0.005 * np.exp(-(d ** 2) / (2 * 0.24 ** 2)) * gauss(Z, 0.48, 0.15)
                     * np.clip(front, 0, 1))
        for zz in (0.435, 0.525):
            displace(-0.0028 * np.exp(-(angdiff(TH, 0) ** 2) / (2 * 0.55 ** 2))
                     * gauss(Z, zz, 0.012) * np.clip(front, 0, 1))
        # obliques: soft diagonal fullness at the sides of the waist
        for sgn in (+1, -1):
            d = angdiff(TH, sgn * 1.25)
            displace(0.004 * np.exp(-(d ** 2) / (2 * 0.35 ** 2)) * gauss(Z, 0.55, 0.13))
    if passes >= 3:
        front = np.clip(np.cos(TH), 0, 1)
        # clavicle grooves: shallow V lines near the top of the chest
        for sgn in (+1, -1):
            zz_line = 1.235 - 0.035 * np.abs(np.sin(TH)) * (np.sign(TH - np.pi) * -1 if False else 1)
            line = 1.245 - 0.030 * np.abs(np.sin(TH))
            side = np.exp(-(angdiff(TH, sgn * 1.05) ** 2) / (2 * 0.55 ** 2))
            displace(-0.0026 * np.exp(-((Z - line) ** 2) / (2 * 0.010 ** 2)) * side * front)
        # sternum centre line
        displace(-0.0018 * np.exp(-(angdiff(TH, 0) ** 2) / (2 * 0.06 ** 2))
                 * gauss(Z, 1.06, 0.10) * front)
        # waist fold crease (front + sides)
        displace(-0.0022 * gauss(Z, 0.615, 0.010)
                 * (0.4 + 0.6 * np.abs(np.sin(TH)) ** 0 + 0.0) * np.clip(np.cos(TH) + 0.55, 0, 1))
        # mm-scale surface life: two smooth sinusoid octaves, tiny amplitude
        rng = np.random.default_rng(7)
        ph1, ph2 = rng.uniform(0, 6.28, 2)
        noise = (0.00055 * np.sin(9 * TH + 5 * Z * 6 + ph1)
                 + 0.00035 * np.sin(17 * TH - 8 * Z * 6 + ph2)) * gauss(Z, 0.8, 0.55)
        displace(noise)
    if passes >= 4:
        # right pec fuller (character's right, +X side)
        d = angdiff(TH, 0.58)
        displace(0.0032 * np.exp(-(d ** 2) / (2 * 0.42 ** 2)) * gauss(Z, 0.99, 0.115)
                 * np.clip(np.cos(TH), 0, 1))
        # left shoulder dropped: grade by side and height
        left = np.clip(-np.sin(TH), 0, 1) * gauss(Z, 1.35, 0.22)
        ZZ = ZZ - 0.009 * left
        # gentle axial twist increasing with height
        tw = 0.022 * (Z / 1.35)
        X, Y = (X * np.cos(tw) - Y * np.sin(tw), X * np.sin(tw) + Y * np.cos(tw))
    return X, Y, ZZ, th, z

def write_obj(path, X, Y, Z):
    nz, nth = X.shape
    with open(path, "w") as f:
        for i in range(nz):
            for j in range(nth):
                f.write(f"v {X[i,j]:.5f} {Y[i,j]:.5f} {Z[i,j]:.5f}\n")
        for i in range(nz - 1):
            for j in range(nth):
                a = i * nth + j + 1
                b = i * nth + (j + 1) % nth + 1
                c = (i + 1) * nth + (j + 1) % nth + 1
                d = (i + 1) * nth + j + 1
                f.write(f"f {a} {b} {c} {d}\n")

stats = {}
# pass 0: blockout -- coarse grid, raw piecewise profile (no smoothing)
th0 = np.linspace(0, 2 * np.pi, 24, endpoint=False)
z0 = CTRL[::2, 0]
rx0 = np.interp(z0, CTRL[:, 0], CTRL[:, 1]); ry0 = np.interp(z0, CTRL[:, 0], CTRL[:, 2])
TH0, Z0 = np.meshgrid(th0, z0)
X0 = np.sin(TH0) * rx0[:, None]; Y0 = np.cos(TH0) * ry0[:, None]
write_obj(OUT / "pass0_blockout.obj", X0, Y0, Z0)
stats["pass0"] = {"verts": int(X0.size), "note": "coarse profile, flat facets"}

prev = None
for p in (1, 2, 3, 4):
    X, Y, Z, th, z = build(160, 130, p)
    write_obj(OUT / f"pass{p}.obj", X, Y, Z)
    r = np.hypot(X, Y)
    delta = 0.0 if prev is None else float(np.sqrt(((X - prev[0]) ** 2
                                        + (Y - prev[1]) ** 2
                                        + (Z - prev[2]) ** 2).mean()) * 1000)
    stats[f"pass{p}"] = {
        "verts": int(X.size),
        "chest_width_m": round(float(X[95].max() - X[95].min()), 4),
        "waist_width_m": round(float(X[54].max() - X[54].min()), 4),
        "radial_std_mm": round(float(r.std()) * 1000, 3),
        "mean_move_vs_prev_pass_mm": round(delta, 3),
    }
    prev = (X, Y, Z)
print(json.dumps(stats, indent=1))
(OUT / "pass_stats.json").write_text(json.dumps(stats, indent=1))
print("objs written to", OUT)
