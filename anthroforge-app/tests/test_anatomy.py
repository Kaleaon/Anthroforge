"""Regression tests for the plan-aware anatomy part contract."""

import json

import pytest

from core.anatomy import (
    AnatomyLibrary,
    BODY_PLANS,
    GENITAL_CHAIN,
    validate_character_anatomy,
    validate_part_manifest,
)


def genital_manifest():
    return {
        "format": "anthroforge.part",
        "version": 1,
        "id": "anatomy.genital.canid.v1",
        "label": "Canid anatomy module",
        "kind": "anatomy",
        "adult_only": True,
        "sockets": ["pelvis.genital"],
        "meshes": {"lod0": "mesh.glb"},
        "skin": {
            "mode": "own-weights",
            "bones": ["Pelvis", "GenBase", "GenScrot", *GENITAL_CHAIN[1:]],
        },
        "plan_fit": {
            "plans": sorted(BODY_PLANS),
            "socket_by_plan": {plan: "pelvis.genital" for plan in BODY_PLANS},
            "excluded_plans": [],
        },
        "function": {
            "genital": {
                "morph_channels": [
                    "length", "girth", "base_volume", "curve", "lift", "scrotal_volume"
                ],
                "motion": {
                    "chain": list(GENITAL_CHAIN),
                    "collision_profile": "pelvis.genital.clearance.v1",
                },
            }
        },
    }


def write_library(tmp_path, manifest=None):
    part_dir = tmp_path / "canid"
    part_dir.mkdir()
    (part_dir / "mesh.glb").write_bytes(b"test mesh placeholder")
    data = manifest or genital_manifest()
    (part_dir / "part.json").write_text(json.dumps(data), encoding="utf-8")
    return AnatomyLibrary.from_folder(tmp_path)


def test_valid_genital_manifest_passes_contract():
    assert validate_part_manifest(genital_manifest()) == []


def test_genital_manifest_requires_adult_flag_and_complete_rig():
    data = genital_manifest()
    data["adult_only"] = False
    data["skin"]["bones"].remove("Gen03")
    errors = validate_part_manifest(data)
    assert any("adult_only=true" in error for error in errors)
    assert any("Gen03" in error for error in errors)


def test_genital_manifest_requires_contiguous_motion_chain():
    data = genital_manifest()
    data["function"]["genital"]["motion"]["chain"] = ["GenBase", "Gen01", "Gen03"]
    errors = validate_part_manifest(data)
    assert any("motion.chain" in error for error in errors)


def test_manifest_rejects_mesh_path_escape():
    data = genital_manifest()
    data["meshes"]["lod0"] = "../../outside.glb"
    assert any("stay inside" in error for error in validate_part_manifest(data))


def test_library_requires_real_lod0_asset(tmp_path):
    part_dir = tmp_path / "canid"
    part_dir.mkdir()
    (part_dir / "part.json").write_text(json.dumps(genital_manifest()), encoding="utf-8")
    with pytest.raises(ValueError, match="asset does not exist"):
        AnatomyLibrary.from_folder(tmp_path, require_mesh_files=True)


def test_equipping_genital_module_is_adult_gated(tmp_path):
    library = write_library(tmp_path)
    parts = [{"slot": "pelvis.genital", "part": "anatomy.genital.canid.v1"}]
    blocked = validate_character_anatomy(parts, library, adult_content_enabled=False)
    assert blocked.ok is False
    assert any("adult-only" in error for error in blocked.errors)

    allowed = validate_character_anatomy(parts, library, adult_content_enabled=True)
    assert allowed.ok is True
    assert allowed.resolved_parts[0]["body_plan"] == "plan.biped"


def test_part_must_be_fitted_for_selected_body_plan(tmp_path):
    manifest = genital_manifest()
    manifest["plan_fit"]["plans"] = ["plan.biped"]
    manifest["plan_fit"]["socket_by_plan"] = {"plan.biped": "pelvis.genital"}
    library = write_library(tmp_path, manifest)
    report = validate_character_anatomy(
        [{"slot": "pelvis.genital", "part": "anatomy.genital.canid.v1"}],
        library,
        body_plan="plan.naga",
        adult_content_enabled=True,
    )
    assert report.ok is False
    assert any("not fitted" in error for error in report.errors)


def test_plan_specific_socket_is_enforced(tmp_path):
    manifest = genital_manifest()
    manifest["plan_fit"]["socket_by_plan"]["plan.naga"] = "pelvis.serpent"
    library = write_library(tmp_path, manifest)
    report = validate_character_anatomy(
        [{"slot": "pelvis.genital", "part": "anatomy.genital.canid.v1"}],
        library,
        body_plan="plan.naga",
        adult_content_enabled=True,
    )
    assert report.ok is False
    assert any("expects socket" in error for error in report.errors)


def test_only_one_module_can_occupy_genital_socket(tmp_path):
    library = write_library(tmp_path)
    part = {"slot": "pelvis.genital", "part": "anatomy.genital.canid.v1"}
    report = validate_character_anatomy(
        [part, part], library, adult_content_enabled=True
    )
    assert report.ok is False
    assert any("only one part" in error for error in report.errors)


def test_unknown_genital_module_is_not_silently_ignored():
    report = validate_character_anatomy(
        [{"slot": "pelvis.genital", "part": "missing.module"}],
        AnatomyLibrary(),
        adult_content_enabled=True,
    )
    assert report.ok is False
    assert any("unknown anatomy part" in error for error in report.errors)


def test_manifest_rejects_unknown_or_malformed_body_plans():
    data = genital_manifest()
    data["plan_fit"]["plans"] = ["plan.biped", {"not": "a plan"}]
    errors = validate_part_manifest(data)
    assert any("non-empty strings" in error for error in errors)
