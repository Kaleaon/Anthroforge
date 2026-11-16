#!/usr/bin/env python3
"""
Belly v5 builder: EXTEND THE SYSTEM INTO THE LIMBS.

Joe (Nov 12, 2026): "keep learning and look up further lessons for
bara, etc, and apply it." v4 made fat a whole-TORSO system and Joe
accepted the direction; its named remaining debit was that the system
boundary sat at the arm/thigh roots -- the limbs stayed lean.

v5 model: the +1 endpoint stays one coupled field,

    D5 = D4 + LIMB_INCREMENT
    LIMB_INCREMENT(v) = m(v) * w_prox(s) * ( F_limb(v) * d_fade(s) - D4(v) )

on limb-region verts, 0 elsewhere:
  * F_limb: a LIMB transfer of the same two learned sources v4 used --
    the Fat Males full field (its body mesh carries arms+legs) and the
    HIMBO "Chonky" preset recipe, this time composed from the preset's
    ARMS and LEGS blocks (the ones v4 excluded as outside its torso
    gate). Atomic Muscle cannot contribute a transferable field: its
    FO4 NIF vertex buffer defeated extraction in the v3 cross-check
    (field-level dz statistics only), so it stays a cross-check, as
    in v3/v4.
  * Parametrization is limb-local, mirroring the torso's (h, theta)
    kernel one level down: each limb gets an axis polyline extracted
    from cross-section centroids (legs: z-bands; arms: PCA bands),
    and verts are described by (s, phi) -- arc position along the limb
    and angle around it, phi measured in MIRRORED right-limb space so
    inner/outer/front/back mean the same on both sides (the torso
    kernel folded |theta|; limbs must NOT fold -- inner thigh != outer
    thigh). Components kept: radial dr and axial da; tangential
    dropped, as the torso dropped it.
  * The increment is a CROSSFADE, the same construction v4 used for
    belly-vs-distribution: proximally (w_prox -> 0) the vert keeps
    v4's value; distally it becomes the pure limb field. This matters
    beyond smoothness: v4's torso field was evaluated off-gate on
    every vert at torso heights, so forearms/hands carry a spurious
    torso-band extrapolation in D4. d_fade -> 0 at the wrist/ankle
    retires it there: hands/feet end at ~zero displacement, lean as
    anatomy says (limb reference rule L1).
  * Calibration mirrors v4: per-limb length-ratio scaling per source,
    HIMBO alpha matched to Fat Males on the thigh band (the largest
    limb fat site, R2), capped [0.5, 2.0], reported.
  * Two disclosed reference-driven shapings sit on top of the blend
    where the sources' construction conflicts with the reference
    rules (details at the code sites): an arm underside sector gain
    (R3/L3 -- HIMBO's arm recipe is muscle-led, Fat Males' arm is
    coarse) and a leg distal taper (L4 -- the blend otherwise tubes
    the shank; gains belong over the gastrocnemius belly).

Limb reference addendum (small targeted check, Nov 12, 2026; FAT_
REFERENCE.md is silent on limbs beyond R2/R3/R10):
  L1 proximal gradient -- limbs carry more fat near the torso:
     upper arm > forearm > hand (least; bone shows), thigh > calf >
     ankle. [Love Life Drawing, "How to draw fat"]
  L2 joints stay findable -- fat accumulates AROUND joints, not on
     top of them: pads behind the knee, around the elbow; the named
     postdeltoid pad on the back of the upper arm (Richer, via
     Morpho: Fat and Skin Folds). Elbow/knee girth minima persist.
  L3 underside pooling -- upper-arm mass hangs on the underside,
     thigh mass pools outer + inner (R3 restated for limbs).
  L4 calf moderation -- the calf's subcutaneous layer is thin even
     in heavy legs (pinch ~1.5-2 cm in lipo candidates); calf shape
     is gastrocnemius-belly dominated, so gains sit HIGH on the calf
     and taper hard to a lean ankle. [clinical/liposuction anatomy]
  L5 contact squish (R10) -- inner thighs meet and flatten; handled
     here as a measured contact cap, not interpenetration.

QA: hard gate 0 flips at +1 over ALL BODY faces on both bases
(attenuation repair on the increment, v2-v4 method; slope limiter;
scale bisection fallback), v4 scorecard re-run on D5, new limb
metrics (girth gains at segment midpoints, elbow/knee landmark
persistence, boundary-step ratios at shoulder/elbow/hip/knee/wrist/
ankle, upper-arm underside pooling, inner-thigh gap/contact).
"""
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import scipy.sparse as sp

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
BODY_END = 13380

# HIMBO "Chonky" preset recipe, ARMS + LEGS blocks only (big values
# /100 from himbo_presets_all.json; every listed slider has small=0
# in the preset). Torso blocks are v4's, not repeated here. Sliders
# the preset leaves at 0 stay 0 (LegsThighInnerSide among them --
# inner-thigh mass in this recipe rides on Size/Thigh/Chubby/
# FemurUpper, not a dedicated inner slider).
# NOTE: 5 of the 22 exist only on the SOS-variant mesh (DeltsShape,
# ThighSmoothCurve, VastusMReduction, CalfOut, CalfSideIn). Verified
# Nov 12, 2026: the SOS OSD's same-named blocks carry different
# vertex supports (e.g. LegsCalfWidth 2422 vs 4009 verts), so they
# do NOT index the Vanilla base v4 used and cannot be composed onto
# it. The 17 carried blocks include every primary mass slider; the
# missing five are shape refinements. Disclosed in GRAVITY_V5.md.
LIMB_HIMBO = {
    "ArmsBiceps": 1.00, "ArmsClavicleCurve": 1.00, "ArmsDelts": 1.00,
    "ArmsDeltsBack": 0.27, "ArmsDeltsLower": 0.23, "ArmsDeltsShape": 0.30,
    "ArmsDeltsUpper": 0.18, "ArmsFore": 1.00,
    "LegsSize": 1.00, "LegsThigh": 1.00, "LegsChubby": 0.94,
    "LegsFemurUpper": 0.62, "LegsFemurLower": 0.05, "LegsGlutes": 0.38,
    "LegsKneePit": 0.57, "LegsThighSmoothCurve": 0.58,
    "LegsVastusMReduction": 0.58, "LegsCalfWidth": 0.72,
    "LegsCalfOut": 0.55, "LegsCalfSideIn": 0.36, "LegsCalfLower": 0.33,
    "LegsCalfUpper": 0.12,
}

