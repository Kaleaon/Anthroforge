#!/usr/bin/env python3
"""DEFINITION GEOMETRY INSTANCES for AnthroForge (Joe approved
Nov 12, 2026).

The Muscle x Tissue evaluator attenuates definition sliders
numerically (MUSCLE_TISSUE_MODEL.md section 5), and the coupling
validation proved the attenuation RATIOS on mesh for two fields
(valleys, vline) -- but the definition family had no shipped hm08
instances, and the validation's fields were uncalibrated kernel
transfers (feature-kernel peak recovery 0.28-0.43 of source).

This build ships calibrated instances for the four definition
sliders that have library records:

  body.definition.flat_abs       <- HIMBO TorsoFlatAbs (Vanilla set)
  body.definition.traps_valleys  <- HIMBO ArmsTrapsValleys (Vanilla)
  body.definition.pecs_crease    <- HIMBO PecsCrease (Vanilla)
  body.definition.back           <- HIMBO TorsoBackDefinition --
      the Vanilla set has NO such block; the record's decode came
      from the SOS set (1519 verts, max 1.367 u), whose base stream
      defeats the pipeline extractor and whose indexing is NOT the
      Vanilla base's (verified: same-named blocks carry different
      index sets). The instance therefore transfers the SOS HP
      twin block (HPTorsoBackDefinition, 1065 verts, max 1.368 u --
      the identical sculpt on the high-poly tessellation), whose
      base stream extracts cleanly and position-verifies against
      the Vanilla body (every Vanilla vert has an exact-position
      match in the HP stream). Documented in DEFINITION_GEOMETRY.md.

Method per slider:
  1. Feature-kernel transfer (sigma_h 0.018, sigma_arc 0.014 -- the
     coupling validation's definition bandwidth) of the source
     block's (dr, dz) field in (h, theta) torso coordinates, region-
     blended (torso weights W3), pipeline scale s = L_mh / L_source.
  2. CALIBRATION: the canonical feature depth is measured with an
     identical station measure on (a) the source base + source
     field at 1.0 and (b) hm08 muscle substrate + transferred field
     at 1.0; the field is scaled so (b) equals (a) x s. The kernel
     supplies the shape; calibration restores the amplitude the
     kernel dilutes. Scale factors reported, bounded [0.4, 4.0].
  3. ATTENUATION QA: the calibrated field composed over the
     strongman (level 0.7575) and gachidebu (level 0.945) substrates
     at the evaluator's EFFECTIVE values for authored value 1.0
     (muscle 0.80); measured dip-increment ratios vs the muscle
     substrate at raw 1.0 must track the evaluator's A x G.
  4. FOLD GATE: 0 flips on raw AND macro bases for the field at 1.0
     over the muscle, strongman and gachidebu substrates.

Machinery copied from build_coupling_validation.py (the proofs'
convention). PROVENANCE: study-only, as the other proofs.
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
DEF_SIG = (0.018, 0.014)

R = {"sliders": {}, "evaluator": {}, "folds": {}}


def sstep(x, a, b):
    t = np.clip((np.asarray(x, float) - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


# ---------------------------------------------------------------- loads
corr = np.load(FP / "work/correspondence.npz")
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

S0 = mh_pos_mac + M_F + W_F                    # muscle system (tissue 0)
S_SM = S0 + T_F                                # strongman (level .7575)
# DELTA_G (gachidebu substrate) is rebuilt in float further below:
# the shipped coupling target is its 0.1 mm-quantised export, and
# parsing it back flips marginally-stable faces (the float build's
# raw min dot was 0.0006). See the rebuild block after the evaluator.
print(f"hm08: {NB} verts, L={L_mh:.4f} m, h*={h_star:.4f}")


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
                cand = (int(e - s), float(run[:, 2].max() - run[:, 2].min()),
                        run)
                if best is None or cand[:2] > best[:2]:
                    best = cand
    return None if best is None else best[2]


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


def neck_base(pos, ctr, axis, crotch):
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


def torso_params(pos, crotch=None, neck=None):
    gate = np.ones(len(pos), bool)
    ctr, axis = compute_axis(pos, gate)
    if crotch is None:
        crotch = crotch_of(pos, gate, 0.030, 0.060)
    if neck is None:
        neck = neck_base(pos, ctr, axis, crotch)
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


def label_mesh(pos, crotch, neck, body_mask=None):
    """Verbatim from build_bara.py (region labeller; only the torso /
    arm / leg split and side are consumed here)."""
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
    return {"arm": arm, "leg": leg, "torso": torso, "side": side,
            "ax": ax, "r": r, "rel": rel}


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
    """Staged increment repair (verbatim protocol): attenuate ONLY
    the increment over an already flip-free base delta."""
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
            print(f" {label}: increment clean after {it} iterations")
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


# ------------------------------------------------------------- sources
hi_pos_u = extract_base_positions(
    (HIMBO_DIR / "HIMBO Body - Vanilla.nif").read_bytes(), 4000)
assert hi_pos_u is not None and len(hi_pos_u) == 9346, "Vanilla base"
hp_pos_u = extract_base_positions(
    (HIMBO_DIR / "SOS HP.nif").read_bytes(), 4000)
assert hp_pos_u is not None and len(hp_pos_u) > 9346, "HP base"
van_blocks = {b["name"]: b for b in
              load_osd(str(HIMBO_DIR / "HIMBO Body - Vanilla.osd"))["blocks"]}
hp_blocks = {b["name"]: b for b in
             load_osd(str(HIMBO_DIR / "SOS HP.osd"))["blocks"]}


def block_delta(blocks, name, n):
    blk = blocks.get(name)
    if blk is None:
        return None
    d = np.zeros((n, 3))
    d[blk["indices"]] = blk["diffs"]
    return d


class Source:
    def __init__(self, tag, pos_u, blocks):
        self.tag = tag
        self.pos_u = pos_u
        self.pos = pos_u * SK
        self.blocks = blocks
        self.n = len(pos_u)
        (self.h, self.th, self.r, self.ax, self.cr, self.nk,
         self.L) = torso_params(self.pos)
        self.lab = label_mesh(self.pos, self.cr, self.nk)
        self.s = L_mh / self.L
        print(f"source {tag}: {self.n} verts, L={self.L:.4f} m, "
              f"s={self.s:.4f}")

    def diff(self, name):
        return block_delta(self.blocks, name, self.n)


SRC_VAN = Source("vanilla", hi_pos_u, van_blocks)
SRC_HP = Source("sos_hp", hp_pos_u, hp_blocks)

h_mh, th_mh, r_mh, ax_mh, _, _, _ = torso_params(
    mh_pos_mac, mh_crotch, mh_neck)
cv_report = {}


def torso_field_p(src, delta, tag, sig_h, sig_a):
    """Parameterized twin of build_coupling_validation.torso_field:
    signed-theta (h, arc) kernel from an arbitrary source base."""
    gate_s = src.lab["torso"] & (
        ((src.h > -0.02) & (src.h < 1.06) & (src.r < 0.30))
        | ((src.h >= 1.06) & (src.h < 1.18) & (src.r < 0.13)))
    hh, tt, rr, dd = src.h[gate_s], src.th[gate_s], src.r[gate_s], \
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
    dr, dz = pair_field(hh, arc_s, dr_s, dz_s, h_mh, arc_q, sig_h, sig_a)
    dr, dz = dr * src.s, dz * src.s
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


# ------------------------------------------- station (feature-depth) measures
def radius_of(P, ax):
    rel = P[:, :2] - ax
    return np.linalg.norm(rel, axis=1)


def _rough(prof, used):
    p = prof[used]
    if len(p) < 6:
        return float("nan")
    k = np.ones(5) / 5
    sm = np.convolve(np.pad(p, 2, mode="edge"), k, "valid")
    return float(np.std(p - sm) * 1000.0)


def core_window(F, n_body, frac=0.5):
    mag = np.linalg.norm(F, axis=1)
    core = np.where(mag >= frac * mag.max())[0]
    return core[core < n_body]


def dip_theta_g(P, pos0, h, th, ax, mask, F, n_body,
                h_pad=0.04, nbins=20, span=1.3):
    """Generalized dip_theta (validation): shoulder-bin mean radius
    minus core-window mean radius, per side, averaged. Radii are read
    on P; windows come from the frame (pos0/h/th) and F's footprint.
    Returns ABSOLUTE dip on P (mm); increments are taken by callers
    as dip(P+F) - dip(P)."""
    core = core_window(F, n_body)
    r = radius_of(P, ax)
    depths, roughs = [], []
    for sgn in (1.0, -1.0):
        cc = core[np.sign(pos0[core, 0] - ax[core, 0]) == sgn]
        if len(cc) < 8:
            continue
        hlo, hhi = h[cc].min() - h_pad, h[cc].max() + h_pad
        uth = np.abs(th[cc])
        clo, chi = uth.min(), uth.max()
        m = mask & (h >= hlo) & (h <= hhi) & (np.abs(th) <= span) \
            & (np.sign(pos0[:, 0] - ax[:, 0]) == sgn)
        u = np.abs(th[m])
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


def dip_h_g(P, h, th, ax, mask, F, n_body,
            th_half=0.5, nbins=22, pad=0.12):
    """Generalized dip_h (validation): pec-plate (above-window) mean
    radius minus core-window mean radius. Returns (above, below,
    roughness) in mm on P."""
    core = core_window(F, n_body)
    r = radius_of(P, ax)
    clo, chi = h[core].min(), h[core].max()
    m = mask & (np.abs(th) < th_half) \
        & (h >= clo - pad) & (h <= chi + pad)
    bins = np.linspace(clo - pad, chi + pad, nbins + 1)
    prof = np.full(nbins, np.nan)
    for i in range(nbins):
        mm = (h[m] >= bins[i]) & (h[m] < bins[i + 1])
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


def inc_profile(P0, F, v, ax, mask, hw, coord_bins, coord_of):
    """Binned mean radial INCREMENT (P0+vF vs P0) over a window.
    coord_of: vertex -> profile coordinate array (precomputed)."""
    inc = radius_of(P0 + v * F, ax) - radius_of(P0, ax)
    m = mask & hw
    u = coord_of[m]
    prof = np.full(len(coord_bins) - 1, np.nan)
    for i in range(len(coord_bins) - 1):
        mm = (u >= coord_bins[i]) & (u < coord_bins[i + 1])
        if mm.sum() >= 3:
            prof[i] = inc[m][mm].mean()
    return prof


def abs_station(P0, F, v, h, th, ax, mask, n_body):
    """flat_abs canonical station: (flattening depth, linea-alba
    groove depth) in mm, as increments over P0 at value v.
    Windows from F's own footprint (h core), front |theta| <= 1.0."""
    core = core_window(F, n_body, frac=0.35)
    hlo, hhi = h[core].min(), h[core].max()
    hw = (h >= hlo) & (h <= hhi) & (np.abs(th) <= 1.0)
    uth = np.abs(th)
    bins = np.linspace(0, 1.0, 11)
    prof = inc_profile(P0, F, v, ax, mask, hw, bins, uth)
    ctr = 0.5 * (bins[:-1] + bins[1:])
    ok = ~np.isnan(prof)
    prof = np.interp(ctr, ctr[ok], prof[ok])
    centre = prof[ctr <= 0.30].mean()
    flank = prof[(ctr >= 0.55) & (ctr <= 0.95)].mean()
    flat = float((flank - centre) * 1000.0)
    gbins = np.linspace(-0.45, 0.45, 19)
    gprof = inc_profile(P0, F, v, ax, mask, hw, gbins, th)
    gctr = 0.5 * (gbins[:-1] + gbins[1:])
    ok = ~np.isnan(gprof)
    gprof = np.interp(gctr, gctr[ok], gprof[ok])
    seg = gprof[(np.abs(gctr) >= 0.12) & (np.abs(gctr) <= 0.35)].mean()
    mid = gprof[np.abs(gctr) <= 0.05].mean()
    groove = float((seg - mid) * 1000.0)
    return flat, groove


