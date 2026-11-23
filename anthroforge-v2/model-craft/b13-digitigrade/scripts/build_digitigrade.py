#!/usr/bin/env python3
"""
B13 — digitigrade leg pair for AnthroForge (PARTS_STANDARD socket leg.digi.L/R).

Run: HOME=/tmp/af_home xvfb-run -a ~/workspace/tools/blender/current/blender \
       -b --python build_digitigrade.py

Canonical frame: metres, x = character right, y = front, z = up, floor z=0.
Blender conversion: (x, -y, z).

Joint design (right leg; left mirrored in x). Hip height and pelvis dims
measured from the hm08 reference base (see DIGITIGRADE.md):
  Hip joint  H = (0.098,  0.000, 0.802)
  Stifle     K = (0.100,  0.070, 0.497)   femur 0.313 m
  Hock       A = (0.102, -0.032, 0.268)   tibia 0.251 m
  MTP        M = (0.102,  0.030, 0.052)   metatarsus 0.225 m
  Toe tip    T = (0.102,  0.118, 0.014)   toes ~0.096 m
Standing interior angles: stifle ~143 deg, hock ~140 deg
(sourced dog bands: stifle 135-140, hock 140-150; anthro upright opens
the stifle slightly -- documented in DIGITIGRADE.md).
Segment split femur/tibia/metatarsus = 39.6 / 31.8 / 28.5 % of the
three-bone chain (canine sourced ~41/30/29, Schmieder 2000 + breed
structure data; see DIGITIGRADE.md).
"""
import json
import math
import os

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
PARTS = os.path.join(OUT, "parts")
RENDERS = os.path.join(OUT, "renders")
WORK = os.path.join(OUT, "work")
for d in (PARTS, RENDERS, WORK):
    os.makedirs(d, exist_ok=True)

# ---------------------------------------------------------------- joints
JOINTS = {  # right leg, canonical (x, y_front, z_up)
    "hip":  (0.098,  0.000, 0.802),
    "knee": (0.100,  0.070, 0.497),
    "ankle": (0.102, -0.032, 0.268),   # anatomical hock (tarsus)
    "mtp":  (0.102,  0.030, 0.052),
    "toe":  (0.102,  0.118, 0.014),
}


def cb(p, side=1):
    """canonical -> blender coords, with side mirror."""
    return Vector((side * p[0], -p[1], p[2]))


def vsub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def vlen(a):
    return math.sqrt(a[0] ** 2 + a[1] ** 2 + a[2] ** 2)


def vnorm(a):
    l = vlen(a) or 1.0
    return (a[0] / l, a[1] / l, a[2] / l)


# ---------------------------------------------------------------- lofting
def ring_points(centre, tangent, width, depth, n=16, front_bias=0.0):
    """Ellipse ring in the plane perpendicular to tangent.
    front_bias: >0 shifts cross-section mass forward (quad), <0 back (calf)
    by scaling the front/back radii asymmetrically."""
    t = vnorm(tangent)
    # lateral axis: world x projected out of tangent
    lat = (1.0, 0.0, 0.0)
    d = lat[0] * t[0] + lat[1] * t[1] + lat[2] * t[2]
    lat = (lat[0] - d * t[0], lat[1] - d * t[1], lat[2] - d * t[2])
    if vlen(lat) < 1e-6:
        lat = (0.0, 1.0, 0.0)
        d = lat[0] * t[0] + lat[1] * t[1] + lat[2] * t[2]
        lat = (lat[0] - d * t[0], lat[1] - d * t[1], lat[2] - d * t[2])
    lat = vnorm(lat)
    # front axis = tangent x lateral  (right-handed: lat x front = ? ) use cross
    fr = (t[1] * lat[2] - t[2] * lat[1],
          t[2] * lat[0] - t[0] * lat[2],
          t[0] * lat[1] - t[1] * lat[0])
    if fr[1] < 0:  # ensure front axis points +y (character front)
        fr = (-fr[0], -fr[1], -fr[2])
    pts = []
    for i in range(n):
        th = 2 * math.pi * i / n
        c, s = math.cos(th), math.sin(th)
        rw = width / 2.0
        rd = depth / 2.0
        if s > 0:
            rd *= (1.0 + front_bias)
        else:
            rd *= (1.0 - front_bias)
        p = (centre[0] + lat[0] * c * rw + fr[0] * s * rd,
             centre[1] + lat[1] * c * rw + fr[1] * s * rd,
             centre[2] + lat[2] * c * rw + fr[2] * s * rd)
        pts.append(p)
    return pts


