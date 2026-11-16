#!/usr/bin/env python3
"""B11 hands & feet build — AnthroForge model-craft wave.

Builds two socket-ready class-A parts procedurally (lofted forms):
  * paw_hand_r        — anthro paw-hand, socket arm.R, anchor Wrist_R
  * paw_foot_digi_r   — digitigrade paw-foot, socket leg.digi.R, anchor Ankle_R

Frame: Blender Z-up, metres. Right-side parts; medial = -X;
hand fingers +Y, palm -Z; foot toes +Y, plantar -Z, ground z=0.

Run: blender -b --python build_hands_feet.py
Outputs (../parts, ../work): .blend, two .glb, STLs for fit scoring.
"""
import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, ".."))
PARTS = os.path.join(OUT, "parts")

# ---------------------------------------------------------------- materials
def make_mat(name, rgb, rough=0.85):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    return m

MAT_COAT = MAT_PAD = MAT_CLAW = None

def init_materials():
    global MAT_COAT, MAT_PAD, MAT_CLAW
    MAT_COAT = make_mat("Coat", (0.36, 0.29, 0.22))
    MAT_PAD = make_mat("Pad", (0.07, 0.06, 0.06), 0.6)
    MAT_CLAW = make_mat("Claw", (0.13, 0.12, 0.11), 0.45)

# ---------------------------------------------------------------- loft core
def ring_frame(tangent):
    t = tangent.normalized()
    ref = Vector((0, 0, 1))
    right = ref.cross(t)
    if right.length < 1e-6:
        right = Vector((1, 0, 0))
    right.normalize()
    up = t.cross(right).normalized()
    return right, up

def loft(rings, n=12, cap_start=True, cap_end=True):
    """rings: list of dicts {c:Vector, rx, rz, t:Vector tangent}.
    Returns (verts, faces, ring_of_vert)."""
    verts, faces, ring_of = [], [], []
    for ri, r in enumerate(rings):
        right, up = ring_frame(r["t"])
        for k in range(n):
            a = 2 * math.pi * k / n
            p = r["c"] + right * (math.cos(a) * r["rx"]) + up * (math.sin(a) * r["rz"])
            verts.append(tuple(p))
            ring_of.append(ri)
    for ri in range(len(rings) - 1):
        for k in range(n):
            k2 = (k + 1) % n
            a, b = ri * n + k, ri * n + k2
            c, d = (ri + 1) * n + k, (ri + 1) * n + k2
            faces.append((a, c, d, b))
    if cap_start:
        c = tuple(rings[0]["c"])
        ci = len(verts); verts.append(c); ring_of.append(0)
        for k in range(n):
            faces.append((ci, (k + 1) % n, k))
    if cap_end:
        c = tuple(rings[-1]["c"])
        ci = len(verts); verts.append(c); ring_of.append(len(rings) - 1)
        base = (len(rings) - 1) * n
        for k in range(n):
            faces.append((ci, base + k, base + (k + 1) % n))
    return verts, faces, ring_of

def ellipsoid(center, radii, seg=12, rings_n=8):
    """Closed ellipsoid with true pole vertices (a naive lathe puts
    `seg` coincident verts at each pole -> a fan of degenerate tris;
    QA pass 1 caught 150-200 per part from exactly this)."""
    verts, faces = [], []
    cx, cy, cz = center
    rx, ry, rz = radii
    verts.append((cx, cy, cz + rz))  # +Z pole, index 0
    for i in range(1, rings_n):
        phi = math.pi * i / rings_n
        for k in range(seg):
            th = 2 * math.pi * k / seg
            verts.append((cx + rx * math.sin(phi) * math.cos(th),
                          cy + ry * math.sin(phi) * math.sin(th),
                          cz + rz * math.cos(phi)))
    bot = len(verts)
    verts.append((cx, cy, cz - rz))  # -Z pole
    def ring_start(i):  # i in 1..rings_n-1
        return 1 + (i - 1) * seg
    for k in range(seg):  # top fan
        faces.append((0, ring_start(1) + (k + 1) % seg, ring_start(1) + k))
    for i in range(1, rings_n - 1):
        for k in range(seg):
            k2 = (k + 1) % seg
            a, b = ring_start(i) + k, ring_start(i) + k2
            c, d = ring_start(i + 1) + k, ring_start(i + 1) + k2
            faces.append((a, c, d, b))
    last = ring_start(rings_n - 1)
    for k in range(seg):  # bottom fan
        faces.append((bot, last + k, last + (k + 1) % seg))
    return verts, faces

