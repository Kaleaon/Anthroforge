#!/usr/bin/env python3
"""Finalize belly v5: write the slider JSON (v4 format) from the
build's QA numbers + the Blender numbers, and compose the labeled
v4-vs-v5 side-by-side renders (front + profile)."""
import json
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent.parent
WORK = HERE / "work"
RENDERS = HERE / "renders"
OUT = HERE

qa5 = json.loads((WORK / "qa_numbers_v5.json").read_text())
qa4 = json.loads((WORK / "qa_numbers_v4.json").read_text())
bl5 = json.loads((WORK / "blender_v5_numbers.json").read_text())
bl4 = json.loads((WORK / "blender_v4_numbers.json").read_text())
M = qa5["model"]

slider = {
    "id": "body.belly.protrusion",
    "label": "Body adiposity (belly-centred)",
    "group": "body/torso",
    "version": 5,
    "supersedes": "body.belly.protrusion.slider_v4.json (v4, whole-torso "
                  "system; limbs lean)",
    "symmetry": "bilateral_x",
    "range": {
        "min": -1, "max": 1, "default": 0, "safe_max": 1.0,
        "endpoint_anchor": "belly core unchanged from v1/v3/v4: max forward "
            "displacement at navel 0.1197 m on hm08 (Fat Males anchor scaled "
            "by torso-length ratio 0.8325); limb layer calibrated separately "
            "(thigh-band match, alpha 0.65) -- see system.limb_distribution",
    },
    "region": {
        "landmarks": ["navel", "sternum_bottom", "pelvis_top"],
        "mask_rule": "v4 whole-torso system, plus the limb crossfade: on "
            "limb-region verts (within 0.135 m of an arm axis / 0.175 m of "
            "a leg axis) the value crossfades proximally (arms s in "
            "[-0.02, 0.16], legs s in [-0.03, 0.13] of limb arc length) "
            "from v4's value to a limb-local (s, phi) transfer field, and "
            "fades distally to zero across the wrist (s 0.58-0.82) / ankle "
            "(s 0.70-0.90) so hands and feet stay lean. The system now "
            "ends at the wrists/ankles, not the limb roots.",
    },
    "semantics": "Whole-BODY adiposity system (FAT_REFERENCE.md + limb "
        "addendum L1-L5 in GRAVITY_V5.md): v4's whole-torso field extended "
        "into upper arms, forearms, thighs and calves by a limb-local "
        "transfer of the same two learned sources. At +1: mid-thigh girth "
        "+17.0 cm, calf belly +10.3 cm, upper arm +6.2 cm, forearm "
        "+5.4 cm, wrist +1.9 cm, ankle +2.2 cm (proximal gradient, L1); "
        "mass pools on the arm's back/underside (field radial 1.81 vs "
        "0.45 cm front, L3); elbow/knee girth minima persist (knee "
        "interior minimum s 0.52 -> 0.56); inner thighs close from a "
        "7.2 cm gap to 6.4 cm at their closest band but do NOT meet at "
        "+1 on this base (R10 approached, not reached -- reported, not "
        "faked). Torso scorecard vs v4: unchanged within noise except "
        "hip girth +1.2 cm (legitimate hip/thigh-root mass).",
    "system": {
        "model": "D5 = D4 + INC; INC(v) = m(v) * w_prox(s) * (F_limb(v) * "
                 "d_fade(s) - D4(v)) on limb verts, 0 elsewhere; "
                 "shape(w) = base + w * LIN5 + sign(w)|w|^2.0 * SAG, "
                 "LIN5 = LIN4 + INC, SAG unchanged from v3/v4",
        "limb_distribution": {
            "blend": "0.5 * Fat Males limb field + 0.5 * alpha_limb * HIMBO "
                     "Chonky limb-recipe field, each scaled by its per-limb "
                     "length ratio (arm/leg separately)",
            "alpha_limb_calibration": M["alpha_limb"],
            "calibration": "thigh-band match (mean |dr| over leg samples "
                "s 0.08-0.45, all phi): Fat Males 2.92 cm vs HIMBO limb "
                "recipe 4.49 cm after length scaling -> alpha 0.65 "
                "(inside the [0.5, 2.0] cap, unlike v4's torso alpha "
                "which capped at 2.0). The sources agree on limbs far "
                "better than on the belly front.",
            "scales": M["scales"],
            "himbo_recipe_used": M["himbo_limb_recipe_used"],
            "himbo_recipe_missing": M["himbo_limb_recipe_missing"],
            "missing_reason": "DeltsShape, ThighSmoothCurve, "
                "VastusMReduction, CalfOut, CalfSideIn exist only on the "
                "SOS-variant HIMBO mesh; verified Nov 12, 2026 that the "
                "SOS OSD's same-named blocks carry different vertex "
                "supports (LegsCalfWidth 2422 vs 4009 verts), so they do "
                "not index the Vanilla base and cannot be composed onto "
                "it. All primary mass sliders are present; the five are "
                "shape refinements.",
            "shipped_inc_scale": M["shipped_inc_scale"],
            "parametrization": "per-limb axis polyline from cross-section "
                "centroids (binomial-smoothed; legs z-bands hip->ankle, "
                "arms PCA bands shoulder->wrist); (s, phi) kernel with "
                "phi in mirrored right-limb space (inner/outer NOT folded, "
                "unlike the torso's |theta|); radial + axial components, "
                "tangential dropped as in v1-v4",
            "reference_shapings": [
                "arm underside sector gain (R3/L3): blended arm dr "
                "reweighted toward phi_down (world-down in the arm's "
                "frame, -2.12 rad) with strength 1.0, mean-preserved -- "
                "both sources under-pool the underside (HIMBO's arm "
                "recipe is deltoid/biceps-led; Fat Males' arm is its "
                "coarsest region)",
                "leg distal taper (L4): leg dr x1.0 through the "
                "gastrocnemius belly (s<=0.68), ->0.55 at s=0.85, ->0.35 "
                "at s=1.0 -- calf fat is a thin layer over a muscle "
                "form; the raw blend tubed the shank",
                "distal fades re-anchored after the r3 run measured "
                "+5.4/+5.5 cm at wrist/ankle: arm fade s 0.58-0.82, "
                "leg fade s 0.70-0.90 (wrist s~0.72, ankle s~0.84 on "
                "the base profile)",
            ],
        },
        "field_cross_validation_cm": M["fields"],
        "whole_body_gate": "fold repair and the 0-flip gate run over ALL "
            "26,756 body faces (both bases), not just the torso",
    },
    "gravity": {
        "coupling": {"formula": "shape(w) = base + w * LIN + f(w) * SAG",
                     "f": "sign(w) * |w|^gamma", "gamma": 2.0,
                     "f_at_0.5": 0.25},
        "fold_repair": "attenuation repair on the limb increment: "
            f"converged in {M['attenuation']['rounds']} rounds, min "
            f"attenuation {M['attenuation']['min']:.2f}, "
            f"{M['attenuation']['verts_under_0.99']} verts attenuated "
            "below 0.99 (slope limiter kappa 0.55 on the increment "
            "first, as v2-v4)",
        "contact_cap_applied": M["contact_cap_applied"],
    },
    "qa": {
        "fold_scan_+1_both_bases": qa5["fold_scan"]["+1 (combined)"],
        "fold_scan_full": qa5["fold_scan"],
        "body_faces_checked": qa5["body_faces_checked"],
        "navel_anchor": {
            "v5_at_+1_numpy": qa5["navel"]["v5_at_+1"],
            "v5_at_+1_blender_cm": {"forward": round(bl5["w+1.0"]["forward_cm"], 2),
                                    "down": round(bl5["w+1.0"]["down_cm"], 2)},
            "v4_at_+1_blender_cm": {"forward": round(bl4["w+1.0"]["forward_cm"], 2),
                                    "down": round(bl4["w+1.0"]["down_cm"], 2)},
            "note": "identical to v4 by construction (navel is outside "
                    "the limb region) and reproduced in Blender",
        },
        "metrics_corrected_v4": qa5["corrected_metrics_v4"],
        "metrics_corrected_v5": qa5["corrected_metrics_v5"],
        "limb_metrics": qa5["limb_metrics"],
        "underside_pooling": qa5["underside_pooling"],
        "inner_thigh_gap": qa5["inner_thigh_gap"],
        "blender_evaluated_belly_region": bl5["eval_belly_region"],
        "blender_evaluated_all_body_faces": bl5["eval_all_body_faces"],
        "moved_verts": qa5["moved_verts"],
    },
    "instances": {
        "makehuman_hm08": {
            "base": "hm08 (MPFB2 base.obj vertex order, 19158 verts; pure "
                    "delta vs the macro-neutral base)",
            "file": "body.belly.protrusion_v5.target",
            "components": {
                "combined_at_+1": "body.belly.protrusion_v5.target "
                    "(= LIN5 + SAG, for hosts without coupling support)",
                "limb_component": "body.belly.protrusion_limb_v5.target "
                    "(= D5 - D4: the limb crossfade increment. NOT a "
                    "standalone field -- apply on top of the v4 combined "
                    "target; its negative regions retire v4's off-gate "
                    "extrapolation on forearms/hands)",
                "v4_combined": "body.belly.protrusion_v4.target (unchanged)",
            },
        }
    },
    "provenance": {
        "source": "v4 system (Fat Males + HIMBO Chonky torso) plus limb "
            "transfers of (a) the Fat Males full field (its body mesh "
            "carries arms and legs) and (b) the HIMBO 'Chonky' preset's "
            "arms+legs blocks (17 of 22 carried on the Vanilla base; 5 "
            "SOS-variant-only, see missing_reason). Atomic Muscle "
            "contributes no transferable field (its FO4 NIF vertex "
            "buffer defeated extraction in the v3 cross-check) and "
            "remains a field-level cross-check only. Rules: "
            "FAT_REFERENCE.md + limb addendum L1-L5.",
        "method": "scripts/build_belly_v5.py (+ test_belly_v5.py, "
                  "finalize_v5.py)",
        "licence": "STUDY-ONLY / internal. Derived from Fat Males + "
            "HIMBO material under Joe's Nov 12, 2026 licence ruling "
            "(no AI-training use). NOT a CC0 MakeHuman asset; do not "
            "ship with stock MPFB content or redistribute.",
    },
}
(OUT / "body.belly.protrusion.slider_v5.json").write_text(
    json.dumps(slider, indent=1))
