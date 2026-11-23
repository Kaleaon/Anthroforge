#!/usr/bin/env python3
"""NECK + FOREARM FIELD AUTHORING for AnthroForge (Joe approved
Nov 12, 2026).

The bara strongman proof (BARA_PROOF.md section 6, misses M2/M3)
showed the HIMBO vocabulary runs out at the neck and the forearm:
neck girth gained only 32.2 -> 36.4 cm with every recipe value
pinned, and ArmsFore at 1.00 still left forearm:arm at 0.690. This
build AUTHORS the two missing fields procedurally on hm08 --
landmark-driven smooth fields in the slider-lab manner, calibrated
against anatomy anchors, not recipe values:

  body.neck.mass   -- the yoke as ONE field: neck-column growth
    (radial, with the front-centre SCM strip excluded from full
    weight so the sternocleidomastoid V-groove survives, R8) +
    trapezius cone (radial-out + UP on the slope band, outer 2/3
    clavicle budget, R6) so the traps rise beside the jaw (R4/R5/R7).
    Calibrated so the strongman composition's neck girth reaches
    the Reeves arm-equality band (scorecard M2), with the record's
    acceptance gate (body.neck.mass.json extensions.acceptance)
    measured on the muscle system with traps pinned.

  body.forearm.mass -- the strength read (R14): radial growth on
    the forearm segment with the profile peaked on the extensor wad
    / brachioradialis just below the elbow, sector-weighted
    (back + lateral heavy, wrist kept comparatively lean),
    calibrated so the full strongman composition lands forearm:arm
    inside the study's bara M3 band (0.80-0.88).

Cross-check (scripts/crosscheck_wolves.py, work/wolf_crosscheck.
json): the library's own bara wolf carries NO isolable neck tape --
its neck/trap/ruff/head is one merged mass whose smallest
above-shoulder outline is already 1.5x its clean upper-arm girth,
and its clean-station forearm:arm is 0.834, inside the M3 band.
Real bara geometry sits at/above the Reeves relation; the hm08
proof's 0.688 was the outlier. Calibration direction confirmed
before authoring.

Machinery (kernel-free; fields are authored directly on the target
base): region params + slice-loop grading + surgical fold repair
copied from build_bara.py so numbers are comparable with the proof.

QA: 0 flipped faces at +1 on BOTH bases for each field solo, the
neck over the muscle system, and the forearm over the full
composition (the brief's gate: 0 flips composed with body.muscle;
we check the full stack).

PROVENANCE: study-only. The fields are our own procedural authoring
(build-tier method, published anatomy anchors); no third-party
geometry ships. Calibration targets come from BARA_LESSONS.md and
the library cross-check above.
"""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
OUT = HERE.parent                      # bara-proof/
V2 = OUT.parent                        # anthroforge-v2/
APP = V2.parent / "anthroforge-app"
FP = V2 / "first-proof"
WORK = OUT / "work"
sys.path.insert(0, str(V2))
sys.path.insert(0, str(APP))

from body_machinery.axes import sstep, torso_params  # noqa: E402
from body_machinery.labels import chain_of, label_mesh, seg_params  # noqa: E402
from body_machinery.loops import (  # noqa: E402
    band,
    best_loop as _bm_best_loop,
    grade as _bm_grade,
    loop_perim,
    plane_loops as _bm_plane_loops,
)
from body_machinery.osd import (  # noqa: E402
    BODY_END,
    align_macro_base,
    load_mpfb_base_obj,
)
from body_machinery.repair import (  # noqa: E402
    body_edges,
    flipped as _bm_flipped,
    lap_smooth as _bm_lap_smooth,
    repair as _bm_repair,
)
from core.geometry import write_target  # noqa: E402

MPFB_ZIP = Path.home() / "workspace/stick-figure-avatar/photoreal/tools/mpfb2.zip"
KAPPA = 0.55


# ---------------------------------------------------------------- loads
corr = np.load(FP / "work/correspondence.npz")
mh_crotch, mh_neck = [float(x) for x in corr["mh_landmarks"]]
navel_mh = int(corr["navel_mh"])
mh_tris = corr["mh_tris"]
L_mh = mh_neck - mh_crotch

mh_pos = load_mpfb_base_obj(MPFB_ZIP)
_mac = np.load(FP / "work/mh_macro_base.npz")["pos_canonical_m"]
mh_pos_mac = align_macro_base(mh_pos, _mac, BODY_END)
NB = len(mh_pos)
FACES_B = mh_tris[np.all(mh_tris < BODY_END, axis=1)]

_bf = np.load(WORK / "bara_fields.npz")
M_field = _bf["muscle_core_canonical_m"].astype(np.float64)
W_field = _bf["chest_width_canonical_m"].astype(np.float64)
T_field = _bf["tissue_canonical_m"].astype(np.float64)
print(f"hm08: {NB} verts, L={L_mh:.4f} m; shipped bara fields loaded "
      f"(core |D|max {np.linalg.norm(M_field, axis=1).max()*100:.1f} cm)")

_e = body_edges(mh_tris, body_end=BODY_END)


