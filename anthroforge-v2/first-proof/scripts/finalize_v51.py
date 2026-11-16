#!/usr/bin/env python3
"""Write the v5.1 slider record from the v5 record + v5.1 QA numbers.
Follows the versioning pattern: a new file, v1-v5 records untouched."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent
WORK = OUT / "work"

rec = json.loads((OUT / "body.belly.protrusion.slider_v5.json").read_text())
qa = json.loads((WORK / "qa_numbers_v51.json").read_text())
bl = json.loads((WORK / "blender_v51_numbers.json").read_text())

rec["version"] = 5.1
rec["supersedes"] = ("body.belly.protrusion.slider_v5.json (v5, whole-body "
                     "system; distal fades ended at zero -- hands/feet lean)")
rec["region"]["mask_rule"] = (
    "v5 system, plus the v5.1 TERMINAL component: the distal fades no "
    "longer end at zero. From the wrist (arm s 0.60-0.90) and ankle "
    "(leg s 0.74-0.99) a low, shaped terminal field (Fat Males "
    "malehands/malefeet measured deltas, zone-scaled) carries small "
    "real tissue into the hands and feet: wrist ring, dorsal-weighted "
    "palm pad, per-digit thickening (rig-weight segmentation) with "
    "knuckle softening and a contact cap between fingers, ankle ring "
    "(capped, excess routed to heel/dorsal), dorsal midfoot and toes.")
rec["semantics"] = (
    "Whole-body adiposity system INCLUDING terminal tissue (Joe, Nov "
    "12, 2026: 'wrists and hands also need fat, not massive amounts "
    "but that is realistic'). v5's limb gains stand; v5.1 adds the "
    "heavy-hand/foot tells at +1: wrist girth +2.98 cm total (v5 "
    "alone +1.85), ankle +3.42 cm total (v5 +2.18), proximal finger "
    "mean radial thickness +13.5-16.2% per finger (thumb +14.3%), "
    "dorsal hand pad, knuckle relief softened (not erased). "
    "Inter-digit minimum distance 2.11 -> 1.01 mm, zero new close "
    "pairs, centroid separations preserved -- fingers thicken into "
    "their free sectors, contact faces flatten (contact cap).")
term = {
    "component_file": "body.belly.protrusion_terminal_v51.target",
    "model": "D51 = D5 + TERM; TERM is linear (part of LIN): "
             "shape(w) = base + w*(LIN5+TERM) + sign(w)|w|^2.0*SAG",
    "source": {
        "primary": "Fat Males malehands/malefeet same-topology deltas "
                   "(learned/fat-males_body_morph.npz): hands mean "
                   "0.150 / max 0.501 Skyrim units, feet mean 0.384 / "
                   "max 1.520 -- per-zone perpendicular magnitudes, "
                   "scaled by hand/foot length ratio to hm08 "
                   "(hand 0.642, foot 0.692)",
        "zone_perp_mean_mm": qa["zone_gains_source"]["hand_perp_mean_mm"],
        "foot_zone_perp_mean_mm": qa["zone_gains_source"]["foot_perp_mean_mm"],
        "gains_pre_cal_mm": qa["zone_gains_source"]["gains_pre_cal_mm"],
        "shaping_E": "sector weights (hand dorsal > lateral > palmar; "
                     "foot dorsal > side > sole) and the knuckle-"
                     "softening term are anatomical shaping [E] over "
                     "the measured magnitudes [S]",
    },
    "calibration": {
        "CAL": qa["cal"],
        "CAL_target": "composed wrist girth gain 3.0 cm (band 2.5-3.5); "
                      "solved CAL = 1.000 (the scaled source itself)",
        "FBOOST": qa["fboost"],
        "FBOOST_target": "fingers 2-5 proximal mean radial thickness "
                         "gain 0.150 (foot of the specified 15-20% "
                         "band); solved FBOOST = 1.000 after the "
                         "round-finger sector rebalance",
        "per_vert_caps": "proximal finger radial <= 20% of local "
                         "radius (the band ceiling; binds dorsally), "
                         "mid/distal <= 15%; contact cap <= 45% of "
                         "distance to nearest other-digit vertex "
                         "+ 0.3 mm; ankle ring capped (see "
                         "ankle_ring_cap_mm), FM ankle/heel excess "
                         "routed to heel/dorsal zones",
        "ankle_ring_cap_mm": qa["zone_gains_source"]["ankle_ring_cap_mm"],
    },
    "segmentation": "digits from the MPFB default rig's finger bone "
                    "skin weights (authoritative; geometric clustering "
                    "and a geodesic watershed both failed on the "
                    "webbed, contact-resting hm08 hand -- probed and "
                    "documented in GRAVITY_V5.md addendum); dorsal "
                    "sign from the base.obj joint helpers (thumb MCP "
                    "joint sits 8.2 mm palmar to the finger MCP plane)",
    "moved_verts_terminal": qa["moved_verts"]["terminal"],
}
rec["system"]["terminal_component"] = term
rec["qa"]["v51_terminal"] = {
    "fold_scan": qa["fold_scan"],
    "wrist": qa["wrist"], "wrist_L": qa["wrist_L"],
    "ankle": qa["ankle"], "ankle_L": qa["ankle_L"],
    "finger_prox_thickness": qa["finger_prox_thickness"],
    "inter_digit_min_dist": qa["inter_digit_min_dist"],
    "blender_evaluated_all_body_faces": bl["eval_all_body_faces_v51"],
    "terminal_support_verts": qa["terminal_support_verts"],
}
rec["instances"]["makehuman_hm08"]["components"]["terminal_component"] = (
    "body.belly.protrusion_terminal_v51.target (= combined v5.1 - "
    "combined v5; stacks on the v5 combined target)")
rec["instances"]["makehuman_hm08"]["components"]["combined_v51"] = (
    "body.belly.protrusion_v5.1.target (= LIN5 + TERM + SAG at +1)")
rec["provenance"]["method"] = (
    "scripts/build_belly_v51.py (+ test_belly_v51.py, finalize_v51.py); "
    "v5 system by scripts/build_belly_v5.py")
(OUT / "body.belly.protrusion.slider_v5.1.json").write_text(
    json.dumps(rec, indent=1))
print("slider v5.1 record written")
