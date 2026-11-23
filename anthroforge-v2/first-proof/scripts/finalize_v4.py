#!/usr/bin/env python3
"""Finalize belly v4: recompute the corrected silhouette metrics and
write the slider JSON.

Why "corrected": three of the build script's first-pass metrics were
flawed, found on inspection (full story in GRAVITY_V4.md):
  M2  minimised over ALL front-low verts -> trivially lands on the
      crotch verts. Corrected: lowest deformed z among front verts
      carrying > 2 cm of added radial tissue (the apron's bottom edge).
  M3  the girth window straddled the heights where the hanging ARMS
      enter the radius gate, so "waist girth" was an arm-inclusive
      ellipse. Corrected: torso-only gate (base radius < 0.215 m) and
      BOTH definitions reported -- narrowest-point waist AND the
      clinical navel-level waist (the one the obesity literature's
      waist:hip ~1.0 refers to).
  M4  compared ring gradient to the median gradient elsewhere
      (anatomy-dominated). Corrected: deformed-vs-BASE max gradient
      inside the same ring bands (ratio 1.0 = no added step).
  M7b the waist window's argmin sat at the window edge / arm artefact.
      Corrected: interior local minima of the torso-only width
      profile, plus the flank roll/pinch read directly off the profile.
"""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
OUT = HERE.parent
V2 = OUT.parent
if str(V2) not in sys.path:
    sys.path.insert(0, str(V2))

from body_machinery import (  # noqa: E402
    BODY_END,
    compute_axis,
    girth_ellipse as girth_of,
    load_mpfb_base_obj,
    torso_cylindrical,
)

WORK = OUT / "work"
MPFB_ZIP = Path.home() / "workspace/stick-figure-avatar/photoreal/tools/mpfb2.zip"

corr = np.load(WORK / "correspondence.npz")
B = corr["mh_mask"].astype(np.float64)
h_star = float(corr["h_star"])
mh_crotch, mh_neck = [float(x) for x in corr["mh_landmarks"]]
L_mh = mh_neck - mh_crotch
D3 = np.load(WORK / "belly_v3.npz")["delta_v3_canonical_m"].astype(np.float64)
D4 = np.load(WORK / "belly_v4.npz")["delta_v4_canonical_m"].astype(np.float64)
mh_pos = load_mpfb_base_obj(MPFB_ZIP)
mh_body = np.zeros(len(mh_pos), bool); mh_body[:BODY_END] = True

ctr, axis = compute_axis(mh_pos, mh_body)
_, mh_th, ax, mh_r = torso_cylindrical(mh_pos, ctr, axis, mh_crotch, mh_neck)
er = np.stack([np.sin(mh_th), np.cos(mh_th)], axis=1)
gate_all = mh_body & (mh_r < 0.30)
gate_torso = mh_body & (mh_r < 0.215)

step = 0.0125
zs = np.arange(mh_crotch - 0.05, mh_neck + 0.02, step)
hh = (zs - mh_crotch) / L_mh
def profiles(P, gate):
    W = np.full(len(zs), np.nan); Dp = np.full(len(zs), np.nan)
    for i, z in enumerate(zs):
        m = gate & (np.abs(mh_pos[:, 2] - z) < step * 0.75)
        if m.sum() >= 8:
            W[i] = P[m, 0].max() - P[m, 0].min()
            Dp[i] = P[m, 1].max() - P[m, 1].min()
    return W, Dp

def corrected(D):
    out = {}
    drad = np.einsum("ij,ij->i", D[:, :2], er)
    sel = gate_all & (np.abs(mh_th) < 0.7) & (drad > 0.02)
    out["M2_apron_bottom_above_crotch_cm"] = (
        round(float((mh_pos[sel, 2] + D[sel, 2]).min() - mh_crotch) * 100, 2)
        if sel.any() else None)
    W, Dp = profiles(mh_pos + D, gate_torso)
    G = girth_of(W, Dp)
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
    chest_win = (hh > 0.80) & (hh < 0.90)
    out["chest_width_cm"] = round(float(np.nanmean(W[chest_win])) * 100, 1)
    # flank roll / pinch read off the width profile
    seg = (hh > 0.10) & (hh < 0.52)
    idx = np.where(seg)[0]
    ipk = idx[int(np.nanargmax(W[idx]))]
    above = (hh > hh[ipk] + 0.10) & (hh < hh[ipk] + 0.24)
    out["flank_roll_peak"] = {"h": round(float(hh[ipk]), 3),
                              "width_cm": round(float(W[ipk]) * 100, 1)}
    out["flank_pinch_above_roll_cm"] = round(
        float(W[ipk] - np.nanmin(W[above])) * 100, 1)
    return out

