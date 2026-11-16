"""Build editable species body blockouts for AnthroForge.

Run:
  blender --background --python build_species_blockouts.py -- \
    --profile species.canid.wolf --output ./out

Outputs one .blend and one .glb per selected profile. These are greybox
construction meshes for fit/rig authoring, not final production topology.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
PROFILE_FILE = ROOT / "species_profiles.v1.json"


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--profile", default="all")
    p.add_argument("--output", default="./species-blockouts")
    return p.parse_args(argv)


def clear_scene():
    bpy.ops.object.select_all(action="SELECT)
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials):
        for block in list(datablocks):
            if block.users == 0:
                datablocks.remove(block)


def material(name, color):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1.0)
    return m


def make_loft(name, start, end, r0, r1, material_slot, sides=16, bulge=0.0):
    """Elliptical loft between two points; r values are (side, depth)."""
    a, b = Vector(start), Vector(end)
    axis = (b - a).normalized()
    helper = Vector((0, 0, 1)) if abs(axis.z) < 0.92 else Vector((0, 1, 0))
    u = axis.cross(helper).normalized()
    v = axis.cross(u).normalized()
    verts, faces = [], []
    rings = 12
    for j in range(rings):
        t = j / (rings - 1)
        center = a.lerp(b, t)
        taper = (1.0 - t) * r0[0] + t * r1[0]
        depth = (1.0 - t) * r0[1] + t * r1[1]
        envelope = 1.0 + bulge * math.sin(math.pi * t)
        for i in range(sides):
            ang = 2.0 * math.pi * i / sides
            p = center + u * (math.cos(ang) * taper * envelope) + v * (math.sin(ang) * depth * envelope)
            verts.append(tuple(p))
    for j in range(rings - 1):
        for i in range(sides):
            a0 = j * sides + i
            a1 = j * sides + (i + 1) % sides
            b0, b1 = a0 + sides, a1 + sides
            faces.append((a0, a1, b1, b0))
    faces.append(tuple(range(sides - 1, -1, -1)))
    faces.append(tuple((rings - 1) * sides + i for i in range(sides)))
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(material_slot)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    for poly in mesh.polygons:
        poly.use_smooth = True
    return obj


def ellipsoid(name, loc, scale, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=16, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    o.data.materials.append(mat)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def build_profile(profile, out_dir):
    clear_scene()
    neutral = material("AF_Blockout_Neutral", (0.48, 0.49, 0.52))
    accents = material("AF_Blockout_Secondary", (0.31, 0.33, 0.37))
    ident = profile["id"].replace(".", "_")
    head, torso, limbs, tail = profile["head"], profile["torso"], profile["limbs"], profile["tail"]

    # Torso: lower pelvis to shoulder girdle, one continuous loft.
    make_loft(ident + "_Torso", (0, 0, 0.72), (0, 0, 1.48),
              (torso["hip_width"] / 2, torso["pelvis_depth"] / 2),
              (torso["shoulder_width"] / 2, torso["chest_depth"] / 2),
              neutral, sides=24, bulge=0.12)
    ellipsoid(ident + "_PelvisVolume", (0, 0, 0.79),
              (torso["hip_width"] * 0.48, torso["pelvis_depth"] * 0.48, 0.24), neutral)
    ellipsoid(ident + "_ChestVolume", (0, 0, 1.34),
              (torso["shoulder_width"] * 0.51, torso["chest_depth"] * 0.52, 0.27), neutral)
    make_loft(ident + "_Neck", (0, 0, 1.42), (0, 0, 1.70),
              (0.12, 0.12), (0.105, 0.11), neutral, sides=16, bulge=0.08)
    ellipsoid(ident + "_Skull", (0, 0, 1.79),
              (head["width"] / 2, head["length"] / 2, head["height"] / 2), neutral)
    if head["muzzle_length"] > 0:
        ellipsoid(ident + "_Muzzle", (0, head["length"] * 0.42, 1.75),
                  (head["width"] * 0.30, head["muzzle_length"] / 2, head["height"] * 0.22), accents)

    # Ears are separate edit-ready objects, not fused into the skull.
    ear_scale = 0.075 if head["ear"] in ("rounded", "species") else 0.11
    for side, label in ((-1, "L"), (1, "R")):
        ellipsoid(ident + "_Ear_" + label,
                  (side * head["width"] * 0.48, -0.005, 1.91),
                  (ear_scale, 0.045, 0.11 if head["ear"] != "rounded" else 0.075), accents)

    # Arms and hands; attachment-ready shoulder/elbow/wrist stations.
    for side, label in ((-1, "L"), (1, "R")):
        x = side * (torso["shoulder_width"] * 0.58)
        make_loft(ident + "_UpperArm_" + label, (side * 0.22, 0, 1.40),
                  (x, 0.015, 1.00), (limbs["arm_girth"], limbs["arm_girth"] * 0.9),
                  (limbs["arm_girth"] * 0.78, limbs["arm_girth"] * 0.72), neutral, bulge=0.12)
        make_loft(ident + "_Forearm_" + label, (x, 0.015, 1.00),
                  (side * (x + 0.015), 0.055, 0.69),
                  (limbs["arm_girth"] * 0.78, limbs["arm_girth"] * 0.72),
                  (limbs["arm_girth"] * 0.58, limbs["arm_girth"] * 0.55), neutral)
        ellipsoid(ident + "_Hand_" + label, (side * (x + 0.015), 0.075, 0.64),
                  (0.075, 0.10, 0.11), accents)

        # Leg modules are independent objects for later authored rig/weights.
        hip_x = side * torso["hip_width"] * 0.25
        knee_z = 0.40 if limbs["digitigrade"] else 0.43
        ankle_z = 0.13 if limbs["digitigrade"] else 0.08
        make_loft(ident + "_Thigh_" + label, (hip_x, 0, 0.83),
                  (hip_x, 0.015, knee_z),
                  (limbs["thigh_girth"], limbs["thigh_girth"] * 0.85),
                  (limbs["thigh_girth"] * 0.72, limbs["thigh_girth"] * 0.68), neutral, bulge=0.16)
        make_loft(ident + "_Shin_" + label, (hip_x, 0.015, knee_z),
                  (hip_x, -0.025 if limbs["digitigrade"] else 0, ankle_z),
                  (limbs["shin_girth"], limbs["shin_girth"] * 0.88),
                  (limbs["shin_girth"] * 0.62, limbs["shin_girth"] * 0.58), neutral)
        foot_y = 0.08
        ellipsoid(ident + "_Paw_" + label, (hip_x, foot_y, 0.055),
                  (0.075 * limbs["paw_scale"], 0.13 * limbs["paw_scale"], 0.055), accents)

    # Tail: segmented lofts with an editable chain of named objects.
    if tail["enabled"]:
        count = 7
        points = []
        for i in range(count):
            t = i / (count - 1)
            points.append((0, -0.10 - tail["length"] * t,
                           0.84 - tail["curve"] * math.sin(math.pi * t) + 0.08 * t))
        for i in range(count - 1):
            radius = tail["girth"] * (1.0 - 0.78 * i / (count - 1))
            make_loft(ident + "_TailSeg_" + str(i + 1), points[i], points[i + 1],
                      (radius, radius), (radius * 0.86, radius * 0.86),
                      neutral, sides=12)

    # Non-destructive metadata for later authoring tools.
    bpy.context.scene["anthroforge_species_id"] = profile["id"]
    bpy.context.scene["anthroforge_body_plan"] = profile["body_plan"]
    bpy.context.scene["anthroforge_mesh_stage"] = "greybox_blockout_unrigged"
    bpy.context.scene["anthroforge_profile_json"] = json.dumps(profile, sort_keys=True)

    out_dir.mkdir(parents=True, exist_ok=True)
    blend_path = out_dir / (ident + "_blockout.blend")
    glb_path = out_dir / (ident + "_blockout.glb")
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    bpy.ops.export_scene.gltf(filepath=str(glb_path), export_format="GLB", export_apply=False)
    return blend_path, glb_path


def main():
    args = parse_args()
    data = json.loads(PROFILE_FILE.read_text(encoding="utf-8"))
    profiles = data["profiles"]
    if args.profile != "all":
        profiles = [p for p in profiles if p["id"] == args.profile]
        if not profiles:
            raise SystemExit("Unknown profile: " + args.profile)
    out = Path(args.output).resolve()
    for profile in profiles:
        blend, glb = build_profile(profile, out)
        print("BUILT", profile["id"], blend, glb)


if __name__ == "__main__":
    main()
