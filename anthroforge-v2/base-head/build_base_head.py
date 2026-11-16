# build_base_head.py — AnthroForge neutral base head (v1)
# Authored procedurally: superellipse cross-section loft for skull+muzzle,
# tapered tube lofts for ears (merged into head mesh), separate lofted jaw
# (origin at hinge), eyeball spheres, simple mouth-interior tunnel.
# Proportions follow species-head-spec.md §3.1 NEUTRAL column, ratios to L.
# L = 1.0 Blender unit along Y: nose tip y=+0.50, occiput y=-0.50. +X = head's left.
import bpy, math, json, os, struct
from mathutils import Vector

OUT = os.path.expanduser("~/workspace/anthroforge-v2/base-head")
os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------- scene reset
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
for coll in (bpy.data.meshes, bpy.data.curves, bpy.data.cameras, bpy.data.lights):
    pass  # leftover datablocks are harmless

# ---------------------------------------------------------------- helpers
def spow(v, p):
    return math.copysign(abs(v) ** p, v) if v != 0.0 else 0.0

def smooth(ch, w=5):
    n = len(ch); h = w // 2; out = []
    for i in range(n):
        lo = max(0, i - h); hi = min(n, i + h + 1)
        out.append(sum(ch[lo:hi]) / (hi - lo))
    return out

def sample_keys(keys, samples, y0, y1):
    """keys: list of (y, [channels...]) ordered y0->y1 (descending y here).
    Returns (ys, channels list-of-lists) linearly interpolated then smoothed."""
    nch = len(keys[0]) - 1
    ys = []; chans = [[] for _ in range(nch)]
    for s in range(samples):
        y = y0 + (y1 - y0) * s / (samples - 1)
        ys.append(y)
        # find bracketing keys
        k = 0
        while k < len(keys) - 2 and keys[k + 1][0] > y:
            k += 1
        ya, va = keys[k][0], keys[k][1:]; yb, vb = keys[k + 1][0], keys[k + 1][1:]
        t = 0.0 if ya == yb else (ya - y) / (ya - yb)
        t = max(0.0, min(1.0, t))
        for c in range(nch):
            chans[c].append(va[c] + (vb[c] - va[c]) * t)
    return ys, [smooth(c) for c in chans]

def gauss(x, mu, sig):
    return math.exp(-(((x - mu) / sig) ** 2))

