import bpy, traceback
import numpy as np
from mathutils import kdtree

ASSETS = "/home/hatch/workspace/tools/blender/blender-5.2.3-linux-x64/5.2/datafiles/assets/nodes/procedural_hair_node_assets.blend"
STAGE1 = "/home/hatch/workspace/anthroforge-v2/fur-prototype/work/fur_stage1.blend"

try:
    bpy.ops.wm.open_mainfile(filepath=STAGE1)
    body = bpy.data.objects["BaraWolfBody"]
    me = body.data

    with bpy.data.libraries.load(ASSETS) as (src, dst):
        dst.node_groups = ["Generate Hair Curves"]
    gen = bpy.data.node_groups["Generate Hair Curves"]

    # --- wrapper group: density mask = FUR_ruff only ---
    wrap = bpy.data.node_groups.new("PROBE_wrap", "GeometryNodeTree")
    wrap.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    wrap.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    gin = wrap.nodes.new("NodeGroupInput"); gout = wrap.nodes.new("NodeGroupOutput")
    gn = wrap.nodes.new("GeometryNodeGroup"); gn.node_tree = gen
    na = wrap.nodes.new("GeometryNodeInputNamedAttribute"); na.data_type = "FLOAT"
    na.inputs["Name"].default_value = "FUR_ruff"
    wrap.links.new(na.outputs["Attribute"], gn.inputs["Density Mask"])
    gn.inputs["Density"].default_value = 3000.0
    gn.inputs["Hair Length"].default_value = 0.17
    gn.inputs["Surface"].default_value = body
    join = wrap.nodes.new("GeometryNodeJoinGeometry")
    wrap.links.new(gin.outputs["Geometry"], join.inputs["Geometry"])
    wrap.links.new(gn.outputs["Geometry"], join.inputs["Geometry"])
    wrap.links.new(join.outputs["Geometry"], gout.inputs["Geometry"])

    # --- curves object attached to body ---
    cu = bpy.data.hair_curves.new("ProbeHair")
    cu.surface = body
    cu.surface_uv_map = "tripo_node_0ffa5503DiffuseUVLayer"
    co = bpy.data.objects.new("ProbeHair", cu)
    bpy.context.scene.collection.objects.link(co)
    mod = co.modifiers.new("PROBE", "NODES"); mod.node_group = wrap

    dg = bpy.context.evaluated_depsgraph_get()
    ev = co.evaluated_get(dg)
    ec = ev.data
    ncurves = len(ec.splines) if hasattr(ec, "splines") else 0
    # curves data API: use attributes
    pts = np.empty(len(ec.points) * 3)
    ec.attributes["position"].data.foreach_get("vector", pts)
    pts = pts.reshape(-1, 3)
    # curve offsets
    offs = np.empty(len(ec.curves) + 1, dtype=np.int64) if hasattr(ec, "curves") else None
    print("POINTS:", len(pts))
    # roots = first point of each curve; get via curve offsets attribute domain
    # In 5.x, CurvesGeometry has .curves_range etc; use foreach on curves domain via attribute 'offset'? Fallback: use spline API through geometry component
    from bpy.types import CurvesGeometry
    # simpler: root indices from curve point counts via low-level: ec.curves gives count
    n_curves = len(ec.curves) if hasattr(ec, "curves") else -1
    print("N_CURVES_ATTR:", n_curves)
    # point->curve mapping: read 'curve_index' if present else compute from points per curve using ec.splines through evaluated object data copy
    counts = []
    # CurvesGeometry python API: ec.points per curve via .curves[i] not iterable; use attribute domain sizes:
    # offsets live in attribute "offset" on curve domain? Not exposed. Use evaluated geometry via to_mesh? no.
    # Alternative: iterate with ec.curves[i].points via foreach_get on "points_in_curve"? 
    # Use the splines-like accessor available in 5.x: ec.splines exists for legacy? try:
    roots = []
    try:
        for s in ec.splines:
            roots.append(np.array(s.points[0].co[:3]))
    except Exception as e:
        print("spline API failed:", e)
        # assume uniform points per curve
        npc = len(pts) // max(n_curves, 1)
        roots = [pts[i * npc] for i in range(n_curves)]
        print("assumed pts/curve:", npc)
    roots = np.array(roots)
    print("ROOTS:", len(roots))

    # nearest mesh vertex per root, compare FUR_ruff weight vs global
    vg_idx = body.vertex_groups["FUR_ruff"].index
    w = np.zeros(len(me.vertices))
    for v in me.vertices:
        for g in v.groups:
            if g.group == vg_idx:
                w[v.index] = g.weight
    verts = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", verts)
    verts = verts.reshape(-1, 3)
    kd = kdtree.KDTree(len(verts))
    for i, co_ in enumerate(verts):
        kd.insert(co_, i)
    kd.balance()
    root_w = np.array([w[kd.find(r)[1]] for r in roots[:: max(1, len(roots)//400)]])
    print("GLOBAL_MEAN_RUFF:", round(float(w.mean()), 4))
    print("ROOT_MEAN_RUFF:", round(float(root_w.mean()), 4))
    print("ROOT_FRAC_RUFF>0.5:", round(float((root_w > 0.5).mean()), 4))
except Exception:
    traceback.print_exc()