c_base = corrected(np.zeros_like(mh_pos))
c_v3 = corrected(D3)
c_v4 = corrected(D4)
# M4' ring gradient ratio (arm-inclusive gate like the build, but the
# denominator is the BASE profile in the same bands)
def ring_ratio(D):
    ring = np.zeros(len(zs), bool)
    for i, z in enumerate(zs):
        m = gate_all & (np.abs(mh_pos[:, 2] - z) < step * 0.75)
        if m.sum() >= 8:
            ring[i] = 0.05 < B[m].max() < 0.95
    def mg(P):
        W, _ = profiles(P, gate_all)
        g = np.abs(np.diff(W)) / step
        idx = np.where(ring[1:-1])[0]
        return float(np.nanmax(g[idx]))
    return round(mg(mh_pos + D) / mg(mh_pos), 2)
m4 = {"v3": ring_ratio(D3), "v4": ring_ratio(D4)}
print("corrected base:", c_base)
print("corrected v3:", c_v3)
print("corrected v4:", c_v4)
print("M4' ratios:", m4)

qa = json.loads((WORK / "qa_numbers_v4.json").read_text())
qa["corrected_metrics"] = {"note": "supersede the same-named first-pass "
    "metrics in qa.metrics where definitions overlap; see GRAVITY_V4.md",
    "base": c_base, "v3": c_v3, "v4": c_v4, "M4_ring_gradient_ratio": m4}
(WORK / "qa_numbers_v4.json").write_text(json.dumps(qa, indent=1))

