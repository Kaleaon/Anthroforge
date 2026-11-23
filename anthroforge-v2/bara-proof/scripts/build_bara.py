#!/usr/bin/env python3
"""BARA STRONGMAN slider proof for AnthroForge (Joe, Nov 12, 2026:
"look up further lessons for bara... and apply it").

Builds the strongman-pole bara build on the MakeHuman hm08 base as a
TWO-VECTOR slider pair, per the doctrine of ../BARA_LESSONS.md section 6:

  body.muscle            -- the Muscle vector: yoke FIRST (neck+traps are
                            the primary size signal, R4), triceps-led arm
                            mass (R13), forearm strength read (R14),
                            lat/pec barrel (R3/R9/R11), legs pinned with
                            the yoke (R19).
  body.tissue.strongman  -- the Tissue vector at the strongman cell:
                            fat layer 15-25% over the muscle (section 1);
                            power belly = built core + fat + pelvic tilt,
                            sitting LOW, chest ring always out-ringing
                            the waist ring (R17, Shaw anchor 1.28).

Source fields: HIMBO granular vocabulary (126 sliders, learned library)
composed on the HIMBO base per BARA_LESSONS section 6C's shared
MuscleVector + the section 4.2 Sen preset (the study's strongman
reference implementation), transferred to hm08 with the v1/v4 kernel
machinery EXTENDED to limbs: torso (h, theta) kernel + per-segment limb
kernels (t, phi) on arm/leg chains. The belly component is NOT
re-derived: it reuses the accepted v4 whole-torso system (belly core
B*D3 + D_posture) at the strongman tissue setting (tau solved so the
chest:waist ring ratio stays >= 1.30 on the composed build).

Joe's additions (Nov 12, 2026, mid-build): (1) chest BROADNESS is its
own editable component -- body.chest.width (lateral frame + lat sweep),
distinct from chest depth (SterDepth, in body.muscle) and pec mass;
measured as M13 (chest loop width, base vs +1). (2) Fat must WRAP
front-to-sides: the tissue layer's angular profile is QA'd front /
flank / back at chest and belly bands (side-mass check), with a
pre-registered flank correction if the sides are under-weighted.

Atomic Muscle was attempted as a second source and is NOT transferred:
its base positions are locked in a FO4 BSTriShape NIF (half-float
interleaved vertex stream) that defeats the in-house extractors --
three routes tried (32-byte f32 stream scan, .tri position probe,
Skyrim NiTriShape parser). Its decode stats are used as a calibration
cross-check only. This matches AM_VS_HIMBO takeaway 1: the granular
vocabulary is the instrument; the two AM macros are the anti-pattern.

QA: 0 flipped faces at +1 (hard gate, slope limiter + attenuation
repair as v4, checked on BOTH the raw target base and the MPFB macro
base, for muscle alone, tissue alone, and the pair composed); 5-fold
kernel CV per field; the BARA_LESSONS 12-metric scorecard measured on
the exported-geometry equivalent (macro base + targets) with mesh-plane
slice loops.

PROVENANCE: study-only. Every field derives from sliders decoded from
Joe's own legitimately obtained mod files (learned library); only
aggregate displacement statistics and our own composed fields ship.
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
LEARNED = Path.home() / "workspace/character_assets/learned"
HIMBO_DIR = (Path.home() / "workspace/character_assets/_himbo_work/"
             "CalienteTools/BodySlide/ShapeData/HIMBO")
sys.path.insert(0, str(LEARNED / "tools"))
from osdparse import load_osd  # noqa: E402

MPFB_ZIP = Path.home() / "workspace/stick-figure-avatar/photoreal/tools/mpfb2.zip"
DM_M = 0.1          # MakeHuman decimetre -> metre
SK = 0.01428        # Skyrim unit -> metre (v1-v4 convention)
BODY_END = 13380    # hm08 body verts (helpers after)

KAPPA = 0.55        # slope-limiter budget (v4)
ATT_BAD, ATT_RING, ATT_FLOOR = 0.82, 0.94, 0.10


def sstep(x, a, b):
    t = np.clip((np.asarray(x, float) - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


# ---------------------------------------------------------------- loads
corr = np.load(FP / "work/correspondence.npz")
B_CORE = corr["mh_mask"].astype(np.float64)          # v4 belly core mask
h_star = float(corr["h_star"])
mh_crotch, mh_neck = [float(x) for x in corr["mh_landmarks"]]
navel_mh = int(corr["navel_mh"])
mh_tris = corr["mh_tris"]
L_mh = mh_neck - mh_crotch
D3 = np.load(FP / "work/belly_v3.npz")["delta_v3_canonical_m"].astype(np.float64)
_v4 = np.load(FP / "work/belly_v4.npz")
D_POSTURE = _v4["d_posture_canonical_m"].astype(np.float64)
W_TORSO_V4 = _v4["torso_weight"].astype(np.float64)

with zipfile.ZipFile(MPFB_ZIP) as z:
    _lines = z.read("mpfb/data/3dobjs/base.obj").decode().splitlines()
_obj = np.array([[float(x) for x in l.split()[1:4]]
                 for l in _lines if l.startswith("v ")])
mh_pos = np.stack([_obj[:, 0], _obj[:, 2], _obj[:, 1]], axis=1) * DM_M
_mac = np.load(FP / "work/mh_macro_base.npz")["pos_canonical_m"]
# FRAME FIX (found in bara QA): the saved macro base lives in its own
# frame (z: feet 0 -> crown 1.659) while base.obj / correspondence /
# D3 / posture / W all live in the raw obj frame (z: -0.817 -> 0.849).
# v4 never noticed because it only used the macro base for
# translation-invariant flip checks. Align per-axis by min/max into
# the raw frame before any landmark/girth use.
mh_pos_mac = mh_pos.copy()
_mb = _mac.copy()
for _ax in range(3):
    r0, r1 = mh_pos[:BODY_END, _ax].min(), mh_pos[:BODY_END, _ax].max()
    m0, m1 = _mb[:, _ax].min(), _mb[:, _ax].max()
    _mb[:, _ax] = r0 + (_mb[:, _ax] - m0) * (r1 - r0) / (m1 - m0)
print("macro->raw alignment: median |delta| per axis (the macro "
      "reshaping itself):",
      np.round(np.median(np.abs(_mb - mh_pos[:BODY_END]), axis=0), 4))
mh_pos_mac[:len(_mb)] = _mb
NB = len(mh_pos)
FACES_B = mh_tris[np.all(mh_tris < BODY_END, axis=1)]
print(f"hm08: {NB} verts, torso L={L_mh:.4f} m, navel h*={h_star:.3f}")


def extract_base_positions(data, expect_min_verts):
    """Embedded vertex stream scan, copied verbatim from
    first-proof/scripts/build_belly_v4.py (itself from
    crosscheck_fields.py), where it recovered the HIMBO 9,346-vert
    base exactly: 32-byte vertex records, positions in floats 0-2,
    float 3 a near-zero pad."""
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


_MISSED_BLOCKS = set()


def hi_diff(name):
    blk = hi_blocks.get(f"HIMBO - Body{name}")
    if blk is None:
        # A miss used to return zeros SILENTLY -- that is how the
        # NeckMass field was dropped from the shipped body.muscle
        # (hi_diff("Weight") vs the actual block 'Weight 0 to 1';
        # see ../FIX_NECK_FIELD.md). Warn loudly, once per name.
        if name not in _MISSED_BLOCKS:
            _MISSED_BLOCKS.add(name)
            print(f"WARNING: hi_diff({name!r}) -- block "
                  f"'HIMBO - Body{name}' not in the Vanilla OSD; "
                  "composing ZEROS for this slider", file=sys.stderr)
        return np.zeros((NH, 3))
    d = np.zeros((NH, 3))
    d[blk["indices"]] = blk["diffs"]
    return d


# ------------------------------------------------------- shared geometry
def compute_axis(pos, gate=None):
    """v4's compute_axis verbatim (incl. the 5-tap axis smoothing)."""
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
    """v4's neck_base verbatim: width profile of r<0.23-gated verts;
    neck = first run of 3 bands above the chest peak narrower than
    55% of chest width (arm/hands excluded by the r gate)."""
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
    print(f"{label}: chest {C[chest_i]:.3f} m (W={Wd[chest_i]:.3f} m), "
          f"neck base {neck:.4f} m")
    return neck


