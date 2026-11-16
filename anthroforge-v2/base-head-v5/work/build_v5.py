"""Neutral Base Head v5 build: lip-line loop cage (B12 F-M7/F-M8) on the v4 head.

Method:
 - merge TissueHead+Jaw (world space) exactly as build_v4 did;
 - the lip line = the front run of the existing tissue/jaw seam between placed
   commissures (F-M8: under the eye's lateral third), resampled, symmetrised,
   lightly smoothed and reprojected onto the surface;
 - cage rows built by surface walking (body +0.020, support +0.045 on both
   sides) and margin rows tucked into the mouth cavity (2 rows, ~0.011 each),
   giving F-M7's >=3 concentric loops + real margin thickness around a real
   opening (the gap between the two margin-deep rows);
 - rows pinch into the commissure points at the ends (poles only there, F-M7);
   philtrum pinch on the centre columns of the upper body/support rows (F-M5);
 - original faces inside a tapered band around the lip line are deleted; the
   cage grid is welded to the hole boundary by a greedy loop-to-loop bridge;
 - split back into TissueHead/Jaw (original faces keep their object; patch
   faces by row side; bridge faces by v3's analytic jaw_test, as build_v4);
 - skull/muscle layers and vertex groups regenerated with build_v4b recipes,
   plus new groups: LipCage, CommissureL/R, Philtrum.
Run: blender -b --threads 2 --python build_v5.py
"""
import bpy, json, math, os
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

V4 = "/home/hatch/workspace/anthroforge-v2/base-head-v4/neutral_base_head_v4.blend"
OUT = "/home/hatch/workspace/anthroforge-v2/base-head-v5"
WORK = OUT + "/work"
os.makedirs(WORK, exist_ok=True)
os.makedirs(OUT + "/renders", exist_ok=True)
LOG = {}

bpy.ops.wm.open_mainfile(filepath=V4)
O = {o.name: o for o in bpy.data.objects}
TIS = O["TissueHead"]; JAW = O["Jaw"]
H = np.array(tuple(JAW.location), float)          # hinge (0, -0.2167, -0.1249)
LOG["hinge"] = [round(v, 4) for v in H]
eye_c = np.array([0.1311, 0.0815, -0.0079])       # delivered eye centre (build_v4)

def jaw_zcut(c):
    if c[1] < H[1] - 0.18 or c[2] > H[2] + 0.12:
        return None
    return H[2] - 0.16 * max(0.0, c[1] - H[1]) + (0.30 * (H[1] - c[1]) if c[1] < H[1] else 0.0) \
        + 0.025 * math.exp(-((c[1] - H[1]) / 0.10) ** 2)
def jaw_test(c):
    zc = jaw_zcut(c)
    return zc is not None and c[2] < zc

# ---------------------------------------------------------------- merge (v4 method)
tis_v = [tuple(v.co) for v in TIS.data.vertices]
jaw_v = [tuple(np.array(tuple(v.co)) + H) for v in JAW.data.vertices]
tis_f = [tuple(p.vertices) for p in TIS.data.polygons]
jaw_f = [tuple(p.vertices) for p in JAW.data.polygons]
key2idx, verts = {}, []
def addv(c):
    k = (round(c[0], 6), round(c[1], 6), round(c[2], 6))
    if k not in key2idx:
        key2idx[k] = len(verts); verts.append(c)
    return key2idx[k]
remap_t = [addv(c) for c in tis_v]
remap_j = [addv(c) for c in jaw_v]
raw_faces = [tuple(remap_t[i] for i in f) for f in tis_f] + [tuple(remap_j[i] for i in f) for f in jaw_f]
raw_owner = ["T"] * len(tis_f) + ["J"] * len(jaw_f)
faces, face_owner = [], []
for f, o in zip(raw_faces, raw_owner):
    if len(set(f)) == len(f):
        faces.append(f); face_owner.append(o)
V = np.array(verts, float)
NV = len(V)
LOG["merged_verts"] = NV; LOG["merged_faces"] = len(faces)
tis_keys = {(round(c[0], 6), round(c[1], 6), round(c[2], 6)) for c in tis_v}
seam_idx = sorted({key2idx[(round(c[0], 6), round(c[1], 6), round(c[2], 6))] for c in jaw_v
                   if (round(c[0], 6), round(c[1], 6), round(c[2], 6)) in tis_keys})
seam_set = set(seam_idx)
LOG["seam_verts"] = len(seam_idx)

# edges + per-vertex normals (area weighted)
edges = set()
for f in faces:
    for i in range(len(f)):
        a, b = f[i], f[(i + 1) % len(f)]
        edges.add((min(a, b), max(a, b)))
tris = []
for f in faces:
    for t in range(1, len(f) - 1):
        tris.append((f[0], f[t], f[t + 1]))
tris = np.array(tris)
fn = np.cross(V[tris[:, 1]] - V[tris[:, 0]], V[tris[:, 2]] - V[tris[:, 0]])
fa = np.linalg.norm(fn, axis=1)
fn = fn / np.maximum(fa, 1e-12)[:, None]
vn = np.zeros_like(V)
for k in range(3):
    np.add.at(vn, tris[:, k], fn * fa[:, None])
vn /= np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-12)
bvh = BVHTree.FromPolygons([Vector(tuple(v)) for v in V], [tuple(t) for t in tris], all_triangles=True)

def surf_project(p):
    loc, nrm, idx, dist = bvh.find_nearest(Vector(tuple(p)))
    return np.array(loc), np.array(nrm), float(dist)

# ---------------------------------------------------------------- ordered seam loop
# the seam curve = edges shared by a tissue-owned and a jaw-owned face
from collections import defaultdict as _dd
edge_faces = _dd(list)
for fi, f in enumerate(faces):
    for i in range(len(f)):
        a, b = f[i], f[(i + 1) % len(f)]
        edge_faces[(min(a, b), max(a, b))].append(fi)
