#!/usr/bin/env python3
"""
Belly v3 builder: REALISTIC GRAVITY pass over the v1 transfer + v2 sag.

Joe on v2: "needs realistic gravity, this floats too much." v2's sag was
a polite downward nudge on a dome. A real heavy belly is a PENDANT mass:

  * it DRAINS: the upper abdomen gives up volume (top flattens/hollows),
  * the navel is dragged DOWN hard (target 7-9 cm at +1, vs v2's 2.95),
  * the apex sits well below the navel,
  * below the crease the tissue DRAPES: down AND inward along a hanging
    curve, so the silhouette's lowest point tucks back toward the body
    (a hanging apron with a deep, shadowed crease).

v3 model (same decomposition as v2, new field):

    shape(w) = base + w * D_protrusion + f(w) * D_sag3,
    f(w) = sign(w) * |w|^2.0      (drape engages late; f(0.5) = 0.25)

  D_sag3 = drain + gain * (descent + drape), with
  * mobility3: steeper, higher field (peak below the navel, cap ~1.0);
  * descent: -mob * p * (1 + 0.25 * umbilical) downward, gain solved so
    the navel drops 8.0 cm pre-repair;
  * drape: below the crease line h_c = h* - 0.16, a ramp
    t = clip((h_c - h)/0.22)^1.3 adds downward pull (0.85 * mob * p * t)
    AND an inward tuck (1.05 * mob * p * t on top of the 0.30 sub-crease
    tuck), soft-floored so tissue never passes through the body surface;
  * drain: upper-belly rows (h > h* - 0.02) surrender 45% of their
    outward delta, weighted by mask x angular profile x height ramp --
    mass leaves the dome because it went somewhere: down.
  * volume: radial compensation on the mid band tracks v1's added patch
    volume; re-solved once more after fold repair (guarded by the flip
    check) so the shipped field stays volume-true.
  * fold control: slope limiter (as v2) + ATTENUATION repair (v2's
    finding: Laplacian repair manufactures steps on field-modulated
    morphs). If full drape will not repair clean, the drape factor is
    bisected down (0.8 / 0.65 / 0.5) and the shipped factor reported.
    0 flips at +1 on both bases is a HARD gate.
  * NO navel micro-pin: the forward anchor is reported as the true
    vector. Draining costs a little forward travel at the navel; that
    trade is the physics, and it is reported, not hidden.

QA adds PROFILE METRICS for v1/v2/v3 from a binned silhouette curve:
apex height of the added-protrusion profile vs the navel, upper-belly
protrusion (the drain readout), crease depth and lowest-point tuck,
plus zone-split residuals (v1 method).
"""
import json
import zipfile
from pathlib import Path

import numpy as np
import scipy.sparse as sp
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
OUT = HERE.parent
WORK = OUT / "work"
LEARNED = Path.home() / "workspace/character_assets/learned"
MPFB_ZIP = Path.home() / "workspace/stick-figure-avatar/photoreal/tools/mpfb2.zip"

SK_UNIT_M = 0.01428
DM_M = 0.1

# v3 model constants (documented in GRAVITY_V3.md)
GAMMA3 = 2.0          # coupling exponent (drape engages late)
CREASE_DH3 = 0.16     # crease line below navel (torso-h units)
DRAPE_SPAN = 0.22     # h-units over which the drape ramp saturates
DRAPE_DOWN = 0.85     # extra downward pull at full drape, per unit p
DRAPE_TUCK = 1.05     # inward tuck at full drape, per unit p
TUCK0 = 0.30          # base sub-crease inward tuck, per unit p
DRAIN_FRAC = 0.45     # upper-belly outward surrender fraction
UMB3 = 0.25           # umbilical descent bonus at the navel
NAV_DROP_TARGET = 0.115   # m, pre-repair navel drop the gain solves for
# (attenuation repair kept 80% of the drop at the 8.0 target and 69% at
# 9.8 -- the stronger the field, the more faces it must soften. The solve
# therefore aims at 11.5 pre-repair for a ~7.5-8 shipped drop, inside
# the 7-9 cm band. Iterations documented in GRAVITY_V3.md.)
GAIN_CAP = 1.6
KAPPA = 0.55          # slope limiter, as v2