def torso_params(pos, crotch=None, neck=None, label="mesh"):
    """(h, theta, r, axis_xy, crotch, neck, L) in v4's exact convention:
    theta = atan2(rel_x, rel_y) (0 = front), h = (z-crotch)/(neck-crotch)
    with crotch/neck detected by v4's crotch_of/neck_base when not
    supplied."""
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
    """v4's kernel evaluation pattern: direct pairwise Gaussian in
    (a, b) space, chunked queries, plain normalisation (region weights
    gate where the field applies)."""
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
    """5-fold CV over informative samples (v4 protocol, seed
    20261112): median + p95 absolute error, cm."""
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
    """Geometric region labels + limb landmarks. Works on any of our
    bases (metres, z-up, A-pose ~45 deg both). Arms hang lateral of the
    torso radius profile; legs split by side below the crotch.
    body_mask: verts eligible for limb labels/landmarks (hm08 helpers
    excluded); defaults to all."""
    if body_mask is None:
        body_mask = np.ones(len(pos), bool)
    z = pos[:, 2]
    ctr, axis = compute_axis(pos, np.ones(len(pos), bool))
    ax = np.stack([np.interp(z, ctr, axis[:, 0]),
                   np.interp(z, ctr, axis[:, 1])], axis=1)
    rel = pos[:, :2] - ax
    r = np.hypot(rel[:, 0], rel[:, 1])
    # torso radius profile (92nd pct per 1 cm band)
    edges = np.arange(z.min() - 0.005, z.max() + 0.011, 0.01)
    prof = np.full(len(edges) - 1, np.nan)
    for i, (a, b) in enumerate(zip(edges[:-1], edges[1:])):
        m = (z >= a) & (z < b) & (r < 0.23)   # r gate excludes arms/hands
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
    # ---- limb landmarks per side
    lm = {}
    for sgn, sname in ((1.0, "R"), (-1.0, "L")):
        am = arm & (side == sgn)
        if am.sum() > 60:
            P = pos[am]
            c = P.mean(axis=0)
            _, _, vt = np.linalg.svd(P - c, full_matrices=False)
            a = vt[0]
            s = (P - c) @ a
            # orient: the hand end sits farther from the body axis
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
            # radius profile along the PCA line
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
            # elbow = FIRST local minimum of the smoothed radius
            # profile (scanning from the shoulder); wrist = thinnest
            # local minimum after it. A plain argmin over a wide
            # window picks the WRIST as the "elbow" (it is thinner)
            # and a finger web as the "wrist" -- caught in QA when
            # the forearm station read 13 cm on the base mesh.
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
            prof = np.full(nb, np.nan)
            for i in range(nb):
                m = (t >= bins[i]) & (t < bins[i + 1])
                if m.sum() > 3:
                    prof[i] = np.mean(rad[m])
            okb = ~np.isnan(prof)
            prof = np.interp(np.arange(nb), np.where(okb)[0], prof[okb])
            bc = 0.5 * (bins[:-1] + bins[1:])
            klo = bc[(bc > 0.35 * hl) & (bc < 0.65 * hl)]
            knee_t = klo[np.argmin(prof[(bc > 0.35 * hl)
                                        & (bc < 0.65 * hl)])]
            K = P[np.abs(t - knee_t) < 0.04 * hl].mean(axis=0)
            lm[f"leg{sname}"] = {"H": H, "K": K, "A": A,
                                 "span": float(hl), "verts": np.where(lg)[0]}
    lab["lm"] = lm
    return lab


def seg_params(pos, A, B, ref):
    """(t, phi, radial_dir, axis_dir, seg_len) of points wrt segment A->B.
    phi measured from the ref-projected basis (world-consistent, both
    meshes, both sides -- no mirroring anywhere)."""
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


REF_ARM = np.array([0.0, 0.0, 1.0])    # "up" projected perp to arm axis
REF_LEG = np.array([0.0, 1.0, 0.0])    # "forward" projected perp to leg axis


def chain_of(lab, kind, sname):
    lm = lab["lm"].get(f"{kind}{sname}")
    if lm is None:
        return None
    if kind == "arm":
        return [(lm["S"], lm["E"]), (lm["E"], lm["W"])], REF_ARM, lm
    return [(lm["H"], lm["K"]), (lm["K"], lm["A"])], REF_LEG, lm