# ------------------------------------------------------------------ loads
corr = np.load(WORK / "correspondence.npz")
navel_mh = int(corr["navel_mh"])
h_star = float(corr["h_star"])
mh_tris = corr["mh_tris"].astype(np.int64)
mh_crotch, mh_neck = [float(x) for x in corr["mh_landmarks"]]
L_mh = mh_neck - mh_crotch
_v4 = np.load(WORK / "belly_v4.npz")
D4 = _v4["delta_v4_canonical_m"].astype(np.float64)
LIN4 = _v4["lin_v4_canonical_m"].astype(np.float64)
SAG = _v4["sag_v4_canonical_m"].astype(np.float64)
GAMMA = float(_v4["gamma"])

fm = np.load(LEARNED / "fat-males_body_morph.npz")
fm_pos = fm["body_vertices"].astype(np.float64) * SK_UNIT_M
fm_delta = fm["body_delta"].astype(np.float64) * SK_UNIT_M

with zipfile.ZipFile(MPFB_ZIP) as z:
    obj_lines = z.read("mpfb/data/3dobjs/base.obj").decode().splitlines()
mh_obj = np.array([[float(x) for x in l.split()[1:4]]
                   for l in obj_lines if l.startswith("v ")])
mh_faces = []
for l in obj_lines:
    if l.startswith("f "):
        mh_faces.append([int(t.split("/")[0]) - 1 for t in l.split()[1:]])
mh_pos = np.stack([mh_obj[:, 0], mh_obj[:, 2], mh_obj[:, 1]], axis=1) * DM_M
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

def crotch_of(pos, gate, mid_hw=0.030, slab_hw=0.060):
    mid = gate & (np.abs(pos[:, 0]) < mid_hw) & (np.abs(pos[:, 1]) < slab_hw)
    return float(pos[mid, 2].min())

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
    print(f"{label}: neck base {neck:.4f} m")
    return neck

def face_normals(P, F):
    n = np.cross(P[F[:, 1]] - P[F[:, 0]], P[F[:, 2]] - P[F[:, 0]])
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-14)

edges_all = np.vstack([mh_tris[:, [0, 1]], mh_tris[:, [1, 2]], mh_tris[:, [2, 0]]])
edges_all = np.unique(np.sort(edges_all, axis=1), axis=0)
A_mat = sp.coo_matrix((np.ones(len(edges_all)),
                       (edges_all[:, 0], edges_all[:, 1])),
                      shape=(len(mh_pos), len(mh_pos)))
A_mat = A_mat + A_mat.T
deg = np.asarray(A_mat.sum(axis=1)).ravel()
Lop = sp.diags(1.0 / np.maximum(deg, 1)) @ A_mat
nbrs = [np.asarray(A_mat[v].nonzero()[1]) for v in range(len(mh_pos))]

# ------------------------------------------------ limb axis extraction
def smooth_polyline(pts, passes=3):
    """Binomial smoothing, endpoints fixed. Coarse source meshes
    (Fat Males: 2,024 verts) give band centroids that zigzag; an
    unsmoothed axis inflates arc length and corrupts (s, phi)."""
    pts = pts.copy()
    for _ in range(passes):
        mid = 0.25 * pts[:-2] + 0.5 * pts[1:-1] + 0.25 * pts[2:]
        pts[1:-1] = mid
    return pts

def extract_limbs(pos, gate, label):
    """Returns dict: for each of arm_R/arm_L/leg_R/leg_L a polyline
    (proximal->distal points), its length, side sign. Legs: z-band
    centroids per side. Arms: PCA-direction bands per side."""
    ctr, axis = compute_axis(pos, gate)
    ax_x = lambda z: np.interp(z, ctr, axis[:, 0])
    crotch = crotch_of(pos, gate)
    neck = neck_base(pos, ctr, axis, crotch, label)
    zmin = float(pos[gate, 2].min())
    out = {}
    # ---- legs (bands ascend ankle->hip; reversed to proximal-first)
    for side, sname in ((1.0, "R"), (-1.0, "L")):
        seeds = gate & (np.sign(pos[:, 0] - ax_x(pos[:, 2])) == side) \
            & (np.abs(pos[:, 0] - ax_x(pos[:, 2])) > 0.025) \
            & (pos[:, 2] < crotch + 0.02) & (pos[:, 2] > zmin + 0.09)
        pts = []
        zb = np.arange(zmin + 0.09, crotch + 0.02, 0.025)
        for a in zb:
            m = seeds & (pos[:, 2] >= a) & (pos[:, 2] < a + 0.025)
            if m.sum() >= 4:
                pts.append(pos[m].mean(axis=0))
        pts = np.array(pts)                       # ankle -> hip order
        d_top = pts[-1] - pts[-2]; d_top /= np.linalg.norm(d_top)
        d_bot = pts[0] - pts[1]; d_bot /= np.linalg.norm(d_bot)
        pts = np.vstack([pts[0] + d_bot * 0.05, pts, pts[-1] + d_top * 0.06])
        pts = smooth_polyline(pts[::-1].copy())   # hip -> ankle order
        seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
        out[f"leg_{sname}"] = {"pts": pts, "length": float(seg.sum()),
                               "side": side, "kind": "leg"}
    # ---- arms
    for side, sname in ((1.0, "R"), (-1.0, "L")):
        seeds = gate & (np.sign(pos[:, 0] - ax_x(pos[:, 2])) == side) \
            & (np.abs(pos[:, 0] - ax_x(pos[:, 2])) > 0.17) \
            & (pos[:, 2] > crotch + 0.10) & (pos[:, 2] < neck + 0.02)
        P = pos[seeds]
        c0 = P.mean(axis=0)
        _, _, vt = np.linalg.svd(P - c0, full_matrices=False)
        d = vt[0]
        if d[0] * side < 0:
            d = -d
        t = (P - c0) @ d
        pts = []
        tb = np.arange(t.min(), t.max(), 0.025)
        for a in tb:
            m = (t >= a) & (t < a + 0.025)
            if m.sum() >= 3:
                pts.append(P[m].mean(axis=0))
        pts = np.array(pts)                       # shoulder -> wrist order
        d0 = pts[1] - pts[0]; d0 /= np.linalg.norm(d0)
        d1 = pts[-1] - pts[-2]; d1 /= np.linalg.norm(d1)
        pts = np.vstack([pts[0] - d0 * 0.05, pts, pts[-1] + d1 * 0.03])
        pts = smooth_polyline(pts)
        seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
        out[f"arm_{sname}"] = {"pts": pts, "length": float(seg.sum()),
                               "side": side, "kind": "arm"}
    for k, v in out.items():
        print(f"{label} {k}: {len(v['pts'])} axis pts, length "
              f"{v['length']*100:.1f} cm, prox {np.round(v['pts'][0],3)}, "
              f"dist {np.round(v['pts'][-1],3)}")
    return out