# ---------------------------------------------------------------- load v1/v2
corr = np.load(WORK / "correspondence.npz")
D1 = corr["mh_delta_canonical_m"].astype(np.float64)
mask = corr["mh_mask"].astype(np.float64)
navel_mh = int(corr["navel_mh"])
h_star = float(corr["h_star"])
mh_tris = corr["mh_tris"].astype(np.int64)
belly_face = corr["belly_face_mask"].astype(bool)
mh_crotch, mh_neck = [float(x) for x in corr["mh_landmarks"]]
L_mh = mh_neck - mh_crotch
D2 = np.load(WORK / "belly_v2.npz")["delta_v2_canonical_m"].astype(np.float64)

src = np.load(LEARNED / "fat-males_body_morph.npz")
sk_pos = src["body_vertices"].astype(np.float64) * SK_UNIT_M
sk_delta = src["body_delta"].astype(np.float64) * SK_UNIT_M

qa1 = json.loads((WORK / "qa_numbers.json").read_text())
anchor = qa1["anchor_m"]
L_sk = qa1["landmarks"]["skyrim"][1] - qa1["landmarks"]["skyrim"][0]

with zipfile.ZipFile(MPFB_ZIP) as z:
    obj_lines = z.read("mpfb/data/3dobjs/base.obj").decode().splitlines()
mh_obj = np.array([[float(x) for x in l.split()[1:4]]
                   for l in obj_lines if l.startswith("v ")])
mh_faces = []
for l in obj_lines:
    if l.startswith("f "):
        mh_faces.append([int(t.split("/")[0]) - 1 for t in l.split()[1:]])
mh_pos = np.stack([mh_obj[:, 0], mh_obj[:, 2], mh_obj[:, 1]], axis=1) * DM_M
BODY_END = 13380
mh_body = np.zeros(len(mh_pos), bool); mh_body[:BODY_END] = True
mh_pos_mac = mh_pos.copy()
_mac = np.load(WORK / "mh_macro_base.npz")["pos_canonical_m"]
mh_pos_mac[:len(_mac)] = _mac

# ------------------------------------------------- torso params (from v1/v2)
def compute_axis(pos, mask_=None):
    if mask_ is None:
        mask_ = np.ones(len(pos), bool)
    hgt = pos[:, 2]
    lo, hi = hgt[mask_].min(), hgt[mask_].max()
    edges = np.linspace(lo, hi, 81)
    ctr = 0.5 * (edges[:-1] + edges[1:])
    axis = np.full((len(ctr), 2), np.nan)
    for i, (a, b) in enumerate(zip(edges[:-1], edges[1:])):
        m = mask_ & (hgt >= a) & (hgt < b) & (np.abs(pos[:, 0]) < 0.23)
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

def axis_at(ctr, axis, hgt):
    return np.stack([np.interp(hgt, ctr, axis[:, 0]),
                     np.interp(hgt, ctr, axis[:, 1])], axis=1)

def torso_params(pos, ctr, axis, crotch, neck):
    ax = axis_at(ctr, axis, pos[:, 2])
    rel = pos[:, :2] - ax
    r = np.linalg.norm(rel, axis=1)
    theta = np.arctan2(rel[:, 0], rel[:, 1])
    h = (pos[:, 2] - crotch) / (neck - crotch)
    return h, theta, ax, r

mh_ctr, mh_axis = compute_axis(mh_pos, mh_body)
mh_h, mh_th, mh_ax, mh_r = torso_params(mh_pos, mh_ctr, mh_axis, mh_crotch, mh_neck)
sk_ctr, sk_axis = compute_axis(sk_pos)
sk_crotch, sk_neck = qa1["landmarks"]["skyrim"]
sk_h, sk_th, sk_ax, sk_r = torso_params(sk_pos, sk_ctr, sk_axis, sk_crotch, sk_neck)

edges = np.vstack([mh_tris[:, [0, 1]], mh_tris[:, [1, 2]], mh_tris[:, [2, 0]]])
edges = np.unique(np.sort(edges, axis=1), axis=0)
A = sp.coo_matrix((np.ones(len(edges)), (edges[:, 0], edges[:, 1])),
                  shape=(len(mh_pos), len(mh_pos)))
A = A + A.T
deg = np.asarray(A.sum(axis=1)).ravel()
Lop = sp.diags(1.0 / np.maximum(deg, 1)) @ A
nbrs = [np.asarray(A[v].nonzero()[1]) for v in range(len(mh_pos))]