def cone(center, direction, length, r0, n=8):
    """Tapered claw: base ring + tip point, slight downward bend faked by
    a mid ring offset along direction with a droop."""
    center = Vector(center)
    d = direction.normalized()
    right, up = ring_frame(d)
    mid = center + d * (length * 0.55) + Vector((0, 0, -length * 0.10))
    tip = center + d * length + Vector((0, 0, -length * 0.30))
    verts, faces = [], []
    for c, r in ((center, r0), (mid, r0 * 0.55)):
        for k in range(n):
            a = 2 * math.pi * k / n
            p = c + right * (math.cos(a) * r) + up * (math.sin(a) * r)
            verts.append(tuple(p))
    for k in range(n):
        k2 = (k + 1) % n
        faces.append((k, n + k, n + k2, k2))
    ti = len(verts); verts.append(tuple(tip))
    for k in range(n):
        faces.append((n + k, ti, n + (k + 1) % n))
    ci = len(verts); verts.append(tuple(center))
    for k in range(n):
        faces.append((ci, (k + 1) % n, k))
    return verts, faces

class MeshBuilder:
    """Accumulates sub-forms into one mesh with per-vertex bone weights."""
    def __init__(self):
        self.verts, self.faces, self.weights = [], [], []
        self.fit = []  # per-vert: include in fit-score surface?

    def add(self, verts, faces, weight_fn, fit=True):
        off = len(self.verts)
        self.verts.extend(verts)
        self.faces.extend(tuple(i + off for i in f) for f in faces)
        for i in range(len(verts)):
            self.weights.append(weight_fn(i))
        self.fit.extend([fit] * len(verts))

    def build(self, name, material):
        me = bpy.data.meshes.new(name)
        me.from_pydata(self.verts, [], self.faces)
        me.update()
        for p in me.polygons:
            p.use_smooth = True
        ob = bpy.data.objects.new(name, me)
        bpy.context.collection.objects.link(ob)
        me.materials.append(material)
        return ob

def apply_weights(ob, builder_weights):
    groups = {}
    for vi, wdict in enumerate(builder_weights):
        for bone, w in wdict.items():
            if w <= 0.0:
                continue
            if bone not in groups:
                groups[bone] = ob.vertex_groups.new(name=bone)
            groups[bone].add([vi], w, "REPLACE")

def rot_x(v, deg):
    return Matrix.Rotation(math.radians(deg), 3, "X") @ v

def rot_z(v, deg):
    return Matrix.Rotation(math.radians(deg), 3, "Z") @ v

# ================================================================ PAW HAND
# Design (metres). Palm loft wrist y=0 -> MCP y~0.098.
PALM_RINGS = [
    # (y, rx, rz, zc) — wrist section kept near-oval (real wrist ~55x35 mm):
    # a flat wrist ring cannot seat into a forearm (fit-pass finding).
    (0.000, 0.030, 0.0165, 0.000),
    (0.020, 0.036, 0.0175, 0.000),
    (0.045, 0.041, 0.0155, -0.001),
    (0.070, 0.043, 0.0150, -0.001),
    (0.090, 0.041, 0.0135, 0.000),
    (0.100, 0.038, 0.0115, 0.001),
    (0.106, 0.0355, 0.0102, 0.0015),  # knuckle brow: seats finger bases deeper
]
THUMB_BASE = (-0.036, 0.032, -0.002)
THUMB_DIR = (-0.45, 0.78, -0.30)
THUMB_SEGS = [(0.032, 0.0118), (0.028, 0.0104), (0.022, 0.0092)]
# name, x, base_y, segs[(len, r)], fan_deg, curl per joint
FINGERS = [
    ("Index",  -0.0225, 0.096, [(0.042, 0.0102), (0.028, 0.0092), (0.021, 0.0080)]),
    ("Middle", -0.0075, 0.100, [(0.046, 0.0106), (0.031, 0.0096), (0.022, 0.0083)]),
    ("Ring",    0.0080, 0.098, [(0.043, 0.0102), (0.029, 0.0092), (0.021, 0.0080)]),
    ("Pinky",   0.0225, 0.092, [(0.034, 0.0088), (0.023, 0.0080), (0.018, 0.0070)]),
]
FAN = {"Index": 4.0, "Middle": 0.0, "Ring": -3.0, "Pinky": -7.0}
CURL = [7.0, 11.0, 14.0]  # relaxed flexion added at each joint

