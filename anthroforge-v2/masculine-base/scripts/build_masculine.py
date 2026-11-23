#!/usr/bin/env python3
"""
Masculine-base builder: correspondence package + belly v1 re-validation.

Faithful adaptation of first-proof/scripts/build_target.py (the v1
method), with the target side changed:

  * v1 (feminine): correspondence/registration derived on RAW base.obj;
    fold checks on raw + default-macro (gender 0.5) evaluated base.
  * here (masculine): correspondence/registration derived on the
    MASCULINE-macro (gender 1.0, all else default) evaluated neutral --
    the mesh the target will actually sit on; fold checks on that
    neutral AND on raw base.obj (the .target basis).

Frames (see MASCULINE_BASE.md for the full trap write-up):
  * base.obj canonical: (x, z_obj, y_obj) * 0.1 m, z centred
    (-0.845..0.850 over all verts; body rows -0.817..0.850).
  * Blender evaluated dumps are GROUNDED (z ~ 0..height). The stored
    feminine mh_macro_base.npz is grounded; the feminine
    correspondence.npz is centred -- the old package mixes frames
    (benign for its flip scans: the offset is a rigid translation of
    the body rows, which cannot change face normals).
  * Here the masculine dump is aligned back into the canonical frame
    BEFORE use: offset = (median dx, median dy, grounded_z_min -
    file_body_z_min). On the feminine dump this method recovers
    (0, +0.65 cm, +81.68 cm); the masculine dump gives
    (0, +0.40 cm, +81.68 cm).

Outputs (masculine-base/):
  body.belly.protrusion.target          masculine instance of the v1 slider
  work/correspondence_masc.npz          correspondence package (see doc)
  work/qa_numbers_masc.json             validation + comparison numbers
"""
import json
import sys
from pathlib import Path

import numpy as np
import scipy.sparse as sp
from scipy.spatial import ConvexHull, cKDTree

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
FP_WORK = Path.home() / "workspace/anthroforge-v2/first-proof/work"
LEARNED = Path.home() / "workspace/character_assets/learned"
MPFB_ZIP = Path.home() / "workspace/stick-figure-avatar/photoreal/tools/mpfb2.zip"

rng = np.random.default_rng(20261112)

# ---------------------------------------------------------------- load source
src = np.load(LEARNED / "fat-males_body_morph.npz")
sk_pos = src["body_vertices"].astype(np.float64) * SK_UNIT_M
sk_tri = src["body_triangles"].astype(np.int64)
sk_delta = src["body_delta"].astype(np.float64) * SK_UNIT_M

# ---------------------------------------------------------------- load hm08 raw
raw_pos, mh_faces = load_mpfb_base_obj(MPFB_ZIP, with_poly_faces=True)
mh_body = np.zeros(len(raw_pos), bool); mh_body[:BODY_END] = True
print(f"hm08 raw: {len(raw_pos)} verts ({mh_body.sum()} body), {len(mh_faces)} faces")

# ------------------------------------------------- masculine neutral (aligned)
_dump = np.load(WORK / "mh_macro_base_masculine.npz")
ev = _dump["pos_canonical_m"].astype(np.float64)          # grounded frame
_body_raw = raw_pos[:len(ev)]
frame_offset = np.array([
    np.median(ev[:, 0] - _body_raw[:, 0]),
    np.median(ev[:, 1] - _body_raw[:, 1]),
    ev[:, 2].min() - _body_raw[:, 2].min()])
ev_aligned = ev - frame_offset
resid = np.linalg.norm(ev_aligned - _body_raw, axis=1)
print(f"masculine dump: {len(ev)} verts grounded z "
      f"{ev[:,2].min():.3f}..{ev[:,2].max():.3f}; frame offset "
      f"{np.round(frame_offset, 4)}; aligned-vs-raw resid cm "
      f"p50 {np.percentile(resid,50)*100:.2f} p95 {np.percentile(resid,95)*100:.2f} "
      f"max {resid.max()*100:.2f} (macro deformation scale => order OK)")
# target neutral: body rows = aligned masculine evaluated; helpers = raw
mh_pos = raw_pos.copy()
mh_pos[:len(ev)] = ev_aligned

# feminine neutral (aligned the same way) for the comparison table
_old = np.load(FP_WORK / "mh_macro_base.npz")["pos_canonical_m"].astype(np.float64)
_off_f = np.array([np.median(_old[:, 0] - _body_raw[:, 0]),
                   np.median(_old[:, 1] - _body_raw[:, 1]),
                   _old[:, 2].min() - _body_raw[:, 2].min()])