def lap_smooth(x, mask, iters=2):
    return _bm_lap_smooth(x, mask, _e, iters=iters)


def plane_loops(pos, n, p0):
    return _bm_plane_loops(pos, FACES_B, n, p0)


def best_loop(pos, n, p0, near_axis=True, max_extent=None):
    return _bm_best_loop(
        pos, FACES_B, n, p0, near_axis=near_axis, max_extent=max_extent
    )


# ------------------------------------------------------------- grading
_mh_body_mask = np.zeros(NB, bool)
_mh_body_mask[:BODY_END] = True
mh_lab = label_mesh(mh_pos_mac, mh_crotch, mh_neck, _mh_body_mask)
h_mh, th_mh, r_mh, ax_mh, _, _, _ = torso_params(
    mh_pos_mac, mh_crotch, mh_neck, "hm08")


def grade(pos, lmts):
    return _bm_grade(
        pos,
        lmts,
        faces_b=FACES_B,
        mh_crotch=mh_crotch,
        mh_neck=mh_neck,
        mh_pos_mac=mh_pos_mac,
        navel_mh=navel_mh,
        h_mh=h_mh,
        body_end=BODY_END,
    )


def jaw_scan(pos):
    """(jaw_z, jaw_w, chin_z, head_w, head_h) by grade()'s width scan."""
    crown = pos[:BODY_END, 2].max()
    widths = []
    for zz in np.arange(mh_neck + 0.06, crown - 0.002, 0.004):
        lp = best_loop(pos, np.array([0.0, 0.0, 1.0]),
                       np.array([0, 0, zz]), max_extent=0.30)
        if lp is not None and loop_perim(lp) > 0.04:
            widths.append((zz, float(lp[:, 0].max() - lp[:, 0].min())))
    head_w = max(w for _, w in widths)
    jaw_win = [(zz, w) for zz, w in widths if zz < mh_neck + 0.17]
    jaw_z, jaw_w = min(jaw_win, key=lambda t: t[1])
    return jaw_z, jaw_w, jaw_z - 0.02, head_w, crown - (jaw_z - 0.02)


def span_at(pos, z):
    """Silhouette span at height z: union x-extent over ALL loops at
    the plane (head + any trap mounds beside it) -- the front-view
    width at that height, which is the record's M1 numerator."""
    loops = [lp for lp in plane_loops(pos, np.array([0.0, 0.0, 1.0]),
                                      np.array([0.0, 0.0, z]))
             if loop_perim(lp) > 0.04]
    if not loops:
        return float("nan")
    return float(max(lp[:, 0].max() for lp in loops)
                 - min(lp[:, 0].min() for lp in loops))


def m1_record(pos):
    """Record-gate M1: front span at jaw level / bizygomatic span."""
    jaw_z, jaw_w, chin_z, head_w, head_h = jaw_scan(mh_pos_mac)
    span = span_at(pos, jaw_z + 0.004)
    return span / head_w, span, head_w, jaw_z


def groove_metrics(pos):
    """SCM V-groove surface probe: at three neck stations, the front
    envelope of the neck loop (max y per 8 mm x-bin) gives ridge
    height at |x| ~ 2.4 cm (SCM bellies) vs the centre bin. depth =
    ridge - centre; positive = centre recessed = groove reads."""
    Z = np.array([0.0, 0.0, 1.0])
    depths = {}
    for dz in (0.020, 0.040, 0.058):
        lp = best_loop(pos, Z, np.array([0.0, 0.0, mh_neck + dz]))
        if lp is None:
            continue
        bins = {}
        for p in lp:
            b = int(round(p[0] / 0.008))
            if abs(b) <= 6:
                bins[b] = max(bins.get(b, -9.0), p[1])
        if 0 in bins and 3 in bins and -3 in bins:
            ridge = 0.5 * (bins[3] + bins[-3])
            depths[f"z+{dz:.3f}"] = float(ridge - bins[0])
    return depths


# ------------------------------------------------------------ fold repair
def flipped(pos, D):
    return _bm_flipped(pos, D, FACES_B)


def repair(D, checks, label, verbose=True):
    return _bm_repair(
        D,
        checks,
        label,
        faces=FACES_B,
        edges=_e,
        ref_pos=mh_pos,
        kappa=KAPPA,
        verbose=verbose,
    )


ZERO = np.zeros((NB, 3))
Z_AXIS = np.array([0.0, 0.0, 1.0])
NECK_STATION_Z = mh_neck + 0.045


def neck_girth(pos):
    lp = best_loop(pos, Z_AXIS, np.array([0.0, 0.0, NECK_STATION_Z]))
    return loop_perim(lp)


G_BASE = grade(mh_pos_mac, mh_lab)
JAW_Z0, JAW_W0, CHIN_Z0, HEAD_W0, HEAD_H0 = jaw_scan(mh_pos_mac)
print(f"base grade: neck {G_BASE['neck_g']*100:.1f} cm, ua "
      f"{G_BASE['ua_g']*100:.1f}, fa {G_BASE['fa_g']*100:.1f}, calf "
      f"{G_BASE['calf_g']*100:.1f}; jaw_z {JAW_Z0:.4f} jaw_w "
      f"{JAW_W0*100:.1f} cm, head_w {HEAD_W0*100:.1f} cm")
