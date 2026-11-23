#!/usr/bin/env python3
"""B14 appendage parts: bushy canine tail, upright canine ears, curved horns.

Procedural construction in Blender (headless). Parts are authored in
LOCAL socket frames (origin = socket anchor):
  tail : origin at tail.base socket, tail extends -Y (back), +Z up.
  ear  : origin at ear socket centre (skull cone centre), +Z along ear,
         +Y forward (cup opens forward), +X outward for the R ear.
  horn : origin at horn base centre on skull, +Z initial growth dir.

Exports GLB (+STL) per part into ../parts and a stats JSON into ../work.
"""
import bpy, math, json, os, random
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "parts")
WORK = os.path.join(HERE, "..", "work")
os.makedirs(OUT, exist_ok=True)
os.makedirs(WORK, exist_ok=True)

random.seed(1414)

# ---------------------------------------------------------------- scene reset
bpy.ops.wm.read_factory_settings(use_empty=True)

# ---------------------------------------------------------------- helpers
def catmull_rom(points, samples):
    """points: list[Vector]; returns `samples` interpolated points + tangents."""
    pts = [points[0]] + list(points) + [points[-1]]
    out = []
    segs = len(points) - 1
    for i in range(samples):
        u = i / (samples - 1)
        f = u * segs
        k = min(int(f), segs - 1)
        t = f - k
        p0, p1, p2, p3 = pts[k], pts[k + 1], pts[k + 2], pts[k + 3]
        pos = 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                     + (-p0 + 3 * p1 - 3 * p2 + p3) * t * t * t)
        tan = 0.5 * ((-p0 + p2) + 2 * (2 * p0 - 5 * p1 + 4 * p2 - p3) * t
                     + 3 * (-p0 + 3 * p1 - 3 * p2 + p3) * t * t)
        out.append((pos, tan.normalized()))
    return out

def lerp_profile(stops, t):
    """stops: list of (t, value) sorted; piecewise-linear interp."""
    if t <= stops[0][0]:
        return stops[0][1]
    for (t0, v0), (t1, v1) in zip(stops, stops[1:]):
        if t <= t1:
            return v0 + (v1 - v0) * (t - t0) / max(t1 - t0, 1e-9)
    return stops[-1][1]

def ring_frames(spine):
    """Parallel-transport frames along spine [(pos, tan)] -> (pos, tan, side, up)."""
    frames = []
    side = Vector((1, 0, 0))
    for pos, tan in spine:
        side = side - tan * side.dot(tan)
        if side.length < 1e-6:
            side = Vector((0, 0, 1)).cross(tan)
        side.normalize()
        up = tan.cross(side).normalized()
        frames.append((pos, tan, side, up))
    return frames

def tube(name, spine_pts, n_rings, per_ring, radius_fn, color_fn=None,
         cap_start=True, cap_end=True, ripple=0.0):
    """Build a tube mesh. radius_fn(t, j, per_ring) -> radius multiplier base.
       color_fn(t, phi) -> (r,g,b) vertex colour. Returns (obj, ring_t list)."""
    spine = catmull_rom(spine_pts, n_rings)
    frames = ring_frames(spine)
    verts, faces, cols, ring_t = [], [], [], []
    for i, (pos, tan, side, up) in enumerate(frames):
        t = i / (n_rings - 1)
        ring_t.append(t)
        for j in range(per_ring):
            phi = 2 * math.pi * j / per_ring
            dirv = side * math.cos(phi) + up * math.sin(phi)
            r = radius_fn(t, phi)
            if ripple:
                r *= 1.0 + ripple * math.sin(phi * 3 + t * 21.0) * math.sin(t * 47.0)
            verts.append(tuple(pos + dirv * r))
            if color_fn:
                cols.append(color_fn(t, phi))
    for i in range(n_rings - 1):
        for j in range(per_ring):
            a = i * per_ring + j
            b = i * per_ring + (j + 1) % per_ring
            c = b + per_ring
            d = a + per_ring
            faces.append((a, b, c, d))
    if cap_start:
        c0 = len(verts); verts.append(tuple(frames[0][0]))
        if color_fn: cols.append(color_fn(0.0, 0.0))
        for j in range(per_ring):
            faces.append((c0, (j + 1) % per_ring, j))
    if cap_end:
        c1 = len(verts); verts.append(tuple(frames[-1][0]))
        if color_fn: cols.append(color_fn(1.0, 0.0))
        base = (n_rings - 1) * per_ring
        for j in range(per_ring):
            faces.append((c1, base + j, base + (j + 1) % per_ring))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    if color_fn:
        attr = mesh.color_attributes.new(name="Col", type='FLOAT_COLOR', domain='POINT')
        for k, c in enumerate(cols):
            attr.data[k].color = (c[0], c[1], c[2], 1.0)
    return obj, ring_t

