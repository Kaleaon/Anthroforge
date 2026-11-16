#!/usr/bin/env python3
"""SEN — character records (.afchar.json) + share codes via the app core.

Two records: sen_titan (the strongman build that was composed in
geometry) and sen_muscle_bear (the section-4.5 tissue variant — record
+ coupling evaluation only; its geometry instance awaits a tissue
field rebuilt at the variant recipe, because the shipped
body.tissue.strongman target is recipe-baked. Documented in
SEN_BUILD.md as an integration limitation, not hidden.)

Slider storage convention: canonical registry ids carry the values
that exist there; the FULL raw vectors ride along under namespaced
ids (himbo.* in normalised BodySlide convention: +1 = full large
pole, -1 = full small pole; head.* in spec units -100..+100).
Validation keeps unknown ids as named errors (never drops them) —
the report quantifies registry coverage honestly.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SEN = HERE.parent
APP = Path.home() / "workspace/anthroforge-app"
sys.path.insert(0, str(APP))

from core.character import Character  # noqa: E402
from core.sharecode import encode, decode  # noqa: E402
from core.sliders import SliderRegistry, CouplingRegistry  # noqa: E402

registry = SliderRegistry.from_folder(APP / "library/sliders")
couplings = CouplingRegistry.from_folder(APP / "library/couplings")

# ---- Sen body vector (presets-titan-batch1.md section 4.2), normalised
HIMBO = {   # slider: value/100 toward the LARGE pole (- = small pole)
    "weight": 0.90, "chubby": 0.80, "muscle": 0.65, "lean": -1.00,
    "body_mass": 0.30, "torso_mass": 1.00, "torso_mass_smooth": 0.75,
    "torso_width": 0.95, "torso_back_size": 0.90, "torso_back_shape": 0.85,
    "torso_lower": 1.00, "torso_waist_size": -0.60, "torso_belly": 0.80,
    "torso_belly_chub": 0.75, "belly_pot": 0.65, "belly_smooth": 0.70,
    "torso_belly_lhandles": 0.60, "torso_flat_abs": 0.00,
    "pecs_size": 1.00, "pecs_mass": 0.90, "pecs_width": 1.00,
    "pecs_lower": 0.70, "pecs_saggy": 0.45, "pecs_clavicle": 0.70,
    "arms_traps": 0.95, "arms_traps_meat": 1.00, "arms_traps_push": 0.90,
    "arms_traps_valleys": 0.30, "arms_shoulders": 0.90, "arms_delts": 0.90,
    "arms_biceps": 0.85, "arms_fore": 1.00, "arms_brachio": 0.80,
    "legs_size": 1.00, "legs_thigh": 1.00, "legs_chubby": 0.75,
    "legs_glutes": 0.80, "legs_calf_size": 0.90, "legs_calf_width": 0.85,
    "butt_booty": 0.75, "bubble_butt": 0.40, "butt_saggy": 0.25,
}
HEAD = {    # spec units -100..+100 (presets section 4.1)
    "muzzle_length": 15, "muzzle_width": 40, "muzzle_taper": -40,
    "muzzle_depth": 40, "nose_size": 35, "cranium_width": -10,
    "cranium_height": -20, "cranium_length": 5, "stop_angle": 40,
    "forehead_width": 25, "ear_length": -10, "ear_width": 55,
    "ear_base_height": -25, "ear_spread": 40, "ear_tilt": -20,
    "ear_tip_point": -80, "jaw_depth": 25, "jaw_length": -50,
    "jaw_width": 55, "cheek_width": 10, "ruff_volume": 70,
    "eye_size": -40, "eye_spacing": 30, "eye_forwardness": 20,
    "brow_thickness": -15, "brow_continuity": -25, "brow_shelf": 25,
    "brow_position": -10, "brow_padding": 25, "brow_scowl": 25,
}

fur_stats = {}
fs_path = SEN / "work/fur_stats.json"
if fs_path.exists():
    fur_stats = json.loads(fs_path.read_text())


def sliders_for(himbo, head):
    s = {
        # canonical registry sliders
        "body.muscle": himbo["muscle"], "body.chubby": himbo["chubby"],
        "body.torso.mass": himbo["torso_mass"],
        "body.torso.lower": himbo["torso_lower"],
        "body.belly.pot": himbo["belly_pot"],
        "body.pecs.size": himbo["pecs_size"],
        "body.tissue.mass_smooth": himbo["torso_mass_smooth"],
        "body.definition.traps_valleys": himbo["arms_traps_valleys"],
        "body.neck.mass": 0.90,      # authored NeckMass (Weight 90 gated)
        "body.chest.broadness": 1.0,  # width component applied at full
        "body.distribution": 0.0,
        "head.brow.projection": -20.0,
    }
    s.update({f"himbo.{k}": v for k, v in himbo.items()})
    s.update({f"head.{k}": float(v) for k, v in head.items()})
    return s


def make(name, preset_id, himbo, head, variant_note=None):
    c = Character(
        name=name,
        base={"body": "hm08 (MPFB2 base, macro-neutral)",
              "head": "af_head_neutral_v3 + species.bear vector"},
        sliders=sliders_for(himbo, head),
        species_preset={"id": preset_id, "species": "species.bear",
                        "source": "presets-titan-batch1.md sections "
                                  "1.3/4.1/4.2" + (" + 4.5" if variant_note
                                                   else "")},
        parts=[
            {"id": "part.body.hm08", "kind": "body",
             "targets": ["body.muscle", "body.chest.width",
                         "body.tissue.strongman",
                         "body.belly.protrusion_terminal_v51"]},
            {"id": "part.head.bear_v3", "kind": "head",
             "file": "sen_head.glb",
             "derived_from": "base-head-v3 (GalileoGB cougar, CC-BY)"},
            {"id": "part.tongue.large", "kind": "interior",
             "scale": 1.3, "note": "Sen canon: huge tongue (section 4.3)"},
        ],
        fur={
            "system": "strand groom -> baked cards (fur-prototype method)",
            "coat_colour": "dark tan/brown",
            "groom_stats": fur_stats,
            "zones": [
                {"id": "furzone.chest_crescent", "kind": "fur_colour_zone",
                 "region": "torso.chest.upper_front",
                 "colour": "pale cream (moon-bear coat marking)",
                 "note": "Natural pale-FUR patch. NOT a tattoo, NOT a "
                         "decal (Joe's correction, Nov 4 2026; MARKINGS.md "
                         "section 1.1 target 2: fur colour function)."},
                {"id": "furzone.forehead_mark", "kind": "fur_colour_zone",
                 "region": "head.forehead", "colour": "pale",
                 "note": "Retained per the character bible; exact shape "
                         "is NOT described in the person file — zone "
                         "recorded, no geometry/texture authored."},
            ],
        },
        materials={
            "skin": {"palette": "sen.coat", "base": "#6B4A2E"},
            "layers": [
                {"id": "lyr_basecoat", "stack": "base", "kind": "palette",
                 "note": "dark tan/brown coat (person file)"},
                {"id": "lyr_crescent", "stack": "markings",
                 "kind": "fur_zone", "zone": "furzone.chest_crescent",
                 "opacity": 1.0},
                {"id": "lyr_forehead", "stack": "markings",
                 "kind": "fur_zone", "zone": "furzone.forehead_mark",
                 "opacity": 1.0},
            ],
            "eyes": {"id": "eye", "colour": "amber",
                     "note": "art-consistency bible (person file); round "
                             "pupil (ursid)"},
        },
        identity={
            "titan_index": 10, "sex": "male",
            "species_blend": "moon bear x grizzly x Asiatic black bear",
            "stance": "bipedal",
            "export_scale": 1.74, "height_export_m": 3.05,
            "canon_mass_kg": 1134,
            "canon_mass_note": "2500 lb canon (SEN CORE v1.3) — a "
                               "density/scale fact, not a slider output",
            "variant_note": variant_note,
        },
        provenance={
            "study_only": True,
            "built": "2026-11-12",
            "sources": ["presets-titan-batch1.md", "bara-proof components",
                        "first-proof belly v5.1 system",
                        "base-head-v3", "fur-prototype method",
                        "memory/people/sen.md"],
        },
    )
    return c


sen = make("Sen", "sen_titan", HIMBO, HEAD)
mb_himbo = dict(HIMBO)
mb_himbo.update({"chubby": 0.55, "torso_mass_smooth": 0.45,
                 "arms_traps_valleys": 0.55, "pecs_saggy": 0.30,
                 "belly_pot": 0.50})
sen_mb = make("Sen (muscle bear)", "sen_muscle_bear", mb_himbo, HEAD,
              variant_note="section 4.5: MuscleVector held; TissueVector "
                           "moved to the gachimuchi cell. Record + "
                           "coupling evaluation only — geometry instance "
                           "pending a variant tissue field.")
sen_mb.sliders["body.definition.back"] = 0.50
sen_mb.sliders["himbo.torso_back_definition"] = 0.50

out = {}
for tag, c in (("sen", sen), ("sen_muscle_bear", sen_mb)):
    rep = c.validate(registry)
    eff = c.effective_sliders(registry, couplings)
    code = encode(c)
    back = decode(code)
    assert back.to_dict(include_provenance=False) == \
        c.to_dict(include_provenance=False), f"{tag} round-trip mismatch"
    path = SEN / f"{tag}.afchar.json"
    path.write_text(json.dumps(c.to_dict(), indent=1))
    out[tag] = {
        "file": str(path), "id": c.id, "share_code": code,
        "share_code_len": len(code), "roundtrip_ok": True,
        "validation": {
            "ok": rep.ok, "n_errors_unknown_sliders": len(rep.errors),
            "unknown_sample": rep.errors[:6],
            "n_warnings": len(rep.warnings)},
        "effective": {
            "sliders": {k: round(v, 4) for k, v in
                        eff.sliders.items() if not k.startswith("himbo.")
                        and not k.startswith("head.")},
            "derived": {k: round(v, 4) for k, v in eff.derived.items()},
            "n_warnings": len(eff.warnings),
            "warnings": [str(w) for w in eff.warnings[:8]],
        },
    }
    print(f"{tag}: code {len(code)} chars, validation errors "
          f"{len(rep.errors)}, derived "
          f"{ {k: round(v,3) for k,v in eff.derived.items()} }")
(SEN / "work/record_report.json").write_text(json.dumps(out, indent=1))
print("records written")