seam_edges = [e for e, fs in edge_faces.items()
              if len(fs) == 2 and face_owner[fs[0]] != face_owner[fs[1]]]
LOG["seam_edges_TJ"] = len(seam_edges)
adj = _dd(list)
for a, b in seam_edges:
    adj[a].append(b); adj[b].append(a)
degs = {i: len(adj[i]) for i in adj}
LOG["seam_degrees"] = {d: sum(1 for v in degs.values() if v == d) for d in sorted(set(degs.values()))}
# the T-J interface is an open path (throat end to throat end, around the front)
ends = [i for i in adj if len(adj[i]) == 1]
LOG["seam_path_endpoints"] = [[round(float(v), 4) for v in V[i]] for i in ends]
start = ends[0]
loop = [start]; prev, cur = -1, start
while True:
    nxt = [w for w in adj[cur] if w != prev]
    if not nxt: break
    w = nxt[0]
    loop.append(w); prev, cur = cur, w
    if len(loop) > len(adj) + 2: break
LOG["seam_loop_len"] = len(loop)
assert len(loop) == len(adj), f"seam path walk failed: {len(loop)} of {len(adj)}"

# ---------------------------------------------------------------- commissures (F-M8)
def pick_commissure(sx):
    tgt = np.array([sx * 0.165, 0.08, -0.18])
    cand = [i for i in loop if V[i][0] * sx > 0.03 and V[i][1] < 0.22]
    i_best = min(cand, key=lambda i: float(np.linalg.norm(V[i] - tgt)))
    return i_best
ci = {sx: pick_commissure(sx) for sx in (1, -1)}
LOG["commissures"] = {("L" if sx > 0 else "R"): [round(float(v), 4) for v in V[ci[sx]]] for sx in (1, -1)}
# front path between commissures = loop sub-path containing the front-most vert
li = {v: k for k, v in enumerate(loop)}
a, b = sorted((li[ci[1]], li[ci[-1]]))
front_path = loop[a:b + 1]
assert max(V[p][1] for p in front_path) > 0.45, "front path does not reach the muzzle front"
if V[front_path[0]][0] < 0: front_path = front_path[::-1]   # start at +x (L) end
raw = V[front_path].copy()
LOG["lip_raw_pts"] = len(raw)

# ---------------------------------------------------------------- resample + symmetrise + smooth
def resample(P, N):
    d = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
    s = np.linspace(0, d[-1], N)
    return np.stack([np.interp(s, d, P[:, k]) for k in range(3)], axis=1), float(d[-1])
