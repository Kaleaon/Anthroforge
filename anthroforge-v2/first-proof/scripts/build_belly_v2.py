#!/usr/bin/env python3
"""
Belly v2 builder: gravity/sag pass over the v1 Fat Males -> hm08 transfer.

v1 (build_target.py) reproduced the studied surface but the shape reads as a
straight-out protrusion: adipose tissue hangs. v2 keeps the v1 field as the
PROTRUSION component and adds a SAG component, computed by modulating a
gravity displacement with a painted-style MOBILITY field:

    shape(w) = base + w * Dv1 + f(w) * Dsag,   f(w) = sign(w) * |w|^GAMMA

so the sag is a separate, separately-stored component with a nonlinear
coupling (at +0.5 only ~31% of the full sag is present). The shipped
body.belly.protrusion_v2.target is the combined field at w = +1
(Dv1 + Dsag); body.belly.protrusion_sag.target is Dsag alone, so a host
(Blender driver / AnthroForge runtime) can apply the coupling live.

Sag model at w = +1 (canonical frame: X right, Y forward, Z up, metres):
  * mobility m(v) in [0,1]: belly mask x angular profile (front-weighted)
    x vertical profile (ribcage anchor above, pelvis-brim anchor below,
    peak in the sub-navel apron band) x mass factor (|Dv1| normalised);
    graph-Laplacian smoothed (painted fields are smooth).
  * downward:  Dsag_z = -m * ALPHA * p   (p = radial protrusion of Dv1)
    plus a mild umbilical-descent term near the navel.
  * overhang tuck: below the crease line h_c = h* - 0.13, lower rows also
    move inward: Dsag_r -= m * BETA * p * gate(h), forming the profile
    inflection (roll above, tucked apron below) without inverting faces.
  * approximate volume preservation: a radial compensation term inside
    the mask is solved (secant) so the belly patch's added volume matches
    v1's within ~1.5% (signed-tetra proxy about the navel axis point).

QA rerun: navel anchor (forward AND downward components), fold scans on
both bases (raw base.obj + MPFB default-macro base), and ZONE-SPLIT
residuals (core / navel pin patch / flank dead zone / under-belly crease)
per the v1 proof's recommendation -- v2 deliberately departs from the
studied surface by exactly the sag field, so residuals are reported for
v1 and v2 side by side with the mean sag per zone.
"""
import json
import sys
from pathlib import Path

import numpy as np
import scipy.sparse as sp

