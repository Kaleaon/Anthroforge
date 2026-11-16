#!/usr/bin/env python3
"""A4 — stylised fur clump library prototype.

Builds low-poly fur clumps (lathe-profile teardrop spikes with a bent
centreline, 6-sided flattened rings, flat shading) and seats them on
the neutral base head v3, in the head's own frame (metres, +Y forward
toward nose, +Z up, L = 1.0 nose->occiput).

Outputs (in ../parts/):
  fur_cheek_tufts.glb / .stl     pair, 3 clumps per side
  fur_ear_tufts.glb / .stl       pair, 2 clumps per ear
  fur_chest_ruff.glb / .stl      5-clump fan
  fur_tail_clumps.glb / .stl     6 clumps, local tail frame (origin at
                                 tail.base, -Y posterior, +Z up)
  tail_core_proxy.stl            reference base the tail set scores vs
  head_base.stl                  TissueHead+Jaw union, for fit scoring
  fur_clumps_demo.blend          head + all head parts seated
Run: blender -b --python build_clumps.py
"""
import bpy, math, json, os
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "parts"))
HEAD_GLB = "/home/hatch/workspace/anthroforge-v2/base-head-v3/neutral_base_head_v3.glb"

# ---------------------------------------------------------------- clump
# Ring profile: (t, radius factor). Plump base, long taper, sharp tip.
PROFILE = [(0.00, 0.62), (0.18, 1.00), (0.42, 0.86),
           (0.68, 0.55), (0.88, 0.24), (1.00, 0.00)]
SIDES = 6

def profile_r(t):
    for (t0, r0), (t1, r1) in zip(PROFILE, PROFILE[1:]):
        if t <= t1:
            u = 0.0 if t1 == t0 else (t - t0) / (t1 - t0)
            return r0 + (r1 - r0) * u
    return 0.0

def clump_mesh(name, length, base_r, flat=0.60, bend=0.38, twist_deg=14.0):
    """One clump in local space: root at origin, axis +Y, tip at +Y*length.
    Bend droops the centreline toward -Z (quadratically); cross-sections
    are flattened ellipses (minor axis = Z, the bend plane) so the clump
    reads as a blade, wide across the flow, thin along it."""
    verts, faces = [], []
    ring_start = []
    for i, (t, _rf) in enumerate(PROFILE):
        r = base_r * profile_r(t)
        cy = t * length
        cz = -bend * length * 0.42 * t * t
        if t >= 1.0:  # tip: single point
            ring_start.append(len(verts))
            verts.append((0.0, cy, cz))
            continue
        ring_start.append(len(verts))
        tw = math.radians(twist_deg) * t
        for j in range(SIDES):
            a = 2 * math.pi * j / SIDES + tw
            verts.append((r * math.cos(a), cy, cz + r * math.sin(a) * flat))
    # base centre, recessed so the root seats like a shallow cone
    base_c = len(verts)
    verts.append((0.0, -0.18 * base_r, 0.0))
    n_rings = len(PROFILE)
    for i in range(n_rings - 1):
        a0, b0 = ring_start[i], ring_start[i + 1]
        if PROFILE[i + 1][0] >= 1.0:  # fan into tip
            for j in range(SIDES):
                faces.append((a0 + j, a0 + (j + 1) % SIDES, b0))
        else:
            for j in range(SIDES):
                j1 = (j + 1) % SIDES
                faces.append((a0 + j, b0 + j, b0 + j1))
                faces.append((a0 + j, b0 + j1, a0 + j1))
    for j in range(SIDES):  # base fan
        faces.append((base_c, ring_start[0] + (j + 1) % SIDES, ring_start[0] + j))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    return me

def place(mesh, name, origin, direction, roll_deg=0.0):
    """Create object from clump mesh, oriented so local +Y -> direction."""
    ob = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(ob)
    d = Vector(direction).normalized()
    q = Vector((0, 1, 0)).rotation_difference(d)
    if roll_deg:
        q = q @ __import__('mathutils').Quaternion(d, math.radians(roll_deg))
    ob.rotation_mode = 'QUATERNION'
    ob.rotation_quaternion = q
    ob.location = Vector(origin)
    return ob

def join_objects(obs, name):
    bpy.ops.object.select_all(action='DESELECT')
    for ob in obs:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = obs[0]
    bpy.ops.object.join()
    joined = bpy.context.view_layer.objects.active
    joined.name = name
    # apply transforms so the part ships in its seating frame
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return joined

MAT = None
def fur_material():
    global MAT
    if MAT is None:
        MAT = bpy.data.materials.new("FurClump_Stylised")
        MAT.use_nodes = True
        bsdf = MAT.node_tree.nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = (0.40, 0.32, 0.26, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.92
    return MAT

def finish_part(ob, name):
    ob.data.materials.append(fur_material())
    for p in ob.data.polygons:
        p.use_smooth = False  # flat shading: graphic clump read
    counts = dict(name=name, verts=len(ob.data.vertices),
                  tris=sum(1 for p in ob.data.polygons if len(p.vertices) == 3)
                       + 2 * sum(1 for p in ob.data.polygons if len(p.vertices) == 4))
    return counts

# ---------------------------------------------------------------- scene
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=HEAD_GLB)
head_obs = [ob for ob in bpy.data.objects if ob.type == 'MESH']
stats = {}

