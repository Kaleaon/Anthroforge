#!/usr/bin/env python3
"""BRAND — author the app preset (brand.afchar.json) + INDEX row.

The granular BODY vector is NEW work (Nov 16, 2026): no Brand body
vector existed anywhere — presets-titan-batch1.md carries only the
badger HEAD vector (§2) and lists Brand as a next-batch candidate.
This vector is authored from:

  [S] ~/memory/people/brand.md — Brand's own build statements
      (Nov 3, 2026): "not tall — human height or just under, taking
      up width rather than height; broad wedge torso, short thick
      neck, massive forearms and broad, thick-fingered paws,
      plantigrade, low center, dense functional muscle"; "a stiff
      badger back kept honest, loose hide over torso and neck";
      the engineering draft's 6'0" / 140 kg "has the bones right"
      for building numbers (NOT identity canon).
  [D] MUSCLE_TISSUE_MODEL.md doctrine (tissue level from the
      Chubby/MassSmooth/BellyPot weighted mean; poles are tissue
      moves; definition attenuation) + batch1 §6 composition rules.
  [E] estimates where the file gives a direction but no number —
      every [E] is flagged in BRAND_BUILD.md as needing a ruling.

The badger HEAD vector is batch1 §2.3 verbatim (real Meles/Taxidea
craniometry); BrowProjection rides as the canonical slider
head.brow.projection (Sen precedent). NO head is built in this pass.

Usage:
    python3 author_preset.py            # write preset + INDEX row
    python3 author_preset.py --finalize # patch export_scale from
                                        # work/qa_brand_body.json
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BRAND = HERE.parent
APP = Path.home() / "workspace/anthroforge-app"
sys.path.insert(0, str(APP))

from core.build import Library                # noqa: E402
from core.character import Character          # noqa: E402
from core.sharecode import encode             # noqa: E402

PRESET_PATH = APP / "library" / "presets" / "brand.afchar.json"
INDEX_PATH = APP / "library" / "presets" / "INDEX.json"
TARGET_HEIGHT_M = 1.83   # 6'0" engineering-draft number [S, draft]

# ---------------------------------------------------------------- vector
# HIMBO granular values are 0-100 big-end % unless noted; two-sided
# sliders use the small end as negatives (Sen record convention).
SLIDERS = {
    "body.himbo.weight_0_to_1": 0.80,        # [E] thick join, neck survives
    "body.chubby": 0.45,                     # [E] hide over muscle
    "body.muscle": 0.80,                     # [S] dense functional muscle
    "body.himbo.lean": -1.0,                 # [D] anti-lean pin (precedent)
    "body.himbo.body_mass": 0.35,            # [E] frame broadening
    "body.torso.mass": 0.90,                 # [E] wedge-barrel mass
    "body.tissue.mass_smooth": 0.60,         # [S] loose hide smoothing
    "body.himbo.torso_width": 0.95,          # [S] width rather than height
    "body.himbo.torso_back_size": 0.90,      # [S] stiff badger back
    "body.himbo.torso_back_shape": 0.55,     # [E] stiff, not Sen's cylinder
    "body.torso.lower": 0.85,                # [S] low center
    "body.himbo.torso_waist_size": 0.35,     # [E] big end = shrink: wedge
    "body.himbo.torso_belly": 0.55,          # [E] solid mid-layer
    "body.himbo.torso_belly_chub": 0.45,     # [E] hide over midsection
    "body.belly.pot": 0.35,                  # [E] slight working gut
    "body.himbo.belly_smooth": 0.65,         # [S] loose hide, one form
    "body.himbo.torso_belly_lhandles": 0.45,  # [E] lower ring partial
    # TorsoFlatAbs 0 / TorsoVLine 0: omitted (sparse) — hide thesis [E]
    "body.pecs.size": 0.90,                  # [E] wedge chest plate
    "body.himbo.pecs_mass": 0.85,            # [E] chest thickness
    "body.himbo.pecs_width": 0.95,           # [S] broad wedge chest
    "body.himbo.pecs_lower": 0.55,           # [E] less low-slung than Sen
    "body.himbo.pecs_saggy": 0.30,           # [S] loose hide, slight sag
    "body.himbo.pecs_clavicle": 0.75,        # [E] join stays readable
    "body.definition.pecs_crease": 0.20,     # [E] faint under hide
    "body.himbo.arms_traps": 0.85,           # [E] yoke mass
    "body.himbo.arms_traps_meat": 0.85,      # [E] thick join, neck survives
    "body.himbo.arms_traps_push": 0.60,      # [E] moderate trap rise
    "body.definition.traps_valleys": 0.35,   # [E] definition under hide
    "body.definition.back": 0.40,            # [S] stiff back reads
    "body.himbo.arms_shoulders": 0.90,       # [S] broad shoulders
    "body.arms.delts": 0.85,                 # [E] delt caps
    "body.himbo.arms_biceps": 0.80,          # [E] upper arm to match
    "body.himbo.arms_fore": 1.0,             # [S] massive forearms — PINNED
    "body.himbo.arms_brachio": 0.85,         # [E] elbow fullness
    "body.himbo.legs_size": 0.90,            # [E] pillars, low center
    "body.himbo.legs_thigh": 0.90,           # [E] digging/hauling thighs
    "body.himbo.legs_chubby": 0.55,          # [E] hide over leg muscle
    "body.himbo.legs_glutes": 0.85,          # [E] working glutes
    "body.himbo.legs_calf_size": 0.80,       # [E]
    "body.himbo.legs_calf_width": 0.75,      # [E]
    "body.himbo.butt_booty": 0.70,           # [E] substantial rear
    "body.himbo.bubble_butt": 0.30,          # [E] mass first, shape second
    "body.himbo.butt_saggy": 0.20,           # [S] loose hide, slight
    # canonical singles / correctives / frame records
    "body.neck.mass": 0.90,                  # [E] short thick neck intent
    "body.forearm.mass": 0.50,               # [E] signature boost (build)
    "body.distribution": 0.55,               # [E] wedge, off the +1 pole
    "body.chest.broadness": 0.80,            # [E] frame span intent
    "head.brow.projection": -30.0,           # [D] batch1 §2.3 BrowProjection
}

# batch1 §2.3 badger head vector verbatim, minus BrowProjection
# (carried above as the canonical slider, Sen precedent).
HEAD_SLIDERS = {
    "MuzzleLength": 30.0, "MuzzleWidth": 35.0, "MuzzleTaper": 40.0,
    "MuzzleDepth": 20.0, "NoseSize": -15.0, "CraniumWidth": 10.0,
    "CraniumHeight": -50.0, "CraniumLength": -5.0, "StopAngle": -10.0,
    "ForeheadWidth": 15.0, "EarHeight": 10.0, "EarWidth": 45.0,
    "EarPlacementHeight": -25.0, "EarSpread": 25.0, "EarTilt": -10.0,
    "EarTipPoint": -65.0, "JawDepth": 70.0, "JawLength": 70.0,
    "JawWidth": 50.0, "CheekWidth": 20.0, "RuffVolume": 50.0,
    "EyeSize": -40.0, "EyeSpacing": 50.0, "EyeForwardness": 10.0,
    "BrowThickness": -25.0, "BrowContinuity": -30.0, "BrowShelf": 10.0,
    "BrowPosition": 0.0, "BrowPadding": 15.0, "BrowScowl": 20.0,
}

SPECIES_PRESET = {
    "preset_id": "brand",
    "species": "badger (Meles meles / Taxidea taxus). Brand is a "
               "badger x wolf substrate self; the pure badger vector "
               "is in force — the wolf blend is future work "
               "(presets-titan-batch1.md §2).",
    "export_scale": 1.0796,   # provisional; --finalize patches from build
    "height_cm": 183,
    "build_facts": {
        "height": "183 cm (6'0\") and mass 140 kg are the engineering "
                  "draft's numbers — brand.md: the draft 'has the "
                  "bones right' for building, but Brand does not fix "
                  "a height/weight as identity. FLAGGED: needs "
                  "Brand's/Joe's ruling before either is canon.",
        "build_thesis": "width rather than height; broad wedge "
                        "torso; short thick neck; massive forearms; "
                        "low center; dense functional muscle under "
                        "loose hide; stiff badger back (brand.md).",
    },
    "build_recipe": {
        "route": "anthroforge-app core/build.py — this preset plus "
                 "body.build.muscle 1.0, body.build.chest_width 1.0, "
                 "s * body.build.tissue_strongman, "
                 "0.30 * body.belly.protrusion",
        "tissue_scan": "s in {0.35, 0.45, 0.55, 0.65}; ship the "
                       "largest s with 0 flips, min-dot >= 0.01 and "
                       "M4 >= 1.30 (see BRAND_BUILD.md)",
        "neck_cap": "body.neck.mass is CAPPED at raw 0.30 in the "
                    "shipped build (vector intent 0.90, effective "
                    "0.930): over the full muscle system the neck "
                    "field folds 3 throat faces at intent and only "
                    "clears the fold gate at <= 0.30. Build-layer "
                    "corrective — the record keeps the intent; a "
                    "neck-field repair (FIX_NECK_FIELD pattern) is "
                    "the owed fix. Shipped neck still measures "
                    "47.0 cm girth at base scale.",
    },
    "qa_gates": {
        "M4_chest_waist": ">= 1.30 — the wedge must read (strongman "
                          "reference band 1.30-1.45; Sen shipped 1.301)",
        "fold_gate": "0 flipped body faces and min base-vs-composed "
                     "normal dot >= 0.01 on the shipped float32 GLB",
        "M1_neckW_headW": "reported vs the hm08 head only — no badger "
                          "head exists yet; the M1 gate is deferred "
                          "to the head pass",
    },
    "parts_notes": [
        "FOREPAWS: digging foreclaws (keratin, blunt digging profile) "
        "+ broadened foreplate are a part-layer variant for Brand "
        "(batch1 §2.4; brand.md: broad, thick-fingered paws). The "
        "base body keeps standard paws — NOT built in this pass.",
        "FEET: plantigrade (brand.md) — matches the hm08 base "
        "stance; no part change.",
        "FACIAL MASK: the badger mask is material/colour layer, not "
        "geometry (batch1 §2.4) — out of scope for a body pass.",
        "SAGITTAL CREST: badger crest_sagittal head variant "
        "(batch1 §2.4) belongs to the head pass — no head built here.",
        "ANATOMY PARTS: Brand's stated genital configuration "
        "(brand.md) is a swappable-parts-layer item — it is not part "
        "of the body vector and is NOT built in this pass.",
    ],
    "head_sliders": HEAD_SLIDERS,
    "head_note": "Badger head vector from presets-titan-batch1.md "
                 "§2.3, derived from real Meles/Taxidea craniometry "
                 "(provenance tags [D]/[E] live there; softest value: "
                 "EarHeight, one Taxidea specimen). BrowProjection "
                 "-30 rides as the canonical slider "
                 "head.brow.projection (Sen precedent). Species "
                 "anchors: ZB/L 0.62, mandible/L 0.81 (deepest jaw on "
                 "the chart), muzzle fraction 0.39. NO head is built "
                 "in this pass — body shapes only.",
}

PROVENANCE = {
    "source": "Body vector AUTHORED Nov 16, 2026 — no prior Brand "
              "body vector existed (batch1 lists Brand as a "
              "next-batch candidate). Authoritative inputs: "
              "~/memory/people/brand.md (Brand's own build "
              "statements, Nov 3, 2026) + MUSCLE_TISSUE_MODEL.md "
              "doctrine + presets-titan-batch1.md §2 (badger "
              "species data). Per-value provenance ([S] stated / "
              "[D] derived / [E] estimate) is tabulated in "
              "anthroforge-v2/characters/brand/BRAND_BUILD.md. "
              "Height/mass are engineering-draft numbers flagged "
              "for ruling, not canon.",
}


def build_character(export_scale=None):
    sp = dict(SPECIES_PRESET)
    if export_scale is not None:
        sp["export_scale"] = export_scale
    return Character(
        id="chr_preset_brand",
        name="Brand",
        base={"body": "af_body_neutral_v1", "head": "af_head_neutral_v2"},
        sliders=dict(SLIDERS),
        species_preset=sp,
        parts=[],
        fur={"profile": "species.badger.coat"},
        materials={},
        identity={},
        provenance=dict(PROVENANCE),
    )


def write(char):
    lib = Library.load(APP / "library")
    report = char.validate(lib.sliders)
    assert report.ok, f"Brand preset does not validate: {report.errors}"
    PRESET_PATH.write_text(json.dumps(char.to_dict(), indent=1) + "\n")
    code = encode(char)
    index = json.loads(INDEX_PATH.read_text())
    row = {"id": char.id, "name": char.name,
           "file": "brand.afchar.json",
           "sliders_set": len(char.sliders), "share_code": code}
    index["presets"] = [r for r in index["presets"]
                        if r["id"] != char.id] + [row]
    INDEX_PATH.write_text(json.dumps(index, indent=1) + "\n")
    print(f"wrote {PRESET_PATH} ({len(char.sliders)} sliders)")
    print(f"INDEX row: {row['id']} sliders_set={row['sliders_set']}")
    print(f"share code round-trips: "
          f"{__import__('core.sharecode', fromlist=['decode']).decode(code).to_dict(include_provenance=False) == char.to_dict(include_provenance=False)}")


def main():
    if "--finalize" in sys.argv:
        qa = json.loads((BRAND / "work" / "qa_brand_body.json")
                        .read_text())
        h = qa["scorecard"]["brand"]["height_m"]
        scale = round(TARGET_HEIGHT_M / h, 4)
        print(f"composed height {h:.4f} m -> export_scale {scale} "
              f"(target {TARGET_HEIGHT_M} m)")
        write(build_character(export_scale=scale))
    else:
        write(build_character())


if __name__ == "__main__":
    main()
