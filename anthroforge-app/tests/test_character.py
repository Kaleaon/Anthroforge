"""Character record: file round-trip + structural validation."""

import pytest

from core.character import Character
from core.errors import SchemaError


def sample_character() -> Character:
    return Character(
        name="Test Orc",
        base={"body": "af_body_neutral_v1", "head": "af_head_neutral_v2"},
        sliders={"body.belly.protrusion": 0.62, "head.brow.projection": 135.0},
        species_preset={"id": "preset.orc_bara_strongman", "weight": 1.0,
                        "residual_edits": {}},
        parts=[{"slot": "teeth.arcade", "part": "teeth_arcade_universal",
                "params": {"canine": 80, "tusk_lower": 80}}],
        fur={"profile": None, "overrides": {}},
        materials={"skin": {"palette": "orc.classic_green", "base": "#6B8E3D"}},
        identity={"notes": "round-trip test subject", "family": None},
        provenance={"created_by": "pytest", "app_version": "0.1.0"},
        id="chr_00000000000000000000000001",
    )


def test_file_round_trip_is_lossless(tmp_path):
    char = sample_character()
    path = char.save(tmp_path / "test_orc.afchar.json")
    loaded = Character.load(path)
    assert loaded.to_dict() == char.to_dict()
    assert loaded.sliders == {"body.belly.protrusion": 0.62,
                              "head.brow.projection": 135.0}


def test_dict_round_trip():
    char = sample_character()
    assert Character.from_dict(char.to_dict()).to_dict() == char.to_dict()


def test_defaults_fill_absent_sections():
    char = Character.from_dict({"format": "anthroforge.character", "version": 1})
    assert char.name == "Unnamed"
    assert char.base == {"body": "af_body_neutral_v1", "head": "af_head_neutral_v2"}
    assert char.sliders == {}
    assert char.id.startswith("chr_")


def test_bad_format_rejected_by_name():
    with pytest.raises(SchemaError, match="'format'"):
        Character.from_dict({"format": "something.else", "version": 1})


def test_unsupported_version_rejected_by_name():
    with pytest.raises(SchemaError, match="'version'.*99"):
        Character.from_dict({"format": "anthroforge.character", "version": 99})


def test_unknown_top_level_field_rejected_by_name():
    with pytest.raises(SchemaError, match="bogus_field"):
        Character.from_dict({"format": "anthroforge.character", "version": 1,
                             "bogus_field": True})


def test_non_numeric_slider_value_rejected_by_name():
    with pytest.raises(SchemaError, match=r"sliders\.body\.belly\.protrusion"):
        Character.from_dict({"format": "anthroforge.character", "version": 1,
                             "sliders": {"body.belly.protrusion": "lots"}})


def test_part_entry_missing_slot_rejected():
    with pytest.raises(SchemaError, match=r"parts\[0\]\.slot"):
        Character.from_dict({"format": "anthroforge.character", "version": 1,
                             "parts": [{"part": "teeth_arcade_universal"}]})
