"""Slider registry: seed records load, clamping behaves as specced."""

from pathlib import Path

import pytest

from core.character import Character
from core.errors import SliderRecordError, UnknownSliderError
from core.sliders import SliderRegistry

SLIDERS_DIR = Path(__file__).resolve().parent.parent / "library" / "sliders"


@pytest.fixture(scope="module")
def registry() -> SliderRegistry:
    return SliderRegistry.from_folder(SLIDERS_DIR)


SEED_IDS = [
    "body.arms.delts",
    "body.belly.pot",
    "body.belly.protrusion",
    "body.chest.broadness",
    "body.chubby",
    "body.definition.back",
    "body.definition.dial",
    "body.definition.flat_abs",
    "body.definition.pecs_crease",
    "body.definition.traps_valleys",
    "body.definition.vline",
    "body.distribution",
    "body.muscle",
    "body.neck.mass",
    "body.pecs.size",
    "body.tissue.level",
    "body.tissue.mass_smooth",
    "body.torso.lower",
    "body.torso.mass",
    "head.brow.projection",
]


def test_seed_registry_loads_nineteen_records(registry):
    # Seed set extended Nov 12, 2026: body.neck.mass (NeckMass) authored
    # per BARA_LESSONS section 6 A2; then the Muscle x Tissue set
    # (muscle/tissue/definition/distribution records) authored per
    # MUSCLE_TISSUE_MODEL.md; then body.chest.broadness (frame width)
    # per the Nov 12, 2026 chest-broadness amendment to that model.
    # Integration pass (Nov 12, 2026, INTEGRATION.md): + the bara
    # composed builds (body.build.*), + body.forearm.mass, + 49
    # generated HIMBO vocabulary records (body.himbo.*) so the spec'd
    # presets validate end to end.
    assert len(registry) == 74
    for sid in SEED_IDS:
        assert sid in registry
    for sid in ("body.build.muscle", "body.build.chest_width",
                "body.build.tissue_strongman", "body.build.bara_strongman",
                "body.forearm.mass", "body.himbo.weight_0_to_1",
                "body.himbo.lean", "body.himbo.torso_waist_size"):
        assert sid in registry


def test_chest_broadness_is_a_two_pole_frame_record(registry):
    """Broadness is a frame variable: two-pole [-1, 1] (the HIMBO
    ShoulderInc/Dec pair), study-only, with the decoded pair's QA —
    and asymmetric poles, because the source pair is (the widen field
    displaces further than the narrow field)."""
    rec = registry.get("body.chest.broadness")
    assert rec.range_min == -1.0 and rec.range_max == 1.0 and rec.default == 0.0
    assert rec.group == "body/chest"
    assert rec.licence_tier == "study-only (internal)"
    pair = rec.instances["skyrim_himbo"]["qa"]["primary_pair"]
    assert pair["positive_disp_max_m"] == pytest.approx(0.05973)
    assert pair["negative_disp_max_m"] == pytest.approx(0.03343)
    assert pair["positive_disp_max_m"] > pair["negative_disp_max_m"]
    applied, warnings = registry.clamp_value("body.chest.broadness", -1.4)
    assert applied == -1.0 and warnings[0].kind == "range"


def test_belly_record_carries_learned_qa(registry):
    rec = registry.get("body.belly.protrusion")
    # safe_max refreshed 0.85 -> 1.0 by the v5.1 record (the fold gate
    # is clean at +1 on both bases; GRAVITY_V5.md v5.1 addendum).
    assert rec.range_max == 1.0 and rec.safe_max == 1.0
    qa = rec.instances["skyrim_fatmales"]["qa"]
    assert qa["disp_max_m"] == pytest.approx(0.156057)
    assert rec.licence_tier == "study-only (internal)"
    # The hm08 instance is the gravity-coupled components form, with
    # the v5.2 contact variant registered and a per-base masculine
    # re-derivation alongside.
    comps = rec.instances["makehuman_hm08"]["components"]
    assert comps["combined"].endswith("body.belly.protrusion_v5.1.target")
    assert comps["sag"].endswith("body.belly.protrusion_sag_v3.target")
    assert comps["gamma"] == 2.0
    assert comps["variants"]["contact"].endswith(
        "body.belly.protrusion_contact_v52.target")
    assert rec.instances["makehuman_hm08"]["qa"]["flips_at_+1_body_faces"] == 0
    assert rec.instances["makehuman_hm08_masculine"]["file"].endswith(
        "masculine-base/body.belly.protrusion.target")


def test_range_clamp_above_max_warns_and_clamps(registry):
    applied, warnings = registry.clamp_value("body.belly.protrusion", 1.7)
    assert applied == 1.0
    assert len(warnings) == 1
    assert warnings[0].kind == "range"
    assert warnings[0].requested == 1.7 and warnings[0].applied == 1.0


def test_range_clamp_below_min_warns_and_clamps(registry):
    applied, warnings = registry.clamp_value("body.belly.protrusion", -2.5)
    assert applied == -1.0
    assert warnings[0].kind == "range"


def test_safe_range_excursion_warns_but_keeps_value():
    # Safe-band semantics, exercised on a synthetic record: the
    # production belly record's safe band became its full range in the
    # v5.1 refresh (safe_max 1.0), so it no longer demonstrates this.
    from core.sliders import SliderRecord

    rec = SliderRecord.from_dict({
        "id": "test.safe_band", "label": "Safe band", "group": "test",
        "range": {"min": -1.0, "max": 1.0, "default": 0.0,
                  "safe_min": -0.5, "safe_max": 0.85},
    })
    applied, warnings = rec.clamp(0.9)
    assert applied == 0.9
    assert len(warnings) == 1 and warnings[0].kind == "safe"


def test_belly_value_inside_v51_safe_band_is_silent(registry):
    applied, warnings = registry.clamp_value("body.belly.protrusion", 0.9)
    assert applied == 0.9 and warnings == []


def test_in_range_value_is_silent(registry):
    applied, warnings = registry.clamp_value("body.belly.protrusion", 0.5)
    assert applied == 0.5 and warnings == []


def test_brow_index_scale_clamps_at_150(registry):
    applied, warnings = registry.clamp_value("head.brow.projection", 500.0)
    assert applied == 150.0 and warnings[0].kind == "range"


def test_unknown_slider_lookup_raises_named_error(registry):
    with pytest.raises(UnknownSliderError, match="body.nope"):
        registry.get("body.nope")


def test_character_validate_reports_unknown_and_clamps(registry):
    char = Character(sliders={"body.belly.protrusion": 5.0, "body.nope": 1.0})
    report = char.validate(registry)
    assert not report.ok
    assert any("body.nope" in e for e in report.errors)
    # Known slider was clamped in place, with the warning returned.
    assert char.sliders["body.belly.protrusion"] == 1.0
    assert any(w.kind == "range" for w in report.warnings)
    # The unknown id is NOT silently dropped.
    assert char.sliders["body.nope"] == 1.0


def test_character_validate_clean_character(registry):
    char = Character(sliders={"body.chubby": 0.4, "head.brow.projection": 100.0})
    report = char.validate(registry)
    assert report.ok and report.warnings == []


def test_filename_id_mismatch_rejected(tmp_path):
    bad = tmp_path / "wrong.name.json"
    bad.write_text((SLIDERS_DIR / "body.chubby.json").read_text())
    with pytest.raises(SliderRecordError, match="does not match"):
        SliderRegistry.from_folder(tmp_path)