def loft(stations, n=16, cap_start=True, cap_end=True):
    """stations: list of dicts {c: centre, t: tangent, w, d, fb}
    Returns (verts, faces) as a tube with optional ngon caps."""
    rings = []
    verts = []
    for st in stations:
        ring = ring_points(st["c"], st["t"], st["w"], st["d"], n,
                           st.get("fb", 0.0))
        rings.append(ring)
        verts.extend(ring)
    faces = []
    nr = len(rings)
    for r in range(nr - 1):
        for i in range(n):
            a = r * n + i
            b = r * n + (i + 1) % n
            c2 = (r + 1) * n + (i + 1) % n
            d2 = (r + 1) * n + i
            faces.append((a, b, c2, d2))
    if cap_start:
        ci = len(verts)
        c0 = stations[0]["c"]
        verts.append(c0)
        for i in range(n):
            faces.append((ci, (i + 1) % n, i))
    if cap_end:
        ci = len(verts)
        verts.append(stations[-1]["c"])
        base = (nr - 1) * n
        for i in range(n):
            faces.append((ci, base + i, base + (i + 1) % n))
    return verts, faces


def seg_stations(p0, p1, profile):
    """profile: list of (frac, width, depth, front_bias) along p0->p1."""
    d = vsub(p1, p0)
    sts = []
    for fr, w, dep, fb in profile:
        c = (p0[0] + d[0] * fr, p0[1] + d[1] * fr, p0[2] + d[2] * fr)
        sts.append({"c": c, "t": d, "w": w, "d": dep, "fb": fb})
    return sts


# ------------------------------------------------------- leg construction
def build_leg_geometry():
    """Returns (verts_canonical, faces, vert_station_tags).
    Tags record which chain zone each vertex belongs to, for weighting:
    ('seg', seg_index, frac_along_total_chain)."""
    H, K, A, M, T = (JOINTS["hip"], JOINTS["knee"], JOINTS["ankle"],
                     JOINTS["mtp"], JOINTS["toe"])
    # Mirror-once rule (fix, Nov 12 2026): geometry is ALWAYS built in
    # right-leg canonical space; the single x-mirror for the left leg
    # happens in cb() at Blender conversion. Do NOT negate joints here --
    # the original code did, and cb() then mirrored a second time,
    # cancelling it (the shipped "pair" was two right legs; see
    # DIGITIGRADE.md s.7 debit 1 / s.9).
    # skirt above hip: two stations rising into the pelvis volume
    skirt_top = (H[0], H[1] - 0.005, H[2] + 0.075)
    thigh = seg_stations(skirt_top, K, [
        (0.00, 0.205, 0.215, 0.00),   # skirt flare (seats in pelvis)
        (0.18, 0.188, 0.200, 0.02),   # skirt_mid ~ hip+0.035
        (0.32, 0.170, 0.188, 0.05),   # hip joint level
        (0.52, 0.174, 0.194, 0.08),   # quad/ham bulge
        (0.72, 0.150, 0.168, 0.05),
        (0.90, 0.124, 0.140, 0.02),
        (1.00, 0.106, 0.122, 0.00),   # stifle
    ])
    # fracs are along skirt_top->K; hip joint sits at frac ~0.19
    shin = seg_stations(K, A, [
        (0.06, 0.102, 0.126, -0.10),
        (0.28, 0.090, 0.120, -0.16),  # gastrocnemius high, back-biased
        (0.55, 0.070, 0.090, -0.08),
        (0.80, 0.057, 0.071, -0.02),
        (1.00, 0.052, 0.064, 0.00),   # hock
    ])
    meta = seg_stations(A, M, [
        (0.10, 0.050, 0.060, 0.00),
        (0.45, 0.044, 0.052, 0.00),   # lean tendinous shaft
        (0.78, 0.047, 0.053, 0.02),
        (1.00, 0.060, 0.057, 0.04),   # MTP knuckle spread
    ])
    paw = seg_stations(M, T, [
        (0.25, 0.068, 0.052, 0.00),
        (0.60, 0.074, 0.040, 0.00),   # paw spreads, flattens
        (1.00, 0.072, 0.030, 0.00),   # toe bases
    ])
    stations = thigh + shin + meta + paw
    verts, faces = loft(stations, n=16, cap_start=True, cap_end=False)
    # station arc positions for weighting: cumulative chord lengths
    centres = [st["c"] for st in stations]
    arc = [0.0]
    for i in range(1, len(centres)):
        arc.append(arc[-1] + vlen(vsub(centres[i], centres[i - 1])))
    tags = []
    nring = 16
    for ri, st in enumerate(stations):
        for _ in range(nring):
            tags.append(arc[ri])
    tags.append(arc[0])  # start cap centre
    return verts, faces, tags, arc[-1], stations