def finger_path(base, segs, fan_deg):
    """Returns list of (joint_point, direction, r_start, r_end) per segment."""
    d = rot_z(Vector((0, 1, 0)), fan_deg)
    p = Vector(base)
    out = []
    for si, (ln, r) in enumerate(segs):
        if si > 0:
            d = rot_x(d, -CURL[si])  # flexion curls toward palm (-Z)
            d.normalize()
        r_end = r * 0.88 if si < len(segs) - 1 else r * 0.55
        out.append((Vector(p), Vector(d), r, r_end))
        p = p + d * ln
    return out, p

def digit_loft(base, segs, fan_deg, n=10):
    path, tip = finger_path(base, segs, fan_deg)
    rings = []
    seg_of_ring = []
    for si, (p, d, r0, r1) in enumerate(path):
        rings.append({"c": p, "rx": r0, "rz": r0 * 0.92, "t": d})
        seg_of_ring.append(si)
        mid = p + d * (segs[si][0] * 0.55)
        rings.append({"c": mid, "rx": (r0 + r1) / 2, "rz": (r0 + r1) / 2 * 0.92, "t": d})
        seg_of_ring.append(si)
        end = p + d * segs[si][0]
        rings.append({"c": end, "rx": r1, "rz": r1 * 0.92, "t": d})
        seg_of_ring.append(si)
    verts, faces, ring_of = loft(rings, n=n)
    seg_of_vert = [seg_of_ring[r] for r in ring_of]
    return verts, faces, seg_of_vert, path, tip