# ------------------------------------------------------------- the recipes
# Every entry traces to BARA_LESSONS: Sen = section 4.2 strongman preset
# (the study's strongman reference implementation); 6C = section 6C
# shared MuscleVector; rule tags in the proof doc.
#
# Joe's addition (Nov 12, 2026): chest BROADNESS is its own editable
# component, distinct from chest depth and chest mass. The muscle
# system therefore ships as TWO sliders whose +1 sum is the build's
# muscle layer:
#   body.muscle       -- mass/depth/yoke/arms/legs (below)
#   body.chest.width  -- lateral frame + lat sweep (WIDTH_RECIPE)
WIDTH_RECIPE = {
    "TorsoShoulderInc": 0.50,  # ribcage/shoulder frame width (R3)
    "TorsoWidth": 0.95,        # Sen (lateral torso frame)
    "ArmsShoulders": 0.90,     # Sen (group-width cap, R3)
    "TorsoBackShape": 0.85,    # Sen (lat sweep = lateral back mass)
}
MUSCLE_RECIPE = {   # value = slider position 0..1 (of the 0..100 decode)
    # frame support (width proper lives in WIDTH_RECIPE)
    "BodyMass": 0.30,          # Sen (capped vs inflation, H1)
    "TorsoSterHeight": 1.00,   # Sen/Chonky (chest frame, vertical)
    "TorsoSterDepth": 0.90,    # M5 corrective lever (chest depth);
                               # raised 0.60->0.90 after the first
                               # grade showed belly depth > chest depth
    # yoke FIRST (R4) -- NeckMass authored below from the Weight block
    "ArmsTraps": 0.95,         # Sen (trap crease)
    "ArmsTrapsMeat": 1.00,     # Sen pin (R4 carrier)
    "ArmsTrapsPush": 0.90,     # Sen (M6 slope carrier)
    # torso masses (R3/R9/R11)
    "Muscle": 0.80,            # 6C shared vector
    "TorsoMass": 1.00,         # Sen pin (the barrel)
    "TorsoBackSize": 1.00,     # Sen 0.90 -> 1.00 in the M5 corrective
                               # pass (lat depth; see BARA_PROOF.md)
    "TorsoBackSlope": 0.90,    # Chonky (lat/back slope)
    "TorsoBackSerratusMid": 0.40,  # H2 power zone, moderated for tier
    "TorsoLower": 1.00,        # Sen pin (trunk; R18 books with muscle)
    "PecsSize": 1.00,          # Sen (R9 with delts)
    "PecsMass": 1.00,          # Sen 0.90 -> 1.00 in the M5 pass
    "PecsWidth": 1.00,         # Sen
    "PecsLower": 0.70,         # Sen
    "PecsClavicle": 0.70,      # Sen (clavicle burial under traps)
    # arms: delts -> triceps-led (R13: back >= 0.7x biceps) -> forearm (R14)
    "ArmsDelts": 0.90,         # Sen
    "ArmsDeltsBack": 0.60,     # R9 delt-as-one-mass support
    "ArmsDeltsShape": 0.60,    # R9
    "ArmsBiceps": 0.85,        # Sen
    "ArmsBicepsBack": 0.75,    # Sen; R13 fix value from 6B
    "ArmsSide": 0.75,          # 6B triceps carrier
    "ArmsBrachio": 0.80,       # Sen (width between bi/tri)
    "ArmsFore": 1.00,          # Sen pin (R14 forearm lead)
    # legs pinned with the yoke (R19)
    "LegsSize": 1.00,          # Sen pin; 6C legs 100
    "LegsThigh": 1.00,         # Sen pin; 6C
    "LegsGlutes": 0.80,        # Sen
    "LegsCalfSize": 0.80,      # Sen 0.90, trimmed in the M2 pass
    "LegsCalfWidth": 0.75,     # Sen 0.85, trimmed (Reeves relation:
                               # the calf stack out-grew the neck --
                               # see BARA_PROOF.md)
    "ButtBooty": 0.75,         # Sen
    "BubbleButt": 0.40,        # Sen
}
NECK_WEIGHT_VALUE = 0.90       # Sen's Weight 90 -- gated to the neck (A2)

TISSUE_RECIPE = {
    "Chubby": 0.80,            # Sen (the 15-25% layer, R15)
    "TorsoMassSmooth": 0.75,   # Sen (barrel smoothing)
    "TorsoBellyLHandles": 0.60,  # Sen (waist mass inside the ratio budget)
    "PecsSaggy": 0.45,         # Sen (chest tissue, R16 partial relaxation)
    "LegsChubby": 0.75,        # Sen
    "ButtSaggy": 0.25,         # Sen
    "BellySmooth": 0.70,       # Sen (belly continuity under the v4 core)
    "ArmsTrapsValleys": 0.30,  # Sen (definition kept LOW at this cell)
}
# EXCLUDED, with reasons (proof doc): Lean (two-sided, sign-ambiguous
# small end -- v4 precedent), TorsoWaistSize ("Shrink Waist" semantics;
# R18 routes the waist through TorsoLower + LHandles + belly core, no
# shrink term), the HIMBO belly stack TorsoBelly/BellyChub/BellyPot/
# BellyForward (replaced by the v4 system per the brief), SamuelLike
# (body-swap) and BodyMass > 0.30 (inflation, H1), Femme*/genital
# orphans (wrong pattern / out of scope), definition family above
# TrapsValleys (definition is tissue-dial-DOWN at the strongman cell).


def compose(recipe):
    D = np.zeros((NH, 3))
    for name, val in recipe.items():
        D += hi_diff(name) * (val * SK)
    return D


M_src = compose(MUSCLE_RECIPE)
W_src = compose(WIDTH_RECIPE)
T_src = compose(TISSUE_RECIPE)

# NeckMass (authored, study A2): Sen's Weight 0.90 lives mostly in the
# neck (46% of the block's displacement). Gate the Weight block to the
# neck band so the muscle vector gets the yoke without the block's
# known whole-body inflation (Sen's own note: raise NeckMass FIRST).
# FIX (Nov 12, 2026): the block is named 'Weight 0 to 1' in the Vanilla
# OSD; hi_diff("Weight") silently composed zeros and the shipped
# body.muscle carried NO neck field (strongman neck 36.4 cm instead of
# 43.2). See ../FIX_NECK_FIELD.md.
h_hi, th_hi, r_hi, ax_hi, cr_hi, nk_hi, L_hi = torso_params(hi_pos_u * SK)
neck_gate = sstep(h_hi, 0.88, 0.96) * (1 - sstep(h_hi, 1.08, 1.18)) \
    * (1 - sstep(r_hi, 0.13, 0.20))
M_src += hi_diff("Weight 0 to 1") * (NECK_WEIGHT_VALUE * SK) \
    * neck_gate[:, None]
s_hi = L_mh / L_hi
print(f"HIMBO: crotch={cr_hi:.3f} neck={nk_hi:.3f} L={L_hi:.3f} m, "
      f"s_hi={s_hi:.3f}; neck gate verts={int((neck_gate > 0.03).sum())}")
for nm, D in (("muscle core", M_src), ("chest width", W_src),
              ("tissue", T_src)):
    mag = np.linalg.norm(D, axis=1)
    print(f" {nm}: |D| mean {mag.mean()*1000:.2f} mm on support "
          f"{int((mag > 0.0002).sum())}, max {mag.max()*100:.1f} cm")
# AM calibration cross-check (decode stats, AM_VS_HIMBO.md): Nuclear
# BodyBuilder max 5.14 u ~ 7.3 cm / 8,664 verts; Nuka Bull mean 1.89 u.
print(" AM cross-check: NuclearBB max ~7.3 cm; composed HIMBO muscle "
      f"system max {np.linalg.norm(M_src + W_src, axis=1).max()*100:.1f} "
      "cm (granular stack at strongman values vs one macro at full -- "
      "same order)")


# ------------------------------------------------------------ field build
hi_lab = label_mesh(hi_pos_u * SK, cr_hi, nk_hi)
_mh_body_mask = np.zeros(NB, bool)
_mh_body_mask[:BODY_END] = True
mh_lab = label_mesh(mh_pos_mac, mh_crotch, mh_neck, _mh_body_mask)
for tag, lab, pos in (("HIMBO", hi_lab, hi_pos_u * SK),
                      ("hm08", mh_lab, mh_pos_mac)):
    print(f"{tag} labels: torso {int(lab['torso'].sum())} "
          f"arm {int(lab['arm'].sum())} leg {int(lab['leg'].sum())}")
    for k, lm in sorted(lab["lm"].items()):
        pts = [f"{n}({v[0]:+.2f},{v[1]:+.2f},{v[2]:+.2f})"
               for n, v in lm.items() if isinstance(v, np.ndarray)]
        print(f"  {k}: span {lm['span']:.3f} m  " + " ".join(pts))