er = np.stack([np.sin(mh_th), np.cos(mh_th)], axis=1)     # radial unit (XY)
p_rad = np.einsum("ij,ij->i", D1[:, :2], er)              # radial protrusion
p_clip = np.clip(p_rad, 0, None)
dmag = np.linalg.norm(D1, axis=1)
prof_ang = np.clip((np.cos(mh_th) + 0.35) / 1.35, 0, 1)   # front-weighted

# fold machinery (defined early: repair is a function now)
def face_normals(P, F):
    n = np.cross(P[F[:, 1]] - P[F[:, 0]], P[F[:, 2]] - P[F[:, 0]])
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-14)
Fb = mh_tris[belly_face]
BASES = {"raw": mh_pos, "macro": mh_pos_mac}
n0_all = {k: face_normals(p, Fb) for k, p in BASES.items()}
def flips(delta, bname):
    nn = face_normals(BASES[bname] + delta, Fb)
    dots = np.einsum("ij,ij->i", n0_all[bname], nn)
    return int((dots < 0).sum()), float(dots.min())

# ---------------------------------------------------------------- mobility v3
massf3 = 0.45 + 0.55 * (dmag / max(dmag[mask > 0.5].max(), 1e-9))
gauss3 = np.exp(-((mh_h - (h_star - 0.10)) / 0.16) ** 2)
prof_h3 = (0.35 + 0.65 * gauss3)
prof_h3 *= np.clip((0.72 - mh_h) / 0.08, 0, 1)             # ribcage anchor
prof_h3 *= np.clip((mh_h - 0.16) / 0.10, 0, 1)             # pelvis anchor (lower)
mob3 = mask * prof_ang * prof_h3 * massf3
mob3[mask <= 0.003] = 0.0
for _ in range(4):                                        # smooth (painted)
    sm = Lop @ mob3
    mob3 = np.where(mask > 0.003, 0.5 * mob3 + 0.5 * sm, 0.0)
mob3 = np.clip(mob3, 0, 1)
print(f"mobility v3: max {mob3.max():.3f}, at navel {mob3[navel_mh]:.3f}, "
      f"verts > 0.05: {(mob3 > 0.05).sum()} (v2: max 0.896, navel 0.590, 266)")

# ---------------------------------------------------------------- sag field v3
h_c = h_star - CREASE_DH3
gate = np.clip((h_c - mh_h) / 0.10, 0, 1)                 # 1 below crease
t_dr = np.clip((h_c - mh_h) / DRAPE_SPAN, 0, 1) ** 1.3    # drape ramp
navel_k = np.exp(-0.5 * (((mh_h - h_star) / 0.045) ** 2 +
                         ((np.abs(mh_th) * mh_r / L_mh) / 0.035) ** 2))
drain_w = mask * prof_ang * np.clip((mh_h - (h_star - 0.02)) / 0.18, 0, 1)
lim = np.where(p_rad > 0.01, p_rad + 0.006, 0.016)        # soft body floor

def build_sag(gain, drape_s):
    down = mob3 * p_clip * (1.0 + UMB3 * navel_k) \
        + drape_s * mob3 * t_dr * DRAPE_DOWN * p_clip
    Ds = np.zeros_like(D1)
    Ds[:, 2] = -gain * down
    rad = -(gain * mob3 * p_clip * (TUCK0 * gate
                                    + drape_s * DRAPE_TUCK * t_dr)
            + DRAIN_FRAC * drain_w * p_clip)
    neg = rad < 0
    rad[neg] = -lim[neg] * np.tanh(-rad[neg] / lim[neg])  # smooth floor
    Ds[:, :2] = rad[:, None] * er
    return Ds

Dsag_u = build_sag(1.0, 1.0)
drop1 = -Dsag_u[navel_mh, 2]
gain = min(NAV_DROP_TARGET / max(drop1, 1e-9), GAIN_CAP)
print(f"sag gain: unit-gain navel drop {drop1*100:.2f} cm -> gain {gain:.3f} "
      f"(target {NAV_DROP_TARGET*100:.1f} cm, cap {GAIN_CAP})")

