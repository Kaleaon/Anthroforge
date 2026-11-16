#!/usr/bin/env python3
"""B9 edge-craft demo: one library ear (base-head-v4 Ear_L) finished 3 ways.
A: smooth-by-angle only   B: smooth + weighted normals   C: bevel + weighted
Outputs: edges_demo.blend, renders, stats.json (paths via argv after --).
"""
import bpy, json, math, sys
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
OUT, RDIR = argv[0], argv[1]
SRC = "/home/hatch/workspace/anthroforge-v2/base-head-v4/neutral_base_head_v4.glb"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
ear = bpy.context.scene.objects["Ear_L"]
for o in list(bpy.context.scene.objects):
    if o is not ear:
        bpy.data.objects.remove(o, do_unlink=True)
bpy.context.view_layer.objects.active = ear
ear.select_set(True)
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

# weld GLB vertex splits so all three variants start from identical geometry
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.remove_doubles(threshold=0.0001)
bpy.ops.mesh.customdata_custom_splitnormals_clear()
bpy.ops.mesh.mark_sharp(clear=True)  # GLB import marked EVERY edge sharp;
# clear so each variant decides its own edges from a clean slate
bpy.ops.object.mode_set(mode='OBJECT')
me = ear.data
base_stats = {"verts": len(me.vertices), "polys": len(me.polygons),
              "edges": len(me.edges),
              "sharp_edges": sum(1 for e in me.edges if e.use_edge_sharp)}
print("BASE after weld:", base_stats, flush=True)

def world_center(ob):
    ws = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    return sum(ws, Vector()) / 8.0

# centre geometry at origin via object location shift
ear.location -= world_center(ear)
bpy.context.view_layer.update()
dims = ear.dimensions
print("dims:", [round(d, 3) for d in dims], "centre now:",
      [round(v, 3) for v in world_center(ear)], flush=True)

def make_variant(name, x_off):
    ob = ear.copy(); ob.data = ear.data.copy(); ob.name = name
    bpy.context.collection.objects.link(ob)
    ob.location.x += x_off
    return ob

def loop_deviation(ob):
    """Mean / p95 angle (deg) between each loop's shading normal and its
    face normal, on the evaluated mesh: a shading-smear proxy."""
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    m = ev.to_mesh()
    m.calc_loop_triangles()
    devs = []
    try:
        cn = m.corner_normals
        for p in m.polygons:
            fn = p.normal
            for li in range(p.loop_start, p.loop_start + p.loop_total):
                ln = cn[li].vector
                if ln.length > 0 and fn.length > 0:
                    devs.append(math.degrees(fn.angle(ln)))
    except Exception as e:
        print("loop dev failed:", e)
    ev.to_mesh_clear()
    devs.sort()
    if not devs:
        return None
    n = len(devs)
    return {"mean_deg": round(sum(devs) / n, 2),
            "p95_deg": round(devs[int(0.95 * n)], 2),
            "loops_over_15deg_pct": round(100.0 * sum(1 for d in devs if d > 15) / n, 1)}