def back_station(P0, F, v, h, th, ax, mask, n_body):
    """back canonical station: (spinal furrow depth, relief RMS) in
    mm, as increments over P0 at value v. Coordinate u = pi - |theta|
    (0 at the back midline); window from F's footprint h core."""
    core = core_window(F, n_body, frac=0.35)
    hlo, hhi = h[core].min(), h[core].max()
    u = np.pi - np.abs(th)
    hw = (h >= hlo) & (h <= hhi) & (u <= 1.3)
    bins = np.linspace(0, 1.3, 14)
    prof = inc_profile(P0, F, v, ax, mask, hw, bins, u)
    ctr = 0.5 * (bins[:-1] + bins[1:])
    ok = ~np.isnan(prof)
    prof = np.interp(ctr, ctr[ok], prof[ok])
    groove = prof[ctr <= 0.10].mean()
    shoulder = prof[(ctr >= 0.22) & (ctr <= 0.60)].mean()
    furrow = float((shoulder - groove) * 1000.0)
    rms = float(np.std(prof[ctr <= 1.0]) * 1000.0)
    return furrow, rms


# frame bundles for the station measures
class Frame:
    def __init__(self, pos0, h, th, ax, mask, n_body):
        self.pos0, self.h, self.th, self.ax = pos0, h, th, ax
        self.mask, self.n_body = mask, n_body


