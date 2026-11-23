#!/usr/bin/env python3
"""
First-proof builder: Fat Males `body.belly.protrusion` -> MakeHuman hm08 .target

Method (see PROOF.md):
  * Canonical frame: X right, Y forward, Z up, metres.
    - Skyrim NIF body: (x, y, z) is already (right, forward, up); 1 unit = 0.01428 m.
      Forward verified geometrically: feet-mesh toes point +Y.
    - hm08 base.obj: canonical = (x, z, y)_obj; 1 unit = 1 dm = 0.1 m.
      Front verified geometrically: stomach-target verts sit at +Z of the slice centre.
  * Base-pair correspondence = shared torso parameterisation (h, theta):
    h = height between anatomical landmarks (crotch = lowest midline vertex;
    neck base = first sustained narrowing of the gated torso width profile
    above the chest), normalised to [0, 1]. theta = angle around a smooth
    torso axis (per-band bounding-box centres of the |x| < 0.23 m gated
    verts, smoothed over bands). Source morph verified bilaterally
    symmetric (mirror-test p95 disagreement 0.27 cm), so theta folds to |theta|.
  * The Fat Males delta (exact-topology; learned/fat-males_body_morph.npz) is
    decomposed into radial + vertical components on the source torso and
    kernel-regressed into a smooth field D(h, theta); fidelity = 5-fold CV.
  * The field is sampled onto hm08 inside the canonical belly mask
    (geodesic falloff from the navel, r = 0.35 x torso length; doc 6.1),
    scaled by the torso-length proportion s = L_mh / L_sk, Laplacian-smoothed
    on the hm08 triangle graph (fold control on the dense target), and
    gain-calibrated so the navel vertex meets the canonical endpoint anchor
    exactly (the slider is defined by its anchor; doc 6.1).
  * Output: stock MakeHuman .target (base.obj frame / dm, MPFB header).
  * Fold QA: per-face normal-flip scan over belly faces, weights [-1, +1.05];
    safe_max = largest weight <= 1.0 with zero flips.
"""
import json
import sys
from pathlib import Path

import numpy as np
import scipy.sparse as sp
from scipy.spatial import cKDTree

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
    crotch_of,
    load_mpfb_base_obj,
    neck_base,
    torso_cylindrical as torso_params,
    tri_closest,
    tri_list,
)
from core.geometry import (  # noqa: E402
    count_flips as _count_flips,
    face_normals,
    write_target,
)

WORK = OUT / "work"
WORK.mkdir(parents=True, exist_ok=True)
LEARNED = Path.home() / "workspace/character_assets/learned"
MPFB_ZIP = Path.home() / "workspace/stick-figure-avatar/photoreal/tools/mpfb2.zip"

rng = np.random.default_rng(20261112)

# ---------------------------------------------------------------- load source
src = np.load(LEARNED / "fat-males_body_morph.npz")
sk_pos = src["body_vertices"].astype(np.float64) * SK_UNIT_M
sk_tri = src["body_triangles"].astype(np.int64)
sk_delta = src["body_delta"].astype(np.float64) * SK_UNIT_M

# ---------------------------------------------------------------- load hm08
mh_pos, mh_faces = load_mpfb_base_obj(MPFB_ZIP, with_poly_faces=True)
mh_body = np.zeros(len(mh_pos), bool); mh_body[:BODY_END] = True
print(f"hm08: {len(mh_pos)} verts ({mh_body.sum()} body), {len(mh_faces)} faces")
# MPFB2's evaluated mesh (the actual test environment) applies the default
# macros, which shift the neutral geometry slightly vs raw base.obj. Fold
# checks must pass on BOTH bases. Dumped by scripts/dump_macro_base.py
# (body verts only, first BODY_END rows; helper rows keep raw positions).
mh_pos_mac = mh_pos.copy()
_mac_path = WORK / "mh_macro_base.npz"
if _mac_path.exists():
    _mac = np.load(_mac_path)["pos_canonical_m"]
    mh_pos_mac[:len(_mac)] = _mac
    print(f"macro base loaded: {len(_mac)} rows replaced, max shift "
          f"{np.abs(mh_pos_mac - mh_pos).max()*100:.2f} cm")