def build_toe(cx_off, fan_deg):
    """One toe: mini-loft from its MTP knuckle forward-down to the tip."""
    M = JOINTS["mtp"]
    cx = abs(M[0]) + cx_off  # side-naive: cb() applies the mirror (fix s.9)
    base = (cx, M[1] + 0.004, 0.040)
    fan = math.radians(fan_deg) * (1 if cx_off > 0 else -1 if cx_off < 0 else 0)
    dx = math.sin(fan) * 0.5
    mid = (cx + dx * 0.04, M[1] + 0.048, 0.020)
    tip = (cx + dx * 0.08, M[1] + 0.082, 0.0125)
    sts = [
        {"c": base, "t": vsub(mid, base), "w": 0.034, "d": 0.032, "fb": 0.0},
        {"c": (cx + dx * 0.02, M[1] + 0.026, 0.027), "t": vsub(mid, base),
         "w": 0.031, "d": 0.029, "fb": 0.0},
        {"c": mid, "t": vsub(tip, mid), "w": 0.027, "d": 0.025, "fb": 0.0},
        {"c": tip, "t": vsub(tip, mid), "w": 0.020, "d": 0.019, "fb": 0.0},
    ]
    verts, faces = loft(sts, n=10, cap_start=True, cap_end=True)
    return verts, faces, base, tip


def chain_weights(arc_s, joint_arcs, half=0.035):
    """Weights over the bone chain for a vertex at chain arc position s.
    joint_arcs: arc positions of the 4 interior joints (hip is arc of the
    hip joint station, then knee, ankle, mtp). Bones: 0 Hip, 1 Knee,
    2 Ankle, 3 Hock, 4 Foot."""
    bones = [0.0] * 5
    # determine segment index
    bounds = [-1e9] + joint_arcs + [1e9]
    for i in range(5):
        if bounds[i] <= arc_s < bounds[i + 1]:
            seg = i
            break
    else:
        seg = 4
    bones[seg] = 1.0
    # blend near interior joints
    for j, ja in enumerate(joint_arcs):
        d = arc_s - ja
        if abs(d) < half:
            w = 0.5 - 0.5 * (d / half)  # weight of the *upper* bone at joint
            w = w * w * (3 - 2 * w)
            lo, hi = j, j + 1
            bones[lo] = max(bones[lo] * 0, 0)  # reset handled below
            bones = [0.0] * 5
            bones[lo] = w
            bones[hi] = 1.0 - w
            break
    s = sum(bones)
    return [b / s for b in bones]


# ------------------------------------------------------------------ scene
def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def make_armature(side):
    sname = "L" if side < 0 else "R"
    H, K, A, M, T = (JOINTS["hip"], JOINTS["knee"], JOINTS["ankle"],
                     JOINTS["mtp"], JOINTS["toe"])
    # mid-metatarsus point for the Hock module bone split
    mid_meta = (A[0] + (M[0] - A[0]) * 0.45, A[1] + (M[1] - A[1]) * 0.45,
                A[2] + (M[2] - A[2]) * 0.45)
    toe_end = (T[0], T[1] + 0.03, T[2] - 0.004)
    bones = [
        (f"Hip_{sname}",   cb(H, side),  cb(K, side),  None),
        (f"Knee_{sname}",  cb(K, side),  cb(A, side),  f"Hip_{sname}"),
        (f"Ankle_{sname}", cb(A, side),  cb(mid_meta, side), f"Knee_{sname}"),
        (f"Hock_{sname}",  cb(mid_meta, side), cb(M, side), f"Ankle_{sname}"),
        (f"Foot_{sname}",  cb(M, side),  cb(toe_end, side), f"Hock_{sname}"),
    ]
    arm_data = bpy.data.armatures.new(f"DigitigradeLeg_{sname}")
    arm = bpy.data.objects.new(f"DigitigradeLeg_{sname}", arm_data)
    bpy.context.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    for name, head, tail, parent in bones:
        b = arm_data.edit_bones.new(name)
        b.head = head
        b.tail = tail
        if parent:
            b.parent = arm_data.edit_bones[parent]
    bpy.ops.object.mode_set(mode="OBJECT")
    return arm, [b[0] for b in bones]