bl = json.loads((WORK / "blender_v4_numbers.json").read_text())
m = qa["model"]; fs = qa["fold_scan"]["+1 (combined)"]
nav_b = bl["w+1.0"]
slider = {
    "id": "body.belly.protrusion",
    "label": "Body adiposity (belly-centred)",
    "group": "body/torso",
    "version": 4,
    "supersedes": "body.belly.protrusion.slider_v3.json (v3, belly-only gravity)",
    "symmetry": "bilateral_x",
    "range": {"min": -1, "max": 1, "default": 0, "safe_max": 1.0,
              "endpoint_anchor": "belly core unchanged from v1/v3: max forward "
              "displacement at navel 0.1197 m on hm08 (Fat Males anchor scaled "
              "by torso-length ratio 0.8325); distribution layer calibrated "
              "separately (flank match, alpha capped 2.0) -- see distribution"},
    "region": {"landmarks": ["navel", "sternum_bottom", "pelvis_top"],
               "mask_rule": "belly core: v1 geodesic mask (r = 0.35 x torso_len) "
               "crossfaded against the whole-torso distribution field across "
               "the mask ring; distribution weight covers h in [-0.08, 1.03] "
               "of the torso parameter, graph-smoothed"},
    "semantics": "Whole-torso adiposity SYSTEM (FAT_REFERENCE.md): the v3 pendant "
        "belly (drain/descent/drape, gamma=2) embedded in a learned fat-"
        "distribution field -- chest, flanks/love-handles, back, hips/glutes, "
        "shoulder roots -- with a posture shear (anterior pelvic tilt lobe + "
        "compensating chest lobe, kept after passing its effect gate). At +1 "
        "the silhouette is one heavy torso: waist girth +20 cm at the "
        "narrowest point, hips +11 cm, chest width +4.8 cm, back band +5.6 cm "
        "mean radial; no silhouette step at the old belly-mask boundary "
        "(ring gradient ratio 1.28 vs base). Limbs are NOT covered (v5 scope).",
    "system": {
        "model": "D4 = LIN + SAG; LIN = B*D_protrusion + (1-B)*D_distribution "
                 "+ D_crease(0: learned fields already carry the flank crease) "
                 "+ D_posture; SAG = B * D_sag3 (v3, gamma = 2.0)",
        "distribution": {
            "blend": "0.5 * Fat Males full-torso field + 0.5 * alpha * HIMBO "
                     "Chonky field (each scaled by its torso-length ratio)",
            "alpha_himbo_calibration": m["alpha_himbo_calibration"],
            "calibration": "flank-band match (mean |radial| over |theta| "
                "1.1-1.9, h 0.3-0.6): the sources DISAGREE on the belly front "
                f"(Fat Males peak {m['fm_peak_cm']:.1f} cm vs Chonky "
                f"{m['himbo_peak_cm']:.1f} cm -- pot-belly vs broad-mass "
                "bodies), so they are matched where the distribution's job "
                "lives and the belly core stays D_protrusion/D_sag3's job. "
                "Alpha hit its 2.0 cap: even doubled, Chonky's flanks are "
                "the lighter of the two; the blend leans Fat Males there.",
            "s_fm": m["s_fm"], "s_hi": m["s_hi"],
            "himbo_recipe_used": m["himbo_recipe_used"],
            "himbo_recipe_missing": m["himbo_recipe_missing"],
            "shipped_scale": m["shipped_dist_scale"]},
        "field_cross_validation_cm": m["fields"],
        "posture": m["posture"],
        "whole_torso_gate": "fold repair and the 0-flip gate run over ALL "
            "12,298 torso faces (both bases), not just the belly patch",
    },
    "gravity": {
        "coupling": {"formula": "shape(w) = base + w * LIN + f(w) * SAG",
                     "f": "sign(w) * |w|^gamma", "gamma": 2.0, "f_at_0.5": 0.25},
        "fold_repair": f"attenuation repair over the whole torso: "
            f"{m['attenuation']['rounds']} rounds, min attenuation "
            f"{m['attenuation']['min']:.2f}, {m['attenuation']['verts_under_0.99']} "
            f"verts touched (the distribution fields are intrinsically smooth; "
            f"contrast v3's 40 rounds / 509 verts)",
        "shipped_distribution_scale": m["shipped_dist_scale"],
    },
    "qa": {
        "fold_scan_+1_both_bases": fs,
        "fold_scan_full": qa["fold_scan"],
        "navel_anchor": {"anchor_forward_m": qa["navel"]["anchor_forward_m"],
                         "v4_at_+1_numpy": qa["navel"]["v4_at_+1"],
                         "v4_at_+1_blender_cm": {"forward": round(nav_b["forward_cm"], 2),
                                                 "down": round(nav_b["down_cm"], 2)}},
        "metrics_first_pass": {"v3": qa["metrics_v3"], "v4": qa["metrics_v4"],
                               "pinch": {"v3": qa["pinch_v3"], "v4": qa["pinch_v4"]}},
        "metrics_corrected": qa["corrected_metrics"],
        "zones": qa["zones"], "zones_all_triangle_exact": qa["zones_all_triangle_exact"],
        "blender_evaluated_belly_region": bl["eval_belly_region"],
    },
    "instances": {"makehuman_hm08": {
        "base": "hm08 (MPFB2 base.obj vertex order, 19158 verts; pure delta vs "
                "the macro-neutral base)",
        "file": "body.belly.protrusion_v4.target",
        "components": {
            "combined_at_+1": "body.belly.protrusion_v4.target (= LIN_v4 + SAG_v3, "
                              "for hosts without coupling support)",
            "distribution_component": "body.belly.distribution_v4.target "
                "(= D4 - D3: everything v4 adds over v3 -- the distribution, "
                "posture and crossfade; stack it on v3 to reproduce v4, or use "
                "it standalone as a torso-mass layer under a different belly)",
            "protrusion": "body.belly.protrusion.target (v1, unchanged)",
            "sag": "body.belly.protrusion_sag_v3.target (v3, unchanged)"}}},
    "provenance": {
        "source": "belly core: Fat Males morph (Skyrim) transferred v1. "
            "Distribution: 50/50 blend of (a) the Fat Males full-torso morph "
            "and (b) the HIMBO 'Chonky' preset recipe (17 Vanilla OSD blocks "
            "at the preset's big values; SamuelLike/FemmeB/FemmeBooba excluded "
            "-- other sets, one a body-swap; BellySmooth absent from the "
            "Vanilla OSD; TorsoWaistSize excluded -- direction ambiguous, its "
            "display name decodes to 'Shrink Waist'), each transferred by the "
            "v1 (h, theta) kernel machinery and flank-calibrated (alpha = "
            f"{m['alpha_himbo_calibration']:.2f}, capped). Rules: FAT_REFERENCE.md.",
        "method": "scripts/build_belly_v4.py (+ analyze/finalize scripts)",
        "licence": "STUDY-ONLY / internal. Derived from Fat Males + HIMBO "
            "material under Joe's Nov 12, 2026 licence ruling (no AI-training "
            "use). NOT a CC0 MakeHuman asset; do not ship with stock MPFB "
            "content or redistribute."},
}
(OUT / "body.belly.protrusion.slider_v4.json").write_text(json.dumps(slider, indent=1))
print("slider v4 JSON written")