path_len = float(np.sum(np.linalg.norm(np.diff(raw, axis=0), axis=1)))
N = int(min(81, max(49, round(path_len / 0.016) + 1)))
lip, _ = resample(raw, N)
# symmetrise: pair i <-> N-1-i mirror-averaged
for i in range(N // 2):
    j = N - 1 - i
    m = 0.5 * (lip[i] + np.array([-lip[j][0], lip[j][1], lip[j][2]]))
    lip[i] = m; lip[j] = np.array([-m[0], m[1], m[2]])
if N % 2: lip[N // 2][0] = 0.0
# light Chaikin + reprojection (2 rounds), endpoints pinned
for _ in range(2):
    Q = [lip[0]]
    for i in range(N - 1):
        Q.append(0.75 * lip[i] + 0.25 * lip[i + 1]); Q.append(0.25 * lip[i] + 0.75 * lip[i + 1])
    Q.append(lip[-1]); Q = np.array(Q)
    lip2, _ = resample(Q, N)
    lip2[0], lip2[-1] = lip[0], lip[-1]
    lip = lip2
    for i in range(1, N - 1):
        p, _, _ = surf_project(lip[i]); lip[i] = p
dev = []
for i in range(N):
    _, _, dd = surf_project(lip[i]); dev.append(dd)
lip[0] = V[ci[1]]; lip[-1] = V[ci[-1]]
LOG["lip_line"] = {"N": N, "length": round(path_len, 4), "spacing": round(path_len / (N - 1), 4),
                   "max_dev_from_surface_after_smooth": round(max(dev), 5),
                   "centre": [round(float(v), 4) for v in lip[N // 2]],
                   "ends": [[round(float(v), 4) for v in lip[0]], [round(float(v), 4) for v in lip[-1]]]}

# per-column frames: tangent, normal (from BVH face), tissue-side walk dir
tang = np.zeros((N, 3)); nrm = np.zeros((N, 3)); udir = np.zeros((N, 3))
for i in range(N):
    a = lip[max(0, i - 1)]; b = lip[min(N - 1, i + 1)]
    t = b - a; tang[i] = t / max(np.linalg.norm(t), 1e-12)
    _, nn, _ = surf_project(lip[i]); nrm[i] = nn
    u = np.cross(nrm[i], tang[i])
    ref = np.array([0.0, 0.25, 1.0])
    if np.dot(u, ref) < 0: u = -u
    udir[i] = u / max(np.linalg.norm(u), 1e-12)

def walk(p0, d0, dist, record_at):
    """Walk on the surface from p0 along tangent dir d0; return {dist: point}."""
    p = p0.copy(); d = d0.copy(); out = {}
    step = 0.0035; travelled = 0.0; rec = sorted(record_at)
    while travelled < dist - 1e-9:
        h = min(step, dist - travelled)
        q = p + d * h
        loc, nn, _ = surf_project(q)
        p = loc
        d = d - nn * float(np.dot(d, nn)); d /= max(np.linalg.norm(d), 1e-12)
        travelled += h
        while rec and travelled >= rec[0] - 1e-9:
            out[rec.pop(0)] = p.copy()
    return out

rows = {}   # name -> (N,3) array
for side, sgn in (("tis", +1.0), ("jaw", -1.0)):
    body = np.zeros((N, 3)); supp = np.zeros((N, 3))
    for i in range(N):
        got = walk(lip[i], udir[i] * sgn, 0.045, [0.020, 0.045])
        body[i] = got[0.020]; supp[i] = got[0.045]
    rows[side + "_body"] = body; rows[side + "_support"] = supp
# smooth walked rows lightly along the row, reproject, endpoints fixed
for k in list(rows):
    R = rows[k]
    for _ in range(3):
        S = R.copy()
        S[1:-1] = R[1:-1] + 0.30 * (0.5 * (R[:-2] + R[2:]) - R[1:-1])
        R = S
    for i in range(1, N - 1):
        p, _, _ = surf_project(R[i]); R[i] = p
    rows[k] = R
rows["edge"] = lip.copy()
# philtrum pinch (F-M5): centre columns of upper body/support, inward along -normal
cen = N // 2
for k, depth in (("tis_body", 0.0030), ("tis_support", 0.0020)):
    R = rows[k]
    for di in range(-3, 4):
        wgt = math.cos(di / 3.0 * math.pi / 2) ** 2
        R[cen + di] = R[cen + di] - nrm[cen + di] * (depth * wgt)
    rows[k] = R
LOG["philtrum"] = {"body_depth": 0.0030, "support_depth": 0.0020, "halfwidth_cols": 3}
# margin rows: tucked into the cavity from the edge, tapered at the ends.
# Depth is CAPPED per column by the measured rim->teeth clearance (both
# arcades): at the side-front columns the vestibule is only ~0.011 deep
# (rim col 16 clearance 0.0107) against a nominal 0.022 tuck, and the first
# builds interpenetrated the upper teeth there (29 tri pairs) and each other.
# Cap = 0.55 x clearance; the front (clearance 0.08-0.10) keeps the full tuck.
def _teeth_bvh(obj, shift):
    vs = [tuple(np.array(tuple(v.co)) + shift) for v in obj.data.vertices]
    ts = []
    for p in obj.data.polygons:
        for t in range(1, len(p.vertices) - 1): ts.append((p.vertices[0], p.vertices[t], p.vertices[t + 1]))
    return BVHTree.FromPolygons([Vector(v) for v in vs], ts, all_triangles=True)
_bvh_tu = _teeth_bvh(O["TeethUpper"], np.zeros(3))
_bvh_tl = _teeth_bvh(O["TeethLower"], H)
teeth_clear = np.zeros(N)
for i in range(N):
    du = _bvh_tu.find_nearest(Vector(tuple(lip[i])))[3]
    dl = _bvh_tl.find_nearest(Vector(tuple(lip[i])))[3]
    teeth_clear[i] = min(float(du), float(dl))
depth_cap = np.minimum(1.0, 0.55 * teeth_clear / 0.022)
LOG["margin_depth_cap"] = {"min": round(float(depth_cap.min()), 3), "cols_at_full": int((depth_cap >= 0.999).sum()),
                           "teeth_clear_min": round(float(teeth_clear.min()), 4)}
def taper(i):
    t = min(i, N - 1 - i) / (0.15 * N)
    t = min(1.0, max(0.0, t))
    return 0.30 + 0.70 * (t * t * (3 - 2 * t))
_mrows = {}
for side, zturn in (("tis", +1.0), ("jaw", -1.0)):   # each margin hugs its OWN shell: tissue rises toward the palate vault, jaw sinks toward the mouth floor (v5.0 had the signs flipped -- the margins crossed in the slit and the jaw margin climbed into the upper teeth)
    m1 = np.zeros((N, 3)); m2 = np.zeros((N, 3))
    for i in range(N):
        tp = taper(i) * depth_cap[i]
        d1 = -nrm[i] * 0.25 + np.array([0, -1, 0]) * 0.25 + np.array([0, 0, zturn]) * 0.85
        d1 /= np.linalg.norm(d1)
        m1[i] = lip[i] + d1 * (0.011 * tp)
        d2 = np.array([0, -1, 0]) * 0.85 + np.array([0, 0, zturn]) * 0.35
        d2 /= np.linalg.norm(d2)
        m2[i] = m1[i] + d2 * (0.011 * tp)
    _mrows[side + "_margin1"] = m1; _mrows[side + "_margin2"] = m2
# separation pass: in the cheek-pouch columns the two margin strips still met
# (9 tri pairs at rest). Push cross pairs apart per column to >= 0.0035.
_sep_pairs = (("tis_margin1", "jaw_margin1"), ("tis_margin1", "jaw_margin2"),
              ("tis_margin2", "jaw_margin1"), ("tis_margin2", "jaw_margin2"))
for _ in range(3):
    for i in range(N):
        for ra, rb in _sep_pairs:
            pa = _mrows[ra][i]; pb = _mrows[rb][i]
            d = pa - pb; dist = float(np.linalg.norm(d))
            if 1e-9 < dist < 0.0035:
                u = d / dist; push = (0.0035 - dist) * 0.5 + 0.0004
                fa = 0.6 if ra.endswith("1") else 1.0
                fb = 0.6 if rb.endswith("1") else 1.0
                _mrows[ra][i] = pa + u * push * fa
                _mrows[rb][i] = pb - u * push * fb
rows.update(_mrows)
LOG["margin_separation_pass"] = "3 iterations, target 0.0035"
# pinch end columns toward the commissure points (the F-M7 poles; 0.92 not 1.0
# so the pole is a tight cluster of distinct verts and end cells stay valid quads)
PINCH = [0.92, 0.60, 0.40, 0.25, 0.12]
for k in list(rows):
    if k == "edge": continue
    R = rows[k]
    for c, w in enumerate(PINCH):
        R[c] = (1 - w) * R[c] + w * lip[0]
        R[N - 1 - c] = (1 - w) * R[N - 1 - c] + w * lip[-1]
    rows[k] = R
# cage symmetry check on the edge row
sym_err = max(float(np.linalg.norm(lip[i] - np.array([-lip[N - 1 - i][0], lip[N - 1 - i][1], lip[N - 1 - i][2]]))) for i in range(N))
LOG["edge_symmetry_max_err"] = round(sym_err, 6)

ROW_ORDER = ["tis_support", "tis_body", "edge", "tis_margin1", "tis_margin2",
             "jaw_margin2", "jaw_margin1", "jaw_edge_dummy", "jaw_body", "jaw_support"]
# NOTE: jaw side reuses 'edge' as its rim row; ROW_ORDER above is documentary only.

# ---------------------------------------------------------------- band deletion field
# nearest point on lip polyline per vertex: distance + parameter + side sign
segs_a = lip[:-1]; segs_b = lip[1:]
segd = segs_b - segs_a
seglen = np.linalg.norm(segd, axis=1)
cum = np.concatenate([[0], np.cumsum(seglen)])
tot = cum[-1]
def lip_field(P):
    """returns dist, s_frac, side(+1 tissue / -1 jaw) for points P (M,3)."""
    M = len(P)
    dist = np.full(M, 1e9); sfrac = np.zeros(M); side = np.ones(M)
    qbest = np.zeros((M, 3)); over = np.zeros(M)
    for s in range(len(segs_a)):
        a = segs_a[s]; ab = segd[s]
        traw = np.einsum('ij,j->i', P - a, ab) / max(float(ab @ ab), 1e-12)
        tt = np.clip(traw, 0, 1)
        q = a + tt[:, None] * ab
        d = np.linalg.norm(P - q, axis=1)
        upd = d < dist
        if upd.any():
            dist[upd] = d[upd]
            qbest[upd] = q[upd]
            sfrac[upd] = (cum[s] + tt[upd] * seglen[s]) / tot
            # overshoot: arc length beyond the polyline ends (end segments only)
            ov = np.where(s == 0, np.maximum(0.0, -traw) * seglen[s], 0.0)
            ov = np.where(s == len(segs_a) - 1, np.maximum(ov, np.maximum(0.0, traw - 1) * seglen[s]), ov)
            over[upd] = ov[upd]
            # side: sign of dot(P-q, tissue walk dir at nearest column)
            col = np.clip(np.round(sfrac[upd] * (N - 1)).astype(int), 0, N - 1)
            sgn = np.sign(np.einsum('ij,ij->i', (P - q)[upd], udir[col]))
            side[upd] = np.where(sgn == 0, 1.0, sgn)
    return dist, sfrac, side, qbest, over
fcent = np.array([V[list(f)].mean(axis=0) for f in faces])
def thr(s):
    u = min(abs(s), abs(1 - s)) / 0.10
    u = min(1.0, max(0.0, u))
    return 0.052 * (0.75 + 0.25 * (u * u * (3 - 2 * u)))
# GEODESIC band field: multi-source Dijkstra over merged-mesh edges from the
# lip-line samples. (v5.0 used 3D Euclidean distance and deleted a disconnected
# island on the cheek where the surface folds near the seam; a geodesic
# sublevel set is connected by construction, and interior sheets behind the
# lips are far away along the surface, so no normal guard is needed.)
import heapq
from collections import defaultdict
src_s = {}
for i in range(N):
    d = np.linalg.norm(V - lip[i], axis=1)
    for vi in np.where(d < 0.009)[0]:
        s_i = i / (N - 1)
        if vi not in src_s or abs(s_i - 0.5) < abs(src_s[vi] - 0.5): src_s[vi] = s_i
LOG["dijkstra_sources"] = len(src_s)
gadj = defaultdict(list)
for a, b in edges:
    w = float(np.linalg.norm(V[a] - V[b]))
    gadj[a].append((b, w)); gadj[b].append((a, w))
gdist = np.full(NV, np.inf); slab = np.full(NV, -1.0)
pq = []
for vi, s_i in src_s.items():
    gdist[vi] = 0.0; slab[vi] = s_i; heapq.heappush(pq, (0.0, vi))
while pq:
    du, u = heapq.heappop(pq)
    if du > gdist[u] + 1e-12: continue
    for w, wt in gadj[u]:
        nd = du + wt
        if nd < gdist[w] - 1e-12:
            gdist[w] = nd; slab[w] = slab[u]; heapq.heappush(pq, (nd, w))
_, _, _, _, fover = lip_field(fcent)
def face_delete(fi, f):
    if fover[fi] > 0.010: return False   # flush end cut at the commissures
    if any(np.isinf(gdist[i]) for i in f): return False
    sf = float(np.mean([slab[i] for i in f]))
    return all(gdist[i] < thr(sf) for i in f)
delete = np.array([face_delete(fi, f) for fi, f in enumerate(faces)])
keep_faces = [f for f, d in zip(faces, delete) if not d]
keep_owner = [o for o, d in zip(face_owner, delete) if not d]
LOG["deleted_faces"] = int(delete.sum())
# boundary loops of the kept merged mesh; the hole = the loop nearest the lip line
from collections import Counter, defaultdict
ecnt = Counter()
for f in keep_faces:
    for i in range(len(f)):
        a, b = f[i], f[(i + 1) % len(f)]
        ecnt[(min(a, b), max(a, b))] += 1
bnd_edges = [e for e, c in ecnt.items() if c == 1]
hole_adj = defaultdict(list)
for a, b in bnd_edges:
    hole_adj[a].append(b); hole_adj[b].append(a)
seen = set(); loops = []
for s0 in sorted(hole_adj):
    if s0 in seen: continue
    lp = [s0]; seen.add(s0); prev, cur = -1, s0
    while True:
        nxt = [w for w in hole_adj[cur] if w != prev]
        if not nxt: break
        w = nxt[0]
        if w == s0: break
        if w in seen: break
        lp.append(w); seen.add(w); prev, cur = cur, w
    loops.append(lp)
def loop_lip_dist(lp):
    P = V[lp]
    return float(np.mean([np.min(np.linalg.norm(lip - p, axis=1)) for p in P]))
loop_info = sorted(((loop_lip_dist(lp), len(lp)) for lp in loops))
LOG["kept_mesh_boundary_loops"] = [(round(d, 4), n) for d, n in loop_info]
hole_loop = min(loops, key=loop_lip_dist)
LOG["hole_loop_len"] = len(hole_loop)
assert loop_lip_dist(hole_loop) < 0.05, "hole loop selection failed"
_hs = set(hole_loop)
LOG["hole_loop_closed"] = all(hole_loop[(k + 1) % len(hole_loop)] in hole_adj[hole_loop[k]] for k in range(len(hole_loop)))
LOG["hole_loop_degrees"] = {d: sum(1 for i in _hs if len(hole_adj[i]) == d) for d in (1, 2, 3, 4)}

# ---------------------------------------------------------------- new verts: cage grid + corner pts
newV = []
def add_new(p):
    newV.append(np.array(p, float)); return NV + len(newV) - 1
grid = {}   # row name -> list of merged indices
for name in ("tis_support", "tis_body", "edge", "tis_margin1", "tis_margin2",
             "jaw_margin2", "jaw_margin1", "jaw_body", "jaw_support"):
    grid[name] = [add_new(rows[name][i]) for i in range(N)]
# cage outer loop: tis_support L->R then jaw_support R->L; the loop closes with
# chords across the commissures (the hole is cut flush there, so no corner
# points reaching behind the commissure are needed -- or wanted: they used to
# sit on kept surface the flush cut now preserves)
cage_loop = grid["tis_support"] + grid["jaw_support"][::-1]
LOG["cage_outer_loop_len"] = len(cage_loop)

# ---------------------------------------------------------------- faces: grid + bridge
new_faces = []   # (verts tuple, owner 'T'/'J')
def quad(a, b, c, d, owner):
    new_faces.append(((a, b, c, d), owner))
for r0, r1, owner in (("tis_support", "tis_body", "T"), ("tis_body", "edge", "T"),
                      ("edge", "tis_margin1", "T"), ("tis_margin1", "tis_margin2", "T"),
                      ("jaw_margin2", "jaw_margin1", "J"), ("jaw_margin1", "edge", "J"),
                      ("edge", "jaw_body", "J"), ("jaw_body", "jaw_support", "J")):
    A, B = grid[r0], grid[r1]
    for i in range(N - 1):
        quad(A[i], A[i + 1], B[i + 1], B[i], owner)
N_GRID = len(new_faces)   # grid faces precede bridge faces in new_faces
# bridge: loop-to-loop between hole_loop (old verts) and cage_loop (new verts)
# via bmesh.ops.bridge_loops. Three hand-rolled walks failed identically (one
# cross-head triangle each): the hole boundary WEAVES at the commissures --
# the geodesic band has a finger past each commissure along the seam, so the
# boundary goes tissue->jaw->tissue within a few steps and no sequential
# pairing rule that assumes one clean traversal of the strip survives it.
# bridge_loops does a global loop-to-loop match and handles the weave.
import bmesh
HP = [V[i] for i in hole_loop]
CP = [V[i] if i < NV else newV[i - NV] for i in cage_loop]
nh_, nc_ = len(hole_loop), len(cage_loop)
HK = CK = None
bm = bmesh.new()
bv = {}
for idx, p in zip(hole_loop, HP): bv[idx] = bm.verts.new(tuple(float(x) for x in p))
for idx, p in zip(cage_loop, CP): bv[idx] = bm.verts.new(tuple(float(x) for x in p))
for loop in (hole_loop, cage_loop):
    for a, b in zip(loop, loop[1:] + loop[:1]):
        bm.edges.new((bv[a], bv[b]))
bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table()
res = bmesh.ops.bridge_loops(bm, edges=list(bm.edges))
inv = {v: i for i, v in bv.items()}
bridge = [tuple(inv[v] for v in f.verts) for f in res["faces"]]
bm.free()
LOG["bridge_tris"] = len(bridge)
def p_of(idx): return V[idx] if idx < NV else newV[idx - NV]
max_be = 0.0; worst = None
for t in bridge:
    for a, b in ((0, 1), (1, 2), (2, 0)):
        e = float(np.linalg.norm(p_of(t[a]) - p_of(t[b])))
        if e > max_be: max_be, worst = e, t
LOG["bridge_max_edge"] = round(max_be, 4)
_bl = [float(np.linalg.norm(p_of(t[a]) - p_of(t[b]))) for t in bridge for a, b in ((0, 1), (1, 2), (2, 0))]
LOG["bridge_edge_stats"] = {"mean": round(float(np.mean(_bl)), 4), "p95": round(float(np.percentile(_bl, 95)), 4),
                            "n_over_0.06": int(sum(1 for e in _bl if e > 0.06))}
if max_be >= 0.12:
    dbg = {"hole_pts": [np.round(p, 4).tolist() for p in HP], "hole_ids": [int(x) for x in hole_loop],
           "cage_pts": [np.round(p, 4).tolist() for p in CP], "cage_ids": [int(x) for x in cage_loop],
           "bridge_faces": [[int(x) for x in t] for t in bridge],
           "worst_tri_ids": [int(x) for x in worst],
           "worst_tri_pts": [np.round(p_of(x), 4).tolist() for x in worst],
           "hole_closed": LOG.get("hole_loop_closed"), "hole_degrees": LOG.get("hole_loop_degrees")}
    json.dump(dbg, open(WORK + "/bridge_debug.json", "w"), indent=1)
    print("BRIDGE_DEBUG_WRITTEN worst", worst, [np.round(p_of(x), 4).tolist() for x in worst])
assert max_be < 0.12, f"bridge produced a long edge ({max_be:.3f}) -- pairing failed"
# Bridge owner split by VOTE + PROPAGATION, not the analytic jaw_test: the hole
# boundary weaves across the seam line at the commissures, so a centroid rule
# zigzags and fragments the jaw object's boundary into stray 1-edge chains.
# Hole verts vote their kept-face owner; cage verts vote their row side; tied
# faces inherit from bridge neighbours (BFS), so each object's bridge region
# stays one contiguous band.
hole_vote = {}
for f, o in zip(keep_faces, keep_owner):
    for i in f:
        if i in _hs:
            hole_vote.setdefault(i, {"T": 0, "J": 0})[o] += 1
cage_vote = {}
for i in grid["tis_support"]: cage_vote[i] = "T"
for i in grid["jaw_support"]: cage_vote[i] = "J"
NB = len(bridge)
b_owner = [None] * NB
for bi, t in enumerate(bridge):
    s = 0
    for i in t:
        if i in hole_vote:
            v = hole_vote[i]; s += (1 if v["J"] > v["T"] else -1 if v["T"] > v["J"] else 0)
        elif i in cage_vote:
            s += (1 if cage_vote[i] == "J" else -1)
    if s > 0: b_owner[bi] = "J"
    elif s < 0: b_owner[bi] = "T"
edge2b = {}
for bi, t in enumerate(bridge):
    for a, b in ((0, 1), (1, 2), (2, 0)):
        edge2b.setdefault(tuple(sorted((t[a], t[b]))), []).append(bi)
from collections import deque
dq = deque(bi for bi in range(NB) if b_owner[bi])
while dq:
    bi = dq.popleft()
    for a, b in ((0, 1), (1, 2), (2, 0)):
        for nb_ in edge2b.get(tuple(sorted((bridge[bi][a], bridge[bi][b]))), []):
            if b_owner[nb_] is None:
                b_owner[nb_] = b_owner[bi]; dq.append(nb_)
for bi, t in enumerate(bridge):
    if b_owner[bi] is None:
        fcen = np.mean([V[k] if k < NV else newV[k - NV] for k in t], axis=0)
        b_owner[bi] = "J" if jaw_test(fcen) else "T"
LOG["bridge_split"] = {"T": b_owner.count("T"), "J": b_owner.count("J")}
for t, o in zip(bridge, b_owner):
    new_faces.append((tuple(t), o))

# ---------------------------------------------------------------- assemble merged v5 + normal repair
Vall = np.vstack([V, np.array(newV)])
all_faces = list(keep_faces) + [f for f, _ in new_faces]
all_owner = list(keep_owner) + [o for _, o in new_faces]
LOG["v5_merged_verts"] = len(Vall); LOG["v5_merged_faces"] = len(all_faces)
# Orientation. The grid is one continuous strip built with uniform winding, so a
# single test fixes it: the centre tis_body quad's normal must agree with the
# original surface (BVH) normal; if not, reverse every grid quad. (Per-face BVH
# tests -- v5.0 -- are wrong for the margin rows, whose correct side faces the
# cavity; and BFS across the merged mesh cannot orient the lip-line edge, which
# carries 4 faces in the merged intermediate: it is interior to BOTH objects.)
nkept = len(keep_faces)
cen_i = N // 2
gf = new_faces[(1 * (N - 1)) + cen_i][0]    # tis_body -> edge quad at the centre column
gp = Vall[list(gf)]
gn = np.cross(gp[1] - gp[0], gp[2] - gp[0]); gn /= max(np.linalg.norm(gn), 1e-12)
_, refn, _ = surf_project(gp.mean(axis=0))
grid_flip = bool(np.dot(gn, refn) < 0)
LOG["grid_winding_flipped"] = grid_flip
if grid_flip:
    new_faces = [(tuple(reversed(f)), o) if k < N_GRID else (f, o) for k, (f, o) in enumerate(new_faces)]
    all_faces = list(keep_faces) + [f for f, _ in new_faces]
# BFS propagation for the BRIDGE faces only, seeded by kept + grid faces (both
# pre-oriented, never flipped): a bridge face is flipped as needed so shared
# edges are traversed oppositely.
from collections import deque
NF = len(all_faces)
edge_map = defaultdict(list)   # (a,b) sorted -> [(face, dir)] dir=+1 if face goes a->b
for fi, f in enumerate(all_faces):
    for i in range(len(f)):
        a, b = f[i], f[(i + 1) % len(f)]
        edge_map[(min(a, b), max(a, b))].append((fi, 1 if a < b else -1))
flip = [None] * NF
for fi in range(nkept + N_GRID): flip[fi] = False
dq = deque(range(nkept + N_GRID))
while dq:
    fi = dq.popleft()
    f = all_faces[fi]
    for i in range(len(f)):
        a, b = f[i], f[(i + 1) % len(f)]
        key = (min(a, b), max(a, b))
        mydir = (1 if a < b else -1) * (-1 if flip[fi] else 1)
        for fj, dj in edge_map[key]:
            if fj == fi or flip[fj] is not None: continue
            want = -mydir          # neighbour must traverse the edge oppositely
            flip[fj] = (dj != want)
            dq.append(fj)
unreached = sum(1 for x in flip if x is None)
for fi in range(NF):
    if flip[fi] is None: flip[fi] = False
nflip = sum(1 for fi in range(nkept, NF) if flip[fi])
all_faces = [tuple(reversed(f)) if flip[fi] else f for fi, f in enumerate(all_faces)]
LOG["orientation"] = {"new_faces_flipped_by_propagation": int(nflip), "faces_unreached_by_bfs": int(unreached)}
edir = Counter(); eund = Counter()
for f in all_faces:
    for i in range(len(f)):
        a, b = f[i], f[(i + 1) % len(f)]
        edir[(a, b)] += 1; eund[(min(a, b), max(a, b))] += 1
incons = sum(1 for (a, b), c in edir.items() if c == 2 and edir[(b, a)] == 0 and eund[(min(a, b), max(a, b))] == 2)
LOG["orientation"]["merged_inconsistent_edges"] = int(incons)
LOG["orientation"]["merged_edges_with_gt2_faces"] = int(sum(1 for c in eund.values() if c > 2))
# degenerate census among new faces
deg = 0
for f, _ in new_faces:
    p = Vall[list(f)]
    a = 0.5 * np.linalg.norm(np.cross(p[1] - p[0], p[2] - p[0]))
    if a < 1e-9: deg += 1
LOG["new_faces_degenerate_area"] = deg

# ---------------------------------------------------------------- split back into objects
def build_object(owner_tag, shift):
    pool = {}; nv = []; nf = []
    for f, o in zip(all_faces, all_owner):
        if o != owner_tag: continue
        row = []
        for idx in f:
            if idx not in pool:
                pool[idx] = len(nv); nv.append(tuple(Vall[idx] - shift))
            row.append(pool[idx])
        nf.append(row)
    return nv, nf, pool
tis_nv, tis_nf, tis_pool = build_object("T", np.zeros(3))
jaw_nv, jaw_nf, jaw_pool = build_object("J", H)
LOG["tissue"] = {"verts": len(tis_nv), "faces": len(tis_nf)}
LOG["jaw"] = {"verts": len(jaw_nv), "faces": len(jaw_nf)}
def swap_mesh(obj, nv, nf):
    old = obj.data
    m2 = bpy.data.meshes.new(obj.name + "_v5")
    m2.from_pydata(nv, [], nf); m2.update()
    obj.data = m2
    bpy.data.meshes.remove(old)
swap_mesh(TIS, tis_nv, tis_nf)
swap_mesh(JAW, jaw_nv, jaw_nf)

# cage membership in per-object indices (for groups)
def cage_members(pool, names):
    out = {}
    for nm in names:   # column order preserved (Philtrum slices by column)
        out[nm] = [pool[grid[nm][i]] for i in range(N) if grid[nm][i] in pool]
    return out
tis_cage = cage_members(tis_pool, ["tis_support", "tis_body", "edge", "tis_margin1", "tis_margin2"])
jaw_cage = cage_members(jaw_pool, ["jaw_support", "jaw_body", "edge", "jaw_margin1", "jaw_margin2"])

# ---------------------------------------------------------------- layers regen (build_v4b recipes)
T4 = TIS; J4 = JAW
T4.data.update()
top4 = max(v.co.z for v in T4.data.vertices)
nose_y4 = max(v.co.y for v in T4.data.vertices)
pal = max(v.co.z for v in O["TeethUpper"].data.vertices if v.co.y > 0.18)
LOG["pal_z"] = round(pal, 4)
def ramp(v, a, b):
    t = max(0.0, min(1.0, (v - a) / (b - a))); return t * t * (3 - 2 * t)
tpos = np.array([tuple(v.co) for v in T4.data.vertices])
tnor = np.array([tuple(v.normal) for v in T4.data.vertices])
thick = np.array([0.009 + 0.005 * ramp(w[1], 0.05, 0.35) - 0.002 * ramp(w[2], top4 - 0.15, top4) for w in tpos])
skull_pos = tpos - tnor * thick[:, None]
tfaces = [tuple(p.vertices) for p in T4.data.polygons]
tcent = np.array([tpos[list(f)].mean(axis=0) for f in tfaces])
def muscle_test(c):
    tempo = -0.30 <= c[1] <= 0.06 and c[2] >= pal + 0.10 and abs(c[0]) >= 0.09
    mass = -0.12 <= c[1] <= 0.10 and pal - 0.01 <= c[2] <= pal + 0.11 and abs(c[0]) >= 0.115
    return tempo or mass
mus_mask = np.array([muscle_test(c) for c in tcent])
def part_from(pos, faces, mask, name, push=0.0, nors=None):
    used = {}; nv = []; nf = []
    for f, m in zip(faces, mask):
        if not m: continue
        row = []
        for i in f:
            if i not in used:
                p = pos[i] + (nors[i] * push if push else 0.0)
                used[i] = len(nv); nv.append(tuple(p))
            row.append(used[i])
        nf.append(row)
    ob = bpy.data.objects[name]
    old = ob.data
    m2 = bpy.data.meshes.new(name + "_v5"); m2.from_pydata(nv, [], nf); m2.update()
    ob.data = m2; bpy.data.meshes.remove(old)
    return ob
SK = part_from(skull_pos, tfaces, ~mus_mask, "Skull")
tmp = bpy.data.meshes.new("tmp"); tmp.from_pydata([tuple(p) for p in skull_pos], [], tfaces); tmp.update()
sk_nor = np.array([tuple(v.normal) for v in tmp.vertices])
bpy.data.meshes.remove(tmp)
MU = part_from(skull_pos, tfaces, mus_mask, "Muscles", push=0.0045, nors=sk_nor)
J4.data.update()
jpos = np.array([tuple(v.co) for v in J4.data.vertices])
jnor = np.array([tuple(v.normal) for v in J4.data.vertices])
skm_pos = jpos - jnor * 0.008
jfaces = [tuple(p.vertices) for p in J4.data.polygons]
SKM = part_from(skm_pos, jfaces, np.ones(len(jfaces), bool), "SkullMandible")
LOG["layers"] = {"skull": len(SK.data.vertices), "muscles": len(MU.data.vertices), "skullmandible": len(SKM.data.vertices)}

# ---------------------------------------------------------------- groups (build_v4b rules + new)
for ob in (T4, J4):
    for g in list(ob.vertex_groups): ob.vertex_groups.remove(g)
eye_x, eye_y, eye_z = 0.13376, 0.08954, -0.00787   # stageD landmark values, as build_v4b
def mk_groups(ob, gmap):
    for gname, idxs in gmap.items():
        vg = ob.vertex_groups.new(name=gname)
        if idxs: vg.add(list(idxs), 1.0, 'REPLACE')
tv = [v.co for v in T4.data.vertices]
def sel(fn): return [i for i, w in enumerate(tv) if fn(w)]
gt = {}
gt["Muzzle"] = sel(lambda w: w.y > eye_y - 0.02)
gt["MuzzleTip"] = sel(lambda w: w.y > nose_y4 - 0.16)
gt["NoseLeather"] = sel(lambda w: w.y > nose_y4 - 0.09 and abs(w.x) < 0.095)
gt["MuzzleBridge"] = sel(lambda w: w.y > eye_y - 0.02 and w.z > pal + 0.13 and abs(w.x) < 0.105)
gt["Cranium"] = sel(lambda w: w.y <= eye_y + 0.06 and w.z > pal + 0.02)
gt["CraniumDome"] = sel(lambda w: w.z > top4 - 0.13)
gt["CheekL"] = sel(lambda w: abs(w.y + 0.02) < 0.17 and w.z < eye_z + 0.05 and w.x > 0)
gt["CheekR"] = sel(lambda w: abs(w.y + 0.02) < 0.17 and w.z < eye_z + 0.05 and w.x < 0)
for side, sx in (("L", 1), ("R", -1)):
    ec = Vector((sx * eye_x, eye_y, eye_z))
    gt["Brow" + side] = sel(lambda w, ec=ec, sx=sx: (w - ec).length < 0.215 and w.z > eye_z + 0.02 and w.x * sx > 0)
    gt["EyeSocket" + side] = sel(lambda w, ec=ec, sx=sx: (w - ec).length < 0.155 and w.x * sx > 0)
# new groups
lipcage_t = sorted(set().union(*[set(v) for v in tis_cage.values()])) if tis_cage else []
gt["LipCage"] = lipcage_t
ph = sorted(set(tis_cage["tis_body"][max(0, cen - 3):cen + 4]) | set(tis_cage["tis_support"][max(0, cen - 3):cen + 4]))
gt["Philtrum"] = ph
comL_t = sorted({i for i in lipcage_t if abs(tv[i].x - float(lip[0][0])) < 0.013 and abs(tv[i].y - float(lip[0][1])) < 0.013 and abs(tv[i].z - float(lip[0][2])) < 0.013})
comR_t = sorted({i for i in lipcage_t if abs(tv[i].x - float(lip[-1][0])) < 0.013 and abs(tv[i].y - float(lip[-1][1])) < 0.013 and abs(tv[i].z - float(lip[-1][2])) < 0.013})
gt["CommissureL"] = comL_t; gt["CommissureR"] = comR_t
groups = {"TissueHead": gt}
mk_groups(T4, gt)
for ob, tag in ((O["Ear_L"], "L"), (O["Ear_R"], "R")):
    for g in list(ob.vertex_groups): ob.vertex_groups.remove(g)
    vs = [v.co for v in ob.data.vertices]
    low = sorted(vs, key=lambda v: v.z)[:max(8, len(vs) // 7)]
    base = Vector((0, 0, 0))
    for v in low: base += v
    base /= len(low)
    tip = max(vs, key=lambda v: (v - base).length); ax = tip - base; L2 = ax.length
    g = {"Ear_" + tag: list(range(len(vs))),
         "EarBase_" + tag: [i for i, v in enumerate(vs) if ((v - base).dot(ax) / L2) / L2 < 0.38],
         "EarTip_" + tag: [i for i, v in enumerate(vs) if ((v - base).dot(ax) / L2) / L2 > 0.68]}
    groups["Ear_" + tag] = g
    mk_groups(ob, g)
jv = [v.co for v in J4.data.vertices]
lipcage_j = sorted(set().union(*[set(v) for v in jaw_cage.values()])) if jaw_cage else []
comL_j = sorted({i for i in lipcage_j if abs((jv[i].x) - float(lip[0][0])) < 0.013 and abs((jv[i].y + H[1]) - float(lip[0][1])) < 0.013 and abs((jv[i].z + H[2]) - float(lip[0][2])) < 0.013})
comR_j = sorted({i for i in lipcage_j if abs((jv[i].x) - float(lip[-1][0])) < 0.013 and abs((jv[i].y + H[1]) - float(lip[-1][1])) < 0.013 and abs((jv[i].z + H[2]) - float(lip[-1][2])) < 0.013})
gj = {"Jaw": list(range(len(J4.data.vertices))),
      "Chin": [v.index for v in J4.data.vertices if (v.co + Vector(tuple(H))).y > nose_y4 - 0.18],
      "LipCage": lipcage_j, "CommissureL": comL_j, "CommissureR": comR_j}
groups["Jaw"] = gj
mk_groups(J4, gj)
with open(OUT + "/neutral_base_head_v5.groups.json", "w") as f: json.dump(groups, f)
LOG["groups"] = {k: {g: len(v) for g, v in vv.items()} for k, vv in groups.items()}
LOG["cage_counts"] = {"tissue": len(lipcage_t), "jaw": len(lipcage_j),
                      "commissureL": [len(comL_t), len(comL_j)], "commissureR": [len(comR_t), len(comR_j)],
                      "philtrum": len(ph)}

# ---------------------------------------------------------------- save + export
FINAL = ["TissueHead", "Jaw", "Ear_L", "Ear_R", "Eyeball_L", "Eyeball_R", "Iris_L", "Iris_R", "Pupil_L", "Pupil_R",
         "Eyelid_L", "Eyelid_R", "LidMargin_L", "LidMargin_R", "NoseLeather", "TeethUpper", "TeethLower", "Tongue", "Throat",
         "NeckSocket", "NeckSocketDisc"]
bpy.ops.wm.save_as_mainfile(filepath=OUT + "/neutral_base_head_v5.blend")
bpy.ops.object.select_all(action='DESELECT')
for nm in FINAL: bpy.data.objects[nm].select_set(True)
bpy.context.view_layer.objects.active = T4
bpy.ops.export_scene.gltf(filepath=OUT + "/neutral_base_head_v5.glb", export_format='GLB', use_selection=True)
bpy.ops.object.select_all(action='DESELECT')
LOG["objects_total"] = len(bpy.data.objects)
json.dump(LOG, open(WORK + "/build_log_v5.json", "w"), indent=1)
print("BUILD_V5_DONE")
print(json.dumps(LOG, indent=1))