FR_MH = Frame(mh_pos_mac, h_mh, th_mh, ax_mh, BODY_MASK, BODY_END)
FR_VAN = Frame(SRC_VAN.pos, SRC_VAN.h, SRC_VAN.th, SRC_VAN.ax,
               np.ones(SRC_VAN.n, bool), SRC_VAN.n)
FR_HP = Frame(SRC_HP.pos, SRC_HP.h, SRC_HP.th, SRC_HP.ax,
              np.ones(SRC_HP.n, bool), SRC_HP.n)


def station(fr, kind, P0, F, v):
    """Feature depth (mm) of field F at value v over substrate P0,
    in frame fr. Primary measure per slider kind."""
    if kind == "valleys":
        d1, _ = dip_theta_g(P0 + v * F, fr.pos0, fr.h, fr.th, fr.ax,
                            fr.mask, F, fr.n_body, span=3.14, nbins=28)
        d0, _ = dip_theta_g(P0, fr.pos0, fr.h, fr.th, fr.ax,
                            fr.mask, F, fr.n_body, span=3.14, nbins=28)
        return d1 - d0
    if kind == "crease":
        a1, _, _ = dip_h_g(P0 + v * F, fr.h, fr.th, fr.ax,
                           fr.mask, F, fr.n_body)
        a0, _, _ = dip_h_g(P0, fr.h, fr.th, fr.ax,
                           fr.mask, F, fr.n_body)
        return a1 - a0
    if kind == "abs":
        f1, _ = abs_station(P0, F, v, fr.h, fr.th, fr.ax, fr.mask,
                            fr.n_body)
        return f1
    if kind == "back":
        f1, _ = back_station(P0, F, v, fr.h, fr.th, fr.ax, fr.mask,
                             fr.n_body)
        return f1
    if kind == "back_rms":
        _, r1 = back_station(P0, F, v, fr.h, fr.th, fr.ax, fr.mask,
                             fr.n_body)
        return r1
    raise ValueError(kind)