else:
    print("WARNING: no macro base dump found; fold checks on raw base only")

# ---------------------------------------------------------------- axis + landmarks
sk_ctr, sk_axis = compute_axis(sk_pos)
mh_ctr, mh_axis = compute_axis(mh_pos, mh_body)
sk_crotch = crotch_of(sk_pos, np.ones(len(sk_pos), bool), 0.030, 0.060)
mh_crotch = crotch_of(mh_pos, mh_body, 0.020, 0.045)
sk_neck = neck_base(sk_pos, sk_ctr, sk_axis, sk_crotch, "skyrim")
mh_neck = neck_base(mh_pos, mh_ctr, mh_axis, mh_crotch, "hm08  ")
L_sk, L_mh = sk_neck - sk_crotch, mh_neck - mh_crotch
s_scale = L_mh / L_sk
print(f"crotch: sk {sk_crotch:.3f} m, mh {mh_crotch:.3f} m | torso lengths: "
      f"sk {L_sk:.4f} m, mh {L_mh:.4f} m -> s = {s_scale:.4f}")

sk_h, sk_th, sk_ax, sk_r = torso_params(sk_pos, sk_ctr, sk_axis, sk_crotch, sk_neck)
mh_h, mh_th, mh_ax, mh_r = torso_params(mh_pos, mh_ctr, mh_axis, mh_crotch, mh_neck)

# ---------------------------------------------------------------- source field
samp = (sk_h > 0.0) & (sk_h < 1.0) & (sk_r < 0.30)
er = np.stack([np.sin(sk_th), np.cos(sk_th)], axis=1)
sk_dr = np.einsum("ij,ij->i", sk_delta[:, :2], er)
sk_dz = sk_delta[:, 2]
sk_dt = np.einsum("ij,ij->i", sk_delta[:, :2],
                  np.stack([np.cos(sk_th), -np.sin(sk_th)], axis=1))
H = sk_h[samp]; TH = np.abs(sk_th[samp])
DR = sk_dr[samp]; DZ = sk_dz[samp]
print(f"source torso samples: {samp.sum()} | tangential |delta| in samples: "
      f"mean {np.abs(sk_dt[samp]).mean()*100:.2f} cm (not modelled)")

rb = np.linspace(0, 1, 21)
rmean = np.array([sk_r[samp][(H >= rb[i]) & (H < rb[i + 1])].mean()
                  if ((H >= rb[i]) & (H < rb[i + 1])).any() else 0.17
                  for i in range(20)])
def arc(theta, hv):
    return theta * np.interp(hv, 0.5 * (rb[:-1] + rb[1:]), rmean)

SIG_H, SIG_A = 0.05, 0.040
def field_eval(hq, tq, idx=None):
    if idx is None:
        idx = np.arange(len(H))
    dh = (H[idx][:, None] - hq[None, :]) / SIG_H
    da = (arc(TH[idx], H[idx])[:, None] - arc(np.abs(tq), hq)[None, :]) / SIG_A
    w = np.exp(-0.5 * (dh ** 2 + da ** 2))
    ws = w.sum(axis=0) + 1e-12
    return (w * DR[idx][:, None]).sum(axis=0) / ws, (w * DZ[idx][:, None]).sum(axis=0) / ws

# ---------------------------------------------------------------- navel + anchor
front_centre = samp & (np.abs(sk_pos[:, 0] - sk_ax[:, 0]) < 0.03)
prof_h, prof_d = [], []
grid = np.linspace(0, 1, 41)
for a, b in zip(grid[:-1], grid[1:]):
    m = front_centre & (sk_h >= a) & (sk_h < b)
    if m.sum() >= 2:
        prof_h.append(0.5 * (a + b)); prof_d.append(sk_delta[m, 1].mean())
h_star = float(prof_h[int(np.argmax(prof_d))])
navel_sk = int(np.argmin(np.where(front_centre,
                                  (sk_h - h_star) ** 2 + (sk_pos[:, 0] - sk_ax[:, 0]) ** 2,
                                  np.inf)))
