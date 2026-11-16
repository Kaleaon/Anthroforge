#!/usr/bin/env python3
"""Convert an AnthroForge skinned GLB into a Unity/VRChat-friendly FBX.

Run with Blender:
  blender --background --python export_unity_fbx.py -- --input avatar.glb --output avatar_vrchat.fbx --profile vrchat

This converts the existing skinned GLB; it does not fabricate missing
facial expressions, eye-look bones, PhysBones, colliders, or Unity SDK setup.
Those requirements are reported explicitly in the companion JSON.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
import bpy

BONE_RENAME = {
    "Root": "Root", "Pelvis": "Hips", "Spine1": "Spine", "Chest": "Chest",
    "Neck": "Neck", "Head": "Head", "Jaw": "Jaw",
    "Shoulder_L": "LeftUpperArm", "Elbow_L": "LeftLowerArm", "Wrist_L": "LeftHand",
    "Shoulder_R": "RightUpperArm", "Elbow_R": "RightLowerArm", "Wrist_R": "RightHand",
    "Hip_L": "LeftUpperLeg", "Knee_L": "LeftLowerLeg", "Ankle_L": "LeftFoot", "Foot_L": "LeftToes",
    "Hip_R": "RightUpperLeg", "Knee_R": "RightLowerLeg", "Ankle_R": "RightFoot", "Foot_R": "RightToes",
}
REQUIRED_HUMANOID = (
    "Hips", "Spine", "Head", "LeftUpperArm", "LeftLowerArm", "LeftHand",
    "RightUpperArm", "RightLowerArm", "RightHand", "LeftUpperLeg", "LeftLowerLeg",
    "LeftFoot", "RightUpperLeg", "RightLowerLeg", "RightFoot",
)

def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--profile", choices=("vrchat", "unity", "unreal"), default="vrchat")
    return p.parse_args(argv)

def main():
    args = parse_args()
    source, output = args.input.expanduser().resolve(), args.output.expanduser().resolve()
    if not source.is_file():
        raise RuntimeError(f"Input GLB does not exist: {source}")
    if source == output:
        raise RuntimeError("Input and output paths must be different.")
    output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(source))
    imported = list(bpy.context.scene.objects)
    armatures = [o for o in imported if o.type == "ARMATURE"]
    meshes = [o for o in imported if o.type == "MESH"]
    if len(armatures) != 1:
        raise RuntimeError(f"Expected exactly one armature in GLB; found {len(armatures)}.")
    if not meshes:
        raise RuntimeError("GLB contains no mesh objects.")
    armature = armatures[0]
    source_names = {b.name for b in armature.data.bones}
    missing = sorted(set(BONE_RENAME) - source_names)
    if missing:
        raise RuntimeError("GLB is missing expected AnthroForge rig bones: " + ", ".join(missing))
    # Rename matching vertex groups along with their deform bones.
    for obj in meshes:
        for old, new in BONE_RENAME.items():
            group = obj.vertex_groups.get(old)
            if group:
                group.name = new
    # Temporary names prevent collisions during the rename pass.
    for bone in armature.data.bones:
        if bone.name in BONE_RENAME:
            bone.name = "__AF_TMP__" + bone.name
    for old, new in BONE_RENAME.items():
        bone = armature.data.bones.get("__AF_TMP__" + old)
        if bone:
            bone.name = new
    final_names = {b.name for b in armature.data.bones}
    missing_humanoid = sorted(set(REQUIRED_HUMANOID) - final_names)
    if missing_humanoid:
        raise RuntimeError("Unity Humanoid mapping incomplete: " + ", ".join(missing_humanoid))
    bpy.ops.object.select_all(action="DESELECT")
    for obj in [armature, *meshes]:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = armature
    bpy.ops.export_scene.fbx(
        filepath=str(output), use_selection=True, object_types={"ARMATURE", "MESH"},
        apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL",
        axis_forward="-Z", axis_up="Y", use_space_transform=True,
        bake_space_transform=False, use_mesh_modifiers=True,
        mesh_smooth_type="FACE", use_tspace=True, add_leaf_bones=False,
        primary_bone_axis="Y", secondary_bone_axis="X",
        use_armature_deform_only=True, armature_nodetype="NULL",
        bake_anim=False, path_mode="COPY", embed_textures=True,
    )
    report = {
        "schema": "anthroforge.avatar-export/v1", "profile": args.profile,
        "source": str(source), "output": str(output), "format": "FBX",
        "mesh_objects": len(meshes), "armature": armature.name,
        "bone_count": len(final_names), "required_humanoid_bones": list(REQUIRED_HUMANOID),
        "missing_humanoid_bones": missing_humanoid, "mapped_bones": BONE_RENAME,
        "status": "fbx_written_unity_import_validation_required",
        "not_provided": ([
            "eye-look bones and constraints", "viseme blendshapes and expression menu",
            "blink and facial expression blendshapes", "VRChat PhysBones and colliders",
            "Unity Humanoid Avatar configuration", "VRChat SDK build and performance validation",
        ] if args.profile == "vrchat" else ["target-engine import and retarget validation"]),
        "warning": "FBX generation succeeded; this is not proof of a VRChat-upload-ready avatar.",
    }
    report_path = output.with_suffix(output.suffix + ".avatar-report.json")
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "report": str(report_path), "status": report["status"]}))

if __name__ == "__main__":
    main()
