#!/usr/bin/env python3
"""
Belly v4 builder: REFERENCE-DRIVEN whole-torso adiposity system.

Joe on v3: "it still bulges weirdly, look at video of someone being
heavier, or furry artist tutorials they make." The study
(FAT_REFERENCE.md) verdict: v1-v3 hang a belly on a LEAN torso, so it
reads as an attached pouch. A heavy body is a SYSTEM (rule R1):
distribution follows muscle mass in levels (R2), pools low (R3), rolls
stack downward (R4), creases sit at fold/compression points (R5), the
apron overlaps the pubic region (R6), the back carries mass (R8), and
posture itself changes -- anterior pelvic tilt + lordosis (R9).

v4 model: the +1 endpoint of body.belly.protrusion becomes

    D4 = LIN + SAG
    LIN = B * D1 + (1 - B) * D_dist + D_crease + D_posture
    SAG = B * Dsag3                       (coupled, f(w) = w^2 as v3)

  * D1, Dsag3: the v1 protrusion and v3 pendant sag, UNCHANGED. Inside
    the belly-mask core (B = 1) v4 is exactly v3.
  * D_dist: a whole-torso DISTRIBUTION field, kernel-transferred
    (v1 machinery: torso-param (h, theta) radial+vertical fields) from
    TWO learned sources, blended 50/50:
      - the Fat Males full-torso morph (a dedicated fat-body sculpt);
      - the HIMBO "Chonky" preset recipe (the fattest artist-authored
        distribution we own) composed from Vanilla .osd blocks at the
        preset's high-weight values, gain-calibrated (alpha) so its
        belly-band forward peak matches Fat Males' -- the two sources
        are made to agree on belly size, then each fills the whole
        torso in its own way.
    Crossfaded against the belly field by the SAME mask B that bounds
    v3, so no region boundary exists in the shipped field: outside the
    ring the torso is pure distribution, inside it is pure v3, and the
    ring is a blend of two fields of comparable magnitude (metric M4
    gates the silhouette step).
  * D_crease: an authored waist crease (R5) -- a shallow radial pinch
    at the natural waist, sides+back only, depth solved against M7b.
  * D_posture: a small pelvis-anchored rotation shear (R9), kept only
    if it improves M1/M2 pre-repair without a fold cost (decision and
    both readings printed).

QA: hard gate 0 flips at +1 over ALL TORSO faces on both bases
(attenuation repair on A = D4 - D1, v2/v3 method; bisection fallback on
the distribution+crease scale), zone-split residuals vs the Fat Males
surface (v1 method), and the FAT_REFERENCE scorecard M1-M9 measured on
v3 and v4 alike.
"""
import json
import sys
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
HIMBO_DIR = (Path.home() / "workspace/character_assets/_himbo_work/CalienteTools"
             "/BodySlide/ShapeData/HIMBO")
sys.path.insert(0, str(LEARNED / "tools"))
from osdparse import load_osd  # noqa: E402

SK_UNIT_M = 0.01428
DM_M = 0.1
GAMMA4 = 2.0            # sag coupling, as v3

# HIMBO "Chonky" recipe: preset high-weight ("big") values / 100, blocks
# present in HIMBO Body - Vanilla.osd. Excluded, with reasons logged in
# GRAVITY_V4.md: SamuelLike 40 + FemmeB/FemmeBooba (blocks live in other
# sets; SamuelLike is a body-swap type morph), BellySmooth 100 (no
# Vanilla block), TorsoWaistSize 23 (direction ambiguous -- its display
# name is "Shrink Waist"), all Arms/Legs sliders (outside the torso
# gate; traps/shoulders kept because they ARE torso surface).
CHONKY = {
    "Chubby": 0.40, "TorsoMass": 1.00, "TorsoLower": 1.00,
    "TorsoBackShape": 0.92, "TorsoBackSlope": 0.90,
    "TorsoBellyLHandles": 0.66, "TorsoSterHeight": 1.00,
    "PecsSize": 1.00, "PecsWidth": 1.00, "PecsClavicle": 1.00,
    "PecsMass": 0.05, "ButtBooty": 0.75, "ButtDimpleDeepen": 1.00,
    "ButtSaggy": 0.11, "ArmsTrapsMeat": 1.00, "ArmsTrapsPush": 0.92,
    "ArmsShoulders": 0.50,
}

# ------------------------------------------------------------------ loads
corr = np.load(WORK / "correspondence.npz")
D1 = corr["mh_delta_canonical_m"].astype(np.float64)
B = corr["mh_mask"].astype(np.float64)                    # belly mask
navel_mh = int(corr["navel_mh"])
h_star = float(corr["h_star"])
mh_tris = corr["mh_tris"].astype(np.int64)
mh_crotch, mh_neck = [float(x) for x in corr["mh_landmarks"]]
L_mh = mh_neck - mh_crotch
_v3 = np.load(WORK / "belly_v3.npz")
D3 = _v3["delta_v3_canonical_m"].astype(np.float64)
Dsag3 = _v3["sag3_canonical_m"].astype(np.float64)

fm = np.load(LEARNED / "fat-males_body_morph.npz")
fm_pos = fm["body_vertices"].astype(np.float64) * SK_UNIT_M
fm_delta = fm["body_delta"].astype(np.float64) * SK_UNIT_M
fm_tri = fm["body_triangles"].astype(np.int64)