anchor_raw = float(sk_delta[navel_sk, 1])
anchor = anchor_raw * s_scale
max_delta = float(np.linalg.norm(sk_delta, axis=1).max())
print(f"navel: h*={h_star:.3f}, source vert {navel_sk}, forward disp "
      f"{anchor_raw*100:.2f} cm -> canonical anchor {anchor*100:.2f} cm "
      f"(max |delta| overall {max_delta*100:.2f} cm)")

# ---------------------------------------------------------------- belly mask + CV
def belly_mask(hv, thv, rv, L):
    """Canonical mask (doc 6.1): geodesic falloff from navel, r = 0.35 L."""
    dh = hv - h_star
    da = np.abs(thv) * rv
    rho = np.sqrt(dh ** 2 * L ** 2 + da ** 2) / (0.35 * L)
    w = 0.5 * (1 + np.cos(np.pi * np.clip((rho - 0.65) / 0.35, 0, 1)))
    w[rho <= 0.65] = 1.0
    return w

sk_w_all = belly_mask(sk_h, sk_th, sk_r, L_sk)
w_samp = sk_w_all[samp]
perm = rng.permutation(len(H)); folds = np.array_split(perm, 5)
errs = np.zeros(len(H))
for f in folds:
    tr = np.setdiff1d(perm, f)
    pr, pz = field_eval(H[f], TH[f], idx=tr)
    errs[f] = np.sqrt((pr - DR[f]) ** 2 + (pz - DZ[f]) ** 2)
def pct(e):
    return {k: float(v) for k, v in
            zip(["p50", "p95", "max"], np.percentile(e, [50, 95, 100]))}
cv = pct(errs[w_samp > 0.5]); cv_all = pct(errs)
print(f"field CV, belly mask (n={int((w_samp>0.5).sum())}): p50={cv['p50']*100:.3f} cm "
      f"p95={cv['p95']*100:.3f} cm max={cv['max']*100:.3f} cm | whole torso "
      f"p95={cv_all['p95']*100:.3f} cm")

mh_w = belly_mask(mh_h, mh_th, mh_r, L_mh)
mh_w[~mh_body] = 0.0
active = mh_w > 0.003
print(f"hm08 verts inside belly mask (w>0.003): {active.sum()}")

# ---------------------------------------------------------------- transfer
mh_tris = tri_list(mh_faces)
act_idx = np.where(active)[0]

# Transfer by non-rigid registration in torso-param space (the fit POC's
# method, cylindrical coordinates). Param point = (arc/L, h, r/L), each
# mesh normalised by its own torso length L, so the spaces are comparable.
# hm08 mask verts are attracted onto the source FAT surface; the delta is
# the displacement from each vert's own neutral -- so the studied shape
# is reproduced, and the navel landmark is then pinned to the canonical
# displacement anchor with a tight local correction (the two differ by
# the neutral-belly radius gap between the bases, measured separately).
gr, gz = field_eval(mh_h[active], np.abs(mh_th[active]))
er_mh = np.stack([np.sin(mh_th[active]), np.cos(mh_th[active])], axis=1)
d_can = np.zeros((active.sum(), 3))
d_can[:, :2] = (mh_w[active] * s_scale * gr)[:, None] * er_mh
d_can[:, 2] = mh_w[active] * s_scale * gz
mh_delta = np.zeros_like(mh_pos)
mh_delta[active] = d_can

def param_coords(pos, ctr, axis, crotch, L):
    h, th, ax, r = torso_params(pos, ctr, axis, crotch, crotch + L)
    return np.stack([th * r / L, h, r / L], axis=1), (h, th, ax, r)

sk_fat = sk_pos + sk_delta
skP_fat, _ = param_coords(sk_fat, sk_ctr, sk_axis, sk_crotch, L_sk)
skP_neu, _ = param_coords(sk_pos, sk_ctr, sk_axis, sk_crotch, L_sk)
mhP_init, _ = param_coords(mh_pos + mh_delta, mh_ctr, mh_axis, mh_crotch, L_mh)
mhP_neu, _ = param_coords(mh_pos, mh_ctr, mh_axis, mh_crotch, L_mh)

src_tris = []
for f in sk_tri:
    if np.all((sk_h[f] > -0.02) & (sk_h[f] < 1.02) & (sk_r[f] < 0.30)):
        u = skP_fat[f][:, 0]
        if np.max(u) - np.min(u) < 0.5:
            src_tris.append(f)
