#!/usr/bin/env python3
"""Profile analysis for v4: dump the torso width profile (base / v3 /
v4) by height, and recompute the three metrics whose first definitions
were flawed (see GRAVITY_V4.md):
  M2' apron bottom = lowest deformed z among FRONT verts carrying
      > 2 cm of added radial tissue (the first M2 minimised over all
      front-low verts, which trivially lands on the crotch verts).
  M4' boundary step = max width-gradient in the belly-mask ring bands
      of the DEFORMED profile DIVIDED BY the same quantity on the BASE
      profile (the first M4 compared against the median gradient
      elsewhere, which conflates anatomy with field boundaries).
  M7b' waist crease = interior local minima of the width profile in
      the waist window, with depth vs +-0.06 h neighbours.
"""
import zipfile
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
OUT = HERE.parent
WORK = OUT / "work"
MPFB_ZIP = Path.home() / "workspace/stick-figure-avatar/photoreal/tools/mpfb2.zip"
DM_M = 0.1

corr = np.load(WORK / "correspondence.npz")
B = corr["mh_mask"].astype(np.float64)
h_star = float(corr["h_star"])
mh_tris = corr["mh_tris"].astype(np.int64)
mh_crotch, mh_neck = [float(x) for x in corr["mh_landmarks"]]
L_mh = mh_neck - mh_crotch
D3 = np.load(WORK / "belly_v3.npz")["delta_v3_canonical_m"].astype(np.float64)
D4 = np.load(WORK / "belly_v4.npz")["delta_v4_canonical_m"].astype(np.float64)

with zipfile.ZipFile(MPFB_ZIP) as z:
    obj_lines = z.read("mpfb/data/3dobjs/base.obj").decode().splitlines()
mh_obj = np.array([[float(x) for x in l.split()[1:4]]
                   for l in obj_lines if l.startswith("v ")])
mh_pos = np.stack([mh_obj[:, 0], mh_obj[:, 2], mh_obj[:, 1]], axis=1) * DM_M
BODY_END = 13380
mh_body = np.zeros(len(mh_pos), bool); mh_body[:BODY_END] = True

def compute_axis(pos, gate):
    hgt = pos[:, 2]
    lo, hi = hgt[gate].min(), hgt[gate].max()
    edges = np.linspace(lo, hi, 81)
    ctr = 0.5 * (edges[:-1] + edges[1:])
    axis = np.full((len(ctr), 2), np.nan)
    for i, (a, b) in enumerate(zip(edges[:-1], edges[1:])):
        m = gate & (hgt >= a) & (hgt < b) & (np.abs(pos[:, 0]) < 0.23)
        if m.sum() >= 4:
            axis[i] = [0.5 * (pos[m, 0].min() + pos[m, 0].max()),
                       0.5 * (pos[m, 1].min() + pos[m, 1].max())]
    ok = ~np.isnan(axis[:, 0])
    for c in range(2):
        axis[:, c] = np.interp(ctr, ctr[ok], axis[ok, c])
    k = np.ones(5) / 5
    for c in range(2):
        axis[:, c] = np.convolve(np.pad(axis[:, c], 2, mode="edge"), k, "valid")
    return ctr, axis
mh_ctr, mh_axis = compute_axis(mh_pos, mh_body)
ax = np.stack([np.interp(mh_pos[:, 2], mh_ctr, mh_axis[:, 0]),
               np.interp(mh_pos[:, 2], mh_ctr, mh_axis[:, 1])], axis=1)
rel = mh_pos[:, :2] - ax
mh_r = np.linalg.norm(rel, axis=1)
mh_th = np.arctan2(rel[:, 0], rel[:, 1])
mh_h = (mh_pos[:, 2] - mh_crotch) / L_mh
er = np.stack([np.sin(mh_th), np.cos(mh_th)], axis=1)
torso_gate = mh_body & (mh_r < 0.30)

step = 0.0125
zs = np.arange(mh_crotch - 0.05, mh_neck + 0.02, step)
def width_at(P, z):
    m = torso_gate & (np.abs(mh_pos[:, 2] - z) < step * 0.75)
    if m.sum() < 8:
        return np.nan
    return float(P[m, 0].max() - P[m, 0].min())