qa1 = json.loads((WORK / "qa_numbers.json").read_text())
anchor = qa1["anchor_m"]
FM_anchor_raw = qa1["anchor_raw_m"]

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

# ------------------------------------------------------- shared machinery
def compute_axis(pos, gate=None):
    if gate is None:
        gate = np.ones(len(pos), bool)
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

def crotch_of(pos, gate, mid_hw, slab_hw):
    mid = gate & (np.abs(pos[:, 0]) < mid_hw) & (np.abs(pos[:, 1]) < slab_hw)
    return pos[mid, 2].min()

def neck_base(pos, ctr, axis, crotch, label):
    ax = axis_at(ctr, axis, pos[:, 2])
    r = np.linalg.norm(pos[:, :2] - ax, axis=1)
    gated = r < 0.23
    bands = np.linspace(crotch, pos[:, 2].max(), 160)
    C = 0.5 * (bands[:-1] + bands[1:]); Wd = np.zeros(len(C))
    for i, (a, b) in enumerate(zip(bands[:-1], bands[1:])):
        m = gated & (pos[:, 2] >= a) & (pos[:, 2] < b)
        if m.sum() >= 4:
            Wd[i] = np.percentile(pos[m, 0], 99) - np.percentile(pos[m, 0], 1)
    above = C > crotch + 0.20 * (C[-1] - crotch)
    chest_i = int(np.argmax(np.where(above, Wd, 0)))
    neck, run = None, 0
    for i in range(chest_i + 1, len(Wd)):
        if 0 < Wd[i] < 0.55 * Wd[chest_i]:
            run += 1
            if run >= 3:
                neck = C[i - 2]; break
        else:
            run = 0
    print(f"{label}: chest {C[chest_i]:.3f} m (W={Wd[chest_i]:.3f} m), "
          f"neck base {neck:.4f} m")
    return neck

mh_ctr, mh_axis = compute_axis(mh_pos, mh_body)
mh_h, mh_th, mh_ax, mh_r = torso_params(mh_pos, mh_ctr, mh_axis, mh_crotch, mh_neck)
er_mh = np.stack([np.sin(mh_th), np.cos(mh_th)], axis=1)

edges_all = np.vstack([mh_tris[:, [0, 1]], mh_tris[:, [1, 2]], mh_tris[:, [2, 0]]])
edges_all = np.unique(np.sort(edges_all, axis=1), axis=0)
A = sp.coo_matrix((np.ones(len(edges_all)), (edges_all[:, 0], edges_all[:, 1])),
                  shape=(len(mh_pos), len(mh_pos)))
A = A + A.T
deg = np.asarray(A.sum(axis=1)).ravel()
Lop = sp.diags(1.0 / np.maximum(deg, 1)) @ A
nbrs = [np.asarray(A[v].nonzero()[1]) for v in range(len(mh_pos))]

def face_normals(P, F):
    n = np.cross(P[F[:, 1]] - P[F[:, 0]], P[F[:, 2]] - P[F[:, 0]])
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-14)

# ------------------------------------------------- kernel field (v1 method)
SIG_H, SIG_A = 0.05, 0.040

def make_field(pos, delta, crotch, neck, label):
    """(h, |theta|) -> (dr, dz) kernel field on a source torso, with
    5-fold CV over informative samples. Returns (eval_fn, info)."""
    ctr, axis = compute_axis(pos)
    h, th, ax, r = torso_params(pos, ctr, axis, crotch, neck)
    samp = (h > -0.02) & (h < 1.02) & (r < 0.30)
    er = np.stack([np.sin(th), np.cos(th)], axis=1)
    dr = np.einsum("ij,ij->i", delta[:, :2], er)
    dz = delta[:, 2]
    H = h[samp]; TH = np.abs(th[samp]); DR = dr[samp]; DZ = dz[samp]
    RR = r[samp]
    rb = np.linspace(0, 1, 21)
    rmean = np.array([RR[(H >= rb[i]) & (H < rb[i + 1])].mean()
                      if ((H >= rb[i]) & (H < rb[i + 1])).any() else 0.17
                      for i in range(20)])
    def arc(theta, hv):
        return theta * np.interp(hv, 0.5 * (rb[:-1] + rb[1:]), rmean)
    def ev(hq, tq, idx=None):
        if idx is None:
            idx = np.arange(len(H))
        out_r = np.zeros(len(hq)); out_z = np.zeros(len(hq))
        for s0 in range(0, len(hq), 800):
            q = slice(s0, s0 + 800)
            dh = (H[idx][:, None] - hq[q][None, :]) / SIG_H
            da = (arc(TH[idx], H[idx])[:, None]
                  - arc(np.abs(tq[q]), hq[q])[None, :]) / SIG_A
            w = np.exp(-0.5 * (dh ** 2 + da ** 2))
            ws = w.sum(axis=0) + 1e-12
            out_r[q] = (w * DR[idx][:, None]).sum(axis=0) / ws
            out_z[q] = (w * DZ[idx][:, None]).sum(axis=0) / ws
        return out_r, out_z
    rng = np.random.default_rng(20261112)
    inf = np.where(np.hypot(DR, DZ) > 0.0005)[0]
    perm = rng.permutation(inf); folds = np.array_split(perm, 5)
    errs = np.zeros(len(inf))
    for f in folds:
        tr = np.setdiff1d(perm, f)
        pos_in_inf = np.searchsorted(inf, f)
        pr, pz = ev(H[f], TH[f], idx=tr)
        errs[pos_in_inf] = np.hypot(pr - DR[f], pz - DZ[f])
    cv = {k: float(v * 100) for k, v in zip(
        ["p50", "p95", "max"], np.percentile(errs, [50, 95, 100]))}
    info = {"label": label, "samples": int(samp.sum()),
            "informative": int(len(inf)), "cv_cm": cv,
            "torso_len_m": float(neck - crotch)}
    print(f"field {label}: {samp.sum()} samples, CV p50 {cv['p50']:.3f} / "
          f"p95 {cv['p95']:.3f} / max {cv['max']:.3f} cm")
    return ev, info, (h, th, dr, dz)