src_tris = np.array(src_tris)
src_verts = np.unique(src_tris)
print(f"param-space source surface: {len(src_tris)} tris, {len(src_verts)} verts")

src_surf = ParamSurface(skP_fat, src_tris)
edges = np.vstack([mh_tris[:, [0, 1]], mh_tris[:, [1, 2]], mh_tris[:, [2, 0]]])
edges = np.unique(np.sort(edges, axis=1), axis=0)
A = sp.coo_matrix((np.ones(len(edges)), (edges[:, 0], edges[:, 1])),
                  shape=(len(mh_pos), len(mh_pos)))
A = A + A.T
deg = np.asarray(A.sum(axis=1)).ravel()
Lop = sp.diags(1.0 / np.maximum(deg, 1)) @ A
Q = mhP_init[act_idx].copy()
w_act = mh_w[act_idx]
Qfull = mhP_init.copy()
for it in range(60):
    cp, dd = src_surf.closest(Q)
    step = 0.5 * (cp - Q)
    nrm = np.linalg.norm(step, axis=1, keepdims=True)
    step *= np.minimum(1.0, 0.02 / np.maximum(nrm, 1e-12))
    Q = Q + w_act[:, None] * step
    if it % 10 == 9:
        Qfull[act_idx] = Q
        sm = Lop @ Qfull
        Q = Q + 0.20 * w_act[:, None] * (sm[act_idx] - Q)
    if it % 20 == 19:
        print(f"  registration iter {it + 1}: mean dist to source surface "
              f"{dd.mean() * L_sk * 100:.3f} cm")
Qfinal = Q

pos_new = mh_pos.copy()
for j, vi in enumerate(act_idx):
    u, v, wq = Qfinal[j]
    r_new = wq * L_mh
    z_new = mh_crotch + v * L_mh
    th_new = u * L_mh / max(r_new, 1e-6)
    ax = axis_at(mh_ctr, mh_axis, np.array([z_new]))[0]
    pos_new[vi] = [ax[0] + r_new * np.sin(th_new),
                   ax[1] + r_new * np.cos(th_new), z_new]
mh_delta = pos_new - mh_pos

cand = mh_body & (np.abs(mh_pos[:, 0] - mh_ax[:, 0]) < 0.02) & (np.abs(mh_h - h_star) < 0.05)
navel_mh = int(np.argmax(np.where(cand, mh_pos[:, 1], -np.inf)))

def pct_cm(e):
    e = e * L_sk * 100
    return {k: float(v) for k, v in
            zip(["p50", "p95", "max"], np.percentile(e, [50, 95, 100]))}

def shipped_residuals(delta):
    """Forward + coverage-matched backward surface residuals of the FINAL
    field (result verts in param space vs source fat surface)."""
    P_res, _ = param_coords(mh_pos + delta, mh_ctr, mh_axis, mh_crotch, L_mh)
    core = act_idx[mh_w[act_idx] > 0.5]
    _, d_fwd = src_surf.closest(P_res[core])
    faces = []
    for f in mh_tris:
        if np.all(mh_w[f] > 0.003):
            u = P_res[f][:, 0]
            if np.max(u) - np.min(u) < 0.5:
                faces.append(f)
    surf = ParamSurface(P_res, np.array(faces))
    src_core = src_verts[sk_w_all[src_verts] > 0.5]
    tree = cKDTree(P_res[np.unique(faces)][:, :2])
    dd_uv, _ = tree.query(skP_fat[src_core][:, :2])
    matched = dd_uv < 0.05
    _, d_bwd = surf.closest(skP_fat[src_core][matched])
    return {"forward_hm08_to_source": pct_cm(d_fwd),
            "backward_source_to_hm08_matched": pct_cm(d_bwd),
            "backward_coverage": float(matched.mean()),
            "backward_n": int(matched.sum())}

belly_face = np.array([mh_w[list(f)].max() > 0.02 for f in mh_tris])
def count_flips(delta, pos=None):
    pos = mh_pos if pos is None else pos
    Fb_ = mh_tris[belly_face]
    dots = np.einsum("ij,ij->i", face_normals(pos, Fb_), face_normals(pos + delta, Fb_))
    return _count_flips(pos, pos + delta, mh_tris, belly_face), float(dots.min())