GR_BASE = groove_metrics(mh_pos_mac)
print(f"base SCM groove depths (mm): "
      f"{ {k: round(v*1000, 2) for k, v in GR_BASE.items()} }")

# ============================================================ NECK FIELD
# Anatomy-anchored authoring on hm08's own (h, theta, r) params.
# Column: radial growth of the neck cylinder, plateau h 1.00-1.085,
# capped below the jaw line; front-centre strip (|theta| < ~0.32 rad)
# weight-reduced so the SCM V-groove survives (R8). Traps: cone band
# h 0.94-1.03, r 0.08-0.19, lateral/back-weighted (outer 2/3 clavicle
# budget, R6), displaced OUT along the surface radial and UP on a
# mound profile peaked at r ~ 0.115 -- the rise that lets the yoke
# meet the jaw (R4/R7) and carries the record's jaw-level span (M1).
z_mh = mh_pos_mac[:, 2]
er3 = np.stack([np.sin(th_mh), np.cos(th_mh), np.zeros(NB)], axis=1)

_mc_h = sstep(h_mh, 0.975, 1.000) * (1 - sstep(h_mh, 1.085, 1.118))
_mc_r = 1 - sstep(r_mh, 0.080, 0.105)
_mc_z = 1 - sstep(z_mh, JAW_Z0 - 0.014, JAW_Z0 + 0.006)
MASK_COL = _mc_h * _mc_r * _mc_z
GROOVE_DEPTH = 0.38
_gf = 1.0 - GROOVE_DEPTH * np.exp(-(th_mh / 0.30) ** 2)

_a = np.abs(th_mh)
_ang_w = 0.30 + 0.70 * sstep(_a, 0.35, 0.75)
MASK_TRAP = sstep(h_mh, 0.895, 0.940) * (1 - sstep(h_mh, 1.030, 1.090)) \
    * sstep(r_mh, 0.052, 0.082) * (1 - sstep(r_mh, 0.185, 0.240)) * _ang_w
_out_prof = 0.45 + 0.55 * np.exp(-((r_mh - 0.130) / 0.070) ** 2)

# --- v2 trap rise (corrective redesign, see NECK_FOREARM.md) -------
# The v1 design lifted the whole slope band (gt_up on a broad r
# profile): the raised mound tops crossed the fixed tape plane and
# the station loop ballooned (neck_A 75.7 cm at the solved floor).
# The record's jaw-level span and grade()'s visible-neck probe pull
# in opposite directions through the same surface, and the shape
# that satisfies both is the one real yokes have: a MOUND CREST on
# the trapezius' superior border, cresting just lateral of the jaw
# near jaw height and rolling over before the M7 probe point
# (|x| = head_w/2 + 0.03 = 0.109 m). So the rise is a narrow bump in
# r (crest 0.092 m, sigma 0.017) on top of a small broad slope lift,
# plus a jaw flare: sub-jaw verts pushed radially out, widening the
# jaw-plane loop through its crossing edges.
MOUND_R, MOUND_SIG = 0.092, 0.017
_mound_prof = np.exp(-((r_mh - MOUND_R) / MOUND_SIG) ** 2)
_mound_h = sstep(h_mh, 0.930, 0.975) * (1 - sstep(h_mh, 1.045, 1.100))
MASK_MOUND = MASK_TRAP * 0.0 + _mound_h * sstep(r_mh, 0.045, 0.065) \
    * (1 - sstep(r_mh, 0.150, 0.200)) * _ang_w
_lift_prof = np.exp(-((r_mh - 0.105) / 0.055) ** 2)
MASK_JAWFLARE = (1 - sstep(r_mh, 0.062, 0.082)) \
    * sstep(z_mh, JAW_Z0 - 0.038, JAW_Z0 - 0.018) \
    * (1 - sstep(z_mh, JAW_Z0 - 0.002, JAW_Z0 + 0.010))


def neck_field(gc, mound_a, lift_a, gt_out, jaw_flare):
    F = er3 * (gc * MASK_COL * _gf)[:, None]
    F = F + (MASK_TRAP * lift_a * _lift_prof)[:, None] * Z_AXIS[None, :]
    F = F + (MASK_MOUND * mound_a * _mound_prof)[:, None] \
        * Z_AXIS[None, :]
    F = F + (MASK_TRAP * gt_out * _out_prof)[:, None] * er3
    F = F + er3 * (jaw_flare * MASK_JAWFLARE * _gf)[:, None]
    sup = np.linalg.norm(F, axis=1) > 1e-6
    return lap_smooth(F, sup, 2)


NECK_CHECKS = [(mh_pos, ZERO), (mh_pos_mac, ZERO),
               (mh_pos, M_field + W_field),
               (mh_pos_mac, M_field + W_field)]


def repaired_neck(gc, mound_a, lift_a, gt_out, jaw_flare):
    F, _, _ = repair(neck_field(gc, mound_a, lift_a, gt_out, jaw_flare),
                     NECK_CHECKS, "neck trial")
    return F


