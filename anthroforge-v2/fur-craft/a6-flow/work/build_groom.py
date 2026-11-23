"""A6 - Groom flow & combing prototype.

Flow-authored groom on the bara wolf head:
  1. extract head submesh (world space)
  2. author a flow field: geodesic potential from face-front seeds
     (hair streams run snout->caudal, Kidd 1903 primitive tract),
     zone-shaped (cheek S-sweep, ear recurve, throat convergence),
     Laplacian-smoothed, stored as colour attributes FLOW_dir/FLOW_len
  3. guides first: advect guide strands along the field
  4. children interpolate the guides (combed groom)
  5. tangled groom: same roots/lengths, direction discipline removed
     (reproduces the fur-prototype's woolly flaw for comparison)
  6. coherence metric + renders + save blend
"""
import bpy, math, random, heapq, json
import numpy as np
from mathutils import Vector, kdtree as mkdt
from mathutils.bvhtree import BVHTree

random.seed(20261112)
np.random.seed(20261112)

SRC = "/home/hatch/workspace/stick-figure-avatar/furry/bara_wolf_base.blend"
OUTDIR = "/home/hatch/workspace/anthroforge-v2/fur-craft/a6-flow"
WORK = OUTDIR + "/work"

# ---------------------------------------------------------------- head extract
bpy.ops.wm.open_mainfile(filepath=SRC)
ob = bpy.data.objects["BaraWolfBody"]
me = ob.data
me.calc_loop_triangles()
W = np.empty(len(me.vertices) * 3)
me.vertices.foreach_get("co", W)
V = (np.array(ob.matrix_world) @ np.hstack([W.reshape(-1, 3), np.ones((len(me.vertices), 1))]).T).T[:, :3]
N = np.empty(len(me.vertices) * 3)
me.vertices.foreach_get("normal", N)
N = N.reshape(-1, 3)
# rotate normals by world matrix (uniform scale, rotation only is fine here)
R = np.array(ob.matrix_world)[:3, :3]
N = (R @ N.T).T
N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
tris = np.empty(len(me.loop_triangles) * 3, dtype=np.int64)
me.loop_triangles.foreach_get("vertices", tris)
tris = tris.reshape(-1, 3)

gate = (V[:, 2] >= 1.585) & (np.abs(V[:, 0]) <= 0.32) & (V[:, 1] >= -0.345) & (V[:, 1] <= 0.335)
gidx = np.where(gate)[0]
remap = -np.ones(len(V), dtype=np.int64)
remap[gidx] = np.arange(len(gidx))
tmask = gate[tris].all(axis=1)
htris_all = remap[tris[tmask]]
# BFS connected faces from the face nearest the muzzle tip
muzzle = np.array([0.0, -0.305, 1.70])
cents = V[gidx][htris_all].mean(axis=1)
seed_face = int(np.argmin(np.linalg.norm(cents - muzzle, axis=1)))
v2f = {}
for fi, f in enumerate(htris_all):
    for v in f:
        v2f.setdefault(int(v), []).append(fi)
seen = np.zeros(len(htris_all), dtype=bool)
stack = [seed_face]; seen[seed_face] = True
while stack:
    f = stack.pop()
    for v in htris_all[f]:
        for nf in v2f[int(v)]:
            if not seen[nf]:
                seen[nf] = True; stack.append(nf)
htris = htris_all[seen]
used = np.unique(htris)
remap2 = -np.ones(len(gidx), dtype=np.int64)
remap2[used] = np.arange(len(used))
HV = V[gidx][used]
HN = N[gidx][used]
HF = remap2[htris]
n = len(HV)
print("HEAD verts", n, "faces", len(HF), "bbox",
      HV.min(axis=0).round(3), HV.max(axis=0).round(3))

# ---------------------------------------------------------------- graph + potential
edges = set()
for a, b, c in HF:
    for u, v in ((a, b), (b, c), (c, a)):
        edges.add((min(u, v), max(u, v)))
adj = [[] for _ in range(n)]
for u, v in edges:
    d = float(np.linalg.norm(HV[u] - HV[v]))
    adj[u].append((v, d)); adj[v].append((u, d))