# finishing: NO global Cartesian smoothing (the registration's in-loop
# param-space smoothing suffices; global smoothing shrinks the navel peak
# and forces a bigger pin) -> TIGHT navel pin (landmark anchor)
# -> TARGETED fold repair (bad-face verts + 1-ring only) -> guarded micro-pin
u_act = mhP_neu[act_idx][:, 0]; v_act = mhP_neu[act_idx][:, 1]
pin_kernel = np.exp(-0.5 * (((v_act - h_star) / 0.045) ** 2 + (u_act / 0.035) ** 2))
er_act = np.stack([np.sin(mh_th[act_idx]), np.cos(mh_th[act_idx])], axis=1)
pin_size = 0.0
for _ in range(3):
    deficit = anchor - float(mh_delta[navel_mh, 1])
    pin_size += deficit
    add = np.zeros((len(act_idx), 3))
    add[:, :2] = (deficit * pin_kernel)[:, None] * er_act
    mh_delta[act_idx] += add
print(f"navel pin: total radial correction {pin_size*100:.2f} cm at the "
      f"landmark (sigma_u 0.035, sigma_v 0.045 in torso-param units)")
Fb_all = mh_tris[belly_face]
BASES = {"raw": mh_pos, "macro": mh_pos_mac}
n0_all = {k: face_normals(p, Fb_all) for k, p in BASES.items()}
def bad_faces(delta, thresh=0.03):
    """Union of near-degenerate belly faces over BOTH bases."""
    bad = np.zeros(len(Fb_all), bool)
    mind = 1.0
    for k, p in BASES.items():
        nn_ = face_normals(p + delta, Fb_all)
        dots = np.einsum("ij,ij->i", n0_all[k], nn_)
        bad |= dots < thresh
        mind = min(mind, float(dots.min()))
    return bad, mind
nbrs = [np.asarray(A[v].nonzero()[1]) for v in range(len(mh_pos))]
gain = 1.0
for rnd in range(60):
    bad, mind = bad_faces(mh_delta)
    if not bad.any():
        print(f"fold repair (dual-base): clean after {rnd} rounds "
              f"(min_dot {mind:.3f})")
        break
    bad_verts = np.unique(Fb_all[bad])
    grow = np.unique(np.concatenate([nbrs[v] for v in bad_verts]))
    grow = grow[mh_w[grow] > 0.003]
    sm = Lop @ mh_delta
    mh_delta[grow] = mh_delta[grow] + 0.5 * mh_w[grow][:, None] * \
        (sm[grow] - mh_delta[grow])
else:
    print("fold repair: rounds exhausted")
# guarded micro-pin: repair may relax the landmark by ~2 mm; re-centre it
# only if the extra pin introduces no flips on either base
deficit = anchor - float(mh_delta[navel_mh, 1])
if abs(deficit) > 0.0005:
    trial = mh_delta.copy()
    add = np.zeros((len(act_idx), 3))
    add[:, :2] = (deficit * pin_kernel)[:, None] * er_act
    trial[act_idx] += add
    if count_flips(trial, mh_pos)[0] == 0 and count_flips(trial, mh_pos_mac)[0] == 0:
        mh_delta = trial
        print(f"micro-pin applied: {deficit*100:+.2f} cm")
    else:
        print(f"micro-pin rejected (would fold); navel stays "
              f"{mh_delta[navel_mh,1]*100:.2f} cm")
print(f"finished field: navel {mh_delta[navel_mh,1]*100:.2f} cm "
      f"(anchor {anchor*100:.2f} cm), flips at +1: raw "
      f"{count_flips(mh_delta, mh_pos)[0]} (min_dot "
      f"{count_flips(mh_delta, mh_pos)[1]:.3f}), macro "
      f"{count_flips(mh_delta, mh_pos_mac)[0]} (min_dot "
      f"{count_flips(mh_delta, mh_pos_mac)[1]:.3f})")
reg_resid = shipped_residuals(mh_delta)
print(f"shipped surface residual fwd (cm): {reg_resid['forward_hm08_to_source']}")
print(f"shipped surface residual bwd matched (cm): "
      f"{reg_resid['backward_source_to_hm08_matched']} "
      f"coverage {reg_resid['backward_coverage']:.2f}")