SIG_H, SIG_A = 0.05, 0.04      # torso kernel (v4)
SIG_U, SIG_ARC = 0.045, 0.04   # limb kernel (metres along axis / arc)
RHO_T, RHO_L = 0.0025, 0.004
cv_report = {}


def torso_field(delta, tag):
    """(h, theta) kernel field of a HIMBO-composed delta, evaluated on
    hm08 -- v4's make_field pattern with SIGNED theta (bara needs front
    pecs distinct from back lats; v4's belly fields folded |theta|).
    Sample gate: v4's torso gate widened for the yoke -- main band
    h<=1.06 & r<0.30, neck band to h=1.18 at r<0.13. Arc uses the
    source's band-mean radius profile, queries included (v4 method)."""
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
    h_mh, th_mh, r_mh, ax_mh, _, _, _ = torso_params(
        mh_pos_mac, mh_crotch, mh_neck, "hm08")
    arc_q = arc(th_mh, h_mh)
    dr, dz = pair_field(hh, arc_s, dr_s, dz_s, h_mh, arc_q,
                        SIG_H, SIG_A)
    dr, dz = dr * s_hi, dz * s_hi
    cv = pair_cv(hh, arc_s, dr_s, dz_s, SIG_H, SIG_A)
    if cv:
        cv_report[f"torso/{tag}"] = cv
    out = np.zeros((NB, 3))
    out[:, 0] = dr * np.sin(th_mh)
    out[:, 1] = dr * np.cos(th_mh)
    out[:, 2] = dz
    return out, (h_mh, r_mh)


def limb_fields(delta, tag):
    """Per (chain, side, segment) (t, phi) kernel fields of a HIMBO
    delta, evaluated on hm08's matching segments. Returns dict
    (kind, side) -> full-length field (zero outside the chain)."""
    out = {}
    for kind in ("arm", "leg"):
        for sname in ("R", "L"):
            ch_s = chain_of(hi_lab, kind, sname)
            ch_t = chain_of(mh_lab, kind, sname)
            if ch_s is None or ch_t is None:
                continue
            segs_s, ref, lm_s = ch_s
            segs_t, _, lm_t = ch_t
            field = np.zeros((NB, 3))
            for si, ((As, Bs), (At, Bt)) in enumerate(zip(segs_s, segs_t)):
                Pv = lm_s["verts"]
                ts, ps, _, _, Ls, _ = seg_params(hi_pos_u * SK, As, Bs, ref)
                # source verts of this chain assigned to this segment
                assign = np.zeros(len(Pv), bool)
                # assignment by nearest segment in t-space: recompute
                # both segments' t and pick the one whose [t] is closer
                # to [0,1]
                tt = []
                for (A2, B2) in segs_s:
                    tt.append(seg_params(hi_pos_u * SK, A2, B2, ref)[0][Pv])
                tt = np.stack(tt, axis=1)
                cost = np.where((tt >= -0.15) & (tt <= 1.15),
                                np.abs(tt - 0.5), 1e3)
                assign = np.argmin(cost, axis=1) == si
                idx = Pv[assign]
                if len(idx) < 25:
                    continue
                t_s, p_s, rd_s, ah_s, _, rl_s = seg_params(
                    hi_pos_u * SK, As, Bs, ref)
                t_s, p_s = t_s[idx], p_s[idx]
                d = delta[idx]
                dr_s = (d * seg_params(hi_pos_u * SK, As, Bs, ref)[2][idx]
                        ).sum(axis=1)
                ds_s = d @ ah_s
                ok = (t_s > -0.12) & (t_s < 1.18)
                idx, t_s, p_s, dr_s, ds_s = idx[ok], t_s[ok], p_s[ok], \
                    dr_s[ok], ds_s[ok]
                rl_s_all = seg_params(hi_pos_u * SK, As, Bs, ref)[5][idx]
                # arc from the SOURCE segment's band-mean radius
                # profile (v4 torso convention), queries included
                tb = np.linspace(-0.1, 1.15, 13)
                rmean = np.array([
                    rl_s_all[(t_s >= tb[i]) & (t_s < tb[i + 1])].mean()
                    if ((t_s >= tb[i]) & (t_s < tb[i + 1])).sum() > 4
                    else max(rl_s_all.mean(), 0.02) for i in range(12)])
                tctr = 0.5 * (tb[:-1] + tb[1:])
                arc_s = p_s * np.interp(t_s, tctr, rmean)
                # target verts of this chain/segment
                Pv_t = lm_t["verts"]
                tt_t = []
                for (A2, B2) in segs_t:
                    tt_t.append(seg_params(mh_pos_mac, A2, B2, ref)[0][Pv_t])
                tt_t = np.stack(tt_t, axis=1)
                cost_t = np.where((tt_t >= -0.15) & (tt_t <= 1.15),
                                  np.abs(tt_t - 0.5), 1e3)
                idx_t = Pv_t[np.argmin(cost_t, axis=1) == si]
                t_t, p_t, rd_t, ah_t, Lt, rl_t = seg_params(
                    mh_pos_mac, At, Bt, ref)
                t_t, p_t, rd_t, rl_t = t_t[idx_t], p_t[idx_t], \
                    rd_t[idx_t], rl_t[idx_t]
                s_seg = Lt / Ls
                # radial scale = target/source BASE radius ratio of
                # the segment (preserve the RELATIVE thickening);
                # axial scale = length ratio. A single length ratio
                # (first version) over-amplified the calf x1.9: the
                # Skyrim calf segment is proportionally much shorter
                # than hm08's, so length is not a homologous radial
                # scale. QA: source calf +42% relative vs target +88%
                # before this fix; thigh (homologous) was faithful.
                s_rad = float(np.mean(rl_t)) / max(float(np.mean(rl_s_all)),
                                                   1e-4)
                arc_t = p_t * np.interp(t_t, tctr, rmean)
                dr, ds = pair_field(t_s * Ls, arc_s, dr_s, ds_s,
                                    t_t * Lt, arc_t, SIG_U, SIG_ARC)
                dr, ds = dr * s_rad, ds * s_seg
                cv = pair_cv(t_s * Ls, arc_s, dr_s, ds_s,
                             SIG_U, SIG_ARC)
                if cv:
                    cv_report[f"{kind}{sname}/seg{si}/{tag}"] = cv
                # hand fade: no recipe slider targets the hands, and
                # kernel smear onto the tiny finger faces was a flip
                # source -- fade the field out past the wrist (t>1)
                fade = 1.0 - sstep(t_t, 1.00, 1.12)
                field[idx_t] += (rd_t * (dr * fade)[:, None]
                                 + (ah_t[None, :] * (ds * fade)[:, None]))
            out[(kind, sname)] = field
    return out


print("building torso fields...")
M_torso, (h_mh, r_mh) = torso_field(M_src, "muscle")
W_torso, _ = torso_field(W_src, "width")
T_torso, _ = torso_field(T_src, "tissue")
print("building limb fields...")
M_limb = limb_fields(M_src, "muscle")
W_limb = limb_fields(W_src, "width")
T_limb = limb_fields(T_src, "tissue")

