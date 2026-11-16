#!/usr/bin/env python3
"""GEOMETRY VALIDATION of the Muscle x Tissue coupling model
(MUSCLE_TISSUE_MODEL.md section 9, item 1 + item 7b) for AnthroForge.

The model doc's vector-layer numbers were evaluator truths, not mesh
truths. This build settles them on hm08 geometry:

  1. GACHIDEBU (muscle 0.80, tissue level 0.945, distribution 0 --
     the section 7.1 worked example): definition submergence measured
     on the surface (trap valleys = yoke class, V line = abdomen
     class) at raw vs evaluator-effective values over the full tissue
     build; neck show-through applied as a separable boost and
     measured; the circumferential WRAP audited per band against the
     coupling's emitted factors (stiff-sides floor 0.40 enforced).
  2. PEAR (-1, tissue-driven) and BIG-CHEST (+1) at the section 7.4
     levels: the distribution factors weight the muscle field (0.6
     strength factors) and the v5 adiposity system (full-strength
     factors) per macro region; girth ratios at chest/waist/hip must
     move in the axis's directions. The PECS CREASE interaction (the
     model's test-asserted distribution x attenuation effect) is
     measured on mesh at the test's own conditions (level 0.6,
     muscle 1.0, raw crease 0.80).

Composition notes (documented, not hidden):
  * Gachidebu tissue = the shipped strongman tissue field scaled by
    the level ratio 0.945/0.7575 (uniform: distribution is 0 at both
    cells, so every region scales by the level ratio -- the model's
    own regional formula). The PowerBelly core/drape routing is a
    vector-layer output; the shipped tissue's belly (v4 system at
    tau=0.60) cannot be re-routed post-hoc because its pre-belly
    kernel component was not saved -- the belly therefore scales with
    the layer, and M4 is graded as the check on that choice.
  * Show-through: PecsSize/TorsoMass boosts clamp at 1.0 in the
    evaluator (their excess is a warning, per the model) and their
    fields sit at recipe 1.00 inside body.muscle, so no geometry
    change is possible or claimed. ArmsDelts (0.90 -> 0.989) is
    inseparable from the composed muscle field post-hoc. NeckMass IS
    separable (it was authored as a gated Weight-block transfer), so
    the neck boost is applied exactly: embedded neck field x
    (0.9574/0.90 - 1).
  * The shipped gachidebu target carries NO added definition fields:
    its definition content is the strongman tissue recipe's own
    (incl. TrapsValleys 0.30). Definition is validated on dedicated
    measurement builds over the same substrate, as dip-depth
    INCREMENTS over the identical build without the added field (so
    the tissue recipe's internal valleys cancel out of the contrast).
  * Distribution characters' tissue substrate is the v5 adiposity
    system (D5(w) = w*LIN5 + w^2*SAG, gamma=2 coupling), NOT the bara
    tissue field: the v5 system is the library's whole-body fat
    system and its limb component is the one the distribution
    weighting needs. The evaluator's level is identified with the v5
    slider value w [E identification: both are 0..1 adiposity
    fractions; v5's +1 anchor sits at level ~0.95 territory].
    Muscle geometry amplitude (the composed strongman field) is held
    constant across the pair so the axis is the only muscle-side
    variable; the evaluator's muscle value enters gate/attenuation.

Machinery (kernel transfer, region labeller, slice loops, grade,
profiles, fold repair, target writer) is copied verbatim from
build_bara.py / finalize_v4.py, the proofs' own convention.
QA: machinery self-check first (the shipped strongman build must
reproduce BARA_PROOF's M4/M1/girths); fold gate 0 flips on raw AND
macro bases for every shipped build; zone residuals reported per
macro zone. PROVENANCE: study-only, as the other proofs.
"""
import json
import sys
import zipfile
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
OUT = HERE.parent                      # bara-proof/
V2 = OUT.parent                        # anthroforge-v2/
FP = V2 / "first-proof"
WORK = OUT / "work"
APP = Path.home() / "workspace/anthroforge-app"
LEARNED = Path.home() / "workspace/character_assets/learned"
HIMBO_DIR = (Path.home() / "workspace/character_assets/_himbo_work/"
             "CalienteTools/BodySlide/ShapeData/HIMBO")
sys.path.insert(0, str(LEARNED / "tools"))
sys.path.insert(0, str(APP))
from osdparse import load_osd  # noqa: E402
from core.sliders import (CouplingRegistry, SliderRegistry,  # noqa: E402
                          evaluate_effective_vector)

MPFB_ZIP = Path.home() / "workspace/stick-figure-avatar/photoreal/tools/mpfb2.zip"
DM_M = 0.1
SK = 0.01428
BODY_END = 13380
KAPPA = 0.55

R = {"evaluator": {}, "selfcheck": {}, "gachidebu": {}, "pear": {},
     "bigchest": {}, "crease": {}, "folds": {}, "zone_residuals": {}}


