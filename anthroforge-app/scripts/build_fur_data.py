#!/usr/bin/env python3
"""Build the app's fur data files from the fur-craft deliverables.

- ``library/fur/species_profiles.json`` — the eight machine-readable
  species coat profiles from SPECIES_FUR.md section 9, extracted
  verbatim from that document's JSON blocks (no re-typing: the blocks
  are parsed out of the Markdown and re-emitted under the app format
  wrapper). Fails loudly if the profile set changes shape.
- ``library/fur/budgets.json`` — the platform / zone / LOD budgets
  from FUR_BUDGETS.md sections 3-5, transcribed from its tables.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

WS = Path.home() / "workspace"
SRC = WS / "anthroforge-v2" / "fur-craft" / "a19-species" / "SPECIES_FUR.md"
OUT = WS / "anthroforge-app" / "library" / "fur"

EXPECTED = [
    "species.wolf.coat", "species.red_fox.coat", "species.fennec.coat",
    "species.lion.coat", "species.bear.coat", "species.badger.coat",
    "species.saint_bernard.coat", "species.clydesdale.coat",
]


def extract_profiles() -> dict:
    text = SRC.read_text(encoding="utf-8")
    section9 = text.split("## 9.", 1)[1].split("## 10.", 1)[0]
    profiles = {}
    for block in re.findall(r"```json\n(.*?)```", section9, re.S):
        data = json.loads(block)
        profiles[data["profile"]] = data
    missing = [p for p in EXPECTED if p not in profiles]
    if missing:
        raise SystemExit(f"SPECIES_FUR.md section 9 is missing profiles: {missing}")
    if sorted(profiles) != sorted(EXPECTED):
        raise SystemExit(f"unexpected profile set: {sorted(profiles)}")
    return {
        "format": "anthroforge.fur_profiles",
        "version": 1,
        "provenance": {
            "source": "anthroforge-v2/fur-craft/a19-species/SPECIES_FUR.md section 9 "
                      "(machine-readable profiles, winter/prime defaults)",
            "note": "Region vocabulary and parameter columns are that document's "
                    "section 0 canon; colour values are representative mid-population "
                    "picks [E] — per-character palettes override them.",
        },
        "profiles": profiles,
    }


def budgets() -> dict:
    return {
        "format": "anthroforge.fur_budgets",
        "version": 1,
        "provenance": {
            "source": "anthroforge-v2/fur-craft/a5-budgets/FUR_BUDGETS.md sections 3-5",
            "note": "Budgets are caps for build/export QA, not targets; measured "
                    "audits of our own assets live in that document's section 7.",
        },
        "platforms": {
            "desktop_glb": {
                "label": "Desktop GLB (AnthroForge app, Babylon; showcase renders)",
                "whole_character_tris_max": 150000,
                "fur_lod0_tris_max": 48000,
                "fur_textures_vram_mb_max": 16,
                "fur_draw_calls_max": 3,
                "shell_layers_max": 8,
                "shell_scope": "short zones only",
            },
            "webgl_mobile": {
                "label": "WebGL / mobile — Telegram Mini App (phone webview, Babylon)",
                "tiers": {
                    "high": {
                        "whole_character_tris_max": 60000,
                        "fur": "LOD0 <= 24000 tris",
                        "fur_lod0_tris_max": 24000,
                        "overdraw_max": 2.0,
                        "fur_textures_vram_mb_max": 4,
                        "payload_mb_max": 3,
                        "fur_draw_calls_max": 1,
                    },
                    "low": {
                        "whole_character_tris_max": 25000,
                        "fur": "LOD1 only",
                        "fur_lod1_tris_max": 12000,
                        "overdraw_max": 1.0,
                        "fur_textures_vram_mb_max": 2,
                        "payload_mb_max": 1.5,
                        "fur_draw_calls_max": 1,
                        "shells": "off",
                    },
                },
                "notes": "Cutout core mandatory (FUR_BUDGETS.md section 6); KTX2/Basis "
                         "required for textures; the page renders at half device "
                         "resolution — keep that, it is worth more than any fur "
                         "optimisation.",
            },
            "second_life": {
                "label": "Second Life (Bento export profile)",
                "lod_slots": ["High", "Medium", "Low", "Lowest"],
                "halving_rule": "each lower LOD may carry ~half the triangles of the "
                                "one above with no download-weight penalty",
                "material_faces_max": 8,
                "tris_per_face_max": 21800,
                "fur_attachment_tris": {"High": 20000, "Medium": 10000, "Low": 5000,
                                        "Lowest": 500},
                "lowest_rule": "Lowest must be hand-authored (impostor-grade "
                               "cross-quads or a slim silhouette shell)",
                "technique": {"High": "cards", "Medium": "cards (half placements)",
                              "Low": "texture-only + silhouette cards",
                              "Lowest": "impostor"},
            },
        },
        "zones_lod0": {
            "tris_per_card": 8,
            "rows": [
                {"zone": "ruff_mane_cheeks", "length_mm": 170, "technique": "cards, cross-plane",
                 "desktop": {"placements": 1500, "tris": 18000},
                 "webgl": {"placements": 800, "tris": 9600},
                 "notes": "silhouette-critical; longest fur earns the most tris"},
                {"zone": "back_dorsal", "length_mm": 95, "technique": "cards",
                 "desktop": {"placements": 1100, "tris": 8800},
                 "webgl": {"placements": 550, "tris": 4400}},
                {"zone": "coat_general", "length_mm": 66, "technique": "cards",
                 "desktop": {"placements": 1600, "tris": 12800},
                 "webgl": {"placements": 800, "tris": 6400}},
                {"zone": "tail_ear_tufts_feathering", "length_mm": None, "technique": "cards",
                 "desktop": {"placements": 500, "tris": 4000},
                 "webgl": {"placements": 250, "tris": 2000},
                 "notes": "tail is a silhouette feature"},
                {"zone": "belly", "length_mm": 42,
                 "technique": "shells x6 (desktop/WebGL-high) / texture (else)",
                 "notes": "shell cost rides on the body LOD's zone tris, not a card count"},
                {"zone": "body_hair", "length_mm": 18,
                 "technique": "texture + fresnel fuzz; shells x4 max on desktop",
                 "notes": "a shader problem, not geometry"},
                {"zone": "muzzle_paws_inner_ear", "length_mm": 10,
                 "technique": "texture-only", "notes": "never geometry"},
            ],
            "card_subtotal_tris": {"desktop": 43600, "webgl": 22400},
            "density_note": "production LOD0 ~4,700 placements vs the prototype's 1,700 "
                            "(~2.8x) = ~1.28x body-surface quad ratio, the minimum at "
                            "which a card coat stops reading as tufts on clay; "
                            "ruff-heavy species push toward 1.5x",
        },
        "lod_switching": {
            "metric": "screen-height fraction f = character height / viewport height",
            "tiers": [
                {"tier": "LOD0", "f_min": 0.50, "content": "full cards + shells on"},
                {"tier": "LOD1", "f_min": 0.25, "content": "half card placements, shells x3, texture mip bias +1"},
                {"tier": "LOD2", "f_min": 0.10, "content": "quarter placements (silhouette zones only), shells off, body zones texture-only"},
                {"tier": "LOD3", "f_min": 0.0, "content": "texture-only fur; impostor cross-quads if the naked silhouette reads wrong"},
            ],
            "hysteresis": "switch down at f, back up at f x 1.15; minimum dwell 0.5 s; "
                          "bias one tier up within 10% of a boundary when the camera "
                          "moves toward the character",
            "per_zone": "zone tier = global tier, +1 for ruff/tail, -1 for belly/bodyhair",
            "textures": "textures are NOT per-LOD; all geometry LODs share one texture "
                        "set, resolution steps via mip bias",
        },
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "species_profiles.json").write_text(
        json.dumps(extract_profiles(), indent=2) + "\n", encoding="utf-8")
    (OUT / "budgets.json").write_text(
        json.dumps(budgets(), indent=2) + "\n", encoding="utf-8")
    print("fur data written:", sorted(p.name for p in OUT.glob("*.json")))


if __name__ == "__main__":
    main()