def make_obj(name, verts, faces, collection=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    (collection or bpy.context.scene.collection).objects.link(ob)
    return ob

def add_groups(ob, groups):
    """groups: dict name -> dict {vert_index: weight}"""
    for name, weights in groups.items():
        vg = ob.vertex_groups.new(name=name)
        buckets = {}
        for idx, w in weights.items():
            if w <= 0.01:
                continue
            buckets.setdefault(round(w, 2), []).append(idx)
        for w, idxs in buckets.items():
            vg.add(idxs, w, 'REPLACE')

# ---------------------------------------------------------------- materials
def clay(name, rgb, rough=0.85):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    return m
MAT_CLAY = clay("Clay", (0.72, 0.70, 0.68))
MAT_DARK = clay("ClayDark", (0.16, 0.13, 0.12), 0.95)

# ================================================================ SKULL LOFT
# Key stations: (y, halfWidth a, halfHeight b, centerZ c, cheekFlare)
# Anchors: muzzle frac 0.33 (stop at y=+0.17); rostrum W 0.17 @ canine (y~0.30);
# muzzle depth 0.20; braincase W 0.36 (y~-0.12); skull height 0.31; ZB 0.58 via flare.
SKULL_KEYS = [
    ( 0.485, 0.012, 0.012, -0.018, 0.00),
    ( 0.470, 0.048, 0.036, -0.018, 0.00),   # nose leather: full W 0.096 = 0.55*muzzleW
    ( 0.440, 0.055, 0.044, -0.016, 0.00),
    ( 0.400, 0.060, 0.060, -0.014, 0.00),
    ( 0.350, 0.072, 0.082, -0.012, 0.00),
    ( 0.300, 0.085, 0.100, -0.010, 0.00),   # canine level: W 0.17, depth 0.20
    ( 0.250, 0.100, 0.115, -0.006, 0.00),
    ( 0.200, 0.115, 0.125, -0.002, 0.00),   # muzzle base W 0.23 (taper 0.096/0.23 ~ 0.42..0.5)
    ( 0.170, 0.138, 0.130,  0.000, 0.04),   # stop
    ( 0.120, 0.168, 0.140,  0.002, 0.16),
    ( 0.050, 0.180, 0.150,  0.006, 0.34),
    ( 0.000, 0.185, 0.154,  0.004, 0.52),
    (-0.060, 0.182, 0.156,  0.003, 0.66),   # zygomatic peak -> ~0.29 half width
    (-0.120, 0.178, 0.158,  0.004, 0.50),   # braincase W 0.356, height ~0.31
    (-0.200, 0.175, 0.150,  0.000, 0.30),
    (-0.280, 0.160, 0.140, -0.004, 0.12),
    (-0.360, 0.135, 0.122, -0.006, 0.00),
    (-0.430, 0.100, 0.096, -0.006, 0.00),
    (-0.485, 0.012, 0.012, -0.004, 0.00),
]
S_ST, S_RING = 96, 56
ys, (ca, cb, cc, cfl) = sample_keys(SKULL_KEYS, S_ST, 0.485, -0.485)

skull_verts = []; zn_list = []
for si in range(S_ST):
    y, a, b, c, fl = ys[si], ca[si], cb[si], cc[si], cfl[si]
    for j in range(S_RING):
        th = 2.0 * math.pi * j / S_RING
        ct, st = math.cos(th), math.sin(th)
        n = 2.6 if st >= 0 else 3.2
        x0 = a * spow(ct, 2.0 / n)
        z0 = b * spow(st, 2.0 / n)
        zn = z0 / b if b > 1e-6 else 0.0
        flare_f = 1.0 + fl * math.exp(-(((zn + 0.45) / 0.42) ** 2)) * (abs(ct) ** 2)
        skull_verts.append([x0 * flare_f, y, c + z0])
        zn_list.append(zn)
def zn_at(i):
    return zn_list[i] if i < len(zn_list) else 0.0
pole_f = len(skull_verts); skull_verts.append([0.0, 0.500, -0.018])
pole_b = len(skull_verts); skull_verts.append([0.0, -0.500, -0.004])
skull_faces = []
for si in range(S_ST - 1):
    for j in range(S_RING):
        j1 = (j + 1) % S_RING
        skull_faces.append((si * S_RING + j, si * S_RING + j1,
                            (si + 1) * S_RING + j1, (si + 1) * S_RING + j))
for j in range(S_RING):
    j1 = (j + 1) % S_RING
    skull_faces.append((pole_f, j1, j))
    base = (S_ST - 1) * S_RING
    skull_faces.append((pole_b, base + j, base + j1))

# ------------------------------------------------- sculpt passes (on skull)
EYE_Y, EYE_Z, EYE_X = 0.150, 0.027, 0.118
for i, v in enumerate(skull_verts):
    x, y, z = v
    zn = zn_at(i)
    # eye sockets: dent toward eye centre + slight rim raise
    for sgn in (1.0, -1.0):
        ex = sgn * EYE_X
        dx, dy, dz = x - ex, y - EYE_Y, z - EYE_Z
        d = math.sqrt(dx * dx + dy * dy + dz * dz)
        if 1e-6 < d < 0.115:
            f = 0.5 * (1.0 + math.cos(math.pi * d / 0.115))
            v[0] -= dx / d * 0.020 * f
            v[1] -= dy / d * 0.020 * f
            v[2] -= dz / d * 0.020 * f
        elif 0.115 <= d < 0.155:
            f = gauss(d, 0.132, 0.013)
            rl = math.hypot(x, z - 0.004) or 1.0
            v[0] += x / rl * 0.0035 * f
            v[2] += (z - 0.004) / rl * 0.0035 * f
        # brow ridge: soft outward bump above/inner eye
        bx, by, bz = sgn * 0.130, 0.190, 0.118
        dx, dy, dz = x - bx, y - by, z - bz
        d = math.sqrt(dx * dx + dy * dy + dz * dz)
        if d < 0.105:
            f = 0.5 * (1.0 + math.cos(math.pi * d / 0.105))
            rl = math.hypot(x, z - 0.01) or 1.0
            v[0] += x / rl * 0.0065 * f
            v[2] += (z - 0.01) / rl * 0.0065 * f
    # stop pinch: dorsal midline dip at the forehead break
    if zn > 0.55:
        v[2] -= 0.012 * gauss(y, 0.170, 0.045) * ((zn - 0.55) / 0.45)
    # mouth crease: gentle inward line on the muzzle sides
    if abs(x) > 0.03 and 0.0 < y < 0.44:
        zline = -0.098 + 0.055 * ((y - 0.02) / 0.42)
        dzl = abs(z - zline)
        if dzl < 0.016:
            v[0] -= math.copysign(1.0, x) * 0.004 * (1.0 - dzl / 0.016) * gauss(y, 0.22, 0.20)

SKULL_N = len(skull_verts)

# ================================================================ EARS
# EarHeight anchor 0.40 L along ear axis; EarWidth 0.55*len = 0.22 max full width.
EAR_LEN = 0.40
ear_data = {}   # side -> (verts, faces, t_per_vert)
for sgn, sname in ((1.0, 'L'), (-1.0, 'R')):
    B = Vector((sgn * 0.115, -0.100, 0.112))
    D = Vector((sgn * 0.36, 0.05, 1.0)); D.normalize()
    vax = Vector((0, 1, 0)).cross(D); vax.normalize()        # width axis (~X)
    uax = D.cross(vax); uax.normalize()                        # depth axis (~Y)
    ca_, sa_ = math.cos(sgn * 0.55), math.sin(sgn * 0.55)     # cant the pinna face outward
    vax, uax = vax * ca_ + uax * sa_, uax * ca_ - vax * sa_
    R, P = 20, 18
    wprof = [(0.0, 0.070), (0.15, 0.095), (0.35, 0.110), (0.60, 0.098),
             (0.80, 0.070), (0.92, 0.038), (1.0, 0.010)]
    dprof = [(0.0, 0.050), (0.15, 0.055), (0.35, 0.052), (0.60, 0.045),
             (0.80, 0.032), (0.92, 0.020), (1.0, 0.010)]
    def prof(p, t):
        for k in range(len(p) - 1):
            if p[k][0] <= t <= p[k + 1][0]:
                tt = (t - p[k][0]) / max(1e-6, p[k + 1][0] - p[k][0])
                return p[k][1] + (p[k + 1][1] - p[k][1]) * tt
        return p[-1][1]
    verts = []; tvals = []
    for ri in range(R):
        t = ri / (R - 1)
        cen = B + D * ((t - 0.06) * EAR_LEN) + Vector((sgn * 0.018 * t * t, -0.045 * t * t, 0.0))
        w, dp = prof(wprof, t), prof(dprof, t)
        for j in range(P):
            ph = 2.0 * math.pi * j / P
            pt = cen + vax * (w * math.cos(ph)) + uax * (dp * math.sin(ph))
            verts.append(list(pt)); tvals.append(t)
    tip = len(verts)
    tipc = B + D * (0.97 * EAR_LEN) + Vector((sgn * 0.018, -0.045, 0.0))
    verts.append(list(tipc)); tvals.append(1.0)
    faces = []
    for ri in range(R - 1):
        for j in range(P):
            j1 = (j + 1) % P
            faces.append((ri * P + j, (ri + 1) * P + j, (ri + 1) * P + j1, ri * P + j1))
    for j in range(P):
        j1 = (j + 1) % P
        faces.append(((R - 1) * P + j, tip, (R - 1) * P + j1))
    ear_data[sname] = (verts, faces, tvals, B, tipc)

# merge ears into skull vertex/face lists (record index ranges)
ear_ranges = {}
all_verts = [tuple(v) for v in skull_verts]
all_faces = list(skull_faces)
for sname in ('L', 'R'):
    ev, ef, tv, B, tipc = ear_data[sname]
    off = len(all_verts)
    ear_ranges[sname] = (off, off + len(ev), tv)
    all_verts.extend(tuple(v) for v in ev)
    all_faces.extend(tuple(off + i for i in f) for f in ef)

head = make_obj("Head", all_verts, all_faces)
head.data.materials.append(MAT_CLAY)

# ------------------------------------------------- head vertex groups
G = {}
def gadd(name, idx, w):
    if w > 0.01:
        G.setdefault(name, {})[idx] = max(w, G.setdefault(name, {}).get(idx, 0.0))
for i in range(SKULL_N):
    x, y, z = skull_verts[i]; zn = zn_at(i)
    topness = max(0.0, zn)
    if y > 0.05:
        gadd("Muzzle", i, min(1.0, (y - 0.05) / 0.12 + 0.25))
    if y > 0.34:
        gadd("MuzzleTip", i, min(1.0, (y - 0.34) / 0.13))
    if y > 0.44:
        gadd("NoseLeather", i, min(1.0, (y - 0.44) / 0.05))
    if 0.12 < y < 0.46 and zn > 0.25:
        gadd("MuzzleBridge", i, topness * min(1.0, (y - 0.12) / 0.08) * min(1.0, (0.46 - y) / 0.06 + 0.3))
    if y < 0.16:
        gadd("Cranium", i, min(1.0, (0.16 - y) / 0.12 + 0.25))
    if y < 0.14 and zn > 0.15:
        gadd("CraniumDome", i, topness * min(1.0, (0.14 - y) / 0.10 + 0.2))
    cheekw = gauss(y, -0.06, 0.115) * max(0.0, (abs(zn + 0.35) < 0.85) * 1.0) * min(1.0, abs(x) / 0.16)
    if x > 0:
        gadd("CheekL", i, cheekw)
    elif x < 0:
        gadd("CheekR", i, cheekw)
    for sgn, sname in ((1.0, 'L'), (-1.0, 'R')):
        ex = sgn * EYE_X
        d = math.dist((x, y, z), (ex, EYE_Y, EYE_Z))
        if d < 0.108:
            gadd("EyeSocket" + sname, i, 0.5 * (1.0 + math.cos(math.pi * d / 0.108)))
        bx, by, bz = sgn * 0.130, 0.190, 0.118
        d = math.dist((x, y, z), (bx, by, bz))
        if d < 0.115:
            gadd("Brow" + sname, i, 0.5 * (1.0 + math.cos(math.pi * d / 0.115)))
for sname in ('L', 'R'):
    off, end, tv = ear_ranges[sname]
    for k in range(off, end):
        t = tv[k - off]
        gadd("Ear" + sname, k, 1.0)
        gadd("EarBase" + sname, k, max(0.0, 1.0 - t / 0.55))
        gadd("EarTip" + sname, k, max(0.0, (t - 0.45) / 0.55))
add_groups(head, G)

# ================================================================ JAW
# Hinge at (0, -0.28, -0.02); built in hinge-local coords, object placed at hinge.
# Mandible length anchor 0.74 -> chin world y = -0.28 + 0.74 = +0.46.
# JawWidth anchor 0.40 -> half 0.20 at angle. JawDepth anchor 0.28 at ramus.
HINGE = Vector((0.0, -0.28, -0.02))
JAW_KEYS = [  # (world y, halfWidth, topZ, bottomZ)
    ( 0.460, 0.075, -0.085, -0.145),
    ( 0.400, 0.095, -0.080, -0.160),
    ( 0.320, 0.115, -0.078, -0.180),
    ( 0.240, 0.132, -0.076, -0.200),
    ( 0.150, 0.148, -0.074, -0.220),
    ( 0.050, 0.163, -0.072, -0.240),
    (-0.050, 0.178, -0.070, -0.258),
    (-0.150, 0.190, -0.045, -0.262),
    (-0.240, 0.198, -0.018, -0.285),   # angle; coronoid top -> ramus depth ~0.27
    (-0.300, 0.178, -0.025, -0.248),
]
J_ST, J_RING = 26, 36
jys, (jw, jt, jb) = sample_keys(JAW_KEYS, J_ST, 0.460, -0.300)
jaw_verts = []
for si in range(J_ST):
    y = jys[si]; w = jw[si]; top = jt[si]; bot = jb[si]
    zc = 0.5 * (top + bot); h = 0.5 * (top - bot)
    for j in range(J_RING):
        th = 2.0 * math.pi * j / J_RING
        ct, st = math.cos(th), math.sin(th)
        n = 4.0 if st >= 0 else 2.3
        lx = w * spow(ct, 2.0 / n)
        lz = zc + h * spow(st, 2.0 / n)
        jaw_verts.append((lx, y - HINGE.y, lz - HINGE.z))
jp_f = len(jaw_verts); jaw_verts.append((0.0, 0.460 - HINGE.y + 0.012, -0.1175 - HINGE.z))
jp_b = len(jaw_verts); jaw_verts.append((0.0, -0.300 - HINGE.y - 0.012, -0.140 - HINGE.z))
jaw_faces = []
for si in range(J_ST - 1):
    for j in range(J_RING):
        j1 = (j + 1) % J_RING
        jaw_faces.append((si * J_RING + j, (si + 1) * J_RING + j, (si + 1) * J_RING + j1, si * J_RING + j1))
for j in range(J_RING):
    j1 = (j + 1) % J_RING
    jaw_faces.append((jp_f, j, j1))
    base = (J_ST - 1) * J_RING
    jaw_faces.append((jp_b, base + j1, base + j))
jaw = make_obj("Jaw", jaw_verts, jaw_faces)
jaw.location = HINGE
jaw.data.materials.append(MAT_CLAY)
add_groups(jaw, {"Jaw": {i: 1.0 for i in range(len(jaw_verts))},
                 "Chin": {i: 1.0 for i in range(3 * J_RING)}})

# ================================================================ EYEBALLS
eyes = {}
for sgn, sname in ((1.0, 'L'), (-1.0, 'R')):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.052,
                                          location=(sgn * EYE_X, EYE_Y, EYE_Z))
    eb = bpy.context.active_object
    eb.name = "Eyeball_" + sname
    bpy.ops.object.shade_smooth()
    eb.data.materials.append(MAT_CLAY)
    eyes[sname] = eb