def sstep(x, a, b):
    t = np.clip((np.asarray(x, float) - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


# ---------------------------------------------------------------- loads
corr = np.load(FP / "work/correspondence.npz")
B_CORE = corr["mh_mask"].astype(np.float64)
h_star = float(corr["h_star"])
mh_crotch, mh_neck = [float(x) for x in corr["mh_landmarks"]]
navel_mh = int(corr["navel_mh"])
mh_tris = corr["mh_tris"]
L_mh = mh_neck - mh_crotch

with zipfile.ZipFile(MPFB_ZIP) as z:
    _lines = z.read("mpfb/data/3dobjs/base.obj").decode().splitlines()
_obj = np.array([[float(x) for x in l.split()[1:4]]
                 for l in _lines if l.startswith("v ")])
mh_pos = np.stack([_obj[:, 0], _obj[:, 2], _obj[:, 1]], axis=1) * DM_M
_mac = np.load(FP / "work/mh_macro_base.npz")["pos_canonical_m"]
mh_pos_mac = mh_pos.copy()
_mb = _mac.copy()
for _ax in range(3):
    r0, r1 = mh_pos[:BODY_END, _ax].min(), mh_pos[:BODY_END, _ax].max()
    m0, m1 = _mb[:, _ax].min(), _mb[:, _ax].max()
    _mb[:, _ax] = r0 + (_mb[:, _ax] - m0) * (r1 - r0) / (m1 - m0)
mh_pos_mac[:len(_mb)] = _mb
NB = len(mh_pos)
FACES_B = mh_tris[np.all(mh_tris < BODY_END, axis=1)]
BODY_MASK = np.zeros(NB, bool)
BODY_MASK[:BODY_END] = True

_bf = np.load(OUT / "work/bara_fields.npz")
M_F = _bf["muscle_core_canonical_m"].astype(np.float64)
W_F = _bf["chest_width_canonical_m"].astype(np.float64)
T_F = _bf["tissue_canonical_m"].astype(np.float64)
W3 = _bf["region_weights"].astype(np.float64)
ATT_M = _bf["att_muscle"].astype(np.float64)
TAU_BAR = float(_bf["tau"])

_v5 = np.load(FP / "work/belly_v5.npz", allow_pickle=True)
LIN5 = _v5["lin_v5_canonical_m"].astype(np.float64)
SAG5 = _v5["sag_v5_canonical_m"].astype(np.float64)
assert np.abs(_v5["delta_v5_canonical_m"] - (LIN5 + SAG5)).max() < 1e-9


def d5(w):
    """v5 adiposity system at slider w (gamma=2 sag coupling)."""
    return w * LIN5 + (w ** 2) * SAG5


print(f"hm08: {NB} verts, L={L_mh:.4f} m, h*={h_star:.4f}, "
      f"body faces {len(FACES_B)}")


def extract_base_positions(data, expect_min_verts):
    """Verbatim from build_bara.py (32-byte vertex stream scan)."""
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
assert hi_pos_u is not None and len(hi_pos_u) == 9346, "HIMBO base extract"
hi_blocks = {b["name"]: b for b in
             load_osd(str(HIMBO_DIR / "HIMBO Body - Vanilla.osd"))["blocks"]}
NH = len(hi_pos_u)


def hi_diff(name):
    blk = hi_blocks.get(f"HIMBO - Body{name}")
    if blk is None:
        return np.zeros((NH, 3))
    d = np.zeros((NH, 3))
    d[blk["indices"]] = blk["diffs"]
    return d


# ------------------------------------------------------- shared geometry
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
        axis[:, c] = np.convolve(np.pad(axis[:, c], 2, mode="edge"),
                                 k, "valid")
    return ctr, axis


def axis_at(ctr, axis, hgt):
    return np.stack([np.interp(hgt, ctr, axis[:, 0]),
                     np.interp(hgt, ctr, axis[:, 1])], axis=1)


def crotch_of(pos, gate, mid_hw, slab_hw):
    mid = gate & (np.abs(pos[:, 0]) < mid_hw) & (np.abs(pos[:, 1]) < slab_hw)
    return pos[mid, 2].min()


def neck_base(pos, ctr, axis, crotch, label):
    ax = axis_at(ctr, axis, pos[:, 2])
    r = np.linalg.norm(pos[:, :2] - ax, axis=1)
    gated = r < 0.23
    bands = np.linspace(crotch, pos[:, 2].max(), 160)
    C = 0.5 * (bands[:-1] + bands[1:])
    Wd = np.zeros(len(C))
    for i, (a, b) in enumerate(zip(bands[:-1], bands[1:])):
        m = gated & (pos[:, 2] >= a) & (pos[:, 2] < b)
        if m.sum() >= 4:
            Wd[i] = np.percentile(pos[m, 0], 99) \
                - np.percentile(pos[m, 0], 1)
    above = C > crotch + 0.20 * (C[-1] - crotch)
    chest_i = int(np.argmax(np.where(above, Wd, 0)))
    neck, run = None, 0
    for i in range(chest_i + 1, len(Wd)):
        if 0 < Wd[i] < 0.55 * Wd[chest_i]:
            run += 1
            if run >= 3:
                neck = C[i - 2]
                break
        else:
            run = 0
    return neck


def torso_params(pos, crotch=None, neck=None, label="mesh"):
    gate = np.ones(len(pos), bool)
    ctr, axis = compute_axis(pos, gate)
    if crotch is None:
        crotch = crotch_of(pos, gate, 0.030, 0.060)
    if neck is None:
        neck = neck_base(pos, ctr, axis, crotch, label)
    ax = axis_at(ctr, axis, pos[:, 2])
    rel = pos[:, :2] - ax
    r = np.linalg.norm(rel, axis=1)
    theta = np.arctan2(rel[:, 0], rel[:, 1])
    h = (pos[:, 2] - crotch) / (neck - crotch)
    return h, theta, r, ax, crotch, neck, neck - crotch


def pair_field(sa, sb, v1, v2, qa, qb, sig_a, sig_b):
    out1 = np.zeros(len(qa))
    out2 = np.zeros(len(qa))
    for s0 in range(0, len(qa), 800):
        q = slice(s0, s0 + 800)
        da = (sa[:, None] - qa[q][None, :]) / sig_a
        db = (sb[:, None] - qb[q][None, :]) / sig_b
        w = np.exp(-0.5 * (da ** 2 + db ** 2))
        ws = w.sum(axis=0) + 1e-12
        out1[q] = (w * v1[:, None]).sum(axis=0) / ws
        out2[q] = (w * v2[:, None]).sum(axis=0) / ws
    return out1, out2


def pair_cv(sa, sb, v1, v2, sig_a, sig_b):
    inf = np.where(np.hypot(v1, v2) > 0.0005)[0]
    if len(inf) < 40:
        return None
    rng = np.random.default_rng(20261112)
    perm = rng.permutation(inf)
    folds = np.array_split(perm, 5)
    errs = np.zeros(len(inf))
    for f in folds:
        tr = np.setdiff1d(perm, f)
        pr, pz = pair_field(sa[tr], sb[tr], v1[tr], v2[tr],
                            sa[f], sb[f], sig_a, sig_b)
        errs[np.searchsorted(inf, f)] = np.hypot(pr - v1[f], pz - v2[f])
    e = errs * 100.0
    return {"n": int(len(e)), "median_cm": float(np.median(e)),
            "p95_cm": float(np.percentile(e, 95))}


# ------------------------------------------------- region labeller (any mesh)
def label_mesh(pos, crotch, neck, body_mask=None):
    """Verbatim from build_bara.py."""
    if body_mask is None:
        body_mask = np.ones(len(pos), bool)
    z = pos[:, 2]
    ctr, axis = compute_axis(pos, np.ones(len(pos), bool))
    ax = np.stack([np.interp(z, ctr, axis[:, 0]),
                   np.interp(z, ctr, axis[:, 1])], axis=1)
    rel = pos[:, :2] - ax
    r = np.hypot(rel[:, 0], rel[:, 1])
    edges = np.arange(z.min() - 0.005, z.max() + 0.011, 0.01)
    prof = np.full(len(edges) - 1, np.nan)
    for i, (a, b) in enumerate(zip(edges[:-1], edges[1:])):
        m = (z >= a) & (z < b) & (r < 0.23)
        if m.sum() > 8:
            prof[i] = np.percentile(r[m], 92)
    zc = 0.5 * (edges[:-1] + edges[1:])
    ok = ~np.isnan(prof)
    r92 = np.interp(z, zc[ok], prof[ok])
    side = np.sign(rel[:, 0])
    arm = (r > r92 + 0.010) & (z > crotch - 0.02) & (z < neck + 0.05) \
        & (side != 0) & (np.abs(rel[:, 0]) > 0.7 * r) & body_mask
    leg = (z < crotch - 0.008) & ~arm & body_mask
    torso = ~arm & ~leg
    lab = {"arm": arm, "leg": leg, "torso": torso, "side": side,
           "ax": ax, "r": r, "rel": rel}
    lm = {}
    for sgn, sname in ((1.0, "R"), (-1.0, "L")):
        am = arm & (side == sgn)
        if am.sum() > 60:
            P = pos[am]
            c = P.mean(axis=0)
            _, _, vt = np.linalg.svd(P - c, full_matrices=False)
            a = vt[0]
            s = (P - c) @ a
            for sgn_a in (1.0,):
                e1 = P[s > np.percentile(s, 92)]
                e0 = P[s < np.percentile(s, 8)]
                d1 = np.mean(np.abs(e1[:, 0] - np.interp(
                    e1[:, 2], ctr, axis[:, 0])))
                d0 = np.mean(np.abs(e0[:, 0] - np.interp(
                    e0[:, 2], ctr, axis[:, 0])))
                if d0 > d1:
                    a, s = -a, -s
            u = s - s.min()
            span = u.max()
            nb = 28
            bins = np.linspace(0, span, nb + 1)
            rad = np.full(nb, np.nan)
            for i in range(nb):
                m = (u >= bins[i]) & (u < bins[i + 1])
                if m.sum() > 3:
                    rad[i] = np.mean(np.linalg.norm(
                        (P[m] - c) - np.outer(s[m], a), axis=1))
            okb = ~np.isnan(rad)
            rad = np.interp(np.arange(nb), np.where(okb)[0], rad[okb])
            bc = 0.5 * (bins[:-1] + bins[1:])
            sm_r = np.convolve(rad, np.ones(3) / 3, mode="same")
            loc_min = [i for i in range(1, nb - 1)
                       if sm_r[i] <= sm_r[i - 1] and sm_r[i] <= sm_r[i + 1]
                       and bc[i] > 0.20 * span]
            if loc_min:
                ei = loc_min[0]
                elb_u = bc[ei]
                cand = [i for i in loc_min
                        if bc[i] > elb_u + 0.18 * span
                        and bc[i] < 0.96 * span]
                wri_u = bc[min(cand, key=lambda i: sm_r[i])] \
                    if cand else bc[min(loc_min[-1], nb - 1)]
            else:
                elo = bc[(bc > 0.32 * span) & (bc < 0.68 * span)]
                elb_u = elo[np.argmin(rad[(bc > 0.32 * span)
                                          & (bc < 0.68 * span)])]
                wlo = bc[(bc > 0.74 * span) & (bc < 0.95 * span)]
                wri_u = wlo[np.argmin(rad[(bc > 0.74 * span)
                                          & (bc < 0.95 * span)])]

            def cent(uc, hw):
                m = np.abs(u - uc) < hw
                return P[m].mean(axis=0) if m.sum() > 2 else c + a * uc
            lm[f"arm{sname}"] = {
                "S": cent(0.03 * span, 0.05 * span),
                "E": cent(elb_u, 0.04 * span),
                "W": cent(wri_u, 0.035 * span),
                "span": float(span), "verts": np.where(am)[0]}
        lg = leg & (side == sgn)
        if lg.sum() > 60:
            P = pos[lg]
            top = P[P[:, 2] > crotch - 0.09]
            hip_off = np.median(np.abs(top[:, 0] - np.interp(
                top[:, 2], ctr, axis[:, 0]))) if len(top) else 0.09
            H = np.array([np.interp(crotch, ctr, axis[:, 0]) + sgn * hip_off,
                          np.interp(crotch, ctr, axis[:, 1]), crotch + 0.005])
            low = P[P[:, 2] <= np.percentile(P[:, 2], 3)]
            A = low.mean(axis=0)
            hv = A - H
            hl = np.linalg.norm(hv)
            ah = hv / hl
            t = (P - H) @ ah
            rad = np.linalg.norm((P - H) - np.outer(t, ah), axis=1)
            nb = 24
            bins = np.linspace(0, hl, nb + 1)
            prof2 = np.full(nb, np.nan)
            for i in range(nb):
                m = (t >= bins[i]) & (t < bins[i + 1])
                if m.sum() > 3:
                    prof2[i] = np.mean(rad[m])
            okb = ~np.isnan(prof2)
            prof2 = np.interp(np.arange(nb), np.where(okb)[0], prof2[okb])
            bc = 0.5 * (bins[:-1] + bins[1:])
            klo = bc[(bc > 0.35 * hl) & (bc < 0.65 * hl)]
            knee_t = klo[np.argmin(prof2[(bc > 0.35 * hl)
                                         & (bc < 0.65 * hl)])]
            K = P[np.abs(t - knee_t) < 0.04 * hl].mean(axis=0)
            lm[f"leg{sname}"] = {"H": H, "K": K, "A": A,
                                 "span": float(hl), "verts": np.where(lg)[0]}
    lab["lm"] = lm
    return lab


def seg_params(pos, A, B, ref):
    ab = B - A
    L = np.linalg.norm(ab)
    ah = ab / L
    t = ((pos - A) @ ah) / L
    rv = (pos - A) - np.outer((pos - A) @ ah, ah)
    rl = np.linalg.norm(rv, axis=1)
    e1 = ref - (ref @ ah) * ah
    e1 = e1 / np.linalg.norm(e1)
    e2 = np.cross(ah, e1)
    phi = np.arctan2(rv @ e2, rv @ e1)
    rdir = np.where(rl[:, None] > 1e-9, rv / np.maximum(rl, 1e-9)[:, None],
                    e1[None, :])
    return t, phi, rdir, ah, L, rl


REF_ARM = np.array([0.0, 0.0, 1.0])
REF_LEG = np.array([0.0, 1.0, 0.0])


def chain_of(lab, kind, sname):
    lm = lab["lm"].get(f"{kind}{sname}")
    if lm is None:
        return None
    if kind == "arm":
        return [(lm["S"], lm["E"]), (lm["E"], lm["W"])], REF_ARM, lm
    return [(lm["H"], lm["K"]), (lm["K"], lm["A"])], REF_LEG, lm


# ------------------------------------------------------------- slice loops
def plane_loops(pos, n, p0):
    n = n / np.linalg.norm(n)
    d = (pos - p0) @ n
    F = FACES_B
    dv = d[F]
    segs = []
    for e in ((0, 1), (1, 2), (2, 0)):
        a, b = dv[:, e[0]], dv[:, e[1]]
        cross = (a >= 0) != (b >= 0)
        if not cross.any():
            continue
        fa, fb = F[cross, e[0]], F[cross, e[1]]
        t = a[cross] / (a[cross] - b[cross])
        pts = pos[fa] + (pos[fb] - pos[fa]) * t[:, None]
        fid = np.where(cross)[0]
        segs.append((fid, pts))
    per_face = {}
    for fid, pts in segs:
        for i, f in enumerate(fid):
            per_face.setdefault(int(f), []).append(pts[i])
    raw = [np.stack(v) for v in per_face.values() if len(v) == 2]
    if not raw:
        return []
    S = np.stack([s[0] for s in raw])
    E = np.stack([s[1] for s in raw])

    def key(p):
        return (round(float(p[0]), 5), round(float(p[1]), 5),
                round(float(p[2]), 5))
    from collections import defaultdict
    at = defaultdict(list)
    for i in range(len(raw)):
        at[key(S[i])].append((i, 0))
        at[key(E[i])].append((i, 1))
    used = np.zeros(len(raw), bool)
    loops = []
    for i0 in range(len(raw)):
        if used[i0]:
            continue
        used[i0] = True
        loop = [S[i0], E[i0]]
        cur = key(E[i0])
        for _ in range(len(raw) + 2):
            nxt = None
            for (j, end) in at.get(cur, []):
                if not used[j]:
                    nxt = (j, end)
                    break
            if nxt is None:
                break
            j, end = nxt
            used[j] = True
            p = E[j] if end == 0 else S[j]
            loop.append(p)
            cur = key(p)
            if cur == key(loop[0]):
                break
        if len(loop) >= 4:
            loops.append(np.array(loop[:-1]) if
                         np.allclose(loop[-1], loop[0]) else
                         np.array(loop))
    return loops


def loop_perim(lp):
    q = np.roll(lp, -1, axis=0)
    return float(np.linalg.norm(q - lp, axis=1).sum())


def best_loop(pos, n, p0, near_axis=True, max_extent=None):
    loops = plane_loops(pos, n, p0)
    if not loops:
        return None

    def ok(lp):
        c = lp.mean(axis=0)
        if near_axis and abs(c[0]) > 0.09:
            return False
        if max_extent and (lp[:, 0].max() - lp[:, 0].min()) > max_extent:
            return False
        return True
    cand = [lp for lp in loops if ok(lp)]
    if not cand:
        cand = loops
    return max(cand, key=loop_perim)


def mesh_volume(pos):
    F = FACES_B
    v0, v1, v2 = pos[F[:, 0]], pos[F[:, 1]], pos[F[:, 2]]
    return abs(float(np.einsum("ij,ij->i", v0,
                               np.cross(v1, v2)).sum() / 6.0))


# grade(): verbatim from build_bara.py (BARA_LESSONS scorecard)
def grade(pos, lmts):
    Z = np.array([0.0, 0.0, 1.0])
    body = pos[:BODY_END]
    crown = body[:, 2].max()
    sole = body[:, 2].min()
    height = crown - sole
    neck_lp = best_loop(pos, Z, np.array([0, 0, mh_neck + 0.045]))
    neck_g = loop_perim(neck_lp)
    neck_w = float(neck_lp[:, 0].max() - neck_lp[:, 0].min())
    widths = []
    for zz in np.arange(mh_neck + 0.06, crown - 0.002, 0.004):
        lp = best_loop(pos, Z, np.array([0, 0, zz]), max_extent=0.30)
        if lp is not None and loop_perim(lp) > 0.04:
            widths.append((zz, float(lp[:, 0].max() - lp[:, 0].min())))
    head_w = max(w for _, w in widths)
    jaw_win = [(zz, w) for zz, w in widths if zz < mh_neck + 0.17]
    jaw_z = min(jaw_win, key=lambda t: t[1])[0]
    chin_z = jaw_z - 0.02
    head_h = crown - chin_z
    z_chest = mh_crotch + 0.85 * L_mh
    chest_lp = best_loop(pos, Z, np.array([0, 0, z_chest]))
    chest_g = loop_perim(chest_lp)
    chest_w = float(chest_lp[:, 0].max() - chest_lp[:, 0].min())
    chest_d = float(chest_lp[:, 1].max() - chest_lp[:, 1].min())
    z_waist = float(mh_pos_mac[navel_mh, 2])
    waist_lp = best_loop(pos, Z, np.array([0, 0, z_waist]))
    waist_g = loop_perim(waist_lp)
    waist_w = float(waist_lp[:, 0].max() - waist_lp[:, 0].min())
    waist_d = float(waist_lp[:, 1].max() - waist_lp[:, 1].min())
    band = (body[:, 2] > mh_neck - 0.17) & (body[:, 2] < mh_neck - 0.02)
    delt_span = float(body[band, 0].max() - body[band, 0].min())
    _h = globals().get("h_mh")
    sil = body[(_h[:BODY_END] <= 1.16)] if _h is not None else body
    xs = np.arange(0.0, 0.30, 0.004)
    ztop = np.full(len(xs), np.nan)
    for i, x0 in enumerate(xs):
        m = (sil[:, 0] >= x0) & (sil[:, 0] < x0 + 0.004)
        if m.sum() > 2:
            ztop[i] = sil[m, 2].max()
    ok = ~np.isnan(ztop)
    ztop = np.interp(xs, xs[ok], ztop[ok])
    neck_half = neck_w / 2
    fx = (xs > 0.10) & (xs < delt_span / 2 - 0.020)
    if fx.sum() > 4:
        fit = np.polyfit(xs[fx], ztop[fx], 1)
        trap_angle = float(np.degrees(np.arctan(abs(fit[0]))))
    else:
        trap_angle = float("nan")
    trap_at_neck = float(np.interp(head_w / 2 + 0.03, xs, ztop))
    visible_neck = chin_z - trap_at_neck
    ua_gs, fa_gs = [], []
    for sname in ("R", "L"):
        lm = lmts["lm"].get(f"arm{sname}")
        if not lm:
            continue
        S_, E_, W_ = lm["S"], lm["E"], lm["W"]
        for A, Bv, ts, acc in ((S_, E_, (0.20, 0.35, 0.50, 0.65), ua_gs),
                               (E_, W_, (0.15, 0.30, 0.45, 0.60), fa_gs)):
            n = (Bv - A) / np.linalg.norm(Bv - A)
            best = 0.0
            for t in ts:
                P0 = A + t * (Bv - A)
                loops = [lp for lp in plane_loops(pos, n, P0)
                         if loop_perim(lp) > 0.05]
                if loops:
                    lp = min(loops, key=lambda l:
                             np.linalg.norm(l.mean(axis=0) - P0))
                    best = max(best, loop_perim(lp))
            if best > 0:
                acc.append(best)
    ua_g = float(np.mean(ua_gs))
    fa_g = float(np.mean(fa_gs))
    loops = plane_loops(pos, Z, np.array([0, 0, mh_crotch - 0.10]))
    th = [loop_perim(lp) for lp in loops
          if abs(lp.mean(axis=0)[0]) > 0.03 and loop_perim(lp) > 0.15]
    thigh_g = float(np.mean(th)) if th else float("nan")
    knee_z = min(lm["K"][2] for lm in
                 (lmts["lm"].get("legR"), lmts["lm"].get("legL")) if lm)
    calf = {}
    for zz in np.arange(knee_z - 0.17, knee_z - 0.04, 0.008):
        for lp in plane_loops(pos, Z, np.array([0, 0, zz])):
            cx = lp.mean(axis=0)[0]
            if abs(cx) > 0.03 and loop_perim(lp) > 0.08:
                s = "R" if cx > 0 else "L"
                calf[s] = max(calf.get(s, 0.0), loop_perim(lp))
    calf_g = float(np.mean(list(calf.values()))) if calf else float("nan")
    return {
        "height_m": height, "volume_L": mesh_volume(pos) * 1000.0,
        "neck_g": neck_g, "neck_w": neck_w, "head_w": head_w,
        "head_h": head_h, "chin_z": chin_z, "chest_g": chest_g,
        "chest_w": chest_w, "waist_w": waist_w,
        "waist_g": waist_g, "chest_d": chest_d, "waist_d": waist_d,
        "delt_span": delt_span, "trap_angle": trap_angle,
        "visible_neck": visible_neck, "ua_g": ua_g, "fa_g": fa_g,
        "thigh_g": thigh_g, "calf_g": calf_g,
        "M1_neckW_headW": neck_w / head_w,
        "M2_neck_arm": neck_g / ua_g, "M2_neck_calf": neck_g / calf_g,
        "M2_arm_calf": ua_g / calf_g,
        "M3_fa_arm": fa_g / ua_g,
        "M4_chest_waist": chest_g / waist_g,
        "M5_depth_ratio": chest_d / waist_d,
        "M6_trap_deg": trap_angle,
        "M7_vis_neck_ratio": visible_neck / head_h,
        "M8_span_headW": delt_span / head_w,
        "M11_thigh_waist": thigh_g / waist_g,
        "M12_heads_tall": height / head_h,
    }


# profiles girths (v4 method, build_bara girths + hip window)
def girths(pos):
    h, th, r, ax, _, _, _ = torso_params(pos, mh_crotch, mh_neck, "def")
    edges = np.arange(0.30, 1.001, 0.02)
    bands = []
    for a, b in zip(edges[:-1], edges[1:]):
        m = (h >= a) & (h < b)
        g30 = g215 = None
        if m.sum() > 20:
            px = pos[m, 0] - ax[m, 0]
            py = pos[m, 1] - ax[m, 1]
            rr = np.hypot(px, py)
            for gate, key in ((0.30, "g30"), (0.215, "g215")):
                mm = rr < gate
                if mm.sum() > 12:
                    A = (px[mm].max() - px[mm].min()) / 2
                    Bv = (py[mm].max() - py[mm].min()) / 2
                    g = np.pi * (3 * (A + Bv) - np.sqrt(
                        (3 * A + Bv) * (A + 3 * Bv)))
                    if key == "g30":
                        g30 = g
                    else:
                        g215 = g
        bands.append((0.5 * (a + b), g30, g215))
    chest = np.mean([g for hh, g, _ in bands
                     if g and 0.80 <= hh <= 0.90])
    nav = [g2 for hh, _, g2 in bands
           if g2 and h_star - 0.02 <= hh <= h_star + 0.04]
    waist_navel = float(np.mean(nav)) if nav else float("nan")
    hip_bands = [g2 for hh, _, g2 in bands if g2 and -0.02 <= hh <= 0.14]
    hip = float(np.max(hip_bands)) if hip_bands else float("nan")
    waist_band = [g2 for hh, _, g2 in bands if g2 and 0.45 <= hh <= 0.62]
    waist_min = float(np.min(waist_band)) if waist_band else waist_navel
    return {"chest": float(chest), "waist_navel": waist_navel,
            "waist_min": waist_min, "hip": hip}


# ------------------------------------------------------------ fold machinery
edges_set = set()
for a, b, c in mh_tris:
    for u, v in ((a, b), (b, c), (c, a)):
        if u < BODY_END and v < BODY_END:
            edges_set.add((min(u, v), max(u, v)))
_e = np.array(sorted(edges_set))


def lap_smooth(x, mask, iters=2):
    x = x.copy()
    for _ in range(iters):
        acc = x.copy()
        cnt = np.ones(len(x))
        np.add.at(acc, _e[:, 0], x[_e[:, 1]])
        np.add.at(acc, _e[:, 1], x[_e[:, 0]])
        np.add.at(cnt, _e[:, 0], 1)
        np.add.at(cnt, _e[:, 1], 1)
        div = cnt[:, None] if x.ndim == 2 else cnt
        x = np.where(mask[:, None] if x.ndim == 2 else mask,
                     acc / div, x)
    return x


def flipped(pos, D):
    p = pos + D
    v0 = p[FACES_B[:, 0]]
    v1 = p[FACES_B[:, 1]]
    v2 = p[FACES_B[:, 2]]
    n0 = np.cross(pos[FACES_B[:, 1]] - pos[FACES_B[:, 0]],
                  pos[FACES_B[:, 2]] - pos[FACES_B[:, 0]])
    n1 = np.cross(v1 - v0, v2 - v0)
    dot = np.einsum("ij,ij->i", n0, n1)
    ln = np.linalg.norm(n0, axis=1) * np.linalg.norm(n1, axis=1)
    return dot < -1e-12 * np.maximum(ln, 1e-30)


def fold_stats(pos, D):
    """(n_flips, min normalised dot) of pos+D against pos's normals."""
    p = pos + D
    v0 = p[FACES_B[:, 0]]
    v1 = p[FACES_B[:, 1]]
    v2 = p[FACES_B[:, 2]]
    n0 = np.cross(pos[FACES_B[:, 1]] - pos[FACES_B[:, 0]],
                  pos[FACES_B[:, 2]] - pos[FACES_B[:, 0]])
    n1 = np.cross(v1 - v0, v2 - v0)
    ln = np.linalg.norm(n0, axis=1) * np.linalg.norm(n1, axis=1)
    dot = np.einsum("ij,ij->i", n0, n1) / np.maximum(ln, 1e-30)
    fl = flipped(pos, D)
    return int(fl.sum()), float(dot.min())


def slope_limit(D, moved):
    D = D.copy()
    nbr = np.linalg.norm(D[_e[:, 0]] - D[_e[:, 1]], axis=1)
    dist = np.linalg.norm(mh_pos[_e[:, 0]] - mh_pos[_e[:, 1]], axis=1)
    bad = nbr > KAPPA * dist
    if bad.any():
        mv = moved.copy()
        mv[np.unique(_e[bad].ravel())] = True
        D = lap_smooth(np.where(mv[:, None], D, 0.0), mv, 3)
        D = np.where(mv[:, None], D, 0.0)
    return D


def repair_inc(base_delta, inc, label):
    """Staged increment repair: attenuate ONLY the increment over an
    already flip-free base delta (the proofs' composition order).
    Attenuating a SUM of cancelling fields per-vertex diverges (the
    first run of this script: 2 flips -> 4479); attenuating the
    increment converges by construction, since inc -> 0 locally
    returns the flip-free base. att floor is 0.0 for increments."""
    for pos, nm in ((mh_pos, "raw"), (mh_pos_mac, "macro")):
        fb, _ = fold_stats(pos, base_delta)
        assert fb == 0, f"{label}: base delta not flip-free on {nm} ({fb})"
    moved = np.linalg.norm(inc, axis=1) > 0.0002
    inc = slope_limit(inc, moved)
    att = np.ones(NB)
    traj = []
    for it in range(80):
        badv = np.zeros(NB, bool)
        for pos in (mh_pos, mh_pos_mac):
            fl = flipped(pos, base_delta + inc * att[:, None])
            if fl.any():
                badv[FACES_B[fl].ravel()] = True
        traj.append(int(badv.sum()))
        if not badv.any():
            print(f" {label}: increment clean after {it} iterations "
                  f"(trajectory {traj})")
            break
        nbr = np.zeros(NB, bool)
        nbr[_e[badv[_e].any(axis=1)].ravel()] = True
        att[badv] *= 0.78
        att[nbr & ~badv] *= 0.93
        att = np.maximum(att, 0.0)
    else:
        print(f" {label}: WARNING flips remain after 80 iterations")
    return inc * att[:, None], att, traj


# ----------------------------------------------------------------- targets
def fmt(v):
    s = f"{abs(v):.3f}".rstrip("0")
    if s.endswith("."):
        s += "0"
    if s in ("", "0."):
        s = "0"
    return ("-" + s) if v < 0 else s


def write_target(path, delta, note):
    d_obj = np.stack([delta[:, 0], delta[:, 2], delta[:, 1]],
                     axis=1) / DM_M
    moved = np.where(np.abs(d_obj).max(axis=1) > 0.001)[0]
    header = ("# This is a target file for MakeHuman\n#\n"
              "# It was written by the MakeTarget submodule of MPFB\n#\n"
              "# For more information, see MakeHuman's home page at "
              "http://www.makehumancommunity.org\n#\n# basemesh hm08\n"
              f"# {note}\n")
    with open(path, "w") as fh:
        fh.write(header)
        for i in moved:
            fh.write(f"{i} {fmt(d_obj[i, 0])} {fmt(d_obj[i, 1])} "
                     f"{fmt(d_obj[i, 2])}\n")
    return int(len(moved))


# ------------------------------------------------------- labels + transfers
h_hi, th_hi, r_hi, ax_hi, cr_hi, nk_hi, L_hi = torso_params(hi_pos_u * SK)
s_hi = L_mh / L_hi
hi_lab = label_mesh(hi_pos_u * SK, cr_hi, nk_hi)
mh_lab = label_mesh(mh_pos_mac, mh_crotch, mh_neck, BODY_MASK)
h_mh, th_mh, r_mh, ax_mh, _, _, _ = torso_params(
    mh_pos_mac, mh_crotch, mh_neck, "hm08")
SIG_H, SIG_A = 0.05, 0.04
cv_report = {}


def torso_field(delta, tag, sig_h=SIG_H, sig_a=SIG_A):
    """Verbatim from build_bara.py (signed-theta (h, arc) kernel),
    with the bandwidth exposed: mass fields use the proof bandwidths;
    definition fields (narrow features, 1-4 cm wide) need a feature-
    scale bandwidth or the kernel dilutes them 5-10x (measured and
    reported in COUPLING_VALIDATION.md)."""
    gate_s = hi_lab["torso"] & (
        ((h_hi > -0.02) & (h_hi < 1.06) & (r_hi < 0.30))
        | ((h_hi >= 1.06) & (h_hi < 1.18) & (r_hi < 0.13)))
    hh, tt, rr, dd = h_hi[gate_s], th_hi[gate_s], r_hi[gate_s], \
        delta[gate_s]
    er = np.stack([np.sin(tt), np.cos(tt)], axis=1)
    dr_s = dd[:, 0] * er[:, 0] + dd[:, 1] * er[:, 1]
    dz_s = dd[:, 2]
    rb = np.linspace(-0.02, 1.18, 25)
    rmean = np.array([rr[(hh >= rb[i]) & (hh < rb[i + 1])].mean()
                      if ((hh >= rb[i]) & (hh < rb[i + 1])).sum() > 5
                      else 0.17 for i in range(24)])
    rctr = 0.5 * (rb[:-1] + rb[1:])

    def arc(theta, hv):
        return theta * np.interp(hv, rctr, rmean)
    arc_s = arc(tt, hh)
    arc_q = arc(th_mh, h_mh)
    dr, dz = pair_field(hh, arc_s, dr_s, dz_s, h_mh, arc_q,
                        sig_h, sig_a)
    dr, dz = dr * s_hi, dz * s_hi
    cv = pair_cv(hh, arc_s, dr_s, dz_s, sig_h, sig_a)
    if cv:
        cv_report[f"torso/{tag}"] = cv
    out = np.zeros((NB, 3))
    out[:, 0] = dr * np.sin(th_mh)
    out[:, 1] = dr * np.cos(th_mh)
    out[:, 2] = dz
    return out


def blend_torso_only(torso_f):
    out = W3[:, 0:1] * torso_f
    return out / np.maximum(1.0, W3.sum(axis=1, keepdims=True))


print("transferring unit definition fields + authored neck field...")
# Definition fields at BOTH bandwidths: the standard (mass) kernel's
# peak recovery is itself a validation finding; the feature-scale
# kernel (sigma_h 0.018, sigma_arc 0.014) is what the measurement
# builds use.
DEF_SIG = (0.018, 0.014)
F_VALLEYS_STD = blend_torso_only(torso_field(
    hi_diff("ArmsTrapsValleys") * SK, "valleys-std"))
F_VLINE_STD = blend_torso_only(torso_field(
    hi_diff("TorsoVLine") * SK, "vline-std"))
F_CREASE_STD = blend_torso_only(torso_field(
    hi_diff("PecsCrease") * SK, "crease-std"))
F_VALLEYS = blend_torso_only(torso_field(
    hi_diff("ArmsTrapsValleys") * SK, "valleys", *DEF_SIG))
F_VLINE = blend_torso_only(torso_field(
    hi_diff("TorsoVLine") * SK, "vline", *DEF_SIG))
F_CREASE = blend_torso_only(torso_field(
    hi_diff("PecsCrease") * SK, "crease", *DEF_SIG))
# NeckMass: the block is 'Weight 0 to 1' in the Vanilla OSD.
# build_bara.py's hi_diff("Weight") silently missed it (zeros), so
# the shipped body.muscle contains NO authored neck field -- caught
# by this validation; see COUPLING_VALIDATION.md bug report. The
# field is derived here exactly as BARA_LESSONS A2 specified.
neck_gate = sstep(h_hi, 0.88, 0.96) * (1 - sstep(h_hi, 1.08, 1.18)) \
    * (1 - sstep(r_hi, 0.13, 0.20))
NECK_EMB = blend_torso_only(torso_field(
    hi_diff("Weight 0 to 1") * (0.90 * SK) * neck_gate[:, None],
    "neck")) * ATT_M[:, None]
R["peak_recovery"] = {}
for nm, F, Fs, srcname in (
        ("valleys", F_VALLEYS, F_VALLEYS_STD, "ArmsTrapsValleys"),
        ("vline", F_VLINE, F_VLINE_STD, "TorsoVLine"),
        ("crease", F_CREASE, F_CREASE_STD, "PecsCrease")):
    src_max = float(np.linalg.norm(hi_diff(srcname), axis=1).max() * SK)
    mag = np.linalg.norm(F, axis=1)
    mags = np.linalg.norm(Fs, axis=1)
    R["peak_recovery"][nm] = {
        "source_max_cm": src_max * 100,
        "std_kernel_max_cm": float(mags.max() * 100),
        "std_kernel_recovery": float(mags.max() / src_max),
        "feature_kernel_max_cm": float(mag.max() * 100),
        "feature_kernel_recovery": float(mag.max() / src_max)}
    print(f" {nm}: source max {src_max*100:.2f} cm; std kernel "
          f"{mags.max()*100:.2f} (x{mags.max()/src_max:.2f}); feature "
          f"kernel {mag.max()*100:.2f} (x{mag.max()/src_max:.2f})")
mag = np.linalg.norm(NECK_EMB, axis=1)
print(f" neck(authored, embedded): support "
      f"{int((mag > 0.0002).sum())}, max {mag.max()*100:.2f} cm")
R["field_cv"] = cv_report

# ------------------------------------------------------------- evaluator
reg = SliderRegistry.from_folder(APP / "library/sliders")
coup = CouplingRegistry.from_folder(APP / "library/couplings")

GACHI_RAW = {"body.muscle": 0.80, "body.chubby": 1.00,
             "body.tissue.mass_smooth": 0.90, "body.belly.pot": 0.85,
             "body.belly.protrusion": 0.85,
             "body.definition.traps_valleys": 0.40,
             "body.definition.vline": 0.85,
             "body.neck.mass": 0.90, "body.pecs.size": 1.00,
             "body.torso.mass": 1.00, "body.arms.delts": 0.90,
             "body.distribution": 0.0}
PEAR_RAW = {"body.distribution": -1.0, "body.muscle": 0.45,
            "body.tissue.level": 0.637}
BIG_RAW = {"body.distribution": 1.0, "body.muscle": 0.85,
           "body.tissue.level": 0.419}
CR_P_RAW = {"body.distribution": -1.0, "body.muscle": 1.0,
            "body.tissue.level": 0.6, "body.definition.pecs_crease": 0.80}
CR_B_RAW = {"body.distribution": 1.0, "body.muscle": 1.0,
            "body.tissue.level": 0.6, "body.definition.pecs_crease": 0.80}

EV = {}
for tag, raw in (("gachidebu", GACHI_RAW), ("pear", PEAR_RAW),
                 ("bigchest", BIG_RAW), ("crease_pear", CR_P_RAW),
                 ("crease_bigchest", CR_B_RAW)):
    out = evaluate_effective_vector(reg, coup, raw)
    EV[tag] = out
    R["evaluator"][tag] = {
        "raw": raw,
        "effective": {k: float(v) for k, v in out.sliders.items()},
        "derived": {k: float(v) for k, v in out.derived.items()},
        "warnings": [{"slider": w.slider_id, "kind": w.kind,
                      "message": w.message} for w in out.warnings]}
    print(f"evaluator {tag}: level "
          f"{out.derived.get('tissue.level', float('nan')):.3f}")

SEN_LEVEL = (0.55 * 0.80 + 0.25 * 0.75 + 0.20 * 0.65)  # = 0.7575 (test-asserted)
GACHI_LEVEL = EV["gachidebu"].derived["tissue.level"]
T_SCALE = GACHI_LEVEL / SEN_LEVEL
print(f"tissue scale strongman-cell -> gachidebu: x{T_SCALE:.4f}")

# ------------------------------------------------- machinery self-check
G_SC = grade(mh_pos_mac + M_F + W_F + T_F, mh_lab)
G_BASE = grade(mh_pos_mac, mh_lab)
R["selfcheck"] = {
    "note": "shipped strongman build re-graded with this script's "
            "machinery; BARA_PROOF.md reference: M4 1.301, M1 0.711, "
            "chest 133.6, waist 102.6, neck 36.4, thigh 75.9 cm",
    "M4": G_SC["M4_chest_waist"], "M1": G_SC["M1_neckW_headW"],
    "chest_g_cm": G_SC["chest_g"] * 100, "waist_g_cm": G_SC["waist_g"] * 100,
    "neck_g_cm": G_SC["neck_g"] * 100, "thigh_g_cm": G_SC["thigh_g"] * 100}
print(f"SELF-CHECK strongman: M4 {G_SC['M4_chest_waist']:.3f} (proof "
      f"1.301), M1 {G_SC['M1_neckW_headW']:.3f} (0.711), chest "
      f"{G_SC['chest_g']*100:.1f} (133.6), waist {G_SC['waist_g']*100:.1f} "
      f"(102.6), neck {G_SC['neck_g']*100:.1f} (36.4)")
assert abs(G_SC["M4_chest_waist"] - 1.301) < 0.03, "machinery distrust: M4"
assert abs(G_SC["M1_neckW_headW"] - 0.711) < 0.03, "machinery distrust: M1"

# ------------------------------------------- macro-region map (per-vertex)
# Geometry-layer region map [E protocol, documented in the validation
# doc]: torso split by (h, theta) bands; arms -> chest macro and legs
# -> thighs macro per the coupling's region_to_macro (upper_arm,
# forearm -> chest; thigh, calf -> thighs; back -> chest; neck ->
# chest; abdomen, flanks -> waist; glutes -> hips_glutes).
MACRO_NAMES = ["chest", "waist", "hips_glutes", "thighs"]
macro = np.zeros(NB, dtype=int)                    # default chest
_torso = mh_lab["torso"]
macro[_torso & (h_mh >= 0.44) & (h_mh < 0.70)
      & (np.abs(th_mh) <= 2.2)] = 1                 # waist (front+sides)
macro[_torso & (h_mh >= 0.02) & (h_mh < 0.44)] = 2  # pelvis/glute band
macro[_torso & (h_mh < 0.02)] = 3
macro[mh_lab["leg"]] = 3
macro[mh_lab["arm"]] = 0
ZONE_MASKS = {name: (macro == i) & BODY_MASK
              for i, name in enumerate(MACRO_NAMES)}
ZONE_MASKS["neck"] = _torso & (h_mh >= 0.98) & BODY_MASK
ZONE_MASKS["arms"] = mh_lab["arm"] & BODY_MASK
print("macro zones:", {k: int(v.sum()) for k, v in ZONE_MASKS.items()})


def factor_map(factors, kind):
    """factors: evaluator derived dict for one character; kind is
    'tissue' or 'muscle'. Returns a lap-smoothed per-vertex map."""
    f = np.array([factors[f"distribution.{kind}.{m}"]
                  for m in MACRO_NAMES])
    m = f[macro]
    return lap_smooth(m, BODY_MASK, 3)


# ------------------------------------------- dip (definition) measurement
def radius_of(P):
    rel = P[:, :2] - ax_mh
    return np.linalg.norm(rel, axis=1)


def core_window(F, frac=0.5):
    mag = np.linalg.norm(F, axis=1)
    core = np.where(mag >= frac * mag.max())[0]
    core = core[core < BODY_END]
    return core


def _rough(prof, used):
    """Profile roughness (mm): std of the profile detrended by a
    5-bin moving average, over the used bins -- the local surface
    variation a feature must exceed to READ on the mesh."""
    p = prof[used]
    if len(p) < 6:
        return float("nan")
    k = np.ones(5) / 5
    sm = np.convolve(np.pad(p, 2, mode="edge"), k, "valid")
    return float(np.std(p - sm) * 1000.0)


def dip_theta(P, F, h_pad=0.04, nbins=20, span=1.3):
    """(dip depth mm, roughness mm) of a theta-profile feature
    (vline / valleys): shoulder-bin mean radius minus core-window
    mean radius, per side, averaged. Windows come from the unit
    field's own footprint."""
    core = core_window(F)
    r = radius_of(P)
    depths, roughs = [], []
    for sgn in (1.0, -1.0):
        cc = core[np.sign(mh_pos_mac[core, 0] - ax_mh[core, 0]) == sgn]
        if len(cc) < 8:
            continue
        hlo, hhi = h_mh[cc].min() - h_pad, h_mh[cc].max() + h_pad
        uth = np.abs(th_mh[cc])
        clo, chi = uth.min(), uth.max()
        m = BODY_MASK & (h_mh >= hlo) & (h_mh <= hhi) \
            & (np.abs(th_mh) <= span) \
            & (np.sign(mh_pos_mac[:, 0] - ax_mh[:, 0]) == sgn)
        u = np.abs(th_mh[m])
        bins = np.linspace(0, span, nbins + 1)
        prof = np.full(nbins, np.nan)
        for i in range(nbins):
            mm = (u >= bins[i]) & (u < bins[i + 1])
            if mm.sum() >= 3:
                prof[i] = r[m][mm].mean()
        ctr = 0.5 * (bins[:-1] + bins[1:])
        ok = ~np.isnan(prof)
        if ok.sum() < 4:
            continue
        prof = np.interp(ctr, ctr[ok], prof[ok])
        core_bins = (ctr >= clo - 0.03) & (ctr <= chi + 0.03)
        sh_bins = ((ctr >= chi + 0.08) & (ctr <= chi + 0.45)) \
            | ((ctr >= clo - 0.45) & (ctr <= clo - 0.08))
        if core_bins.sum() >= 1 and sh_bins.sum() >= 2:
            depths.append(float(prof[sh_bins].mean()
                                - prof[core_bins].mean()))
            roughs.append(_rough(prof, core_bins | sh_bins))
    if not depths:
        return float("nan"), float("nan")
    return float(np.mean(depths)) * 1000.0, float(np.mean(roughs))


def dip_h(P, F, th_half=0.5, nbins=22, pad=0.12):
    """(dip above mm, dip below mm, roughness mm) of an h-profile
    feature (pecs crease): pec-plate (above-window) mean radius
    minus core-window mean radius."""
    core = core_window(F)
    r = radius_of(P)
    clo, chi = h_mh[core].min(), h_mh[core].max()
    m = BODY_MASK & (np.abs(th_mh) < th_half) \
        & (h_mh >= clo - pad) & (h_mh <= chi + pad)
    bins = np.linspace(clo - pad, chi + pad, nbins + 1)
    prof = np.full(nbins, np.nan)
    for i in range(nbins):
        mm = (h_mh[m] >= bins[i]) & (h_mh[m] < bins[i + 1])
        if mm.sum() >= 3:
            prof[i] = r[m][mm].mean()
    ctr = 0.5 * (bins[:-1] + bins[1:])
    ok = ~np.isnan(prof)
    if ok.sum() < 4:
        return float("nan"), float("nan"), float("nan")
    prof = np.interp(ctr, ctr[ok], prof[ok])
    core_bins = (ctr >= clo - 0.01) & (ctr <= chi + 0.01)
    above = (ctr > chi + 0.01) & (ctr <= chi + 0.09)
    below = (ctr < clo - 0.01) & (ctr >= clo - 0.09)
    d_above = float(prof[above].mean() - prof[core_bins].mean()) * 1000.0
    d_below = float(prof[below].mean() - prof[core_bins].mean()) * 1000.0 \
        if below.sum() >= 2 else float("nan")
    return d_above, d_below, _rough(prof, core_bins | above | below)


def dip_increment(sub_pos, F, v, kind, **kw):
    """Feature expression of field F at value v over substrate
    sub_pos: (dip increment mm, absolute dip mm on the applied
    build, roughness mm of the applied build's profile)."""
    if kind == "theta":
        d1, r1 = dip_theta(sub_pos + v * F, F, **kw)
        d0, _ = dip_theta(sub_pos, F, **kw)
        return d1 - d0, d1, r1
    a1, _, r1 = dip_h(sub_pos + v * F, F, **kw)
    a0, _, _ = dip_h(sub_pos, F, **kw)
    return a1 - a0, a1, r1


# ------------------------------------------- wrap audit (angular sectors)
def sector_audit(D, bands):
    er = np.stack([np.sin(th_mh), np.cos(th_mh)], axis=1)
    dr = np.abs(D[:, 0] * er[:, 0] + D[:, 1] * er[:, 1])
    drs = D[:, 0] * er[:, 0] + D[:, 1] * er[:, 1]
    out = {}
    for band, (h0, h1) in bands.items():
        hb = BODY_MASK & (h_mh >= h0) & (h_mh < h1)
        fr = hb & (np.abs(th_mh) < 0.5)
        fl = hb & (np.abs(th_mh) > 0.9) & (np.abs(th_mh) < 2.2)
        bk = hb & (np.abs(th_mh) > 2.7)
        f_ = float(dr[fr].mean() * 100) if fr.sum() else 0.0
        l_ = float(dr[fl].mean() * 100) if fl.sum() else 0.0
        b_ = float(dr[bk].mean() * 100) if bk.sum() else 0.0
        fs = float(drs[fr].mean() * 100) if fr.sum() else 0.0
        ls = float(drs[fl].mean() * 100) if fl.sum() else 0.0
        out[band] = {"front_cm": f_, "flank_cm": l_, "back_cm": b_,
                     "flank_front": (l_ / f_) if f_ > 0 else 0.0,
                     "flank_front_signed": (ls / fs) if fs > 0 else 0.0}
    return out


def zone_residuals(delta, twin, label):
    out = {}
    for zname, m in ZONE_MASKS.items():
        d = np.linalg.norm((delta - twin)[m], axis=1)
        out[zname] = {"rms_cm": float(np.sqrt((d ** 2).mean()) * 100),
                      "max_cm": float(d.max() * 100),
                      "mean_abs_delta_cm": float(
                          np.linalg.norm(delta[m], axis=1).mean() * 100)}
    print(f" zone residuals {label}: " +
          ", ".join(f"{k} rms {v['rms_cm']:.2f}" for k, v in out.items()))
    return out


def fold_report(delta, label, store=True):
    fr_, md_ = fold_stats(mh_pos, delta)
    fm_, mdm_ = fold_stats(mh_pos_mac, delta)
    print(f" fold gate {label}: raw {fr_} flips (min dot {md_:.3f}), "
          f"macro {fm_} (min dot {mdm_:.3f})")
    if store:
        R["folds"][label] = {"raw_flips": fr_, "raw_min_dot": md_,
                             "macro_flips": fm_, "macro_min_dot": mdm_}
    return fr_, fm_


# ============================================================ GACHIDEBU
print("\n== GACHIDEBU ==")
eff_g = EV["gachidebu"]
TG = T_SCALE * T_F
NECK_EFF_SCALE = float(eff_g.sliders["body.neck.mass"]) / 0.90
BASE_G = M_F + W_F + T_F                      # shipped strongman (flip-free)
INC_G = (T_SCALE - 1.0) * T_F + NECK_EMB * NECK_EFF_SCALE
INC_G, att_g, traj_g = repair_inc(BASE_G, INC_G, "gachidebu increment")
DELTA_G = BASE_G + INC_G
fold_report(DELTA_G, "gachidebu")
R["folds"]["gachidebu"]["repair"] = {
    "att_min": float(att_g.min()),
    "verts_touched": int((att_g < 0.999).sum()),
    "trajectory": [int(t) for t in traj_g]}
POS_G = mh_pos_mac + DELTA_G
POS_G_RAWNECK = mh_pos_mac + (BASE_G + (T_SCALE - 1.0) * T_F + NECK_EMB)
POS_SC_NECK = mh_pos_mac + BASE_G + NECK_EMB
G_G = grade(POS_G, mh_lab)
G_G_RN = grade(POS_G_RAWNECK, mh_lab)
G_SCN = grade(POS_SC_NECK, mh_lab)
GH_G = girths(POS_G)
R["gachidebu"]["grade"] = {k: float(v) for k, v in G_G.items()}
R["gachidebu"]["girths_profiles"] = GH_G
R["gachidebu"]["tissue_scale"] = T_SCALE
R["gachidebu"]["neck_show_through"] = {
    "raw": 0.90, "effective": float(eff_g.sliders["body.neck.mass"]),
    "factor": NECK_EFF_SCALE,
    "note": "the shipped body.muscle contains NO authored neck field "
            "(build_bara hi_diff name miss -- bug report in the doc); "
            "the neck component here is the A2 field derived in this "
            "script from the 'Weight 0 to 1' block, so the comparison "
            "is neck-at-raw vs neck-at-effective on identical builds, "
            "plus the field's worth vs the shipped strongman neck",
    "neck_girth_cm_effective": G_G["neck_g"] * 100,
    "neck_girth_cm_raw": G_G_RN["neck_g"] * 100,
    "neck_girth_delta_mm": (G_G["neck_g"] - G_G_RN["neck_g"]) * 1000,
    "neck_width_cm_effective": G_G["neck_w"] * 100,
    "neck_width_cm_raw": G_G_RN["neck_w"] * 100,
    "M1_effective": G_G["M1_neckW_headW"], "M1_raw": G_G_RN["M1_neckW_headW"],
    "strongman_neck_girth_cm_shipped": G_SC["neck_g"] * 100,
    "strongman_neck_girth_cm_with_authored_field": G_SCN["neck_g"] * 100,
    "strongman_M1_with_authored_field": G_SCN["M1_neckW_headW"]}
print(f" neck: strongman shipped {G_SC['neck_g']*100:.1f} cm, with "
      f"authored field {G_SCN['neck_g']*100:.1f}; gachidebu raw-neck "
      f"{G_G_RN['neck_g']*100:.1f} -> effective "
      f"{G_G['neck_g']*100:.1f} cm "
      f"({(G_G['neck_g']-G_G_RN['neck_g'])*1000:+.1f} mm), M1 "
      f"{G_G['M1_neckW_headW']:.3f}")
WRAP_BANDS = {"chest": (0.78, 0.92),
              "waist": (h_star - 0.06, h_star + 0.06),
              "belly_apron": (0.35, 0.55)}
R["gachidebu"]["wrap_audit"] = sector_audit(TG, WRAP_BANDS)
TG_RING = TG.copy()
TG_RING[B_CORE > 0.05] = 0.0     # drape (belly core) excluded: ring only
R["gachidebu"]["wrap_audit_ring_only"] = sector_audit(TG_RING, WRAP_BANDS)
R["gachidebu"]["wrap_emitted"] = {
    "wrap.factor.waist": eff_g.derived["wrap.factor.waist"],
    "wrap.factor.chest": eff_g.derived["wrap.factor.chest"],
    "wrap.ratio.waist": eff_g.derived["wrap.ratio.waist"],
    "floor": 0.40}
for tag, aud in (("full", R["gachidebu"]["wrap_audit"]),
                 ("ring-only", R["gachidebu"]["wrap_audit_ring_only"])):
    for b, v in aud.items():
        print(f" wrap[{tag}] {b}: flank/front {v['flank_front']:.3f} "
              f"(signed {v['flank_front_signed']:.3f}) front "
              f"{v['front_cm']:.2f} flank {v['flank_cm']:.2f} cm")

# definition submergence: dip increments over identical substrates;
# S1 is the SHIPPED gachidebu build (post-repair), S0 the muscle
# system alone (the low-tissue reference substrate).
S0 = mh_pos_mac + M_F + W_F
S1 = POS_G
DEF = {}
for nm, F, raw_v, eff_v, kw in (
        ("vline", F_VLINE, GACHI_RAW["body.definition.vline"],
         float(eff_g.sliders["body.definition.vline"]), {"span": 1.3}),
        ("valleys", F_VALLEYS, GACHI_RAW["body.definition.traps_valleys"],
         float(eff_g.sliders["body.definition.traps_valleys"]),
         {"span": 3.14, "nbins": 28})):
    i_low, a_low, r_low = dip_increment(S0, F, raw_v, "theta", **kw)
    i_naive, a_naive, r_naive = dip_increment(S1, F, raw_v, "theta", **kw)
    i_coup, a_coup, r_coup = dip_increment(S1, F, eff_v, "theta", **kw)
    att = eff_v / raw_v
    DEF[nm] = {"raw": raw_v, "effective": eff_v, "attenuation": att,
               "dip_inc_low_tissue_mm": i_low,
               "dip_inc_naive_mm": i_naive,
               "dip_inc_coupled_mm": i_coup,
               "dip_abs_coupled_mm": a_coup,
               "roughness_coupled_mm": r_coup,
               "snr_coupled": (i_coup / r_coup) if r_coup else None,
               "tissue_fill_factor": i_naive / i_low if i_low else None,
               "total_read_vs_model": (i_coup / i_low) if i_low else None,
               "model_prediction": att}
    print(f" def {nm}: inc low {i_low:.2f} mm, naive {i_naive:.2f}, "
          f"coupled {i_coup:.2f} (abs dip {a_coup:.2f}, rough "
          f"{r_coup:.2f}, SNR {i_coup/r_coup:.2f}); fill "
          f"{i_naive/i_low:.3f}, total {i_coup/i_low:.3f} vs model "
          f"A*G {att:.3f}")
R["gachidebu"]["definition"] = DEF
R["zone_residuals"]["gachidebu"] = zone_residuals(DELTA_G, BASE_G,
                                                  "gachidebu vs strongman")

# ============================================================ PEAR / BIG
print("\n== DISTRIBUTION PAIR ==")
GH_BASE = girths(mh_pos_mac)
GH_SC = girths(mh_pos_mac + M_F + W_F + T_F)
R["profile_girths"] = {"base": GH_BASE, "strongman_control": GH_SC}


def hip_width(pos):
    Z = np.array([0.0, 0.0, 1.0])
    lp = best_loop(pos, Z, np.array([0, 0, mh_crotch + 0.05]))
    return float(lp[:, 0].max() - lp[:, 0].min()) if lp is not None \
        else float("nan")


DIST_BUILDS = {}
for tag, evtag, raw in (("pear", "pear", PEAR_RAW),
                        ("bigchest", "bigchest", BIG_RAW)):
    ev = EV[evtag]
    w = ev.derived["tissue.level"]
    tfac = factor_map(ev.derived, "tissue")
    mfac = factor_map(ev.derived, "muscle")
    chest_mf = ev.derived["distribution.muscle.chest"]
    muscle_w = M_F * mfac[:, None] + W_F * chest_mf
    tissue_w = d5(w) * tfac[:, None]
    twin = (M_F + W_F) + d5(w)
    # staged repair: weighting increment over the flip-free muscle
    # system, then the tissue layer over the weighted muscle
    inc_m = muscle_w - (M_F + W_F)
    inc_m, att_m, traj_m = repair_inc(M_F + W_F, inc_m,
                                      f"{tag} muscle weighting")
    muscle_w = M_F + W_F + inc_m
    tissue_w, att_t, traj_t = repair_inc(muscle_w, tissue_w,
                                         f"{tag} tissue layer")
    delta = muscle_w + tissue_w
    fold_report(delta, tag)
    R["folds"][tag]["repair"] = {
        "muscle_inc": {"att_min": float(att_m.min()),
                       "verts_touched": int((att_m < 0.999).sum())},
        "tissue": {"att_min": float(att_t.min()),
                   "verts_touched": int((att_t < 0.999).sum())}}
    DIST_BUILDS[tag] = delta
    pos = mh_pos_mac + delta
    pos0 = mh_pos_mac + twin
    G = grade(pos, mh_lab)
    gh, gh0 = girths(pos), girths(pos0)
    hw, hw0 = hip_width(pos), hip_width(pos0)
    R[tag] = {
        "level_w": w, "grade": {k: float(v) for k, v in G.items()},
        "girths": gh, "girths_control_dist0": gh0,
        "ratios": {
            "chest_waist": gh["chest"] / gh["waist_navel"],
            "waist_hip": gh["waist_navel"] / gh["hip"],
            "chest_hip": gh["chest"] / gh["hip"]},
        "ratios_control": {
            "chest_waist": gh0["chest"] / gh0["waist_navel"],
            "waist_hip": gh0["waist_navel"] / gh0["hip"],
            "chest_hip": gh0["chest"] / gh0["hip"]},
        "hip_width_m": hw, "hip_width_control_m": hw0,
        "shoulder_hip_width": G["delt_span"] / hw,
        "shoulder_hip_width_control": G["delt_span"] / hw0,
        "thigh_g_cm": G["thigh_g"] * 100}
    print(f" {tag}: C {gh['chest']*100:.1f} W {gh['waist_navel']*100:.1f} "
          f"H {gh['hip']*100:.1f} cm | W:H {gh['waist_navel']/gh['hip']:.3f} "
          f"(ctl {gh0['waist_navel']/gh0['hip']:.3f}) | C:W "
          f"{gh['chest']/gh['waist_navel']:.3f} (ctl "
          f"{gh0['chest']/gh0['waist_navel']:.3f}) | thigh "
          f"{G['thigh_g']*100:.1f} cm")
    R["zone_residuals"][tag] = zone_residuals(delta, twin,
                                              f"{tag} vs dist-0 twin")
    fr, md = fold_stats(mh_pos_mac, twin)
    R["folds"][f"{tag}_control_dist0"] = {"macro_flips": fr, "min_dot": md}

# ============================================================ CREASE PAIR
print("\n== PECS CREASE INTERACTION (test conditions) ==")
CR = {}
for tag, evtag, evraw in (("pear", "crease_pear", CR_P_RAW),
                          ("bigchest", "crease_bigchest", CR_B_RAW)):
    ev = EV[evtag]
    tfac = factor_map(ev.derived, "tissue")
    mfac = factor_map(ev.derived, "muscle")
    chest_mf = ev.derived["distribution.muscle.chest"]
    sub = mh_pos_mac + M_F * mfac[:, None] + W_F * chest_mf \
        + d5(0.6) * tfac[:, None]
    eff_v = float(ev.sliders["body.definition.pecs_crease"])
    i_eff, a_eff, r_eff = dip_increment(sub, F_CREASE, eff_v, "h")
    i_raw, _, _ = dip_increment(sub, F_CREASE, 0.80, "h")
    _, b_eff, _ = dip_h(sub + eff_v * F_CREASE, F_CREASE)
    fr, md = fold_stats(mh_pos_mac, (sub - mh_pos_mac) + eff_v * F_CREASE)
    CR[tag] = {"effective": eff_v, "attenuation": eff_v / 0.80,
               "dip_inc_coupled_mm": i_eff, "dip_inc_raw_mm": i_raw,
               "dip_abs_coupled_mm": a_eff, "dip_below_mm": b_eff,
               "roughness_mm": r_eff,
               "snr_coupled": (i_eff / r_eff) if r_eff else None,
               "full_build_macro_flips": fr}
    print(f" crease {tag}: eff {eff_v:.3f}; inc coupled {i_eff:.2f} mm, "
          f"inc raw {i_raw:.2f} mm")
fill = CR["bigchest"]["dip_inc_raw_mm"] / CR["pear"]["dip_inc_raw_mm"]
ratio_meas = CR["bigchest"]["dip_inc_coupled_mm"] \
    / CR["pear"]["dip_inc_coupled_mm"]
ratio_pred = (CR["bigchest"]["effective"] / CR["pear"]["effective"]) * fill
CR["comparison"] = {"fill_ratio_big_over_pear": fill,
                    "coupled_ratio_measured": ratio_meas,
                    "coupled_ratio_predicted": ratio_pred,
                    "attenuation_ratio": CR["bigchest"]["effective"]
                    / CR["pear"]["effective"]}
R["crease"] = CR
print(f" crease ratio: measured {ratio_meas:.3f} vs predicted "
      f"{ratio_pred:.3f} (attenuation-only "
      f"{CR['comparison']['attenuation_ratio']:.3f}, fill {fill:.3f})")

# ============================================================ OUTPUTS
NOTE_G = ("Provenance: omniversal coupling validation -- GACHIDEBU "
          "character (Muscle x Tissue model section 7.1): body.muscle "
          "+ body.chest.width + body.tissue.strongman scaled by the "
          "level ratio 0.945/0.7575, NeckMass show-through boost "
          "applied separably. Instance makehuman_hm08. Study-only, "
          "internal. See COUPLING_VALIDATION.md.")
NOTE_P = ("Provenance: omniversal coupling validation -- PEAR "
          "character (distribution -1, tissue-driven, section 7.4): "
          "muscle field weighted by distribution muscle factors, v5 "
          "adiposity system at w=0.637 weighted by distribution "
          "tissue factors. Instance makehuman_hm08. Study-only, "
          "internal. See COUPLING_VALIDATION.md.")
NOTE_B = ("Provenance: omniversal coupling validation -- BIG-CHEST "
          "character (distribution +1, section 7.4): muscle field "
          "weighted by distribution muscle factors, v5 adiposity "
          "system at w=0.419 weighted by distribution tissue "
          "factors. Instance makehuman_hm08. Study-only, internal. "
          "See COUPLING_VALIDATION.md.")
n1 = write_target(OUT / "body.coupling.gachidebu.target", DELTA_G, NOTE_G)
n2 = write_target(OUT / "body.coupling.pear.target", DIST_BUILDS["pear"],
                  NOTE_P)
n3 = write_target(OUT / "body.coupling.bigchest.target",
                  DIST_BUILDS["bigchest"], NOTE_B)
print(f"\ntargets written: gachidebu {n1}, pear {n2}, bigchest {n3} "
      f"moved verts")
R["targets"] = {"gachidebu": n1, "pear": n2, "bigchest": n3}
(WORK / "coupling_validation_numbers.json").write_text(
    json.dumps(R, indent=1, default=float))
print("wrote work/coupling_validation_numbers.json")
print("BUILD COUPLING VALIDATION DONE")