# ---------------------------------------------------------------- folds
belly_face = np.array([mh_w[list(f)].max() > 0.02 for f in mh_tris])
Fb = mh_tris[belly_face]
face_h = mh_h[Fb].mean(axis=1)
fold_scan = {}
for wgt in [-1.0, 0.5, 0.7, 0.8, 0.9, 0.95, 1.0, 1.05]:
    entry = {"faces_checked": int(belly_face.sum())}
    for bname, bpos in BASES.items():
        n0 = face_normals(bpos, Fb)
        nn = face_normals(bpos + wgt * mh_delta, Fb)
        dots = np.einsum("ij,ij->i", n0, nn)
        fl = dots < 0
        entry[bname] = {"flips": int(fl.sum()), "min_dot": float(dots.min()),
                        "flip_h_range": [float(face_h[fl].min()), float(face_h[fl].max())]
                        if fl.any() else None}
    fold_scan[str(wgt)] = entry
    print(f"weight {wgt:+.2f}: raw flips={entry['raw']['flips']} "
          f"(min_dot {entry['raw']['min_dot']:.3f}), macro flips="
          f"{entry['macro']['flips']} (min_dot {entry['macro']['min_dot']:.3f}) "
          f"over {belly_face.sum()} belly faces")
safe_max = max([float(w) for w, v in fold_scan.items()
                if v["raw"]["flips"] == 0 and v["macro"]["flips"] == 0
                and 0 < float(w) <= 1.0] or [0.0])

# ---------------------------------------------------------------- write .target
NOTE1 = (
    "Provenance: omniversal slider body.belly.protrusion, instance "
    "makehuman_hm08.\nLearned from the Fat Males body morph "
    "(study-only, internal - not a CC0 MakeHuman asset)."
)
target_path = OUT / "body.belly.protrusion.target"
n_moved = write_target(target_path, mh_delta, NOTE1)
print(f"wrote {target_path} with {n_moved} moved verts")

np.savez(WORK / "correspondence.npz",
         mh_delta_canonical_m=mh_delta, mh_mask=mh_w,
         navel_mh=navel_mh, navel_sk=navel_sk, h_star=h_star,
         sk_landmarks=[sk_crotch, sk_neck], mh_landmarks=[mh_crotch, mh_neck],
         belly_face_mask=belly_face, mh_tris=mh_tris)
qa = {
    "s_scale": s_scale, "h_star": h_star, "anchor_raw_m": anchor_raw,
    "anchor_m": anchor, "max_delta_source_m": max_delta,
    "navel_mh": navel_mh, "navel_sk": navel_sk,
    "navel_predicted_m": float(mh_delta[navel_mh, 1]), "gain": gain,
    "cv_residual_m": cv, "cv_residual_torso_m": cv_all,
    "surface_residual_cm": reg_resid,
    "navel_pin_cm": float(pin_size * 100),
    "fold_scan": fold_scan, "safe_max": safe_max,
    "moved_verts": int(n_moved),
    "tangential_mean_cm": float(np.abs(sk_dt[samp]).mean() * 100),
    "landmarks": {"skyrim": [sk_crotch, sk_neck], "hm08": [mh_crotch, mh_neck]},
    "kernel": {"sigma_h": SIG_H, "sigma_arc_m": SIG_A},
    "method": "non-rigid registration in torso-param space (arc/L, h, r/L) "
              "onto the source fat surface, kernel-field init; mask falloff; "
              "tight navel pin to the canonical displacement anchor "
              "(sigma_u 0.035, sigma_v 0.045); targeted dual-base fold "
              "repair (bad-face verts + 1-ring, checked on raw base.obj "
              "geometry AND the MPFB default-macro evaluated base)",
    "smoothing": {"registration": "param-space graph Laplacian x6 in-loop",
                  "fold_repair": "targeted, bad-face verts + 1-ring, 0.5"},
}
(WORK / "qa_numbers.json").write_text(json.dumps(qa, indent=1))
print("QA:", json.dumps({k: qa[k] for k in
                         ["s_scale", "anchor_m", "safe_max", "moved_verts", "gain"]}, indent=1))