be = np.array([e for e in np.unique(np.sort(np.vstack(
    [mh_tris[:, [0, 1]], mh_tris[:, [1, 2]], mh_tris[:, [2, 0]]]), axis=1), axis=0)
    if mask[e[0]] > 0.003 and mask[e[1]] > 0.003])
elen = np.linalg.norm(mh_pos[be[:, 0]] - mh_pos[be[:, 1]], axis=1)

def slope_limit(Ds):
    Ds = Ds.copy()
    for it in range(80):
        diff = Ds[be[:, 0]] - Ds[be[:, 1]]
        dn = np.linalg.norm(diff, axis=1)
        excess = dn - KAPPA * elen
        if (excess <= 0).all():
            return Ds, it
        corr_ = np.zeros_like(Ds)
        wgt = np.zeros(len(Ds))
        m_ = excess > 0
        adj = (0.5 * excess[m_] / np.maximum(dn[m_], 1e-12))[:, None] * diff[m_]
        np.add.at(corr_, be[m_, 0], -adj); np.add.at(corr_, be[m_, 1], adj)
        np.add.at(wgt, be[m_, 0], 1); np.add.at(wgt, be[m_, 1], 1)
        Ds += 0.7 * corr_ / np.maximum(wgt, 1)[:, None]
    return Ds, 80

# volume machinery (patch about the navel axis point, as v2)
z_nav = mh_pos[navel_mh, 2]
c0 = np.array([mh_ax[navel_mh, 0], mh_ax[navel_mh, 1], z_nav])
patch = np.array([f for f in mh_tris if mask[list(f)].min() > 0.003])
def patch_vol(P):
    a = P[patch[:, 0]] - c0; b = P[patch[:, 1]] - c0; c = P[patch[:, 2]] - c0
    return float(np.einsum("ij,ij->i", a, np.cross(b, c)).sum() / 6.0)
V0 = patch_vol(mh_pos)
V1 = patch_vol(mh_pos + D1)
target_added = V1 - V0
comp_w = mask * prof_ang * (1 - gate) * (1 - drain_w)
er3 = np.concatenate([er, np.zeros((len(er), 1))], axis=1)

def volume_solve(Ds, lo_b, hi_b):
    """Bisect a radial compensation so patch volume tracks v1's added
    volume. Returns (Ds_with_comp, comp, solved_bool)."""
    def added(comp):
        return patch_vol(mh_pos + D1 + Ds
                         + (comp * comp_w)[:, None] * er3) - V0
    g_lo = added(lo_b) - target_added
    g_hi = added(hi_b) - target_added
    if not (g_lo > 0 and g_hi < 0):
        return Ds, 0.0, False
    lo, hi = lo_b, hi_b
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        if added(mid) - target_added > 0:
            lo = mid
        else:
            hi = mid
    comp = 0.5 * (lo + hi)
    Ds2 = Ds.copy()
    Ds2[:, :2] += (comp * comp_w)[:, None] * er
    return Ds2, comp, True

def repair(Ds_raw, max_rounds=60):
    """Attenuation fold repair (v2's method): turn the sag DOWN locally
    where faces flip; direction preserved. Gentler att diffusion than
    v2 (1 pass, 0.35 blend) so a long repair stays local."""
    att = np.ones(len(Ds_raw))
    Ds = Ds_raw.copy()
    for rnd in range(max_rounds):
        D = D1 + Ds
        if flips(D, "raw")[0] == 0 and flips(D, "macro")[0] == 0:
            return Ds, att, True, rnd
        bad = np.zeros(len(Fb), bool)
        for k, p in BASES.items():
            nn = face_normals(p + D, Fb)
            dots = np.einsum("ij,ij->i", n0_all[k], nn)
            bad |= dots < 0.01
        bad_verts = np.unique(Fb[bad])
        ring = np.unique(np.concatenate([nbrs[v] for v in bad_verts]))
        att[bad_verts] *= 0.82
        att[ring] *= 0.94
        att = np.where(mask > 0.003, 0.65 * att + 0.35 * (Lop @ att), att)
        att = np.clip(att, 0.10, 1.0)
        Ds = att[:, None] * Ds_raw
    D = D1 + Ds
    ok = flips(D, "raw")[0] == 0 and flips(D, "macro")[0] == 0
    return Ds, att, ok, max_rounds