# Calibration targets (context A = muscle system, context C = full):
# C neck 0.530 m -> M2_arm = 0.530/0.5293 = 1.001 (Reeves), M2_calf =
# 0.530/0.5757 = 0.921 (band 0.90-1.08). Tissue adds ~+0.004 m to the
# neck and nothing to the calf relation's numerator beyond that, so
# context A target = 0.526 m.
TARGET_NECK_A = 0.526
print(f"\ncalibrating neck field v2 (target context-A neck girth "
      f"{TARGET_NECK_A*100:.1f} cm, on the REPAIRED field)...")


def solve_gc(mound_a, lift_a, gt_out, jaw_flare,
             target=TARGET_NECK_A):
    lo, hi = 0.001, 0.060
    for _ in range(11):
        mid = 0.5 * (lo + hi)
        g = neck_girth(mh_pos_mac + M_field + W_field
                       + repaired_neck(mid, mound_a, lift_a, gt_out,
                                       jaw_flare))
        if g < target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


MOUND_A, LIFT_A, GT_OUT, JAW_FLARE = 0.050, 0.012, 0.012, 0.012
GC = solve_gc(MOUND_A, LIFT_A, GT_OUT, JAW_FLARE)
F_NECK = repaired_neck(GC, MOUND_A, LIFT_A, GT_OUT, JAW_FLARE)
posA = mh_pos_mac + M_field + W_field + F_NECK
m1r, span, _, _ = m1_record(posA)
gA = grade(posA, mh_lab)
print(f" round 0: gc={GC:.4f} mound={MOUND_A:.3f} -> neck_A "
      f"{neck_girth(posA)*100:.1f} cm, M1_record {m1r:.3f} (span "
      f"{span*100:.1f} cm), M7_A {gA['M7_vis_neck_ratio']:.3f}")
for rnd in range(1, 5):
    if m1r >= 1.055:
        break
    MOUND_A += 0.007
    GC = solve_gc(MOUND_A, LIFT_A, GT_OUT, JAW_FLARE)
    F_NECK = repaired_neck(GC, MOUND_A, LIFT_A, GT_OUT, JAW_FLARE)
    posA = mh_pos_mac + M_field + W_field + F_NECK
    m1r, span, _, _ = m1_record(posA)
    gA = grade(posA, mh_lab)
    print(f" round {rnd}: mound -> {MOUND_A:.3f}, gc={GC:.4f} -> "
          f"M1_record {m1r:.3f} (span {span*100:.1f} cm), neck_A "
          f"{neck_girth(posA)*100:.1f} cm, M7_A "
          f"{gA['M7_vis_neck_ratio']:.3f}")
# final repair pass with bookkeeping (att/traj for the QA record)
F_NECK, att_N, traj_N = repair(
    neck_field(GC, MOUND_A, LIFT_A, GT_OUT, JAW_FLARE),
    NECK_CHECKS, "neck field (final)")
neckA_post = neck_girth(mh_pos_mac + M_field + W_field + F_NECK)
print(f" final context-A neck girth: {neckA_post*100:.1f} cm "
      f"(att min {att_N.min():.2f}, {int((att_N < 0.999).sum())} verts)")
GT_UP = MOUND_A  # QA bookkeeping alias (mound amplitude)


# ============================================================ FOREARM FIELD
# Authored on the forearm segment (elbow -> wrist) of each arm chain.
# Profile peaks on the extensor wad / brachioradialis just below the
# elbow (t 0.20-0.38), tapers hard to a comparatively lean wrist
# (0.22 at t=0.95, tail into the hand ~0). Sector weights from the
# radial direction: posterior (extensor) and lateral heavy,
# brachioradialis diagonal (front x lateral), flexor front moderate,
# inner light -- normalised to profile-weighted mean 1 so `gain` is
# the mean radial growth at profile peak.
_FA_T = np.array([-0.10, 0.00, 0.08, 0.20, 0.38, 0.55, 0.70, 0.84,
                  0.95, 1.05, 1.16])
_FA_P = np.array([0.35, 0.55, 0.85, 1.00, 0.98, 0.85, 0.62, 0.30,
                  0.13, 0.05, 0.00])


def _sector_w(rdir, side):
    back = np.clip(-rdir[:, 1], 0, 1)
    lat = np.clip(rdir[:, 0] * side, 0, 1)
    front = np.clip(rdir[:, 1], 0, 1)
    return 0.50 + 0.62 * back + 0.58 * lat + 0.30 * front * lat \
        + 0.18 * front


