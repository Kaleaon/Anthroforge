#!/usr/bin/env python3
"""JORGE BODY BUILD for AnthroForge (Joe, Nov 16, 2026: body shapes
first -- no fur, no renders).

Composes Jorge's body geometry on the MakeHuman hm08 base from his
recorded preset vector (anthroforge-app/library/presets/
jorge.afchar.json; derivation in anthroforge-v2/presets-titan-
batch1.md section 5.2), using the bara-proof machinery verbatim
(bara-proof/scripts/build_bara.py, copied Nov 16, 2026 and adapted
only in the recipe tables, the belly drive, the scorecard reporting
and the output paths/notes -- every kernel, blend, repair and grading
function is byte-identical to the proven build).

Composition (the Sen pattern, SEN_BUILD.md section 2):
  delta_jorge = muscle + chest.width + tissue.jorge
                + belly terminal (v5.1 component, scaled)
  muscle       -- Jorge's MuscleVector at Muscle 0.45 (the flagged
                  watch item: built AT 45, per Joe's ruling; the
                  muscle-vs-fat evidence is measured and reported
                  for his judgement, NOT pre-corrected).
  chest.width  -- broadness component (TorsoWidth / TorsoBackShape /
                  ArmsShoulders at Jorge's values).
  tissue.jorge -- Jorge's TissueVector (the gentle-mass pole:
                  Chubby 0.85, MassSmooth intended 0.85 -- see the
                  vocabulary gap below) with the v4 whole-torso belly
                  system at tau = BellyPot 0.60. The strongman
                  ratio-solve (chest:waist >= 1.30) does NOT apply to
                  Jorge's cell; tau is driven by his recorded
                  BellyPot and the resulting ratio is reported.
  terminal     -- the v5.1 belly slider's terminal component
                  (hands/feet tissue) at x0.60, following the v5.1
                  linear-component semantics at w = BellyPot. (Sen's
                  build shipped his terminal at x1.0; divergence
                  documented in JORGE_BUILD.md.)

VOCABULARY GAP (known, Joe's open decision -- FIX_NECK_FIELD.md):
five of Jorge's vector entries have NO block in the Vanilla OSD the
machinery composes on -- BodyMass, PecsLower, BubbleButt,
TorsoMassSmooth, BellySmooth -- and compose as ZEROS here, exactly
as they did in Sen's shipped build. They exist in SOS.osd, but that
file's base has ~11k verts (max index 11006) vs the Vanilla base's
9346, so its diffs are not index-compatible with this machinery
without new verification. hi_diff() warns loudly for each miss;
the warnings are part of this build's log and of JORGE_BUILD.md.
The build therefore UNDERSTATES Jorge's softness; judge the
muscle-vs-fat evidence with that bias in mind.

Excluded with bara-proof precedent: Lean (two-sided, sign-ambiguous),
TorsoWaistSize ("Shrink Waist" semantics; the waist is routed
through TorsoLower + LHandles + the belly core), TorsoBelly /
TorsoBellyChub (HIMBO belly stack, replaced by the v4/v5.1 belly
system). The fat-wrap side-mass check is MEASURED and reported;
the strongman build's pre-registered flank correction is NOT
applied (its correction table is Sen-recipe-specific).

QA: float-space fold repair as build_bara (0 flips, both bases,
each component solo and composed), THEN the house ship gate on the
shipped quantised numbers (0.1 mm .target quantisation): 0 flips
and min normalised face dot >= 0.01 on both bases for every
component solo and the full sum, with quantised-space attenuation
repair (neckfix precedent) if the gate fails. Grading: the
BARA_LESSONS 12-metric scorecard machinery, reported as values
(no strongman PASS bands -- Jorge is a different cell).

PROVENANCE: study-only. Every field derives from sliders decoded
from Joe's own legitimately obtained mod files (learned library);
only aggregate displacement statistics and our own composed
fields ship.
"""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
OUT = HERE.parent                      # characters/jorge/
V2 = OUT.parent.parent                 # anthroforge-v2/
APP = V2.parent / "anthroforge-app"
FP = V2 / "first-proof"
WORK = OUT / "work"
TG = OUT / "targets"
LEARNED = Path.home() / "workspace/character_assets/learned"
HIMBO_DIR = (Path.home() / "workspace/character_assets/_himbo_work/"
             "CalienteTools/BodySlide/ShapeData/HIMBO")