seed_mask = np.linalg.norm(HV - muzzle, axis=1) < 0.085
seeds = np.where(seed_mask)[0]
print("seeds", len(seeds))
INF = 1e18
pot = np.full(n, INF)
pq = []
for s in seeds:
    pot[s] = 0.0; heapq.heappush(pq, (0.0, int(s)))
while pq:
    d, u = heapq.heappop(pq)
    if d > pot[u]:
        continue
    for v, w in adj[u]:
        nd = d + w
        if nd < pot[v]:
            pot[v] = nd; heapq.heappush(pq, (nd, v))
print("potential max %.3f m, unreachable %d" % (pot.max(), int((pot >= INF/2).sum())))

# ---------------------------------------------------------------- raw flow = -grad(potential)
face_flow = np.zeros((len(HF), 3))
for fi, (a, b, c) in enumerate(HF):
    p0, p1, p2 = HV[a], HV[b], HV[c]
    fn = np.cross(p1 - p0, p2 - p0)
    L = np.linalg.norm(fn)
    if L < 1e-14:
        continue
    fn /= L
    # gradient of the piecewise-linear potential on this triangle
    g = (pot[a] * np.cross(fn, p2 - p1) + pot[b] * np.cross(fn, p0 - p2) + pot[c] * np.cross(fn, p1 - p0)) / (2.0 * (L / 2.0))
    face_flow[fi] = g  # flow = direction of INCREASING potential: away from the face seeds, caudally
flow = np.zeros((n, 3))
cnt = np.zeros(n)
for fi, f in enumerate(HF):
    for v in f:
        flow[v] += face_flow[fi]; cnt[v] += 1
flow /= np.maximum(cnt, 1)[:, None]

def tangentise(F, Nrm):
    F = F - np.einsum('ij,ij->i', F, Nrm)[:, None] * Nrm
    l = np.linalg.norm(F, axis=1, keepdims=True)
    return F / np.maximum(l, 1e-12), (l[:, 0] > 1e-9)

flow, ok = tangentise(flow, HN)
flow[~ok] = 0.0

# ---------------------------------------------------------------- zone shaping
x, y, z = HV[:, 0], HV[:, 1], HV[:, 2]
absx = np.abs(x)
caudal = np.array([0.0, 1.0, 0.0])
down = np.array([0.0, 0.0, -1.0])

def blend_dir(F, target, w):
    T = np.tile(target, (len(F), 1)) if target.ndim == 1 else target
    Tt, _ = tangentise(T.copy(), HN)
    out = F * (1 - w)[:, None] + Tt * w[:, None]
    o, _ = tangentise(out, HN)
    return o

# cheek S-sweep: below the eye line, on the sides, pull flow caudo-ventral
w = np.clip((1.815 - z) / 0.10, 0, 1) * np.clip((absx - 0.055) / 0.05, 0, 1) * np.clip((y + 0.30) / 0.25, 0, 1)
w *= 0.65
flow = blend_dir(flow, caudal * 0.55 + down * 0.85, w)

# throat / jaw underside: converge caudo-medially toward the midline
under = np.clip((-HN[:, 2] - 0.25) / 0.5, 0, 1) * np.clip((1.70 - z) / 0.08, 0, 1)
inward = np.stack([-np.sign(x) * np.ones(n), np.full(n, 0.55), np.full(n, -0.25)], axis=1)
flow = blend_dir(flow, inward, under * 0.55)

# ears: base->tip on the ear; detect ear = high + lateral + behind face front
ear_w = np.clip((z - 1.875) / 0.05, 0, 1) * np.clip((absx - 0.030) / 0.03, 0, 1)
tipdir = np.stack([np.sign(x) * 0.45, np.full(n, 0.10), np.full(n, 1.0)], axis=1)
flow = blend_dir(flow, tipdir, ear_w * 0.85)

# neck sides: caudoventral obliquity (below the jaw, sides)
neck_w = np.clip((1.635 - z) / 0.05, 0, 1) * np.clip((absx - 0.05) / 0.05, 0, 1) * (1 - under)
flow = blend_dir(flow, caudal * 0.8 + down * 0.6, neck_w * 0.45)