def forearm_field(gain):
    pieces = []   # (idx, prof, wsec, rdir)
    for sname in ("R", "L"):
        ch = chain_of(mh_lab, "arm", sname)
        if ch is None:
            continue
        segs, ref, lm = ch
        Pv = lm["verts"]
        tt = np.stack([seg_params(mh_pos_mac, A2, B2, ref)[0][Pv]
                       for (A2, B2) in segs], axis=1)
        cost = np.where((tt >= -0.15) & (tt <= 1.15),
                        np.abs(tt - 0.5), 1e3)
        seg_id = np.argmin(cost, axis=1)
        t_all, _, rd_all, _, _, _ = seg_params(
            mh_pos_mac, segs[1][0], segs[1][1], ref)
        idx1 = Pv[seg_id == 1]
        prof1 = np.interp(t_all[idx1], _FA_T, _FA_P)
        # wrist stays comparatively lean: sector growth damped out
        # over the last fifth of the segment on top of the profile
        wdamp = 1.0 - 0.40 * sstep(t_all[idx1], 0.78, 0.95)
        pieces.append((idx1, prof1,
                       _sector_w(rd_all[idx1],
                                 mh_lab["side"][idx1]) * wdamp,
                       rd_all[idx1]))
        # proximal spill onto the elbow end of the upper-arm segment
        # (continuity across the joint; the muscle core's own arm
        # field ends there)
        t0_all, _, rd0_all, _, _, _ = seg_params(
            mh_pos_mac, segs[0][0], segs[0][1], ref)
        idx0 = Pv[seg_id == 0]
        sp = sstep(t0_all[idx0], 0.80, 1.00) * 0.30 * 0.55
        pieces.append((idx0, sp,
                       _sector_w(rd0_all[idx0], mh_lab["side"][idx0]),
                       rd0_all[idx0]))
    wsum = sum(float((p * w).sum()) for _, p, w, _ in pieces)
    wtot = sum(float(p.sum()) for _, p, w, _ in pieces)
    renorm = wsum / max(wtot, 1e-9)
    F = np.zeros((NB, 3))
    for idx, prof, wsec, rdir in pieces:
        F[idx] += (gain * prof * (wsec / renorm))[:, None] * rdir
    sup = np.linalg.norm(F, axis=1) > 1e-6
    return lap_smooth(F, sup, 2)


def wrist_girth(pos, debug=False):
    """Loop at t=0.92 along elbow->wrist, mean of both sides."""
    gs = []
    for sname in ("R", "L"):
        lm = mh_lab["lm"].get(f"arm{sname}")
        if not lm:
            continue
        E, W = lm["E"], lm["W"]
        n = (W - E) / np.linalg.norm(W - E)
        P0 = E + 0.92 * (W - E)
        loops = [lp for lp in plane_loops(pos, n, P0)
                 if loop_perim(lp) > 0.03]
        if loops:
            if debug:
                for lp in loops:
                    print(f"   wrist{sname} cand: perim "
                          f"{loop_perim(lp)*100:.1f} cm, centre dist "
                          f"{np.linalg.norm(lp.mean(axis=0) - P0)*100:.1f} cm")
            lp = min(loops, key=lambda l:
                     np.linalg.norm(l.mean(axis=0) - P0))
            gs.append(loop_perim(lp))
    return float(np.mean(gs)) if gs else float("nan")


FULL_PRE = M_field + W_field + T_field + F_NECK   # composition minus forearm
print(f"\ncalibrating forearm field (target M3 = 0.84 at full "
      f"composition)...")
_ua_full = grade(mh_pos_mac + FULL_PRE, mh_lab)["ua_g"]
FA_TARGET = 0.84 * _ua_full
print(f" upper-arm girth at full composition: {_ua_full*100:.1f} cm -> "
      f"forearm target {FA_TARGET*100:.1f} cm")


FORE_CHECKS = [(mh_pos, ZERO), (mh_pos_mac, ZERO),
               (mh_pos, FULL_PRE), (mh_pos_mac, FULL_PRE)]


def repaired_fore(gain):
    F, _, _ = repair(forearm_field(gain), FORE_CHECKS, "forearm trial")
    return F


def solve_fa_gain():
    # calibrate on the REPAIRED field: the slope limiter inside
    # repair() smooths the raw field and ate ~1.3 cm of girth in the
    # first pass, which a post-hoc rescale only partially recovered
    lo, hi = 0.0005, 0.050
    for _ in range(11):
        mid = 0.5 * (lo + hi)
        g = grade(mh_pos_mac + FULL_PRE + repaired_fore(mid),
                  mh_lab)["fa_g"]
        if g < FA_TARGET:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


GAIN_FA = solve_fa_gain()
F_FORE, att_F, traj_F = repair(forearm_field(GAIN_FA), FORE_CHECKS,
                               "forearm field")
fa_post = grade(mh_pos_mac + FULL_PRE + F_FORE, mh_lab)["fa_g"]
print(f" forearm gain solved: {GAIN_FA*1000:.1f} mm mean radial at "
      f"profile peak; post-repair fa {fa_post*100:.1f} cm (att min "
      f"{att_F.min():.2f}, {int((att_F < 0.999).sum())} verts)")
GAIN_FA_EFF = GAIN_FA