W0 = np.array([width_at(mh_pos, z) for z in zs])
W3 = np.array([width_at(mh_pos + D3, z) for z in zs])
W4 = np.array([width_at(mh_pos + D4, z) for z in zs])
hh = (zs - mh_crotch) / L_mh
print(f"h_star (navel) = {h_star:.3f}; torso L = {L_mh*100:.1f} cm")
print("  h     base   v3    v4   (width cm)   v4-base")
for i in range(0, len(zs), 2):
    if np.isnan(W0[i]):
        continue
    print(f"{hh[i]:+.3f}  {W0[i]*100:5.1f} {W3[i]*100:5.1f} {W4[i]*100:5.1f}   "
          f"{(W4[i]-W0[i])*100:+5.1f}")

# ---- M2' apron bottom
def apron_bottom(D):
    drad = np.einsum("ij,ij->i", D[:, :2], er)
    sel = torso_gate & (np.abs(mh_th) < 0.7) & (drad > 0.02)
    zmin = float((mh_pos[sel, 2] + D[sel, 2]).min())
    return (zmin - mh_crotch) * 100
print(f"\nM2' apron bottom above crotch: v3 {apron_bottom(D3):.2f} cm, "
      f"v4 {apron_bottom(D4):.2f} cm")

# ---- M4' gradient ratio in ring bands
ring = np.zeros(len(zs), bool)
for i, z in enumerate(zs):
    m = torso_gate & (np.abs(mh_pos[:, 2] - z) < step * 0.75)
    if m.sum() >= 8:
        bmax = B[m].max()
        ring[i] = 0.05 < bmax < 0.95
def max_grad(W):
    g = np.abs(np.diff(W)) / step
    idx = np.where(ring[1:-1])[0]
    return float(np.nanmax(g[idx])) if len(idx) else float("nan")
print(f"M4' ring max |dW/dz|: base {max_grad(W0):.2f} m/m, v3 "
      f"{max_grad(W3):.2f}, v4 {max_grad(W4):.2f} -> ratios v3 "
      f"{max_grad(W3)/max_grad(W0):.2f}, v4 {max_grad(W4)/max_grad(W0):.2f}")

# ---- M7b' interior local minima of the width profile
def local_minima(W, label):
    win = (hh > h_star + 0.02) & (hh < h_star + 0.34)
    out = []
    for i in range(1, len(zs) - 1):
        if not win[i] or np.isnan(W[i]):
            continue
        if W[i] <= W[i - 1] and W[i] <= W[i + 1]:
            lo = (hh > hh[i] - 0.11) & (hh < hh[i] - 0.05)
            hi = (hh > hh[i] + 0.05) & (hh < hh[i] + 0.11)
            if lo.any() and hi.any():
                depth = min(np.nanmax(W[lo]), np.nanmax(W[hi])) - W[i]
                out.append((round(float(hh[i]), 3), round(float(depth) * 100, 2)))
    print(f"M7b' {label} interior width minima in waist window: {out}")
local_minima(W0, "base")
local_minima(W3, "v3  ")
local_minima(W4, "v4  ")

# flank-specific: width at the waist heights from the SIDE silhouette is
# the same width profile; also report depth profile minima (front/back)
def depth_at(P, z):
    m = torso_gate & (np.abs(mh_pos[:, 2] - z) < step * 0.75)
    if m.sum() < 8:
        return np.nan
    return float(P[m, 1].max() - P[m, 1].min())
print("\ndepth profile (cm) at selected heights:")
for hq in (0.30, 0.40, 0.478, 0.55, 0.65, 0.75, 0.85):
    z = mh_crotch + hq * L_mh
    print(f"  h {hq:.3f}: base {depth_at(mh_pos, z)*100:5.1f}  "
          f"v3 {depth_at(mh_pos + D3, z)*100:5.1f}  "
          f"v4 {depth_at(mh_pos + D4, z)*100:5.1f}")