# ------------------------------------------------------- target region weights
# torso weight: v4's W extended into the neck band (yoke queries)
# neck fade tightened (1.13-1.18 -> 1.07-1.15): the jaw band was the
# largest flip cluster; the yoke lives at h <= ~1.05 and the neck
# girth station sits at h ~ 1.07, still at full strength
w_neck = sstep(h_mh, 1.00, 1.05) * (1 - sstep(h_mh, 1.07, 1.15)) \
    * (1 - sstep(r_mh, 0.11, 0.15))
W_t = np.maximum(W_TORSO_V4, w_neck)

# arm weight: ramp in from the shoulder along the arm; leg weight: ramp
# in below the hip. Weights are per-vertex, then graph-smoothed over
# the mesh adjacency and normalised (v2 seam method).
edges = set()
for a, b, c in mh_tris:
    for u, v in ((a, b), (b, c), (c, a)):
        if u < BODY_END and v < BODY_END:
            edges.add((min(u, v), max(u, v)))
_e = np.array(sorted(edges))
ADJ = [[] for _ in range(NB)]
for u, v in _e:
    ADJ[u].append(v)
    ADJ[v].append(u)


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


w_arm = np.zeros(NB)
w_leg = np.zeros(NB)
for kind, warr in (("arm", w_arm), ("leg", w_leg)):
    for sname in ("R", "L"):
        ch = chain_of(mh_lab, kind, sname)
        if ch is None:
            continue
        segs, ref, lm = ch
        idx = lm["verts"]
        # distance along chain from its root point
        root = segs[0][0]
        d = np.linalg.norm(mh_pos_mac[idx] - root, axis=1)
        warr[idx] = np.maximum(warr[idx], sstep(d, 0.005, 0.055))
W3 = np.stack([W_t, w_arm, w_leg], axis=1)
sup = W3.sum(axis=1) > 0
for j in range(3):
    W3[:, j] = lap_smooth(W3[:, j], sup, 2)
W3 = W3 / np.maximum(W3.sum(axis=1, keepdims=True), 1e-9)
W3[~sup] = 0.0
print(f"region weights: torso-dominant {int((W3[:,0]>0.5).sum())}, "
      f"arm {int((W3[:,1]>0.5).sum())}, leg {int((W3[:,2]>0.5).sum())}, "
      f"uncovered body verts {int((sup[:BODY_END]==0).sum())}")


def blend(torso_f, limb_f):
    # partition of unity ONLY where coverage >= 1; below that the
    # field fades at the region edge instead of being normalised up
    # to full strength at boundary verts (spike/flip source)
    out = W3[:, 0:1] * torso_f
    for (kind, sname), f in limb_f.items():
        j = 1 if kind == "arm" else 2
        out = out + W3[:, j:j + 1] * f
    return out / np.maximum(1.0, W3.sum(axis=1, keepdims=True))


M_field = blend(M_torso, M_limb)
W_field = blend(W_torso, W_limb)
T_field = blend(T_torso, T_limb)
for nm, D in (("M_field(core)", M_field), ("W_field(width)", W_field),
              ("T_field(pre-belly)", T_field)):
    mag = np.linalg.norm(D, axis=1)
    print(f" {nm} on hm08: support {int((mag>0.0002).sum())}, "
          f"max {mag.max()*100:.1f} cm")

# ------------------------------------- fat wrap check (Joe, Nov 12)
# Tissue must wrap front-to-sides: real mass at the flanks (|theta|
# near +-90 deg), not a front-only pad. Measure the tissue field's
# angular profile; ONE pre-registered correction round if the flanks
# are under-weighted (rules fixed before measuring):
#   belly flank/front < 0.50 -> LHandles 0.60->0.85, MassSmooth .75->.85
#   chest flank/front < 0.45 -> Chubby 0.80->0.90
_, th_mh_qa, _, _, _, _, _ = torso_params(mh_pos_mac, mh_crotch, mh_neck,
                                          "hm08")


def side_mass(D):
    er = np.stack([np.sin(th_mh_qa), np.cos(th_mh_qa)], axis=1)
    dr = np.abs(D[:, 0] * er[:, 0] + D[:, 1] * er[:, 1])
    out = {}
    for band, (h0, h1) in (("chest", (0.78, 0.92)),
                           ("belly", (0.35, 0.55))):
        hb = (h_mh >= h0) & (h_mh < h1)
        fr = hb & (np.abs(th_mh_qa) < 0.5)
        fl = hb & (np.abs(th_mh_qa) > 0.9) & (np.abs(th_mh_qa) < 2.2)
        bk = hb & (np.abs(th_mh_qa) > 2.7)
        f_, l_, b_ = (float(dr[m].mean() * 100) if m.sum() else 0.0
                      for m in (fr, fl, bk))
        out[band] = {"front_cm": f_, "flank_cm": l_, "back_cm": b_,
                     "flank_front": (l_ / f_) if f_ > 0 else 0.0}
    return out


SM_BEFORE = side_mass(T_field)
print("side-mass (tissue, pre-correction):",
      {k: {kk: round(vv, 3) for kk, vv in v.items()}
       for k, v in SM_BEFORE.items()})
CORRECTION = {}
if SM_BEFORE["belly"]["flank_front"] < 0.50:
    CORRECTION["TorsoBellyLHandles"] = (
        TISSUE_RECIPE["TorsoBellyLHandles"], 0.85)
    CORRECTION["TorsoMassSmooth"] = (TISSUE_RECIPE["TorsoMassSmooth"],
                                     0.85)
    TISSUE_RECIPE["TorsoBellyLHandles"] = 0.85
    TISSUE_RECIPE["TorsoMassSmooth"] = 0.85
if SM_BEFORE["chest"]["flank_front"] < 0.45:
    CORRECTION["Chubby"] = (TISSUE_RECIPE["Chubby"], 0.90)
    TISSUE_RECIPE["Chubby"] = 0.90
if CORRECTION:
    print(" flank correction applied:", CORRECTION)
    T_src = compose(TISSUE_RECIPE)
    T_torso, _ = torso_field(T_src, "tissue-corrected")
    T_limb = limb_fields(T_src, "tissue-corrected")
    T_field = blend(T_torso, T_limb)
SM_AFTER = side_mass(T_field)
if CORRECTION:
    print("side-mass (tissue, post-correction):",
          {k: {kk: round(vv, 3) for kk, vv in v.items()}
           for k, v in SM_AFTER.items()})


def plane_loops(pos, n, p0):
    """Intersect the body mesh with a plane; chain segments into loops.
    Returns list of (M,3) point arrays (closed loops, not repeated)."""
    n = n / np.linalg.norm(n)
    d = (pos - p0) @ n
    F = FACES_B
    dv = d[F]                                    # (nf, 3)
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
        for k in range(2):
            pass
        segs.append((fid, pts))
    # each crossing face yields exactly 2 points -> pair them per face
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



# ------------------------------------------- belly: v4 system at the cell
def tissue_with_belly(tau):
    """Tissue field with the belly zone served by the v4 system: inside
    the core mask the kernel tissue is crossfaded to tau * D3 (the v4
    core = learned field + pendant drape), and the v4 posture term is
    added over the torso. Muscle stays fully applied underneath (the
    built core of R17)."""
    return T_field + B_CORE[:, None] * (tau * D3 - T_torso) \
        + W_TORSO_V4[:, None] * D_POSTURE