# Fat Males field
fm_crotch = crotch_of(fm_pos, np.ones(len(fm_pos), bool), 0.030, 0.060)
_fm_ctr, _fm_axis = compute_axis(fm_pos)
fm_neck = neck_base(fm_pos, _fm_ctr, _fm_axis, fm_crotch, "fatmales")
fm_ev, fm_info, _ = make_field(fm_pos, fm_delta, fm_crotch, fm_neck, "fat_males")
s_fm = L_mh / fm_info["torso_len_m"]

# ------------------------------------------------------------- HIMBO side
def extract_base_positions(data, expect_min_verts):
    """Embedded vertex stream scan, copied from crosscheck_fields.py."""
    best = None
    for phase in range(0, 32, 2):
        n = (len(data) - phase) // 32
        if n < expect_min_verts:
            continue
        rec = np.frombuffer(data[phase:phase + n * 32], dtype="<f4")
        rec = rec.reshape(n, 8).astype(np.float64)
        pos, pad = rec[:, :3], rec[:, 3]
        ok = (np.isfinite(pos).all(axis=1) & (np.abs(pos[:, 0]) < 60) &
              (np.abs(pos[:, 1]) < 45) & (pos[:, 2] > -15) &
              (pos[:, 2] < 160) & (np.abs(pad) < 0.01) &
              (np.abs(pos).max(axis=1) > 0.05))
        ch = np.diff(np.concatenate(([0], ok.view(np.int8), [0])))
        st = np.where(ch == 1)[0]
        en = np.where(ch == -1)[0]
        for s, e in zip(st, en):
            if e - s >= expect_min_verts:
                run = pos[s:e]
                cand = (int(e - s), float(run[:, 2].max() - run[:, 2].min()), run)
                if best is None or cand[:2] > best[:2]:
                    best = cand
    return None if best is None else best[2]

hi_pos_u = extract_base_positions((HIMBO_DIR / "HIMBO Body - Vanilla.nif").read_bytes(), 4000)
assert hi_pos_u is not None and len(hi_pos_u) == 9346, None if hi_pos_u is None else len(hi_pos_u)
hi_pos = hi_pos_u * SK_UNIT_M
_osd = load_osd(str(HIMBO_DIR / "HIMBO Body - Vanilla.osd"))
blocks = {b["name"]: b for b in _osd["blocks"]}
hi_delta = np.zeros_like(hi_pos)
used, missing = {}, []
for slider, val in CHONKY.items():
    blk = blocks.get(f"HIMBO - Body{slider}")
    if blk is None:
        missing.append(slider); continue
    D = np.zeros_like(hi_pos)
    D[blk["indices"]] = blk["diffs"] * SK_UNIT_M
    hi_delta += val * D
    used[slider] = val
print(f"HIMBO Chonky composition: {len(used)} blocks used, missing: {missing}")
hi_crotch = crotch_of(hi_pos, np.ones(len(hi_pos), bool), 0.030, 0.060)
_hi_ctr, _hi_axis = compute_axis(hi_pos)
hi_neck = neck_base(hi_pos, _hi_ctr, _hi_axis, hi_crotch, "himbo   ")
hi_ev, hi_info, hi_par = make_field(hi_pos, hi_delta, hi_crotch, hi_neck, "himbo_chonky")
s_hi = L_mh / hi_info["torso_len_m"]

# gain calibration on the FLANK band. First attempt calibrated on the
# belly-band forward peak and failed instructively: the two sources
# DISAGREE about where fat goes -- Fat Males is a pot-belly sculpt
# (front peak 15.4 cm), Chonky is broad mass whose strongest front push
# is its pecs (belly front only ~4 cm). Forcing belly-peak equality
# would triple Chonky's widths. But the belly core is D1/D3's job (the
# crossfade replaces the distribution there); the distribution's job is
# torso WIDTH and mass, so the sources are matched where that job
# lives: mean |radial| over the flank band (|theta| 1.1-1.9, h 0.3-0.6).
def src_params(pos, delta, crotch, neck):
    ctr, axis = compute_axis(pos)
    h, th, ax, r = torso_params(pos, ctr, axis, crotch, neck)
    er = np.stack([np.sin(th), np.cos(th)], axis=1)
    dr = np.einsum("ij,ij->i", delta[:, :2], er)
    return h, th, dr
def flank_mean(h, th, dr):
    band = (np.abs(th) > 1.1) & (np.abs(th) < 1.9) & (h > 0.3) & (h < 0.6)
    return float(np.abs(dr[band]).mean())
def front_peak(h, th, dr):
    band = (np.abs(th) < 0.6) & (h > 0.25) & (h < 0.65)
    return float(dr[band].max())
