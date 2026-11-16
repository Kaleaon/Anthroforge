#!/usr/bin/env python3
"""Wire the Nov 12 proof deliverables into the app slider library.

Transforms (never re-types) the source records:

1. ``body.belly.protrusion`` — refreshed from the v5.1 canonical
   record: the hm08 instance becomes the gravity-coupled components
   form (combined v5.1 + sag v3, gamma 2.0) with the v5.2 contact
   variant registered; the masculine base gets its re-derived v1
   instance; safe_max moves to the v5.1 record's 1.0. The Skyrim
   Fat Males instance (the lineage's origin) is kept.
2. Bara composed builds — bara-proof shipped its fields under the ids
   body.muscle / body.chest.width / body.tissue.strongman. In the app
   library the composed builds live under ``body.build.*`` so the
   atomic HIMBO slider ids keep their meaning (body.muscle is the
   HIMBO BodyMuscle slider; its composed namesake is a whole build).
   The combined strongman target becomes ``body.build.bara_strongman``.
3. ``body.neck.mass`` — gains its hm08 instance (the authored yoke
   field from bara-proof, built to this record's own spec);
   ``body.forearm.mass`` — new record from bara-proof's JSON + target.

Idempotent: re-running rewrites the same files.
"""

from __future__ import annotations

import json
from pathlib import Path

WS = Path.home() / "workspace"
V2 = WS / "anthroforge-v2"
SLIDERS = WS / "anthroforge-app" / "library" / "sliders"
FP = "anthroforge-v2/first-proof"
BP = "anthroforge-v2/bara-proof"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save(record: dict) -> None:
    path = SLIDERS / f"{record['id']}.json"
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")
    print("wrote", path.name)


# ---------------------------------------------------------------- belly
def wire_belly() -> None:
    rec = load(SLIDERS / "body.belly.protrusion.json")
    v51 = load(V2 / "first-proof" / "body.belly.protrusion.slider_v5.1.json")
    rec["label"] = v51["label"]
    rec["semantics"] = v51["semantics"]
    rec["range"]["safe_max"] = 1.0
    rec["range"]["endpoint_anchor"] = v51["range"]["endpoint_anchor"]
    rec.setdefault("provenance", {})
    rec["provenance"]["licence"] = "study-only (internal)"
    rec["provenance"]["source"] = (
        "Fat Males + HIMBO Chonky fields transferred to hm08 (first-proof "
        "lineage v1-v5.1); see anthroforge-v2/first-proof/GRAVITY_V5.md"
    )
    rec["instances"]["makehuman_hm08"] = {
        "components": {
            "combined": f"{FP}/body.belly.protrusion_v5.1.target",
            "sag": f"{FP}/body.belly.protrusion_sag_v3.target",
            "gamma": 2.0,
            "variants": {
                "contact": f"{FP}/body.belly.protrusion_contact_v52.target",
            },
        },
        "note": "v5.1 system: shape(w) = base + w*LIN + sign(w)|w|^2.0*SAG with "
                "LIN = combined - sag (the engine decomposes at load). The "
                "'contact' variant is the v5.2 thigh-contact combined field "
                "(GRAVITY_V5.md v5.2 addendum); selecting it swaps the combined "
                "field and keeps the v3 sag decomposition, as that build's own "
                "record documents. QA at +1: 0 flipped faces over all 26,756 "
                "body faces on both bases; navel +11.27 cm fwd / -6.99 cm down "
                "(Blender). Known debit: the -1 pole folds (~184 faces, linear "
                "evaluation) — a separately authored decrease target is owed.",
        "qa": {
            "flips_at_+1_body_faces": 0,
            "body_faces_checked": 26756,
            "navel_at_+1_cm": {"forward": 11.27, "down": 6.99},
            "wrist_girth_gain_cm": 2.98,
            "ankle_girth_gain_cm": 3.32,
        },
    }
    rec["instances"]["makehuman_hm08_masculine"] = {
        "file": "anthroforge-v2/masculine-base/body.belly.protrusion.target",
        "note": "v1-lineage field RE-DERIVED on the masculine base (targets are "
                "per-base; the hm08 field does not transfer). 542 moved verts; "
                "navel achieved 0.12257 m vs anchor 0.12447 m (error -0.19 cm).",
        "qa": {"navel_error_cm": -0.19},
    }
    save(rec)


# ------------------------------------------------------- bara composed
def _bara_record(src_name: str, new_id: str, target: str, extra_note: str) -> dict:
    src = load(V2 / "bara-proof" / src_name)
    rec = {k: v for k, v in src.items() if k != "version"}
    rec["id"] = new_id
    rec["instances"] = {
        "makehuman_hm08": {
            "file": f"{BP}/{target}",
            "note": extra_note,
        }
    }
    rec["provenance"] = {
        "source": f"anthroforge-v2/bara-proof/{src_name} (composed build field, "
                  "BARA_LESSONS Muscle x Tissue composition on hm08)",
        "licence": "study-only (internal)",
        "id_note": "bara-proof shipped this field as "
                   f"{src.get('id')!r}; the app library namespaces composed "
                   "builds under body.build.* so atomic HIMBO slider ids keep "
                   "their meaning",
    }
    if "qa" in src:
        rec["instances"]["makehuman_hm08"]["qa"] = src["qa"]
    return rec


