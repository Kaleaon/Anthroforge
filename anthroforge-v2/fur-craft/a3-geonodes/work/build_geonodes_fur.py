"""A3 — Geometry Nodes fur generator prototype for AnthroForge (v2).

Architecture (per-region hair objects — see GEONODES_FUR.md for the probe
evidence behind this design):

  For each region r in {ruff, back, belly, coat, bodyhair}:
    AF_Fur_<r> (Curves, surface = BaraWolfBody)
      AF Fur Generate <r>   wrapper -> shipped "Generate Hair Curves"
                            Density Mask = Named Attribute FUR_<r>  (field: works)
                            Hair Length  = region constant          (field: does NOT
                              drive the nested asset in Blender 5.2 — probe-proven;
                              constants provably work, cf. the curtain's 0.30 m)
      AF Smooth / AF Curl / AF Clump        (shared wrapper groups)
      AF Interpolate <r>    wrapper -> "Interpolate Hair Curves",
                            Density Mask = FUR_<r> again, so children stay regional
      AF Frizz              (Preserve Length = True)

  CurtainSheet + CurtainHair: constant-mask Generate (0.30 m) -> Rotate (hang,
  auto-flip checked) -> Frizz.

Stages: AF_STAGE unset = build + save blend. AF_STAGE=render = renders only.
Run: blender -b --factory-startup -noaudio --python build_geonodes_fur.py
"""
import bpy, sys, time, math, os, traceback
import numpy as np
from mathutils import kdtree

sys.path.append("/home/hatch/workspace/anthroforge-v2/fur-prototype/work")
from studio import build_studio, set_camera  # noqa: E402

BLENDER_ASSETS = ("/home/hatch/workspace/tools/blender/blender-5.2.3-linux-x64"
                  "/5.2/datafiles/assets/nodes/procedural_hair_node_assets.blend")
STAGE1 = "/home/hatch/workspace/anthroforge-v2/fur-prototype/work/fur_stage1.blend"
OUTDIR = "/home/hatch/workspace/anthroforge-v2/fur-craft/a3-geonodes"
UV_NAME = "tripo_node_0ffa5503DiffuseUVLayer"

REGIONS = ["ruff", "back", "belly", "coat", "bodyhair"]
# particle-prototype parity values (FUR_PROTOTYPE.md section 3)
REGION_LENGTH = {"ruff": 0.170, "back": 0.095, "belly": 0.042,
                 "coat": 0.066, "bodyhair": 0.018}
REGION_DENSITY_MULT = {"ruff": 1.0, "back": 1.0, "belly": 1.0,
                       "coat": 1.0, "bodyhair": 1.0}
TARGET_GUIDES = 13500
TARGET_CHILDREN = 88000


def load_assets(names):
    todo = [n for n in names if n not in bpy.data.node_groups]
    if todo:
        lst = list(todo)
        with bpy.data.libraries.load(BLENDER_ASSETS) as (src, dst):
            dst.node_groups = lst
    return {n: bpy.data.node_groups[n] for n in names}


def new_group(name):
    g = bpy.data.node_groups.get(name)
    if g:
        bpy.data.node_groups.remove(g)
    g = bpy.data.node_groups.new(name, "GeometryNodeTree")
    g.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    g.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    return g


def make_generate_group(name, gen_asset, surface_obj, region, density, seed):
    """Wrapper around the shipped Generate Hair Curves asset for ONE region.

    Input geometry MUST be wired to the asset's 'Hair Surface' socket:
    Blender 5.2 carries the attachment surface as a geometry bundle on the
    curves object's input geometry; without this link the asset sees no
    surface and emits nothing (probe-proven).
    Density Mask = the region's vertex-group field (single Named Attribute).
    Hair Length = constant (fields into 'Hair Length' are not honoured in
    this nested configuration — probe-proven; constants are).
    Returns (group, asset_node) so density can be calibrated after a
    first evaluation.
    """
    g = new_group(name)
    gin = g.nodes.new("NodeGroupInput")
    gout = g.nodes.new("NodeGroupOutput")
    gn = g.nodes.new("GeometryNodeGroup")
    gn.node_tree = gen_asset
    gn.inputs["Density"].default_value = density
    gn.inputs["Seed"].default_value = seed
    gn.inputs["Control Points"].default_value = 10
    gn.inputs["Surface"].default_value = surface_obj
    gn.inputs["Hair Length"].default_value = (
        REGION_LENGTH[region] if region is not None else 0.30)
    mat = bpy.data.materials.get("FurHair")
    if mat:
        gn.inputs["Hair Material"].default_value = mat
    g.links.new(gin.outputs["Geometry"], gn.inputs["Hair Surface"])
    if region is not None:
        na = g.nodes.new("GeometryNodeInputNamedAttribute")
        na.data_type = "FLOAT"
        na.inputs["Name"].default_value = f"FUR_{region}"
        g.links.new(na.outputs["Attribute"], gn.inputs["Density Mask"])
    g.links.new(gn.outputs["Geometry"], gout.inputs["Geometry"])
    return g, gn