fm_h2, fm_th2, fm_dr2 = src_params(fm_pos, fm_delta, fm_crotch, fm_neck)
hi_h2, hi_th2, hi_dr2 = src_params(hi_pos, hi_delta, hi_crotch, hi_neck)
fm_fl = flank_mean(fm_h2, fm_th2, fm_dr2); hi_fl = flank_mean(hi_h2, hi_th2, hi_dr2)
fm_peak = front_peak(fm_h2, fm_th2, fm_dr2); hi_peak = front_peak(hi_h2, hi_th2, hi_dr2)
alpha = float(np.clip((fm_fl * s_fm) / max(hi_fl * s_hi, 1e-9), 0.5, 2.0))
print(f"flank means (own base): Fat Males {fm_fl*100:.2f} cm, HIMBO Chonky "
      f"{hi_fl*100:.2f} cm -> alpha {alpha:.3f} (s_fm {s_fm:.3f}, s_hi {s_hi:.3f}); "
      f"belly front peaks (NOT matched, by design): FM {fm_peak*100:.2f} cm, "
      f"HIMBO {hi_peak*100:.2f} cm")

# ------------------------------------------------------- torso weight W
ramp_lo = np.clip((mh_h + 0.08) / 0.10, 0, 1)
ramp_hi = np.clip((1.03 - mh_h) / 0.10, 0, 1)
W = ramp_lo * ramp_hi
W[~mh_body] = 0.0
for _ in range(3):
    sm = Lop @ W
    W = np.where(W > 0.003, 0.5 * W + 0.5 * sm, 0.0)
W = np.clip(W, 0, 1)
torso_on = W > 0.003
print(f"torso weight: {(W > 0.05).sum()} verts > 0.05, max {W.max():.3f}")

# ------------------------------------------------------- D_dist on hm08
q_idx = np.where(torso_on | (B > 0.003))[0]
fm_dr_q, fm_dz_q = fm_ev(mh_h[q_idx], mh_th[q_idx])
hi_dr_q, hi_dz_q = hi_ev(mh_h[q_idx], mh_th[q_idx])
dr_d = 0.5 * (s_fm * fm_dr_q + alpha * s_hi * hi_dr_q)
dz_d = 0.5 * (s_fm * fm_dz_q + alpha * s_hi * hi_dz_q)
D_dist = np.zeros_like(mh_pos)
D_dist[q_idx, :2] = (W[q_idx] * dr_d)[:, None] * er_mh[q_idx]
D_dist[q_idx, 2] = W[q_idx] * dz_d
print(f"D_dist: moved {(np.abs(D_dist).max(axis=1) > 0.001).sum()} verts, "
      f"max |D| {np.linalg.norm(D_dist, axis=1).max()*100:.2f} cm")

# ------------------------------------------------- width/depth profiles
torso_gate = mh_body & (mh_r < 0.30)
def profiles(P, step=0.0125):
    zs = np.arange(mh_crotch - 0.05, mh_neck + 0.02, step)
    rows = []
    for z in zs:
        m = torso_gate & (np.abs(mh_pos[:, 2] - z) < step * 0.75)
        if m.sum() < 8:
            rows.append((z, np.nan, np.nan, np.nan)); continue
        axz = axis_at(mh_ctr, mh_axis, np.array([z]))[0]
        width = float(P[m, 0].max() - P[m, 0].min())
        depth = float(P[m, 1].max() - P[m, 1].min())
        rmean = float(np.linalg.norm(P[m, :2] - axz, axis=1).mean())
        rows.append((z, width, depth, rmean))
    return np.array(rows)
def girth_ellipse(width, depth):
    a, b = width / 2, depth / 2
    return np.pi * (3 * (a + b) - np.sqrt((3 * a + b) * (a + 3 * b)))
prof_base = profiles(mh_pos)
print("profiles computed")

# ------------------------------------------------------------- crease
def waist_find(P):
    pr = profiles(P)
    hh = (pr[:, 0] - mh_crotch) / L_mh
    win = (hh > h_star + 0.06) & (hh < h_star + 0.36)
    i = np.nanargmin(np.where(win, pr[:, 1], np.inf))
    h_w = float(hh[i])
    near = (hh > h_w + 0.05) & (hh < h_w + 0.11)
    far = (hh > h_w - 0.11) & (hh < h_w - 0.05)
    depth = float(min(np.nanmax(pr[near, 1]), np.nanmax(pr[far, 1])) - pr[i, 1])
    return h_w, depth, float(pr[i, 1])
D_pre0 = B[:, None] * D3 + (1 - B[:, None]) * D_dist          # composition before crease/posture
h_w, crease_depth0, waist_w0 = waist_find(mh_pos + D_pre0)
print(f"waist on dist-composition: h_w {h_w:.3f}, width {waist_w0*100:.1f} cm, "
      f"existing crease depth {crease_depth0*100:.2f} cm (M7b target 0.80)")
need = max(0.0, 0.008 - crease_depth0)
delta_crease = float(np.clip(need / 2 + (0.0015 if need > 0 else 0.0), 0, 0.012))
gth = np.clip((np.abs(mh_th) - 0.45) / 0.60, 0, 1)
gth = 0.5 - 0.5 * np.cos(np.pi * gth)                     # cosine ramp
gh = np.exp(-0.5 * ((mh_h - h_w) / 0.028) ** 2)
D_crease = np.zeros_like(mh_pos)
D_crease[:, :2] = (-delta_crease * gh * gth * W)[:, None] * er_mh
print(f"crease pinch: delta {delta_crease*100:.2f} cm radial at h_w "
      f"(sides+back gate)")