# smooth: 4 graph-Laplacian passes, re-tangentised each pass (comb-ability)
for _ in range(4):
    acc = flow.copy(); c2 = np.ones(n)
    for u in range(n):
        for v, _w in adj[u]:
            acc[u] += flow[v]; c2[u] += 1
    flow = acc / c2[:, None]
    flow, _ = tangentise(flow, HN)

np.savez(WORK + "/field.npz", V=HV, N=HN, F=HF, flow=flow, pot=pot, ear_w=ear_w)
print("flow field done; mean |flow| ok:", float(np.linalg.norm(flow, axis=1).mean()))

# ---------------------------------------------------------------- length + density maps
def sstep(a, b, v):
    t = np.clip((v - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)

length = np.full(n, 0.045)
face_front = np.clip((pot - 0.055) / 0.05, 0, 1)          # 0 at muzzle -> 1 on skull
length = length * 0 + (0.016 + 0.034 * face_front)          # face 16 mm -> crown 50 mm
ruff_w = sstep(1.78, 1.66, -z + 3.44) * 0  # placeholder (unused)
ruff = np.clip((1.77 - z) / 0.14, 0, 1) * np.clip((pot - 0.07) / 0.09, 0, 1)
ruff *= 1.0 - np.clip((-y - 0.16) / 0.10, 0, 1) * np.clip((0.12 - absx) / 0.06, 0, 1)  # not on the front of the muzzle
length = length * (1 - ruff) + 0.125 * ruff                  # cheek/jaw/neck ruff up to 125 mm
neck = np.clip((1.66 - z) / 0.05, 0, 1)
length = length * (1 - neck * 0.5) + (0.105 * (neck * 0.5))
length = length * (1 - ear_w) + 0.028 * ear_w                # ears short
density = 0.30 + 0.75 * face_front + 0.30 * ruff + 0.25 * neck
density = density * (1 - ear_w) + 0.8 * ear_w

# ---------------------------------------------------------------- scene objects
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
mesh = bpy.data.meshes.new("WolfHead")
mesh.from_pydata([tuple(p) for p in HV], [], [tuple(f) for f in HF])
mesh.update()
# custom split normals are PER-LOOP in Blender 5.x: expand vertex normals
# to corners, in the same face order from_pydata created them
loop_normals = [tuple(HN[v]) for f in HF for v in f]
mesh.normals_split_custom_set(loop_normals)
head_ob = bpy.data.objects.new("WolfHead", mesh)
bpy.context.scene.collection.objects.link(head_ob)
attr = mesh.attributes.new("FLOW_dir", 'FLOAT_COLOR', 'POINT')
attr.data.foreach_set("color", np.hstack([flow * 0.5 + 0.5, np.ones((n, 1))]).ravel())
attr2 = mesh.attributes.new("FLOW_len", 'FLOAT', 'POINT')
attr2.data.foreach_set("value", length.astype(np.float32))
attr3 = mesh.attributes.new("FLOW_pot", 'FLOAT', 'POINT')
attr3.data.foreach_set("value", pot.astype(np.float32))

def make_mat(name, color, rough=0.85, emission=None):
    m = bpy.data.materials.new(name)
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = rough
    if emission is not None:
        out = m.node_tree.nodes["Material Output"]
        em = m.node_tree.nodes.new("ShaderNodeEmission")
        em.inputs["Color"].default_value = (*emission, 1)
        em.inputs["Strength"].default_value = 1.6
        m.node_tree.links.new(em.outputs["Emission"], out.inputs["Surface"])
    return m

clay = make_mat("clay", (0.40, 0.385, 0.36), 0.92)
head_ob.data.materials.append(clay)

# flow-viz duplicate: own mesh copy (materials are per-polygon in Blender),
# emission driven by the FLOW_dir attribute
viz_mesh = mesh.copy()
viz_ob = bpy.data.objects.new("WolfHead_flowviz", viz_mesh)
bpy.context.scene.collection.objects.link(viz_ob)
vm = bpy.data.materials.new("flowviz")
nt = vm.node_tree
out = nt.nodes["Material Output"]
em = nt.nodes.new("ShaderNodeEmission")
at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_name = "FLOW_dir"
em.inputs["Strength"].default_value = 1.25
nt.links.new(at.outputs["Color"], em.inputs["Color"])
nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
viz_mesh.materials.clear()
viz_mesh.materials.append(vm)

bvh = BVHTree.FromObject(head_ob, bpy.context.evaluated_depsgraph_get())
kd = mkdt.KDTree(n)
for i, p in enumerate(HV):
    kd.insert(p, i)
kd.balance()

def surf_project(p, lift=0.0012):
    loc, nrmv, idx, dist = bvh.find_nearest(Vector(p), 0.08)
    if loc is None:
        return np.array(p), None, None
    loc = np.array(loc); nrmv = np.array(nrmv)
    return loc + nrmv * lift, nrmv, idx

def flow_at(p):
    co, idx, dist = kd.find(Vector(p))
    return flow[idx], idx

# ---------------------------------------------------------------- guides
SEG = 7
face_area = np.linalg.norm(np.cross(HV[HF[:, 1]] - HV[HF[:, 0]], HV[HF[:, 2]] - HV[HF[:, 0]]), axis=1) * 0.5
fdens = density[HF].mean(axis=1)
wts = face_area * fdens
wts /= wts.sum()
NGUIDES = 260
face_pick = np.random.choice(len(HF), size=NGUIDES, replace=True, p=wts)

def bary_sample(fi):
    r1, r2 = np.random.rand(), np.random.rand()
    if r1 + r2 > 1: r1, r2 = 1 - r1, 1 - r2
    a, b, c = HF[fi]
    p = HV[a] + r1 * (HV[b] - HV[a]) + r2 * (HV[c] - HV[a])
    w = (1 - r1 - r2, r1, r2)
    fl = flow[a] * w[0] + flow[b] * w[1] + flow[c] * w[2]
    fl = fl - (fl @ (HN[a] * w[0] + HN[b] * w[1] + HN[c] * w[2]))
    L = length[a] * w[0] + length[b] * w[1] + length[c] * w[2]
    nr = HN[a] * w[0] + HN[b] * w[1] + HN[c] * w[2]
    return p, fl / max(np.linalg.norm(fl), 1e-9), nr / max(np.linalg.norm(nr), 1e-9), L

def advect(root, f0, n0, L, droop_amt):
    pts = [root.copy()]
    p = root.copy()
    d = f0 + n0 * 0.30
    d /= np.linalg.norm(d)
    ds = L / SEG
    for i in range(SEG):
        t = (i + 1) / SEG
        p = p + d * ds
        q, nrmv, _ = surf_project(p, lift=0.0009 + 0.0035 * t)
        if nrmv is not None:
            p = q
        f, _ = flow_at(p)
        tgt = f + np.array([0, 0, -1.0]) * droop_amt * t
        tgt = tgt - (tgt @ nrmv) * nrmv if nrmv is not None else tgt
        tl = np.linalg.norm(tgt)
        if tl > 1e-9:
            tgt /= tl
            d = d * 0.42 + tgt * 0.58
            d /= np.linalg.norm(d)
        pts.append(p.copy())
    return np.array(pts)

guides = []
roots = []
for fi in face_pick:
    p, f0, n0, L = bary_sample(int(fi))
    q, nrmv, _ = surf_project(p, lift=0.0012)
    root = q if nrmv is not None else p
    droop_amt = 0.38 if (root[2] < 1.74 and pot[np.argmin(np.linalg.norm(HV - root, axis=1))] > 0.07) else 0.14
    g = advect(root, f0, n0, L, droop_amt)
    guides.append(g)
    roots.append((root, f0, n0, L))
print("guides built:", len(guides))

# ---------------------------------------------------------------- children (interpolation)
def resample(pts, scale=1.0):
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    cum = np.concatenate([[0], np.cumsum(seg)])
    tot = cum[-1]
    ts = np.linspace(0, 1, SEG + 1) * min(scale, 1.0) * tot if scale <= 1 else np.linspace(0, 1, SEG + 1) * tot
    out = np.stack([np.interp(ts, cum, pts[:, k]) for k in range(3)], axis=1)
    if scale > 1.0:  # extend last segment
        d = pts[-1] - pts[-2]; d /= max(np.linalg.norm(d), 1e-9)
        extra = (scale - 1.0) * tot
        out[-1] = pts[-1] + d * extra
        for i in range(1, SEG + 1):
            tt = i / SEG
            out[i] = out[i] + d * extra * tt * tt
    return out

def perp_frame(d):
    a = np.array([0.0, 0.0, 1.0]) if abs(d[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    u = np.cross(d, a); u /= max(np.linalg.norm(u), 1e-9)
    v = np.cross(d, u)
    return u, v

combed, tangled = [], []
coh_c, coh_t = [], []
NCHILD = 10
for gi, g in enumerate(guides):
    root, f0, n0, L = roots[gi]
    u, v = perp_frame(f0)
    for ci in range(NCHILD):
        ang = random.uniform(0, 2 * math.pi)
        rj = 0.0055 * math.sqrt(random.uniform(0, 1))
        off = u * math.cos(ang) * rj + v * math.sin(ang) * rj
        croot = root + off
        q, nrmv, _ = surf_project(croot, lift=0.0012)
        if nrmv is not None:
            croot = q
        ls = random.uniform(0.88, 1.10)
        base = resample(g, ls)
        shift = croot - root
        phase = random.uniform(0, 2 * math.pi)
        child = []
        for i in range(SEG + 1):
            t = i / SEG
            wob = math.sin(t * math.pi * 1.0 + phase) * 0.0006
            d_i = base[min(i + 1, SEG)] - base[i] if i < SEG else base[-1] - base[-2]
            uu, vv = perp_frame(d_i / max(np.linalg.norm(d_i), 1e-9))
            p = base[i] + shift * ((1 - t) ** 1.15) + uu * wob
            child.append(p)
        child = np.array(child)
        combed.append(child)
        # coherence: mid-strand direction vs flow at root
        dmid = child[SEG // 2 + 1] - child[SEG // 2]
        dmid /= max(np.linalg.norm(dmid), 1e-9)
        coh_c.append(math.degrees(math.acos(np.clip(dmid @ f0, -1, 1))))
        # ---- tangled twin: same root/length, direction discipline removed
        tilt_axis = np.cross(f0, np.random.randn(3)); tilt_axis /= max(np.linalg.norm(tilt_axis), 1e-9)
        tilt = math.radians(np.clip(np.random.randn() * 32, -78, 78))
        d = f0 * math.cos(tilt) + np.cross(tilt_axis, f0) * math.sin(tilt)
        d = d + n0 * 0.30; d /= np.linalg.norm(d)
        p = croot.copy(); tp = [p.copy()]
        ds = (L * ls) / SEG
        kink_phase = random.uniform(0, 2 * math.pi)
        for i in range(SEG):
            t = (i + 1) / SEG
            ax = np.random.randn(3); ax /= max(np.linalg.norm(ax), 1e-9)
            wob_ang = math.radians(16)
            d = d * math.cos(wob_ang) + np.cross(ax, d) * math.sin(wob_ang); d /= np.linalg.norm(d)
            p = p + d * ds
            uu, vv = perp_frame(d)
            p = p + uu * math.sin(t * math.pi * 3.0 + kink_phase) * 0.0032 * t
            loc, nrmv2, _idx, dist = bvh.find_nearest(Vector(p), 0.09)
            if loc is not None and dist > 0.016:
                p = np.array(loc) + np.array(nrmv2) * 0.016
            tp.append(p.copy())
            if i == SEG // 2:
                dmid_t = d.copy()
        tangled.append(np.array(tp))
        coh_t.append(math.degrees(math.acos(np.clip(dmid_t @ f0, -1, 1))))

print("children per groom:", len(combed))
metrics = {
    "guides": len(guides), "children_per_guide": NCHILD,
    "coherence_mean_deg": {"combed": float(np.mean(coh_c)), "tangled": float(np.mean(coh_t))},
    "coherence_median_deg": {"combed": float(np.median(coh_c)), "tangled": float(np.median(coh_t))},
}
print(json.dumps(metrics, indent=1))
with open(WORK + "/metrics.json", "w") as fh:
    json.dump(metrics, fh, indent=1)

# ---------------------------------------------------------------- curve objects
def make_strand_object(name, strands, mat, bevel):
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = bevel
    cu.bevel_resolution = 1
    cu.resolution_u = 1
    for s in strands:
        sp = cu.splines.new('POLY')
        sp.points.add(len(s) - 1)
        for i, p in enumerate(s):
            sp.points[i].co = (p[0], p[1], p[2], 1.0)
    o = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(o)
    cu.materials.append(mat)
    return o

hair_c = make_mat("hair", (0.148, 0.108, 0.078), 0.52)
guide_mat = make_mat("guides", (1.0, 0.4, 0.05), 0.5, emission=(1.0, 0.32, 0.04))
guides_ob = make_strand_object("Guides", guides, guide_mat, 0.0011)
combed_ob = make_strand_object("Groom_combed", combed, hair_c, 0.00062)
tangled_ob = make_strand_object("Groom_tangled", tangled, hair_c, 0.00062)

# ---------------------------------------------------------------- lights, cameras, world
sc = bpy.context.scene
world = bpy.data.worlds.new("W"); sc.world = world
world.node_tree.nodes["Background"].inputs[0].default_value = (0.045, 0.045, 0.05, 1)
world.node_tree.nodes["Background"].inputs[1].default_value = 1.0
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN'))
sun.data.energy = 3.2; sun.rotation_euler = (math.radians(52), math.radians(8), math.radians(-38))
sc.collection.objects.link(sun)
area = bpy.data.objects.new("Key", bpy.data.lights.new("Key", 'AREA'))
area.data.energy = 260; area.data.shape = 'DISK'; area.data.size = 1.6
area.location = (0.75, -0.85, 2.35)
sc.collection.objects.link(area)

def look_at(ob, target):
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()

def make_cam(name, loc, target, lens):
    c = bpy.data.objects.new(name, bpy.data.cameras.new(name))
    c.location = loc; c.data.lens = lens; c.data.clip_end = 20
    sc.collection.objects.link(c); look_at(c, target)
    return c

cam_cheek = make_cam("cam_cheek", (0.46, -0.52, 1.90), (0.085, -0.115, 1.705), 92)
cam_side = make_cam("cam_side", (0.78, -0.42, 1.98), (0.0, -0.02, 1.745), 58)
cam_flow = make_cam("cam_flow", (0.40, -0.80, 2.02), (0.0, -0.01, 1.755), 52)
area.rotation_euler = (Vector((0, -0.05, 1.75)) - area.location).to_track_quat('-Z', 'Y').to_euler()

sc.render.engine = 'CYCLES'
sc.cycles.samples = 64
sc.cycles.use_denoising = True
sc.render.resolution_x = 700; sc.render.resolution_y = 700
sc.render.image_settings.file_format = 'PNG'

def setvis(**kw):
    for name, vis in kw.items():
        o = bpy.data.objects[name]
        o.hide_render = not vis
        o.hide_viewport = not vis

def render(cam, path):
    sc.camera = cam
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("rendered", path)

setvis(WolfHead=True, WolfHead_flowviz=False, Guides=False, Groom_combed=True, Groom_tangled=False)
render(cam_cheek, OUTDIR + "/render_cheek_combed.png")
setvis(Groom_combed=False, Groom_tangled=True)
render(cam_cheek, OUTDIR + "/render_cheek_tangled.png")
setvis(Groom_combed=True, Groom_tangled=False)
render(cam_side, OUTDIR + "/render_head_combed.png")
setvis(Groom_combed=False, Guides=True)
render(cam_flow, OUTDIR + "/render_guides.png")
setvis(Guides=False, WolfHead=False, WolfHead_flowviz=True)
render(cam_flow, OUTDIR + "/render_flowmap.png")

# final saved state: combed groom on, tangled + guides present but hidden
setvis(WolfHead=True, WolfHead_flowviz=False, Guides=False, Groom_combed=True, Groom_tangled=False)
bpy.ops.wm.save_as_mainfile(filepath=OUTDIR + "/wolf_head_flow_groom.blend")
print("SAVED", OUTDIR + "/wolf_head_flow_groom.blend")