HERE = Path(__file__).resolve().parent
OUT = HERE.parent
V2 = OUT.parent
APP = V2.parent / "anthroforge-app"
for _p in (str(V2), str(APP)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from body_machinery import (  # noqa: E402
    BODY_END,
    DM_M,
    SK_UNIT_M,
    ParamSurface,
    axis_at,
    compute_axis,
    load_mpfb_base_obj,
    slope_limit_iter,
    torso_cylindrical as torso_params,
    tri_closest,
)
from core.geometry import face_normals, write_target  # noqa: E402

WORK = OUT / "work"
LEARNED = Path.home() / "workspace/character_assets/learned"
MPFB_ZIP = Path.home() / "workspace/stick-figure-avatar/photoreal/tools/mpfb2.zip"

# sag model constants (documented in GRAVITY_WEIGHTS.md)
ALPHA = 0.40        # downward sag per unit radial protrusion at m = 1
BETA = 0.35         # inward tuck below the crease, per unit protrusion
UMBILICAL = 0.12    # extra descent factor near the navel
GAMMA = 1.7         # coupling exponent: f(w) = sign(w) * |w|^GAMMA
CREASE_DH = 0.13    # crease line offset below navel, in torso-h units

# ---------------------------------------------------------------- load v1
corr = np.load(WORK / "correspondence.npz")
D1 = corr["mh_delta_canonical_m"].astype(np.float64)
mask = corr["mh_mask"].astype(np.float64)
navel_mh = int(corr["navel_mh"])
h_star = float(corr["h_star"])
mh_tris = corr["mh_tris"].astype(np.int64)
belly_face = corr["belly_face_mask"].astype(bool)
mh_crotch, mh_neck = [float(x) for x in corr["mh_landmarks"]]
L_mh = mh_neck - mh_crotch

src = np.load(LEARNED / "fat-males_body_morph.npz")
sk_pos = src["body_vertices"].astype(np.float64) * SK_UNIT_M
sk_delta = src["body_delta"].astype(np.float64) * SK_UNIT_M

qa1 = json.loads((WORK / "qa_numbers.json").read_text())
anchor = qa1["anchor_m"]
L_sk = qa1["landmarks"]["skyrim"][1] - qa1["landmarks"]["skyrim"][0]

# ---------------------------------------------------------------- load hm08
mh_pos, mh_faces = load_mpfb_base_obj(MPFB_ZIP, with_poly_faces=True)
mh_body = np.zeros(len(mh_pos), bool); mh_body[:BODY_END] = True
mh_pos_mac = mh_pos.copy()
_mac = np.load(WORK / "mh_macro_base.npz")["pos_canonical_m"]
mh_pos_mac[:len(_mac)] = _mac

# ------------------------------------------------- torso params (from v1)
mh_ctr, mh_axis = compute_axis(mh_pos, mh_body)
mh_h, mh_th, mh_ax, mh_r = torso_params(mh_pos, mh_ctr, mh_axis, mh_crotch, mh_neck)
sk_ctr, sk_axis = compute_axis(sk_pos)
sk_crotch, sk_neck = qa1["landmarks"]["skyrim"]
sk_h, sk_th, sk_ax, sk_r = torso_params(sk_pos, sk_ctr, sk_axis, sk_crotch, sk_neck)

# graph Laplacian (row-normalised adjacency), as in v1
edges = np.vstack([mh_tris[:, [0, 1]], mh_tris[:, [1, 2]], mh_tris[:, [2, 0]]])
edges = np.unique(np.sort(edges, axis=1), axis=0)
A = sp.coo_matrix((np.ones(len(edges)), (edges[:, 0], edges[:, 1])),
                  shape=(len(mh_pos), len(mh_pos)))
A = A + A.T
deg = np.asarray(A.sum(axis=1)).ravel()
Lop = sp.diags(1.0 / np.maximum(deg, 1)) @ A
nbrs = [np.asarray(A[v].nonzero()[1]) for v in range(len(mh_pos))]

# ---------------------------------------------------------------- mobility
er = np.stack([np.sin(mh_th), np.cos(mh_th)], axis=1)     # radial unit (XY)
p_rad = np.einsum("ij,ij->i", D1[:, :2], er)              # radial protrusion
p_clip = np.clip(p_rad, 0, None)
dmag = np.linalg.norm(D1, axis=1)
massf = 0.30 + 0.70 * (dmag / max(dmag[mask > 0.5].max(), 1e-9))

prof_ang = np.clip((np.cos(mh_th) + 0.35) / 1.35, 0, 1)   # front-weighted
gauss = np.exp(-((mh_h - (h_star - 0.06)) / 0.15) ** 2)
prof_h = (0.25 + 0.75 * gauss)
prof_h *= np.clip((0.70 - mh_h) / 0.08, 0, 1)              # ribcage anchor
prof_h *= np.clip((mh_h - 0.22) / 0.08, 0, 1)              # pelvis anchor

mob = mask * prof_ang * prof_h * massf
mob[mask <= 0.003] = 0.0
for _ in range(6):                                        # smooth (painted)
    sm = Lop @ mob
    mob = np.where(mask > 0.003, 0.5 * mob + 0.5 * sm, 0.0)
mob = np.clip(mob, 0, 1)
print(f"mobility: max {mob.max():.3f}, at navel {mob[navel_mh]:.3f}, "
      f"verts > 0.05: {(mob > 0.05).sum()}")

# ---------------------------------------------------------------- sag field
h_c = h_star - CREASE_DH
gate = np.clip((h_c - mh_h) / 0.10, 0, 1)                 # 1 below crease
navel_k = np.exp(-0.5 * (((mh_h - h_star) / 0.045) ** 2 +
                         ((np.abs(mh_th) * mh_r / L_mh) / 0.035) ** 2))
Dsag = np.zeros_like(D1)
Dsag[:, 2] = -mob * p_clip * (ALPHA + UMBILICAL * navel_k)
Dsag[:, :2] = (-mob * BETA * p_clip * gate)[:, None] * er
# bound the sag field's own gradient: a real crease is a smooth inflection,
# not a vertex-scale kink -- an unsmoothed gate kink at h_c folds faces.
for _ in range(4):
    sm = Lop @ Dsag
    Dsag = Dsag + 0.35 * mask[:, None] * (sm - Dsag)
Dsag[mask <= 0.003] = 0.0
# slope limiter: |Dsag(u) - Dsag(v)| <= KAPPA * |edge| on belly edges.
# Diagnosed on the failing faces: a -1.23 cm sag step across a 0.82 cm
# edge at the crease shears the face past inversion; v1's field has no
# such step, so the limiter applies to the added sag component only.
KAPPA = 0.55
be = np.array([e for e in np.unique(np.sort(np.vstack(
    [mh_tris[:, [0, 1]], mh_tris[:, [1, 2]], mh_tris[:, [2, 0]]]), axis=1), axis=0)
    if mask[e[0]] > 0.003 and mask[e[1]] > 0.003])
elen = np.linalg.norm(mh_pos[be[:, 0]] - mh_pos[be[:, 1]], axis=1)
Dsag, _lim_it = slope_limit_iter(Dsag, be, mh_pos, kappa=KAPPA, max_iters=80)
if _lim_it < 80:
    print(f"slope limiter: clean after {_lim_it} iterations")
else:
    _excess = np.linalg.norm(Dsag[be[:, 0]] - Dsag[be[:, 1]], axis=1) - KAPPA * elen
    print(f"slope limiter: 80 iterations, residual max excess "
          f"{float(_excess.max())*100:.2f} cm")

# approximate volume preservation: radial compensation solved on the
# belly patch's signed-tetra volume about the navel axis point
z_nav = mh_pos[navel_mh, 2]
c0 = np.array([mh_ax[navel_mh, 0], mh_ax[navel_mh, 1], z_nav])
patch = np.array([f for f in mh_tris if mask[list(f)].min() > 0.003])
def patch_vol(P):
    a = P[patch[:, 0]] - c0; b = P[patch[:, 1]] - c0; c = P[patch[:, 2]] - c0
    return float(np.einsum("ij,ij->i", a, np.cross(b, c)).sum() / 6.0)
V0 = patch_vol(mh_pos)
V1 = patch_vol(mh_pos + D1)
comp_w = mask * prof_ang * (1 - 0.7 * gate)
er3 = np.concatenate([er, np.zeros((len(er), 1))], axis=1)
def added_vol(comp):
    return patch_vol(mh_pos + D1 + Dsag + (comp * comp_w)[:, None] * er3) - V0
# signed volumes are negative with this winding; added volume DECREASES
# (grows in magnitude) as comp increases. Bisect g(comp) = added - target.
target_added = V1 - V0
lo, hi = -0.01, 0.03
g_lo = added_vol(lo) - target_added
g_hi = added_vol(hi) - target_added
assert g_lo > 0 and g_hi < 0, f"volume bracket wrong: g_lo {g_lo:.2e}, g_hi {g_hi:.2e}"
for _ in range(40):
    mid = 0.5 * (lo + hi)
    if added_vol(mid) - target_added > 0:
        lo = mid
    else:
        hi = mid
comp = 0.5 * (lo + hi)
Dsag[:, :2] += (comp * comp_w)[:, None] * er
V2 = patch_vol(mh_pos + D1 + Dsag)
print(f"volume proxy: base {V0*1e6:.1f} cm^3, v1 adds {(V1-V0)*1e6:.1f}, "
      f"v2 adds {(V2-V0)*1e6:.1f} (comp {comp*100:+.2f} cm radial, "
      f"ratio {(V2-V0)/(V1-V0):.3f})")

D2 = D1 + Dsag

# ---------------------------------------------------------------- fold QA
Fb = mh_tris[belly_face]
BASES = {"raw": mh_pos, "macro": mh_pos_mac}
n0_all = {k: face_normals(p, Fb) for k, p in BASES.items()}
def flips(delta, bname):
    nn = face_normals(BASES[bname] + delta, Fb)
    dots = np.einsum("ij,ij->i", n0_all[bname], nn)
    return int((dots < 0).sum()), float(dots.min())
def bad_faces(delta, thresh=0.03):
    bad = np.zeros(len(Fb), bool); mind = 1.0
    for k, p in BASES.items():
        nn = face_normals(p + delta, Fb)
        dots = np.einsum("ij,ij->i", n0_all[k], nn)
        bad |= dots < thresh; mind = min(mind, float(dots.min()))
    return bad, mind

_d = np.linalg.norm(Dsag[be[:, 0]] - Dsag[be[:, 1]], axis=1) - KAPPA * elen
print(f"pre-repair: sag max edge excess {float(_d.max())*100:.3f} cm, "
      f"flips raw {flips(D2, 'raw')[0]}, macro {flips(D2, 'macro')[0]}")
# Fold repair by ATTENUATION, not smoothing: v1's field sits at min_dot
# ~0.06, so marginal faces flip under any added gradient -- but Laplacian
# smoothing of the combined field drags grow-set boundary verts along the
# sag gradient and manufactures new steps (diagnosed: a -1.23 cm step
# re-created at the crease edge). Instead, turn the sag DOWN locally via
# a smooth attenuation field a(v) -- the same operation as painting
# influence weight down in dForce / Chaos Cloth.
Dsag_raw = Dsag.copy()
att = np.ones(len(Dsag))
def flips_both(D):
    return flips(D, "raw"), flips(D, "macro")
for rnd in range(80):
    (fr, mr), (fm, mm) = flips_both(D2)
    if fr == 0 and fm == 0:
        print(f"attenuation repair: clean after {rnd} rounds "
              f"(min_dot raw {mr:.3f}, macro {mm:.3f}); "
              f"att min {att.min():.2f}, verts att<0.99: {(att < 0.99).sum()}")
        break
    bad = np.zeros(len(Fb), bool)
    for k, p in BASES.items():
        nn = face_normals(p + D2, Fb)
        dots = np.einsum("ij,ij->i", n0_all[k], nn)
        bad |= dots < 0.01
    bad_verts = np.unique(Fb[bad])
    ring = np.unique(np.concatenate([nbrs[v] for v in bad_verts]))
    att[bad_verts] *= 0.82
    att[ring] *= 0.94
    for _ in range(2):
        att = np.where(mask > 0.003, 0.5 * att + 0.5 * (Lop @ att), att)
    att = np.clip(att, 0.10, 1.0)
    Dsag = att[:, None] * Dsag_raw
    D2 = D1 + Dsag
else:
    (fr, mr), (fm, mm) = flips_both(D2)
    print(f"attenuation repair: rounds exhausted (raw flips {fr}, macro {fm}); "
          f"att min {att.min():.2f}")

# guarded re-pin of the navel FORWARD anchor if repair drifted it
deficit = anchor - float(D2[navel_mh, 1])
if abs(deficit) > 0.002:
    u_act = np.abs(mh_th) * mh_r / L_mh
    pin_k = np.exp(-0.5 * (((mh_h - h_star) / 0.045) ** 2 + (u_act / 0.035) ** 2))
    trial = D2.copy()
    add = np.zeros_like(D2)
    add[:, :2] = ((deficit / max(er[navel_mh, 1], 0.5)) * pin_k)[:, None] * er
    trial += add
    if flips(trial, "raw")[0] == 0 and flips(trial, "macro")[0] == 0:
        D2 = trial; Dsag = D2 - D1
        print(f"micro-pin applied: {deficit*100:+.2f} cm forward at navel")
    else:
        print(f"micro-pin rejected (would fold); deficit {deficit*100:+.2f} cm stands")

f05 = 0.5 ** GAMMA
states = {
    "-1 (linear)": -D2,
    "+0.5 (coupled)": 0.5 * D1 + f05 * Dsag,
    "+1 (combined)": D2,
    "+1.05 (combined)": 1.05 * D2,
}
fold_scan = {}
for name, D in states.items():
    fold_scan[name] = {b: flips(D, b) for b in BASES}
    print(f"fold scan {name}: raw {fold_scan[name]['raw']}, macro {fold_scan[name]['macro']}")

nav = {
    "v1": {"forward_cm": float(D1[navel_mh, 1] * 100),
           "down_cm": float(-D1[navel_mh, 2] * 100)},
    "v2_at_+1": {"forward_cm": float(D2[navel_mh, 1] * 100),
                 "down_cm": float(-D2[navel_mh, 2] * 100),
                 "forward_error_mm": float(abs(D2[navel_mh, 1] - anchor) * 1000)},
    "v2_at_+0.5_coupled": {
        "forward_cm": float((0.5 * D1[navel_mh, 1] + f05 * Dsag[navel_mh, 1]) * 100),
        "down_cm": float(-(0.5 * D1[navel_mh, 2] + f05 * Dsag[navel_mh, 2]) * 100)},
    "sag_at_navel_cm": {"down": float(-Dsag[navel_mh, 2] * 100),
                        "forward": float(Dsag[navel_mh, 1] * 100)},
}
print("navel:", json.dumps(nav, indent=1))

# ------------------------------------------------------- zone-split residuals
# Triangle-exact forward residuals in torso-param space, same machinery
# and metric as the v1 proof (result verts -> closest point on the source
# fat surface), so v1 and v2 numbers are directly comparable.
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

src_surf = ParamSurface(skP_fat, src_tris)
def fwd_resid(delta):
    P = param_coords(mh_pos + delta, mh_ctr, mh_axis, mh_crotch, L_mh)
    core = np.where(mask > 0.5)[0]
    _, d = src_surf.closest(P[core])
    return core, d * L_sk * 100  # cm
core1, r1 = fwd_resid(D1)
_, r2 = fwd_resid(D2)
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
    zone_rows[zn] = {
        "n": int(zm.sum()),
        "v1_p50_cm": float(np.percentile(r1[zm], 50)),
        "v1_p95_cm": float(np.percentile(r1[zm], 95)),
        "v2_p50_cm": float(np.percentile(r2[zm], 50)),
        "v2_p95_cm": float(np.percentile(r2[zm], 95)),
        "mean_abs_sag_cm": float(np.linalg.norm(Dsag[idx], axis=1).mean() * 100),
        "mean_sag_down_cm": float(-Dsag[idx, 2].mean() * 100),
    }
    print(f"zone {zn}: n={zm.sum()} v1 p95 {zone_rows[zn]['v1_p95_cm']:.2f} cm, "
          f"v2 p95 {zone_rows[zn]['v2_p95_cm']:.2f} cm, mean sag "
          f"{zone_rows[zn]['mean_abs_sag_cm']:.2f} cm (down "
          f"{zone_rows[zn]['mean_sag_down_cm']:.2f})")
allrow = {"n": int(len(core1)),
          "v1_p50_cm": float(np.percentile(r1, 50)), "v1_p95_cm": float(np.percentile(r1, 95)),
          "v2_p50_cm": float(np.percentile(r2, 50)), "v2_p95_cm": float(np.percentile(r2, 95))}
print(f"zone ALL (triangle-exact, recomputed): v1 p95 {allrow['v1_p95_cm']:.2f} cm "
      f"(v1 doc: 1.394), v2 p95 {allrow['v2_p95_cm']:.2f} cm")

# ---------------------------------------------------------------- write targets
NOTE2 = ("Provenance: omniversal slider body.belly.protrusion v2 (gravity pass), "
         "instance makehuman_hm08. Combined field at w=+1: v1 protrusion + sag "
         "component. Learned from the Fat Males body morph (study-only, internal "
         "- not a CC0 MakeHuman asset). See GRAVITY_WEIGHTS.md.")
NOTES = ("Provenance: sag component of body.belly.protrusion v2 (gravity pass). "
         "Apply with coupling f(w) = sign(w)|w|^1.7 alongside the v1 protrusion "
         "target. Study-only, internal.")
n_v2 = write_target(OUT / "body.belly.protrusion_v2.target", D2, NOTE2)
n_sag = write_target(OUT / "body.belly.protrusion_sag.target", Dsag, NOTES)
n_c05 = write_target(WORK / "target_coupled_w0.5.target",
                     0.5 * D1 + f05 * Dsag, "QA harness artefact: coupled v2 shape at w=+0.5.")
print(f"targets written: v2 combined {n_v2} moved verts, sag {n_sag}, coupled@0.5 {n_c05}")

np.savez(WORK / "belly_v2.npz", delta_v2_canonical_m=D2, sag_canonical_m=Dsag,
         mobility=mob, navel_mh=navel_mh, gamma=GAMMA)
qa2 = {
    "model": {"alpha": ALPHA, "beta": BETA, "umbilical": UMBILICAL,
              "gamma_coupling": GAMMA, "crease_h": h_c, "f_at_0.5": f05,
              "volume_comp_cm": float(comp * 100),
              "volume_proxy_cm3": {"base": V0 * 1e6, "v1_added": (V1 - V0) * 1e6,
                                   "v2_added": (V2 - V0) * 1e6,
                                   "v2_over_v1": float((V2 - V0) / (V1 - V0))}},
    "mobility": {"max": float(mob.max()), "at_navel": float(mob[navel_mh]),
                 "verts_over_0.05": int((mob > 0.05).sum())},
    "navel": nav, "fold_scan": {k: {b: {"flips": v[b][0], "min_dot": v[b][1]}
                                    for b in BASES} for k, v in fold_scan.items()},
    "zones": zone_rows, "zones_all_triangle_exact": allrow,
    "moved_verts": {"v2_combined": n_v2, "sag_component": n_sag},
}
(WORK / "qa_numbers_v2.json").write_text(json.dumps(qa2, indent=1))
print("QA v2 saved")