# ------------------------------------------------------------- posture
z_piv = mh_crotch + 0.02 * L_mh
piv = np.array([axis_at(mh_ctr, mh_axis, np.array([z_piv]))[0, 0],
                axis_at(mh_ctr, mh_axis, np.array([z_piv]))[0, 1], z_piv])
def posture_field(sign_on=True):
    if not sign_on:
        return np.zeros_like(mh_pos)
    a = (np.radians(-3.0) * np.exp(-0.5 * ((mh_h - 0.10) / 0.26) ** 2)
         + np.radians(1.4) * np.exp(-0.5 * ((mh_h - 0.85) / 0.16) ** 2))
    rel = mh_pos - piv
    ca, sa = np.cos(a), np.sin(a)
    rot = np.stack([rel[:, 0],
                    ca * rel[:, 1] - sa * rel[:, 2],
                    sa * rel[:, 1] + ca * rel[:, 2]], axis=1)
    return (rot - rel) * W[:, None]
D_posture = posture_field(True)

# ------------------------------------------- fold machinery on torso faces
Ft_mask = np.array([max(B[list(f)]) > 0.02 or max(W[list(f)]) > 0.02
                    for f in mh_tris])
Ft = mh_tris[Ft_mask]
BASES = {"raw": mh_pos, "macro": mh_pos_mac}
n0_all = {k: face_normals(p, Ft) for k, p in BASES.items()}
def flips_on(delta, bname, F, n0):
    nn = face_normals(BASES[bname] + delta, F)
    dots = np.einsum("ij,ij->i", n0, nn)
    return int((dots < 0).sum()), float(dots.min())
def flips_t(delta, bname):
    return flips_on(delta, bname, Ft, n0_all[bname])
print(f"torso fold faces: {len(Ft)} (belly faces were "
      f"{int(corr['belly_face_mask'].sum())})")

# ------------------------------------- posture decision (pre-repair M1/M2)
def m1_m2(D):
    drad = np.einsum("ij,ij->i", D[:, :2], er_mh)
    front = torso_gate & (np.abs(mh_th) < 0.6) & ((W > 0.1) | (B > 0.1))
    pos = np.clip(drad[front], 0, None)
    below = pos[mh_h[front] < h_star].sum(); above = pos[mh_h[front] >= h_star].sum()
    low = front & (mh_h < h_star) & (np.abs(mh_th) < 0.7)
    lowest = float((mh_pos[low, 2] + D[low, 2]).min() - mh_crotch) * 100
    return {"below_share_pct": float(below / max(below + above, 1e-12)) * 100,
            "lowest_above_crotch_cm": lowest}
D4_post = B[:, None] * D3 + (1 - B[:, None]) * D_dist + D_crease + D_posture
D4_nopost = B[:, None] * D3 + (1 - B[:, None]) * D_dist + D_crease
mm_post, mm_nopost = m1_m2(D4_post), m1_m2(D4_nopost)
fp_post = flips_t(D4_post, "raw")[0] + flips_t(D4_post, "macro")[0]
fp_nopost = flips_t(D4_nopost, "raw")[0] + flips_t(D4_nopost, "macro")[0]
keep_posture = (mm_post["below_share_pct"] >= mm_nopost["below_share_pct"] - 1.0
                and mm_post["lowest_above_crotch_cm"] <= mm_nopost["lowest_above_crotch_cm"] + 0.05
                and fp_post <= fp_nopost + 200)
print(f"posture decision: with {mm_post} pre-flips {fp_post}; without "
      f"{mm_nopost} pre-flips {fp_nopost} -> keep_posture {keep_posture}")
if not keep_posture:
    D_posture = np.zeros_like(mh_pos)

# ------------------------------------------------- compose + repair
def compose(dist_scale=1.0):
    LIN = B[:, None] * D1 + (1 - B[:, None]) * (dist_scale * D_dist) \
        + dist_scale * D_crease + D_posture
    SAG = B[:, None] * Dsag3
    return LIN + SAG, LIN, SAG
torso_edges = np.array([e for e in edges_all
                        if (W[e[0]] > 0.003 or B[e[0]] > 0.003)
                        and (W[e[1]] > 0.003 or B[e[1]] > 0.003)])
elen = np.linalg.norm(mh_pos[torso_edges[:, 0]] - mh_pos[torso_edges[:, 1]], axis=1)
KAPPA = 0.55
def slope_limit(Ds):
    Ds = Ds.copy()
    for it in range(80):
        diff = Ds[torso_edges[:, 0]] - Ds[torso_edges[:, 1]]
        dn = np.linalg.norm(diff, axis=1)
        excess = dn - KAPPA * elen
        if (excess <= 0).all():
            return Ds, it
        corr_ = np.zeros_like(Ds); wgt = np.zeros(len(Ds))
        m_ = excess > 0
        adj = (0.5 * excess[m_] / np.maximum(dn[m_], 1e-12))[:, None] * diff[m_]
        np.add.at(corr_, torso_edges[m_, 0], -adj)
        np.add.at(corr_, torso_edges[m_, 1], adj)
        np.add.at(wgt, torso_edges[m_, 0], 1); np.add.at(wgt, torso_edges[m_, 1], 1)
        Ds += 0.7 * corr_ / np.maximum(wgt, 1)[:, None]
    return Ds, 80