sys.path.insert(0, str(LEARNED / "tools"))
sys.path.insert(0, str(V2))
sys.path.insert(0, str(APP))
from osdparse import load_osd  # noqa: E402
from body_machinery.axes import sstep, torso_params  # noqa: E402
from body_machinery.labels import (  # noqa: E402
    blend_regions,
    label_mesh,
    region_weights_w3,
)
from body_machinery.loops import (  # noqa: E402
    grade as _bm_grade,
    side_mass as _bm_side_mass,
    slice_ratio as _bm_slice_ratio,
)
from body_machinery.osd import (  # noqa: E402
    BODY_END,
    SK_UNIT_M as SK,
    align_macro_base,
    compose_osd,
    extract_base_positions,
    hi_diff as _bm_hi_diff,
    load_mpfb_base_obj,
)
from body_machinery.repair import (  # noqa: E402
    flipped as _bm_flipped,
    repair as _bm_repair,
)
from body_machinery.transfer import limb_fields, torso_field  # noqa: E402
from core.geometry import write_target  # noqa: E402

MPFB_ZIP = Path.home() / "workspace/stick-figure-avatar/photoreal/tools/mpfb2.zip"
KAPPA = 0.55        # slope-limiter budget (v4)


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
# JORGE: the v5.1 belly system's terminal component (extremity
# tissue), scaled by his belly drive w = BellyPot 0.60 per the v5.1
# linear-component semantics (delta(w) = w*LIN + sign(w)|w|^gamma*SAG;
# the terminal sits inside LIN). Sen's build shipped his at x1.0 --
# divergence documented in JORGE_BUILD.md.
_v51 = np.load(FP / "work/belly_v51.npz")
TERM_FIELD = _v51["terminal_canonical_m"].astype(np.float64) * 0.60
print(f"terminal component: v5.1 TERM x0.60, max "
      f"{np.abs(TERM_FIELD).max()*100:.2f} cm, "
      f"{int((np.abs(TERM_FIELD).max(axis=1) > 1e-4).sum())} verts")
W_TORSO_V4 = _v4["torso_weight"].astype(np.float64)

mh_pos = load_mpfb_base_obj(MPFB_ZIP)
_mac = np.load(FP / "work/mh_macro_base.npz")["pos_canonical_m"]
mh_pos_mac = align_macro_base(mh_pos, _mac, BODY_END)
print("macro->raw alignment: median |delta| per axis (the macro "
      "reshaping itself):",
      np.round(np.median(np.abs(mh_pos_mac[:BODY_END] - mh_pos[:BODY_END]),
                         axis=0), 4))
NB = len(mh_pos)
FACES_B = mh_tris[np.all(mh_tris < BODY_END, axis=1)]
print(f"hm08: {NB} verts, torso L={L_mh:.4f} m, navel h*={h_star:.3f}")

hi_pos_u = extract_base_positions(
    (HIMBO_DIR / "HIMBO Body - Vanilla.nif").read_bytes(), 4000)
assert hi_pos_u is not None and len(hi_pos_u) == 9346, "HIMBO base extract"
hi_blocks = {b["name"]: b for b in
             load_osd(str(HIMBO_DIR / "HIMBO Body - Vanilla.osd"))["blocks"]}
NH = len(hi_pos_u)
_MISSED_BLOCKS: set[str] = set()


def hi_diff(name):
    return _bm_hi_diff(
        hi_blocks, NH, name, warn_missing=True, missed=_MISSED_BLOCKS
    )


# ------------------------------------------------------------- the recipes
# Every entry traces to Jorge's recorded preset vector
# (anthroforge-app/library/presets/jorge.afchar.json; derivation in
# presets-titan-batch1.md section 5.2). HIMBO names are mapped exactly
# as the Sen build mapped Sen's record (same 41-slider ID set).
# The muscle system ships as TWO sliders whose sum is the build's
# muscle layer:
#   body.muscle       -- mass/yoke/arms/legs (below)
#   body.chest.width  -- lateral frame + lat sweep (WIDTH_RECIPE)
WIDTH_RECIPE = {
    "TorsoWidth": 0.90,        # body.width.torso
    "TorsoBackShape": 0.70,    # body.width.back_shape (lat sweep)
    "ArmsShoulders": 0.85,     # body.width.shoulders
}
MUSCLE_RECIPE = {   # value = slider position 0..1 (of the 0..100 decode)
    "BodyMass": 0.25,          # body.mass -- VOCAB GAP: no Vanilla
                               # OSD block -> composes ZERO (see header)
    # yoke first (R4) -- NeckMass authored below from the Weight block;
    # strong but deliberately under Sen's (section 5.2: a working
    # dog's yoke, not a strongman's)
    "ArmsTraps": 0.80,         # body.muscle.traps
    "ArmsTrapsMeat": 0.90,     # body.muscle.traps_meat
    "ArmsTrapsPush": 0.70,     # body.muscle.traps_push
    # torso masses: full lower torso (never tucked), broad back
    "Muscle": 0.45,            # body.muscle -- THE WATCH ITEM (Joe:
                               # build at 45; 45->60 only if the build
                               # reads fat-not-strong, his call)
    "TorsoMass": 1.00,         # body.muscle.torso_mass (pin)
    "TorsoBackSize": 0.85,     # body.muscle.back_size
    "TorsoLower": 1.00,        # body.muscle.torso_lower (pin; R18
                               # books trunk mass with muscle)
    # chest: big soft pecs -- size/width near Sen, less hard mass
    "PecsSize": 0.95,          # body.muscle.pecs_size
    "PecsMass": 0.85,          # body.muscle.pecs_mass
    "PecsWidth": 0.95,         # body.muscle.pecs_width
    "PecsLower": 0.65,         # body.muscle.pecs_lower -- VOCAB GAP:
                               # only PecsLowerSide exists -> ZERO
    "PecsClavicle": 0.60,      # body.muscle.pecs_clavicle
    # arms: strong-working (delts/biceps/forearm), under Sen's peak
    "ArmsDelts": 0.80,         # body.muscle.delts
    "ArmsBiceps": 0.75,        # body.muscle.biceps
    "ArmsBrachio": 0.70,       # body.muscle.brachio
    "ArmsFore": 0.85,          # body.muscle.forearm
    # legs: full working legs pinned with the torso (R19)
    "LegsSize": 1.00,          # body.muscle.legs_size (pin)
    "LegsThigh": 1.00,         # body.muscle.legs_thigh (pin)
    "LegsGlutes": 0.75,        # body.muscle.glutes
    "LegsCalfSize": 0.85,      # body.muscle.calf_size
    "LegsCalfWidth": 0.80,     # body.muscle.calf_width
    "ButtBooty": 0.75,         # body.muscle.butt
    "BubbleButt": 0.50,        # body.muscle.butt_bubble -- VOCAB GAP
                               # -> composes ZERO
}
NECK_WEIGHT_VALUE = 0.95       # body.neck.weight -- gated to the neck