def make_mesh(side, arm, bone_names):
    sname = "L" if side < 0 else "R"
    verts, faces, tags, total_arc, stations = build_leg_geometry()
    # joint arc positions: find arc of stations nearest each joint height
    centres = [st["c"] for st in stations]
    arc = [0.0]
    for i in range(1, len(centres)):
        arc.append(arc[-1] + vlen(vsub(centres[i], centres[i - 1])))

    def arc_at(point):
        best, bi = 1e9, 0
        for i, c in enumerate(centres):
            d = vlen(vsub(c, point))
            if d < best:
                best, bi = d, i
        return arc[bi]

    H, K, A, M = (JOINTS["hip"], JOINTS["knee"], JOINTS["ankle"],
                  JOINTS["mtp"])
    # raw right-leg joints: stations are built in right-leg space for both
    # sides now (mirror lives in cb() only) -- see build_leg_geometry.
    joint_arcs = [arc_at(H), arc_at(K), arc_at(A), arc_at(M)]

    # toes + pads + claws appended as extra geometry
    extra_verts, extra_faces = [], []
    toe_tags = []  # (bone_weights list) per extra vertex
    toe_specs = [(-0.0275, -7.0), (-0.0092, -2.5), (0.0092, 2.5), (0.0275, 7.0)]
    for cx_off, fan in toe_specs:
        tv, tf, tbase, ttip = build_toe(cx_off, fan)
        off = len(verts) + len(extra_verts)
        extra_verts.extend(tv)
        extra_faces.extend([tuple(v + off for v in f) for f in tf])
        # weight: base of toe blends Hock->Foot, tip pure Foot
        for v in tv:
            fr = (v[1] - tbase[1]) / max(ttip[1] - tbase[1], 1e-6)
            wfoot = 0.45 + 0.55 * min(max(fr, 0.0), 1.0)
            toe_tags.append([0, 0, 0, 1.0 - wfoot, wfoot])
    # main pad: flattened UV sphere under MTP
    pad_c = (0.102, 0.026, 0.017)  # side-naive (cb mirrors); fix s.9
    pad_r = (0.031, 0.027, 0.011)
    pv, pf = uv_sphere(pad_c, pad_r, 12, 8)
    off = len(verts) + len(extra_verts)
    extra_verts.extend(pv)
    extra_faces.extend([tuple(v + off for v in f) for f in pf])
    toe_tags.extend([[0, 0, 0, 0.35, 0.65]] * len(pv))
    # toe pads
    for cx_off, fan in toe_specs:
        tc = ((0.102 + cx_off), 0.052, 0.0105)  # side-naive; fix s.9
        pv, pf = uv_sphere(tc, (0.0115, 0.0135, 0.006), 10, 6)
        off = len(verts) + len(extra_verts)
        extra_verts.extend(pv)
        extra_faces.extend([tuple(v + off for v in f) for f in pf])
        toe_tags.extend([[0, 0, 0, 0.1, 0.9]] * len(pv))
    # claws: small cones at toe tips
    for cx_off, fan in toe_specs:
        tip = ((0.102 + cx_off) + math.sin(math.radians(fan)) * 0.04,
               0.030 + 0.082, 0.0125)  # side-naive; fix s.9
        cv_, cf = cone(tip, (0.0, 0.75, -0.45), 0.020, 0.0058, 8)
        off = len(verts) + len(extra_verts)
        extra_verts.extend(cv_)
        extra_faces.extend([tuple(v + off for v in f) for f in cf])
        toe_tags.extend([[0, 0, 0, 0.0, 1.0]] * len(cv_))

    all_verts = verts + extra_verts
    all_faces = faces + extra_faces
    if side < 0:
        # cb() bakes exactly one x-mirror into the left leg's verts; a
        # baked mirror reverses triangle orientation, so flip face order
        # to restore the right leg's outward winding/normals (the buggy
        # double-mirrored L shipped with inward normals; fix s.9).
        all_faces = [tuple(reversed(f)) for f in all_faces]
    weights = []
    for s in tags:
        weights.append(chain_weights(s, joint_arcs))
    weights.extend(toe_tags)

    mesh = bpy.data.meshes.new(f"leg_digitigrade_{sname}")
    mesh.from_pydata([tuple(cb(p, side)) for p in all_verts], [], all_faces)
    mesh.update()
    for p in mesh.polygons:
        p.use_smooth = True
    obj = bpy.data.objects.new(f"leg_digitigrade_{sname}", mesh)
    bpy.context.collection.objects.link(obj)
    for bi, bname in enumerate(bone_names):
        vg = obj.vertex_groups.new(name=bname)
        for vi, w in enumerate(weights):
            if w[bi] > 0.001:
                vg.add([vi], w[bi], "REPLACE")
    mod = obj.modifiers.new("Armature", "ARMATURE")
    mod.object = arm
    obj.parent = arm
    return obj, {"verts": len(all_verts), "tris": sum(len(f) - 2 for f in all_faces),
                 "joint_arcs": joint_arcs, "total_arc": total_arc}