# ------------------------------------------------------------- evaluator
reg = SliderRegistry.from_folder(APP / "library/sliders")
coup = CouplingRegistry.from_folder(APP / "library/couplings")
DEF_IDS = ["body.definition.flat_abs", "body.definition.traps_valleys",
           "body.definition.pecs_crease", "body.definition.back"]
SM_RAW = {"body.muscle": 0.80, "body.chubby": 0.80,
          "body.tissue.mass_smooth": 0.75, "body.belly.pot": 0.65}
G_RAW = {"body.muscle": 0.80, "body.chubby": 1.00,
         "body.tissue.mass_smooth": 0.90, "body.belly.pot": 0.85,
         "body.belly.protrusion": 0.85, "body.neck.mass": 0.90,
         "body.pecs.size": 1.00, "body.torso.mass": 1.00,
         "body.arms.delts": 0.90, "body.distribution": 0.0}
EFF = {}
for tag, base in (("strongman", SM_RAW), ("gachidebu", G_RAW)):
    raw = dict(base)
    for d in DEF_IDS:
        raw[d] = 1.0
    out = evaluate_effective_vector(reg, coup, raw)
    EFF[tag] = {d: float(out.sliders[d]) for d in DEF_IDS}
    R["evaluator"][tag] = {
        "level": float(out.derived["tissue.level"]),
        "effective_at_raw_1.0": EFF[tag],
        "attenuation": {d: EFF[tag][d] / 1.0 for d in DEF_IDS}}
    print(f"evaluator {tag}: level {out.derived['tissue.level']:.4f}, "
          f"attenuation " +
          ", ".join(f"{d.split('.')[-1]} {EFF[tag][d]:.3f}"
                    for d in DEF_IDS))

# ------------------------------------------- gachidebu substrate (float)
# Rebuilt exactly as build_coupling_validation built it: shipped
# strongman (flip-free) + repaired increment [(T_SCALE - 1) x tissue
# + authored NeckMass field x show-through scale]. The neck field is
# the A2 gated Weight-block transfer at the STANDARD kernel (the
# validation's construction; ATT_M is the muscle build's attenuation).
GACHI_RAW_FULL = {"body.muscle": 0.80, "body.chubby": 1.00,
                  "body.tissue.mass_smooth": 0.90,
                  "body.belly.pot": 0.85, "body.belly.protrusion": 0.85,
                  "body.definition.traps_valleys": 0.40,
                  "body.definition.vline": 0.85,
                  "body.neck.mass": 0.90, "body.pecs.size": 1.00,
                  "body.torso.mass": 1.00, "body.arms.delts": 0.90,
                  "body.distribution": 0.0}