# ================================================================ MOUTH INTERIOR
fx, bx = 0.075, 0.082           # front/back half widths
fy, by = 0.30, -0.08            # front/back y
tz, bz = -0.055, -0.150         # top/bottom z
cv = [(-fx, fy, tz), (fx, fy, tz), (fx, fy, bz), (-fx, fy, bz),
      (-bx, by, tz), (bx, by, tz), (bx, by, bz), (-bx, by, bz)]
# inward-wound faces: top, back, left, right (front + bottom left open)
cf = [(0, 4, 5, 1), (5, 4, 7, 6), (4, 0, 3, 7), (1, 5, 6, 2)]
mouth = make_obj("MouthInterior", cv, cf)
mouth.data.materials.append(MAT_DARK)
mouth.parent = head

# ================================================================ VERIFY
def vrange(ob, idxs=None, local=False):
    vs = ob.data.vertices
    pts = []
    for i, v in enumerate(vs):
        if idxs is not None and i not in idxs:
            continue
        p = v.co if local else (ob.matrix_world @ v.co)
        pts.append(p)
    xs = [p.x for p in pts]; ysv = [p.y for p in pts]; zs = [p.z for p in pts]
    return (min(xs), max(xs)), (min(ysv), max(ysv)), (min(zs), max(zs))