def slice_ratio(pos):
    """Light M4: chest/waist slice-loop girth ratio only (the
    scorecard's own measure), for the tau solve."""
    Z = np.array([0.0, 0.0, 1.0])
    cl = best_loop(pos, Z, np.array([0, 0, mh_crotch + 0.85 * L_mh]))
    wl = best_loop(pos, Z, np.array([0, 0, float(mh_pos_mac[navel_mh, 2])]))
    return loop_perim(cl) / loop_perim(wl)




# ------------------------------------------------------------ fold repair
print(f"body faces for fold gate: {len(FACES_B)}")


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


def repair(D, checks, label):
    """Surgical attenuation repair: only flipped verts (x0.78) and
    their direct edge-neighbours (x0.93) are attenuated -- the first
    bara run used v4's broad ring rule (x0.94 over the whole moved
    component) and it dusted ~10.5k verts, costing real chest/neck
    mass between the tau solve and the final grade. Flip clusters in
    this build are localised (jaw band, finger webs, creases), so the
    repair is localised too. checks: list of (base_pos, base_delta);
    a flip is judged on the FULL delta against each base's normals."""
    moved = np.linalg.norm(D, axis=1) > 0.0002
    D = slope_limit(D, moved)
    att = np.ones(NB)
    traj = []
    for it in range(80):
        badv = np.zeros(NB, bool)
        for pos, base_delta in checks:
            fl = flipped(pos, base_delta + D * att[:, None])
            if fl.any():
                badv[FACES_B[fl].ravel()] = True
        traj.append(int(badv.sum()))
        if not badv.any():
            print(f" {label}: clean after {it} repair iterations "
                  f"(bad-vert trajectory {traj})")
            break
        nbr = np.zeros(NB, bool)
        nbr[_e[badv[_e].any(axis=1)].ravel()] = True
        att[badv] *= 0.78
        att[nbr & ~badv] *= 0.93
        att = np.maximum(att, 0.05)
    else:
        print(f" {label}: WARNING flips remain after 80 iterations "
              f"(trajectory {traj})")
    return D * att[:, None], att, traj


ZERO = np.zeros((NB, 3))
M_field, att_M, traj_M = repair(
    M_field, [(mh_pos, ZERO), (mh_pos_mac, ZERO)], "muscle core")
W_field, att_W, traj_W = repair(
    W_field, [(mh_pos, ZERO), (mh_pos_mac, ZERO),
              (mh_pos, M_field), (mh_pos_mac, M_field)],
    "chest width (solo and over core)")
print("solving belly tau for slice chest:waist >= 1.30 "
      "(Shaw anchor 1.28)...")
TAU = None
for tau_try in np.arange(0.75, 0.29, -0.05):
    tau_try = round(float(tau_try), 2)
    r = slice_ratio(mh_pos_mac + M_field + W_field
                    + tissue_with_belly(tau_try))
    print(f"  tau={tau_try:.2f}: slice chest:waist {r:.3f}")
    if r >= 1.30:
        TAU = tau_try
        break
if TAU is None:
    TAU = 0.30
    print("  WARNING: even tau=0.30 misses 1.30 -- shipping smallest "
          "belly and reporting the miss honestly")
T_field = tissue_with_belly(TAU)
print(f"TAU = {TAU}")

T_field, att_T, traj_T = repair(
    T_field, [(mh_pos, ZERO), (mh_pos_mac, ZERO),
              (mh_pos, M_field + W_field),
              (mh_pos_mac, M_field + W_field)],
    "tissue (solo and over muscle system)")
print(f"attenuation: core min {att_M.min():.2f} "
      f"({int((att_M < 0.999).sum())} verts), width min {att_W.min():.2f} "
      f"({int((att_W < 0.999).sum())}), tissue min {att_T.min():.2f} "
      f"({int((att_T < 0.999).sum())})")


# ------------------------------------------------------- slice-loop metrics
def mesh_volume(pos):
    F = FACES_B
    v0, v1, v2 = pos[F[:, 0]], pos[F[:, 1]], pos[F[:, 2]]
    return abs(float(np.einsum("ij,ij->i", v0,
                                np.cross(v1, v2)).sum() / 6.0))


def grade(pos, lmts):
    """The BARA_LESSONS section-2 scorecard, measured. Stations are
    base-mesh anatomical heights (documented protocol); circumferences
    are true mesh-plane loop perimeters."""
    Z = np.array([0.0, 0.0, 1.0])
    body = pos[:BODY_END]
    crown = body[:, 2].max()
    sole = body[:, 2].min()
    height = crown - sole
    # neck + head
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
    chin_z = jaw_z - 0.02                      # [E] protocol constant
    head_h = crown - chin_z
    # chest / waist stations
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
    # deltoid span (vert extents in the shoulder band)
    band = (body[:, 2] > mh_neck - 0.17) & (body[:, 2] < mh_neck - 0.02)
    delt_span = float(body[band, 0].max() - body[band, 0].min())
    # trap slope from the (x, z) silhouette, right side. Head verts
    # (base-mesh h > 1.16) are EXCLUDED: the skull's silhouette stays
    # high at small |x| and poisons both the fit and the neck-edge
    # read (first grade measured the base human as neck-buried).
    # Fit window starts lateral of the neck cylinder; the trap line
    # at the neck edge is the fit extrapolated to neck_half.
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
    fx = (xs > 0.10) & (xs < delt_span / 2 - 0.020)
    if fx.sum() > 4:
        fit = np.polyfit(xs[fx], ztop[fx], 1)
        trap_angle = float(np.degrees(np.arctan(abs(fit[0]))))
    else:
        trap_angle = float("nan")
    # visible neck: DIRECT read -- silhouette height just lateral of
    # the head (head_w/2 + 0.03), no extrapolation (a steep trap fit
    # extrapolated to the neck edge overshoots past the chin even on
    # the base mesh; the eye reads the shoulder mass beside the head)
    trap_at_neck = float(np.interp(head_w / 2 + 0.03, xs, ztop))
    visible_neck = chin_z - trap_at_neck
    # limbs: largest-loop tape convention (the field data's own
    # convention -- Hall's forearm 45 cm is a max girth), stations
    # swept along each segment, nearest-centroid loop per station
    ua_gs, fa_gs = [], []
    for sname in ("R", "L"):
        lm = lmts["lm"].get(f"arm{sname}")
        if not lm:
            continue
        S, E, W = lm["S"], lm["E"], lm["W"]
        for A, Bv, ts, acc in ((S, E, (0.20, 0.35, 0.50, 0.65), ua_gs),
                               (E, W, (0.15, 0.30, 0.45, 0.60), fa_gs)):
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
    # thigh loops at crotch - 0.10 (two loops, one per leg)
    loops = plane_loops(pos, Z, np.array([0, 0, mh_crotch - 0.10]))
    th = [loop_perim(lp) for lp in loops
          if abs(lp.mean(axis=0)[0]) > 0.03 and loop_perim(lp) > 0.15]
    thigh_g = float(np.mean(th)) if th else float("nan")
    # calf: max loop per side in the anatomical calf zone (4-17 cm
    # below the knee line; sweeping to the knee measures the knee /
    # lower-thigh junction and calls it calf)
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