_out_g = evaluate_effective_vector(reg, coup, GACHI_RAW_FULL)
NECK_EFF = float(_out_g.sliders["body.neck.mass"])
SEN_LEVEL = 0.55 * 0.80 + 0.25 * 0.75 + 0.20 * 0.65     # 0.7575
T_SCALE = float(_out_g.derived["tissue.level"]) / SEN_LEVEL
_neck_gate = sstep(SRC_VAN.h, 0.88, 0.96) \
    * (1 - sstep(SRC_VAN.h, 1.08, 1.18)) \
    * (1 - sstep(SRC_VAN.r, 0.13, 0.20))
NECK_EMB = blend_torso_only(torso_field_p(
    SRC_VAN, SRC_VAN.diff("HIMBO - BodyWeight 0 to 1")
    * (0.90 * SK) * _neck_gate[:, None], "neck", 0.05, 0.04)) \
    * ATT_M[:, None]
BASE_G = M_F + W_F + T_F
INC_G = (T_SCALE - 1.0) * T_F + NECK_EMB * (NECK_EFF / 0.90)
INC_G, _att_g, _traj_g = repair_inc(BASE_G, INC_G, "gachidebu rebuild")
DELTA_G = BASE_G + INC_G
S_G = mh_pos_mac + DELTA_G                     # gachidebu (level .945)
R["gachidebu_substrate"] = {
    "tissue_scale": T_SCALE, "neck_effective": NECK_EFF,
    "repair_att_min": float(_att_g.min()),
    "repair_verts_touched": int((_att_g < 0.999).sum()),
    "note": "float rebuild of the shipped body.coupling.gachidebu "
            "build (build_coupling_validation protocol); the "
            "shipped target is this field's 0.1 mm-quantised export"}
print(f"gachidebu substrate rebuilt: T_SCALE {T_SCALE:.4f}, neck "
      f"eff {NECK_EFF:.4f}, repair touched "
      f"{int((_att_g < 0.999).sum())} verts")

# ------------------------------------------------------------- per-slider
SLIDERS = [
    {"id": "body.definition.flat_abs", "kind": "abs",
     "label": "Flat Abs", "src": SRC_VAN, "frame": FR_VAN,
     "block": "HIMBO - BodyTorsoFlatAbs",
     "record_block": "HIMBO - TorsoFlatAbs",
     "region_class": "abdomen"},
    {"id": "body.definition.traps_valleys", "kind": "valleys",
     "label": "Traps Valleys", "src": SRC_VAN, "frame": FR_VAN,
     "block": "HIMBO - BodyArmsTrapsValleys",
     "record_block": "HIMBO - ArmsTrapsValleys",
     "region_class": "yoke"},
    {"id": "body.definition.pecs_crease", "kind": "crease",
     "label": "Pecs Crease (Underside)", "src": SRC_VAN, "frame": FR_VAN,
     "block": "HIMBO - BodyPecsCrease",
     "record_block": "HIMBO - PecsCrease",
     "region_class": "chest"},
    {"id": "body.definition.back", "kind": "back",
     "label": "Back Definition", "src": SRC_HP, "frame": FR_HP,
     "block": "HIMBO - Body HPTorsoBackDefinition",
     "record_block": "HIMBO - TorsoBackDefinition (SOS set decode; "
                     "instance transfers the SOS HP twin block)",
     "region_class": "back"},
]