TISSUE_RECIPE = {
    "Chubby": 0.85,            # body.fat.chubby (kept under Sen's
                               # 1.00 record value -- section 5.2)
    "TorsoMassSmooth": 0.85,   # body.fat.mass_smooth -- VOCAB GAP:
                               # no Vanilla OSD block -> composes
                               # ZERO. NOTE: per section 5.2 this is
                               # most of the intended Sen/Jorge tissue
                               # difference; its absence biases this
                               # build STRONGER than Jorge's vector.
    "TorsoBellyLHandles": 0.65,  # body.fat.love_handles
    "PecsSaggy": 0.50,         # body.fat.pecs_sag
    "LegsChubby": 0.80,        # body.fat.legs_chubby
    "ButtSaggy": 0.35,         # body.fat.butt_sag
    "BellySmooth": 0.80,       # body.fat.belly_smooth -- VOCAB GAP
                               # -> composes ZERO
    "ArmsTrapsValleys": 0.20,  # body.definition.traps_valleys (Sen
                               # mapping: definition rides the tissue
                               # component)
}
# EXCLUDED, with reasons (bara-proof precedent): Lean -1.00
# (two-sided, sign-ambiguous -- v4 precedent), TorsoWaistSize -0.65
# ("Shrink Waist" semantics; R18 routes the waist through TorsoLower
# + LHandles + belly core, no shrink term), the HIMBO belly stack
# TorsoBelly 0.75 / TorsoBellyChub 0.80 (replaced by the v4/v5.1
# belly system; the belly DRIVE is Jorge's BellyPot 0.60 -> tau,
# below). Machinery-only entries of the strongman build (SterHeight,
# SterDepth, BackSlope, SerratusMid, DeltsBack, DeltsShape,
# BicepsBack, ArmsSide, ShoulderInc) are absent from Jorge's record
# and are NOT carried over -- adding them would invent values.


def compose(recipe):
    return compose_osd(
        hi_blocks, NH, recipe, scale=SK, warn_missing=True, missed=_MISSED_BLOCKS
    )


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
cv_report = {}