# ------------------------------------------------- build -> repair, drape bisect
drape_factor = None
for s_try in (1.0, 0.8, 0.65, 0.5):
    Dsag = build_sag(gain, s_try)
    for _ in range(5):                                    # smooth the field
        sm = Lop @ Dsag
        Dsag = Dsag + 0.35 * mask[:, None] * (sm - Dsag)
    Dsag[mask <= 0.003] = 0.0
    Dsag, lim_it = slope_limit(Dsag)
    Dsag, comp, solved = volume_solve(Dsag, -0.02, 0.05)
    pre = (flips(D1 + Dsag, "raw")[0], flips(D1 + Dsag, "macro")[0])
    Dsag, att, converged, rounds = repair(Dsag)
    print(f"drape {s_try}: limiter {lim_it} it, vol solved {solved} "
          f"(comp {comp*100:+.2f} cm), pre-repair flips raw/macro {pre}, "
          f"repair converged {converged} in {rounds} rounds, "
          f"att min {att.min():.2f}, navel drop "
          f"{-Dsag[navel_mh, 2]*100:.2f} cm")
    if converged:
        drape_factor = s_try
        break
assert drape_factor is not None, "no drape factor repaired clean"
D3 = D1 + Dsag

# post-repair volume re-solve (repair shrinks the field; restore the
# volume track with a small mid-band radial comp, flip-guarded)
Dsag2, comp2, solved2 = volume_solve(Dsag, -0.01, 0.02)
if solved2 and comp2 != 0.0:
    if flips(D1 + Dsag2, "raw")[0] == 0 and flips(D1 + Dsag2, "macro")[0] == 0:
        Dsag = Dsag2
        D3 = D1 + Dsag
        print(f"post-repair volume re-solve applied: comp2 {comp2*100:+.2f} cm")
    else:
        print("post-repair volume re-solve rejected (would fold); "
              "pre-repair track stands")
V3 = patch_vol(mh_pos + D3)
print(f"volume proxy: v1 adds {(V1-V0)*1e6:.1f} cm^3, v3 adds "
      f"{(V3-V0)*1e6:.1f} (ratio {(V3-V0)/(V1-V0):.3f})")

# ---------------------------------------------------------------- fold scans
f05 = 0.5 ** GAMMA3
states = {
    "-1 (linear)": -D3,
    "+0.5 (coupled)": 0.5 * D1 + f05 * Dsag,
    "+1 (combined)": D3,
    "+1.05 (combined)": 1.05 * D3,
}
fold_scan = {}
for name, D in states.items():
    fold_scan[name] = {b: flips(D, b) for b in BASES}
    print(f"fold scan {name}: raw {fold_scan[name]['raw']}, macro {fold_scan[name]['macro']}")

def navel_vec(D):
    return {"forward_cm": float(D[navel_mh, 1] * 100),
            "down_cm": float(-D[navel_mh, 2] * 100)}
nav = {"v1": navel_vec(D1), "v2": navel_vec(D2), "v3_at_+1": navel_vec(D3),
       "v3_at_+0.5_coupled": navel_vec(0.5 * D1 + f05 * Dsag),
       "sag3_at_navel_cm": {"down": float(-Dsag[navel_mh, 2] * 100),
                            "forward": float(Dsag[navel_mh, 1] * 100)},
       "anchor_forward_m": anchor,
       "v3_forward_error_mm": float(abs(D3[navel_mh, 1] - anchor) * 1000)}
print("navel:", json.dumps(nav, indent=1))