fem_pos = raw_pos.copy()
fem_pos[:len(_old)] = _old - _off_f
print(f"feminine frame offset {np.round(_off_f, 4)} (same method)")

# ---------------------------------------------------------------- axis + landmarks
sk_ctr, sk_axis = compute_axis(sk_pos)
mh_ctr, mh_axis = compute_axis(mh_pos, mh_body)
sk_crotch = crotch_of(sk_pos, np.ones(len(sk_pos), bool), 0.030, 0.060)
mh_crotch = crotch_of(mh_pos, mh_body, 0.020, 0.045)
sk_neck = neck_base(sk_pos, sk_ctr, sk_axis, sk_crotch, "skyrim")
mh_neck = neck_base(mh_pos, mh_ctr, mh_axis, mh_crotch, "hm08-masc")
L_sk, L_mh = sk_neck - sk_crotch, mh_neck - mh_crotch
s_scale = L_mh / L_sk
print(f"crotch: sk {sk_crotch:.3f} m, mh-masc {mh_crotch:.3f} m | torso lengths: "
      f"sk {L_sk:.4f} m, mh-masc {L_mh:.4f} m -> s = {s_scale:.4f} "
      f"(feminine v1: L 0.6272 m, s 0.8325)")

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
      f"{anchor_raw*100:.2f} cm -> canonical anchor (masc) {anchor*100:.2f} cm "
      f"(feminine anchor 11.97 cm)")

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
print(f"hm08-masc verts inside belly mask (w>0.003): {active.sum()} "
      f"(feminine v1: 535 moved / mask count in its qa)")

# ---------------------------------------------------------------- transfer
mh_tris = tri_list(mh_faces)
act_idx = np.where(active)[0]

# Transfer by non-rigid registration in torso-param space (identical to v1).
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
print(f"navel_mh (masc, same selection rule): {navel_mh} "
      f"(feminine v1: 4075)")

def pct_cm(e):
    e = e * L_sk * 100
    return {k: float(v) for k, v in
            zip(["p50", "p95", "max"], np.percentile(e, [50, 95, 100]))}

def shipped_residuals(delta):
    """Forward + coverage-matched backward surface residuals (as v1)."""
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

# finishing: TIGHT navel pin -> TARGETED fold repair -> guarded micro-pin
# (dual bases here: masculine neutral + raw base.obj)
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
BASES = {"neutral_masc": mh_pos, "raw_baseobj": raw_pos}
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
repair_rounds_used = None
for rnd in range(300):
    bad, mind = bad_faces(mh_delta)
    if not bad.any():
        repair_rounds_used = rnd
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
    repair_rounds_used = 300
    print("fold repair: rounds exhausted (300) -- residual bad faces remain "
          "on at least one base; see fold scan")
deficit = anchor - float(mh_delta[navel_mh, 1])
if abs(deficit) > 0.0005:
    trial = mh_delta.copy()
    add = np.zeros((len(act_idx), 3))
    add[:, :2] = (deficit * pin_kernel)[:, None] * er_act
    trial[act_idx] += add
    if count_flips(trial, mh_pos)[0] == 0 and count_flips(trial, raw_pos)[0] == 0:
        mh_delta = trial
        print(f"micro-pin applied: {deficit*100:+.2f} cm")
    else:
        print(f"micro-pin rejected (would fold); navel stays "
              f"{mh_delta[navel_mh,1]*100:.2f} cm")
print(f"finished field: navel {mh_delta[navel_mh,1]*100:.2f} cm "
      f"(anchor {anchor*100:.2f} cm), flips at +1: neutral_masc "
      f"{count_flips(mh_delta, mh_pos)[0]} (min_dot "
      f"{count_flips(mh_delta, mh_pos)[1]:.3f}), raw_baseobj "
      f"{count_flips(mh_delta, raw_pos)[0]} (min_dot "
      f"{count_flips(mh_delta, raw_pos)[1]:.3f})")
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
    print(f"weight {wgt:+.2f}: neutral_masc flips={entry['neutral_masc']['flips']} "
          f"(min_dot {entry['neutral_masc']['min_dot']:.3f}), raw flips="
          f"{entry['raw_baseobj']['flips']} (min_dot "
          f"{entry['raw_baseobj']['min_dot']:.3f}) over {belly_face.sum()} belly faces")
def _sm(base_key):
    return max([float(w) for w, v in fold_scan.items()
                if v[base_key]["flips"] == 0 and 0 < float(w) <= 1.0] or [0.0])