def limb_params(pos, limb):
    """(s, dist, phi, er, adir) for every vert vs one limb polyline.
    phi measured in mirrored right-limb space: left limbs are x-flipped
    about x=0 for the angle only, so phi=0 is lateral-out, +pi/2 front,
    pi inner, -pi/2 back on BOTH sides."""
    pts = limb["pts"]; side = limb["side"]
    segv = np.diff(pts, axis=0)
    seglen = np.linalg.norm(segv, axis=1)
    cum = np.concatenate([[0], np.cumsum(seglen)])
    L = cum[-1]
    best_d2 = np.full(len(pos), np.inf)
    s_out = np.zeros(len(pos)); pt_out = np.zeros_like(pos)
    dir_out = np.zeros_like(pos)
    for i, (p0, v) in enumerate(zip(pts[:-1], segv)):
        vv = max(float(v @ v), 1e-14)
        tt = np.clip(((pos - p0) @ v) / vv, 0, 1)
        q = p0 + tt[:, None] * v
        d2 = np.einsum("ij,ij->i", pos - q, pos - q)
        m = d2 < best_d2
        best_d2[m] = d2[m]
        s_out[m] = (cum[i] + tt[m] * seglen[i]) / L
        pt_out[m] = q[m]
        dir_out[m] = (v / seglen[i])
    dist = np.sqrt(best_d2)
    rel = pos - pt_out
    er = rel / np.maximum(dist, 1e-9)[:, None]
    # mirrored-space angle: flip x of the radial dir for left limbs
    rel_m = rel.copy(); rel_m[:, 0] *= side
    adir_m = dir_out.copy(); adir_m[:, 0] *= side
    # per-vertex frames (vectorised gram-schmidt)
    a = adir_m
    eo = np.tile(np.array([1.0, 0, 0]), (len(pos), 1))
    eo = eo - np.einsum("ij,ij->i", eo, a)[:, None] * a
    eo /= np.maximum(np.linalg.norm(eo, axis=1, keepdims=True), 1e-12)
    ef = np.tile(np.array([0.0, 1.0, 0]), (len(pos), 1))
    ef = ef - np.einsum("ij,ij->i", ef, a)[:, None] * a \
             - np.einsum("ij,ij->i", ef, eo)[:, None] * eo
    ef /= np.maximum(np.linalg.norm(ef, axis=1, keepdims=True), 1e-12)
    reln = rel_m / np.maximum(dist, 1e-9)[:, None]
    phi = np.arctan2(np.einsum("ij,ij->i", reln, ef),
                     np.einsum("ij,ij->i", reln, eo))
    return s_out, dist, phi, er, dir_out

GATE = {"arm": 0.135, "leg": 0.175}

def limb_field(pos, delta, limbs, kind, label):
    """(s, phi) -> (dr, da) kernel field for one limb kind, both sides
    pooled (mirrored). Returns (eval_fn, info)."""
    S_, P_, R_, A_ = [], [], [], []
    for name in (f"{kind}_R", f"{kind}_L"):
        lb = limbs[name]
        s, dist, phi, er, adir = limb_params(pos, lb)
        samp = (dist < GATE[kind]) & (s > -0.04) & (s < 1.05)
        S_.append(s[samp]); P_.append(phi[samp])
        R_.append(np.einsum("ij,ij->i", delta, er)[samp])
        A_.append(np.einsum("ij,ij->i", delta, adir)[samp])
    S = np.concatenate(S_); PH = np.concatenate(P_)
    DR = np.concatenate(R_); DA = np.concatenate(A_)
    # arc length around the limb uses a constant characteristic radius
    # per kind (arm 0.055 m, leg 0.085 m); sigma_A is metres of arc.
    R_CHAR = 0.055 if kind == "arm" else 0.085
    SIG_S, SIG_A = 0.06, 0.035
    def ev(sq, pq, idx=None):
        if idx is None:
            idx = np.arange(len(S))
        o_r = np.zeros(len(sq)); o_a = np.zeros(len(sq))
        for s0 in range(0, len(sq), 800):
            q = slice(s0, s0 + 800)
            ds = (S[idx][:, None] - sq[q][None, :]) / SIG_S
            dp = (PH[idx][:, None] - pq[q][None, :])
            dp = (dp + np.pi) % (2 * np.pi) - np.pi
            da_ = dp * R_CHAR / SIG_A
            w = np.exp(-0.5 * (ds ** 2 + da_ ** 2))
            ws = w.sum(axis=0) + 1e-12
            o_r[q] = (w * DR[idx][:, None]).sum(axis=0) / ws
            o_a[q] = (w * DA[idx][:, None]).sum(axis=0) / ws
        return o_r, o_a
    rng = np.random.default_rng(20261112)
    inf = np.where(np.hypot(DR, DA) > 0.0005)[0]
    perm = rng.permutation(inf); folds = np.array_split(perm, 5)
    errs = np.zeros(len(inf))
    for f in folds:
        tr = np.setdiff1d(perm, f)
        pos_in_inf = np.searchsorted(inf, f)
        pr, pa = ev(S[f], PH[f], idx=tr)
        errs[pos_in_inf] = np.hypot(pr - DR[f], pa - DA[f])
    cv = {k: float(v * 100) for k, v in zip(
        ["p50", "p95", "max"], np.percentile(errs, [50, 95, 100]))}
    info = {"label": label, "kind": kind, "samples": int(len(S)),
            "informative": int(len(inf)), "cv_cm": cv}
    print(f"limb field {label}: {len(S)} samples ({len(inf)} informative), "
          f"CV p50 {cv['p50']:.3f} / p95 {cv['p95']:.3f} / max {cv['max']:.3f} cm")
    return ev, info

# ---------------------------------------------------------------- sources
fm_limbs = extract_limbs(fm_pos, np.ones(len(fm_pos), bool), "fatmales")

def extract_base_positions(data, expect_min_verts):
    """Embedded vertex stream scan, copied from build_belly_v4.py."""
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

hi_pos_u = extract_base_positions(
    (HIMBO_DIR / "HIMBO Body - Vanilla.nif").read_bytes(), 4000)
assert hi_pos_u is not None and len(hi_pos_u) == 9346
hi_pos = hi_pos_u * SK_UNIT_M
_osd = load_osd(str(HIMBO_DIR / "HIMBO Body - Vanilla.osd"))
blocks = {b["name"]: b for b in _osd["blocks"]}
hi_delta_limb = np.zeros_like(hi_pos)
used, missing = {}, []
for slider, val in LIMB_HIMBO.items():
    blk = blocks.get(f"HIMBO - Body{slider}")
    if blk is None:
        missing.append(slider); continue
    D = np.zeros_like(hi_pos)
    D[blk["indices"]] = blk["diffs"] * SK_UNIT_M
    hi_delta_limb += val * D
    used[slider] = val