def build_hand():
    mb = MeshBuilder()       # main mesh (coat)
    pads = MeshBuilder()     # pads mesh
    claws = MeshBuilder()    # claws mesh
    # ---- palm loft
    rings = [{"c": Vector((0, y, zc)), "rx": rx, "rz": rz, "t": Vector((0, 1, 0))}
             for (y, rx, rz, zc) in PALM_RINGS]
    v, f, _ = loft(rings, n=14)
    mb.add(v, f, lambda i: {"Wrist_R": 1.0})
    # thenar mound (thumb muscle) — palmar-lateral ellipsoid merged in;
    # mostly internal overlap -> excluded from the fit-score surface
    v, f = ellipsoid((-0.024, 0.034, -0.004), (0.015, 0.023, 0.0095))
    mb.add(v, f, lambda i: {"Wrist_R": 1.0}, fit=False)
    # ---- fingers
    finger_tips = {}
    for name, x, by, segs in FINGERS:
        base = (x, by, 0.001)
        v, f, seg_of, path, tip = digit_loft(base, segs, FAN[name])
        bones = [f"{name}{s+1}_R" for s in range(3)]
        def wf(i, seg_of=seg_of, bones=bones):
            s = seg_of[i]
            if s == 0:
                return {bones[0]: 1.0}
            return {bones[s]: 0.85, bones[s - 1]: 0.15}
        mb.add(v, f, wf)
        finger_tips[name] = (path, tip)
        # digital pad: underside of distal segment, sunk deep so it
        # reads as a swelling, not a stuck-on disc (render pass 1 note)
        p2, d2, _, _ = path[2]
        pad_c = p2 + d2 * segs[2][0] * 0.45 + Vector((0, 0, -segs[2][1] * 0.58))
        v2, f2 = ellipsoid(tuple(pad_c), (segs[2][1] * 0.78, segs[2][0] * 0.42, 0.0030), seg=10, rings_n=6)
        pads.add(v2, f2, lambda i, b=bones[2]: {b: 1.0})
        # claw: dorsal-distal, embedded base, pointing forward + slightly down
        claw_base = tip + Vector((0, 0, segs[2][1] * 0.35)) - path[2][1] * 0.004
        cd = (path[2][1] + Vector((0, 0, -0.35))).normalized()
        v3, f3 = cone(tuple(claw_base), cd, 0.016, segs[2][1] * 0.52)
        claws.add(v3, f3, lambda i, b=bones[2]: {b: 1.0})
    # ---- thumb: metacarpal + 2 phalanges, angled out/palmar
    tbase = Vector(THUMB_BASE)
    td = Vector(THUMB_DIR).normalized()
    tsegs = THUMB_SEGS
    rings = []
    seg_of_ring = []
    thumb_joints = [Vector(tbase)]
    p = Vector(tbase)
    d = Vector(td)
    for si, (ln, r) in enumerate(tsegs):
        if si > 0:
            d = rot_x(d, -9.0).normalized()
        r1 = r * 0.88 if si < 2 else r * 0.55
        rings.append({"c": p, "rx": r, "rz": r * 0.92, "t": d}); seg_of_ring.append(si)
        rings.append({"c": p + d * ln * 0.55, "rx": (r + r1) / 2, "rz": (r + r1) / 2 * 0.92, "t": d}); seg_of_ring.append(si)
        rings.append({"c": p + d * ln, "rx": r1, "rz": r1 * 0.92, "t": d}); seg_of_ring.append(si)
        p = p + d * ln
        thumb_joints.append(Vector(p))
    v, f, ring_of = loft(rings, n=10)
    seg_of = [seg_of_ring[r] for r in ring_of]
    tbones = ["Thumb1_R", "Thumb2_R", "Thumb3_R"]
    def twf(i, seg_of=seg_of):
        s = seg_of[i]
        return {tbones[s]: 1.0} if s == 0 else {tbones[s]: 0.85, tbones[s - 1]: 0.15}
    mb.add(v, f, twf)
    # thumb pad: underside of the distal segment, NOT a cap on the tip
    # (render pass 1: tip placement read as a dark cap over the claw)
    tpad_c = thumb_joints[2] + d * tsegs[2][0] * 0.35 + Vector((0.001, 0, -0.0055))
    v2, f2 = ellipsoid(tuple(tpad_c), (0.0068, 0.0082, 0.0030), seg=10, rings_n=6)
    pads.add(v2, f2, lambda i: {"Thumb3_R": 1.0})
    v3, f3 = cone(tuple(p + Vector((0, 0.002, 0.003))), (d + Vector((0, 0, -0.3))).normalized(), 0.014, 0.0048)
    claws.add(v3, f3, lambda i: {"Thumb3_R": 1.0})
    # ---- palm pads: metacarpal heart pad (2 lobes + apex), carpal pad
    # sunk ~1.2 mm deeper than pass 1 (disc-read fix); carpal pad moved
    # out to actually clear the wrist surface (was fully buried).
    for c, r in [((-0.0155, 0.060, -0.0106), (0.0155, 0.017, 0.0041)),
                 ((0.0155, 0.060, -0.0106), (0.0155, 0.017, 0.0041)),
                 ((0.0, 0.080, -0.0098), (0.0135, 0.015, 0.0038))]:
        v, f = ellipsoid(c, r, seg=12, rings_n=7)
        pads.add(v, f, lambda i: {"Wrist_R": 1.0})
    v, f = ellipsoid((0.008, 0.010, -0.0152), (0.009, 0.011, 0.0036), seg=10, rings_n=6)
    pads.add(v, f, lambda i: {"Wrist_R": 1.0})  # carpal (stopper) pad
    return mb, pads, claws