skull_idx = set(range(SKULL_N))
hx, hy, hz = vrange(head, skull_idx)
cran = {i for i in range(SKULL_N) if -0.18 <= skull_verts[i][1] <= -0.08 and skull_verts[i][2] > 0.05}
cx, _, _ = vrange(head, cran)
ros = {i for i in range(SKULL_N) if 0.29 <= skull_verts[i][1] <= 0.31}
rx, _, _ = vrange(head, ros)
crz = {i for i in range(SKULL_N) if -0.20 <= skull_verts[i][1] <= 0.0}
_, _, czr = vrange(head, crz)
jx, jy, jz = vrange(jaw, local=True)
ear_len = {}
for sname in ('L', 'R'):
    ev, ef, tv, B, tipc = ear_data[sname]
    ear_len[sname] = (Vector(tipc) - Vector(B)).length + 0.06 * EAR_LEN
report = {
    "head_verts_total": len(head.data.vertices),
    "jaw_verts": len(jaw.data.vertices),
    "skull_verts": SKULL_N,
    "L_total (nose->occiput)": round(hy[1] - hy[0], 3),
    "ZB max width": round(hx[1] - hx[0], 3),
    "braincase width @y[-0.18,-0.08],z>0.05": round(cx[1] - cx[0], 3),
    "rostrum width @y~0.30": round(rx[1] - rx[0], 3),
    "skull height @y[-0.20,0]": round(czr[1] - czr[0], 3),
    "symmetry |minx+maxx|": round(abs(hx[0] + hx[1]), 4),
    "jaw length (local ymax)": round(jy[1], 3),
    "jaw width": round(jx[1] - jx[0], 3),
    "jaw ramus height (local z span)": round(jz[1] - jz[0], 3),
    "ear length L/R": {k: round(v, 3) for k, v in ear_len.items()},
    "eyeball diameter": 0.104,
    "eye centre spacing": round(2 * EYE_X, 3),
    "targets": {"L": 1.0, "ZB": 0.58, "braincaseW": 0.36, "rostrumW": 0.17,
                "skullH": 0.31, "mandibleL": 0.74, "jawW": 0.40, "earL": 0.40,
                "orbitD": 0.15, "interorbitalW": 0.19},
}
print(json.dumps(report, indent=1))
with open(os.path.join(OUT, "proportions.json"), "w") as f:
    json.dump(report, f, indent=1)