def repair(A_raw, max_rounds=60):
    att = np.ones(len(A_raw))
    Av = A_raw.copy()
    for rnd in range(max_rounds):
        D = D1 + Av
        if flips_t(D, "raw")[0] == 0 and flips_t(D, "macro")[0] == 0:
            return Av, att, True, rnd
        bad = np.zeros(len(Ft), bool)
        for k in BASES:
            nn = face_normals(BASES[k] + D, Ft)
            dots = np.einsum("ij,ij->i", n0_all[k], nn)
            bad |= dots < 0.01
        bad_verts = np.unique(Ft[bad])
        ring = np.unique(np.concatenate([nbrs[v] for v in bad_verts]))
        att[bad_verts] *= 0.82
        att[ring] *= 0.94
        att = np.where((W > 0.003) | (B > 0.003),
                       0.65 * att + 0.35 * (Lop @ att), att)
        att = np.clip(att, 0.10, 1.0)
        Av = att[:, None] * A_raw
    D = D1 + Av
    ok = flips_t(D, "raw")[0] == 0 and flips_t(D, "macro")[0] == 0
    return Av, att, ok, max_rounds

shipped_scale = None
for s_try in (1.0, 0.85, 0.7, 0.55):
    D4c, LINc, SAGc = compose(s_try)
    A_raw = D4c - D1
    for _ in range(5):
        sm = Lop @ A_raw
        gate = np.maximum(W, B)
        A_raw = A_raw + 0.35 * gate[:, None] * (sm - A_raw)
    A_raw, lim_it = slope_limit(A_raw)
    pre = (flips_t(D1 + A_raw, "raw")[0], flips_t(D1 + A_raw, "macro")[0])
    A_fin, att, converged, rounds = repair(A_raw)
    print(f"dist scale {s_try}: limiter {lim_it} it, pre-repair flips "
          f"raw/macro {pre}, repair converged {converged} in {rounds} "
          f"rounds, att min {att.min():.2f}")
    if converged:
        shipped_scale = s_try
        D4 = D1 + A_fin
        LIN = D4 - SAGc
        SAG = SAGc
        A_shipped = A_fin
        break
assert shipped_scale is not None, "no distribution scale repaired clean"
print(f"shipped distribution scale: {shipped_scale}")

# ------------------------------------------------------------- fold scans
f05 = 0.5 ** GAMMA4
states = {"-1 (linear)": -D4,
          "+0.5 (coupled)": 0.5 * LIN + f05 * SAG,
          "+1 (combined)": D4,
          "+1.05 (combined)": 1.05 * D4}
fold_scan = {}
for name, D in states.items():
    fold_scan[name] = {b: flips_t(D, b) for b in BASES}
    print(f"fold scan {name}: raw {fold_scan[name]['raw']}, "
          f"macro {fold_scan[name]['macro']}")

def navel_vec(D):
    return {"forward_cm": float(D[navel_mh, 1] * 100),
            "down_cm": float(-D[navel_mh, 2] * 100)}
nav = {"v3_at_+1": navel_vec(D3), "v4_at_+1": navel_vec(D4),
       "v4_at_+0.5_coupled": navel_vec(0.5 * LIN + f05 * SAG),
       "anchor_forward_m": anchor}
print("navel:", json.dumps(nav, indent=1))

# ------------------------------------------------------------- metrics
def full_metrics(D, tag):
    P = mh_pos + D
    pr = profiles(P); pr0 = prof_base
    hh = (pr[:, 0] - mh_crotch) / L_mh
    gir = girth_ellipse(pr[:, 1], pr[:, 2])
    waist_i = np.nanargmin(np.where((hh > h_star + 0.06) & (hh < h_star + 0.36), gir, np.inf))
    hip_i = np.nanargmax(np.where((hh > -0.02) & (hh < 0.12), gir, -np.inf))
    chest = (hh > 0.80) & (hh < 0.90)
    height = float(mh_pos[mh_body, 2].max() - mh_pos[mh_body, 2].min())
    mm = m1_m2(D)
    # M4 boundary step on the width profile (1.25 cm bands as computed)
    wprof = pr[:, 1]
    grads = np.abs(np.diff(wprof)) / 0.0125
    ring = np.zeros(len(pr), bool)
    for i, z in enumerate(pr[:, 0]):
        m = torso_gate & (np.abs(mh_pos[:, 2] - z) < 0.0094)
        if m.sum() >= 8:
            bmax = B[m].max()
            ring[i] = 0.05 < bmax < 0.95
    g_ring = grads[:-1][ring[1:-1]] if ring[1:-1].any() else np.array([0.0])
    g_out = grads[:-1][~ring[1:-1]] if (~ring[1:-1]).any() else np.array([1.0])
    m4 = float(np.nanmax(g_ring) / max(np.nanmedian(g_out), 1e-9))
    # M5 back, M6 chest front (added radial)
    drad = np.einsum("ij,ij->i", D[:, :2], er_mh)
    back = torso_gate & (np.abs(mh_th) > 2.5) & (mh_h > h_star + 0.02) & (mh_h < h_star + 0.30)
    chestf = torso_gate & (np.abs(mh_th) < 0.8) & (mh_h > 0.78) & (mh_h < 0.92)
    # M7b waist crease on width profile
    hw2, dep2, _ = waist_find(P)
    # M8 volume proxy: sum over bands of pi (R^2_def - R^2_base) dz
    vol = float(np.nansum(np.pi * (pr[:, 3] ** 2 - pr0[:, 3] ** 2)) * 0.0125) * 1e6
    out = {
        "below_share_pct (M1)": round(mm["below_share_pct"], 1),
        "lowest_above_crotch_cm (M2)": round(mm["lowest_above_crotch_cm"], 2),
        "waist_girth_cm": round(float(gir[waist_i]) * 100, 1),
        "hip_girth_cm": round(float(gir[hip_i]) * 100, 1),
        "waist_hip_ratio (M3)": round(float(gir[waist_i] / gir[hip_i]), 3),
        "boundary_step_ratio (M4)": round(m4, 2),
        "back_radial_cm (M5)": round(float(drad[back].mean()) * 100, 2),
        "chest_front_radial_cm (M6)": round(float(drad[chestf].mean()) * 100, 2),
        "chest_width_gain_cm (M6b)": round(float(np.nanmean(pr[chest, 1]) - np.nanmean(pr0[chest, 1])) * 100, 2),
        "waist_crease_depth_cm (M7b)": round(dep2 * 100, 2),
        "waist_h_found": round(hw2, 3),
        "added_torso_volume_proxy_cm3 (M8)": round(vol, 1),
        "waist_height_ratio (M9)": round(float(gir[waist_i]) / height, 3),
    }
    print(f"metrics {tag}: " + json.dumps(out, indent=1))
    return out