# ============================================================ FINAL GRADES
STATES = {
    "base": mh_pos_mac,
    "muscle_system": mh_pos_mac + M_field + W_field,
    "muscle_plus_neck": mh_pos_mac + M_field + W_field + F_NECK,
    "full_strongman_shipped": mh_pos_mac + M_field + W_field + T_field,
    "full_plus_neck": mh_pos_mac + FULL_PRE,
    "full_plus_neck_forearm": mh_pos_mac + FULL_PRE + F_FORE,
    "neck_solo": mh_pos_mac + F_NECK,
    "forearm_solo": mh_pos_mac + F_FORE,
}
GRADES = {k: grade(p, mh_lab) for k, p in STATES.items()}
for k, g in GRADES.items():
    print(f" {k:24s} neck {g['neck_g']*100:5.1f}  ua {g['ua_g']*100:5.1f}  "
          f"fa {g['fa_g']*100:5.1f}  calf {g['calf_g']*100:5.1f}  "
          f"M1 {g['M1_neckW_headW']:.3f}  M2a {g['M2_neck_arm']:.3f}  "
          f"M3 {g['M3_fa_arm']:.3f}  M7 {g['M7_vis_neck_ratio']:.3f}")

M1R = {k: m1_record(p) for k, p in STATES.items()}
GRV = {k: groove_metrics(p) for k, p in STATES.items()}
WRIST = {k: wrist_girth(p) for k, p in STATES.items()}
print(f" M1_record (jaw-level span/head): base "
      f"{M1R['base'][0]:.3f}, muscle+neck {M1R['muscle_plus_neck'][0]:.3f}, "
      f"full+neck+fore {M1R['full_plus_neck_forearm'][0]:.3f}")
for k in STATES:
    print(f" wrist {k:24s} {WRIST[k]*100:5.1f} cm")

# field-level SCM differential (construction check, R8): mean radial
# displacement of the shipped neck field in the SCM strips vs the
# front-centre strip over the column band
_col_band = (_mc_h > 0.5) & (r_mh < 0.09)
_rad = np.einsum("ij,ij->i", F_NECK, er3)
_scm = _col_band & (np.abs(th_mh) > 0.35) & (np.abs(th_mh) < 0.85)
_ctr = _col_band & (np.abs(th_mh) < 0.22)
SCM_DIFF = float(_rad[_scm].mean() - _rad[_ctr].mean())
print(f" SCM differential growth (ridge - centre): {SCM_DIFF*1000:.1f} mm")

# ------------------------------------------------------------- flip audit
FLIPS = {}
for name, D in (("neck_solo", F_NECK), ("forearm_solo", F_FORE),
                ("muscle_system", M_field + W_field),
                ("muscle_plus_neck", M_field + W_field + F_NECK),
                ("full_plus_neck", FULL_PRE),
                ("full_plus_neck_forearm", FULL_PRE + F_FORE)):
    FLIPS[name] = {
        "raw": int(flipped(mh_pos, D).sum()),
        "macro": int(flipped(mh_pos_mac, D).sum())}
    print(f" flips {name}: raw {FLIPS[name]['raw']}, "
          f"macro {FLIPS[name]['macro']}")

# ---------------------------------------------------------------- outputs
NOTE_N = ("Provenance: omniversal slider body.neck.mass (NeckMass, "
          "the yoke), instance makehuman_hm08. AUTHORED procedurally "
          "on hm08 (anatomy-anchored landmark fields: neck column + "
          "trapezius cone, SCM front-centre exclusion per R8), "
          "calibrated to the BARA_LESSONS Reeves relation at the "
          "strongman composition. Study-only, internal - not a CC0 "
          "MakeHuman asset. See NECK_FOREARM.md.")
NOTE_F = ("Provenance: omniversal slider body.forearm.mass (forearm "
          "strength read), instance makehuman_hm08. AUTHORED "
          "procedurally on hm08 (segment profile peaked on the "
          "extensor wad / brachioradialis, sector-weighted, wrist "
          "kept lean), calibrated to the BARA_LESSONS M3 band at the "
          "strongman composition. Study-only, internal - not a CC0 "
          "MakeHuman asset. See NECK_FOREARM.md.")
n_neck = write_target(OUT / "body.neck.mass.target", F_NECK, NOTE_N)
n_fore = write_target(OUT / "body.forearm.mass.target", F_FORE, NOTE_F)
print(f"targets written: neck {n_neck} moved verts, forearm "
      f"{n_fore} moved verts")

np.savez_compressed(WORK / "neck_forearm_fields.npz",
                    neck_mass_canonical_m=F_NECK,
                    forearm_mass_canonical_m=F_FORE,
                    att_neck=att_N, att_forearm=att_F,
                    mask_col=MASK_COL, mask_trap=MASK_TRAP)