# sidecar: vertex groups -> indices (blend-space, per object)
sidecar = {}
for ob in (head, jaw):
    sidecar[ob.name] = {vg.name: [v.index for v in ob.data.vertices
                                  if any(g.group == vg.index and g.weight > 0.01
                                         for g in v.groups)]
                        for vg in ob.vertex_groups}
with open(os.path.join(OUT, "neutral_base_head.groups.json"), "w") as f:
    json.dump(sidecar, f)

# ================================================================ SAVE + EXPORT
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "neutral_base_head.blend"))
for ob in (head, jaw, mouth, eyes['L'], eyes['R']):
    ob.select_set(True)
bpy.context.view_layer.objects.active = head
glb_path = os.path.join(OUT, "neutral_base_head.glb")
bpy.ops.export_scene.gltf(filepath=glb_path, export_format='GLB')
# inspect GLB for vertex-group survival
with open(glb_path, "rb") as f:
    data = f.read()
jlen = struct.unpack("<I", data[12:16])[0]
gltf = json.loads(data[20:20 + jlen])
print("GLB meshes:", [m.get("name") for m in gltf.get("meshes", [])])
print("GLB nodes:", [n.get("name") for n in gltf.get("nodes", [])])
print("GLB has extras/groups:", "extras" in json.dumps(gltf)[:200000])