met3 = full_metrics(D3, "v3")
met4 = full_metrics(D4, "v4")
met4["added_torso_volume_ratio_v4_over_v3 (M8)"] = round(
    met4["added_torso_volume_proxy_cm3 (M8)"] / max(met3["added_torso_volume_proxy_cm3 (M8)"], 1e-9), 2)

# v3-style profile metrics (crease pinch M7a) for both
def profile_metrics(D):
    drad = np.einsum("ij,ij->i", D[:, :2], er_mh)
    h_c = h_star - 0.16
    front = (B > 0.3) & (np.abs(mh_th) < 0.5)
    def band(hlo, hhi):
        m_ = front & (mh_h > hlo) & (mh_h < hhi)
        return float(drad[m_].mean()) * 100 if m_.sum() >= 3 else None
    bulge = band(h_c + 0.05, h_c + 0.17)
    crease = band(h_c - 0.035, h_c + 0.035)
    pinch = None if (not bulge or crease is None) else round(crease / bulge, 3)
    return {"bulge_extent_cm": None if bulge is None else round(bulge, 2),
            "crease_extent_cm": None if crease is None else round(crease, 2),
            "crease_pinch_ratio (M7a)": pinch}
pm3, pm4 = profile_metrics(D3), profile_metrics(D4)
print("pinch:", json.dumps({"v3": pm3, "v4": pm4}, indent=1))

# ------------------------------------------------- zone-split residuals
def param_coords(pos, ctr, axis, crotch, L):
    h, th, ax, r = torso_params(pos, ctr, axis, crotch, crotch + L)
    return np.stack([th * r / L, h, r / L], axis=1)
def tri_closest(P, A_, B_, C_):
    ab, ac, ap = B_ - A_, C_ - A_, P - A_
    d1 = np.einsum("ij,ij->i", ab, ap); d2 = np.einsum("ij,ij->i", ac, ap)
    d3 = np.einsum("ij,ij->i", ab, ab); d4 = np.einsum("ij,ij->i", ab, ac)
    d5 = np.einsum("ij,ij->i", ac, ac)
    den = np.maximum(d3 * d5 - d4 * d4, 1e-14)
    vc = (d3 * d2 - d4 * d1) / den; vb = (d5 * d1 - d4 * d2) / den
    inside = (vb >= 0) & (vc >= 0) & (vb + vc <= 1)
    plane = A_ + vb[:, None] * ab + vc[:, None] * ac
    best = plane.copy()
    bestd = np.where(inside, np.linalg.norm(P - plane, axis=1), np.inf)
    for E0, E1 in ((A_, B_), (B_, C_), (C_, A_)):
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
            A_ = self.P[self.F[cand, 0]]; B_ = self.P[self.F[cand, 1]]
            C_ = self.P[self.F[cand, 2]]
            cp, dd = tri_closest(np.repeat(Q[i:i + 1], len(cand), axis=0), A_, B_, C_)
            j = int(np.argmin(dd))
            out_c[i] = cp[j]; out_d[i] = dd[j]
        return out_c, out_d
L_sk = fm_neck - fm_crotch
skP_fat = param_coords(fm_pos + fm_delta, _fm_ctr, _fm_axis, fm_crotch, L_sk)
_fm_h3, _fm_th3, _fm_ax3, _fm_r3 = torso_params(fm_pos, _fm_ctr, _fm_axis, fm_crotch, fm_neck)
src_tris = []
for f in fm_tri:
    if np.all((_fm_h3[f] > -0.02) & (_fm_h3[f] < 1.02) & (_fm_r3[f] < 0.30)):
        u = skP_fat[f][:, 0]
        if np.max(u) - np.min(u) < 0.5:
            src_tris.append(f)