def make_wrapper(name, asset, params):
    """Thin wrapper around a shipped asset so its parameters are
    script-settable node defaults (modifier ID-property assignment is not
    reliable for node-group inputs from Python)."""
    g = new_group("AF " + name)
    gin = g.nodes.new("NodeGroupInput")
    gout = g.nodes.new("NodeGroupOutput")
    gn = g.nodes.new("GeometryNodeGroup")
    gn.node_tree = asset
    for k, v in params.items():
        try:
            gn.inputs[k].default_value = v
        except Exception as e:
            print(f"  wrapper {name}: could not set {k}={v}: {e}", flush=True)
    if "Geometry" in gn.inputs:
        g.links.new(gin.outputs["Geometry"], gn.inputs["Geometry"])
    out_sock = "Geometry" if "Geometry" in gn.outputs else gn.outputs[0].name
    g.links.new(gn.outputs[out_sock], gout.inputs["Geometry"])
    return g


def make_interpolate_group(name, asset, region, density):
    """Interpolate wrapper with the region field as Density Mask, so
    children are spawned in the same region as their guides."""
    g = new_group(name)
    gin = g.nodes.new("NodeGroupInput")
    gout = g.nodes.new("NodeGroupOutput")
    gn = g.nodes.new("GeometryNodeGroup")
    gn.node_tree = asset
    gn.inputs["Density"].default_value = density
    gn.inputs["Interpolation Guides"].default_value = 4
    gn.inputs["Follow Surface Normal"].default_value = True
    gn.inputs["Distance to Guides"].default_value = 0.03
    if region is not None:
        na = g.nodes.new("GeometryNodeInputNamedAttribute")
        na.data_type = "FLOAT"
        na.inputs["Name"].default_value = f"FUR_{region}"
        g.links.new(na.outputs["Attribute"], gn.inputs["Density Mask"])
    g.links.new(gin.outputs["Geometry"], gn.inputs["Geometry"])
    g.links.new(gn.outputs["Geometry"], gout.inputs["Geometry"])
    return g, gn


def make_radius_group(root_r=0.0011, tip_r=0.00025):
    """Set Curve Radius tapered along each strand (Curve Parameter factor
    0..1 -> root..tip radius). The Generate asset's default radius profile
    renders as thick ribbons at close range (see GEONODES_FUR.md SS5);
    this pass thins strands to hair-like widths."""
    g = new_group("AF Radius Taper")
    gin = g.nodes.new("NodeGroupInput")
    gout = g.nodes.new("NodeGroupOutput")
    scr = g.nodes.new("GeometryNodeSetCurveRadius")
    cp = g.nodes.new("GeometryNodeSplineParameter")
    mr = g.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 0.0
    mr.inputs["From Max"].default_value = 1.0
    mr.inputs["To Min"].default_value = root_r
    mr.inputs["To Max"].default_value = tip_r
    g.links.new(cp.outputs["Factor"], mr.inputs["Value"])
    g.links.new(mr.outputs["Result"], scr.inputs["Radius"])
    g.links.new(gin.outputs["Geometry"], scr.inputs["Curve"])
    g.links.new(scr.outputs["Curve"], gout.inputs["Geometry"])
    return g


def hair_material():
    m = bpy.data.materials.get("FurHair") or bpy.data.materials.new("FurHair")
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    hair = nt.nodes.new("ShaderNodeBsdfHairPrincipled")
    hair.inputs["Color"].default_value = (0.30, 0.21, 0.14, 1.0)
    hair.inputs["Roughness"].default_value = 0.42
    hair.inputs["Radial Roughness"].default_value = 0.55
    nt.links.new(hair.outputs["BSDF"], out.inputs["Surface"])
    return m


def add_hair_object(name, surface_obj, uv_name):
    cu = bpy.data.hair_curves.new(name)
    cu.surface = surface_obj
    cu.surface_uv_map = uv_name
    ob = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def add_mod(ob, name, group):
    mod = ob.modifiers.new(name, "NODES")
    mod.node_group = group
    return mod