FIELDS = {}
for spec in SLIDERS:
    sid, kind, src = spec["id"], spec["kind"], spec["src"]
    print(f"\n== {sid} <- {spec['block']} ==")
    d_src = src.diff(spec["block"])
    assert d_src is not None, f"missing block {spec['block']}"
    d_src_m = d_src * SK
    src_peak = float(np.linalg.norm(d_src_m, axis=1).max())
    src_sup = int((np.linalg.norm(d_src_m, axis=1) > 0.0002).sum())
    # back: probe both station measures on the source and calibrate
    # on the stronger signal (the furrow-specific contrast of this
    # broad sculpt is sub-mm; the relief RMS is its canonical depth)
    mkind = kind
    back_detail = None
    if kind == "back":
        _fur, _rms = back_station(src.pos, d_src_m, 1.0, src.h, src.th,
                                  src.ax, np.ones(src.n, bool), src.n)
        mkind = "back_rms" if _rms >= 0.5 else "back"
        back_detail = {"furrow_source_mm": _fur, "rms_source_mm": _rms,
                       "primary_measure": mkind}
        print(f" back station probe: furrow {_fur:.2f} mm, relief "
              f"RMS {_rms:.2f} mm -> primary {mkind}")
    # source-side canonical depth (bare source base, value 1.0)
    D_src = station(spec["frame"], mkind, src.pos, d_src_m, 1.0)
    D_target = D_src * src.s
    print(f" source: support {src_sup}, peak {src_peak*1000:.1f} mm, "
          f"canonical depth {D_src:.2f} mm -> target {D_target:.2f} mm "
          f"(x s {src.s:.3f})")
    # transfer at the feature kernel
    F = blend_torso_only(torso_field_p(src, d_src_m, sid.split(".")[-1],
                                       *DEF_SIG))
    D_tr = station(FR_MH, mkind, S0, F, 1.0)
    print(f" transfer: canonical depth on hm08 muscle substrate "
          f"{D_tr:.2f} mm (source {D_src:.2f}, target {D_target:.2f})")
    groove_note = None
    if kind == "abs":
        # flat_abs calibrates on TWO station measures jointly: the
        # flattening depth (primary) and the linea-alba groove. The
        # transferred field under-carries the groove (0.45 of a
        # 0.92 mm target), so a groove component is authored inside
        # the source footprint (slider-lab authoring where the
        # source is thin) and the pair (transfer scale a, groove
        # peak d) is solved as a 2x2 linear system against both
        # targets -- the station measures are near-linear in the
        # fields at these amplitudes.
        _, g_src = abs_station(src.pos, d_src_m, 1.0, src.h, src.th,
                               src.ax, np.ones(src.n, bool), src.n)
        g_target = g_src * src.s
        flat_t, groove_t = abs_station(S0, F, 1.0, h_mh, th_mh, ax_mh,
                                       BODY_MASK, BODY_END)
        print(f" linea alba groove: source {g_src:.2f} mm, target "
              f"{g_target:.2f}, transferred {groove_t:.2f}")
        groove_note = {"source_mm": g_src, "target_mm": g_target,
                       "transferred_mm": groove_t, "authored": False}
        scale = D_target / D_tr
        if g_src >= 0.3 and groove_t < 0.5 * g_target:
            core = core_window(F, BODY_END, frac=0.35)
            hlo, hhi = h_mh[core].min(), h_mh[core].max()
            hw = sstep(h_mh, hlo - 0.02, hlo + 0.03) \
                * (1 - sstep(h_mh, hhi - 0.03, hhi + 0.02))
            g = np.exp(-0.5 * (th_mh / 0.045) ** 2) * hw
            er = np.stack([np.sin(th_mh), np.cos(th_mh)], axis=1)
            G = np.zeros((NB, 3))
            G[:, 0] = -g * er[:, 0]
            G[:, 1] = -g * er[:, 1]
            G = blend_torso_only(G)
            # G's peak is 1.0 (dimensionless shape); probe it at a
            # physical 1 mm amplitude and express its station
            # coefficients per metre of peak.
            _fg, _gg = abs_station(S0, G, 0.001, h_mh, th_mh,
                                   ax_mh, BODY_MASK, BODY_END)
            flat_g, groove_g = _fg / 0.001, _gg / 0.001
            A = np.array([[flat_t, flat_g], [groove_t, groove_g]])
            sol = np.linalg.solve(A, np.array([D_target, g_target]))
            a, d = float(sol[0]), float(sol[1])
            if d < 0:
                a, d = D_target / flat_t, 0.0
            assert 0.4 <= a <= 4.0, f"{sid}: solved transfer scale {a}"
            F_t = F
            F = a * F_t + d * G
            # one refinement pass: the station windows ride on the
            # combined field's own footprint, so the linear solve
            # lands ~10% off; correct once with the same coefficients
            flat_c, groove_c = abs_station(S0, F, 1.0, h_mh, th_mh,
                                           ax_mh, BODY_MASK, BODY_END)
            if abs(flat_c - D_target) > 0.05 * D_target \
                    or abs(groove_c - g_target) > 0.05 * g_target:
                delta = np.linalg.solve(
                    A, np.array([D_target - flat_c,
                                 g_target - groove_c]))
                da, dd = float(delta[0]), float(delta[1])
                F = F + da * F_t + dd * G
                a, d = a + da, d + dd
                flat_c, groove_c = abs_station(
                    S0, F, 1.0, h_mh, th_mh, ax_mh, BODY_MASK, BODY_END)
                print(f" groove refinement: da {da:+.3f}, dd "
                      f"{dd*1000:+.2f} mm -> flat {flat_c:.2f}, "
                      f"groove {groove_c:.2f}")
            scale = a
            groove_note.update({"authored": True,
                                "groove_field_peak_mm": d * 1000.0,
                                "final_mm": groove_c})
            print(f" authored linea-alba groove: solved a={a:.3f}, "
                  f"groove peak {d*1000:.2f} mm -> groove "
                  f"{groove_c:.2f} mm (target {g_target:.2f})")
    else:
        # signed-depth calibration: the dip measures are signed
        # (valleys read negative under the dip_theta convention on
        # BOTH frames -- the coupling validation's own finding), so
        # calibration is by signed ratio with a sign-match guard.
        assert abs(D_tr) >= 0.05 and np.sign(D_tr) == np.sign(D_src), \
            f"{sid}: transfer depth {D_tr:.2f} mm vs source " \
            f"{D_src:.2f} -- shape/sign suspect"
        scale = D_target / D_tr
        assert 0.4 <= scale <= 4.0, f"{sid}: calibration scale " \
            f"{scale:.3f} outside [0.4, 4.0] -- transfer shape suspect"
        F = F * scale
    print(f" calibration scale {scale:.3f}")
    FIELDS[sid] = (F, spec)
    D_fin = station(FR_MH, mkind, S0, F, 1.0)
    peak_fin = float(np.linalg.norm(F, axis=1).max())
    moved = int((np.linalg.norm(F, axis=1) > 0.0002).sum())
    print(f" calibrated: depth {D_fin:.2f} mm (target {D_target:.2f}), "
          f"peak {peak_fin*1000:.1f} mm, moved {moved}")
    # ---- attenuation QA (authored value 1.0)
    att = {}
    for tag, sub, eff in (("strongman", S_SM, EFF["strongman"][sid]),
                          ("gachidebu", S_G, EFF["gachidebu"][sid])):
        d_low = station(FR_MH, mkind, S0, F, 1.0)
        d_eff = station(FR_MH, mkind, sub, F, eff)
        d_naive = station(FR_MH, mkind, sub, F, 1.0)
        pred = eff / 1.0
        att[tag] = {
            "effective_value": eff, "predicted_ratio": pred,
            "dip_inc_tissue0_mm": d_low,
            "dip_inc_coupled_mm": d_eff,
            "dip_inc_naive_mm": d_naive,
            "measured_ratio": (d_eff / d_low) if d_low else None,
            "fill_factor_naive_over_tissue0": (d_naive / d_low)
            if d_low else None,
            "abs_error": abs(d_eff / d_low - pred) if d_low else None}
        print(f" attenuation {tag}: pred {pred:.3f}, measured "
              f"{d_eff/d_low:.3f} (coupled {d_eff:.2f} mm vs tissue0 "
              f"{d_low:.2f}; naive {d_naive:.2f})")
    # ---- fold gate: field at raw 1.0 over all three substrates
    folds = {}
    ok_all = True
    for tag, base_delta in (("muscle", M_F + W_F),
                            ("strongman", M_F + W_F + T_F),
                            ("gachidebu", DELTA_G)):
        for pos, nm in ((mh_pos, "raw"), (mh_pos_mac, "macro")):
            fb, _ = fold_stats(pos, base_delta)
            assert fb == 0, f"{sid}/{tag}: substrate not flip-free {nm}"
        fr_, mdr = fold_stats(mh_pos, base_delta + F)
        fm_, mdm = fold_stats(mh_pos_mac, base_delta + F)
        folds[tag] = {"raw_flips": fr_, "raw_min_dot": mdr,
                      "macro_flips": fm_, "macro_min_dot": mdm}
        ok_all &= (fr_ == 0 and fm_ == 0)
        print(f" fold gate {tag}: raw {fr_} (min dot {mdr:.3f}), "
              f"macro {fm_} ({mdm:.3f})")
    if not ok_all:
        # repair the field as an increment over the gachidebu build
        F, att_r, _ = repair_inc(DELTA_G, F, f"{sid} field repair")
        D_rep = station(FR_MH, mkind, S0, F, 1.0)
        print(f" repaired field: depth re-measured {D_rep:.2f} mm "
              f"(target {D_target:.2f}); att touched "
              f"{int((att_r < 0.999).sum())} verts")
        folds["after_repair"] = {}
        for tag, base_delta in (("muscle", M_F + W_F),
                                ("strongman", M_F + W_F + T_F),
                                ("gachidebu", DELTA_G)):
            fr_, mdr = fold_stats(mh_pos, base_delta + F)
            fm_, mdm = fold_stats(mh_pos_mac, base_delta + F)
            folds["after_repair"][tag] = {
                "raw_flips": fr_, "raw_min_dot": mdr,
                "macro_flips": fm_, "macro_min_dot": mdm}
            ok_all &= (fr_ == 0 and fm_ == 0)
        FIELDS[sid] = (F, spec)
        D_fin = D_rep
        peak_fin = float(np.linalg.norm(F, axis=1).max())
        moved = int((np.linalg.norm(F, axis=1) > 0.0002).sum())
    assert ok_all, f"{sid}: fold gate FAILED"
    R["folds"][sid] = folds
    R["sliders"][sid] = {
        "kind": kind, "block": spec["block"],
        "record_block": spec["record_block"],
        "source_set": spec["src"].tag,
        "source_support_verts": src_sup,
        "source_peak_mm": src_peak * 1000.0,
        "source_canonical_depth_mm": D_src,
        "pipeline_scale_s": src.s,
        "target_depth_mm": D_target,
        "transfer_depth_mm": D_tr,
        "calibration_scale": scale,
        "final_depth_mm": D_fin,
        "final_peak_mm": peak_fin * 1000.0,
        "moved_verts": moved,
        "groove": groove_note,
        "back_station_detail": back_detail,
        "measure": mkind,
        "attenuation": att,
        "kernel_cv": cv_report.get(f"torso/{sid.split('.')[-1]}"),
    }

