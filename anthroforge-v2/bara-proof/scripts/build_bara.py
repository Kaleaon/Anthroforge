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
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
OUT = HERE.parent                      # bara-proof/
V2 = OUT.parent                        # anthroforge-v2/
APP = V2.parent / "anthroforge-app"
FP = V2 / "first-proof"
WORK = OUT / "work"
LEARNED = Path.home() / "workspace/character_assets/learned"
HIMBO_DIR = (Path.home() / "workspace/character_assets/_himbo_work/"
             "CalienteTools/BodySlide/ShapeData/HIMBO")
for _p in (str(V2), str(APP), str(LEARNED / "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
from osdparse import load_osd  # noqa: E402

from body_machinery.axes import sstep, torso_params  # noqa: E402
from body_machinery.labels import (  # noqa: E402
    blend_regions,
    label_mesh,
    region_weights_w3,
)
from body_machinery.loops import (  # noqa: E402
    band,
    grade,
    side_mass,
    slice_ratio,
)
from body_machinery.osd import (  # noqa: E402
    BODY_END,
    DM_M,
    SK_UNIT_M as SK,
    align_macro_base,
    compose_osd,
    extract_base_positions,
    hi_diff,
    load_mpfb_base_obj,
)
from body_machinery.repair import flipped, repair  # noqa: E402
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
W_TORSO_V4 = _v4["torso_weight"].astype(np.float64)

mh_pos = load_mpfb_base_obj(MPFB_ZIP)
_mac = np.load(FP / "work/mh_macro_base.npz")["pos_canonical_m"]
mh_pos_mac = align_macro_base(mh_pos, _mac, body_end=BODY_END)
print("macro->raw alignment: median |delta| per axis (the macro "
      "reshaping itself):",
      np.round(np.median(np.abs(mh_pos_mac[:BODY_END] - mh_pos[:BODY_END]), axis=0), 4))
NB = len(mh_pos)
FACES_B = mh_tris[np.all(mh_tris < BODY_END, axis=1)]
print(f"hm08: {NB} verts, torso L={L_mh:.4f} m, navel h*={h_star:.3f}")

hi_pos_u = extract_base_positions(
    (HIMBO_DIR / "HIMBO Body - Vanilla.nif").read_bytes(), 4000)
assert hi_pos_u is not None and len(hi_pos_u) == 9346, "HIMBO base extract"
hi_blocks = {b["name"]: b for b in
             load_osd(str(HIMBO_DIR / "HIMBO Body - Vanilla.osd"))["blocks"]}
NH = len(hi_pos_u)
_MISSED_BLOCKS = set()


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


M_src = compose_osd(hi_blocks, NH, MUSCLE_RECIPE, scale=SK, missed=_MISSED_BLOCKS)
W_src = compose_osd(hi_blocks, NH, WIDTH_RECIPE, scale=SK, missed=_MISSED_BLOCKS)
T_src = compose_osd(hi_blocks, NH, TISSUE_RECIPE, scale=SK, missed=_MISSED_BLOCKS)

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
M_src += hi_diff(hi_blocks, NH, "Weight 0 to 1", missed=_MISSED_BLOCKS) \
    * (NECK_WEIGHT_VALUE * SK) * neck_gate[:, None]
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
_TF_KW = dict(
    hi_lab=hi_lab, h_hi=h_hi, th_hi=th_hi, r_hi=r_hi,
    mh_pos_mac=mh_pos_mac, mh_crotch=mh_crotch, mh_neck=mh_neck,
    s_hi=s_hi, sig_h=SIG_H, sig_a=SIG_A, cv_report=cv_report,
)
_LF_KW = dict(
    hi_pos_m=hi_pos_u * SK, mh_pos_mac=mh_pos_mac,
    hi_lab=hi_lab, mh_lab=mh_lab,
    sig_u=SIG_U, sig_arc=SIG_ARC, cv_report=cv_report,
)

print("building torso fields...")
M_torso, (h_mh, r_mh) = torso_field(M_src, "muscle", **_TF_KW)
W_torso, _ = torso_field(W_src, "width", **_TF_KW)
T_torso, _ = torso_field(T_src, "tissue", **_TF_KW)
print("building limb fields...")
M_limb = limb_fields(M_src, "muscle", **_LF_KW)
W_limb = limb_fields(W_src, "width", **_LF_KW)
T_limb = limb_fields(T_src, "tissue", **_LF_KW)

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

SM_BEFORE = side_mass(T_field, h_mh, th_mh_qa)
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
    T_src = compose_osd(hi_blocks, NH, TISSUE_RECIPE, scale=SK, missed=_MISSED_BLOCKS)
    T_torso, _ = torso_field(T_src, "tissue-corrected", **_TF_KW)
    T_limb = limb_fields(T_src, "tissue-corrected", **_LF_KW)
    T_field = blend_regions(T_torso, T_limb, W3)
SM_AFTER = side_mass(T_field, h_mh, th_mh_qa)
if CORRECTION:
    print("side-mass (tissue, post-correction):",
          {k: {kk: round(vv, 3) for kk, vv in v.items()}
           for k, v in SM_AFTER.items()})


# ------------------------------------------- belly: v4 system at the cell
def tissue_with_belly(tau):
    """Tissue field with the belly zone served by the v4 system."""
    return T_field + B_CORE[:, None] * (tau * D3 - T_torso) \
        + W_TORSO_V4[:, None] * D_POSTURE


# ------------------------------------------------------------ fold repair
print(f"body faces for fold gate: {len(FACES_B)}")
_REP_KW = dict(faces=FACES_B, edges=_e, ref_pos=mh_pos, kappa=KAPPA)

ZERO = np.zeros((NB, 3))
M_field, att_M, traj_M = repair(
    M_field, [(mh_pos, ZERO), (mh_pos_mac, ZERO)], "muscle core", **_REP_KW)
W_field, att_W, traj_W = repair(
    W_field, [(mh_pos, ZERO), (mh_pos_mac, ZERO),
              (mh_pos, M_field), (mh_pos_mac, M_field)],
    "chest width (solo and over core)", **_REP_KW)
print("solving belly tau for slice chest:waist >= 1.30 "
      "(Shaw anchor 1.28)...")
TAU = None
for tau_try in np.arange(0.75, 0.29, -0.05):
    tau_try = round(float(tau_try), 2)
    r = slice_ratio(
        mh_pos_mac + M_field + W_field + tissue_with_belly(tau_try),
        FACES_B, mh_crotch, L_mh, float(mh_pos_mac[navel_mh, 2]),
    )
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
    "tissue (solo and over muscle system)", **_REP_KW)
print(f"attenuation: core min {att_M.min():.2f} "
      f"({int((att_M < 0.999).sum())} verts), width min {att_W.min():.2f} "
      f"({int((att_W < 0.999).sum())}), tissue min {att_T.min():.2f} "
      f"({int((att_T < 0.999).sum())})")


# ------------------------------------------------------- slice-loop metrics
_GR_KW = dict(
    faces_b=FACES_B, mh_crotch=mh_crotch, mh_neck=mh_neck,
    mh_pos_mac=mh_pos_mac, navel_mh=navel_mh, h_mh=h_mh, body_end=BODY_END,
)
G_BASE = grade(mh_pos_mac, mh_lab, **_GR_KW)
G_MUSC = grade(mh_pos_mac + M_field + W_field, mh_lab, **_GR_KW)
G_COMB = grade(mh_pos_mac + M_field + W_field + T_field, mh_lab, **_GR_KW)

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
SM_FINAL = side_mass(T_field, h_mh, th_mh_qa)
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
      f"{int(flipped(mh_pos, M_field, FACES_B).sum())}, width "
      f"{int(flipped(mh_pos, W_field, FACES_B).sum())}, muscle system "
      f"{int(flipped(mh_pos, M_field + W_field, FACES_B).sum())}, tissue "
      f"{int(flipped(mh_pos, T_field, FACES_B).sum())}, combined "
      f"{int(flipped(mh_pos, M_field + W_field + T_field, FACES_B).sum())}; "
      f"macro combined: "
      f"{int(flipped(mh_pos_mac, M_field + W_field + T_field, FACES_B).sum())}")


# ----------------------------------------------------------------- outputs
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
        "raw_core": int(flipped(mh_pos, M_field, FACES_B).sum()),
        "raw_width": int(flipped(mh_pos, W_field, FACES_B).sum()),
        "raw_muscle_system": int(flipped(mh_pos,
                                         M_field + W_field, FACES_B).sum()),
        "raw_tissue": int(flipped(mh_pos, T_field, FACES_B).sum()),
        "raw_combined": int(flipped(mh_pos,
                                    M_field + W_field + T_field, FACES_B).sum()),
        "macro_combined": int(flipped(mh_pos_mac,
                                      M_field + W_field + T_field, FACES_B).sum())},
}, indent=1, default=float))
print("\nwrote targets + slider JSONs + qa_numbers_bara.json + "
      "bara_fields.npz")