print(f"HIMBO limb composition: {len(used)} blocks used, missing: {missing}")
hi_limbs = extract_limbs(hi_pos, np.ones(len(hi_pos), bool), "himbo   ")
mh_limbs = extract_limbs(mh_pos, mh_body, "hm08    ")

scales, fields = {}, {}
for kind in ("arm", "leg"):
    scales[f"fm_{kind}"] = mh_limbs[f"{kind}_R"]["length"] / fm_limbs[f"{kind}_R"]["length"]
    scales[f"hi_{kind}"] = mh_limbs[f"{kind}_R"]["length"] / hi_limbs[f"{kind}_R"]["length"]
    fields[f"fm_{kind}"] = limb_field(fm_pos, fm_delta, fm_limbs, kind,
                                      f"fat_males_{kind}")
    fields[f"hi_{kind}"] = limb_field(hi_pos, hi_delta_limb, hi_limbs, kind,
                                      f"himbo_limb_{kind}")
print("limb length scales:", {k: round(v, 3) for k, v in scales.items()})

# alpha calibration on the THIGH band: mean |dr| over leg samples
# s in [0.08, 0.45] (all phi), each source scaled by its length ratio.
def band_mean_dr(pos, delta, limbs, kind, scale):
    vals = []
    for name in (f"{kind}_R", f"{kind}_L"):
        s, dist, phi, er, adir = limb_params(pos, limbs[name])
        m = (dist < GATE[kind]) & (s > 0.08) & (s < 0.45)
        vals.append(np.abs(np.einsum("ij,ij->i", delta, er)[m]) * scale)
    return float(np.concatenate(vals).mean())
fm_thigh = band_mean_dr(fm_pos, fm_delta, fm_limbs, "leg", scales["fm_leg"])
hi_thigh = band_mean_dr(hi_pos, hi_delta_limb, hi_limbs, "leg", scales["hi_leg"])
alpha_limb = float(np.clip(fm_thigh / max(hi_thigh, 1e-9), 0.5, 2.0))
print(f"thigh-band |dr| (scaled): Fat Males {fm_thigh*100:.2f} cm, HIMBO limb "
      f"recipe {hi_thigh*100:.2f} cm -> alpha_limb {alpha_limb:.3f}")