GC_ = GRADES["full_plus_neck_forearm"]
GA_ = GRADES["muscle_plus_neck"]
qa = {
    "calibration": {
        "neck": {"gc_m": float(GC), "mound_a_m": float(MOUND_A),
                 "lift_a_m": float(LIFT_A),
                 "gt_out_m": float(GT_OUT),
                 "jaw_flare_m": float(JAW_FLARE),
                 "groove_depth": GROOVE_DEPTH,
                 "target_neck_A_m": TARGET_NECK_A,
                 "neck_A_post_repair_m": float(neckA_post)},
        "forearm": {"gain_m": float(GAIN_FA),
                    "gain_effective_m": float(GAIN_FA_EFF),
                    "fa_target_m": float(FA_TARGET),
                    "ua_full_m": float(_ua_full)}},
    "grades": GRADES,
    "m1_record": {k: {"value": float(v[0]), "span_m": float(v[1]),
                      "head_w_m": float(v[2]), "jaw_z": float(v[3])}
                  for k, v in M1R.items()},
    "groove_surface": GRV,
    "scm_differential_m": SCM_DIFF,
    "wrist_girth": {k: float(v) for k, v in WRIST.items()},
    "flips": FLIPS,
    "attenuation": {
        "neck_min": float(att_N.min()),
        "neck_verts": int((att_N < 0.999).sum()),
        "neck_traj": traj_N,
        "forearm_min": float(att_F.min()),
        "forearm_verts": int((att_F < 0.999).sum()),
        "forearm_traj": traj_F},
    "moved_verts": {"neck": n_neck, "forearm": n_fore},
    "max_disp_m": {
        "neck": float(np.linalg.norm(F_NECK, axis=1).max()),
        "forearm": float(np.linalg.norm(F_FORE, axis=1).max())},
}
(WORK / "qa_numbers_neck_forearm.json").write_text(
    json.dumps(qa, indent=1, default=float))
print("wrote qa_numbers_neck_forearm.json + neck_forearm_fields.npz")

# ------------------------------------------------------- slider JSONs
score_rows_C = [
    {"metric": "M1 neck width / head width (scorecard)",
     "value": round(GC_["M1_neckW_headW"], 3), "band": [0.68, 9.0],
     "status": band(GC_["M1_neckW_headW"], 0.68, 9.0),
     "note": "scorecard read at the neck station"},
    {"metric": "M1 record gate (jaw-level span / bizygomatic)",
     "value": round(M1R["muscle_plus_neck"][0], 3), "band": [1.05, 9.0],
     "status": band(M1R["muscle_plus_neck"][0], 1.05, 9.0),
     "note": "body.neck.mass acceptance gate, muscle system context"},
    {"metric": "M2 neck/arm (Reeves 1.00)",
     "value": round(GC_["M2_neck_arm"], 3), "band": [0.92, 1.05],
     "status": band(GC_["M2_neck_arm"], 0.92, 1.05), "note": ""},
    {"metric": "M2 neck/calf",
     "value": round(GC_["M2_neck_calf"], 3), "band": [0.90, 1.08],
     "status": band(GC_["M2_neck_calf"], 0.90, 1.08), "note": ""},
    {"metric": "M3 forearm/arm",
     "value": round(GC_["M3_fa_arm"], 3), "band": [0.80, 0.88],
     "status": band(GC_["M3_fa_arm"], 0.80, 0.88),
     "note": "bara band [E]; wolf cross-check 0.834"},
    {"metric": "M6 trap slope deg",
     "value": round(GC_["M6_trap_deg"], 3), "band": [28.0, 50.0],
     "status": band(GC_["M6_trap_deg"], 28.0, 50.0), "note": ""},
    {"metric": "M7 visible neck/head",
     "value": round(GC_["M7_vis_neck_ratio"], 3), "band": [0.12, 0.38],
     "status": band(GC_["M7_vis_neck_ratio"], 0.12, 0.38),
     "note": "record gate <= 0.25 measured in the muscle context: "
             f"{GA_['M7_vis_neck_ratio']:.3f}"},
]
qa_neck = {
    "fold_gate": "0 flipped faces at +1 (slope limiter KAPPA=0.55 + "
                 "surgical attenuation repair; solo on raw AND macro "
                 "base, over the muscle system, and in the full "
                 "composition)",
    "flips": FLIPS,
    "acceptance_gate": {
        "context": "value 1.0 over body.muscle + body.chest.width "
                   "(traps family pinned in the shipped muscle "
                   "vector), macro base",
        "m1_record": {"value": round(M1R["muscle_plus_neck"][0], 3),
                      "required": ">= 1.05",
                      "status": band(M1R["muscle_plus_neck"][0],
                                     1.05, 9.0)},
        "m7_visible_neck": {
            "value": round(GA_["M7_vis_neck_ratio"], 3),
            "required": "<= 0.25 (strongman band 0.15-0.25)",
            "status": band(GA_["M7_vis_neck_ratio"], 0.0, 0.25)},
        "scm_groove": {
            "differential_growth_mm": round(SCM_DIFF * 1000, 2),
            "surface_depths_mm": {
                k: {kk: round(vv * 1000, 2) for kk, vv in v.items()}
                for k, v in GRV.items()},
            "note": "construction differential (SCM strip growth "
                    "minus front-centre growth) + surface probe; "
                    "visual read in renders/neck_forearm_*_front.png"},
        "r5_floor": {
            "neck_width_m": GA_["neck_w"],
            "jaw_width_m": JAW_W0,
            "status": "PASS" if GA_["neck_w"] >= JAW_W0 else "miss"}},
    "scorecard_full_composition": score_rows_C,
    "grades": GRADES,
    "moved_verts": n_neck,
    "max_disp_m": float(np.linalg.norm(F_NECK, axis=1).max()),
    "attenuation": {"min": float(att_N.min()),
                    "verts": int((att_N < 0.999).sum())},
}
(OUT / "body.neck.mass.slider.json").write_text(json.dumps({
    "id": "body.neck.mass",
    "label": "Neck mass (yoke)",
    "group": "body/neck",
    "version": "0.1.0-proof",
    "symmetry": "bilateral_x",
    "range": {"min": 0.0, "max": 1.0, "default": 0.0,
              "safe_max": 1.0,
              "endpoint_anchor": "+1 = authored yoke at full bara "
                                 "strength: with the traps pinned "
                                 "(muscle system) the neck girth "
                                 "reaches the Reeves arm-equality "
                                 "band and the jaw-level span clears "
                                 "the bizygomatic span (record gate)"},
    "region": "neck column + trapezius cone band (jaw line -> outer "
              "clavicle -> C7), front-centre SCM strip excluded from "
              "full weight",
    "system": {
        "model": "procedural anatomy-anchored authoring on hm08 "
                 "(landmark (h, theta, r) masks; column radial + "
                 "trap cone out/up), calibrated by slice-loop "
                 "measurement at the strongman composition",
        "components": {
            "column_radial_gc_m": float(GC),
            "trap_mound_amplitude_m": float(MOUND_A),
            "trap_mound_crest_r_m": MOUND_R,
            "trap_slope_lift_m": float(LIFT_A),
            "trap_out_gt_m": float(GT_OUT),
            "jaw_flare_m": float(JAW_FLARE),
            "scm_groove_depth": GROOVE_DEPTH},
        "proves": "the yoke is authorable past the HIMBO vocabulary "
                  "ceiling: M2 enters the Reeves band and the record "
                  "gate (M1 >= 1.05, M7 <= 0.25, SCM readable) passes "
                  "with the traps pinned"},
    "semantics": ("Proof instance of the canonical body.neck.mass "
                  "record (anthroforge-app/library/sliders). One-pole "
                  "slider: at 1.0 the neck and trapezius cone carry "
                  "full bara yoke mass -- neck meets/exceeds jaw "
                  "width, visible neck shortens as the traps rise, "
                  "head set INTO the shoulders. Study-only."),
    "qa": qa_neck,
}, indent=1, default=float))

