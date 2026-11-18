"""Kaleaon reference-informed greybox builder.

Run from Blender:
  blender --background --python build_kaleaon_blockout.py -- --output ./out

This is a proportion-editable greybox, not production topology. Dimensions are
provisional until the supplied turnaround is available. The script uses named
objects and separate accessory meshes so later sculpt/retopo work can replace
each component without losing character assembly semantics.
"""
from __future__ import annotations
import argparse, json, math, sys
from pathlib import Path
import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
PROFILE_PATH = HERE.parent / "kaleaon.v1.json"
# Reuse the project's shared species blockout primitives rather than forking
# the mesh-generation implementation.
from build_species_blockouts import clear_scene, material, make_loft, ellipsoid


def parse_args():
    av = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--output", default="./kaleaon-blockout")
    return p.parse_args(av)


def coat_material(name):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (0.82, 0.81, 0.78, 1)
    m.use_nodes = True
    nodes, links = m.node_tree.nodes, m.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    tex = nodes.new("ShaderNodeTexCoord")
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 5.5
    noise.inputs["Detail"].default_value = 2.0
    vor = nodes.new("ShaderNodeTexVoronoi")
    vor.inputs["Scale"].default_value = 7.0
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.12
    ramp.color_ramp.elements[0].color = (0.48, 0.47, 0.48, 1)
    ramp.color_ramp.elements[1].position = 0.28
    ramp.color_ramp.elements[1].color = (0.88, 0.87, 0.84, 1)
    links.new(tex.outputs["Generated"], vor.inputs["Vector"])
    links.new(vor.outputs["Distance"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(tex.outputs["Generated"], noise.inputs["Vector"])
    bsdf.inputs["Roughness"].default_value = 0.78
    return m


def curve_object(name, points, bevel, mat, cyclic=False):
    data = bpy.data.curves.new(name + "_Curve", "CURVE")
    data.dimensions = "3D"
    data.resolution_u = 16
    data.bevel_depth = bevel
    data.bevel_resolution = 4
    spline = data.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for p, co in zip(spline.points, points):
        p.co = (*co, 1)
    spline.use_cyclic_u = cyclic
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    return obj


def build(profile, output):
    clear_scene()
    d = profile["blockout_dimensions_m"]
    h, t, limbs, tail = d["head"], d["torso"], d["limbs"], d["tail"]
    coat = coat_material("Kaleaon_Coat_OffWhite_GreySpots")
    mauve = material("Kaleaon_Mauve_Shading", (0.42, 0.31, 0.39))
    dark = material("Kaleaon_Harness_Charcoal", (0.035, 0.032, 0.04))
    pink = material("Kaleaon_Nose_MutedPink", (0.42, 0.23, 0.28))
    metal = material("Kaleaon_Belt_Fitting", (0.42, 0.40, 0.35))
    ident = "Kaleaon"

    # Main trunk and deliberately exaggerated shoulder/chest mass.
    make_loft(ident+"_Torso_Blockout", (0, 0, 0.78), (0, 0, 1.55),
              (t["hip_width"]*.46, t["pelvis_depth"]*.48),
              (t["shoulder_width"]*.49, t["chest_depth"]*.50), coat, sides=32, bulge=.22)
    ellipsoid(ident+"_Pelvis", (0, 0, .82), (t["hip_width"]*.48, t["pelvis_depth"]*.52, .27), coat)
    ellipsoid(ident+"_Chest", (0, .015, 1.37), (t["shoulder_width"]*.52, t["chest_depth"]*.54, .31), coat)
    ellipsoid(ident+"_Abdominal_Mass", (0, .025, 1.08), (t["waist_width"]*.48, .18, .27), coat)
    ellipsoid(ident+"_Neck", (0, .02, 1.62), (.22, .20, .24), coat)

    # Sculpt guides for muscular shoulders, upper arms, forearms and thighs.
    for side, lr in [(-1, "L"), (1, "R")]:
        sx = side * t["shoulder_width"] * .48
        ellipsoid(ident+"_Deltoid_"+lr, (sx, .015, 1.43), (.22, .23, .23), coat)
        make_loft(ident+"_UpperArm_"+lr, (side*.30, .01, 1.43), (sx*1.12, .045, 1.02),
                  (limbs["upper_arm_girth"], limbs["upper_arm_girth"]*.90),
                  (limbs["upper_arm_girth"]*.82, limbs["upper_arm_girth"]*.78),
                  coat, sides=24, bulge=.18)
        make_loft(ident+"_Forearm_"+lr, (sx*1.12, .045, 1.02), (sx*1.17, .10, .72),
                  (limbs["forearm_girth"], limbs["forearm_girth"]*.85),
                  (limbs["forearm_girth"]*.65, limbs["forearm_girth"]*.62), coat, sides=24)
        ellipsoid(ident+"_HandPaw_"+lr, (sx*1.17, .15, .66), (.12, .16, .13), coat)
        hipx = side*t["hip_width"]*.26
        make_loft(ident+"_Thigh_"+lr, (hipx, 0, .84), (hipx, .015, .39),
                  (limbs["thigh_girth"], limbs["thigh_girth"]*.92),
                  (limbs["thigh_girth"]*.70, limbs["thigh_girth"]*.68), coat, sides=24, bulge=.18)
        make_loft(ident+"_Digitigrade_Shin_"+lr, (hipx, .015, .40), (hipx, -.12, .13),
                  (limbs["shin_girth"], limbs["shin_girth"]*.9),
                  (limbs["shin_girth"]*.48, limbs["shin_girth"]*.5), coat, sides=20)
        ellipsoid(ident+"_Hock_"+lr, (hipx, -.12, .16), (.075, .09, .11), mauve)
        ellipsoid(ident+"_Paw_"+lr, (hipx, .045, .085),
                  (.105*limbs["paw_scale"], .19*limbs["paw_scale"], .075), coat)

    # Feline head, muzzle, jaw and layered cheek/neck ruff masses.
    ellipsoid(ident+"_Skull", (0, .10, 1.82), (h["width"]*.5, h["length"]*.48, h["height"]*.5), coat)
    ellipsoid(ident+"_Muzzle", (0, .275, 1.77), (h["width"]*.31, h["muzzle_length"]*.50, .105), coat)
    ellipsoid(ident+"_Jaw", (0, .245, 1.70), (h["width"]*.30, .14, .075), mauve)
    ellipsoid(ident+"_Nose", (0, .405, 1.79), (.045, .035, .032), pink)
    for side, lr in [(-1, "L"), (1, "R")]:
        ellipsoid(ident+"_CheekRuff_"+lr, (side*.18, .035, 1.72), (.13, .17, .22), mauve)
        ellipsoid(ident+"_Ear_"+lr, (side*.145, .015, 2.015), (.095, .085, .115), coat)
        ellipsoid(ident+"_InnerEar_"+lr, (side*.145, .088, 2.02), (.052, .018, .067), mauve)

    # Long, flexible tail greybox: separate named curve, ready for spline rig.
    tail_pts = [(0, -.16, .87), (0, -.40, .83), (.03, -.68, .77),
                (.08, -.92, .69), (.13, -1.12, .63), (.18, -1.20, .68)]
    curve_object(ident+"_Tail_Blockout", tail_pts, tail["base_girth"]*.42, coat)

    # Harness is separate wearable geometry, never baked into skin.
    curve_object(ident+"_Harness_LeftStrap", [(-.28,.17,1.55),(-.36,.18,1.34),(-.30,.17,1.12),(-.22,.15,.91)], .026, dark)
    curve_object(ident+"_Harness_RightStrap", [(.28,.17,1.55),(.36,.18,1.34),(.30,.17,1.12),(.22,.15,.91)], .026, dark)
    curve_object(ident+"_Harness_ChestBand", [(-.39,.16,1.34),(0,.20,1.31),(.39,.16,1.34)], .03, dark)
    curve_object(ident+"_Harness_WaistBand", [(-.30,.12,.91),(0,.18,.89),(.30,.12,.91)], .03, dark)
    ellipsoid(ident+"_Belt_Fitting", (0,.205,.90), (.07,.025,.045), metal)

    # Separate glasses frame and bridge; lenses are translucent material objects.
    frame = material("Kaleaon_Glasses_Frame", (.045,.04,.05))
    lens = material("Kaleaon_Glasses_Lens", (.30,.38,.43))
    lens.diffuse_color = (.30,.38,.43,1.0)
    for side in (-1, 1):
        x = side*.105
        ring = [(x-.075,.405,1.845),(x+.075,.405,1.845),(x+.075,.405,1.765),(x-.075,.405,1.765)]
        curve_object(ident+("_Glasses_L" if side<0 else "_Glasses_R"), ring, .009, frame, True)
        ellipsoid(ident+("_Lens_L" if side<0 else "_Lens_R"), (x,.399,1.805), (.067,.008,.035), lens)
    curve_object(ident+"_Glasses_Bridge", [(-.03,.41,1.805),(.03,.41,1.805)], .008, frame)

    scene = bpy.context.scene
    scene["anthroforge_character_id"] = "sona.kaleaon"
    scene["anthroforge_build_stage"] = "reference_informed_greybox"
    scene["anthroforge_reference_status"] = profile["status"]
    scene["anthroforge_profile_json"] = json.dumps(profile, sort_keys=True)
    out = Path(output).resolve()
    out.mkdir(parents=True, exist_ok=True)
    blend, glb = out/"Kaleaon_blockout.blend", out/"Kaleaon_blockout.glb"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    bpy.ops.export_scene.gltf(filepath=str(glb), export_format="GLB", export_apply=False)
    return blend, glb


def main():
    args = parse_args()
    profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    print("BUILT", *build(profile, args.output))


if __name__ == "__main__":
    main()
