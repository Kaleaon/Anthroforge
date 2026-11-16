"""Static contract tests for the Blender Unity/VRChat FBX sidecar.

The script runs inside Blender's Python, so the normal pytest environment
checks its syntax and the mapping contract without importing bpy.
"""
import ast
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "blender" / "export_unity_fbx.py"


def _constants():
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    found = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in {"BONE_RENAME", "REQUIRED_HUMANOID"}:
                    found[target.id] = ast.literal_eval(node.value)
    return found


def test_blender_export_script_is_valid_python():
    ast.parse(SCRIPT.read_text(encoding="utf-8"))


def test_humanoid_required_bones_have_unique_source_bones():
    values = _constants()
    mapping = values["BONE_RENAME"]
    required = values["REQUIRED_HUMANOID"]
    assert set(required).issubset(set(mapping.values()))
    # Unity Humanoid requires a unique transform for each mapped body bone.
    required_sources = [source for source, target in mapping.items() if target in required]
    assert len(required_sources) == len(set(required_sources))


def test_vrchat_export_does_not_claim_sdk_readiness():
    source = SCRIPT.read_text(encoding="utf-8")
    assert "fbx_written_unity_import_validation_required" in source
    assert "VRChat SDK build and performance validation" in source