print("building torso fields...")
M_torso, (h_mh, r_mh) = torso_field(
    M_src,
    "muscle",
    hi_lab=hi_lab,
    h_hi=h_hi,
    th_hi=th_hi,
    r_hi=r_hi,
    mh_pos_mac=mh_pos_mac,
    mh_crotch=mh_crotch,
    mh_neck=mh_neck,
    s_hi=s_hi,
    sig_h=SIG_H,
    sig_a=SIG_A,
    cv_report=cv_report,
)
W_torso, _ = torso_field(
    W_src,
    "width",
    hi_lab=hi_lab,
    h_hi=h_hi,
    th_hi=th_hi,
    r_hi=r_hi,
    mh_pos_mac=mh_pos_mac,
    mh_crotch=mh_crotch,
    mh_neck=mh_neck,
    s_hi=s_hi,
    sig_h=SIG_H,
    sig_a=SIG_A,
    cv_report=cv_report,
)
T_torso, _ = torso_field(
    T_src,
    "tissue",
    hi_lab=hi_lab,
    h_hi=h_hi,
    th_hi=th_hi,
    r_hi=r_hi,
    mh_pos_mac=mh_pos_mac,
    mh_crotch=mh_crotch,
    mh_neck=mh_neck,
    s_hi=s_hi,
    sig_h=SIG_H,
    sig_a=SIG_A,
    cv_report=cv_report,
)
print("building limb fields...")
M_limb = limb_fields(
    M_src,
    "muscle",
    hi_pos_m=hi_pos_u * SK,
    mh_pos_mac=mh_pos_mac,
    hi_lab=hi_lab,
    mh_lab=mh_lab,
    sig_u=SIG_U,
    sig_arc=SIG_ARC,
    cv_report=cv_report,
)
W_limb = limb_fields(
    W_src,
    "width",
    hi_pos_m=hi_pos_u * SK,
    mh_pos_mac=mh_pos_mac,
    hi_lab=hi_lab,
    mh_lab=mh_lab,
    sig_u=SIG_U,
    sig_arc=SIG_ARC,
    cv_report=cv_report,
)
T_limb = limb_fields(
    T_src,
    "tissue",
    hi_pos_m=hi_pos_u * SK,
    mh_pos_mac=mh_pos_mac,
    hi_lab=hi_lab,
    mh_lab=mh_lab,
    sig_u=SIG_U,
    sig_arc=SIG_ARC,
    cv_report=cv_report,
)

# ------------------------------------------------------- target region weights
W3, _e = region_weights_w3(
    mh_pos_mac, mh_lab, h_mh, r_mh, W_TORSO_V4, mh_tris, body_end=BODY_END
)
M_field = blend_regions(M_torso, M_limb, W3)
W_field = blend_regions(W_torso, W_limb, W3)
T_field = blend_regions(T_torso, T_limb, W3)
for nm, D in (("M_field(core)", M_field), ("W_field(width)", W_field),
              ("T_field(pre-belly)", T_field)):
    mag = np.linalg.norm(D, axis=1)
    print(f" {nm} on hm08: support {int((mag>0.0002).sum())}, "
          f"max {mag.max()*100:.1f} cm")

# ------------------------------------- fat wrap check (Joe, Nov 12)
_, th_mh_qa, _, _, _, _, _ = torso_params(mh_pos_mac, mh_crotch, mh_neck,
                                          "hm08")
SM_BEFORE = _bm_side_mass(T_field, h_mh, th_mh_qa)
print("side-mass (tissue, as composed):",
      {k: {kk: round(vv, 3) for kk, vv in v.items()}
       for k, v in SM_BEFORE.items()})
CORRECTION = {}
SM_AFTER = SM_BEFORE


# ------------------------------------------- belly: v4 system at the cell
def tissue_with_belly(tau):
    """Tissue field with the belly zone served by the v4 system."""
    return T_field + B_CORE[:, None] * (tau * D3 - T_torso) \
        + W_TORSO_V4[:, None] * D_POSTURE


# ------------------------------------------------------------ fold repair
print(f"body faces for fold gate: {len(FACES_B)}")


def flipped(pos, D):
    return _bm_flipped(pos, D, FACES_B)


def repair(D, checks, label):
    return _bm_repair(
        D,
        checks,
        label,
        faces=FACES_B,
        edges=_e,
        ref_pos=mh_pos,
        kappa=KAPPA,
    )


ZERO = np.zeros((NB, 3))
M_field, att_M, traj_M = repair(
    M_field, [(mh_pos, ZERO), (mh_pos_mac, ZERO)], "muscle core")
W_field, att_W, traj_W = repair(
    W_field, [(mh_pos, ZERO), (mh_pos_mac, ZERO),
              (mh_pos, M_field), (mh_pos_mac, M_field)],
    "chest width (solo and over core)")
# JORGE: no ratio solve. The strongman build solves tau for a
# chest:waist >= 1.30 gate; Jorge's cell has no such gate -- his
# belly drive is his recorded BellyPot 0.60, and the resulting
# chest:waist ratio is MEASURED and reported as watch-item evidence.
TAU = 0.60
T_field = tissue_with_belly(TAU)
_r_jorge = _bm_slice_ratio(
    mh_pos_mac + M_field + W_field + T_field,
    FACES_B,
    mh_crotch,
    L_mh,
    float(mh_pos_mac[navel_mh, 2]),
)
print(f"TAU = {TAU} (BellyPot, fixed); composed slice chest:waist "
      f"{_r_jorge:.3f} (reported, not gated)")

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


G_BASE = grade(mh_pos_mac, mh_lab)
G_MUSC = grade(mh_pos_mac + M_field + W_field, mh_lab)
G_COMB = grade(mh_pos_mac + M_field + W_field + T_field + TERM_FIELD,
               mh_lab)