G_BASE = grade(mh_pos_mac, mh_lab)
G_MUSC = grade(mh_pos_mac + M_field + W_field, mh_lab)
G_COMB = grade(mh_pos_mac + M_field + W_field + T_field, mh_lab)


def band(v, lo, hi):
    return "PASS" if lo <= v <= hi else "miss"


SC = []
SC.append(("M1 neck width / head width", G_COMB["M1_neckW_headW"],
           0.68, 0.80, ">=0.68 pass, target 0.75"))
SC.append(("M2 neck/arm (Reeves 1.00)", G_COMB["M2_neck_arm"],
           0.92, 1.05, "Shaw 0.91 / Reeves 1.00"))
SC.append(("M2 neck/calf", G_COMB["M2_neck_calf"], 0.90, 1.08, ""))
SC.append(("M3 forearm/arm", G_COMB["M3_fa_arm"], 0.80, 0.88,
           "bara band [E]; strongman field 0.70-0.76"))
SC.append(("M4 chest/waist", G_COMB["M4_chest_waist"], 1.28, 9.0,
           "Shaw 1.28 -- the belly constraint"))
SC.append(("M5 chest depth/waist depth", G_COMB["M5_depth_ratio"],
           1.25, 9.0, ""))
SC.append(("M6 trap slope deg", G_COMB["M6_trap_deg"], 28.0, 50.0,
           "steep = traps read as yoke"))
SC.append(("M7 visible neck/head", G_COMB["M7_vis_neck_ratio"],
           0.12, 0.38, "burial failure < 0.10"))
SC.append(("M8 delt span/head width", G_COMB["M8_span_headW"], 2.6, 9.0,
           ""))
SC.append(("M11 thigh/waist", G_COMB["M11_thigh_waist"], 0.62, 9.0, ""))
SC.append(("M12 heads tall", G_COMB["M12_heads_tall"], 6.4, 7.2,
           "bara band; human norm 7.5"))
score_rows = []
print("\n== BARA_LESSONS SCORECARD (combined +1/+1, macro base) ==")
for name, v, lo, hi, note in SC:
    st = band(v, lo, hi)
    score_rows.append({"metric": name, "value": round(float(v), 3),
                       "band": [lo, hi], "status": st, "note": note})
    print(f" {name:34s} {v:7.3f}  [{lo},{hi}]  {st}  {note}")
SM_FINAL = side_mass(T_field)
M13_RATIO = G_COMB["chest_w"] / G_BASE["chest_w"]
score_rows.append({
    "metric": "M13 chest width ratio (broadness, Joe addition)",
    "value": round(float(M13_RATIO), 3), "band": [1.15, 9.0],
    "status": band(M13_RATIO, 1.15, 9.0),
    "note": "chest loop width at +1 / base; broadness ships as its "
            "own slider (body.chest.width)"})
print(f" M13 chest width: {G_BASE['chest_w']*100:.1f} -> "
      f"{G_COMB['chest_w']*100:.1f} cm (x{M13_RATIO:.3f}); waist width "
      f"{G_BASE['waist_w']*100:.1f} -> {G_COMB['waist_w']*100:.1f} cm "
      f"(lateral silhouette check); delt span "
      f"{G_BASE['delt_span']*100:.1f} -> {G_COMB['delt_span']*100:.1f} cm")
print(f" side-mass final (tissue): belly flank/front "
      f"{SM_FINAL['belly']['flank_front']:.2f}, chest "
      f"{SM_FINAL['chest']['flank_front']:.2f}")
vol_gain = (G_COMB["volume_L"] - G_BASE["volume_L"]) / G_BASE["volume_L"]
tissue_share = (G_COMB["volume_L"] - G_MUSC["volume_L"]) / max(
    G_COMB["volume_L"] - G_BASE["volume_L"], 1e-9)
print(f" M9 mass: volume {G_BASE['volume_L']:.1f} -> "
      f"{G_COMB['volume_L']:.1f} L ({vol_gain:+.1%}) at fixed height "
      f"{G_BASE['height_m']:.3f} m")
print(f" M10 tissue share of added volume: {tissue_share:.2f} "
      "(proxy only -- see proof doc)")
print(f" muscle-system chest/waist: {G_MUSC['M4_chest_waist']:.3f}; "
      f"base: {G_BASE['M4_chest_waist']:.3f}")
print(f" raw-base flips recheck: core "
      f"{int(flipped(mh_pos, M_field).sum())}, width "
      f"{int(flipped(mh_pos, W_field).sum())}, muscle system "
      f"{int(flipped(mh_pos, M_field + W_field).sum())}, tissue "
      f"{int(flipped(mh_pos, T_field).sum())}, combined "
      f"{int(flipped(mh_pos, M_field + W_field + T_field).sum())}; "
      f"macro combined: "
      f"{int(flipped(mh_pos_mac, M_field + W_field + T_field).sum())}")


# ----------------------------------------------------------------- outputs
def fmt(v):
    s = f"{abs(v):.3f}".rstrip("0")
    if s.endswith("."):
        s += "0"
    if s in ("", "0."):
        s = "0"
    return ("-" + s) if v < 0 else s


def write_target(path, delta, note):
    """v4's writer verbatim: standard MakeHuman sparse target --
    header + 'index x z y' lines in decimetres (canonical (x,y,z)
    maps to file (x, z, y)), moved verts only (> 0.001 dm)."""
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


NOTE_M = ("Provenance: omniversal slider body.muscle (bara muscle "
          "vector, core), instance makehuman_hm08. HIMBO granular "
          "vocabulary composed per BARA_LESSONS 6C x Sen 4.2, yoke "
          "first; NeckMass authored from the Weight block gated to "
          "the neck. Chest width ships separately as body.chest.width. "
          "Study-only, internal - not a CC0 MakeHuman asset. "
          "See BARA_PROOF.md.")
NOTE_W = ("Provenance: omniversal slider body.chest.width (broadness "
          "component), instance makehuman_hm08. Lateral frame + lat "
          "sweep ONLY (TorsoShoulderInc/TorsoWidth/ArmsShoulders/"
          "TorsoBackShape), split from body.muscle per Joe Nov 12 "
          "2026: width editable independently of depth and mass. "
          "Study-only, internal. See BARA_PROOF.md.")
NOTE_T = ("Provenance: omniversal slider body.tissue.strongman "
          "(tissue vector, strongman cell), instance makehuman_hm08. "
          "HIMBO tissue vocabulary over the muscle system; belly = v4 "
          "whole-torso system at tau=0.60 (chest:waist >= 1.30). "
          "Study-only, internal - not a CC0 MakeHuman asset. "
          "See BARA_PROOF.md.")
NOTE_C = ("Provenance: combined bara strongman build at +1/+1/+1 "
          "(body.muscle + body.chest.width + body.tissue.strongman), "
          "instance makehuman_hm08. QA convenience target; the three "
          "component sliders are the deliverable. Study-only, "
          "internal. See BARA_PROOF.md.")