def eval_counts(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    m = ev.to_mesh()
    c = {"verts": len(m.vertices), "polys": len(m.polygons)}
    ev.to_mesh_clear()
    return c

stats = {"base": base_stats, "variants": {}}
gap = dims.x * 1.7

# make all three copies FIRST, then remove the source: edit-mode ops in an
# earlier version contaminated later copies through the still-selected
# source object (multi-object edit mode). No edit-mode ops are used below
# at all now -- edge sharpness is set by direct attribute writes.
a = make_variant("A_raw_autosmooth", -gap)
b = make_variant("B_weighted_normals", 0.0)
c = make_variant("C_bevelled_weighted", gap)
bpy.data.objects.remove(ear, do_unlink=True)

def sharp_by_angle(ob, deg=30.0):
    """Pure-python auto-smooth emulation: all faces smooth; edges whose
    adjacent face normals differ by more than `deg` are marked sharp."""
    import numpy as np
    me = ob.data
    for p in me.polygons:
        p.use_smooth = True
    fn = np.empty(len(me.polygons) * 3)
    me.polygons.foreach_get("normal", fn)
    fn = fn.reshape(-1, 3)
    ef = {}
    for p in me.polygons:
        vs = list(p.vertices)
        for i in range(len(vs)):
            key = tuple(sorted((vs[i], vs[(i + 1) % len(vs)])))
            ef.setdefault(key, []).append(p.index)
    n_sharp = 0
    for e in me.edges:
        adj = ef.get(tuple(sorted(e.vertices)), [])
        if len(adj) == 2:
            cosang = float(np.dot(fn[adj[0]], fn[adj[1]]))
            if math.degrees(math.acos(max(-1.0, min(1.0, cosang)))) > deg:
                e.use_edge_sharp = True
                n_sharp += 1
    return n_sharp

# ---- A: auto-smooth only (the 'just turn it on' finish) -------------------
na = sharp_by_angle(a, 30.0)
stats["variants"]["A"] = {"eval": eval_counts(a), "loop_dev": loop_deviation(a),
                          "mods": [m.type for m in a.modifiers],
                          "sharp_edges": na}
print("A sharp edges:", na, flush=True)

# ---- B: full smooth + weighted normals ------------------------------------
for p in b.data.polygons:
    p.use_smooth = True
wn = b.modifiers.new("WeightedNormal", 'WEIGHTED_NORMAL')
wn.mode = 'FACE_AREA_WITH_ANGLE'
wn.keep_sharp = True
stats["variants"]["B"] = {"eval": eval_counts(b), "loop_dev": loop_deviation(b),
                          "mods": [m.type for m in b.modifiers],
                          "sharp_edges": 0}

# ---- C: bevelled rim + weighted normals (production finish) ---------------
for p in c.data.polygons:
    p.use_smooth = True
bev = c.modifiers.new("Bevel", 'BEVEL')
bev.width = 0.008
bev.segments = 3
bev.limit_method = 'ANGLE'
bev.angle_limit = math.radians(30.0)
bev.harden_normals = True
wn2 = c.modifiers.new("WeightedNormal", 'WEIGHTED_NORMAL')
wn2.mode = 'FACE_AREA_WITH_ANGLE'
wn2.keep_sharp = True
stats["variants"]["C"] = {"eval": eval_counts(c), "loop_dev": loop_deviation(c),
                          "mods": [m.type for m in c.modifiers],
                          "sharp_edges": 0}
print("STATS:", json.dumps(stats), flush=True)

# ---- studio: clay material, key + rim lights, one camera -------------------
mat = bpy.data.materials.new("clay")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.40, 0.385, 0.37, 1)
bsdf.inputs["Roughness"].default_value = 0.62
for ob in (a, b, c):
    ob.data.materials.clear()
    ob.data.materials.append(mat)

def point_at(ob, tgt):
    ob.rotation_euler = (Vector(tgt) - ob.location).to_track_quat('-Z', 'Y').to_euler()

def add_light(name, loc, energy, size):
    ld = bpy.data.lights.new(name, 'AREA')
    ld.energy = energy; ld.shape = 'DISK'; ld.size = size
    lo = bpy.data.objects.new(name, ld)
    bpy.context.collection.objects.link(lo)
    lo.location = loc
    point_at(lo, (0, 0, 0))
    return lo

add_light("Key", (0.6, -0.9, 0.9), 42, 1.2)
add_light("Rim", (-0.8, 0.7, 0.5), 90, 0.8)
add_light("Fill", (-0.7, -0.6, -0.4), 18, 1.5)

cam_data = bpy.data.cameras.new("Cam"); cam_data.lens = 70
cam = bpy.data.objects.new("Cam", cam_data)
bpy.context.collection.objects.link(cam)
sc = bpy.context.scene
sc.camera = cam
sc.render.engine = 'CYCLES'
sc.cycles.samples = 48
sc.cycles.use_denoising = False
sc.render.resolution_x = 640; sc.render.resolution_y = 640
sc.world = bpy.data.worlds.new("W")
sc.world.use_nodes = True
sc.world.node_tree.nodes["Background"].inputs[0].default_value = (0.08, 0.08, 0.09, 1)
sc.world.node_tree.nodes["Background"].inputs[1].default_value = 1.0

def shoot(ob, tag, direction):
    tgt = world_center(ob)
    cam.location = tgt + Vector(direction).normalized() * 0.95 + Vector((0, 0, 0.02))
    point_at(cam, tgt)
    for o in (a, b, c):
        o.hide_render = o is not ob
    sc.render.filepath = f"{RDIR}/{tag}.png"
    bpy.ops.render.render(write_still=True)
    print("rendered", tag, flush=True)

FRONT = (0.35, -1.0, 0.25)   # three-quarter front: reads blade + inner fold
SIDE = (1.0, -0.25, 0.1)     # profile: reads the rim edge itself
for ob, tag in ((a, "a_autosmooth"), (b, "b_weighted"), (c, "c_bevelled")):
    shoot(ob, f"{tag}_front", FRONT)
    shoot(ob, f"{tag}_side", SIDE)
# lineup: all three, straight on
for o in (a, b, c):
    o.hide_render = False
cam_data.lens = 50
cam.location = Vector((0, -1.45, 0.12)); point_at(cam, (0, 0, 0))
sc.render.filepath = f"{RDIR}/lineup.png"
bpy.ops.render.render(write_still=True)
print("rendered lineup", flush=True)

bpy.ops.wm.save_as_mainfile(filepath=f"{OUT}/edges_demo.blend")
with open(f"{OUT}/stats.json", "w") as f:
    json.dump(stats, f, indent=1)
print("DONE", flush=True)