def eval_curves(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    return ob.evaluated_get(dg).data


def curve_stats(ec):
    pos = np.empty(len(ec.points) * 3, dtype=np.float64)
    ec.attributes["position"].data.foreach_get("vector", pos)
    pos = pos.reshape(-1, 3)
    roots, lengths = [], []
    for c in ec.curves:
        idx = [c.first_point_index + j for j in range(c.points_length)]
        p = pos[idx]
        roots.append(p[0])
        lengths.append(float(np.linalg.norm(np.diff(p, axis=0), axis=1).sum()))
    return (np.array(roots) if roots else np.zeros((0, 3)),
            np.array(lengths))


def region_weights(body):
    me = body.data
    vg = {r: body.vertex_groups[f"FUR_{r}"].index for r in REGIONS}
    W = np.zeros((len(me.vertices), len(REGIONS)))
    for v in me.vertices:
        for gr in v.groups:
            for j, r in enumerate(REGIONS):
                if gr.group == vg[r]:
                    W[v.index, j] = gr.weight
    return W


def effective_areas(body, W):
    """Per-region effective surface area: sum over faces of area * mean
    vertex weight of the region."""
    me = body.data
    eff = np.zeros(len(REGIONS))
    for p in me.polygons:
        w = W[list(p.vertices)].mean(axis=0)
        eff += p.area * w
    return eff


def main():
    t_start = time.time()
    bpy.ops.wm.open_mainfile(filepath=STAGE1)
    body = bpy.data.objects["BaraWolfBody"]
    hair_material()
    assets = load_assets(["Generate Hair Curves", "Smooth Hair Curves",
                          "Curl Hair Curves", "Clump Hair Curves",
                          "Frizz Hair Curves", "Interpolate Hair Curves",
                          "Rotate Hair Curves"])
    gen = assets["Generate Hair Curves"]
    W = region_weights(body)
    eff_area = effective_areas(body, W)
    total_area = sum(p.area for p in body.data.polygons)
    print("EFF_AREA " + " ".join(f"{r}={eff_area[j]:.2f}"
                                 for j, r in enumerate(REGIONS))
          + f" total={total_area:.2f}", flush=True)

    groom = {
        "Smooth": make_wrapper("Smooth", assets["Smooth Hair Curves"],
                               {"Amount": 0.35, "Iterations": 4}),
        "Curl": make_wrapper("Curl", assets["Curl Hair Curves"],
                             {"Factor": 0.55, "Radius": 0.014,
                              "Random Offset": 0.35, "Curl Start": 0.15}),
        "Clump": make_wrapper("Clump", assets["Clump Hair Curves"],
                              {"Factor": 0.45, "Shape": 0.6}),
        "Frizz": make_wrapper("Frizz", assets["Frizz Hair Curves"],
                              {"Factor": 0.5, "Distance": 0.006,
                               "Preserve Length": True}),
    }

    # ---- pass 1: generate at probe density, count guides per region ----
    objects, gen_nodes = {}, {}
    D0 = 1500.0
    for i, r in enumerate(REGIONS):
        g, gn = make_generate_group(f"AF Fur Generate {r}", gen, body, r,
                                    D0 * REGION_DENSITY_MULT[r], seed=7 + i)
        ob = add_hair_object(f"AF_Fur_{r}", body, UV_NAME)
        add_mod(ob, f"AF Fur Generate {r}", g)
        objects[r] = ob
        gen_nodes[r] = gn
    counts = {}
    for r in REGIONS:
        counts[r] = len(eval_curves(objects[r]).curves)
    total_guides = sum(counts.values())
    print(f"PASS1 guides={counts} total={total_guides}", flush=True)
    scale = TARGET_GUIDES / max(total_guides, 1)
    for r in REGIONS:
        gen_nodes[r].inputs["Density"].default_value = (
            D0 * REGION_DENSITY_MULT[r] * scale)
    print(f"CALIBRATION scale={scale:.3f} -> target {TARGET_GUIDES}", flush=True)

    # ---- pass 2: grooming + children, calibrated per region ----
    guide_share = {r: counts[r] / max(total_guides, 1) for r in REGIONS}
    final_counts = {}
    for r in REGIONS:
        ob = objects[r]
        add_mod(ob, "AF Smooth", groom["Smooth"])
        add_mod(ob, "AF Curl", groom["Curl"])
        add_mod(ob, "AF Clump", groom["Clump"])
        target_r = TARGET_CHILDREN * guide_share[r]
        dens_r = target_r / max(eff_area[REGIONS.index(r)], 0.01)
        gi, _ = make_interpolate_group(f"AF Interpolate {r}",
                                       assets["Interpolate Hair Curves"],
                                       r, dens_r)
        add_mod(ob, f"AF Interpolate {r}", gi)
        add_mod(ob, "AF Frizz", groom["Frizz"])
        add_mod(ob, "AF Radius", make_radius_group())
        t0 = time.time()
        ec = eval_curves(ob)
        final_counts[r] = len(ec.curves)
        print(f"REGION {r}: guides~{int(counts[r]*scale)} children_total="
              f"{final_counts[r]} eval_s={time.time()-t0:.1f}", flush=True)
    print(f"CHILDREN_TOTAL={sum(final_counts.values())}", flush=True)

    # ---- verification: per-object strand lengths on the full stack ----
    print("LENGTH_CHECK (full-stack strands, by owning object):", flush=True)
    for r in REGIONS:
        ec = eval_curves(objects[r])
        _, lengths = curve_stats(ec)
        if len(lengths):
            print(f"  {r:9s} n={len(lengths):6d} mean_len={lengths.mean():.3f} "
                  f"p50={np.percentile(lengths, 50):.3f} "
                  f"target={REGION_LENGTH[r]:.3f}", flush=True)
    # placement: guide roots of the coat object vs dominant region
    ob = objects["coat"]
    for m in ob.modifiers:
        m.show_viewport = (m.name == "AF Fur Generate coat")
    bpy.context.view_layer.update()
    ec_g = eval_curves(ob)
    roots, _ = curve_stats(ec_g)
    for m in ob.modifiers:
        m.show_viewport = True
    bpy.context.view_layer.update()
    verts = np.empty(len(body.data.vertices) * 3)
    body.data.vertices.foreach_get("co", verts)
    verts = verts.reshape(-1, 3)
    kd = kdtree.KDTree(len(verts))
    for i, c in enumerate(verts):
        kd.insert(c, i)
    kd.balance()
    dom = np.array([int(np.argmax(W[kd.find(r)[1]])) for r in roots])
    shares = {REGIONS[j]: round(float((dom == j).mean()), 3)
              for j in range(len(REGIONS))}
    print(f"PLACEMENT coat-object guide roots by dominant region: {shares}",
          flush=True)

    build_curtain(assets, gen)
    bpy.ops.wm.save_as_mainfile(filepath=f"{OUTDIR}/geonodes_fur.blend")
    print("SAVED built blend", flush=True)
    print(f"TOTAL_S={time.time()-t_start:.1f}", flush=True)


def build_curtain(assets, gen):
    # sheet: vertical wall spanning X/Z, normal toward -Y (camera side)
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=64, y_subdivisions=16,
                                    size=1.0)
    sheet = bpy.context.active_object
    sheet.name = "CurtainSheet"
    sheet.scale = (1.1, 0.55, 1.0)
    bpy.ops.object.transform_apply(scale=True)
    sheet.rotation_euler = (math.radians(90), 0, 0)
    sheet.location = (4.0, 0.0, 1.08)
    bpy.ops.object.transform_apply(rotation=True)
    g, _ = make_generate_group("AF Curtain Generate", gen, sheet, None,
                               42000.0, seed=3)
    # constant length for the curtain: override the region default
    for n in g.nodes:
        if n.bl_idname == "GeometryNodeGroup":
            n.inputs["Hair Length"].default_value = 0.30
    hair = add_hair_object("CurtainHair", sheet, "UVMap")
    hair.location = sheet.location
    add_mod(hair, "AF Curtain Generate", g)
    rot = make_wrapper("CurtainRotate", assets["Rotate Hair Curves"],
                       {"Axis": (1.0, 0.0, 0.0), "Angle": math.radians(-105),
                        "Random Offset": 0.12})
    add_mod(hair, "AF Curtain Rotate", rot)
    add_mod(hair, "AF Curtain Frizz", make_wrapper(
        "CurtainFrizz", assets["Frizz Hair Curves"],
        {"Factor": 0.5, "Distance": 0.008, "Preserve Length": True}))
    ec = eval_curves(hair)
    roots, _ = curve_stats(ec)
    pos = np.empty(len(ec.points) * 3)
    ec.attributes["position"].data.foreach_get("vector", pos)
    pos = pos.reshape(-1, 3)
    tips = np.array([pos[c.first_point_index + c.points_length - 1]
                     for c in ec.curves])
    print(f"CURTAIN curves={len(ec.curves)} root_z={roots[:,2].mean():.3f} "
          f"tip_z={tips[:,2].mean():.3f}", flush=True)
    if tips[:, 2].mean() > roots[:, 2].mean():
        print("CURTAIN flipping rotate angle", flush=True)
        rot_g = bpy.data.node_groups["AF CurtainRotate"]
        for n in rot_g.nodes:
            if n.bl_idname == "GeometryNodeGroup":
                n.inputs["Angle"].default_value = math.radians(105)
        ec = eval_curves(hair)
        print(f"CURTAIN after flip curves={len(ec.curves)}", flush=True)
    print("CURTAIN built", flush=True)