# JORGE: no strongman PASS bands -- his cell is judged by Joe from
# the measured evidence. Report the scorecard metrics as VALUES for
# base / muscle system / combined side by side (the muscle-vs-fat
# read: how far the muscle system alone carries the strong read, and
# how much the tissue layer then softens it).
_METRICS = [
    ("M1_neckW_headW", "M1 neck width / head width"),
    ("M2_neck_arm", "M2 neck/arm (Reeves 1.00)"),
    ("M2_neck_calf", "M2 neck/calf"),
    ("M3_fa_arm", "M3 forearm/arm"),
    ("M4_chest_waist", "M4 chest/waist girth"),
    ("M5_depth_ratio", "M5 chest depth/waist depth"),
    ("M6_trap_deg", "M6 trap slope deg"),
    ("M7_vis_neck_ratio", "M7 visible neck/head"),
    ("M8_span_headW", "M8 delt span/head width"),
    ("M11_thigh_waist", "M11 thigh/waist"),
    ("M12_heads_tall", "M12 heads tall"),
]
score_rows = []
print("\n== SCORECARD VALUES (macro base): base | muscle | combined ==")
for key, name in _METRICS:
    score_rows.append({
        "metric": name, "base": round(float(G_BASE[key]), 3),
        "muscle_system": round(float(G_MUSC[key]), 3),
        "combined": round(float(G_COMB[key]), 3)})
    print(f" {name:34s} {G_BASE[key]:7.3f} | {G_MUSC[key]:7.3f} | "
          f"{G_COMB[key]:7.3f}")
SM_FINAL = _bm_side_mass(T_field, h_mh, th_mh_qa)
M13_RATIO = G_COMB["chest_w"] / G_BASE["chest_w"]
score_rows.append({
    "metric": "M13 chest width ratio (broadness)",
    "base": 1.0, "muscle_system": None,
    "combined": round(float(M13_RATIO), 3),
    "note": "chest loop width, combined / base; broadness ships as "
            "its own component (body.chest.width)"})
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
      f"{int(flipped(mh_pos, M_field + W_field + T_field + TERM_FIELD).sum())}; "
      f"macro combined: "
      f"{int(flipped(mh_pos_mac, M_field + W_field + T_field + TERM_FIELD).sum())}")


# ----------------------------------------------------------------- outputs
NOTE_M = ("Provenance: Jorge body build (Nov 16, 2026), component "
          "body.muscle at Jorge's recorded vector (body.muscle 0.45 "
          "-- the watch item, built at 45 per Joe's ruling), "
          "instance makehuman_hm08. HIMBO granular vocabulary "
          "composed via the bara-proof machinery; NeckMass authored "
          "from the 'Weight 0 to 1' block at 0.95 gated to the "
          "neck. Chest width ships separately as body.chest.width. "
          "BodyMass 0.25, PecsLower 0.65 and BubbleButt 0.50 of "
          "the vector compose ZERO (no Vanilla OSD block -- see "
          "JORGE_BUILD.md). Study-only, internal - not a CC0 "
          "MakeHuman asset.")
NOTE_W = ("Provenance: Jorge body build (Nov 16, 2026), component "
          "body.chest.width (broadness), instance makehuman_hm08. "
          "Lateral frame + lat sweep ONLY (TorsoWidth 0.90 / "
          "TorsoBackShape 0.70 / ArmsShoulders 0.85). Study-only, "
          "internal. See JORGE_BUILD.md.")
NOTE_T = ("Provenance: Jorge body build (Nov 16, 2026), component "
          "body.tissue.jorge (his tissue vector), instance "
          "makehuman_hm08. HIMBO tissue vocabulary over the muscle "
          "system; belly = v4 whole-torso system at tau = BellyPot "
          "0.60 (fixed drive, no ratio solve). TorsoMassSmooth "
          "0.85 and BellySmooth 0.80 of the vector compose ZERO "
          "(no Vanilla OSD block -- see JORGE_BUILD.md). "
          "Study-only, internal - not a CC0 MakeHuman asset.")
NOTE_E = ("Provenance: Jorge body build (Nov 16, 2026), belly "
          "terminal component (v5.1 extremity tissue) scaled "
          "x0.60 = BellyPot, per the v5.1 linear-component "
          "semantics. Study-only, internal. See JORGE_BUILD.md.")
NOTE_C = ("Provenance: combined Jorge body build (Nov 16, 2026): "
          "body.muscle + body.chest.width + body.tissue.jorge + "
          "belly terminal x0.60, instance makehuman_hm08. QA "
          "convenience target; the component targets are the "
          "deliverable. Study-only, internal. See JORGE_BUILD.md.")
n_m = write_target(TG / "body.muscle.target", M_field, NOTE_M)
n_w = write_target(TG / "body.chest.width.target", W_field, NOTE_W)
n_t = write_target(TG / "body.tissue.jorge.target", T_field, NOTE_T)
n_e = write_target(TG / "body.belly.protrusion_terminal_v51.target",
                   TERM_FIELD, NOTE_E)