src_surf = ParamSurface(skP_fat, np.array(src_tris))
def fwd_resid(delta):
    P = param_coords(mh_pos + delta, mh_ctr, mh_axis, mh_crotch, L_mh)
    core = np.where(B > 0.5)[0]
    _, d = src_surf.closest(P[core])
    return core, d * L_sk * 100
core1, r4 = fwd_resid(D4)
pd_navel = np.sqrt(((mh_h[core1] - h_star) * L_mh) ** 2 +
                   (np.abs(mh_th[core1]) * mh_r[core1]) ** 2)
zones = {
    "pin_patch": pd_navel < 0.045,
    "crease": (pd_navel >= 0.045) & (mh_h[core1] < h_star - 0.08) & (np.abs(mh_th[core1]) < 1.05),
    "flank": (pd_navel >= 0.045) & ~((mh_h[core1] < h_star - 0.08) & (np.abs(mh_th[core1]) < 1.05)) & (np.abs(mh_th[core1]) >= 0.9),
}
zones["core"] = ~(zones["pin_patch"] | zones["crease"] | zones["flank"])
qa3 = json.loads((WORK / "qa_numbers_v3.json").read_text())
zone_rows = {}
for zn, zm in zones.items():
    if zm.sum() == 0:
        continue
    z3 = qa3["zones"].get(zn, {})
    zone_rows[zn] = {"n": int(zm.sum()),
                     "v3_p95_cm": z3.get("v3_p95_cm"),
                     "v4_p50_cm": float(np.percentile(r4[zm], 50)),
                     "v4_p95_cm": float(np.percentile(r4[zm], 95))}
    print(f"zone {zn}: n={zm.sum()} v4 p95 {zone_rows[zn]['v4_p95_cm']:.2f} cm "
          f"(v3 {zone_rows[zn]['v3_p95_cm']})")
allrow = {"n": int(len(core1)),
          "v4_p50_cm": float(np.percentile(r4, 50)),
          "v4_p95_cm": float(np.percentile(r4, 95)),
          "v3_p95_cm": qa3["zones_all_triangle_exact"]["v3_p95_cm"]}
print(f"zone ALL: v4 p95 {allrow['v4_p95_cm']:.2f} cm (v3 {allrow['v3_p95_cm']})")

# ---------------------------------------------------------------- targets
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
NOTE4 = ("Provenance: omniversal slider body.belly.protrusion v4 (reference-"
         "driven whole-torso adiposity), instance makehuman_hm08. Combined "
         "field at w=+1: v3 belly in the mask core, learned whole-torso "
         "distribution field (Fat Males + HIMBO Chonky recipe) outside it, "
         "authored waist crease, posture shear. Study-only, internal - "
         "not a CC0 MakeHuman asset. See GRAVITY_V4.md / FAT_REFERENCE.md.")
NOTED = ("Provenance: DISTRIBUTION component of body.belly.protrusion v4 "
         "(= combined v4 - v3 combined). Apply linearly in w alongside the "
         "v1 protrusion target and the v3 sag target (coupling gamma 2.0). "
         "Study-only, internal.")
n_v4 = write_target(OUT / "body.belly.protrusion_v4.target", D4, NOTE4)
Ddist_comp = D4 - D3
n_dc = write_target(OUT / "body.belly.protrusion_distribution_v4.target",
                    Ddist_comp, NOTED)
print(f"targets written: v4 combined {n_v4} moved verts, "
      f"distribution component {n_dc}")

np.savez(WORK / "belly_v4.npz", delta_v4_canonical_m=D4, lin_v4_canonical_m=LIN,
         sag_v4_canonical_m=SAG, dist_component_canonical_m=Ddist_comp,
         d_dist_canonical_m=D_dist, d_crease_canonical_m=D_crease,
         d_posture_canonical_m=D_posture, torso_weight=W,
         alpha=alpha, shipped_dist_scale=shipped_scale,
         keep_posture=keep_posture, navel_mh=navel_mh, gamma=GAMMA4)
qa4 = {
    "model": {"gamma_coupling": GAMMA4, "shipped_dist_scale": shipped_scale,
              "alpha_himbo_calibration": alpha,
              "fm_peak_cm": fm_peak * 100, "himbo_peak_cm": hi_peak * 100,
              "s_fm": s_fm, "s_hi": s_hi,
              "himbo_recipe_used": used, "himbo_recipe_missing": missing,
              "crease": {"h_w": h_w, "pre_depth_cm": crease_depth0 * 100,
                         "pinch_cm": delta_crease * 100},
              "posture": {"kept": bool(keep_posture),
                          "with": mm_post, "without": mm_nopost,
                          "preflips_with": fp_post, "preflips_without": fp_nopost},
              "attenuation": {"min": float(att.min()),
                              "verts_under_0.99": int((att < 0.99).sum()),
                              "rounds": rounds},
              "fields": {"fm": fm_info, "himbo": hi_info}},
    "navel": nav,
    "metrics_v3": met3, "metrics_v4": met4,
    "pinch_v3": pm3, "pinch_v4": pm4,
    "fold_scan": {k: {b: {"flips": v[b][0], "min_dot": v[b][1]}
                      for b in BASES} for k, v in fold_scan.items()},
    "torso_faces_checked": int(len(Ft)),
    "zones": zone_rows, "zones_all_triangle_exact": allrow,
    "moved_verts": {"v4_combined": n_v4, "distribution_component": n_dc},
}
(WORK / "qa_numbers_v4.json").write_text(json.dumps(qa4, indent=1))
print("QA v4 saved")