# ================================================================ DIGI FOOT
# Path: hock (Ankle_R) at z 0.255 -> metatarsus -> MTP -> toes to ground.
MT_RINGS = [
    # (center, rx, rz)
    ((0, -0.006, 0.258), 0.0200, 0.0240),
    ((0, 0.002, 0.205), 0.0170, 0.0200),
    ((0, 0.014, 0.148), 0.0158, 0.0180),
    ((0, 0.030, 0.096), 0.0168, 0.0178),
    ((0, 0.050, 0.050), 0.0208, 0.0158),
    ((0, 0.057, 0.032), 0.0218, 0.0130),
]
# digit, x, total segs [(len, r)] — radii bumped x1.15 after render
# pass 1 (toes read spindly against the metatarsus)
TOES = [
    ("Toe2", -0.0300, [(0.025, 0.0122), (0.017, 0.0108), (0.013, 0.0094)]),
    ("Toe3", -0.0105, [(0.027, 0.0129), (0.019, 0.0114), (0.014, 0.0099)]),
    ("Toe4",  0.0105, [(0.027, 0.0129), (0.019, 0.0114), (0.014, 0.0099)]),
    ("Toe5",  0.0300, [(0.023, 0.0117), (0.016, 0.0104), (0.012, 0.0090)]),
]
TOE_FAN = {"Toe2": 4.0, "Toe3": 1.5, "Toe4": -1.5, "Toe5": -4.0}
TOE_DROP = [38.0, 22.0, 5.0]  # segment pitch down (deg) cumulative-ish

def build_foot():
    mb = MeshBuilder()
    pads = MeshBuilder()
    claws = MeshBuilder()
    # ---- metatarsus loft along path
    pts = [Vector(c) for c, _, _ in MT_RINGS]
    rings = []
    for i, ((c, rx, rz), p) in enumerate(zip(MT_RINGS, pts)):
        if i == 0:
            t = (pts[1] - pts[0])
        elif i == len(pts) - 1:
            t = (pts[-1] - pts[-2])
        else:
            t = (pts[i + 1] - pts[i - 1])
        rings.append({"c": p, "rx": rx, "rz": rz, "t": t})
    v, f, ring_of = loft(rings, n=14)
    def mwf(i, ring_of=ring_of):
        # blend Ankle_R (hock) -> Metatarsus_R down the shaft
        frac = ring_of[i] / (len(MT_RINGS) - 1)
        wa = max(0.0, 1.0 - frac * 1.6)
        return {"Ankle_R": wa, "Metatarsus_R": 1.0 - wa} if wa > 0 else {"Metatarsus_R": 1.0}
    mb.add(v, f, mwf)
    # calcaneal (hock) knob — back of the hock; mostly internal overlap
    # -> excluded from the fit-score surface
    v, f = ellipsoid((0, -0.017, 0.250), (0.0125, 0.010, 0.016))
    mb.add(v, f, lambda i: {"Ankle_R": 1.0}, fit=False)
    # ---- toes
    toe_base_y, toe_base_z = 0.056, 0.034
    for name, x, segs in TOES:
        p = Vector((x, toe_base_y, toe_base_z))
        d = rot_z(Vector((0, 1, 0)), TOE_FAN[name])
        rings = []
        seg_of_ring = []
        for si, (ln, r) in enumerate(segs):
            d = rot_x(d, -TOE_DROP[si] if si == 0 else -(TOE_DROP[si] - TOE_DROP[si - 1]))
            d.normalize()
            r1 = r * 0.88 if si < 2 else r * 0.55
            rings.append({"c": p, "rx": r, "rz": r * 0.90, "t": d}); seg_of_ring.append(si)
            rings.append({"c": p + d * ln * 0.55, "rx": (r + r1) / 2, "rz": (r + r1) / 2 * 0.90, "t": d}); seg_of_ring.append(si)
            rings.append({"c": p + d * ln, "rx": r1, "rz": r1 * 0.90, "t": d}); seg_of_ring.append(si)
            p = p + d * ln
        v, f, ring_of = loft(rings, n=10)
        seg_of = [seg_of_ring[r] for r in ring_of]
        b1, b2 = f"{name}_1_R", f"{name}_2_R"  # _1 proximal, _2 mid+distal
        def twf(i, seg_of=seg_of, b1=b1, b2=b2):
            s = seg_of[i]
            return {b1: 1.0} if s == 0 else {b2: 0.85, b1: 0.15}
        mb.add(v, f, twf)
        tip = p
        # digital pad under distal segment, sunk (disc-read fix)
        pad_c = tip - d * segs[2][0] * 0.5 + Vector((0, 0, -segs[2][1] * 0.62))
        v2, f2 = ellipsoid(tuple(pad_c), (segs[2][1] * 0.80, segs[2][0] * 0.45, 0.0030), seg=10, rings_n=6)
        pads.add(v2, f2, lambda i, b=b2: {b: 1.0})
        # claw at tip, forward-down, base embedded
        claw_base = tip + Vector((0, 0, segs[2][1] * 0.30)) - d * 0.003
        cd = (d + Vector((0, 0.15, -0.55))).normalized()
        v3, f3 = cone(tuple(claw_base), cd, 0.015, segs[2][1] * 0.50)
        claws.add(v3, f3, lambda i, b=b2: {b: 1.0})
    # ---- dewclaw (digit I): small 2-phalanx digit, medial-proximal metatarsus
    dp = Vector((-0.0205, 0.026, 0.118))
    dd = Vector((-0.15, 0.45, -0.88)).normalized()
    rings = []
    p = Vector(dp)
    d = Vector(dd)
    for si, (ln, r) in enumerate([(0.011, 0.0062), (0.009, 0.0052)]):
        r1 = r * 0.85 if si == 0 else r * 0.5
        rings.append({"c": p, "rx": r, "rz": r * 0.9, "t": d})
        rings.append({"c": p + d * ln, "rx": r1, "rz": r1 * 0.9, "t": d})
        p = p + d * ln
    v, f, _ = loft(rings, n=8)
    mb.add(v, f, lambda i: {"Dewclaw_R": 1.0})
    v3, f3 = cone(tuple(p + Vector((0, 0, 0.002))), (d + Vector((0, 0, -0.3))).normalized(), 0.009, 0.0028, n=7)
    claws.add(v3, f3, lambda i: {"Dewclaw_R": 1.0})
    # ---- metatarsal pad: heart (2 lobes + distal apex), plantar under MTP
    for c, r in [((-0.0130, 0.044, 0.0217), (0.0130, 0.0145, 0.0039)),
                 ((0.0130, 0.044, 0.0217), (0.0130, 0.0145, 0.0039)),
                 ((0.0, 0.062, 0.0197), (0.0115, 0.013, 0.0036))]:
        v, f = ellipsoid(c, r, seg=12, rings_n=7)
        pads.add(v, f, lambda i: {"Metatarsus_R": 1.0})
    return mb, pads, claws