def make_material(name, rough=0.9):
    mat = bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = rough
    vc = mat.node_tree.nodes.new("ShaderNodeVertexColor")
    vc.layer_name = "Col"
    mat.node_tree.links.new(vc.outputs["Color"], bsdf.inputs["Base Color"])
    return mat

def assign_material(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)

def tri_weights(t, centres):
    """Triangular falloff weights over bone centres; returns [(idx, w)]."""
    out = []
    for i, c in enumerate(centres):
        if i == 0:
            lo, hi = centres[0], centres[1]
            w = 1.0 - max(0.0, (t - c)) / max(hi - c, 1e-9) if t >= c else 1.0
        elif i == len(centres) - 1:
            lo = centres[-2]
            w = max(0.0, (t - lo)) / max(c - lo, 1e-9) if t > lo else 0.0
            if t <= lo: w = 0.0
        else:
            if t < centres[i - 1] or t > centres[i + 1]:
                w = 0.0
            elif t <= c:
                w = (t - centres[i - 1]) / max(c - centres[i - 1], 1e-9)
            else:
                w = 1.0 - (t - c) / max(centres[i + 1] - c, 1e-9)
        if w > 1e-4:
            out.append((i, min(w, 1.0)))
    s = sum(w for _, w in out)
    return [(i, w / s) for i, w in out] if s > 0 else [(0, 1.0)]

def make_armature(name, bone_defs):
    """bone_defs: [(name, head Vector, tail Vector, parent_name|None)]"""
    arm = bpy.data.armatures.new(name)
    obj = bpy.data.objects.new(name, arm)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    made = {}
    for bname, head, tail, parent in bone_defs:
        b = arm.edit_bones.new(bname)
        b.head = head; b.tail = tail
        if parent:
            b.parent = made[parent]
        made[bname] = b
    bpy.ops.object.mode_set(mode='OBJECT')
    return obj

def skin(obj, arm_obj, bone_names, weight_fn):
    """weight_fn(vert_index) -> [(bone_idx, w)]. Adds groups + armature modifier."""
    for bn in bone_names:
        obj.vertex_groups.new(name=bn)
    for v in obj.data.vertices:
        for bi, w in weight_fn(v.index):
            obj.vertex_groups[bone_names[bi]].add([v.index], w, 'REPLACE')
    mod = obj.modifiers.new("Armature", 'ARMATURE')
    mod.object = arm_obj
    obj.parent = arm_obj

def export_obj(objs, arm_obj, path_glb, path_stl=None):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    if arm_obj:
        arm_obj.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.gltf(filepath=path_glb, export_format='GLB',
                              use_selection=True, export_yup=True,
                              export_skins=True, export_animations=False)
    if path_stl:
        bpy.ops.wm.stl_export(filepath=path_stl, export_selected_objects=True)

stats = {}

# ================================================================ TAIL
# Spine control points (socket frame: -Y back, +Z up). Dips then rises.
TAIL_SPINE = [Vector(p) for p in [
    (0, 0.005, 0.002), (0, -0.075, -0.028), (0, -0.155, -0.030),
    (0, -0.235, 0.005), (0, -0.300, 0.065), (0, -0.345, 0.135),
    (0, -0.365, 0.185), (0, -0.370, 0.215)]]
CORE_R = [(0.0, 0.030), (0.15, 0.028), (0.35, 0.025), (0.55, 0.022),
          (0.75, 0.019), (0.9, 0.014), (1.0, 0.007)]
VOL_R = [(0.0, 0.050), (0.15, 0.064), (0.35, 0.077), (0.55, 0.084),
         (0.72, 0.079), (0.88, 0.058), (1.0, 0.024)]

def tail_color(t, phi):
    # phi measured from +X side axis; up component = sin(phi) in frame(side,up)
    upness = math.sin(phi)
    dark = (0.23, 0.18, 0.14)
    pale = (0.78, 0.68, 0.55)
    k = 0.5 - 0.5 * upness          # 0 top -> dark, 1 bottom -> pale
    if t > 0.86:                    # distal third darkens again (canine tail tip)
        k *= 0.45
    return tuple(dark[i] + (pale[i] - dark[i]) * k for i in range(3))

