"""Kaleaon reference-informed greybox builder.

Run from Blender:
  blender --background --python build_kaleaon_blockout.py -- --output ./out

This is a reference-informed sculpt blockout. It fuses overlapping coat masses
into a single voxel-remeshed sculpt surface while retaining separate wearable
accessories and facial details. It is not yet retopologized or rig-ready.
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
    noise.inputs["Scale"].default_value = 3.0
    noise.inputs["Detail"].default_value = 2.0
    vor = nodes.new("ShaderNodeTexVoronoi")
    vor.inputs["Scale"].default_value = 3.2
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.10
    ramp.color_ramp.elements[0].color = (0.48, 0.47, 0.48, 1)
    ramp.color_ramp.elements[1].position = 0.34
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


def fuse_coat_surface(voxel_size=0.016):
    """Fuse overlapping coat masses into one sculptable surface.

    Wearables, eyes, nose, jaw accents and tail remain separate so they can be
    fitted, edited and rigged independently. This is a sculpt base, not final
    animation topology.
    """
    bpy.ops.object.select_all(action="DESELECT")
    body = []
    excluded = ("_Nose", "_Eye_", "_Iris_", "_InnerEar_", "_Jaw",
                "_Hock_", "_Harness_", "_UpperArmBand_", "_Belt_",
                "_Glasses_", "_Lens_", "_Tail_", "_PawToe_", "_Claw_",\n                "_Genitalia_", "_Sac_", "_Teat_")
    for obj in list(bpy.context.scene.objects):
        if obj.type == "MESH" and obj.name.startswith("Kaleaon_") and not any(
            token in obj.name for token in excluded
        ):
            body.append(obj)
    if not body:
        raise RuntimeError("No coat meshes found for sculpt-surface fusion")
    bpy.ops.object.select_all(action="DESELECT")
    for obj in body:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = body[0]
    bpy.ops.object.join()
    skin = bpy.context.object
    skin.name = "Kaleaon_SculptBase_Unified"
    skin.data.name = "Kaleaon_SculptBase_Unified_Mesh"
    skin.data.remesh_voxel_size = voxel_size
    skin.data.remesh_mode = "VOXEL"
    bpy.ops.object.voxel_remesh()
    for poly in skin.data.polygons:
        poly.use_smooth = True
    smooth = skin.modifiers.new("SculptBase_SurfaceRelax", "SMOOTH")
    smooth.factor = 0.65
    smooth.iterations = 4
    skin["anthroforge_mesh_role"] = "unified_sculpt_base"
    skin["anthroforge_topology_status"] = "voxel_remeshed_sculpt_base_not_retopologized"
    return skin


def apply_character_scale(target_height):
    """Scale the complete character so its measured bounds match the chosen height."""
    bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
    bpy.ops.object.select_all(action="SELECT")
    bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
    bpy.context.scene.tool_settings.transform_pivot_point = "CURSOR"
    bpy.context.view_layer.update()
    corners = [
        obj.matrix_world @ Vector(corner)
        for obj in bpy.context.selected_objects
        if obj.type in {"MESH", "CURVE"}
        for corner in obj.bound_box
    ]
    if not corners:
        raise RuntimeError("Cannot determine character bounds for scale calibration")
    current_height = max(v.z for v in corners) - min(v.z for v in corners)
    if current_height <= 0:
        raise RuntimeError("Character bounds have non-positive height")
    factor = target_height / current_height
    bpy.ops.transform.resize(value=(factor, factor, factor), orient_type="GLOBAL")
    bpy.context.view_layer.update()
    return factor


def make_component_collection(name, parent=None):
    """Create a dedicated collection, optionally nested under a module root."""
    collection = bpy.data.collections.new(name)
    (parent.children if parent else bpy.context.scene.collection.children).link(collection)
    return collection


def move_to_collection(obj, collection):
    for owner in list(obj.users_collection):
        owner.objects.unlink(obj)
    collection.objects.link(obj)


def tag_anatomy_component(obj, role, index=None):
    obj["anthroforge_component_group"] = "kaleaon_lower_anatomy"
    obj["anthroforge_anatomy_role"] = role
    obj["anthroforge_independent_component"] = True
    if index is not None:
        obj["anthroforge_component_index"] = index
    obj["anthroforge_attach_region"] = "pelvic_mount"
    obj["anthroforge_rigging_status"] = "separate_mesh_pending_armature_weights"


def build_lower_anatomy(profile, coat):
    """Build optional lower anatomy as three independently editable assemblies.

    The four shaft meshes, shared sac mesh, and individual teat meshes are
    deliberately excluded from the unified body sculpt surface. They remain
    separate objects and collections for independent visibility, fitting,
    scaling, material assignment and later rigging.
    """
    cfg = profile["anatomy_components"]
    root = make_component_collection("Kaleaon_Anatomy_Modules")
    shafts_collection = make_component_collection("Kaleaon_Genitalia_Quad", root)
    sac_collection = make_component_collection("Kaleaon_Sac_Module", root)
    teats_collection = make_component_collection("Kaleaon_Teats_Module", root)

    dark = material("Kaleaon_Anatomy_DeepMauve", (0.20, 0.045, 0.085))
    pink = material("Kaleaon_Teat_MutedRose", (0.62, 0.27, 0.38))
    shafts = cfg["genitalia"]
    count = shafts["count"]
    if count != 4:
        raise ValueError("Kaleaon anatomy profile requires exactly four independent shafts")
    spacing_x = shafts["spacing_x_m"]
    spacing_z = shafts["spacing_z_m"]
    center_z = shafts["center_z_m"]
    for i in range(count):
        col = (i % 2) - 0.5
        row = (i // 2) - 0.5
        obj = ellipsoid(
            "Kaleaon_Genitalia_Shaft_%02d" % (i + 1),
            (col * spacing_x, cfg["mount_y_m"], center_z + row * spacing_z),
            (shafts["radius_x_m"], shafts["radius_y_m"], shafts["length_m"] * 0.5),
            dark,
        )
        move_to_collection(obj, shafts_collection)
        tag_anatomy_component(obj, "independent_shaft", i + 1)
        obj["anthroforge_pivot_hint"] = "proximal_end"

    sac_cfg = cfg["sac"]
    sac = ellipsoid(
        "Kaleaon_Sac_Shared",
        (0.0, cfg["mount_y_m"] - 0.035, sac_cfg["center_z_m"]),
        (sac_cfg["width_m"] * 0.5, sac_cfg["depth_m"] * 0.5, sac_cfg["height_m"] * 0.5),
        dark,
    )
    move_to_collection(sac, sac_collection)
    tag_anatomy_component(sac, "shared_sac")

    teat_cfg = cfg["teats"]
    for i, (x, zoff) in enumerate(teat_cfg["positions_m"]):
        teat = ellipsoid(
            "Kaleaon_Teat_%02d" % (i + 1),
            (x, cfg["mount_y_m"] - 0.075, sac_cfg["center_z_m"] + zoff),
            (teat_cfg["radius_x_m"], teat_cfg["radius_y_m"], teat_cfg["radius_z_m"]),
            pink,
        )
        move_to_collection(teat, teats_collection)
        tag_anatomy_component(teat, "individual_teat", i + 1)
    return root


def build(profile, output):
    clear_scene()
    d = profile["blockout_dimensions_m"]
    h, t, limbs, tail = d["head"], d["torso"], d["limbs"], d["tail"]
    coat = coat_material("Kaleaon_Coat_OffWhite_GreySpots")
    mauve = material("Kaleaon_Mauve_Shading", (0.42, 0.31, 0.39))
    dark = material("Kaleaon_Harness_Charcoal", (0.035, 0.032, 0.04))
    pink = material("Kaleaon_Nose_MutedPink", (0.42, 0.23, 0.28))
    eye_white = material("Kaleaon_Eye_OffWhite", (0.82, 0.81, 0.76))
    iris = material("Kaleaon_Iris_Green", (0.18, 0.34, 0.12))
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
        ellipsoid(ident+"_Eye_"+lr, (side*.095, .345, 1.835), (.045, .025, .045), eye_white)
        ellipsoid(ident+"_Iris_"+lr, (side*.095, .369, 1.835), (.022, .012, .026), iris)
        ellipsoid(ident+"_CheekRuff_"+lr, (side*.18, .035, 1.72), (.13, .17, .22), mauve)
        ellipsoid(ident+"_Ear_"+lr, (side*.145, .015, 2.015), (.095, .085, .115), coat)
        ellipsoid(ident+"_InnerEar_"+lr, (side*.145, .088, 2.02), (.052, .018, .067), mauve)

        # Four editable toe lobes and dark claw tips give each foot a paw silhouette.
        for toe in range(4):
            toe_x = hipx + (toe - 1.5) * .047
            toe_y = .18
            ellipsoid(ident+"_PawToe_"+lr+"_"+str(toe+1), (toe_x, toe_y, .075),
                      (.034, .085, .045), coat)
            ellipsoid(ident+"_Claw_"+lr+"_"+str(toe+1), (toe_x, .245, .068),
                      (.018, .032, .018), dark)

    # Long, flexible tail greybox: separate named curve, ready for spline rig.
    tail_len = tail["length"]
    tail_pts = [(0, -.15*tail_len, .87), (0, -.38*tail_len, .83), (.03*tail_len, -.62*tail_len, .77),
                (.08*tail_len, -.82*tail_len, .69), (.13*tail_len, -.98*tail_len, .63),
                (.18*tail_len, -tail_len, .68)]
    curve_object(ident+"_Tail_Blockout", tail_pts, tail["base_girth"]*.42, coat)

    # Harness is separate wearable geometry, never baked into skin.
    curve_object(ident+"_Harness_LeftStrap", [(-.28,.17,1.55),(-.36,.18,1.34),(-.30,.17,1.12),(-.22,.15,.91)], .026, dark)
    curve_object(ident+"_Harness_RightStrap", [(.28,.17,1.55),(.36,.18,1.34),(.30,.17,1.12),(.22,.15,.91)], .026, dark)
    curve_object(ident+"_Harness_ChestBand", [(-.39,.16,1.34),(0,.20,1.31),(.39,.16,1.34)], .03, dark)
    curve_object(ident+"_Harness_WaistBand", [(-.30,.12,.91),(0,.18,.89),(.30,.12,.91)], .03, dark)
    # Shoulder harness continues over the back as a distinct X, matching the
    # supplied rear turnaround. Keep it separate from the body for fitting.
    curve_object(ident+"_Harness_Back_Left", [(-.30,-.16,1.55),(-.20,-.19,1.36),(0,-.20,1.18),(.24,-.15,.91)], .028, dark)
    curve_object(ident+"_Harness_Back_Right", [(.30,-.16,1.55),(.20,-.19,1.36),(0,-.20,1.18),(-.24,-.15,.91)], .028, dark)
    # Paired upper-arm bands are independent wearable parts.
    for side, lr in [(-1, "L"), (1, "R")]:
        x = side * .49
        curve_object(ident+"_UpperArmBand_"+lr, [(x-.13,.04,1.28),(x,.16,1.28),(x+.13,.04,1.28),(x,-.12,1.28)], .025, dark, True)
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

    # Optional lower anatomy remains modular and is never fused into the body.\n    anatomy_root = build_lower_anatomy(profile, coat)\n\n    # Fuse the coat-colored anatomy into one continuous sculpting surface.
    skin = fuse_coat_surface()
    # Calibrate the complete character to the user-selected seven-foot target.
    scale_factor = apply_character_scale(d["overall_height"])

    scene = bpy.context.scene
    scene["anthroforge_character_id"] = "sona.kaleaon"
    scene["anthroforge_build_stage"] = "reference_informed_unified_sculpt_blockout"
    scene["anthroforge_target_height_m"] = d["overall_height"]
    scene["anthroforge_scale_factor"] = scale_factor
    scene["anthroforge_sculpt_base"] = skin.name\n    scene["anthroforge_anatomy_module"] = anatomy_root.name\n    scene["anthroforge_anatomy_separation"] = "four_independent_shafts_shared_sac_individual_teats_all_separate_from_body"
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