# ================================================================ armatures
def make_armature(name, bones):
    """bones: list of (name, head, tail, parent_name_or_None)"""
    arm = bpy.data.armatures.new(name)
    ob = bpy.data.objects.new(name, arm)
    bpy.context.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode="EDIT")
    eb = {}
    for bname, head, tail, parent in bones:
        b = arm.edit_bones.new(bname)
        b.head = head
        b.tail = tail
        eb[bname] = b
    for bname, head, tail, parent in bones:
        if parent:
            eb[bname].parent = eb[parent]
    bpy.ops.object.mode_set(mode="OBJECT")
    return ob

def hand_bones():
    bones = [("Wrist_R", (0, -0.035, 0), (0, 0.03, 0), None)]
    for name, x, by, segs in FINGERS:
        path, tip = finger_path((x, by, 0.001), segs, FAN[name])
        prev = "Wrist_R"
        for si, (p, d, r0, r1) in enumerate(path):
            bn = f"{name}{si+1}_R"
            bones.append((bn, tuple(p), tuple(p + d * segs[si][0]), prev))
            prev = bn
    # thumb
    p = Vector(THUMB_BASE)
    d = Vector(THUMB_DIR).normalized()
    prev = "Wrist_R"
    for si, (ln, r) in enumerate(THUMB_SEGS):
        if si > 0:
            d = rot_x(d, -9.0).normalized()
        bn = f"Thumb{si+1}_R"
        bones.append((bn, tuple(p), tuple(p + d * ln), prev))
        prev = bn
        p = p + d * ln
    return bones