tail_core, ct = tube("tail_core", TAIL_SPINE, 13, 8,
                     lambda t, phi: lerp_profile(CORE_R, t))
tail_vol, vt = tube("tail_volume", TAIL_SPINE, 17, 12,
                    lambda t, phi: lerp_profile(VOL_R, t),
                    color_fn=tail_color, ripple=0.035)
fur_mat = make_material("coat", 0.95)
plain_mat = make_material("core_mat", 0.9)
assign_material(tail_vol, fur_mat)
assign_material(tail_core, plain_mat)
tail_core.hide_render = True   # core ships in the file, hidden in beauty renders

# tail armature: 6 bones, heads at spine samples 0, .2, .4, .6, .8, tip
spine_s = catmull_rom(TAIL_SPINE, 31)
def spine_at(u):
    idx = min(int(u * 30), 29)
    f = u * 30 - idx
    return spine_s[idx][0].lerp(spine_s[idx + 1][0], f)
bone_pts = [spine_at(u) for u in (0.0, 0.18, 0.38, 0.58, 0.78, 0.93, 1.0)]
tail_bones = []
for i in range(6):
    tail_bones.append((f"Tail_{i+1}", bone_pts[i], bone_pts[i + 1],
                       f"Tail_{i}" if i else None))
tail_arm = make_armature("tail_rig", tail_bones)
TAIL_CENTRES = [0.0, 0.18, 0.38, 0.58, 0.78, 0.97]
for obj, rts in ((tail_core, ct), (tail_vol, vt)):
    skin(obj, tail_arm, [b[0] for b in tail_bones],
         lambda vi, rts=rts: tri_weights(rts[vi // (8 if rts is ct else 12)] if False else 0.0, TAIL_CENTRES))
# NOTE: the lambda above is replaced below with a per-vertex t lookup (cleaner):
def tail_weights(obj, rts, per_ring):
    for g in obj.vertex_groups:
        g.remove(list(range(len(obj.data.vertices))))
    for v in obj.data.vertices:
        ring = min(v.index // per_ring, len(rts) - 1) if v.index < per_ring * len(rts) else len(rts) - 1
        t = rts[ring]
        for bi, w in tri_weights(t, TAIL_CENTRES):
            obj.vertex_groups[TAIL_CENTRES and f"Tail_{bi+1}"].add([v.index], w, 'REPLACE')
tail_weights(tail_core, ct, 8)
tail_weights(tail_vol, vt, 12)

export_obj([tail_vol, tail_core], tail_arm,
           os.path.join(OUT, "tail_canine_bushy.glb"),
           os.path.join(OUT, "tail_canine_bushy.stl"))
stats["tail_canine_bushy"] = {
    "verts": len(tail_vol.data.vertices) + len(tail_core.data.vertices),
    "tris": sum(len(p.vertices) - 2 for p in tail_vol.data.polygons)
            + sum(len(p.vertices) - 2 for p in tail_core.data.polygons),
    "bones": 6, "meshes": ["tail_volume", "tail_core"]}

# ================================================================ EARS
EAR_H = 0.115
W_PROF = [(0.0, 0.060), (0.12, 0.072), (0.38, 0.088), (0.65, 0.076),
          (0.85, 0.052), (0.95, 0.026), (1.0, 0.003)]
CUP_PROF = [(0.0, 0.014), (0.3, 0.020), (0.6, 0.018), (0.85, 0.010), (1.0, 0.002)]

def ear_geometry(side):
    """Returns (verts, faces, vcoord) for outer sheet (side=+1 R, -1 L).

    Two skirt rows below v=0 dive into the skull cone (narrowing as they
    go): a flat-bottomed sheet's corners poke past the curved skull, so
    the base must be a buried skirt, not a cut edge (rule E2)."""
    skirt = [(-0.13, 0.76), (-0.065, 0.89)]
    rows, cols = 12, 9
    verts, vcoord = [], []
    for i in range(rows):
        if i < 2:
            v, wfac = skirt[i]
        else:
            v = (i - 2) / (rows - 3)
            wfac = 1.0
        w = lerp_profile(W_PROF, max(v, 0.0)) / 2.0 * wfac
        cup = lerp_profile(CUP_PROF, max(v, 0.0))
        z = EAR_H * v
        back = -0.016 * math.sin(max(v, 0.0) * math.pi * 0.72)  # distal lean-back
        out = side * 0.010 * max(v, 0.0)                  # slight outward cant
        fold = math.radians(20.0) * max(0.0, 1.0 - max(v, 0.0) / 0.38)  # base fold twist
        for j in range(cols):
            u = j / (cols - 1) * 2 - 1                   # -1..1 across width
            x = u * w
            y = -cup * (u * u) - 0.005 * abs(u) ** 3 + back
            if v < 0:
                # round the skirt footprint: pull the deep back corners
                # forward so they stay inside the skull's curve (E2)
                y += 0.011 * (-v / 0.13) * (u * u)
            # apply base fold: rotate (x, y) around Z axis by fold*side*
            a = fold * (1 if side > 0 else 1)
            xr = x * math.cos(a) - y * math.sin(a) * 0.35
            yr = x * math.sin(a) * 0.35 + y * math.cos(a)
            verts.append((side * (abs(xr) if False else xr) + out, yr, z))
            vcoord.append(v)
    faces = []
    for i in range(rows - 1):
        for j in range(cols - 1):
            a = i * cols + j; b = a + 1; c = a + cols; d = c + 1
            faces.append((a, b, d, c) if side > 0 else (a, c, d, b))
    return verts, faces, vcoord, rows, cols

def inner_geometry(side):
    """Inner pinna sheet: inset, forward-offset into the cup, tragus bump."""
    rows, cols = 7, 7
    verts, vcoord = [], []
    for i in range(rows):
        v = 0.16 + 0.74 * (i / (rows - 1))
        w = lerp_profile(W_PROF, v) / 2.0 * 0.74
        cup = lerp_profile(CUP_PROF, v)
        z = EAR_H * v
        back = -0.016 * math.sin(v * math.pi * 0.72)
        out = side * 0.010 * v
        for j in range(cols):
            u = j / (cols - 1) * 2 - 1
            x = u * w
            y = -cup * (u * u) * 0.82 + 0.0042 + back
            # tragus ridge: gaussian bump low-centre, pushed forward (+Y)
            g = math.exp(-(((u + 0.1) / 0.34) ** 2 + ((v - 0.24) / 0.13) ** 2))
            y += 0.0038 * g
            verts.append((side * x + out, y, z))
            vcoord.append(v)
    faces = []
    for i in range(rows - 1):
        for j in range(cols - 1):
            a = i * cols + j; b = a + 1; c = a + cols; d = c + 1
            faces.append((a, b, d, c) if side > 0 else (a, c, d, b))
    return verts, faces, vcoord

EAR_CENTRES = [0.0, 0.36, 0.68, 1.0]
ear_stats = {}
for side, tag in ((1, "R"), (-1, "L")):
    verts, faces, vcoord, rows, cols = ear_geometry(side)
    mesh = bpy.data.meshes.new(f"ear_{tag}_outer")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    outer = bpy.data.objects.new(f"ear_{tag}_outer", mesh)
    bpy.context.collection.objects.link(outer)
    # vertex colours: coat; tip slightly darker
    attr = mesh.color_attributes.new(name="Col", type='FLOAT_COLOR', domain='POINT')
    for k, v in enumerate(vcoord):
        c = (0.32, 0.25, 0.19) if v < 0.9 else (0.22, 0.17, 0.13)
        attr.data[k].color = (*c, 1.0)
    sol = outer.modifiers.new("thickness", 'SOLIDIFY')
    sol.thickness = 0.0022
    sol.offset = -0.5
    bpy.context.view_layer.objects.active = outer
    outer.select_set(True)
    bpy.ops.object.modifier_apply(modifier="thickness")
    outer.select_set(False)
    # weights after solidify: use z-height fraction of each vertex
    vfrac = [min(max(v.co.z / EAR_H, 0.0), 1.0) for v in outer.data.vertices]

    iverts, ifaces, ivcoord = inner_geometry(side)
    imesh = bpy.data.meshes.new(f"ear_{tag}_inner")
    imesh.from_pydata(iverts, [], ifaces)
    imesh.update()
    inner = bpy.data.objects.new(f"ear_{tag}_inner", imesh)
    bpy.context.collection.objects.link(inner)
    iattr = imesh.color_attributes.new(name="Col", type='FLOAT_COLOR', domain='POINT')
    for k in range(len(iverts)):
        iattr.data[k].color = (0.85, 0.66, 0.55, 1.0)     # pale inner ear
    ivfrac = list(ivcoord)

    bones = [("EarBase_" + tag, Vector((0, 0, 0.0)), Vector((0, 0, EAR_H * 0.36)), None),
             ("Ear1_" + tag, Vector((0, 0, EAR_H * 0.36)), Vector((0, 0, EAR_H * 0.68)), "EarBase_" + tag),
             ("Ear2_" + tag, Vector((0, 0, EAR_H * 0.68)), Vector((0, 0, EAR_H * 0.97)), "Ear1_" + tag),
             ("EarTip_" + tag, Vector((0, 0, EAR_H * 0.97)), Vector((0, 0, EAR_H * 1.12)), "Ear2_" + tag)]
    arm = make_armature(f"ear_rig_{tag}", bones)
    bnames = [b[0] for b in bones]
    # outer weights
    for o, fr in ((outer, vfrac), (inner, ivfrac)):
        for bn in bnames:
            o.vertex_groups.new(name=bn)
        for vtx in o.data.vertices:
            for bi, w in tri_weights(fr[vtx.index], EAR_CENTRES):
                o.vertex_groups[bnames[bi]].add([vtx.index], w, 'REPLACE')
        mod = o.modifiers.new("Armature", 'ARMATURE')
        mod.object = arm
        o.parent = arm
    assign_material(outer, fur_mat)
    inner_mat = make_material("inner_ear", 0.75)
    assign_material(inner, inner_mat)
    export_obj([outer, inner], arm,
               os.path.join(OUT, f"ear_canine_upright_{tag}.glb"),
               os.path.join(OUT, f"ear_canine_upright_{tag}.stl"))
    ear_stats[tag] = {
        "verts": len(outer.data.vertices) + len(inner.data.vertices),
        "tris": sum(len(p.vertices) - 2 for p in outer.data.polygons)
                + sum(len(p.vertices) - 2 for p in inner.data.polygons),
        "bones": 4}
stats["ear_canine_upright"] = ear_stats

# ================================================================ HORNS
HORN_SPINE_R = [Vector(p) for p in [
    (0.0, 0.0, 0.0), (0.011, -0.026, 0.055), (0.025, -0.066, 0.100),
    (0.040, -0.104, 0.122), (0.053, -0.134, 0.122), (0.062, -0.154, 0.104),
    (0.067, -0.163, 0.082)]]
HORN_R = [(0.0, 0.0245), (0.2, 0.0215), (0.45, 0.0168), (0.7, 0.0118),
          (0.88, 0.0072), (1.0, 0.0016)]

def horn_color(t, phi):
    base = (0.55, 0.47, 0.37)
    tip = (0.20, 0.16, 0.12)
    c = tuple(base[i] + (tip[i] - base[i]) * (t ** 1.4) for i in range(3))
    return c

def horn_radius(t, phi):
    r = lerp_profile(HORN_R, t)
    r *= 1.0 + 0.038 * math.sin(t * math.pi * 15.0) * (1.0 - t)   # growth annuli
    return r

horn_objs = []
horn_total = {"verts": 0, "tris": 0}
for side, tag in ((1, "R"), (-1, "L")):
    spine = [Vector((side * p.x, p.y, p.z)) for p in HORN_SPINE_R]
    # elliptical base: scale ring x by 1.18 via custom radius in x? tube is
    # circular; approximate ellipse by scaling finished mesh x1.15 at base rows
    obj, rts = tube(f"horn_{tag}", spine, 15, 10, horn_radius, color_fn=horn_color)
    # pair spacing: each horn's base sits 36 mm off the skull midline, so
    # the pair file's origin is the midpoint between the two bases.
    # Baked into geometry so every exporter sees the shipped frame.
    for v in obj.data.vertices:
        v.co.x += side * 0.036
    horn_mat = make_material(f"keratin_{tag}", 0.55)
    assign_material(obj, horn_mat)
    horn_objs.append(obj)
    horn_total["verts"] += len(obj.data.vertices)
    horn_total["tris"] += sum(len(p.vertices) - 2 for p in obj.data.polygons)
export_obj(horn_objs, None,
           os.path.join(OUT, "horns_curved_pair.glb"),
           os.path.join(OUT, "horns_curved_pair.stl"))
stats["horns_curved_pair"] = {**horn_total, "bones": 0}

with open(os.path.join(WORK, "stats.json"), "w") as f:
    json.dump(stats, f, indent=1)
print("B14 STATS:", json.dumps(stats, indent=1))