# ------------------------------------------------------------- profile metrics
def profile_metrics(D):
    """Per-vertex band statistics (no binning -- the binned silhouette
    proved too jittery at hm08's row density). All heights are DEFORMED
    heights; references are the base (anatomical) navel line and the
    deformed navel vertex, both reported."""
    drad = np.einsum("ij,ij->i", D[:, :2], er)
    z_def = mh_pos[:, 2] + D[:, 2]
    h_def = (z_def - mh_crotch) / L_mh
    z_nav0 = mh_pos[navel_mh, 2]
    z_navd = z_def[navel_mh]
    front = (mask > 0.3) & (np.abs(mh_th) < 0.5)
    w = np.clip(drad[front], 0, None)
    zz = z_def[front]
    mass_c = float((w * zz).sum() / max(w.sum(), 1e-12))
    up = (mask > 0.3) & (np.abs(mh_th) < 0.9) & \
        (mh_h > h_star + 0.03) & (mh_h < h_star + 0.20)
    upper = float(drad[up].mean()) * 100
    def band(hlo, hhi, use_def=True):
        hh = h_def if use_def else mh_h
        m_ = front & (hh > hlo) & (hh < hhi)
        return float(drad[m_].mean()) * 100 if m_.sum() >= 3 else None
    # bulge/crease/apron are MATERIAL bands (the crease is a feature of
    # the tissue, not of space): read them in BASE height, unlike the
    # spatial band profile above.
    bulge = band(h_c + 0.05, h_c + 0.17, use_def=False)
    crease = band(h_c - 0.035, h_c + 0.035, use_def=False)
    apron = band(h_c - 0.16, h_c - 0.06, use_def=False)
    pinch = None if (bulge in (None, 0) or crease is None) \
        else round(crease / bulge, 3)
    return {
        "mass_centroid_below_base_navel_cm": round((z_nav0 - mass_c) * 100, 2),
        "mass_centroid_below_deformed_navel_cm":
            round((z_navd - mass_c) * 100, 2),
        "upper_protrusion_cm": round(upper, 2),
        "bulge_extent_cm": None if bulge is None else round(bulge, 2),
        "crease_extent_cm": None if crease is None else round(crease, 2),
        "crease_pinch_ratio": pinch,
        "apron_bottom_extent_cm": None if apron is None else round(apron, 2),
    }

def band_profile(D):
    """Mean added radial extent by deformed-height band (front slice),
    labelled by cm below the BASE navel line -- the stable profile read."""
    drad = np.einsum("ij,ij->i", D[:, :2], er)
    h_def = (mh_pos[:, 2] + D[:, 2] - mh_crotch) / L_mh
    front = (mask > 0.3) & (np.abs(mh_th) < 0.5)
    rows = []
    for off in (0.10, 0.05, 0.0, -0.05, -0.10, -0.15, -0.20, -0.25, -0.30):
        m_ = front & (h_def > h_star + off - 0.025) & (h_def < h_star + off + 0.025)
        if m_.sum() >= 3:
            rows.append((round(-off * L_mh * 100), round(float(drad[m_].mean()) * 100, 1),
                         int(m_.sum())))
    return rows
prof = {"v1": profile_metrics(D1), "v2": profile_metrics(D2),
        "v3": profile_metrics(D3)}
print("profile metrics:", json.dumps(prof, indent=1))
for tag, D in (("v1", D1), ("v2", D2), ("v3", D3)):
    print(f"band profile {tag} (cm below base navel line: mean added "
          f"extent cm, n): " + ", ".join(f"{o:+d}:{e}({n})"
                                         for o, e, n in band_profile(D)))

# ------------------------------------------------------- zone-split residuals
def param_coords(pos, ctr, axis, crotch, L):
    h, th, ax, r = torso_params(pos, ctr, axis, crotch, crotch + L)
    return np.stack([th * r / L, h, r / L], axis=1)
sk_tri = src["body_triangles"].astype(np.int64)
skP_fat = param_coords(sk_pos + sk_delta, sk_ctr, sk_axis, sk_crotch, L_sk)
src_tris = []
for f in sk_tri:
    if np.all((sk_h[f] > -0.02) & (sk_h[f] < 1.02) & (sk_r[f] < 0.30)):
        u = skP_fat[f][:, 0]
        if np.max(u) - np.min(u) < 0.5:
            src_tris.append(f)
src_tris = np.array(src_tris)

def tri_closest(P, A, B, C):
    ab, ac, ap = B - A, C - A, P - A
    d1 = np.einsum("ij,ij->i", ab, ap); d2 = np.einsum("ij,ij->i", ac, ap)
    d3 = np.einsum("ij,ij->i", ab, ab); d4 = np.einsum("ij,ij->i", ab, ac)
    d5 = np.einsum("ij,ij->i", ac, ac)
    den = np.maximum(d3 * d5 - d4 * d4, 1e-14)
    vc = (d3 * d2 - d4 * d1) / den; vb = (d5 * d1 - d4 * d2) / den
    inside = (vb >= 0) & (vc >= 0) & (vb + vc <= 1)
    plane = A + vb[:, None] * ab + vc[:, None] * ac
    best = plane.copy()
    bestd = np.where(inside, np.linalg.norm(P - plane, axis=1), np.inf)
    for E0, E1 in ((A, B), (B, C), (C, A)):
        seg = E1 - E0
        t = np.einsum("ij,ij->i", P - E0, seg) / np.maximum(
            np.einsum("ij,ij->i", seg, seg), 1e-14)
        q = E0 + np.clip(t, 0, 1)[:, None] * seg
        dd = np.linalg.norm(P - q, axis=1)
        m_ = dd < bestd
        best[m_] = q[m_]; bestd[m_] = dd[m_]
    return best, bestd