# ---- cheek tufts: fan of 3 per side, descending the jaw side ---------
cheek_specs = [  # origin (right side), direction, length, base_r, bend
    ((0.238, -0.015, -0.030), (0.30, -0.35, -0.89), 0.150, 0.046, 0.30),
    ((0.248, -0.085, -0.075), (0.28, -0.55, -0.79), 0.195, 0.056, 0.38),
    ((0.238, -0.150, -0.120), (0.22, -0.78, -0.58), 0.160, 0.048, 0.42),
]
obs = []
for side in (1, -1):
    sname = 'R' if side > 0 else 'L'
    for i, (org, dirv, ln, br, bd) in enumerate(cheek_specs):
        me = clump_mesh(f"cheek_{sname}{i}", ln, br, bend=bd)
        obs.append(place(me, f"cheek_{sname}{i}",
                         (org[0] * side, org[1], org[2]),
                         (dirv[0] * side, dirv[1], dirv[2])))
cheek = join_objects(obs, "fur_cheek_tufts")
stats['fur_cheek_tufts'] = finish_part(cheek, "fur_cheek_tufts")

# ---- ear tufts: 2 per ear, rooted in the bowl, pointing up-in --------
ear_specs = [
    ((0.268, -0.180, 0.055), (-0.25, -0.05, 0.97), 0.125, 0.030, 0.18),
    ((0.292, -0.148, 0.095), (-0.38, 0.06, 0.92), 0.098, 0.024, 0.22),
]
obs = []
for side in (1, -1):
    sname = 'R' if side > 0 else 'L'
    for i, (org, dirv, ln, br, bd) in enumerate(ear_specs):
        me = clump_mesh(f"eartuft_{sname}{i}", ln, br, bend=bd)
        obs.append(place(me, f"eartuft_{sname}{i}",
                         (org[0] * side, org[1], org[2]),
                         (dirv[0] * side, dirv[1], dirv[2])))
eartuft = join_objects(obs, "fur_ear_tufts")
stats['fur_ear_tufts'] = finish_part(eartuft, "fur_ear_tufts")

# ---- chest ruff: 5-clump fan under the jaw/neck front ----------------
ruff_specs = [  # throat fan: roots under the chin/throat line, hanging
    ((0.000, 0.060, -0.295), (0.00, -0.05, -0.99), 0.200, 0.058, 0.40),
    ((0.085, -0.020, -0.295), (0.18, -0.20, -0.96), 0.185, 0.050, 0.40),
    ((-0.085, -0.020, -0.295), (-0.18, -0.20, -0.96), 0.185, 0.050, 0.40),
    ((0.155, -0.100, -0.275), (0.40, -0.30, -0.86), 0.155, 0.042, 0.36),
    ((-0.155, -0.100, -0.275), (-0.40, -0.30, -0.86), 0.155, 0.042, 0.36),
]
obs = []
for i, (org, dirv, ln, br, bd) in enumerate(ruff_specs):
    me = clump_mesh(f"ruff_{i}", ln, br, bend=bd)
    obs.append(place(me, f"ruff_{i}", org, dirv))
ruff = join_objects(obs, "fur_chest_ruff")
stats['fur_chest_ruff'] = finish_part(ruff, "fur_chest_ruff")

# ---- tail clump set + proxy core (local tail frame) ------------------
SPINE = [(0, 0.00, 0.020), (0, -0.18, 0.052), (0, -0.36, 0.018), (0, -0.52, -0.058)]
def spine_point(t):
    # piecewise-linear along SPINE
    segs = len(SPINE) - 1
    ft = min(max(t, 0.0), 0.9999) * segs
    i = int(ft); u = ft - i
    a, b = SPINE[i], SPINE[i + 1]
    return Vector(tuple(a[k] + (b[k] - a[k]) * u for k in range(3)))
def spine_dir(t):
    i = min(int(min(max(t, 0.0), 0.9999) * (len(SPINE) - 1)), len(SPINE) - 2)
    return (Vector(SPINE[i + 1]) - Vector(SPINE[i])).normalized()

# proxy core: tube along spine, radius 0.046 -> 0.020
core_verts, core_faces = [], []
RADII = [0.046, 0.044, 0.036, 0.020]
for i, p in enumerate(SPINE):
    d = spine_dir(min(i / (len(SPINE) - 1), 0.99))
    side = Vector((1, 0, 0))
    up = d.cross(side).normalized() if abs(d.dot(side)) < 0.99 else Vector((0, 0, 1))
    for j in range(8):
        a = 2 * math.pi * j / 8
        off = side * math.cos(a) * RADII[i] + up * math.sin(a) * RADII[i]
        core_verts.append(tuple(Vector(p) + off))