n_c = write_target(TG / "body.jorge.target",
                   M_field + W_field + T_field + TERM_FIELD, NOTE_C)
print(f"targets written: muscle {n_m}, width {n_w}, tissue {n_t}, "
      f"terminal {n_e}, combined {n_c} moved verts")

EXPORT_SCALE = 1.39            # record: export x1.39 -> 2.44 m
V_EXPORT_L = G_COMB["volume_L"] * EXPORT_SCALE ** 3
qa_doc = {
    "build": "Jorge body (no head, no fur, no render), stage-1 "
             "pattern per SEN_BUILD.md, Nov 16, 2026",
    "base": "makehuman_hm08 (MPFB macro base for grading; raw "
            "base.obj frame for the second fold-gate basis)",
    "vector_applied": {
        "muscle_recipe": MUSCLE_RECIPE,
        "width_recipe": WIDTH_RECIPE,
        "tissue_recipe": TISSUE_RECIPE,
        "neck_weight_gated": NECK_WEIGHT_VALUE,
        "belly_tau": TAU,
        "belly_drive": "tau := BellyPot 0.60 (fixed; NO strongman "
                       "ratio solve)",
        "terminal_scale": 0.60,
        "slice_ratio_pre_repair": float(_r_jorge),
    },
    "vocab_gap_composes_zero": {
        "BodyMass": MUSCLE_RECIPE["BodyMass"],
        "PecsLower": MUSCLE_RECIPE["PecsLower"],
        "BubbleButt": MUSCLE_RECIPE["BubbleButt"],
        "TorsoMassSmooth": TISSUE_RECIPE["TorsoMassSmooth"],
        "BellySmooth": TISSUE_RECIPE["BellySmooth"],
        "note": "no block in HIMBO Body - Vanilla.osd (the "
                "machinery's vocabulary); all five exist in SOS.osd "
                "but on a ~11k-vert base (max index 11006 vs "
                "Vanilla 9345) -- not index-compatible without new "
                "verification. Same gap as Sen's shipped build; "
                "Joe's open decision (FIX_NECK_FIELD.md). Effect: "
                "this build UNDERSTATES Jorge's softness."},
    "excluded_with_precedent": {
        "Lean -1.00": "two-sided, sign-ambiguous (v4 precedent)",
        "TorsoWaistSize -0.65": "Shrink Waist semantics; waist "
                                "routed via TorsoLower + LHandles "
                                "+ belly core (R18)",
        "TorsoBelly 0.75 / TorsoBellyChub 0.80": "HIMBO belly "
                                "stack replaced by the v4/v5.1 "
                                "belly system"},
    "cv": cv_report,
    "scorecard": score_rows,
    "grades": {"base": G_BASE, "muscle_system": G_MUSC,
               "combined": G_COMB},
    "broadness": {
        "chest_width_base_cm": G_BASE["chest_w"] * 100,
        "chest_width_build_cm": G_COMB["chest_w"] * 100,
        "chest_width_ratio": float(M13_RATIO),
        "waist_width_base_cm": G_BASE["waist_w"] * 100,
        "waist_width_build_cm": G_COMB["waist_w"] * 100,
        "delt_span_base_cm": G_BASE["delt_span"] * 100,
        "delt_span_build_cm": G_COMB["delt_span"] * 100},
    "side_mass": {"as_composed": SM_BEFORE,
                  "correction": "none -- measured only (the "
                                "strongman flank-correction table "
                                "is Sen-recipe-specific)"},
    "m9_volume_gain": vol_gain,
    "m10_tissue_share_proxy": tissue_share,
    "attenuation": {"core_min": float(att_M.min()),
                    "core_verts": int((att_M < 0.999).sum()),
                    "width_min": float(att_W.min()),
                    "width_verts": int((att_W < 0.999).sum()),
                    "tissue_min": float(att_T.min()),
                    "tissue_verts": int((att_T < 0.999).sum())},
    "repair_trajectories": {"core": traj_M, "width": traj_W,
                            "tissue": traj_T},
    "flips_final_float": {
        "raw_core": int(flipped(mh_pos, M_field).sum()),
        "raw_width": int(flipped(mh_pos, W_field).sum()),
        "raw_muscle_system": int(flipped(mh_pos,
                                         M_field + W_field).sum()),
        "raw_tissue": int(flipped(mh_pos, T_field).sum()),
        "raw_combined": int(flipped(
            mh_pos, M_field + W_field + T_field + TERM_FIELD).sum()),
        "macro_combined": int(flipped(
            mh_pos_mac,
            M_field + W_field + T_field + TERM_FIELD).sum())},
    "export": {
        "scale": EXPORT_SCALE,
        "height_m_at_base_scale": G_COMB["height_m"],
        "height_m_export": G_COMB["height_m"] * EXPORT_SCALE,
        "volume_L_at_base_scale": G_COMB["volume_L"],
        "volume_L_export": V_EXPORT_L,
        "mass_estimate": {
            "basis": "export volume x density; the person file "
                     "records NO mass for Jorge -- estimate only",
            "kg_at_1.00_kg_per_L": V_EXPORT_L,
            "kg_band_0.95_1.05": [V_EXPORT_L * 0.95,
                                  V_EXPORT_L * 1.05],
            "lbs_at_1.00": V_EXPORT_L * 2.20462}},
}
np.savez_compressed(WORK / "jorge_fields.npz",
                    muscle_core_canonical_m=M_field,
                    chest_width_canonical_m=W_field,
                    tissue_canonical_m=T_field,
                    terminal_canonical_m=TERM_FIELD,
                    region_weights=W3, tau=np.float64(TAU),
                    att_muscle=att_M, att_width=att_W,
                    att_tissue=att_T)