def uv_sphere(centre, radii, nu=12, nv=8):
    verts, faces = [], []
    for j in range(nv + 1):
        phi = math.pi * j / nv
        for i in range(nu):
            th = 2 * math.pi * i / nu
            verts.append((centre[0] + radii[0] * math.sin(phi) * math.cos(th),
                          centre[1] + radii[1] * math.sin(phi) * math.sin(th),
                          centre[2] + radii[2] * math.cos(phi)))
    for j in range(nv):
        for i in range(nu):
            a = j * nu + i
            b = j * nu + (i + 1) % nu
            c2 = (j + 1) * nu + (i + 1) % nu
            d2 = (j + 1) * nu + i
            faces.append((a, b, c2, d2))
    return verts, faces


def cone(tip_base, direction, length, radius, n=8):
    d = vnorm(direction)
    # ring at base, apex at tip_base + d*length ; base centre at tip_base
    lat = (1.0, 0.0, 0.0)
    dd = lat[0] * d[0] + lat[1] * d[1] + lat[2] * d[2]
    lat = vnorm((lat[0] - dd * d[0], lat[1] - dd * d[1], lat[2] - dd * d[2]))
    fr = (d[1] * lat[2] - d[2] * lat[1], d[2] * lat[0] - d[0] * lat[2],
          d[0] * lat[1] - d[1] * lat[0])
    verts = []
    for i in range(n):
        th = 2 * math.pi * i / n
        verts.append((tip_base[0] + (lat[0] * math.cos(th) + fr[0] * math.sin(th)) * radius,
                      tip_base[1] + (lat[1] * math.cos(th) + fr[1] * math.sin(th)) * radius,
                      tip_base[2] + (lat[2] * math.cos(th) + fr[2] * math.sin(th)) * radius))
    apex = (tip_base[0] + d[0] * length, tip_base[1] + d[1] * length,
            tip_base[2] + d[2] * length)
    verts.append(apex)
    faces = [(i, (i + 1) % n, n) for i in range(n)]
    return verts, faces


# ----------------------------------------------------------------- pelvis stub (renders only)
def make_pelvis_stub():
    pv, pf = uv_sphere((0.0, 0.002, 0.875), (0.191, 0.118, 0.145), 20, 12)
    mesh = bpy.data.meshes.new("pelvis_stub")
    mesh.from_pydata([tuple(cb(p)) for p in pv], [], pf)
    mesh.update()
    for p in mesh.polygons:
        p.use_smooth = True
    obj = bpy.data.objects.new("pelvis_stub", mesh)
    bpy.context.collection.objects.link(obj)
    mat = bpy.data.materials.new("stub_mat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.42, 0.36, 0.33, 1)
    bsdf.inputs["Roughness"].default_value = 0.9
    obj.data.materials.append(mat)
    return obj


def setup_render(objs):
    for o in objs:
        mat = bpy.data.materials.new("leg_mat")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        bsdf.inputs["Base Color"].default_value = (0.55, 0.47, 0.42, 1)
        bsdf.inputs["Roughness"].default_value = 0.85
        o.data.materials.append(mat)
    # ground
    bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 0, 0))
    gnd = bpy.context.active_object
    gm = bpy.data.materials.new("ground_mat")
    gm.use_nodes = True
    gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.16, 0.16, 0.17, 1)
    gm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 1.0
    gnd.data.materials.append(gm)
    # sun + fill
    ld = bpy.data.lights.new("sun", "SUN")
    ld.energy = 3.0
    lo = bpy.data.objects.new("sun", ld)
    bpy.context.collection.objects.link(lo)
    lo.rotation_euler = (math.radians(55), 0, math.radians(35))
    ld2 = bpy.data.lights.new("fill", "AREA")
    ld2.energy = 250
    lo2 = bpy.data.objects.new("fill", ld2)
    bpy.context.collection.objects.link(lo2)
    lo2.location = (-1.6, -1.4, 1.2)
    lo2.rotation_euler = (math.radians(70), 0, math.radians(-50))
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.samples = 48
    sc.cycles.use_denoising = False
    sc.render.resolution_x = 700
    sc.render.resolution_y = 860
    sc.world = bpy.data.worlds.new("w")
    sc.world.use_nodes = True
    sc.world.node_tree.nodes["Background"].inputs[0].default_value = (0.05, 0.05, 0.06, 1)
    sc.world.node_tree.nodes["Background"].inputs[1].default_value = 0.6


