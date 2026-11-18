"""Strict structural validation for species and adult anatomy profile data."""
from __future__ import annotations

import ast
import json
import math
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_FAMILIES = {"canid", "feline", "equine", "draconic", "avian", "serpentine"}
PLANS = {"plan.biped", "plan.quadruped_feral", "plan.quadruped_taur", "plan.naga"}
REQUIRED = {
    "head": {"length", "width", "height", "muzzle_length", "ear"},
    "torso": {"shoulder_width", "waist_width", "hip_width", "chest_depth", "pelvis_depth"},
    "limbs": {"arm_girth", "thigh_girth", "shin_girth", "digitigrade", "paw_scale"},
    "tail": {"enabled", "length", "girth", "curve"},
}


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON numeric constant is not allowed: {value}")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(
            path.read_text(encoding="utf-8"),
            parse_constant=_reject_constant,
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"{path}: cannot read valid JSON ({exc})") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{path}: document root must be an object")
    return data


def _finite_tree(value: Any, context: str) -> None:
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return
    if isinstance(value, (int, float)):
        if not math.isfinite(value):
            raise ValueError(f"{context}: numeric values must be finite")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _finite_tree(item, f"{context}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            _finite_tree(item, f"{context}.{key}")
        return
    raise ValueError(f"{context}: unsupported value type {type(value).__name__}")


def _positive_number(value: Any, context: str, *, allow_zero: bool = False) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{context}: expected a number")
    if not math.isfinite(value) or (value < 0 if allow_zero else value <= 0):
        qualifier = "non-negative" if allow_zero else "positive"
        raise ValueError(f"{context}: expected a finite {qualifier} number")


def validate(root: Path = ROOT) -> dict[str, int]:
    root = Path(root)
    species_path = root / "species_profiles.v1.json"
    species = _read_json(species_path)
    _finite_tree(species, "species profiles")
    if species.get("schema") != "anthroforge.species-mesh-profiles":
        raise ValueError("species profile schema identifier is invalid")
    if species.get("version") != 1 or species.get("units") != "metres":
        raise ValueError("species profile version must be 1 and units must be metres")
    profiles = species.get("profiles")
    if not isinstance(profiles, list) or not profiles:
        raise ValueError("species profiles must be a non-empty list")

    ids: set[str] = set()
    families: set[str] = set()
    for index, profile in enumerate(profiles):
        context = f"species profiles[{index}]"
        if not isinstance(profile, dict):
            raise ValueError(f"{context}: expected an object")
        profile_id = profile.get("id")
        if not isinstance(profile_id, str) or not profile_id:
            raise ValueError(f"{context}.id must be a non-empty string")
        if profile_id in ids:
            raise ValueError(f"duplicate species profile id: {profile_id}")
        ids.add(profile_id)

        family = profile.get("family")
        if family not in ALLOWED_FAMILIES:
            raise ValueError(f"{profile_id}: unknown family {family!r}")
        families.add(family)
        if profile.get("body_plan") not in PLANS:
            raise ValueError(f"{profile_id}: unknown body plan")
        supported = profile.get("supported_plans")
        if not isinstance(supported, list) or not supported or len(set(supported)) != len(supported):
            raise ValueError(f"{profile_id}: supported_plans must be a non-empty unique list")
        if not set(supported) <= PLANS or profile["body_plan"] not in supported:
            raise ValueError(f"{profile_id}: supported_plans contains an unknown plan or omits body_plan")
        if (family == "serpentine") != ("plan.naga" in supported):
            raise ValueError(f"{profile_id}: naga support must match the serpentine family")

        for group, keys in REQUIRED.items():
            section = profile.get(group)
            if not isinstance(section, dict):
                raise ValueError(f"{profile_id}: {group} must be an object")
            missing = keys - set(section)
            if missing:
                raise ValueError(f"{profile_id}: missing {group} keys {sorted(missing)}")
        for group in ("head", "torso"):
            for key, value in profile[group].items():
                if key != "ear":
                    _positive_number(value, f"{profile_id}.{group}.{key}")
        for key in ("arm_girth", "thigh_girth", "shin_girth"):
            _positive_number(profile["limbs"][key], f"{profile_id}.limbs.{key}")
        _positive_number(profile["limbs"]["paw_scale"], f"{profile_id}.limbs.paw_scale", allow_zero=True)
        if not isinstance(profile["limbs"]["digitigrade"], bool):
            raise ValueError(f"{profile_id}.limbs.digitigrade must be boolean")
        if not isinstance(profile["tail"]["enabled"], bool):
            raise ValueError(f"{profile_id}.tail.enabled must be boolean")
        for key in ("length", "girth"):
            _positive_number(profile["tail"][key], f"{profile_id}.tail.{key}")
        _positive_number(profile["tail"]["curve"], f"{profile_id}.tail.curve", allow_zero=True)

    if families != ALLOWED_FAMILIES:
        raise ValueError(f"missing species families: {sorted(ALLOWED_FAMILIES - families)}")

    anatomy_path = root / "anatomy_profiles.v1.json"
    anatomy = _read_json(anatomy_path)
    _finite_tree(anatomy, "adult anatomy profiles")
    if anatomy.get("schema") != "anthroforge.adult-anatomy-profiles" or anatomy.get("version") != 1:
        raise ValueError("adult anatomy schema identifier/version is invalid")
    scale = anatomy.get("scale")
    if not isinstance(scale, dict):
        raise ValueError("adult anatomy scale must be an object")
    minimum, maximum, default = scale.get("minimum"), scale.get("maximum"), scale.get("default")
    for key, value in (("minimum", minimum), ("maximum", maximum), ("default", default)):
        _positive_number(value, f"adult anatomy scale.{key}")
    if not minimum <= default <= maximum:
        raise ValueError("adult anatomy scale must satisfy minimum <= default <= maximum")

    anatomy_profiles = anatomy.get("profiles")
    if not isinstance(anatomy_profiles, dict) or not anatomy_profiles:
        raise ValueError("adult anatomy profiles must be a non-empty object")
    for key, profile in anatomy_profiles.items():
        context = f"adult anatomy profile {key}"
        if not isinstance(profile, dict) or profile.get("id") != key:
            raise ValueError(f"{context}: profile id must match its key")
        if profile.get("adult_only") is not True:
            raise ValueError(f"{context}: adult_only must be true")
        count = profile.get("default_member_count")
        if not isinstance(count, int) or isinstance(count, bool) or not 1 <= count <= 4:
            raise ValueError(f"{context}: default_member_count must be an integer from 1 to 4")
        compatible_families = profile.get("compatible_families")
        compatible_plans = profile.get("compatible_plans")
        if not isinstance(compatible_families, list) or not compatible_families:
            raise ValueError(f"{context}: compatible_families must be a non-empty list")
        if not set(compatible_families) <= ALLOWED_FAMILIES:
            raise ValueError(f"{context}: contains an unknown family")
        if not isinstance(compatible_plans, list) or not compatible_plans:
            raise ValueError(f"{context}: compatible_plans must be a non-empty list")
        if not set(compatible_plans) <= PLANS:
            raise ValueError(f"{context}: contains an unknown body plan")
        dims = profile.get("dimensions_m")
        if not isinstance(dims, dict):
            raise ValueError(f"{context}: dimensions_m must be an object")
        for name in ("length", "girth", "sac_width", "sac_height"):
            _positive_number(dims.get(name), f"{context}.dimensions_m.{name}")
        stations = profile.get("shape", {}).get("stations")
        if not isinstance(stations, list) or len(stations) < 3:
            raise ValueError(f"{context}: shape.stations must contain at least three entries")
        ts = []
        for index, station in enumerate(stations):
            if not isinstance(station, dict):
                raise ValueError(f"{context}: station {index} must be an object")
            t = station.get("t")
            radius = station.get("radius")
            if isinstance(t, bool) or not isinstance(t, (int, float)) or not 0 <= t <= 1:
                raise ValueError(f"{context}: station {index} t must be within [0, 1]")
            _positive_number(radius, f"{context}: station {index} radius")
            ts.append(t)
        if ts[0] != 0 or ts[-1] != 1 or any(a >= b for a, b in zip(ts, ts[1:])):
            raise ValueError(f"{context}: station t values must increase strictly from 0 to 1")

    scripts = list((root / "scripts").glob("*.py"))
    for path in scripts:
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError) as exc:
            raise ValueError(f"{path}: Blender script syntax error: {exc}") from exc

    return {
        "species_profiles": len(ids),
        "species_families": len(families),
        "anatomy_profiles": len(anatomy_profiles),
        "blender_scripts": len(scripts),
    }


if __name__ == "__main__":
    try:
        summary = validate()
        print(
            "OK: "
            + str(summary["species_profiles"])
            + " species profiles, "
            + str(summary["species_families"])
            + " families, "
            + str(summary["anatomy_profiles"])
            + " adult anatomy profiles, "
            + str(summary["blender_scripts"])
            + " Blender scripts parse"
        )
    except Exception as exc:
        print("FAIL:", exc, file=sys.stderr)
        sys.exit(1)
