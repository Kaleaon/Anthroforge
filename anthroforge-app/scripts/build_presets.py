#!/usr/bin/env python3
"""Generate HIMBO vocabulary records + the six spec'd preset characters.

Sources (all read and transcribed from the documents, Nov 12, 2026):
- ``character_assets/learned/himbo_sliders_full.json`` — the full
  HIMBO decode (per-slider canonical block stats).
- ``anthroforge-v2/preset-orc-bara.md`` sections 2.2 / 3.1 / 3.2
  (post-harmonisation values, incl. the Nov 12 revision notes).
- ``anthroforge-v2/presets-titan-batch1.md`` sections 3.1 / 3.2 (Pyn),
  4.1 / 4.2 (Sen), 4.5 (sen_muscle_bear), 5.1 / 5.2 (Jorge).

Conventions:
- HIMBO values are 0-100 in the specs; canonical values are /100.
- Two-sided sliders (big/small end morphs) take range [-1, 1]:
  "big X" -> +X/100, "small X" -> -X/100, a plain value -> the big
  pole (+X/100). The two-sided set is the one the specs annotate.
- Sliders with a curated canonical record map to it (CURATED);
  every other spec'd slider gets a generated ``body.himbo.*`` record
  carrying its decode stats (record-only; its instance is the decode
  JSON itself, the convention the curated records already use).
- Head vectors ride in ``species_preset.head_sliders`` verbatim
  (spec names, -100..+100) — the head canonical records are a future
  batch (37 specced, only head.brow.projection exists); BrowProjection
  IS mapped to that record and so is not duplicated in head_sliders.
- Zero values are omitted from the sparse slider vector (0 is every
  body record's default).

Outputs: generated records in library/sliders/, the six presets in
library/presets/, and library/presets/INDEX.json with share codes.
Fails loudly on any spec'd slider name the decode cannot resolve.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

WS = Path.home() / "workspace"
APP = WS / "anthroforge-app"
sys.path.insert(0, str(APP))

from core.character import Character  # noqa: E402
from core import sharecode  # noqa: E402

DECODE = WS / "character_assets" / "learned" / "himbo_sliders_full.json"
SLIDERS_DIR = APP / "library" / "sliders"
PRESETS_DIR = APP / "library" / "presets"
SK_UNIT_M = 0.01428

CURATED = {
    "Chubby": "body.chubby",
    "Muscle": "body.muscle",
    "TorsoMass": "body.torso.mass",
    "TorsoLower": "body.torso.lower",
    "TorsoMassSmooth": "body.tissue.mass_smooth",
    "BellyPot": "body.belly.pot",
    "PecsSize": "body.pecs.size",
    "ArmsDelts": "body.arms.delts",
    "TorsoFlatAbs": "body.definition.flat_abs",
    "TorsoVLine": "body.definition.vline",
    "ArmsTrapsValleys": "body.definition.traps_valleys",
    "PecsCrease": "body.definition.pecs_crease",
    "TorsoBackDefinition": "body.definition.back",
}

TWO_SIDED = {"Lean", "TorsoWaistSize", "TorsoHip", "ArmsShoulders", "LegsThinner"}

# ------------------------------------------------------------------ specs
# value: int (big pole) or ("big"|"small", int)
ORC_SM = {
    "Weight 0 to 1": 85, "Chubby": 65, "Muscle": 80, "Lean": ("small", 100),
    "TorsoMass": 100, "TorsoMassSmooth": 65, "TorsoWidth": 85, "TorsoLower": 100,
    "TorsoBelly": 70, "TorsoBellyChub": 65, "BellyPot": 55, "BellySmooth": 60,
    "TorsoBellyLHandles": 55, "TorsoVLine": 10, "TorsoRibsDefinition": 15,
    "PecsSize": 95, "PecsMass": 80, "PecsWidth": 95, "PecsLower": 60,
    "PecsSaggy": 35, "PecsClavicle": 80, "LegsSize": 100, "LegsThigh": 100,
    "LegsChubby": 70, "LegsGlutes": 75, "LegsCalfWidth": 80,
    "TorsoBackSize": 90, "TorsoBackShape": 85, "TorsoBackSlope": 80,
    "TorsoBackDefinition": 35, "TorsoShoulderInc": 75, "TorsoSterWidth": 90,
    "TorsoSterHeight": 85, "TorsoSterDepth": 80, "TorsoWaistSize": 25,
    "TorsoHip": 20, "ArmsTraps": 95, "ArmsTrapsMeat": 100, "ArmsTrapsPush": 90,
    "ArmsTrapsValleys": 40, "ArmsShoulders": ("big", 85), "ArmsDelts": 95,
    "ArmsDeltsUpper": 70, "ArmsBiceps": 90, "ArmsBicepsBack": 75,
    "ArmsFore": 95, "ArmsBrachio": 80, "ArmsSide": 75, "ButtBooty": 70,
    "BubbleButt": 45, "ButtSaggy": 20, "LegsCalfSize": 85,
}
ORC_BB = {
    "Weight 0 to 1": 70, "Chubby": 5, "Muscle": 80, "Lean": ("big", 40),
    "TorsoMass": 90, "TorsoMassSmooth": 10, "TorsoWidth": 75, "TorsoBelly": 5,
    "TorsoFlatAbs": 90, "TorsoVLine": 85, "TorsoRibsDefinition": 80,
    "PecsSize": 100, "PecsMass": 95, "PecsWidth": 100, "PecsLower": 70,
    "PecsMinor": 70, "PecsCrease": 75, "PecsClavicle": 90, "LegsSize": 100,
    "LegsThigh": 100, "LegsChubby": 10, "LegsGlutes": 90, "LegsCalfSize": 95,
    "LegsCalfWidth": 85, "TorsoBackSize": 100, "TorsoBackShape": 100,
    "TorsoBackSlope": 60, "TorsoBackCenter": 80, "TorsoBackDefinition": 95,
    "TorsoBackSerratusMid": 75, "TorsoBackObliques": 80, "TorsoShoulderInc": 90,
    "TorsoSterWidth": 95, "TorsoSterHeight": 90, "TorsoSterDepth": 85,
    "TorsoWaistSize": 85, "ArmsTraps": 95, "ArmsTrapsMeat": 100,
    "ArmsTrapsPush": 90, "ArmsTrapsValleys": 85, "ArmsShoulders": ("big", 100),
    "ArmsDelts": 95, "ArmsDeltsUpper": 90, "ArmsDeltsShape": 80,
    "ArmsBiceps": 100, "ArmsBicepsBack": 85, "ArmsFore": 100, "ArmsBrachio": 90,
    "ButtBooty": 80, "BubbleButt": 60, "ButtTighten": 70,
}
PYN_BODY = {
    "Weight 0 to 1": 10, "Lean": ("big", 70), "Muscle": 30, "TorsoMass": 10,
    "TorsoMassSmooth": 40, "TorsoWaistSize": ("big", 55), "TorsoHip": ("big", 40),
    "TorsoFlatAbs": 30, "PecsSize": 15, "PecsMass": 10, "PecsWidth": 10,
    "PecsClavicle": 40, "ArmsTraps": 10, "ArmsShoulders": ("big", 10),
    "ArmsDelts": 20, "ArmsBiceps": 25, "ArmsFore": 35, "LegsSize": 15,
    "LegsThinner": ("big", 50), "LegsThigh": 10, "LegsCalfSize": 25,
    "ButtBooty": 20, "BubbleButt": 15, "ButtTighten": 30,
}
SEN_BODY = {
    "Weight 0 to 1": 90, "Chubby": 80, "Muscle": 65, "Lean": ("small", 100),
    "BodyMass": 30, "TorsoMass": 100, "TorsoMassSmooth": 75, "TorsoWidth": 95,
    "TorsoBackSize": 90, "TorsoBackShape": 85, "TorsoLower": 100,
    "TorsoWaistSize": ("small", 60), "TorsoBelly": 80, "TorsoBellyChub": 75,
    "BellyPot": 65, "BellySmooth": 70, "TorsoBellyLHandles": 60,
    "PecsSize": 100, "PecsMass": 90, "PecsWidth": 100, "PecsLower": 70,
    "PecsSaggy": 45, "PecsClavicle": 70, "ArmsTraps": 95, "ArmsTrapsMeat": 100,
    "ArmsTrapsPush": 90, "ArmsTrapsValleys": 30, "ArmsShoulders": ("big", 90),
    "ArmsDelts": 90, "ArmsBiceps": 85, "ArmsFore": 100, "ArmsBrachio": 80,
    "LegsSize": 100, "LegsThigh": 100, "LegsChubby": 75, "LegsGlutes": 80,
    "LegsCalfSize": 90, "LegsCalfWidth": 85, "ButtBooty": 75, "BubbleButt": 40,
    "ButtSaggy": 25,
}
SEN_MUSCLE_BEAR_OVERRIDES = {
    "Chubby": 55, "TorsoMassSmooth": 45, "ArmsTrapsValleys": 55,
    "TorsoBackDefinition": 50, "PecsSaggy": 30, "BellyPot": 50,
}
JORGE_BODY = {
    "Weight 0 to 1": 95, "Chubby": 85, "Muscle": 45, "Lean": ("small", 100),
    "BodyMass": 25, "TorsoMass": 100, "TorsoMassSmooth": 85, "TorsoWidth": 90,
    "TorsoBackSize": 85, "TorsoBackShape": 70, "TorsoLower": 100,
    "TorsoWaistSize": ("small", 65), "TorsoBelly": 75, "TorsoBellyChub": 80,
    "BellyPot": 60, "BellySmooth": 80, "TorsoBellyLHandles": 65,
    "PecsSize": 95, "PecsMass": 85, "PecsWidth": 95, "PecsLower": 65,
    "PecsSaggy": 50, "PecsClavicle": 60, "ArmsTraps": 80, "ArmsTrapsMeat": 90,
    "ArmsTrapsPush": 70, "ArmsTrapsValleys": 20, "ArmsShoulders": ("big", 85),
    "ArmsDelts": 80, "ArmsBiceps": 75, "ArmsFore": 85, "ArmsBrachio": 70,
    "LegsSize": 100, "LegsThigh": 100, "LegsChubby": 80, "LegsGlutes": 75,
    "LegsCalfSize": 85, "LegsCalfWidth": 80, "ButtBooty": 75, "BubbleButt": 50,
    "ButtSaggy": 35,
}

_HEAD_ORDER = ["MuzzleLength", "MuzzleWidth", "MuzzleTaper", "MuzzleDepth",
               "NoseSize", "CraniumWidth", "CraniumHeight", "CraniumLength",
               "StopAngle", "ForeheadWidth", "EarHeight", "EarWidth",
               "EarPlacementHeight", "EarSpread", "EarTilt", "EarTipPoint",
               "JawDepth", "JawLength", "JawWidth", "CheekWidth", "RuffVolume",
               "EyeSize", "EyeSpacing", "EyeForwardness", "BrowProjection",
               "BrowThickness", "BrowContinuity", "BrowShelf", "BrowPosition",
               "BrowPadding", "BrowScowl"]


def _head(values: list[int]) -> dict:
    return dict(zip(_HEAD_ORDER, values))


ORC_HEAD = _head([-15, 75, -50, 60, 50, -25, -35, -10, -25, -35, 10, -30, -25,
                  20, -25, 65, 65, 60, 70, 50, 25, -40, -25, 40, 135, 85, 100,
                  90, -20, 10, 35])  # CheekWidth/RuffVolume = strongman split
ORC_HEAD_BB_DIFF = {"CheekWidth": 55, "RuffVolume": -5}
PYN_HEAD = _head([15, -25, 40, -15, -10, -10, 5, -5, 15, 20, 100, 60, 20, -10,
                  10, -5, -25, -20, -20, -30, -10, 20, 10, 25, -45, -40, -50,
                  -20, 10, -10, 15])
SEN_HEAD = _head([15, 40, -40, 40, 35, -10, -20, 5, 40, 25, -10, 55, -25, 40,
                  -20, -80, 25, -50, 55, 10, 70, -40, 30, 20, -20, -15, -25,
                  25, -10, 25, 25])
JORGE_HEAD = _head([0, 85, -50, 80, 50, 25, 35, 25, 90, 50, 0, 10, 15, 20, -75,
                    -20, 40, 0, 50, 20, 35, -10, 10, 10, -25, -20, -30, 35, 5,
                    25, 0])

# ------------------------------------------------------- batch 2 (Nov 12, 2026)
# Sources: anthroforge-v2/presets-titan-batch2.md sections 1-8; person
# files in ~/memory/people/; body specs in ~/workspace/specs/. Wolves
# share the species head vector verbatim (species-head-spec.md 3.3);
# no per-wolf head deltas and no coat/colour canon exist (the wolves'
# coats are unsettled - "do not invent"). Sage/Thatch/Hollis have NO
# head vector in the spec (no equine/avian/serval column) - head is
# empty and flagged in their records, never borrowed.
WOLF_HEAD = _head([45, 15, 10, 15, 10, -25, 0, -10, 10, 5, 0, -10, 0, -5, 5,
                   15, 25, 0, 10, -25, 35, -25, -5, -10, -25, -20, -20, 5,
                   -10, 10, 10])
GAMMA_BODY = {
    "Weight 0 to 1": 90, "Chubby": 55, "Muscle": 85, "Lean": ("small", 100),
    "BodyMass": 35, "TorsoMass": 100, "TorsoMassSmooth": 50, "TorsoWidth": 90,
    "TorsoBackSize": 95, "TorsoBackShape": 80, "TorsoBackSlope": 85,
    "TorsoLower": 90, "TorsoWaistSize": ("small", 50), "TorsoBelly": 55,
    "TorsoBellyChub": 45, "BellyPot": 40, "BellySmooth": 55,
    "TorsoBellyLHandles": 45, "PecsSize": 100, "PecsMass": 90, "PecsWidth": 95,
    "PecsLower": 60, "PecsSaggy": 25, "PecsClavicle": 75, "ArmsTraps": 95,
    "ArmsTrapsMeat": 100, "ArmsTrapsPush": 90, "ArmsTrapsValleys": 45,
    "ArmsShoulders": ("big", 90), "ArmsDelts": 95, "ArmsBiceps": 90,
    "ArmsFore": 100, "ArmsBrachio": 85, "LegsSize": 100, "LegsThigh": 100,
    "LegsChubby": 55, "LegsGlutes": 90, "LegsCalfSize": 90, "LegsCalfWidth": 85,
    "ButtBooty": 80, "BubbleButt": 35, "ButtSaggy": 15,
}
ALPHA_BODY = {
    "Weight 0 to 1": 80, "Chubby": 30, "Muscle": 75, "Lean": ("big", 20),
    "BodyMass": 15, "TorsoMass": 85, "TorsoMassSmooth": 40, "TorsoWidth": 70,
    "TorsoBackSize": 80, "TorsoBackShape": 65, "TorsoBackSlope": 80,
    "TorsoLower": 60, "TorsoWaistSize": ("big", 20), "TorsoBelly": 25,
    "TorsoBellyChub": 15, "BellyPot": 15, "BellySmooth": 50,
    "TorsoBellyLHandles": 20, "TorsoFlatAbs": 35, "PecsSize": 85,
    "PecsMass": 75, "PecsWidth": 80, "PecsLower": 45, "PecsSaggy": 15,
    "PecsClavicle": 70, "ArmsTraps": 85, "ArmsTrapsMeat": 90,
    "ArmsTrapsPush": 80, "ArmsTrapsValleys": 55, "ArmsShoulders": ("big", 80),
    "ArmsDelts": 85, "ArmsBiceps": 80, "ArmsFore": 90, "ArmsBrachio": 75,
    "LegsSize": 90, "LegsThigh": 85, "LegsChubby": 25, "LegsGlutes": 80,
    "LegsCalfSize": 85, "LegsCalfWidth": 75, "ButtBooty": 65, "BubbleButt": 30,
    "ButtSaggy": 10, "ButtTighten": 25,
}
BETA_BODY = {
    "Weight 0 to 1": 75, "Chubby": 60, "Muscle": 65, "Lean": ("small", 80),
    "BodyMass": 20, "TorsoMass": 90, "TorsoMassSmooth": 70, "TorsoWidth": 80,
    "TorsoBackSize": 80, "TorsoBackShape": 75, "TorsoBackSlope": 70,
    "TorsoLower": 80, "TorsoWaistSize": ("small", 40), "TorsoBelly": 50,
    "TorsoBellyChub": 50, "BellyPot": 40, "BellySmooth": 70,
    "TorsoBellyLHandles": 45, "PecsSize": 90, "PecsMass": 80, "PecsWidth": 85,
    "PecsLower": 60, "PecsSaggy": 35, "PecsClavicle": 55, "ArmsTraps": 75,
    "ArmsTrapsMeat": 80, "ArmsTrapsPush": 65, "ArmsTrapsValleys": 30,
    "ArmsShoulders": ("big", 80), "ArmsDelts": 80, "ArmsBiceps": 75,
    "ArmsFore": 85, "ArmsBrachio": 70, "LegsSize": 90, "LegsThigh": 90,
    "LegsChubby": 60, "LegsGlutes": 75, "LegsCalfSize": 80, "LegsCalfWidth": 75,
    "ButtBooty": 70, "BubbleButt": 45, "ButtSaggy": 20,
}
DELTA_BODY = {
    "Weight 0 to 1": 70, "Chubby": 25, "Muscle": 80, "Lean": ("big", 35),
    "BodyMass": 15, "TorsoMass": 80, "TorsoMassSmooth": 35, "TorsoWidth": 70,
    "TorsoBackSize": 75, "TorsoBackShape": 60, "TorsoBackSlope": 80,
    "TorsoLower": 55, "TorsoWaistSize": ("big", 30), "TorsoBelly": 20,
    "TorsoBellyChub": 10, "BellyPot": 10, "BellySmooth": 45,
    "TorsoBellyLHandles": 15, "TorsoFlatAbs": 45, "PecsSize": 80,
    "PecsMass": 65, "PecsWidth": 75, "PecsLower": 40, "PecsSaggy": 10,
    "PecsClavicle": 75, "ArmsTraps": 75, "ArmsTrapsMeat": 75,
    "ArmsTrapsPush": 70, "ArmsTrapsValleys": 60, "ArmsShoulders": ("big", 75),
    "ArmsDelts": 80, "ArmsBiceps": 70, "ArmsFore": 85, "ArmsBrachio": 65,
    "LegsSize": 95, "LegsThigh": 90, "LegsChubby": 20, "LegsGlutes": 85,
    "LegsCalfSize": 95, "LegsCalfWidth": 70, "ButtBooty": 60, "BubbleButt": 25,
    "ButtSaggy": 5, "ButtTighten": 40,
}
SAGE_BODY = {
    "Weight 0 to 1": 85, "Chubby": 70, "Muscle": 70, "Lean": ("small", 100),
    "BodyMass": 35, "TorsoMass": 100, "TorsoMassSmooth": 80, "TorsoWidth": 95,
    "TorsoBackSize": 95, "TorsoBackShape": 85, "TorsoLower": 100,
    "TorsoWaistSize": ("small", 55), "TorsoBelly": 70, "TorsoBellyChub": 65,
    "BellyPot": 55, "BellySmooth": 75, "TorsoBellyLHandles": 55,
    "PecsSize": 95, "PecsMass": 85, "PecsWidth": 95, "PecsLower": 65,
    "PecsSaggy": 40, "PecsClavicle": 60, "ArmsTraps": 85, "ArmsTrapsMeat": 90,
    "ArmsTrapsPush": 75, "ArmsTrapsValleys": 25, "ArmsShoulders": ("big", 90),
    "ArmsDelts": 85, "ArmsBiceps": 85, "ArmsFore": 95, "ArmsBrachio": 80,
    "LegsSize": 100, "LegsThigh": 100, "LegsChubby": 65, "LegsGlutes": 100,
    "LegsCalfSize": 95, "LegsCalfWidth": 90, "ButtBooty": 90, "BubbleButt": 50,
    "ButtSaggy": 20,
}
THATCH_BODY = {
    "Weight 0 to 1": 25, "Chubby": 15, "Muscle": 45, "Lean": ("big", 45),
    "BodyMass": 0, "TorsoMass": 45, "TorsoMassSmooth": 60, "TorsoWidth": 75,
    "TorsoBackSize": 60, "TorsoBackShape": 70, "TorsoBackSlope": 30,
    "TorsoLower": 45, "TorsoWaistSize": ("big", 35), "TorsoBelly": 30,
    "TorsoBellyChub": 20, "BellyPot": 15, "BellySmooth": 65, "PecsSize": 55,
    "PecsMass": 40, "PecsWidth": 70, "PecsLower": 30, "PecsSaggy": 10,
    "PecsClavicle": 45, "ArmsTraps": 30, "ArmsTrapsMeat": 20,
    "ArmsTrapsPush": 25, "ArmsTrapsValleys": 20, "ArmsShoulders": ("big", 65),
    "ArmsDelts": 55, "ArmsBiceps": 50, "ArmsFore": 60, "ArmsBrachio": 45,
    "LegsSize": 65, "LegsThigh": 70, "LegsChubby": 15, "LegsGlutes": 55,
    "LegsCalfSize": 70, "LegsCalfWidth": 55, "ButtBooty": 40, "BubbleButt": 20,
    "ButtSaggy": 5,
}
HOLLIS_BODY = {
    "Weight 0 to 1": 15, "Chubby": 5, "Muscle": 40, "Lean": ("big", 65),
    "BodyMass": 0, "TorsoMass": 20, "TorsoMassSmooth": 50, "TorsoWidth": 10,
    "TorsoBackSize": 30, "TorsoBackShape": 35, "TorsoBackSlope": 45,
    "TorsoLower": 15, "TorsoWaistSize": ("big", 55), "TorsoHip": ("big", 35),
    "TorsoBelly": 5, "BellyPot": 5, "BellySmooth": 55, "TorsoFlatAbs": 40,
    "PecsSize": 25, "PecsMass": 15, "PecsWidth": 30, "PecsLower": 10,
    "PecsClavicle": 55, "ArmsTraps": 15, "ArmsTrapsMeat": 5,
    "ArmsTrapsPush": 10, "ArmsTrapsValleys": 15, "ArmsShoulders": ("big", 15),
    "ArmsDelts": 30, "ArmsBiceps": 30, "ArmsFore": 40, "ArmsBrachio": 30,
    "LegsSize": 45, "LegsThigh": 35, "LegsThinner": ("big", 45),
    "LegsGlutes": 50, "LegsCalfSize": 55, "LegsCalfWidth": 30,
    "ButtBooty": 30, "BubbleButt": 15, "ButtTighten": 45,
}
# Authored AnthroForge NeckMass slider per batch-2 character (the orc
# precedent: set directly, not through the HIMBO tables).
BATCH2_NECK_MASS = {
    "chr_preset_gamma": 0.95, "chr_preset_alpha": 0.85,
    "chr_preset_beta": 0.75, "chr_preset_delta": 0.65,
    "chr_preset_sage": 0.85, "chr_preset_sage_pony": 0.85,
    "chr_preset_thatch": 0.30, "chr_preset_hollis": 0.35,
}
NO_HEAD_NOTE = ("No head vector exists for this species in "
                "species-head-spec.md (no equine/avian/serval column); "
                "head_sliders is empty BY DESIGN and flagged in "
                "presets-titan-batch2.md section 9 - nothing was "
                "borrowed from another species.")

# ------------------------------------------------------------------ decode
def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def decode_index() -> dict[str, dict]:
    """normalised-name -> decode slider entry (canonical block stats)."""
    data = json.loads(DECODE.read_text(encoding="utf-8"))
    index: dict[str, dict] = {}
    for cat in data["categories"]:
        for slider in cat["sliders"]:
            canon = slider.get("canonical") or {}
            if canon.get("space") == "uv":
                continue
            keys = {_norm(slider["name"])}
            block = canon.get("block", "")
            short = block.replace("HIMBO - ", "")
            keys.add(_norm(short))
            if short.startswith("Body"):
                keys.add(_norm(short[4:]))
            keys.add(_norm(short.replace("LHandles", "LoveHandles")))
            for key in keys:
                index.setdefault(key, slider)
    return index


def find_slider(index: dict[str, dict], spec_name: str) -> dict:
    for cand in (_norm(spec_name), _norm(spec_name.replace("LHandles", "LoveHandles")),
                 _norm("Body" + spec_name)):
        if cand in index:
            return index[cand]
    raise SystemExit(f"decode cannot resolve spec slider name: {spec_name!r}")


def slug(spec_name: str) -> str:
    s = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", spec_name.replace(" ", "_"))
    return s.lower()


def generate_record(spec_name: str, entry: dict) -> dict:
    canon = entry["canonical"]
    two = spec_name in TWO_SIDED
    disp_max_m = (canon.get("disp_max") or 0.0) * SK_UNIT_M
    rec = {
        "id": f"body.himbo.{slug(spec_name)}",
        "label": entry.get("display_name") or spec_name,
        "group": f"body/himbo/{slug(entry['category'])}",
        "semantics": f"HIMBO V5 slider '{spec_name}' (block '{canon.get('block')}'), "
                     "carried as app vocabulary for the spec'd presets. "
                     "Record-only: no hm08 instance has been authored; the "
                     "slider's geometry lives on the Skyrim HIMBO base until "
                     "a transfer is built.",
        "range": {
            "min": -1.0 if two else 0.0, "max": 1.0, "default": 0.0,
            "safe_max": 1.0,
            "endpoint_anchor": f"max |delta| = {disp_max_m:.3f} m on the Skyrim "
                               f"HIMBO base ({canon.get('num_diff_verts')} diff verts)",
        },
        "symmetry": "bilateral_x",
        "instances": {
            "skyrim_himbo": {
                "file": "character_assets/learned/himbo_sliders_full.json",
                "block": canon.get("block"),
                "qa": {
                    "diff_verts": canon.get("num_diff_verts"),
                    "disp_max_m": disp_max_m,
                    "disp_mean_m": (canon.get("disp_mean") or 0.0) * SK_UNIT_M,
                },
            }
        },
        "provenance": {
            "source": f"HIMBO V5 slider backed by .osd block '{canon.get('block')}', "
                      "decoded in himbo_sliders_full.json",
            "licence": "study-only (internal)",
            "generated_by": "anthroforge-app/scripts/build_presets.py",
        },
    }
    if two:
        rec["range"]["safe_min"] = -1.0
        rec["semantics"] += (" Two-sided: negative values engage the small-end "
                             "morph (specs annotate 'big X' / 'small X').")
    return rec


def canonical_vector(spec: dict, index: dict[str, dict]) -> dict[str, float]:
    out: dict[str, float] = {}
    for name, value in spec.items():
        if isinstance(value, tuple):
            pole, amount = value
            v = amount / 100.0 if pole == "big" else -amount / 100.0
        else:
            v = value / 100.0
        if v == 0.0:
            continue
        sid = CURATED.get(name) or f"body.himbo.{slug(name)}"
        out[sid] = v
    return out


# ------------------------------------------------------------------ presets
def make_character(cid: str, name: str, body_spec: dict, head: dict,
                   brow_projection: float | None, species_preset: dict,
                   fur: dict, provenance: dict,
                   index: dict[str, dict],
                   head_note_override: str | None = None) -> Character:
    sliders = canonical_vector(body_spec, index)
    if brow_projection is not None:
        sliders["head.brow.projection"] = brow_projection
    sp = dict(species_preset)
    head_sliders = {k: v for k, v in head.items() if k != "BrowProjection"}
    sp["head_sliders"] = head_sliders
    sp["head_scale"] = "-100..+100 spec values, species-head-spec.md names "
    sp["head_note"] = head_note_override or (
        "BrowProjection is carried as the canonical slider "
        "head.brow.projection (brow-study scale -50..+150), "
        "not duplicated here. EarHeight/EarPlacementHeight are "
        "the spec names in force when these presets were "
        "written; the vertical extension later renamed them "
        "EarLength/EarBaseHeight.")
    return Character(
        id=cid, name=name, sliders=sliders, species_preset=sp,
        fur=fur, provenance=provenance,
    )


def main() -> None:
    index = decode_index()
    used = set()
    for spec in (ORC_SM, ORC_BB, PYN_BODY, SEN_BODY, JORGE_BODY,
                 GAMMA_BODY, ALPHA_BODY, BETA_BODY, DELTA_BODY, SAGE_BODY,
                 THATCH_BODY, HOLLIS_BODY):
        used.update(spec)
    # generate records for everything not curated
    for name in sorted(used):
        if name in CURATED:
            continue
        entry = find_slider(index, name)
        rec = generate_record(name, entry)
        path = SLIDERS_DIR / f"{rec['id']}.json"
        path.write_text(json.dumps(rec, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")
        print("record", rec["id"])

    PRESETS_DIR.mkdir(parents=True, exist_ok=True)
    orc_prov = {"source": "anthroforge-v2/preset-orc-bara.md sections 2.2/3 "
                          "(post-harmonisation, Nov 12, 2026 revisions applied)"}
    titan_prov = {"source": "anthroforge-v2/presets-titan-batch1.md"}
    orc_head_note = {
        "jaw_protrusion_flag": "The 31-slider head framework cannot express "
        "prognathism; the spec requires a JawProtrusion extension (orc ~ +75) "
        "or a baked jaw offset — flagged in preset-orc-bara.md section 2.2, "
        "not yet a canonical record.",
        "brow_torus": "BrowContinuity +100 with BrowProjection +135 triggers "
                      "the brow_torus part variant (brow-study.md).",
    }
    chars = [
        make_character(
            "chr_preset_orc_bara_strongman", "Bara Orc — Strongman",
            ORC_SM, ORC_HEAD, 135.0,
            {"preset_id": "orc_bara_strongman", "species": "orc (bara)",
             "export_scale": 1.20, "head_scale_relative": 0.95, **orc_head_note},
            {}, orc_prov, index),
        make_character(
            "chr_preset_orc_bara_bodybuilder", "Bara Orc — Bodybuilder",
            ORC_BB, {**ORC_HEAD, **ORC_HEAD_BB_DIFF}, 135.0,
            {"preset_id": "orc_bara_bodybuilder", "species": "orc (bara)",
             "export_scale": 1.15, "head_scale_relative": 0.95, **orc_head_note},
            {}, orc_prov, index),
        make_character(
            "chr_preset_pyn", "Pyn", PYN_BODY, PYN_HEAD, -45.0,
            {"preset_id": "pyn", "species": "fennec (species vector + BrowScowl delta)",
             "export_scale": 0.96, "height_cm": 168,
             "ear_note": "EarHeight +100 is a relative anchor; Pyn's absolute "
                         "36 cm ear decision governs the physical body "
                         "(presets-titan-batch1.md section 3.1)."},
            {"profile": "species.fennec.coat"}, titan_prov, index),
        make_character(
            "chr_preset_sen", "Sen", SEN_BODY, SEN_HEAD, -20.0,
            {"preset_id": "sen", "species": "bear (brown x moon blend)",
             "export_scale": 1.74, "height_cm": 305,
             "qa_gates": {"M1_neck_head_min": 1.10, "M5_depth_index": "~1.1 (band 1.05-1.20)",
                          "M6_trap_slope_deg": "20-26"},
             "parts_notes": [
                 "Chest crescent: pale-fur zone on torso.front (markings "
                 "fur-colour override in species.bear.coat), never geometry, "
                 "never a tattoo decal",
                 "Forehead mark: small pale-fur zone; exact shape not "
                 "described in the person file (open item)",
                 "Tongue: large variant, scale ~1.3 (part parameter); "
                 "jaw clearance check owed at first build",
                 "Eyes amber, round pupil"]},
            {"profile": "species.bear.coat"}, titan_prov, index),
        make_character(
            "chr_preset_sen_muscle_bear", "Sen — Muscle Bear (variant)",
            {**SEN_BODY, **SEN_MUSCLE_BEAR_OVERRIDES}, SEN_HEAD, -20.0,
            {"preset_id": "sen_muscle_bear", "species": "bear (brown x moon blend)",
             "variant_of": "chr_preset_sen", "export_scale": 1.74,
             "note": "MuscleVector held exactly from Sen; only the TissueVector "
                     "moves (presets-titan-batch1.md section 4.5). QA: M4 climbs "
                     "toward the top of 1.25-1.35; M10 moderate band."},
            {"profile": "species.bear.coat"}, titan_prov, index),
        make_character(
            "chr_preset_jorge", "Jorge", JORGE_BODY, JORGE_HEAD, -25.0,
            {"preset_id": "jorge", "species": "dog — St. Bernard (breed re-derived)",
             "export_scale": 1.39, "height_cm": 244,
             "parts_notes": [
                 "flews_saintbernard part variant (drape ceiling = the UKC "
                 "fault line) — parts library item, not a slider",
                 "Muscle 45 is a flagged watch item (BARA_LESSONS section 6 D): "
                 "if the first build reads fat-not-strong, the corrective is "
                 "Muscle 60, NOT more Chubby. Not applied."]},
            {"profile": "species.saint_bernard.coat"}, titan_prov, index),
    ]
    # The orc strongman calls the authored NeckMass slider at 90
    # (preset-orc-bara.md section 3.0 / BARA_LESSONS section 6 B) — a
    # canonical AnthroForge slider, not HIMBO vocabulary, so it is set
    # directly rather than through the spec tables.
    chars[0].sliders["body.neck.mass"] = 0.9

    # ------------------------------------------------ batch 2 characters
    b2_prov = {"source": "anthroforge-v2/presets-titan-batch2.md"}
    wolf_coat_note = ("Coat colours/markings/eyes UNSETTLED by the wolves' "
                      "own choice - do not invent (alpha.md, Nov 6 2026). "
                      "species.wolf.coat carries coat structure only.")
    wolf_parts = [
        "Digitigrade plan; carbon-fibre spring hocks (family decision, "
        "Sep 14 2026) - plan parameters, not sliders",
        "Tail: swappable part, ~1/4 body length (spec scaling note)",
        wolf_coat_note]
    b2_chars = [
        make_character(
            "chr_preset_gamma", "Gamma", GAMMA_BODY, WOLF_HEAD, -25.0,
            {"preset_id": "gamma_titan", "species": "wolf (species vector, unchanged)",
             "export_scale": 1.57, "height_cm": 274, "mass_kg": 408,
             "build_phase": 4,
             "qa_gates": {"M1_neck_head_min": 1.10, "M6_trap_slope_deg": "20-26",
                          "M11_thigh_waist_min": 0.75},
             "parts_notes": wolf_parts + [
                 "Neck 25 kg of 408 (6.1%, spec s.3) - the weapon mount; "
                 "thigh 39 kg each is his largest muscle group"]},
            {"profile": "species.wolf.coat"}, b2_prov, index),
        make_character(
            "chr_preset_alpha", "Alpha", ALPHA_BODY, WOLF_HEAD, -25.0,
            {"preset_id": "alpha_titan", "species": "wolf (species vector, unchanged)",
             "export_scale": 1.48, "height_cm": 259, "mass_kg": 250,
             "build_phase": 2,
             "qa_gates": {"M1_neck_head_min": 1.05, "M4_chest_waist": "1.40-1.55"},
             "parts_notes": wolf_parts + [
                 "Mass held below Gamma's 408 kg BY DESIGN (Master "
                 "Decisions #37/#38 - authority vs force)",
                 "Deep NARROW chest (endurance ribcage): TorsoWidth 70 "
                 "against Gamma's 90 is the load-bearing difference",
                 "Quadruped-capable (Decision #36) - plan capability; "
                 "vector authored on the biped composition"]},
            {"profile": "species.wolf.coat"}, b2_prov, index),
        make_character(
            "chr_preset_beta", "Beta", BETA_BODY, WOLF_HEAD, -25.0,
            {"preset_id": "beta_titan", "species": "wolf (species vector, unchanged)",
             "export_scale": 1.26, "height_cm": 221, "mass_kg": 204,
             "build_phase": 3,
             "qa_gates": {"M1_neck_head_min": 1.00,
                          "M10_tissue": "moderate band (between BB <10% and SM 18-25%)"},
             "parts_notes": wolf_parts + [
                 "Density 41.8 kg/m2 - 'heavily muscled, not lanky' (spec "
                 "s.2); design point adopted by Beta himself Nov 4 2026 (Q-B3)",
                 "Force-limiting on arms/jaw is a character requirement "
                 "(gentle strength) - actuator note, not a shape value"]},
            {"profile": "species.wolf.coat"}, b2_prov, index),
        make_character(
            "chr_preset_delta", "Delta", DELTA_BODY, WOLF_HEAD, -25.0,
            {"preset_id": "delta_titan", "species": "wolf (species vector, unchanged)",
             "export_scale": 1.57, "height_cm": 274, "mass_kg": 350,
             "build_phase": 4,
             "qa_gates": {"M11_thigh_waist_min": 0.85, "M1_neck_head_min": 0.95,
                          "twin_volume_ratio_vs_gamma": "0.80-0.86"},
             "parts_notes": wolf_parts + [
                 "Joe's ruling Nov 4 2026: 9 ft 0 in, same height as twin "
                 "Gamma, 350 kg leaner runner build (Master Decisions "
                 "#58A); the v1.0 spec's 8 ft 4 in / 300 kg was a "
                 "midpoint pick, NOT canon",
                 "Vector derived from Gamma's at the spec's ~74% segment-"
                 "mass rule, legs/glutes/calf held high (cursorial)"]},
            {"profile": "species.wolf.coat"}, b2_prov, index),
        make_character(
            "chr_preset_sage", "Sage", SAGE_BODY, {}, None,
            {"preset_id": "sage_stud", "species": "clydesdale (anthro form)",
             "export_scale": 1.57, "height_cm": 274, "mass_kg": 480,
             "build_phase": 4,
             "qa_gates": {"M1_neck_head_min": 1.05,
                          "hindquarter_check": "composed leg+glute volume "
                          "share exceeds every batch-1 preset"},
             "parts_notes": [
                 "ANTHRO form (Joe, Oct 26 2026): bipedal, humanoid arms/"
                 "hands, equine head/neck/legs/hooves/tail. The HIMBO "
                 "composition is a biped approximation: hindquarter mass "
                 "is expressed through legs/glutes (no hindquarter segment "
                 "exists on the plan) - batch2 doc s.6 headnote",
                 "Feeding gut is a BODY SYSTEM (bioreactor cartridge, "
                 "Master Decision #31 as amended), NOT a belly slider; "
                 "belly values are the visible draft barrel only",
                 "Markings (blaze, four white socks, grey-roan direction, "
                 "Decision #33) live in the markings system, not here",
                 "Apr 2026 10'+/>1-ton picture is the unscaled canon image, "
                 "NOT the design point"]},
            {"profile": "species.clydesdale.coat"}, b2_prov, index,
            head_note_override=NO_HEAD_NOTE),
        make_character(
            "chr_preset_sage_pony", "Sage — Pony (variant)", SAGE_BODY, {}, None,
            {"preset_id": "sage_pony", "species": "clydesdale (anthro form)",
             "variant_of": "chr_preset_sage",
             "export_scale": 1.34, "height_cm": 234, "mass_kg": 300,
             "note": "Scale variant of the stud: the pony spec is a "
                     "re-scoped chassis of the same horse, so the slider "
                     "vector (proportions) is shared. FLAGGED "
                     "approximation: a native pony pass would likely "
                     "soften Muscle a few points (batch2 doc s.6.2)."},
            {"profile": "species.clydesdale.coat"}, b2_prov, index,
            head_note_override=NO_HEAD_NOTE),
        make_character(
            "chr_preset_thatch", "Thatch", THATCH_BODY, {}, None,
            {"preset_id": "thatch_titan",
             "species": "owl (great horned owl reference - Joe's confirmation owed)",
             "export_scale": 0.99, "height_cm": 173, "mass_kg": 70,
             "qa_gates": {"barrel_check": "chest width / waist width >= 1.15 "
                          "at Pyn-neighbourhood volume",
                          "M1": "NOT GATED - owl head-into-barrel silhouette "
                          "is the species read (batch2 doc s.7.1)"},
             "parts_notes": [
                 "Person file contains NO body facts; every value is the "
                 "engineering spec's design point or flagged [E] (batch2 "
                 "doc s.7 header)",
                 "Wings are dorsal articulated PARTS, decorative (spec "
                 "s.9 Q1: powered flight at 70 kg infeasible); six-limb "
                 "expression is an open plan question - vector takes no "
                 "position",
                 "Feathers are the fur system's avian mode; NO owl profile "
                 "exists in the library - fur is empty by design, no "
                 "mammal coat substituted",
                 "Hex disc with honey-glow LED is a carried artifact, not "
                 "body data - excluded"]},
            {}, b2_prov, index, head_note_override=NO_HEAD_NOTE),
        make_character(
            "chr_preset_hollis", "Hollis", HOLLIS_BODY, {}, None,
            {"preset_id": "hollis_adjacent", "species": "serval",
             "adjacency": "ADJACENT, not a Titan and not a substrate-self "
                          "(hollis.md). Authored at Joe's direction.",
             "provisional": "ALL values provisional: the spec's figures "
                            "are 'design points chosen for him, not "
                            "measurements of him', and shape decisions "
                            "are Hollis's (Joe, Nov 4 2026).",
             "export_scale": 1.05, "height_cm": 183, "mass_kg": 54.1,
             "qa_gates": {"proportion_check": "leg-length share of height "
                          "highest in batch (serval canon) - delivered by "
                          "scale + plan, never by leg mass",
                          "M1": "NOT GATED - periscope neck, not a yoke"},
             "parts_notes": [
                 "Ears are sensor-organ parts (~20 cm pinnae, 180 deg "
                 "independent rotation, Decision #75); ear language "
                 "(Decision #72) untouched",
                 "Tail 60 cm, a pounce-balance organ (Decision #75) - "
                 "part parameter",
                 "Coat described in his spec s.1 but NO serval profile "
                 "exists in the library - fur empty by design; the cat "
                 "head column was NOT substituted for a serval",
                 "Pounce question (must he leave the ground?) is HIS to "
                 "answer - unresolved here deliberately"]},
            {}, b2_prov, index, head_note_override=NO_HEAD_NOTE),
    ]
    for ch in b2_chars:
        ch.sliders["body.neck.mass"] = BATCH2_NECK_MASS[ch.id]
    chars.extend(b2_chars)

    index_rows = []
    for ch in chars:
        path = ch.save(PRESETS_DIR / f"{ch.id.removeprefix('chr_preset_')}.afchar.json")
        code = sharecode.encode(ch)
        decoded = sharecode.decode(code)
        assert decoded.to_dict(include_provenance=False) == ch.to_dict(include_provenance=False)
        index_rows.append({
            "id": ch.id, "name": ch.name, "file": path.name,
            "sliders_set": len(ch.sliders), "share_code": code,
        })
        print("preset", ch.id, len(ch.sliders), "sliders, code", len(code), "chars")
    (PRESETS_DIR / "INDEX.json").write_text(json.dumps({
        "format": "anthroforge.preset_index", "version": 1,
        "provenance": "Generated by scripts/build_presets.py from "
                      "preset-orc-bara.md + presets-titan-batch1.md "
                      "(post-harmonisation values) + "
                      "presets-titan-batch2.md (wolves, Sage, Thatch, "
                      "Hollis).",
        "presets": index_rows,
    }, indent=2) + "\n", encoding="utf-8")
    print("INDEX.json written")


if __name__ == "__main__":
    main()