# ------------------------------------------------------- target-side field
def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)
def cosfade(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return 0.5 + 0.5 * np.cos(np.pi * t)

limb_of = {}
for name in ("arm_R", "arm_L", "leg_R", "leg_L"):
    kind = name.split("_")[0]
    lb = mh_limbs[name]
    s, dist, phi, er, adir = limb_params(mh_pos, lb)
    gate = GATE[kind]
    m_soft = np.clip((gate - dist) / 0.02, 0, 1) * mh_body
    reg = (m_soft > 0.003) & (s > -0.05) & (s < 1.07)
    if kind == "arm":
        w_prox = smoothstep(-0.02, 0.16, s)
        # distal fade anchored to the MEASURED wrist (base profile:
        # wrist minimum s~0.72, hand bulge from s~0.78): the r3 run's
        # [0.86, 1.02] window left +5.4 cm on the wrist. Fade now
        # spans the forearm's distal third to mid-hand.
        d_fade = cosfade(0.58, 0.82, s)
    else:
        w_prox = smoothstep(-0.03, 0.13, s)
        # leg: ankle at s~0.84, foot from s~0.88 (base profile);
        # r3's window left +5.5 cm on the ankle. Fade spans the
        # lower shank to the foot.
        d_fade = cosfade(0.70, 0.90, s)
    limb_of[name] = {"s": s, "dist": dist, "phi": phi, "er": er,
                     "adir": adir, "w": m_soft * w_prox,
                     "d_fade": d_fade, "reg": reg}

# Per-limb evaluated (dr, da) on the target, so compose() can rebuild
# the field with the distal fade folded in.
#
# ARM UNDERSIDE EMPHASIS (reference-driven sector correction, R3/L3):
# both learned arm sources under-pool the underside -- HIMBO's arm
# recipe is deltoid/biceps-led (muscle sliders), Fat Males' arm is
# its coarsest region (CV p95 2.80 cm). The reference rule is better
# evidenced than either source's arm phi-distribution, so the blended
# arm dr gets a smooth sector gain toward the world-down direction
# (phi_down, from the arm's own frame), mean-preserved over the arm
# region so total arm volume is ~unchanged: mass MOVES to the
# underside, it is not added. Strength 1.0, disclosed here and in
# GRAVITY_V5.md.
_a = mh_limbs["arm_R"]["pts"][-1] - mh_limbs["arm_R"]["pts"][0]
_a = _a / np.linalg.norm(_a)
_eo = np.array([1.0, 0, 0]); _eo = _eo - (_eo @ _a) * _a
_eo /= np.linalg.norm(_eo)
_ef = np.array([0.0, 1.0, 0]); _ef = _ef - (_ef @ _a) * _a - (_ef @ _eo) * _eo
_ef /= np.linalg.norm(_ef)
_dn = np.array([0.0, 0, -1.0]); _dn = _dn - (_dn @ _a) * _a
_dn /= np.linalg.norm(_dn)
PHI_DOWN = float(np.arctan2(_dn @ _ef, _dn @ _eo))
_arm_phi_pool = np.concatenate(
    [limb_of[n]["phi"][limb_of[n]["reg"]] for n in ("arm_R", "arm_L")])
BUMP = lambda ph: np.maximum(0.0, np.cos(ph - PHI_DOWN)) ** 3
BUMP_MEAN = float(BUMP(_arm_phi_pool).mean())
SECTOR = {"phi_down_rad": PHI_DOWN, "strength": 1.0,
          "bump_mean": BUMP_MEAN}
print(f"arm underside sector: phi_down {PHI_DOWN:.2f} rad, "
      f"bump mean {BUMP_MEAN:.3f}")

limb_eval = {}
for name in ("arm_R", "arm_L", "leg_R", "leg_L"):
    kind = name.split("_")[0]
    lb = mh_limbs[name]
    s, dist, phi, er, adir = limb_params(mh_pos, lb)
    reg = limb_of[name]["reg"]
    fm_ev, _ = fields[f"fm_{kind}"]
    hi_ev, _ = fields[f"hi_{kind}"]
    fdr, fda = fm_ev(s[reg], phi[reg])
    hdr, hda = hi_ev(s[reg], phi[reg])
    dr = 0.5 * (scales[f"fm_{kind}"] * fdr + alpha_limb * scales[f"hi_{kind}"] * hdr)
    da = 0.5 * (scales[f"fm_{kind}"] * fda + alpha_limb * scales[f"hi_{kind}"] * hda)
    if kind == "arm":
        dr = dr * (1.0 + SECTOR["strength"] * (BUMP(phi[reg]) - BUMP_MEAN))
    else:
        # LEG DISTAL SHAPING (reference-driven, L4): the blend adds
        # near-uniform radial down the whole shank (~1.6 cm from the
        # knee to s=0.9), which would tube the calf. L4: calf fat is
        # a thin layer over a muscle-belly form -- gains belong over
        # the gastrocnemius belly (upper shank) and taper hard to the
        # ankle. Factor: 1.0 through the belly (s<=0.68), ramping to
        # 0.55 at s=0.85 and 0.35 at s=1.0 (the distal fade acts on
        # top). Disclosed in GRAVITY_V5.md.
        sg = s[reg]
        shape = np.ones_like(sg)
        m1 = (sg > 0.68) & (sg <= 0.85)
        m2 = sg > 0.85
        shape[m1] = 1.0 - 0.45 * (sg[m1] - 0.68) / 0.17
        shape[m2] = 0.55 - 0.20 * np.clip((sg[m2] - 0.85) / 0.15, 0, 1)
        dr = dr * shape
    limb_eval[name] = {"idx": np.where(reg)[0], "dr": dr, "da": da,
                       "er": er[reg], "adir": adir[reg]}

def compose(inc_scale=1.0):
    Ftar = np.zeros_like(mh_pos)     # target field value (faded)
    Wgt = np.zeros(len(mh_pos))
    for name, lo in limb_of.items():
        ev = limb_eval[name]
        idx = ev["idx"]
        Fv = (ev["dr"][:, None] * ev["er"] + ev["da"][:, None] * ev["adir"]) \
            * lo["d_fade"][idx][:, None]
        w = lo["w"][idx]
        tk = w >= Wgt[idx]
        ii = idx[tk]
        Ftar[ii] = Fv[tk]; Wgt[ii] = w[tk]
    INC = Wgt[:, None] * (Ftar - D4) * inc_scale
    return INC, Ftar, Wgt

INC0, Ftar, Wgt = compose(1.0)
supp = np.linalg.norm(INC0, axis=1) > 0.0002
print(f"limb increment: support {supp.sum()} verts, max |INC| "
      f"{np.linalg.norm(INC0, axis=1).max()*100:.2f} cm")

# graph smoothing of the increment (v4 W-smoothing analogue)
def graph_smooth(V, supp_mask, passes=3, keep=0.35):
    V = V.copy()
    for _ in range(passes):
        sm = Lop @ V
        V = np.where(supp_mask[:, None], (1 - keep) * V + keep * sm, V)
    return V

# ------------------------------------------- fold machinery (all body faces)
Fb = mh_tris[np.array([np.all(f < BODY_END) for f in mh_tris])]
print(f"body faces for fold gate: {len(Fb)}")
BASES = {"raw": mh_pos, "macro": mh_pos_mac}
n0_all = {k: face_normals(p, Fb) for k, p in BASES.items()}
def flips_on(delta, bname):
    nn = face_normals(BASES[bname] + delta, Fb)
    dots = np.einsum("ij,ij->i", n0_all[bname], nn)
    return int((dots < 0).sum()), float(dots.min())

aff_edges = np.array([e for e in edges_all
                      if supp[e[0]] or supp[e[1]]])
elen = np.linalg.norm(mh_pos[aff_edges[:, 0]] - mh_pos[aff_edges[:, 1]], axis=1)
KAPPA = 0.55
def slope_limit(Ds, supp_mask):
    Ds = Ds.copy()
    for it in range(80):
        diff = Ds[aff_edges[:, 0]] - Ds[aff_edges[:, 1]]
        dn = np.linalg.norm(diff, axis=1)
        excess = dn - KAPPA * elen
        if (excess <= 0).all():
            return Ds, it
        corr_ = np.zeros_like(Ds); wgt = np.zeros(len(Ds))
        m_ = excess > 0
        adj = (0.5 * excess[m_] / np.maximum(dn[m_], 1e-12))[:, None] * diff[m_]
        np.add.at(corr_, aff_edges[m_, 0], -adj)
        np.add.at(corr_, aff_edges[m_, 1], adj)
        np.add.at(wgt, aff_edges[m_, 0], 1); np.add.at(wgt, aff_edges[m_, 1], 1)
        Ds += 0.7 * corr_ / np.maximum(wgt, 1)[:, None]
        Ds[~supp_mask] = 0.0
    return Ds, 80

def repair_inc(INC_raw, supp_mask, max_rounds=60):
    att = np.ones(len(INC_raw))
    Av = INC_raw.copy()
    for rnd in range(max_rounds):
        D = D4 + Av
        if flips_on(D, "raw")[0] == 0 and flips_on(D, "macro")[0] == 0:
            return Av, att, True, rnd
        bad = np.zeros(len(Fb), bool)
        for k in BASES:
            nn = face_normals(BASES[k] + D, Fb)
            dots = np.einsum("ij,ij->i", n0_all[k], nn)
            bad |= dots < 0.01
        bad_verts = np.unique(Fb[bad])
        ring = np.unique(np.concatenate([nbrs[v] for v in bad_verts]))
        att[bad_verts] *= 0.82
        att[ring] *= 0.94
        att = np.where(supp_mask, 0.65 * att + 0.35 * (Lop @ att), att)
        att = np.clip(att, 0.10, 1.0)
        Av = att[:, None] * INC_raw
    D = D4 + Av
    ok = flips_on(D, "raw")[0] == 0 and flips_on(D, "macro")[0] == 0
    return Av, att, ok, max_rounds

shipped_inc_scale = None
for s_try in (1.0, 0.85, 0.7, 0.55):
    INCc, _, _ = compose(s_try)
    supp_c = np.linalg.norm(INCc, axis=1) > 0.0002
    INCc = graph_smooth(INCc, supp_c)
    INCc, lim_it = slope_limit(INCc, supp_c)
    pre = (flips_on(D4 + INCc, "raw")[0], flips_on(D4 + INCc, "macro")[0])
    INC_fin, att, converged, rounds = repair_inc(INCc, supp_c)
    print(f"inc scale {s_try}: limiter {lim_it} it, pre-repair flips "
          f"raw/macro {pre}, repair converged {converged} in {rounds} "
          f"rounds, att min {att.min():.2f}")
    if converged:
        shipped_inc_scale = s_try
        INC = INC_fin
        supp = supp_c
        break
assert shipped_inc_scale is not None, "no increment scale repaired clean"
print(f"shipped increment scale: {shipped_inc_scale}")
D5 = D4 + INC
LIN5 = LIN4 + INC

# ------------------------------------------------- inner-thigh contact
def thigh_gap(D):
    """Inner-thigh gap per z-band. Side-correct verts only (x on the
    leg's own side of the midline) and robust percentile extents:
    min/max extents are corrupted by midline perineum verts, which
    sit within BOTH legs' axis gates and fake a 12 cm 'overlap' on
    the undeformed base (caught in the r2 probe, Nov 12, 2026).
    Bands stop 6 cm below the crotch, above the pelvis merge."""
    P = mh_pos + D
    gaps = []
    sR, dR, _, _, _ = limb_params(mh_pos, mh_limbs["leg_R"])
    sL, dL, _, _, _ = limb_params(mh_pos, mh_limbs["leg_L"])
    inR = mh_body & (dR < GATE["leg"]) & (sR > 0.02) & (sR < 0.55) \
        & (mh_pos[:, 0] > 0.008)
    inL = mh_body & (dL < GATE["leg"]) & (sL > 0.02) & (sL < 0.55) \
        & (mh_pos[:, 0] < -0.008)
    for z0 in np.arange(mh_pos[:, 2].min(), mh_crotch - 0.06, 0.02):
        mR = inR & (P[:, 2] >= z0) & (P[:, 2] < z0 + 0.02)
        mL = inL & (P[:, 2] >= z0) & (P[:, 2] < z0 + 0.02)
        if mR.sum() >= 4 and mL.sum() >= 4:
            gaps.append((z0, float(np.percentile(P[mR, 0], 2)
                                   - np.percentile(P[mL, 0], 98))))
    if not gaps:
        return None, []
    gmin = min(gaps, key=lambda t: t[1])
    return gmin, gaps
g0 = thigh_gap(np.zeros_like(mh_pos))
g5 = thigh_gap(D5)
print(f"inner-thigh gap: base min {None if g0[0] is None else round(g0[0][1]*100,2)} cm "
      f"at z {None if g0[0] is None else round(g0[0][0],3)}; "
      f"v5 min {None if g5[0] is None else round(g5[0][1]*100,2)} cm "
      f"at z {None if g5[0] is None else round(g5[0][0],3)}")
CONTACT_CAP = False
if g5[0] is not None and g5[0][1] < -0.002:
    # attenuate the inner sector of the leg increment until gap ~ 0
    print("inner-thigh OVERLAP beyond 2 mm -- applying contact cap (L5/R10)")
    lo_, hi_ = 0.4, 1.0
    for _ in range(14):
        mid = 0.5 * (lo_ + hi_)
        INCc = INC.copy()
        for name in ("leg_R", "leg_L"):
            phi = limb_of[name]["phi"]; s = limb_of[name]["s"]
            inner = mh_body & (np.abs(np.abs(phi) - np.pi) < 0.85) & (s > -0.02) & (s < 0.55)
            INCc[inner] *= mid
        gt = thigh_gap(D4 + INCc)
        if gt[0] is not None and gt[0][1] < -0.001:
            hi_ = mid
        else:
            lo_ = mid
    INCc = INC.copy()
    for name in ("leg_R", "leg_L"):
        phi = limb_of[name]["phi"]; s = limb_of[name]["s"]
        inner = mh_body & (np.abs(np.abs(phi) - np.pi) < 0.85) & (s > -0.02) & (s < 0.55)
        INCc[inner] *= lo_
    if flips_on(D4 + INCc, "raw")[0] == 0 and flips_on(D4 + INCc, "macro")[0] == 0:
        INC = INCc; D5 = D4 + INC; LIN5 = LIN4 + INC
        CONTACT_CAP = True
        g5 = thigh_gap(D5)
        print(f"contact cap shipped at inner-sector scale {lo_:.2f}; "
              f"new min gap {round(g5[0][1]*100,2)} cm")
    else:
        print("contact-capped field failed the fold gate; shipping uncapped "
              "and reporting the overlap honestly")

# ------------------------------------------------------------- fold scans
f05 = 0.5 ** GAMMA
states = {"-1 (linear)": -D5,
          "+0.5 (coupled)": 0.5 * LIN5 + f05 * SAG,
          "+1 (combined)": D5,
          "+1.05 (combined)": 1.05 * D5}
fold_scan = {}
for name_, D in states.items():
    fold_scan[name_] = {b: flips_on(D, b) for b in BASES}
    print(f"fold scan {name_}: raw {fold_scan[name_]['raw']}, "
          f"macro {fold_scan[name_]['macro']}")

def navel_vec(D):
    return {"forward_cm": float(D[navel_mh, 1] * 100),
            "down_cm": float(-D[navel_mh, 2] * 100)}
nav = {"v4_at_+1": navel_vec(D4), "v5_at_+1": navel_vec(D5),
       "v5_at_+0.5_coupled": navel_vec(0.5 * LIN5 + f05 * SAG)}
print("navel:", json.dumps(nav))

# ------------------------------------------------------------- limb metrics
def girth_ellipse(w, d):
    a, b = w / 2, d / 2
    return np.pi * (3 * (a + b) - np.sqrt((3 * a + b) * (a + 3 * b)))

def limb_profile(P, name):
    lb = mh_limbs[name]
    s, dist, phi, er, adir = limb_params(mh_pos, lb)
    reg = mh_body & (dist < GATE[lb["kind"]])
    rows = []
    for s0 in np.arange(-0.02, 1.0, 0.04):
        m = reg & (s >= s0) & (s < s0 + 0.04)
        if m.sum() < 8:
            rows.append((s0 + 0.02, np.nan)); continue
        # local frame at band centre from stored per-vert frames: use er
        # spread -- extents along the two frame dirs of the band's mean vert
        i0 = np.where(m)[0][np.argmin(np.abs(s[m] - (s0 + 0.02)))]
        a_dir = adir[i0]
        eo = np.array([1.0, 0, 0]) * lb["side"]
        eo = eo - (eo @ a_dir) * a_dir; eo /= np.linalg.norm(eo)
        ef = np.cross(a_dir, eo) * lb["side"]
        # NOTE: ef sign canonicalised like limb_params (side * cross)
        q = P[m] - P[m].mean(axis=0)
        w = float(np.percentile(q @ eo, 99) - np.percentile(q @ eo, 1))
        d = float(np.percentile(q @ ef, 99) - np.percentile(q @ ef, 1))
        rows.append((s0 + 0.02, girth_ellipse(w, d)))
    return np.array(rows)

def find_landmark(prof, kind):
    """Elbow/knee as the girth-profile local minimum within +/-0.12 of
    an anatomical prior (elbow s~0.42 of shoulder->wrist, knee s~0.52
    of hip->ankle). Flags whether the minimum is interior to the
    window -- an edge hit means the profile tapers monotonically
    through the joint zone and no local minimum exists to find."""
    ss, gg = prof[:, 0], prof[:, 1]
    prior = 0.46 if kind == "arm" else 0.52
    win_idx = np.where(np.abs(ss - prior) <= 0.12)[0]
    j = win_idx[int(np.nanargmin(gg[win_idx]))]
    interior = bool(win_idx[0] < j < win_idx[-1])
    return float(ss[j]), float(gg[j]), interior

limb_metrics = {}
# Anatomical sample points along s, validated against the base
# profiles in the r2 probe (Nov 12, 2026): arm sections at s<0.28 are
# the shoulder/deltoid merge, not the arm tube; the leg's calf belly
# sits at s~0.60, the wrist at s~0.72 (before the hand bulge), the
# ankle at s~0.84. Mid-thigh is taken halfway hip->knee.
POINTS = {"arm": [("upper_arm_tube", 0.36), ("forearm", 0.64),
                  ("wrist", 0.72)],
          "leg": [("calf_belly", 0.60), ("ankle", 0.84)]}
for name in ("arm_R", "leg_R", "arm_L", "leg_L"):
    kind = name.split("_")[0]
    pb = limb_profile(mh_pos, name)
    p5 = limb_profile(mh_pos + D5, name)
    p4 = limb_profile(mh_pos + D4, name)
    lm_b = find_landmark(pb, kind); lm_5 = find_landmark(p5, kind)
    def gat(prof, s_t):
        return float(prof[np.argmin(np.abs(prof[:, 0] - s_t)), 1])
    # boundary-step ratios: max |dgirth/ds| windowed, deformed vs base
    def grad_ratio(prof_d, prof_b, s_c, hw=0.07):
        def gmax(prof):
            ss, gg = prof[:, 0], prof[:, 1]
            gr = np.abs(np.diff(gg)) / np.diff(ss)
            ctr = 0.5 * (ss[:-1] + ss[1:])
            win = np.abs(ctr - s_c) < hw
            return float(np.nanmax(gr[win])) if win.any() else np.nan
        gb = gmax(prof_b)
        return round(gmax(prof_d) / gb, 2) if gb and gb > 0 else None
    sample = ([("mid_thigh", round(lm_b[0] / 2, 2))] if kind == "leg"
              else []) + POINTS[kind]
    pts = {}
    for label, s_t in sample:
        pts[label] = {"s": s_t,
                      "base_cm": round(gat(pb, s_t) * 100, 1),
                      "v4_cm": round(gat(p4, s_t) * 100, 1),
                      "v5_cm": round(gat(p5, s_t) * 100, 1),
                      "gain_cm": round((gat(p5, s_t) - gat(pb, s_t)) * 100, 2)}
    limb_metrics[name] = {
        "landmark": {"joint": "elbow" if kind == "arm" else "knee",
                     "s_base": lm_b[0], "s_v5": lm_5[0],
                     "girth_base_cm": round(lm_b[1] * 100, 1),
                     "girth_v5_cm": round(lm_5[1] * 100, 1),
                     "gain_cm": round((lm_5[1] - lm_b[1]) * 100, 2),
                     "interior_min_base": lm_b[2],
                     "interior_min_v5": lm_5[2]},
        "points": pts,
        "boundary_step_ratio": {
            "proximal_crossfade": grad_ratio(
                p5, pb, 0.08 if kind == "arm" else 0.15),
            "joint": grad_ratio(p5, pb, lm_b[0])},
    }
    print(f"limb metrics {name}: " + json.dumps(limb_metrics[name]))

# upper-arm pooling (R3/L3), ANATOMICAL sectors: on a posed arm the
# underside is the triceps/postdeltoid side (phi ~ -pi/2 in the limb
# frame), not the world-down direction -- a world-vertical sector
# test is pose-confounded (r2 probe: the back bins carry the field's
# largest radial, +2.1 cm, incl. the named postdeltoid pad).
pool = {}
for name in ("arm_R", "arm_L"):
    lb = mh_limbs[name]
    s, dist, phi, er, adir = limb_params(mh_pos, lb)
    lm_s = limb_metrics[name]["landmark"]["s_base"]
    band = mh_body & (dist < GATE["arm"]) & (s > 0.08) & (s < lm_s - 0.04)
    back = band & (phi > -2.4) & (phi < -0.7)
    front = band & (phi > 0.7) & (phi < 2.4)
    drF = np.einsum("ij,ij->i", Ftar, er)
    dr5 = np.einsum("ij,ij->i", D5, er)
    pool[name] = {
        "field_radial_cm": {
            "back_underside": round(float(drF[back].mean()) * 100, 2),
            "front": round(float(drF[front].mean()) * 100, 2)},
        "total_radial_cm": {
            "back_underside": round(float(dr5[back].mean()) * 100, 2),
            "front": round(float(dr5[front].mean()) * 100, 2)},
        "n_back": int(back.sum()), "n_front": int(front.sum())}
print("underside pooling:", json.dumps(pool))

# ------------------------------------------------- v4 scorecard re-run
def compute_axis_full(pos, gate):
    return compute_axis(pos, gate)
mh_ctr, mh_axis = compute_axis(mh_pos, mh_body)
_h = (mh_pos[:, 2] - mh_crotch) / L_mh
_ax = axis_at(mh_ctr, mh_axis, mh_pos[:, 2])
_rel = mh_pos[:, :2] - _ax
mh_r = np.linalg.norm(_rel, axis=1)
mh_th = np.arctan2(_rel[:, 0], _rel[:, 1])
er_mh = np.stack([np.sin(mh_th), np.cos(mh_th)], axis=1)
torso_gate = mh_body & (mh_r < 0.30)
torso_gate_narrow = mh_body & (mh_r < 0.215)

def torso_profiles(P, gate, step=0.0125):
    zs = np.arange(mh_crotch - 0.05, mh_neck + 0.02, step)
    W = np.full(len(zs), np.nan); Dp = np.full(len(zs), np.nan)
    for i, z in enumerate(zs):
        m = gate & (np.abs(mh_pos[:, 2] - z) < step * 0.75)
        if m.sum() >= 8:
            W[i] = P[m, 0].max() - P[m, 0].min()
            Dp[i] = P[m, 1].max() - P[m, 1].min()
    return zs, W, Dp

def corrected(D):
    out = {}
    drad = np.einsum("ij,ij->i", D[:, :2], er_mh)
    sel = torso_gate & (np.abs(mh_th) < 0.7) & (drad > 0.02)
    out["M2_apron_bottom_above_crotch_cm"] = (
        round(float((mh_pos[sel, 2] + D[sel, 2]).min() - mh_crotch) * 100, 2)
        if sel.any() else None)
    zs, W, Dp = torso_profiles(mh_pos + D, torso_gate_narrow)
    hh = (zs - mh_crotch) / L_mh
    G = girth_ellipse(W, Dp)
    height = float(mh_pos[mh_body, 2].max() - mh_pos[mh_body, 2].min())
    waist_win = (hh > h_star + 0.02) & (hh < h_star + 0.14)
    hip_win = (hh > -0.02) & (hh < 0.14)
    nav_win = (hh > h_star - 0.025) & (hh < h_star + 0.025)
    iw = int(np.nanargmin(np.where(waist_win, G, np.inf)))
    hip_g = float(np.nanmax(G[hip_win]))
    out["M3_waist_girth_narrowest_cm"] = round(float(G[iw]) * 100, 1)
    out["M3_hip_girth_cm"] = round(hip_g * 100, 1)
    out["M3_ratio_narrowest"] = round(float(G[iw]) / hip_g, 3)
    out["M3_navel_girth_cm"] = round(float(np.nanmean(G[nav_win])) * 100, 1)
    out["M3_ratio_navel_level"] = round(float(np.nanmean(G[nav_win])) / hip_g, 3)
    out["M9_waist_height_ratio_narrowest"] = round(float(G[iw]) / height, 3)
    seg = (hh > 0.10) & (hh < 0.52)
    idx = np.where(seg)[0]
    ipk = idx[int(np.nanargmax(W[idx]))]
    above = (hh > hh[ipk] + 0.10) & (hh < hh[ipk] + 0.24)
    out["flank_roll_peak"] = {"h": round(float(hh[ipk]), 3),
                              "width_cm": round(float(W[ipk]) * 100, 1)}
    out["flank_pinch_above_roll_cm"] = round(
        float(W[ipk] - np.nanmin(W[above])) * 100, 1)
    # M1 below-navel share, M5 back, M6 chest (build-script definitions)
    Bm = corr["mh_mask"].astype(np.float64)
    W4 = np.load(WORK / "belly_v4.npz")["torso_weight"]
    front = torso_gate & (np.abs(mh_th) < 0.6) & ((W4 > 0.1) | (Bm > 0.1))
    pos_ = np.clip(drad[front], 0, None)
    below = pos_[_h[front] < h_star].sum(); above_ = pos_[_h[front] >= h_star].sum()
    out["below_share_pct (M1)"] = round(float(below / max(below + above_, 1e-12)) * 100, 1)
    back = torso_gate & (np.abs(mh_th) > 2.5) & (_h > h_star + 0.02) & (_h < h_star + 0.30)
    chestf = torso_gate & (np.abs(mh_th) < 0.8) & (_h > 0.78) & (_h < 0.92)
    out["back_radial_cm (M5)"] = round(float(drad[back].mean()) * 100, 2)
    out["chest_front_radial_cm (M6)"] = round(float(drad[chestf].mean()) * 100, 2)
    return out

c4 = corrected(D4); c5 = corrected(D5)
print("corrected v4:", json.dumps(c4))
print("corrected v5:", json.dumps(c5))
qa4 = json.loads((WORK / "qa_numbers_v4.json").read_text())
m4_first = {"v3": qa4["metrics_v3"], "v4": qa4["metrics_v4"]}

# ---------------------------------------------------------------- targets
def fmt(v):
    s_ = f"{abs(v):.3f}".rstrip("0")
    if s_.endswith("."): s_ += "0"
    if s_ in ("", "0."): s_ = "0"
    return ("-" + s_) if v < 0 else s_
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
NOTE5 = ("Provenance: omniversal slider body.belly.protrusion v5 (whole-"
         "body adiposity: v4 whole-torso system extended into the limbs), "
         "instance makehuman_hm08. Combined field at w=+1: v4 (torso) plus "
         "the limb crossfade increment (Fat Males + HIMBO Chonky limb "
         "recipe, limb-local (s, phi) kernel transfer). Study-only, "
         "internal - not a CC0 MakeHuman asset. See GRAVITY_V5.md.")
NOTEI = ("Provenance: LIMB component of body.belly.protrusion v5 "
         "(= combined v5 - combined v4). A crossfade increment, not a "
         "standalone field: apply on top of the v4 combined target. "
         "Study-only, internal.")
n_v5 = write_target(OUT / "body.belly.protrusion_v5.target", D5, NOTE5)
n_inc = write_target(OUT / "body.belly.protrusion_limb_v5.target", INC, NOTEI)
print(f"targets written: v5 combined {n_v5} moved verts, limb component {n_inc}")

np.savez(WORK / "belly_v5.npz", delta_v5_canonical_m=D5,
         lin_v5_canonical_m=LIN5, sag_v5_canonical_m=SAG,
         limb_increment_canonical_m=INC, limb_field_canonical_m=Ftar,
         limb_weight=Wgt, alpha_limb=alpha_limb,
         shipped_inc_scale=shipped_inc_scale, scales=scales,
         contact_cap=CONTACT_CAP, gamma=GAMMA,
         navel_mh=navel_mh)
qa5 = {
    "model": {"gamma_coupling": GAMMA,
              "shipped_inc_scale": shipped_inc_scale,
              "alpha_limb": alpha_limb,
              "thigh_band_dr_cm": {"fat_males": fm_thigh * 100,
                                   "himbo_limb": hi_thigh * 100},
              "scales": scales,
              "himbo_limb_recipe_used": used,
              "himbo_limb_recipe_missing": missing,
              "fields": {k: v[1] for k, v in fields.items()},
              "attenuation": {"min": float(att.min()),
                              "verts_under_0.99": int((att < 0.99).sum()),
                              "rounds": rounds},
              "contact_cap_applied": CONTACT_CAP,
              "leg_distal_shaping": "dr x1.0 to s=0.68, ->0.55 at "
                                    "s=0.85, ->0.35 at s=1.0 (L4)"},
    "navel": nav,
    "fold_scan": {k: {b: {"flips": v[b][0], "min_dot": v[b][1]}
                      for b in BASES} for k, v in fold_scan.items()},
    "body_faces_checked": int(len(Fb)),
    "limb_metrics": limb_metrics,
    "underside_pooling": pool,
    "inner_thigh_gap": {
        "base_min_cm": None if g0[0] is None else round(g0[0][1] * 100, 2),
        "v5_min_cm": None if g5[0] is None else round(g5[0][1] * 100, 2),
        "v5_min_at_z_m": None if g5[0] is None else round(g5[0][0], 3),
        "base_top_band_cm": None if not g0[1] else round(g0[1][-1][1] * 100, 2),
        "v5_top_band_cm": None if not g5[1] else round(g5[1][-1][1] * 100, 2)},
    "arm_sector_correction": SECTOR,
    "corrected_metrics_v4": c4, "corrected_metrics_v5": c5,
    "first_pass_metrics_v4_for_reference": m4_first,
    "moved_verts": {"v5_combined": n_v5, "limb_component": n_inc},
}
(WORK / "qa_numbers_v5.json").write_text(json.dumps(qa5, indent=1))
print("QA v5 saved")
