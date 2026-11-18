"""Validate Kaleaon's editable profile and modular Blender mesh builder."""
from __future__ import annotations
import ast, json, math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "kaleaon.v1.json"
BUILDER = ROOT / "scripts" / "build_kaleaon_blockout.py"
BLENDER_SMOKE_TEST = ROOT / "scripts" / "verify_kaleaon_blender_output.py"


def positive_number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
        raise ValueError(f"{label} must be a finite positive number")


def validate() -> dict[str, int]:
    data = json.loads(PROFILE.read_text(encoding="utf-8"))
    if data.get("schema") != "anthroforge.sona-blockout-profile" or data.get("version") != 1:
        raise ValueError("unsupported Kaleaon profile schema/version")
    if data.get("id") != "sona.kaleaon":
        raise ValueError("profile id must be sona.kaleaon")
    if data.get("coordinate_system") != {"x": "character right", "y": "front", "z": "up"}:
        raise ValueError("coordinate system must be x-right, y-front, z-up")

    dims = data.get("blockout_dimensions_m")
    if not isinstance(dims, dict):
        raise ValueError("blockout_dimensions_m must be an object")
    height = dims.get("overall_height")
    if isinstance(height, bool) or not isinstance(height, (int, float)) or not math.isfinite(height) or abs(height - 2.1336) > 1e-6:
        raise ValueError("overall_height must match the user-selected 7 ft target (2.1336 m)")
    required = {
        "head": ("width", "length", "height", "muzzle_length", "ear_height"),
        "torso": ("shoulder_width", "waist_width", "hip_width", "chest_depth", "pelvis_depth"),
        "limbs": ("upper_arm_girth", "forearm_girth", "thigh_girth", "shin_girth", "paw_scale"),
        "tail": ("length", "base_girth"),
    }
    for section, keys in required.items():
        values = dims.get(section)
        if not isinstance(values, dict):
            raise ValueError(f"{section} dimensions must be an object")
        for key in keys:
            positive_number(values.get(key), f"{section}.{key}")

    anatomy = data.get("anatomy_components")
    if not isinstance(anatomy, dict):
        raise ValueError("anatomy_components must be an object")
    shafts, sac, teats = anatomy.get("genitalia", {}), anatomy.get("sac", {}), anatomy.get("teats", {})
    if shafts.get("count") != 4 or teats.get("count") != 4:
        raise ValueError("anatomy module requires four independent shafts and four individual teats")
    for key in ("length_m", "radius_x_m", "radius_y_m", "spacing_x_m", "spacing_z_m"):
        positive_number(shafts.get(key), f"anatomy_components.genitalia.{key}")
    for key in ("width_m", "depth_m", "height_m"):
        positive_number(sac.get(key), f"anatomy_components.sac.{key}")
    for key in ("radius_x_m", "radius_y_m", "radius_z_m"):
        positive_number(teats.get(key), f"anatomy_components.teats.{key}")
    positions = teats.get("positions_m")
    if not isinstance(positions, list) or len(positions) != 4 or any(
        not isinstance(pair, list) or len(pair) != 2 or any(
            isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
            for v in pair
        ) for pair in positions
    ):
        raise ValueError("teats.positions_m must contain four finite [x,z] pairs")
    if "separate" not in anatomy.get("assembly_policy", ""):
        raise ValueError("anatomy assembly policy must preserve separate components")

    if not isinstance(data.get("status"), str) or "provisional" not in data["status"]:
        raise ValueError("profile status must disclose provisional proportions")
    if data.get("scale_anchor", {}).get("source") != "user estimate: approximately 7 ft":
        raise ValueError("scale anchor must disclose the user-estimated 7 ft target")

    source = BUILDER.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(BUILDER))
    smoke_source = BLENDER_SMOKE_TEST.read_text(encoding="utf-8")
    ast.parse(smoke_source, filename=str(BLENDER_SMOKE_TEST))
    functions = {node.name: node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    for name in ("make_rounded_component", "build_lower_anatomy", "fuse_coat_surface"):
        if name not in functions:
            raise ValueError(f"Blender builder is missing required function: {name}")
    anatomy_source = ast.get_source_segment(source, functions["build_lower_anatomy"]) or ""
    if "make_rounded_component(" not in anatomy_source:
        raise ValueError("anatomy builder must create parametric closed meshes")
    if "ellipsoid(" in anatomy_source:
        raise ValueError("anatomy builder must not use primitive ellipsoid placeholders")
    return {
        "profiles": 1,
        "dimension_sections": len(required),
        "anatomy_mesh_families": 3,
        "independent_anatomy_objects": 9,
        "blender_scripts": 2,
    }


if __name__ == "__main__":
    print("Kaleaon profile validation passed:", validate())