print("slider v5 JSON written")

# ------------------------------------------------------- side-by-sides
def side_by_side(left_path, right_path, left_label, right_label, out_path):
    L = Image.open(left_path).convert("RGB")
    R = Image.open(right_path).convert("RGB")
    band = 34
    canvas = Image.new("RGB", (L.width + R.width, L.height + band),
                       (24, 24, 26))
    canvas.paste(L, (0, band))
    canvas.paste(R, (L.width, band))
    d = ImageDraw.Draw(canvas)
    d.text((12, 10), left_label, fill=(235, 235, 235))
    d.text((L.width + 12, 10), right_label, fill=(235, 235, 235))
    canvas.save(out_path)
    print("wrote", out_path.name, canvas.size)

side_by_side(RENDERS / "belly_v4_w+1.0_front.png",
             RENDERS / "belly_v5_w+1.0_front.png",
             "v4  +1  (torso system, lean limbs)",
             "v5  +1  (whole-body system)",
             RENDERS / "belly_v4_vs_v5_front.png")
side_by_side(RENDERS / "belly_v4_w+1.0_profile.png",
             RENDERS / "belly_v5_w+1.0_profile.png",
             "v4  +1  profile",
             "v5  +1  profile",
             RENDERS / "belly_v4_vs_v5_profile.png")
print("FINALIZE V5 DONE")