(WORK / "qa_jorge_body.json").write_text(json.dumps(
    qa_doc, indent=1, default=float))
print("wrote targets + work/jorge_fields.npz + "
      "work/qa_jorge_body.json (ship gate follows)")


# ------------------------------------------- quantised ship gate
# House rule (from the hyper pass): gates run on the SHIPPED numbers
# -- the 0.1 mm-quantised .target files parsed back from disk --
# requiring 0 flips AND min normalised face dot >= 0.01 on BOTH
# bases, for every component solo and the full sum. Repair follows
# the neckfix precedent (bara-proof/work/
# repair_neckfix_quantised.py): attenuation IN QUANTISED SPACE,
# bad verts x0.90 / neighbours x0.97, judged with a 0.02 band until
# nothing sits below the 0.01 floor.
sys.path.insert(0, str(V2 / "hyper" / "scripts"))
from hyper_common import body_edges as _hc_edges          # noqa: E402
from hyper_common import dequantise as _hc_dequantise     # noqa: E402
from hyper_common import face_dots as _hc_face_dots       # noqa: E402
from hyper_common import fold_stats as _hc_fold_stats     # noqa: E402
from hyper_common import load_base as _hc_load_base       # noqa: E402
from hyper_common import load_macro as _hc_load_macro     # noqa: E402
from hyper_common import load_target as _hc_load_target   # noqa: E402
from hyper_common import quantise as _hc_quantise         # noqa: E402

_V, _F, _Fb = _hc_load_base()
_Vm = _hc_load_macro(_V)
_EDGES = _hc_edges(_Fb)
_PATHS = {"muscle": TG / "body.muscle.target",
          "width": TG / "body.chest.width.target",
          "tissue": TG / "body.tissue.jorge.target",
          "terminal": TG / "body.belly.protrusion_terminal_v51.target"}
_NOTES = {"muscle": NOTE_M, "width": NOTE_W, "tissue": NOTE_T,
          "terminal": NOTE_E}
_qc = {k: _hc_quantise(_hc_load_target(p)) for k, p in _PATHS.items()}
_FULL = ("muscle", "width", "tissue", "terminal")
_JUDGE = {"muscle": [("muscle",), ("muscle", "width"), _FULL],
          "width": [("width",), ("muscle", "width"), _FULL],
          "tissue": [("tissue",), _FULL],
          "terminal": [("terminal",), _FULL]}
_CHECKS = [("muscle",), ("width",), ("tissue",), ("terminal",),
           ("muscle", "width"), _FULL]


def _delta(names):
    return sum(_hc_dequantise(_qc[n]) for n in names)


def _gate_report():
    rep = {}
    for names in _CHECKS:
        D = _delta(names)
        rep["+".join(names)] = {
            bn: [int(nf), float(md)]
            for bn, (nf, md) in (
                ("raw", _hc_fold_stats(_V, _Fb, D)),
                ("macro", _hc_fold_stats(_Vm, _Fb, D)))}
    return rep


def _fails(rep):
    return any(nf > 0 or md < 0.01
               for chk in rep.values() for nf, md in chk.values())


_gate0 = _gate_report()
print("ship gate (quantised, as first written):")
for k, v in _gate0.items():
    print(f"  {k:36s} raw {v['raw'][0]} flips min_dot "
          f"{v['raw'][1]:+.5f} | macro {v['macro'][0]} flips "
          f"min_dot {v['macro'][1]:+.5f}")