for i in range(len(SPINE) - 1):
    for j in range(8):
        j1 = (j + 1) % 8
        core_faces.append((i * 8 + j, (i + 1) * 8 + j, (i + 1) * 8 + j1))
        core_faces.append((i * 8 + j, (i + 1) * 8 + j1, i * 8 + j1))
core_me = bpy.data.meshes.new("tail_core_proxy")
core_me.from_pydata(core_verts, [], core_faces)
core_me.update()
core = bpy.data.objects.new("tail_core_proxy", core_me)
bpy.context.collection.objects.link(core)

def core_radius(t):
    ft = min(max(t, 0.0), 0.9999) * (len(RADII) - 1)
    i = int(ft); u = ft - i
    return RADII[i] + (RADII[i + 1] - RADII[i]) * u

tail_specs = [  # spine t, hang direction (local), length, base_r, bend
    (0.10, (0.00, -0.35, -0.94), 0.150, 0.052, 0.35),
    (0.34, (0.00, -0.30, -0.95), 0.185, 0.062, 0.38),
    (0.58, (0.00, -0.38, -0.92), 0.175, 0.058, 0.38),
    (0.80, (0.00, -0.55, -0.83), 0.155, 0.048, 0.34),
    (0.30, (0.55, -0.45, 0.72), 0.120, 0.040, 0.25),   # side/top filler
    (0.55, (-0.55, -0.45, 0.72), 0.120, 0.040, 0.25),  # side/top filler
]
# inner layer: short clumps rooted on the core surface, hugging the
# spine direction — real fur sets layer short-under / long-over, and
# the inner layer is what surface-engagement measures.
inner_specs = [
    (0.14, (0.22, -0.93, -0.30), 0.072, 0.036, 0.18),
    (0.30, (-0.22, -0.93, -0.30), 0.074, 0.037, 0.18),
    (0.46, (0.20, -0.94, -0.28), 0.072, 0.035, 0.18),
    (0.62, (-0.20, -0.94, -0.28), 0.070, 0.033, 0.18),
    (0.76, (0.14, -0.95, -0.26), 0.066, 0.030, 0.18),
    (0.24, (0.00, -0.88, 0.42), 0.070, 0.034, 0.16),   # top, swept back-up
    (0.38, (0.00, -0.90, -0.40), 0.072, 0.034, 0.18),  # underside mid
    (0.68, (0.00, -0.92, -0.36), 0.068, 0.031, 0.18),  # underside rear
]
obs = []
for i, (t, dirv, ln, br, bd) in enumerate(tail_specs):
    root = spine_point(t) + Vector(dirv).normalized() * (core_radius(t) - 0.010)
    me = clump_mesh(f"tailclump_{i}", ln, br, bend=bd)
    obs.append(place(me, f"tailclump_{i}", tuple(root), dirv))
for i, (t, dirv, ln, br, bd) in enumerate(inner_specs):
    root = spine_point(t) + Vector(dirv).normalized() * (core_radius(t) - 0.008)
    me = clump_mesh(f"tailinner_{i}", ln, br, bend=bd)
    obs.append(place(me, f"tailinner_{i}", tuple(root), dirv))
tail = join_objects(obs, "fur_tail_clumps")
stats['fur_tail_clumps'] = finish_part(tail, "fur_tail_clumps")

# ---------------------------------------------------------------- saves
os.makedirs(OUT, exist_ok=True)
def export_glb(ob, path):
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB',
                              use_selection=True, export_apply=True)
def export_stl(ob, path):
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.wm.stl_export(filepath=path, export_selected_objects=True)

for ob, nm in ((cheek, 'fur_cheek_tufts'), (eartuft, 'fur_ear_tufts'),
               (ruff, 'fur_chest_ruff'), (tail, 'fur_tail_clumps')):
    export_glb(ob, os.path.join(OUT, nm + '.glb'))
    export_stl(ob, os.path.join(OUT, nm + '.stl'))
export_stl(core, os.path.join(OUT, 'tail_core_proxy.stl'))

# per-socket-assembly base STLs for fit scoring (PARTS_STANDARD §5.1:
# bases are unioned per socket assembly, not per file)
def export_base(names, fname):
    bpy.ops.object.select_all(action='DESELECT')
    for ob in head_obs:
        if ob.name in names:
            ob.select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects[names[0]]
    bpy.ops.wm.stl_export(filepath=os.path.join(OUT, fname),
                          export_selected_objects=True)
export_base(('TissueHead', 'Jaw'), 'head_base.stl')
export_base(('TissueHead', 'Jaw', 'Ear_L', 'Ear_R'), 'head_base_ears.stl')
export_base(('TissueHead', 'Jaw', 'NeckSocket'), 'head_base_ruff.stl')

# tail demo: core + clumps together
core.hide_render = False
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'fur_clumps_demo.blend'))
print("STATS " + json.dumps(stats))