n_m = write_target(OUT / "body.muscle.target", M_field, NOTE_M)
n_w = write_target(OUT / "body.chest.width.target", W_field, NOTE_W)
n_t = write_target(OUT / "body.tissue.strongman.target", T_field, NOTE_T)
n_c = write_target(OUT / "body.bara.strongman.target",
                   M_field + W_field + T_field, NOTE_C)
print(f"targets written: core {n_m}, width {n_w}, tissue {n_t}, "
      f"combined {n_c} moved verts")


def slider_json(sid, label, recipe, extra_sem, qa_extra):
    return {
        "id": sid,
        "label": label,
        "group": "body",
        "version": "0.1.0-proof",
        "symmetry": "symmetric",
        "range": {"min": 0.0, "max": 1.0, "default": 0.0,
                  "endpoint_anchor":
                      "+1 = the BARA_LESSONS strongman-pole build "
                      "(section 6C MuscleVector x section 4.2 Sen "
                      "strongman cell), measured on hm08"},
        "region": "full body (torso kernel + limb segment kernels; "
                  "belly core served by the v4 system in the tissue "
                  "vector only)",
        "system": {
            "model": "transfer from HIMBO granular vocabulary composed "
                     "on the HIMBO base; (h,theta) torso kernel + "
                     "(t,phi) limb segment kernels; v4 belly system "
                     "reused for the tissue belly (tau-solved)",
            "source_fields": recipe,
            "proves": "two-vector bara composition at the strongman "
                      "cell: yoke-first muscle + 15-25% tissue over it, "
                      "chest ring >= waist ring, 0 flips at +1"},
        "semantics": ("Proof slider, study-only provenance. Source "
                      "morphs decoded from Joe's own mod files (learned "
                      "library); only composed displacement fields "
                      "ship, never source assets.") + extra_sem,
        "qa": qa_extra,
    }


qa_common = {
    "fold_gate": "0 flipped faces at +1 required (slope limiter "
                 "KAPPA=0.55 + surgical attenuation repair, raw AND "
                 "macro base; each slider solo and composed)",
    "kernel_cv": cv_report,
    "scorecard_combined": score_rows,
    "grades": {"base": G_BASE, "muscle_system": G_MUSC,
               "combined": G_COMB},
    "broadness": {"chest_width_base_cm": G_BASE["chest_w"] * 100,
                  "chest_width_build_cm": G_COMB["chest_w"] * 100,
                  "chest_width_ratio": float(M13_RATIO),
                  "waist_width_base_cm": G_BASE["waist_w"] * 100,
                  "waist_width_build_cm": G_COMB["waist_w"] * 100,
                  "delt_span_base_cm": G_BASE["delt_span"] * 100,
                  "delt_span_build_cm": G_COMB["delt_span"] * 100},
    "side_mass": {"before_correction": SM_BEFORE,
                  "after_correction": SM_AFTER,
                  "correction": {k: list(v) for k, v in
                                 CORRECTION.items()},
                  "final_shipped": SM_FINAL},
}
(OUT / "body.muscle.slider.json").write_text(json.dumps(slider_json(
    "body.muscle", "Body — Muscle (bara vector, core)",
    {k: v for k, v in MUSCLE_RECIPE.items()},
    " NeckMass authored from the Weight block gated to the neck band "
    "(study A2; Sen's Weight 0.90 with the inflation left behind). "
    "Chest BROADNESS is NOT in this slider: it ships separately as "
    "body.chest.width (Joe, Nov 12) so width can be edited "
    "independently of chest depth (TorsoSterDepth, here) and mass.",
    qa_common), indent=1))
(OUT / "body.chest.width.slider.json").write_text(json.dumps(
    slider_json(
        "body.chest.width", "Chest — Width (broadness)",
        {k: v for k, v in WIDTH_RECIPE.items()},
        " Broadness component (Joe, Nov 12): lateral ribcage/shoulder "
        "frame + lat sweep ONLY -- no depth (TorsoSterDepth lives in "
        "body.muscle), no pec mass. +1 with body.muscle +1 and "
        "body.tissue.strongman +1 is the graded strongman build; "
        f"chest loop width at the build: {G_BASE['chest_w']*100:.1f} "
        f"-> {G_COMB['chest_w']*100:.1f} cm.",
        qa_common), indent=1))
(OUT / "body.tissue.strongman.slider.json").write_text(json.dumps(
    slider_json(
        "body.tissue.strongman", "Body — Tissue (strongman cell)",
        {**{k: v for k, v in TISSUE_RECIPE.items()},
         "belly_core_v4_tau": TAU,
         "belly_posture_v4": 1.0},
        " Belly = v4 whole-torso system at the strongman setting: "
        "core crossfade to tau*D3 + D_posture, tau solved so the "
        "chest:waist ring ratio stays >= 1.30 (Shaw anchor 1.28, R17). "
        "Fat-wrap QA (Joe, Nov 12): the layer's angular profile is "
        "measured front/flank/back at chest and belly bands (side_mass "
        "in qa); flank correction applied: "
        + (str({k: list(v) for k, v in CORRECTION.items()})
           if CORRECTION else "none needed"),
        qa_common), indent=1))

np.savez_compressed(WORK / "bara_fields.npz",
                    muscle_core_canonical_m=M_field,
                    chest_width_canonical_m=W_field,
                    tissue_canonical_m=T_field,
                    region_weights=W3, tau=np.float64(TAU),
                    att_muscle=att_M, att_width=att_W, att_tissue=att_T)
(WORK / "qa_numbers_bara.json").write_text(json.dumps({
    "tau": TAU,
    "girth_solve": "chest:waist >= 1.30 by mesh-plane slice loops "
                   "(the scorecard's own measure); final M4 re-graded "
                   "post-repair",
    "cv": cv_report,
    "scorecard": score_rows,
    "grades": {"base": G_BASE, "muscle_system": G_MUSC,
               "combined": G_COMB},
    "broadness": qa_common["broadness"],
    "side_mass": qa_common["side_mass"],
    "m9_volume_gain": vol_gain, "m10_tissue_share_proxy": tissue_share,
    "attenuation": {"core_min": float(att_M.min()),
                    "core_verts": int((att_M < 0.999).sum()),
                    "width_min": float(att_W.min()),
                    "width_verts": int((att_W < 0.999).sum()),
                    "tissue_min": float(att_T.min()),
                    "tissue_verts": int((att_T < 0.999).sum())},
    "repair_trajectories": {"core": traj_M, "width": traj_W,
                            "tissue": traj_T},
    "flips_final": {
        "raw_core": int(flipped(mh_pos, M_field).sum()),
        "raw_width": int(flipped(mh_pos, W_field).sum()),
        "raw_muscle_system": int(flipped(mh_pos,
                                         M_field + W_field).sum()),
        "raw_tissue": int(flipped(mh_pos, T_field).sum()),
        "raw_combined": int(flipped(mh_pos,
                                    M_field + W_field + T_field).sum()),
        "macro_combined": int(flipped(mh_pos_mac,
                                      M_field + W_field + T_field).sum())},
}, indent=1, default=float))
print("\nwrote targets + slider JSONs + qa_numbers_bara.json + "
      "bara_fields.npz")