_repairs = {}
if _fails(_gate0):
    for comp in ("muscle", "width", "tissue", "terminal"):
        judged = _JUDGE[comp]

        def _bad(judged=judged):
            weak = set()
            ok = True
            for names in judged:
                D = _delta(names)
                for base in (_V, _Vm):
                    dots = _hc_face_dots(base, _Fb, D)
                    if dots.min() < 0.01:
                        ok = False
                    weak.update(
                        np.where(dots < 0.02)[0].tolist())
            return ok, weak

        ok, weak = _bad()
        if ok and not weak:
            continue
        att_total = np.ones(NB)
        rounds = 0
        for rounds in range(1, 601):
            badv = np.unique(_Fb[sorted(weak)].ravel())
            nbr = np.unique(_EDGES[
                np.isin(_EDGES[:, 0], badv)
                | np.isin(_EDGES[:, 1], badv)].ravel())
            att = np.ones(NB)
            att[badv] *= 0.90
            att[np.setdiff1d(nbr, badv)] *= 0.97
            _qc[comp] = np.round(_qc[comp] * att[:, None], 3)
            att_total *= att
            ok, weak = _bad()
            if ok and not weak:
                break
        else:
            raise SystemExit(
                f"quantised repair of {comp} did not converge")
        dev = np.linalg.norm(
            _hc_dequantise(_qc[comp])
            - _hc_load_target(_PATHS[comp]), axis=1)
        _repairs[comp] = {
            "rounds": rounds,
            "verts_changed": int((att_total < 0.999).sum()),
            "att_min": float(att_total.min()),
            "deviation_max_mm": float(dev.max() * 1000)}
        n_rw = write_target(
            _PATHS[comp], _hc_dequantise(_qc[comp]),
            _NOTES[comp] + f" REPAIRED in quantised space Nov 16, "
            f"2026 ({rounds} rounds of attenuation) to clear the "
            f"ship gate: 0 flips, min_dot >= 0.01 on both bases, "
            f"solo and composed. See JORGE_BUILD.md.")
        print(f" quantised repair: {comp}: {rounds} rounds, "
              f"{_repairs[comp]['verts_changed']} verts attenuated, "
              f"max deviation {dev.max()*1000:.2f} mm; target "
              f"rewritten ({n_rw} moved verts)")
    n_c2 = write_target(
        TG / "body.jorge.target", _delta(_FULL),
        NOTE_C + " Rewritten Nov 16, 2026 from the quantised-"
                 "repaired components.")
    print(f" combined target rewritten from repaired components "
          f"({n_c2} moved verts)")
_gate1 = _gate_report()
print("ship gate (quantised, final):")
for k, v in _gate1.items():
    print(f"  {k:36s} raw {v['raw'][0]} flips min_dot "
          f"{v['raw'][1]:+.5f} | macro {v['macro'][0]} flips "
          f"min_dot {v['macro'][1]:+.5f}")
assert not _fails(_gate1), "SHIP GATE FAILED after repair"

# shipped numbers, parsed back from disk: grade + persist
_ship = {k: _hc_load_target(p) for k, p in _PATHS.items()}
_delta_ship = sum(_ship.values())
G_SHIP = grade(mh_pos_mac + _delta_ship, mh_lab)
qa_doc["ship_gate_quantised"] = {
    "rule": "0 flips AND min normalised face dot >= 0.01, both "
            "bases (raw base.obj frame + MPFB macro frame), every "
            "component solo and the full sum, on the shipped "
            "0.1 mm-quantised targets parsed back from disk",
    "as_first_written": _gate0,
    "quantised_repairs": _repairs,
    "final": _gate1}
qa_doc["grades"]["shipped_quantised"] = G_SHIP
V_SHIP_EXPORT_L = G_SHIP["volume_L"] * EXPORT_SCALE ** 3
qa_doc["export"]["volume_L_export_shipped"] = V_SHIP_EXPORT_L
qa_doc["export"]["mass_estimate_shipped_kg_at_1.00"] = \
    V_SHIP_EXPORT_L
qa_doc["export"]["mass_estimate_shipped_lbs_at_1.00"] = \
    V_SHIP_EXPORT_L * 2.20462
qa_doc["export"]["height_m_export_shipped"] = \
    G_SHIP["height_m"] * EXPORT_SCALE
(WORK / "qa_jorge_body.json").write_text(json.dumps(
    qa_doc, indent=1, default=float))
_bf = dict(np.load(WORK / "jorge_fields.npz"))
_bf["delta_jorge_shipped_m"] = _delta_ship
_bf["muscle_shipped_m"] = _ship["muscle"]
_bf["width_shipped_m"] = _ship["width"]
_bf["tissue_shipped_m"] = _ship["tissue"]
_bf["terminal_shipped_m"] = _ship["terminal"]
np.savez_compressed(WORK / "jorge_fields.npz", **_bf)
print(f"shipped grade: height {G_SHIP['height_m']:.4f} m, volume "
      f"{G_SHIP['volume_L']:.2f} L, M4 {G_SHIP['M4_chest_waist']:.3f}"
      f"; export x1.39: height "
      f"{G_SHIP['height_m'] * EXPORT_SCALE:.3f} m, volume "
      f"{V_SHIP_EXPORT_L:.1f} L")
print("JORGE BUILD DONE")