def foot_bones():
    bones = [
        ("Ankle_R", (0, -0.004, 0.256), (0, 0.014, 0.148), None),
        ("Metatarsus_R", (0, 0.014, 0.148), (0, 0.056, 0.034), "Ankle_R"),
    ]
    for name, x, segs in TOES:
        p = Vector((x, 0.056, 0.034))
        d = rot_z(Vector((0, 1, 0)), TOE_FAN[name])
        joints = [Vector(p)]
        for si, (ln, r) in enumerate(segs):
            d = rot_x(d, -TOE_DROP[si] if si == 0 else -(TOE_DROP[si] - TOE_DROP[si - 1]))
            d.normalize()
            p = p + d * ln
            joints.append(Vector(p))
        bones.append((f"{name}_1_R", tuple(joints[0]), tuple(joints[1]), "Metatarsus_R"))
        bones.append((f"{name}_2_R", tuple(joints[1]), tuple(joints[3]), f"{name}_1_R"))
    bones.append(("Dewclaw_R", (-0.0205, 0.026, 0.118), (-0.0235, 0.034, 0.099), "Metatarsus_R"))
    return bones

# ================================================================ stubs (fit)
def sleeve_stub(name, ring_specs):
    """Solid limb-end sleeve the part's cuff seats into.
    ring_specs: list of (center, rx, rz, tangent)."""
    rings = [{"c": Vector(c), "rx": rx, "rz": rz, "t": Vector(t)}
             for c, rx, rz, t in ring_specs]
    v, f, _ = loft(rings, n=14)
    me = bpy.data.meshes.new(name)
    me.from_pydata(v, [], f)
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return ob

def export_cuff_stl(src_ob, path, pred, fit_flags=None):
    """Export only the faces whose verts all satisfy pred(co) — the
    part's socket fit region — as a temp mesh STL. Faces touching a
    fit-excluded vertex (internal cosmetic blobs) are skipped."""
    me = src_ob.data
    verts = [tuple(v.co) for v in me.vertices]
    faces = []
    for p in me.polygons:
        idx = list(p.vertices)
        if fit_flags is not None and not all(fit_flags[i] for i in idx):
            continue
        if all(pred(Vector(verts[i])) for i in idx):
            faces.append(tuple(idx))
    used = sorted({i for fc in faces for i in fc})
    remap = {old: k for k, old in enumerate(used)}
    nv = [verts[i] for i in used]
    nf = [tuple(remap[i] for i in fc) for fc in faces]
    m2 = bpy.data.meshes.new("cuff_tmp")
    m2.from_pydata(nv, [], nf)
    m2.update()
    o2 = bpy.data.objects.new("cuff_tmp", m2)
    bpy.context.collection.objects.link(o2)
    bpy.ops.object.select_all(action="DESELECT")
    o2.select_set(True)
    bpy.context.view_layer.objects.active = o2
    bpy.ops.wm.stl_export(filepath=path, export_selected_objects=True)
    bpy.data.objects.remove(o2, do_unlink=True)
    return len(nv)

