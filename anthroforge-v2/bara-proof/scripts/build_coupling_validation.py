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
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
OUT = HERE.parent                      # bara-proof/
V2 = OUT.parent                        # anthroforge-v2/
FP = V2 / "first-proof"
WORK = OUT / "work"
APP = V2.parent / "anthroforge-app"
LEARNED = Path.home() / "workspace/character_assets/learned"
HIMBO_DIR = (Path.home() / "workspace/character_assets/_himbo_work/"
             "CalienteTools/BodySlide/ShapeData/HIMBO")
for _p in (str(V2), str(APP), str(LEARNED / "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from body_machinery.axes import sstep, torso_params  # noqa: E402
from body_machinery.labels import label_mesh  # noqa: E402
from body_machinery.loops import (  # noqa: E402
    best_loop,
    girths,
    grade,
)
from body_machinery.osd import (  # noqa: E402
    BODY_END,
    DM_M,
    SK_UNIT_M as SK,
    align_macro_base,
    extract_base_positions,
    hi_diff,
    load_mpfb_base_obj,
)
from body_machinery.repair import (  # noqa: E402
    body_edges,
    fold_stats,
    lap_smooth,
    repair_inc,
)
from body_machinery.transfer import torso_field  # noqa: E402
from core.geometry import write_target  # noqa: E402
from core.sliders import (  # noqa: E402
    CouplingRegistry,
    SliderRegistry,
    evaluate_effective_vector,
)

MPFB_ZIP = Path.home() / "workspace/stick-figure-avatar/photoreal/tools/mpfb2.zip"
KAPPA = 0.55
MACRO_NAMES = ["chest", "waist", "hips_glutes", "thighs"]

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


def load_coupling_validation_context():
    """Load meshes, transferred definition/neck fields, evaluator states,
    and region factor maps shared by ``build_coupling_validation.py``,
    ``measure_coupling_validation.py``, and ``measure_coupling_hip.py``."""
    from osdparse import load_osd

    R = {"evaluator": {}, "selfcheck": {}, "gachidebu": {}, "pear": {},
         "bigchest": {}, "crease": {}, "folds": {}, "zone_residuals": {}}

    corr = np.load(FP / "work/correspondence.npz")
    B_CORE = corr["mh_mask"].astype(np.float64)
    h_star = float(corr["h_star"])
    mh_crotch, mh_neck = [float(x) for x in corr["mh_landmarks"]]
    navel_mh = int(corr["navel_mh"])
    mh_tris = corr["mh_tris"]
    L_mh = mh_neck - mh_crotch

    mh_pos = load_mpfb_base_obj(MPFB_ZIP)
    _mac = np.load(FP / "work/mh_macro_base.npz")["pos_canonical_m"]
    mh_pos_mac = align_macro_base(mh_pos, _mac, body_end=BODY_END)
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

    hi_pos_u = extract_base_positions(
        (HIMBO_DIR / "HIMBO Body - Vanilla.nif").read_bytes(), 4000)
    assert hi_pos_u is not None and len(hi_pos_u) == 9346, "HIMBO base extract"
    hi_blocks = {b["name"]: b for b in
                 load_osd(str(HIMBO_DIR / "HIMBO Body - Vanilla.osd"))["blocks"]}
    NH = len(hi_pos_u)
    edges = body_edges(mh_tris, body_end=BODY_END)

    h_hi, th_hi, r_hi, ax_hi, cr_hi, nk_hi, L_hi = torso_params(
        hi_pos_u * SK, verbose=False)
    s_hi = L_mh / L_hi
    hi_lab = label_mesh(hi_pos_u * SK, cr_hi, nk_hi)
    mh_lab = label_mesh(mh_pos_mac, mh_crotch, mh_neck, BODY_MASK)
    h_mh, th_mh, r_mh, ax_mh, _, _, _ = torso_params(
        mh_pos_mac, mh_crotch, mh_neck, "hm08")
    SIG_H, SIG_A = 0.05, 0.04
    cv_report = {}

    def _tf(delta, tag, sig_h=SIG_H, sig_a=SIG_A):
        out, _ = torso_field(
            delta, tag,
            hi_lab=hi_lab, h_hi=h_hi, th_hi=th_hi, r_hi=r_hi,
            mh_pos_mac=mh_pos_mac, mh_crotch=mh_crotch, mh_neck=mh_neck,
            s_hi=s_hi, sig_h=sig_h, sig_a=sig_a, cv_report=cv_report,
        )
        return out

    def blend_torso_only(torso_f):
        out = W3[:, 0:1] * torso_f
        return out / np.maximum(1.0, W3.sum(axis=1, keepdims=True))

    def _hd(name):
        return hi_diff(hi_blocks, NH, name, warn_missing=False)

    print("transferring unit definition fields + authored neck field...")
    DEF_SIG = (0.018, 0.014)
    F_VALLEYS_STD = blend_torso_only(_tf(_hd("ArmsTrapsValleys") * SK, "valleys-std"))
    F_VLINE_STD = blend_torso_only(_tf(_hd("TorsoVLine") * SK, "vline-std"))
    F_CREASE_STD = blend_torso_only(_tf(_hd("PecsCrease") * SK, "crease-std"))
    F_VALLEYS = blend_torso_only(_tf(_hd("ArmsTrapsValleys") * SK, "valleys", *DEF_SIG))
    F_VLINE = blend_torso_only(_tf(_hd("TorsoVLine") * SK, "vline", *DEF_SIG))
    F_CREASE = blend_torso_only(_tf(_hd("PecsCrease") * SK, "crease", *DEF_SIG))
    neck_gate = sstep(h_hi, 0.88, 0.96) * (1 - sstep(h_hi, 1.08, 1.18)) \
        * (1 - sstep(r_hi, 0.13, 0.20))
    NECK_EMB = blend_torso_only(_tf(
        _hd("Weight 0 to 1") * (0.90 * SK) * neck_gate[:, None],
        "neck")) * ATT_M[:, None]

    R["peak_recovery"] = {}
    for nm, F, Fs, srcname in (
            ("valleys", F_VALLEYS, F_VALLEYS_STD, "ArmsTrapsValleys"),
            ("vline", F_VLINE, F_VLINE_STD, "TorsoVLine"),
            ("crease", F_CREASE, F_CREASE_STD, "PecsCrease")):
        src_max = float(np.linalg.norm(_hd(srcname), axis=1).max() * SK)
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
              f"{mag.max()*100:.2f} (x{mag.max()/src_max:.2f})")
    mag = np.linalg.norm(NECK_EMB, axis=1)
    print(f" neck(authored, embedded): support "
          f"{int((mag > 0.0002).sum())}, max {mag.max()*100:.2f} cm")
    R["field_cv"] = cv_report

    reg = SliderRegistry.from_folder(APP / "library/sliders")
    coup = CouplingRegistry.from_folder(APP / "library/couplings")
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

    SEN_LEVEL = (0.55 * 0.80 + 0.25 * 0.75 + 0.20 * 0.65)
    GACHI_LEVEL = EV["gachidebu"].derived["tissue.level"]
    T_SCALE = GACHI_LEVEL / SEN_LEVEL
    print(f"tissue scale strongman-cell -> gachidebu: x{T_SCALE:.4f}")

    grade_kw = dict(
        faces_b=FACES_B, mh_crotch=mh_crotch, mh_neck=mh_neck,
        mh_pos_mac=mh_pos_mac, navel_mh=navel_mh, h_mh=h_mh,
        body_end=BODY_END,
    )
    G_SC = grade(mh_pos_mac + M_F + W_F + T_F, mh_lab, **grade_kw)
    G_BASE = grade(mh_pos_mac, mh_lab, **grade_kw)
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

    macro = np.zeros(NB, dtype=int)
    _torso = mh_lab["torso"]
    macro[_torso & (h_mh >= 0.44) & (h_mh < 0.70)
          & (np.abs(th_mh) <= 2.2)] = 1
    macro[_torso & (h_mh >= 0.02) & (h_mh < 0.44)] = 2
    macro[_torso & (h_mh < 0.02)] = 3
    macro[mh_lab["leg"]] = 3
    macro[mh_lab["arm"]] = 0
    ZONE_MASKS = {name: (macro == i) & BODY_MASK
                  for i, name in enumerate(MACRO_NAMES)}
    ZONE_MASKS["neck"] = _torso & (h_mh >= 0.98) & BODY_MASK
    ZONE_MASKS["arms"] = mh_lab["arm"] & BODY_MASK
    print("macro zones:", {k: int(v.sum()) for k, v in ZONE_MASKS.items()})

    def factor_map(factors, kind):
        f = np.array([factors[f"distribution.{kind}.{m}"]
                      for m in MACRO_NAMES])
        return lap_smooth(f[macro], BODY_MASK, edges, iters=3)

    return {
        "R": R, "B_CORE": B_CORE, "h_star": h_star,
        "mh_crotch": mh_crotch, "mh_neck": mh_neck, "navel_mh": navel_mh,
        "mh_tris": mh_tris, "L_mh": L_mh, "mh_pos": mh_pos,
        "mh_pos_mac": mh_pos_mac, "NB": NB, "FACES_B": FACES_B,
        "BODY_MASK": BODY_MASK, "edges": edges, "M_F": M_F, "W_F": W_F,
        "T_F": T_F, "W3": W3, "ATT_M": ATT_M, "TAU_BAR": TAU_BAR,
        "LIN5": LIN5, "SAG5": SAG5, "d5": d5, "hi_lab": hi_lab,
        "mh_lab": mh_lab, "h_mh": h_mh, "th_mh": th_mh, "r_mh": r_mh,
        "ax_mh": ax_mh, "F_VALLEYS": F_VALLEYS, "F_VLINE": F_VLINE,
        "F_CREASE": F_CREASE, "NECK_EMB": NECK_EMB, "reg": reg,
        "coup": coup, "EV": EV, "T_SCALE": T_SCALE, "G_SC": G_SC,
        "G_BASE": G_BASE, "ZONE_MASKS": ZONE_MASKS,
        "factor_map": factor_map, "grade_kw": grade_kw,
    }


def _rough(prof, used):
    p = prof[used]
    if len(p) < 6:
        return float("nan")
    k = np.ones(5) / 5
    sm = np.convolve(np.pad(p, 2, mode="edge"), k, "valid")
    return float(np.std(p - sm) * 1000.0)


def main():
    ctx = load_coupling_validation_context()
    R = ctx["R"]
    B_CORE = ctx["B_CORE"]
    h_star = ctx["h_star"]
    mh_crotch, mh_neck = ctx["mh_crotch"], ctx["mh_neck"]
    mh_pos, mh_pos_mac = ctx["mh_pos"], ctx["mh_pos_mac"]
    FACES_B, BODY_MASK, _e = ctx["FACES_B"], ctx["BODY_MASK"], ctx["edges"]
    M_F, W_F, T_F = ctx["M_F"], ctx["W_F"], ctx["T_F"]
    d5 = ctx["d5"]
    mh_lab = ctx["mh_lab"]
    h_mh, th_mh, ax_mh = ctx["h_mh"], ctx["th_mh"], ctx["ax_mh"]
    F_VALLEYS, F_VLINE, F_CREASE = ctx["F_VALLEYS"], ctx["F_VLINE"], ctx["F_CREASE"]
    NECK_EMB = ctx["NECK_EMB"]
    EV, T_SCALE, G_SC = ctx["EV"], ctx["T_SCALE"], ctx["G_SC"]
    ZONE_MASKS = ctx["ZONE_MASKS"]
    factor_map = ctx["factor_map"]
    grade_kw = ctx["grade_kw"]

    def radius_of(P):
        rel = P[:, :2] - ax_mh
        return np.linalg.norm(rel, axis=1)

    def core_window(F, frac=0.5):
        mag = np.linalg.norm(F, axis=1)
        core = np.where(mag >= frac * mag.max())[0]
        return core[core < BODY_END]

    def dip_theta(P, F, h_pad=0.04, nbins=20, span=1.3):
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
        if kind == "theta":
            d1, r1 = dip_theta(sub_pos + v * F, F, **kw)
            d0, _ = dip_theta(sub_pos, F, **kw)
            return d1 - d0, d1, r1
        a1, _, r1 = dip_h(sub_pos + v * F, F, **kw)
        a0, _, _ = dip_h(sub_pos, F, **kw)
        return a1 - a0, a1, r1

    def sector_audit(D, bands):
        er = np.stack([np.sin(th_mh), np.cos(th_mh)], axis=1)
        dr = np.abs(D[:, 0] * er[:, 0] + D[:, 1] * er[:, 1])
        drs = D[:, 0] * er[:, 0] + D[:, 1] * er[:, 1]
        out = {}
        for band_name, (h0, h1) in bands.items():
            hb = BODY_MASK & (h_mh >= h0) & (h_mh < h1)
            fr = hb & (np.abs(th_mh) < 0.5)
            fl = hb & (np.abs(th_mh) > 0.9) & (np.abs(th_mh) < 2.2)
            bk = hb & (np.abs(th_mh) > 2.7)
            f_ = float(dr[fr].mean() * 100) if fr.sum() else 0.0
            l_ = float(dr[fl].mean() * 100) if fl.sum() else 0.0
            b_ = float(dr[bk].mean() * 100) if bk.sum() else 0.0
            fs = float(drs[fr].mean() * 100) if fr.sum() else 0.0
            ls = float(drs[fl].mean() * 100) if fl.sum() else 0.0
            out[band_name] = {
                "front_cm": f_, "flank_cm": l_, "back_cm": b_,
                "flank_front": (l_ / f_) if f_ > 0 else 0.0,
                "flank_front_signed": (ls / fs) if fs > 0 else 0.0,
            }
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

    def _fstats(pos, delta):
        return fold_stats(pos, FACES_B, delta, flip_tol=-1e-12)

    def _rinc(base_delta, inc, label):
        return repair_inc(
            base_delta, inc, label,
            bases=((mh_pos, "raw"), (mh_pos_mac, "macro")),
            faces=FACES_B, edges=_e, ref_pos=mh_pos, kappa=KAPPA,
        )

    def fold_report(delta, label, store=True):
        fr_, md_ = _fstats(mh_pos, delta)
        fm_, mdm_ = _fstats(mh_pos_mac, delta)
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
    BASE_G = M_F + W_F + T_F
    INC_G = (T_SCALE - 1.0) * T_F + NECK_EMB * NECK_EFF_SCALE
    INC_G, att_g, traj_g = _rinc(BASE_G, INC_G, "gachidebu increment")
    DELTA_G = BASE_G + INC_G
    fold_report(DELTA_G, "gachidebu")
    R["folds"]["gachidebu"]["repair"] = {
        "att_min": float(att_g.min()),
        "verts_touched": int((att_g < 0.999).sum()),
        "trajectory": [int(t) for t in traj_g]}
    POS_G = mh_pos_mac + DELTA_G
    POS_G_RAWNECK = mh_pos_mac + (BASE_G + (T_SCALE - 1.0) * T_F + NECK_EMB)
    POS_SC_NECK = mh_pos_mac + BASE_G + NECK_EMB
    G_G = grade(POS_G, mh_lab, **grade_kw)
    G_G_RN = grade(POS_G_RAWNECK, mh_lab, **grade_kw)
    G_SCN = grade(POS_SC_NECK, mh_lab, **grade_kw)
    GH_G = girths(POS_G, mh_crotch, mh_neck, h_star, include_hip=True)
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
    TG_RING[B_CORE > 0.05] = 0.0
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
    GH_BASE = girths(mh_pos_mac, mh_crotch, mh_neck, h_star, include_hip=True)
    GH_SC = girths(mh_pos_mac + M_F + W_F + T_F, mh_crotch, mh_neck, h_star, include_hip=True)
    R["profile_girths"] = {"base": GH_BASE, "strongman_control": GH_SC}

    def hip_width(pos):
        Z = np.array([0.0, 0.0, 1.0])
        lp = best_loop(pos, FACES_B, Z, np.array([0, 0, mh_crotch + 0.05]))
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
        inc_m = muscle_w - (M_F + W_F)
        inc_m, att_m, traj_m = _rinc(M_F + W_F, inc_m,
                                     f"{tag} muscle weighting")
        muscle_w = M_F + W_F + inc_m
        tissue_w, att_t, traj_t = _rinc(muscle_w, tissue_w,
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
        G = grade(pos, mh_lab, **grade_kw)
        gh = girths(pos, mh_crotch, mh_neck, h_star, include_hip=True)
        gh0 = girths(pos0, mh_crotch, mh_neck, h_star, include_hip=True)
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
        fr, md = _fstats(mh_pos_mac, twin)
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
        fr, md = _fstats(mh_pos_mac, (sub - mh_pos_mac) + eff_v * F_CREASE)
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


if __name__ == "__main__":
    main()