class ParamSurface:
    def __init__(self, P, F):
        self.P, self.F = P, F
        self.tree = cKDTree(P)
        vf = {}
        for fi, f in enumerate(F):
            for v in f:
                vf.setdefault(int(v), []).append(fi)
        self.vf = vf
    def closest(self, Q, k=12):
        _, nn = self.tree.query(Q, k=k)
        out_c = np.empty_like(Q); out_d = np.empty(len(Q))
        for i, row in enumerate(nn):
            cand = np.unique(np.concatenate(
                [self.vf[int(v)] for v in row if int(v) in self.vf]))
            A = self.P[self.F[cand, 0]]; B = self.P[self.F[cand, 1]]
            C = self.P[self.F[cand, 2]]
            cp, dd = tri_closest(np.repeat(Q[i:i + 1], len(cand), axis=0), A, B, C)
            j = int(np.argmin(dd))
            out_c[i] = cp[j]; out_d[i] = dd[j]
        return out_c, out_d

src_surf = ParamSurface(skP_fat, src_tris)
def fwd_resid(delta):
    P = param_coords(mh_pos + delta, mh_ctr, mh_axis, mh_crotch, L_mh)
    core = np.where(mask > 0.5)[0]
    _, d = src_surf.closest(P[core])
    return core, d * L_sk * 100
core1, r3 = fwd_resid(D3)
qa2 = json.loads((WORK / "qa_numbers_v2.json").read_text())
pd_navel = np.sqrt(((mh_h[core1] - h_star) * L_mh) ** 2 +
                   (np.abs(mh_th[core1]) * mh_r[core1]) ** 2)
zones = {
    "pin_patch": pd_navel < 0.045,
    "crease": (pd_navel >= 0.045) & (mh_h[core1] < h_star - 0.08) & (np.abs(mh_th[core1]) < 1.05),
    "flank": (pd_navel >= 0.045) & ~((mh_h[core1] < h_star - 0.08) & (np.abs(mh_th[core1]) < 1.05)) & (np.abs(mh_th[core1]) >= 0.9),
}
zones["core"] = ~(zones["pin_patch"] | zones["crease"] | zones["flank"])
zone_rows = {}
for zn, zm in zones.items():
    if zm.sum() == 0:
        continue
    idx = core1[zm]
    z2 = qa2["zones"].get(zn, {})
    zone_rows[zn] = {
        "n": int(zm.sum()),
        "v1_p95_cm": z2.get("v1_p95_cm"), "v2_p95_cm": z2.get("v2_p95_cm"),
        "v3_p50_cm": float(np.percentile(r3[zm], 50)),
        "v3_p95_cm": float(np.percentile(r3[zm], 95)),
        "mean_abs_sag3_cm": float(np.linalg.norm(Dsag[idx], axis=1).mean() * 100),
        "mean_sag3_down_cm": float(-Dsag[idx, 2].mean() * 100),
    }
    print(f"zone {zn}: n={zm.sum()} v3 p95 {zone_rows[zn]['v3_p95_cm']:.2f} cm, "
          f"mean sag3 {zone_rows[zn]['mean_abs_sag3_cm']:.2f} cm")
allrow = {"n": int(len(core1)),
          "v3_p50_cm": float(np.percentile(r3, 50)),
          "v3_p95_cm": float(np.percentile(r3, 95)),
          "v1_p95_cm": qa2["zones_all_triangle_exact"]["v1_p95_cm"],
          "v2_p95_cm": qa2["zones_all_triangle_exact"]["v2_p95_cm"]}
print(f"zone ALL: v3 p95 {allrow['v3_p95_cm']:.2f} cm "
      f"(v1 {allrow['v1_p95_cm']}, v2 {allrow['v2_p95_cm']})")