# ================================================================ RENDERS
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 48
scene.cycles.device = 'CPU'
scene.render.resolution_x = 640
scene.render.resolution_y = 640
world = bpy.data.worlds.new("W") if not scene.world else scene.world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.18, 0.18, 0.19, 1.0)
world.node_tree.nodes["Background"].inputs[1].default_value = 1.0
bpy.ops.object.light_add(type='SUN', location=(2, 3, 4))
sun = bpy.context.active_object
sun.data.energy = 3.0
sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(35))
bpy.ops.object.light_add(type='AREA', location=(-2.5, -1.5, 1.5))
fill = bpy.context.active_object
fill.data.energy = 250.0
fill.data.size = 3.0
fill.rotation_euler = (math.radians(70), 0, math.radians(-120))

cam_data = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam
cam_data.lens = 55
TARGET = Vector((0.0, -0.02, 0.06))
def shoot(name, loc):
    cam.location = loc
    d = TARGET - Vector(loc)
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = os.path.join(OUT, name)
    bpy.ops.render.render(write_still=True)

shoot("preview_front.png", (0.0, 2.3, 0.10))
shoot("preview_side.png", (2.3, -0.02, 0.10))
jaw.rotation_euler.x = -0.26   # ~15 deg open for the 3/4 view only
shoot("preview_threequarter.png", (1.55, 1.65, 0.80))
jaw.rotation_euler.x = 0.0
print("DONE")