safe_max = _sm("neutral_masc")            # headline: the instance's own base
safe_max_raw = _sm("raw_baseobj")         # misuse case: target w/o its macro
print(f"safe_max: neutral_masc {safe_max}, raw_baseobj {safe_max_raw}; "
      f"+1 raw flip h range: {fold_scan['1.0']['raw_baseobj']['flip_h_range']}")

# ------------------------------------------------------- proportions comparison
def measure_base(pos, label):
    """Girths (convex-hull perimeter of a +-1.25 cm slab) at landmark-
    relative stations + chest shape metrics. Identical method per base."""
    ctr_, axis_ = compute_axis(pos, mh_body)
    cro_ = crotch_of(pos, mh_body, 0.020, 0.045)
    neck_ = neck_base(pos, ctr_, axis_, cro_, label)
    L_ = neck_ - cro_
    ax_ = axis_at(ctr_, axis_, pos[:, 2])
    r_ = np.linalg.norm(pos[:, :2] - ax_, axis=1)
    torso_gate = mh_body & (r_ < 0.30)   # exclude arms/hands from slabs
    girth_gate = mh_body & (r_ < 0.215)  # v4-precedent torso-only gate:
    # at chest height the deltoid/upper-arm cross-sections sit within
    # r<0.30 of the axis and poison hull girths/widths; r<0.215 keeps
    # the slice on the ribcage.
    def slab(hfrac, hw=0.0125):
        z0 = cro_ + hfrac * L_
        m = girth_gate & (np.abs(pos[:, 2] - z0) < hw)
        return pos[m], z0
    def girth(hfrac):
        P, _ = slab(hfrac)
        hull = ConvexHull(P[:, :2])
        return float(hull.area)          # 2D hull: .area == perimeter
    def extent(hfrac, col, lo=1, hi=99):
        P, _ = slab(hfrac)
        return float(np.percentile(P[:, col], hi) - np.percentile(P[:, col], lo))
    def frontband_y(hfrac, half_w=0.11):
        """Front surface of the torso band: 99th-pct y among slab verts
        within +-half_w of the axis x. Wide gate on purpose: the breast
        apex sits OFF the midline, so a midline gate measures the
        sternum and reports no bust on any base."""
        z0 = cro_ + hfrac * L_
        m = torso_gate & (np.abs(pos[:, 2] - z0) < 0.0125)
        P = pos[m]
        mid = np.abs(P[:, 0] - np.interp(z0, ctr_, axis_[:, 0])) < half_w
        return float(np.percentile(P[mid, 1], 99)) if mid.sum() >= 4 else float("nan")
    chest_h, waist_h, hip_h = 0.78, h_star, 0.12
    prof_hs = np.arange(0.58, 0.921, 0.02)
    prof = {round(float(h), 3): frontband_y(float(h)) for h in prof_hs}
    # chest-front mound prominence: peak frontband y in the chest band
    # above the straight line joining the underbust (h 0.62) and
    # upper-chest (h 0.88) references -- measures a localised mound
    # over the chest's own slope (a flat pec plane scores ~0).
    band = {k: v for k, v in prof.items() if 0.68 <= k <= 0.88}
    pk = max(band, key=band.get)
    ref = prof[round(0.62, 3)] + (prof[round(0.88, 3)] - prof[round(0.62, 3)]) \
        * (pk - 0.62) / (0.88 - 0.62)
    bust = band[pk] - ref
    def shoulder_width():
        z0 = cro_ + 0.93 * L_
        m = mh_body & (r_ < 0.36) & (np.abs(pos[:, 2] - z0) < 0.0125)
        P = pos[m]
        return float(np.percentile(P[:, 0], 99.5) - np.percentile(P[:, 0], 0.5))
    out = {
        "height_m": float(pos[mh_body, 2].max() - pos[mh_body, 2].min()),
        "torso_length_m": float(L_),
        "crotch_m": float(cro_), "neck_m": float(neck_),
        "chest_girth_m": girth(chest_h), "waist_girth_m": girth(waist_h),
        "hip_girth_m": girth(hip_h),
        "chest_width_m": extent(chest_h, 0), "chest_depth_m": extent(chest_h, 1),
        "shoulder_width_m": shoulder_width(),
        "hip_width_m": extent(hip_h, 0),
        "bust_protrusion_m": float(bust),
        "frontband_profile_y_m": prof,
        "stations_h": {"chest": chest_h, "waist": waist_h, "hip": hip_h,
                       "shoulder": 0.93, "bust_ref": 0.62,
                       "bust_band": [0.68, 0.88]},
    }
    print(f"{label}: " + json.dumps({k: (round(v, 3) if isinstance(v, float) else v)
                                    for k, v in out.items() if k != 'stations_h'}))
    return out