# ---------------------------------------------------------------- write targets
def fmt(v):
    s = f"{abs(v):.3f}".rstrip("0")
    if s.endswith("."): s += "0"
    if s in ("", "0."): s = "0"
    return ("-" + s) if v < 0 else s
def write_target(path, delta, note):
    d_obj = np.stack([delta[:, 0], delta[:, 2], delta[:, 1]], axis=1) / DM_M
    moved = np.where(np.abs(d_obj).max(axis=1) > 0.001)[0]
    header = ("# This is a target file for MakeHuman\n#\n"
              "# It was written by the MakeTarget submodule of MPFB\n#\n"
              "# For more information, see MakeHuman's home page at "
              "http://www.makehumancommunity.org\n#\n# basemesh hm08\n"
              f"# {note}\n")
    with open(path, "w") as fh:
        fh.write(header)
        for i in moved:
            fh.write(f"{i} {fmt(d_obj[i,0])} {fmt(d_obj[i,1])} {fmt(d_obj[i,2])}\n")
    return int(len(moved))
NOTE3 = ("Provenance: omniversal slider body.belly.protrusion v3 (realistic "
         "gravity pass), instance makehuman_hm08. Combined field at w=+1: "
         "v1 protrusion + v3 sag (drain + pendant drape). Learned from the "
         "Fat Males body morph (study-only, internal - not a CC0 MakeHuman "
         "asset). See GRAVITY_V3.md.")
NOTES3 = ("Provenance: sag component of body.belly.protrusion v3 (realistic "
          "gravity). Apply with coupling f(w) = sign(w)|w|^2.0 alongside the "
          "v1 protrusion target. Study-only, internal.")
n_v3 = write_target(OUT / "body.belly.protrusion_v3.target", D3, NOTE3)
n_sag3 = write_target(OUT / "body.belly.protrusion_sag_v3.target", Dsag, NOTES3)
n_c05 = write_target(WORK / "target_coupled_v3_w0.5.target",
                     0.5 * D1 + f05 * Dsag, "QA harness artefact: coupled v3 shape at w=+0.5.")
print(f"targets written: v3 combined {n_v3} moved verts, sag3 {n_sag3}, coupled@0.5 {n_c05}")

np.savez(WORK / "belly_v3.npz", delta_v3_canonical_m=D3, sag3_canonical_m=Dsag,
         mobility3=mob3, navel_mh=navel_mh, gamma=GAMMA3, gain=gain,
         drape_factor=drape_factor)
qa3 = {
    "model": {"gamma_coupling": GAMMA3, "f_at_0.5": f05, "gain": float(gain),
              "drape_factor_shipped": drape_factor,
              "crease_h": float(h_c), "crease_dh": CREASE_DH3,
              "drape_span": DRAPE_SPAN, "drape_down": DRAPE_DOWN,
              "drape_tuck": DRAPE_TUCK, "tuck0": TUCK0,
              "drain_frac": DRAIN_FRAC, "umbilical": UMB3,
              "nav_drop_target_cm": NAV_DROP_TARGET * 100,
              "pre_repair_flips_raw_macro": list(pre),
              "attenuation": {"min": float(att.min()),
                              "verts_under_0.99": int((att < 0.99).sum()),
                              "rounds": rounds},
              "volume_comp_cm": float(comp * 100),
              "volume_comp2_cm": float(comp2 * 100) if solved2 else 0.0,
              "volume_proxy_cm3": {"base": V0 * 1e6, "v1_added": (V1 - V0) * 1e6,
                                   "v3_added": (V3 - V0) * 1e6,
                                   "v3_over_v1": float((V3 - V0) / (V1 - V0))}},
    "mobility3": {"max": float(mob3.max()), "at_navel": float(mob3[navel_mh]),
                  "verts_over_0.05": int((mob3 > 0.05).sum())},
    "navel": nav, "profile_metrics": prof,
    "fold_scan": {k: {b: {"flips": v[b][0], "min_dot": v[b][1]}
                      for b in BASES} for k, v in fold_scan.items()},
    "zones": zone_rows, "zones_all_triangle_exact": allrow,
    "moved_verts": {"v3_combined": n_v3, "sag3_component": n_sag3},
}
(WORK / "qa_numbers_v3.json").write_text(json.dumps(qa3, indent=1))
print("QA v3 saved")