def render(cam_loc, cam_target, path):
    cd = bpy.data.cameras.new("cam")
    cam = bpy.data.objects.new("cam", cd)
    bpy.context.collection.objects.link(cam)
    cam.location = cam_loc
    direction = Vector(cam_target) - Vector(cam_loc)
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    cd.lens = 42
    bpy.context.scene.camera = cam
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam, do_unlink=True)


def pose_stride(arm_l, arm_r):
    """One stride: left leg swung forward (hip flex), right leg trailing."""
    def setrot(arm, bone, deg):
        pb = arm.pose.bones[bone]
        pb.rotation_mode = "XYZ"
        pb.rotation_euler = (math.radians(deg), 0, 0)
    # Blender pose rotation about local X: sign tuned so + swings forward(-y blender)
    setrot(arm_l, "Hip_L", -24)
    setrot(arm_l, "Knee_L", 30)
    setrot(arm_l, "Ankle_L", -18)
    setrot(arm_l, "Hock_L", -6)
    setrot(arm_l, "Foot_L", 22)
    setrot(arm_r, "Hip_R", 16)
    setrot(arm_r, "Knee_R", 8)
    setrot(arm_r, "Ankle_R", 12)
    setrot(arm_r, "Hock_R", 14)
    setrot(arm_r, "Foot_R", -28)  # trailing toe-off
    bpy.context.view_layer.update()


def reset_pose(arm):
    for pb in arm.pose.bones:
        pb.rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()


def main():
    clear_scene()
    arm_r, bones_r = make_armature(1)
    arm_l, bones_l = make_armature(-1)
    obj_r, info_r = make_mesh(1, arm_r, bones_r)
    obj_l, info_l = make_mesh(-1, arm_l, bones_l)
    print("LEG INFO R:", json.dumps(info_r))
    print("LEG INFO L:", json.dumps(info_l))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(PARTS, "legs_digitigrade.blend"))

    # --- exports (bind pose) ---
    def export(path, objs):
        bpy.ops.object.select_all(action="DESELECT")
        for o in objs:
            o.select_set(True)
        bpy.context.view_layer.objects.active = objs[0]
        bpy.ops.export_scene.gltf(filepath=path, export_format="GLB",
                                  use_selection=True, export_skins=True,
                                  export_apply=False)
    export(os.path.join(PARTS, "legs_digitigrade_pair.glb"),
           [obj_r, arm_r, obj_l, arm_l])
    export(os.path.join(PARTS, "legs_digitigrade.R.glb"), [obj_r, arm_r])
    export(os.path.join(PARTS, "legs_digitigrade.L.glb"), [obj_l, arm_l])
    # OBJ of right leg for fit scoring
    bpy.ops.object.select_all(action="DESELECT")
    obj_r.select_set(True)
    bpy.context.view_layer.objects.active = obj_r
    bpy.ops.wm.obj_export(filepath=os.path.join(WORK, "leg_R.obj"),
                          export_selected_objects=True, apply_modifiers=False)

    # --- renders ---
    make_pelvis_stub()
    setup_render([obj_r, obj_l])
    render((1.35, -1.5, 0.75), (0, 0, 0.45),
           os.path.join(RENDERS, "standing_threequarter.png"))
    render((1.7, -0.25, 0.55), (0, 0, 0.45),
           os.path.join(RENDERS, "standing_side.png"))
    pose_stride(arm_l, arm_r)
    render((1.7, -0.25, 0.55), (0, 0.02, 0.45),
           os.path.join(RENDERS, "stride_side.png"))
    render((1.35, -1.5, 0.75), (0, 0.02, 0.45),
           os.path.join(RENDERS, "stride_threequarter.png"))
    reset_pose(arm_l)
    reset_pose(arm_r)
    info = {"R": info_r, "L": info_l,
            "joints": {k: list(v) for k, v in JOINTS.items()}}
    with open(os.path.join(WORK, "build_info.json"), "w") as f:
        json.dump(info, f, indent=1)
    print("DONE")


if __name__ == "__main__":
    main()