def wire_bara() -> None:
    save(_bara_record(
        "body.muscle.slider.json", "body.build.muscle", "body.muscle.target",
        "The section 6C MuscleVector x Sen section 4.2 composition as ONE field "
        "(yoke-first; triceps-led arms; legs pinned). At +1 with the full "
        "strongman composition: 0 flipped faces. This is a build, not the "
        "HIMBO BodyMuscle morph — see body.muscle for the atomic slider."))
    save(_bara_record(
        "body.chest.width.slider.json", "body.build.chest_width",
        "body.chest.width.target",
        "Lateral frame only (ShoulderInc 0.50 / TorsoWidth 0.95 / ArmsShoulders "
        "0.90 / BackShape 0.85): width without depth or pec mass. Combined "
        "build M13: chest width 46.7 -> 56.0 cm. Distinct from the two-pole "
        "body.chest.broadness frame record."))
    save(_bara_record(
        "body.tissue.strongman.slider.json", "body.build.tissue_strongman",
        "body.tissue.strongman.target",
        "Sen's tissue vector as one field; the belly component is the v4 "
        "gravity system reused at tau = 0.60 (solved for chest:waist >= 1.30). "
        "Fat wrap measured on this layer alone: belly flank/front 0.74, chest "
        "1.08 — both clear the MUSCLE_TISSUE_MODEL section 4 floors."))
    combined = {
        "id": "body.build.bara_strongman",
        "label": "Bara strongman — combined build",
        "group": "body/build",
        "semantics": "The full strongman composition (body.build.muscle + "
                     "body.build.chest_width + body.build.tissue_strongman, all "
                     "at +1) summed into one field — verified equal to the "
                     "component sum (max deviation 0.020 cm). Scorecard: M4 "
                     "chest:waist 1.303, M13 chest width x1.199, volume +94.2%. "
                     "Honest misses: M2 neck ratios and M3 forearm ratio are "
                     "vocabulary-capped by the HIMBO source fields (see "
                     "body.neck.mass / body.forearm.mass for the authored "
                     "correctives).",
        "range": {"min": 0.0, "max": 1.0, "default": 0.0, "safe_max": 1.0,
                  "endpoint_anchor": "+1 = the BARA_PROOF.md combined build, "
                                     "measured on hm08"},
        "symmetry": "bilateral_x",
        "instances": {
            "makehuman_hm08": {
                "file": f"{BP}/body.bara.strongman.target",
                "qa": {"flips_at_+1": 0,
                       "combined_vs_components_max_dev_cm": 0.020},
            }
        },
        "provenance": {
            "source": "anthroforge-v2/bara-proof/BARA_PROOF.md",
            "licence": "study-only (internal)",
        },
    }
    save(combined)


# ------------------------------------------------------------ neck/fore
def wire_neck_forearm() -> None:
    neck = load(SLIDERS / "body.neck.mass.json")
    src = load(V2 / "bara-proof" / "body.neck.mass.slider.json")
    neck["instances"] = {
        "makehuman_hm08": {
            "file": f"{BP}/body.neck.mass.target",
            "note": "Authored yoke field (traps + SCM + neck cylinder) built to "
                    "this record's acceptance gate after the bara proof found "
                    "the source-field neck capped (neck girth only 32.2 -> 36.4 "
                    "cm) — later traced to a dropped NeckMass block in "
                    "build_bara.py and fixed at the source (the composed "
                    "build now reads 43.0 cm; see anthroforge-v2/bara-proof/"
                    "FIX_NECK_FIELD.md). This field remains the fine-control "
                    "yoke slider. QA: bara-proof/work/qa_numbers_neck_forearm.json.",
            "qa": src.get("qa", {}),
        }
    }
    save(neck)

    fore = load(V2 / "bara-proof" / "body.forearm.mass.slider.json")
    fore.pop("version", None)
    fore["instances"] = {
        "makehuman_hm08": {
            "file": f"{BP}/body.forearm.mass.target",
            "note": "Authored forearm field (brachioradialis + extensors, wrist "
                    "kept lean) — the strength read the HIMBO Fore block alone "
                    "could not reach (M3 forearm:arm was 0.690 against the "
                    "0.80-0.88 bara band). QA: bara-proof/work/qa_numbers_neck_forearm.json.",
            "qa": fore.get("qa", {}),
        }
    }
    fore["provenance"] = {
        "source": "anthroforge-v2/bara-proof/body.forearm.mass.slider.json "
                  "(authored field; qa_numbers_neck_forearm.json)",
        "licence": "study-only (internal)",
    }
    save(fore)


if __name__ == "__main__":
    wire_belly()
    wire_bara()
    wire_neck_forearm()