# ================================================================ main
def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    init_materials()
    stats = {}
    # HAND
    mb, pads, claws = build_hand()
    hand_main = mb.build("paw_hand_main", MAT_COAT)
    apply_weights(hand_main, mb.weights)
    hand_pads = pads.build("paw_hand_pads", MAT_PAD)
    apply_weights(hand_pads, pads.weights)
    hand_claws = claws.build("paw_hand_claws", MAT_CLAW)
    apply_weights(hand_claws, claws.weights)
    hand_arm = make_armature("paw_hand_armature", hand_bones())
    for ob in (hand_main, hand_pads, hand_claws):
        mod = ob.modifiers.new("Armature", "ARMATURE")
        mod.object = hand_arm
        ob.parent = hand_arm
    # FOOT
    fb, fpads, fclaws = build_foot()
    foot_main = fb.build("paw_foot_main", MAT_COAT)
    apply_weights(foot_main, fb.weights)
    foot_pads = fpads.build("paw_foot_pads", MAT_PAD)
    apply_weights(foot_pads, fpads.weights)
    foot_claws = fclaws.build("paw_foot_claws", MAT_CLAW)
    apply_weights(foot_claws, fclaws.weights)
    foot_arm = make_armature("paw_foot_armature", foot_bones())
    for ob in (foot_main, foot_pads, foot_claws):
        mod = ob.modifiers.new("Armature", "ARMATURE")
        mod.object = foot_arm
        ob.parent = foot_arm
    # STUBS (fit-score bases, kept in blend, excluded from part GLBs):
    # limb-end sleeves ~2.5 mm proud of the part cuff they receive.
    wrist_stub = sleeve_stub("stub_forearm", [
        ((0, -0.030, 0), 0.0315, 0.0180, (0, 1, 0)),
        ((0, 0.000, 0), 0.0315, 0.0180, (0, 1, 0)),
        ((0, 0.034, 0), 0.0400, 0.0190, (0, 1, 0)),
    ])
    shin_stub = sleeve_stub("stub_shin", [
        ((0, -0.016, 0.370), 0.0260, 0.0280, (0, 0.10, -1)),
        ((0, -0.010, 0.300), 0.0235, 0.0265, (0, 0.08, -1)),
        ((0, -0.006, 0.255), 0.0215, 0.0255, (0, 0.05, -1)),
        ((0, -0.002, 0.228), 0.0195, 0.0230, (0, 0.08, -1)),
        ((0, 0.002, 0.202), 0.0185, 0.0215, (0, 0.10, -1)),
    ])
    # stats
    for label, obs in (("hand", (hand_main, hand_pads, hand_claws)),
                       ("foot", (foot_main, foot_pads, foot_claws))):
        nv = sum(len(o.data.vertices) for o in obs)
        nt = sum(len(o.data.polygons) for o in obs)
        stats[label] = {"verts": nv, "tris": nt}
    stats["hand_bones"] = len(hand_bones())
    stats["foot_bones"] = len(foot_bones())
    print("STATS", json.dumps(stats))
    # save blend
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(PARTS, "b11_hands_feet.blend"))
    # export GLBs (per part: armature + its 3 meshes)
    def export_glb(objs, path):
        bpy.ops.object.select_all(action="DESELECT")
        for o in objs:
            o.select_set(True)
        bpy.context.view_layer.objects.active = objs[0]
        bpy.ops.export_scene.gltf(filepath=path, export_format="GLB",
                                  use_selection=True, export_skins=True,
                                  export_yup=True)
    export_glb([hand_arm, hand_main, hand_pads, hand_claws],
               os.path.join(PARTS, "paw_hand_r.glb"))
    export_glb([foot_arm, foot_main, foot_pads, foot_claws],
               os.path.join(PARTS, "paw_foot_digi_r.glb"))
    # STLs for fit scoring: part main mesh + stub
    def export_stl(ob, path):
        bpy.ops.object.select_all(action="DESELECT")
        ob.select_set(True)
        bpy.context.view_layer.objects.active = ob
        bpy.ops.wm.stl_export(filepath=path, export_selected_objects=True)
    export_stl(hand_main, os.path.join(HERE, "hand_main.stl"))
    export_stl(wrist_stub, os.path.join(HERE, "wrist_stub.stl"))
    export_stl(foot_main, os.path.join(HERE, "foot_main.stl"))
    export_stl(shin_stub, os.path.join(HERE, "shin_stub.stl"))
    # cuff (fit-region) STLs — the socket seating surface, scored separately
    n1 = export_cuff_stl(hand_main, os.path.join(HERE, "hand_cuff.stl"),
                         lambda co: co.y <= 0.032, mb.fit)
    n2 = export_cuff_stl(foot_main, os.path.join(HERE, "foot_cuff.stl"),
                         lambda co: co.z >= 0.200, fb.fit)
    print("CUFF VERTS", n1, n2)
    with open(os.path.join(HERE, "build_stats.json"), "w") as fh:
        json.dump(stats, fh, indent=1)
    print("BUILD DONE")

main()
