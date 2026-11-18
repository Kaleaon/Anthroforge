"""Validate the reference-informed Kaleaon blockout profile and Blender script."""
from __future__ import annotations
import ast, json, math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "kaleaon.v1.json"
BUILDER = ROOT / "scripts" / "build_kaleaon_blockout.py"

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
            value = values.get(key)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
                raise ValueError(f"{section}.{key} must be a finite positive number")
    if not isinstance(data.get("status"), str) or "provisional" not in data["status"]:
        raise ValueError("profile status must disclose provisional proportions")
    ast.parse(BUILDER.read_text(encoding="utf-8"), filename=str(BUILDER))
    return {"profiles": 1, "dimension_sections": len(required), "blender_scripts": 1}

if __name__ == "__main__":
    print("Kaleaon profile validation passed:", validate())