def render_stage():
    bpy.ops.wm.open_mainfile(filepath=f"{OUTDIR}/geonodes_fur.blend")
    sc = bpy.context.scene
    cam = build_studio(sc)
    sc.render.engine = "CYCLES"
    sc.cycles.samples = 32
    sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = 720, 900
    set_camera(cam, (-2.0, -4.1, 1.55), (0, 0, 1.0), lens=40)
    sc.render.filepath = f"{OUTDIR}/render_geonodes_strands.png"
    t0 = time.time()
    bpy.ops.render.render(write_still=True)
    print(f"RENDER hero_s={time.time()-t0:.1f}", flush=True)
    set_camera(cam, (-0.95, -1.35, 1.75), (0.02, 0.05, 1.38), lens=55)
    sc.render.resolution_x, sc.render.resolution_y = 800, 800
    sc.render.filepath = f"{OUTDIR}/render_geonodes_closeup.png"
    bpy.ops.render.render(write_still=True)
    print("RENDER closeup done", flush=True)
    render_curtain()
    bpy.ops.wm.save_as_mainfile(filepath=f"{OUTDIR}/geonodes_fur.blend")
    print("RENDER_STAGE_DONE", flush=True)


def render_curtain():
    sheet = bpy.data.objects["CurtainSheet"]
    sc = bpy.context.scene
    cam = build_studio(sc)
    sc.render.engine = "CYCLES"
    sc.cycles.samples = 32
    sc.cycles.use_denoising = True
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = 1.25
    set_camera(cam, (4.0, -3.0, 1.0), (4.0, 0.0, 1.0), lens=50)
    sc.render.resolution_x, sc.render.resolution_y = 640, 800
    sc.render.film_transparent = False
    sc.render.filepath = f"{OUTDIR}/render_curtain.png"
    bpy.ops.render.render(write_still=True)
    print("RENDER curtain done", flush=True)
    sheet.hide_render = True
    for o in ("BaraWolfBody", "Ground"):
        if o in bpy.data.objects:
            bpy.data.objects[o].hide_render = True
    for o in bpy.data.objects:
        if o.name.startswith("AF_Fur"):
            o.hide_render = True
    sc.render.film_transparent = True
    sc.render.resolution_x, sc.render.resolution_y = 512, 1024
    cam.data.ortho_scale = 1.14
    sc.render.filepath = f"{OUTDIR}/curtain_card_texture.png"
    bpy.ops.render.render(write_still=True)
    print("RENDER curtain bake done", flush=True)
    sheet.hide_render = False
    for o in ("BaraWolfBody", "Ground"):
        if o in bpy.data.objects:
            bpy.data.objects[o].hide_render = False
    for o in bpy.data.objects:
        if o.name.startswith("AF_Fur"):
            o.hide_render = False
    sc.render.film_transparent = False
    cam.data.type = "PERSP"


def render_curtain_only_bake():
    """Bake half of render_curtain(), standalone (used by finish_a3.py
    after the combined render stage was interrupted during the bake)."""
    sheet = bpy.data.objects["CurtainSheet"]
    sc = bpy.context.scene
    cam = build_studio(sc)
    sc.render.engine = "CYCLES"
    sc.cycles.samples = 32
    sc.cycles.use_denoising = True
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = 1.14
    set_camera(cam, (4.0, -3.0, 1.0), (4.0, 0.0, 1.0), lens=50)
    sheet.hide_render = True
    for o in ("BaraWolfBody", "Ground"):
        if o in bpy.data.objects:
            bpy.data.objects[o].hide_render = True
    for o in bpy.data.objects:
        if o.name.startswith("AF_Fur"):
            o.hide_render = True
    sc.render.film_transparent = True
    sc.render.resolution_x, sc.render.resolution_y = 512, 1024
    sc.render.filepath = f"{OUTDIR}/curtain_card_texture.png"
    bpy.ops.render.render(write_still=True)
    print("RENDER curtain bake done", flush=True)


if __name__ == "__main__":
    try:
        if os.environ.get("AF_STAGE") == "render":
            render_stage()
        else:
            main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