props_masc = measure_base(mh_pos, "masculine")
props_fem = measure_base(fem_pos, "feminine ")
props_raw = measure_base(raw_pos, "raw      ")

# ---------------------------------------------------------------- write .target
NOTE_MASC = (
    "Provenance: omniversal slider body.belly.protrusion, instance "
    "makehuman_hm08 MASCULINE base (MPFB macro gender 1.0, all other "
    "macros default).\nPER-BASE INSTANCE: deltas are relative to "
    "the masculine-macro neutral; apply only on the masculine-macro "
    "human.\nLearned from the Fat Males body morph "
    "(study-only, internal - not a CC0 MakeHuman asset)."
)
target_path = OUT / "body.belly.protrusion.target"
n_moved = write_target(target_path, mh_delta, NOTE_MASC)
print(f"wrote {target_path} with {n_moved} moved verts")

# ------------------------------------------------------- correspondence package
np.savez(WORK / "correspondence_masc.npz",
         # --- keys mirroring first-proof/work/correspondence.npz ---
         mh_delta_canonical_m=mh_delta, mh_mask=mh_w,
         navel_mh=navel_mh, navel_sk=navel_sk, h_star=h_star,
         sk_landmarks=[sk_crotch, sk_neck], mh_landmarks=[mh_crotch, mh_neck],
         belly_face_mask=belly_face, mh_tris=mh_tris,
         # --- masculine-package extras ---
         pos_neutral_canonical_m=mh_pos,          # aligned masc neutral (19,158)
         pos_raw_baseobj_m=raw_pos,               # shared raw base.obj frame
         pos_macro_grounded_m=ev,                 # as dumped from Blender (13,380)
         frame_offset_m=frame_offset,             # grounded -> canonical shift
         torso_h=mh_h, torso_theta=mh_th,
         macro_gender=1.0)
qa = {
    "base": "hm08 masculine macro (gender 1.0; age/muscle/weight/proportions/"
            "height/cupsize/firmness 0.5; race thirds) -- MPFB defaults "
            "except gender",
    "frame_offset_m": frame_offset.tolist(),
    "frame_offset_method": "x/y: median of (grounded - raw) over body rows; "
                           "z: grounded z-min minus raw body z-min",
    "s_scale": s_scale, "h_star": h_star, "anchor_raw_m": anchor_raw,
    "anchor_m": anchor, "anchor_feminine_m": 0.1197,
    "anchor_deviation_vs_feminine_cm": float((anchor - 0.1197) * 100),
    "max_delta_source_m": max_delta,
    "navel_mh": navel_mh, "navel_sk": navel_sk,
    "navel_achieved_m": float(mh_delta[navel_mh, 1]),
    "navel_error_vs_anchor_cm": float((mh_delta[navel_mh, 1] - anchor) * 100),
    "cv_residual_m": cv, "cv_residual_torso_m": cv_all,
    "surface_residual_cm": reg_resid,
    "navel_pin_cm": float(pin_size * 100),
    "fold_scan": fold_scan, "safe_max": safe_max,
    "safe_max_raw_baseobj": safe_max_raw,
    "fold_repair_rounds_used": repair_rounds_used,
    "moved_verts": int(n_moved),
    "tangential_mean_cm": float(np.abs(sk_dt[samp]).mean() * 100),
    "landmarks": {"skyrim": [sk_crotch, sk_neck], "hm08_masc": [mh_crotch, mh_neck]},
    "kernel": {"sigma_h": SIG_H, "sigma_arc_m": SIG_A},
    "proportions": {"masculine": props_masc, "feminine": props_fem,
                    "raw_baseobj": props_raw},
    "method": "v1 method verbatim (kernel-field init; 60-iter non-rigid "
              "registration in torso-param space onto the source fat "
              "surface; canonical belly mask; tight navel pin; targeted "
              "fold repair) with the target side derived on the "
              "masculine-macro neutral and fold-checked on that neutral "
              "AND raw base.obj",
}
(WORK / "qa_numbers_masc.json").write_text(json.dumps(qa, indent=1))
print("QA:", json.dumps({k: qa[k] for k in
                         ["s_scale", "anchor_m", "safe_max", "moved_verts"]}, indent=1))
print("BUILD DONE")