# combined definition set at 1.0 over gachidebu (the renders' state)
DEF_SUM = sum(F for F, _ in FIELDS.values())
for pos, nm in ((mh_pos, "raw"), (mh_pos_mac, "macro")):
    fr_, mdr = fold_stats(pos, DELTA_G + DEF_SUM)
    fm_ = fr_
    print(f"combined defs over gachidebu ({nm}): {fr_} flips "
          f"(min dot {mdr:.3f})")
    R["folds"][f"combined_defs_gachidebu_{nm}"] = {
        "flips": fr_, "min_dot": mdr}
    assert fr_ == 0, "combined definition set folds over gachidebu"

# ------------------------------------------------------------- outputs
NOTES = {
    "body.definition.flat_abs":
        "Provenance: omniversal definition instance -- Flat Abs "
        "(HIMBO TorsoFlatAbs, Vanilla set), feature-kernel transfer "
        "calibrated to the source canonical depth. Instance "
        "makehuman_hm08. Study-only, internal. See "
        "DEFINITION_GEOMETRY.md.",
    "body.definition.traps_valleys":
        "Provenance: omniversal definition instance -- Traps "
        "Valleys (HIMBO ArmsTrapsValleys, Vanilla set), feature-"
        "kernel transfer calibrated to the source canonical depth. "
        "Instance makehuman_hm08. Study-only, internal. See "
        "DEFINITION_GEOMETRY.md.",
    "body.definition.pecs_crease":
        "Provenance: omniversal definition instance -- Pecs Crease "
        "(HIMBO PecsCrease, Vanilla set), feature-kernel transfer "
        "calibrated to the source canonical depth. Instance "
        "makehuman_hm08. Study-only, internal. See "
        "DEFINITION_GEOMETRY.md.",
    "body.definition.back":
        "Provenance: omniversal definition instance -- Back "
        "Definition (HIMBO TorsoBackDefinition; SOS-set slider, "
        "instance transfers the SOS HP twin block on its position-"
        "verified base), feature-kernel transfer calibrated to the "
        "source canonical depth. Instance makehuman_hm08. "
        "Study-only, internal. See DEFINITION_GEOMETRY.md.",
}
for sid, (F, spec) in FIELDS.items():
    n = write_target(OUT / f"{sid}.target", F, NOTES[sid])
    R["sliders"][sid]["target_moved_verts"] = n
    print(f"wrote {sid}.target ({n} moved verts)")

np.savez(WORK / "definition_fields.npz",
         **{sid.replace(".", "_"): F for sid, (F, _) in FIELDS.items()})
(WORK / "definition_numbers.json").write_text(
    json.dumps(R, indent=1, default=float))
print("wrote work/definition_numbers.json")
print("BUILD DEFINITION DONE")
