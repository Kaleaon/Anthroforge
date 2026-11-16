#!/usr/bin/env python3
"""Write the four body.definition.*.slider.json records (bara-proof)
and register the makehuman_hm08 instances in the anthroforge-app
slider library, from work/definition_numbers.json (single source of
truth: build_definition.py's measured QA)."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
N = json.loads((HERE / "work/definition_numbers.json").read_text())

LABELS = {
 "body.definition.flat_abs": ("Flat abs relief", "abdomen",
   "Rectus relief at value 1: the abdomen centre sits one "
   "calibrated flattening depth (2.70 mm at the canonical station) "
   "below its flanks inside the footprint band, with the linea "
   "alba groove at 0.91 mm. Pure relief: no mass, no radius change "
   "outside the footprint."),
 "body.definition.traps_valleys": ("Trapezius valleys", "yoke",
   "Trap/neck valley relief at value 1: the canonical dip-theta "
   "increment is -0.94 mm (signed convention; the coupling "
   "validation's measure). Pure relief beside the neck and across "
   "the upper chest; carries no neck mass (that is body.neck.mass)."),
 "body.definition.pecs_crease": ("Pec crease", "chest",
   "Pec separation + lower-border crease at value 1: canonical "
   "dip depth 1.21 mm across the chest footprint. Pure relief; "
   "the chest's width and mass are body.chest.width / body.pecs."),
 "body.definition.back": ("Back definition", "back",
   "Back relief at value 1: canonical relief RMS 1.56 mm over the "
   "back profile (spinal furrow station reads 0.23 mm of it -- "
   "the source sculpt is mostly broad lat/scapular shaping). "
   "Pure relief; no back mass."),
}
SRC_TXT = {
 "body.definition.flat_abs": "HIMBO - BodyTorsoFlatAbs (Vanilla HIMBO .osd, full decode) transferred at the slider-lab feature kernel (sigma_h 0.018, sigma_arc 0.014) and closed-loop calibrated at the canonical flattening station; the linea alba groove is AUTHORED (midline radial Gaussian inside the source footprint), because the kernel transfer carried only 0.42 of its 0.92 mm target.",
 "body.definition.traps_valleys": "HIMBO - BodyArmsTrapsValleys (Vanilla HIMBO .osd, full decode) transferred at the slider-lab feature kernel (sigma_h 0.018, sigma_arc 0.014) and closed-loop calibrated at the canonical dip-theta station (the coupling validation's own measure).",
 "body.definition.pecs_crease": "HIMBO - BodyPecsCrease (Vanilla HIMBO .osd, full decode) transferred at the slider-lab feature kernel (sigma_h 0.018, sigma_arc 0.014) and closed-loop calibrated at the canonical dip-in-h station.",
 "body.definition.back": "HIMBO - Body HPTorsoBackDefinition (SOS HP .osd twin of the SOS.osd block) transferred from the SOS HP base (14,597 verts, position-verified 1:1 over the Vanilla footprint; the Vanilla .osd carries no back-definition block and SOS-family sets do not index the Vanilla base) at the slider-lab feature kernel, closed-loop calibrated at the canonical relief-RMS station.",
}
for sid, (label, region, sem) in LABELS.items():
    s = N["sliders"][sid]
    att = s["attenuation"]
    rec = {
      "id": sid, "label": label, "group": "definition",
      "version": 1, "symmetry": "symmetric",
      "range": {"min": 0.0, "max": 1.0, "default": 0.0,
                "endpoint_anchor":
                    "1.0 = the source sculpt's own relief depth at "
                    "the canonical station, frame-scaled to hm08 "
                    "(closed-loop calibrated; see qa)"},
      "region": region,
      "system": {"model": "makehuman_hm08 relief field (sparse "
                          "MakeHuman target, metres)",
                 "file": f"body.definition.{sid.split('.')[-1]}.target",
                 "source": SRC_TXT[sid],
                 "study_only": True},
      "semantics": sem,
      "qa": {
        "canonical_measure": s["measure"],
        "source_depth_mm": s["source_canonical_depth_mm"],
        "target_depth_mm": s["target_depth_mm"],
        "transfer_depth_mm": s["transfer_depth_mm"],
        "calibration_scale": s["calibration_scale"],
        "calibrated_depth_mm": s["final_depth_mm"],
        "source_peak_mm": s["source_peak_mm"],
        "calibrated_peak_mm": s["final_peak_mm"],
        "moved_verts": s["moved_verts"],
        "kernel_cv_p95_cm": s["kernel_cv"]["p95_cm"],
        "attenuation": {
          tag: {"predicted": att[tag]["predicted_ratio"],
                "measured": att[tag]["measured_ratio"],
                "naive_fill_factor":
                    att[tag]["fill_factor_naive_over_tissue0"]}
          for tag in ("strongman", "gachidebu")},
        "fold_gate": {k: {"raw_flips": v["raw_flips"],
                          "macro_flips": v["macro_flips"]}
                      for k, v in N["folds"][sid].items()
                      if isinstance(v, dict)},
        "combined_set_over_gachidebu": {
            "raw": N["folds"].get("combined_defs_gachidebu_raw"),
            "macro": N["folds"].get("combined_defs_gachidebu_macro")},
      },
    }
    if s.get("groove"):
        rec["qa"]["linea_alba_groove"] = s["groove"]
    if s.get("back_station_detail"):
        rec["qa"]["back_station_detail"] = s["back_station_detail"]
    fn = HERE / f"{sid}.slider.json"
    fn.write_text(json.dumps(rec, indent=1, sort_keys=True) + "\n")
    print("wrote", fn.name)

APP = Path("/home/hatch/workspace/anthroforge-app/library/sliders")
for sid in LABELS:
    p = APP / f"{sid}.json"
    rec = json.loads(p.read_text())
    s = N["sliders"][sid]
    rec.setdefault("instances", {})["makehuman_hm08"] = {
      "file": f"anthroforge-v2/bara-proof/{sid}.target",
      "qa": {
        "base_verts": 19158,
        "moved_verts": s["target_moved_verts"],
        "canonical_measure": s["measure"],
        "feature_depth_mm": s["final_depth_mm"],
        "feature_depth_target_mm": s["target_depth_mm"],
        "relief_peak_mm": s["final_peak_mm"],
        "calibration_scale": s["calibration_scale"],
        "attenuation_measured_vs_predicted": {
          tag: [s["attenuation"][tag]["measured_ratio"],
                s["attenuation"][tag]["predicted_ratio"]]
          for tag in ("strongman", "gachidebu")},
        "fold_gate": "0 flips at raw 1.0 over muscle / strongman "
                     "/ gachidebu substrates (raw + macro bases); "
                     "combined definition set over gachidebu also 0",
        "blender_evaluated": "tissue0 0 flips, strongman 0; the "
                     "gachidebu render state carries 2 flips from "
                     "the SHIPPED quantised coupling target alone "
                     "(present with definition keys at 0; the "
                     "definition set adds none at 1.0)",
      },
      "note": "Relief instance authored Nov 12, 2026 "
              "(DEFINITION_GEOMETRY.md): HIMBO source transferred "
              "at the feature kernel and closed-loop calibrated at "
              "the canonical station; composes at the evaluator's "
              "effective values (definition is evaluation-stage "
              "relief, never stored mass)."}
    p.write_text(json.dumps(rec, indent=1, sort_keys=True) + "\n")
    print("updated", p.name)
print("GEN DONE")