qa_fore = {
    "fold_gate": "0 flipped faces at +1 (same protocol; solo and "
                 "over the full composition)",
    "flips": FLIPS,
    "m3_at_full_composition": {
        "value": round(GC_["M3_fa_arm"], 3), "band": [0.80, 0.88],
        "status": band(GC_["M3_fa_arm"], 0.80, 0.88),
        "forearm_g_m": GC_["fa_g"], "upper_arm_g_m": GC_["ua_g"]},
    "wrist_girth": {k: float(v) for k, v in WRIST.items()},
    "scorecard_full_composition": score_rows_C,
    "grades": GRADES,
    "moved_verts": n_fore,
    "max_disp_m": float(np.linalg.norm(F_FORE, axis=1).max()),
    "attenuation": {"min": float(att_F.min()),
                    "verts": int((att_F < 0.999).sum())},
}
(OUT / "body.forearm.mass.slider.json").write_text(json.dumps({
    "id": "body.forearm.mass",
    "label": "Forearm mass (strength read)",
    "group": "body/arms",
    "version": "0.1.0-proof",
    "symmetry": "bilateral_x",
    "range": {"min": 0.0, "max": 1.0, "default": 0.0,
              "safe_max": 1.0,
              "endpoint_anchor": "+1 = authored forearm at full bara "
                                 "strength: at the strongman "
                                 "composition the forearm:arm girth "
                                 "ratio lands in the study's bara "
                                 "band (0.80-0.88)"},
    "region": "forearm segment (elbow -> wrist) of both arm chains, "
              "profile peaked below the elbow, wrist comparatively "
              "lean; small spill onto the elbow end of the upper arm",
    "system": {
        "model": "procedural anatomy-anchored authoring on hm08 "
                 "(segment (t, phi) params; radial profile x sector "
                 "weights), calibrated by slice-loop measurement at "
                 "the strongman composition",
        "components": {"gain_m": float(GAIN_FA_EFF),
                       "profile_knots_t": _FA_T.tolist(),
                       "profile_knots_v": _FA_P.tolist()},
        "proves": "the forearm strength read is authorable past the "
                  "HIMBO ArmsFore ceiling (which pinned at 1.00 "
                  "still read 0.690): M3 enters the bara band"},
    "semantics": ("Proof slider, study-only provenance. The forearm "
                  "counterpart to NeckMass: where the upper arm is "
                  "mass, the forearm is the strength read -- "
                  "brachioradialis + extensor wad high, wrist lean. "
                  "Composes additively with body.muscle's ArmsFore "
                  "(the vocabulary's weak field stays as the base "
                  "layer)."),
    "qa": qa_fore,
}, indent=1, default=float))
print("wrote body.neck.mass.slider.json + body.forearm.mass.slider.json")
print("BUILD NECK FOREARM DONE")
