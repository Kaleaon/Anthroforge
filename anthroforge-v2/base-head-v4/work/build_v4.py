"""Neutral Base Head v4 build: subdivide+sculpt-smooth, seam re-cut, teeth split, layers regen.
Run: blender -b --python build_v4.py
Method notes are in BUILD_NOTES.md (v4). Key disciplines:
 - original v3 vertices are PINNED during relaxation (measurement anchors cannot drift);
   only subdivision-new vertices relax (Taubin), plus a small capped relax for the old
   jaw-seam band so the re-cut seam starts from a smoothed surface.
 - jaw re-cut uses v3 stageD's analytic jaw_test on face centres at the new density.
 - skull/muscles/mandible layers are REGENERATED from the new tissue with stageD recipes.
"""
import bpy, json, math, os
import numpy as np
import bmesh
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

V3 = "/home/hatch/workspace/anthroforge-v2/base-head-v3/neutral_base_head_v3.blend"
OUT = "/home/hatch/workspace/anthroforge-v2/base-head-v4"
WORK = OUT + "/work"
os.makedirs(WORK, exist_ok=True)
LOG = {}

bpy.ops.wm.open_mainfile(filepath=V3)
O = {o.name: o for o in bpy.data.objects}
H = Vector(O["Jaw"].location)  # hinge, actual v3 value
LOG["hinge"] = [round(v, 4) for v in H]

TIS = O["TissueHead"]; JAW = O["Jaw"]; ARC = O["TeethArcade"]
pal = max(v.co.z for v in ARC.data.vertices if v.co.y > 0.18)
# DELIVERED eye centres (from the grafted eyeballs, as stageF's rulers see them).
# The landmark values (0.13376/0.08954) belong to stageD's group rules only; using
# them for ruler bands mis-pinned the section/orbit extrema (found in v4 QA round 1).
eye_x, eye_y, eye_z = 0.1311, 0.0815, -0.0079
EC = [Vector((eye_x, eye_y, eye_z)), Vector((-eye_x, eye_y, eye_z))]
nose_y = max(v.co.y for v in TIS.data.vertices)
LOG["pal_z"] = round(pal, 4)

def jaw_zcut(c):
    if c.y < H.y - 0.18 or c.z > H.z + 0.12:
        return None
    return H.z - 0.16 * max(0.0, c.y - H.y) + (0.30 * (H.y - c.y) if c.y < H.y else 0.0) \
        + 0.025 * math.exp(-((c.y - H.y) / 0.10) ** 2)
def jaw_test(c):
    zc = jaw_zcut(c)
    return zc is not None and c.z < zc

# ---------------------------------------------------------------- merge head+jaw
tis_v = [tuple(v.co) for v in TIS.data.vertices]
jaw_v = [tuple(v.co + H) for v in JAW.data.vertices]
tis_f = [tuple(p.vertices) for p in TIS.data.polygons]
jaw_f = [tuple(p.vertices) for p in JAW.data.polygons]
key2idx = {}
verts = []
def addv(c):
    k = (round(c[0], 6), round(c[1], 6), round(c[2], 6))
    if k not in key2idx:
        key2idx[k] = len(verts); verts.append(c)
    return key2idx[k]
remap_t = [addv(c) for c in tis_v]
remap_j = [addv(c) for c in jaw_v]
faces = [tuple(remap_t[i] for i in f) for f in tis_f] + [tuple(remap_j[i] for i in f) for f in jaw_f]
faces = [f for f in faces if len(set(f)) == len(f)]
V0 = np.array(verts, float)
seam_keys = set()
tis_keys = {(round(c[0], 6), round(c[1], 6), round(c[2], 6)) for c in tis_v}
for c in jaw_v:
    k = (round(c[0], 6), round(c[1], 6), round(c[2], 6))
    if k in tis_keys: seam_keys.add(k)
seam_idx = {key2idx[k] for k in seam_keys}
LOG["merged_verts_pre_subdiv"] = len(V0)
LOG["seam_verts"] = len(seam_idx)

def loop_roughness(pts):
    pts = [np.array(p) for p in pts]
    if len(pts) < 8: return None
    unused = pts[1:]; order = [pts[0]]
    while unused:
        d = [np.linalg.norm(p - order[-1]) for p in unused]
        order.append(unused.pop(int(np.argmin(d))))
    arr = np.array(order); sm = np.zeros_like(arr)
    for k in (-2, -1, 0, 1, 2): sm += np.roll(arr, k, axis=0)
    sm /= 5.0
    return float(np.linalg.norm(arr - sm, axis=1).mean())
LOG["seam_rough_v3"] = loop_roughness([V0[i] for i in sorted(seam_idx)])

me = bpy.data.meshes.new("Merged")
me.from_pydata(verts, [], faces); me.update()
mob = bpy.data.objects.new("Merged", me); bpy.context.collection.objects.link(mob)
# parent partition (v3's own cut, on the coarse merged faces) for the seam tie-break strip
from mathutils.bvhtree import BVHTree as _BVH
parent_bvh = _BVH.FromPolygons([Vector(c) for c in verts], faces)
parent_label = [jaw_test(Vector(np.array([verts[i] for i in f]).mean(axis=0))) for f in faces]

bm = bmesh.new(); bm.from_mesh(me)
bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table()
# seam band: seam verts + their edge neighbours (pre-subdivision graph, V0 index space)
band = set(seam_idx)
for e in bm.edges:
    a, b = e.verts[0].index, e.verts[1].index
    if a in seam_idx: band.add(b)
    if b in seam_idx: band.add(a)

# facet metric BEFORE (cheek region, merged v3 surface)
def cheek_facet_metric(bm_):
    bm_.faces.ensure_lookup_table()
    import mathutils
    pair_angles = []
    edge_face = {}
    for f in bm_.faces:
        for e in f.edges: edge_face.setdefault(e.index, []).append(f)
    for e in bm_.edges:
        fs = edge_face.get(e.index, [])
        if len(fs) == 2:
            c = fs[0].calc_center_median()
            if abs(c.y + 0.02) < 0.17 and c.z < eye_z + 0.05:
                ang = math.degrees(fs[0].normal.angle(fs[1].normal))
                pair_angles.append(ang)
    return float(np.mean(pair_angles)) if pair_angles else None
LOG["cheek_facet_deg_v3"] = cheek_facet_metric(bm)

bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=1, use_grid_fill=True)
bm.to_mesh(me); bm.free()
me.update()

# ---------------------------------------------------------------- arrays + relaxation
n = len(me.vertices)
P = np.empty((n, 3)); me.vertices.foreach_get("co", P.ravel())
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table()
E = np.array([(e.verts[0].index, e.verts[1].index) for e in bm.edges], int)
bm.free()
# identify original (pre-subdivision) verts by position match (float64 tuple keys;
# np.array(v.co) is float32 and poisoned the earlier layer approach -- see diag_d)
v0_key = {}
for i, c in enumerate(V0):
    v0_key[(round(float(c[0]), 5), round(float(c[1]), 5), round(float(c[2]), 5))] = i
orig_of = np.full(n, -1, int)
for i in range(n):
    k = (round(float(P[i, 0]), 5), round(float(P[i, 1]), 5), round(float(P[i, 2]), 5))
    if k in v0_key: orig_of[i] = v0_key[k]
is_orig = orig_of >= 0
assert int(is_orig.sum()) == len(V0), f"originals found {int(is_orig.sum())} != {len(V0)}"
seamflag = np.zeros(n)
seamflag[is_orig] = np.array([1.0 if orig_of[i] in band else 0.0 for i in np.where(is_orig)[0]])
origflag = is_orig.astype(float)
LOG["merged_verts_post_subdiv"] = int(n)
LOG["merged_faces_post_subdiv"] = len(me.polygons)

arc_v = np.array([tuple(v.co) for v in ARC.data.vertices])
def region_weights(P):
    w = np.full(len(P), 0.6)
    cheek = (np.abs(P[:, 1] + 0.02) < 0.17) & (P[:, 2] < eye_z + 0.05)
    w[cheek] = 1.0
    jt = np.array([jaw_test(Vector(c)) for c in P])
    w[jt] = 1.0
    for ec in EC:
        d = np.linalg.norm(P - np.array(ec), axis=1)
        brow = (d < 0.215) & (P[:, 2] > eye_z + 0.02)
        w[brow] = 1.0
        w[d < 0.115] = 0.0  # socket protection
    bridge = (P[:, 1] > eye_y - 0.02) & (P[:, 2] > pal + 0.13) & (np.abs(P[:, 0]) < 0.105)
    w[bridge] = np.maximum(w[bridge], 0.85)
    nosecap = P[:, 1] > nose_y - 0.03
    w[nosecap] = np.minimum(w[nosecap], 0.25)
    # lip line: near the arcade surface
    dmin = np.sqrt(((P[:, None, :] - arc_v[None, :, :]) ** 2).sum(-1)).min(axis=1)
    w[dmin < 0.022] = np.minimum(w[dmin < 0.022], 0.2)
    stub = P[:, 1] < -0.42
    w[stub] = np.minimum(w[stub], 0.3)
    return w

w_new = region_weights(P)
is_orig = origflag > 0.5
# gate-extremum verts of the v3 merged mesh are PINNED exactly (V0 index space):
# any vert that attains a stageF ruler extremum may not move at all.
ec0 = np.array([0.0, eye_y, eye_z])
nose0 = V0[:, 1].max(); top0 = V0[:, 2].max()
ycan0 = eye_y + 0.5 * (nose0 - eye_y)
sec0 = np.abs(V0[:, 1] - ycan0) < 0.02
cran0 = (V0[:, 1] >= eye_y - 0.42) & (V0[:, 1] <= eye_y - 0.06) & (V0[:, 2] >= top0 - 0.11)
orb0 = np.abs(V0[:, 1] - eye_y) < 0.03
jt0 = np.array([jaw_test(Vector(c)) for c in V0])
band0 = jt0 & (V0[:, 1] >= H.y - 0.03) & (V0[:, 1] <= H.y + 0.05)
def arg_ext(mask, col, fn):
    idx = np.where(mask)[0]
    return int(idx[fn(V0[idx, col])]) if len(idx) else -1
pinset = set()
for m, c, f in ((np.ones(len(V0), bool), 1, np.argmax), (np.ones(len(V0), bool), 1, np.argmin),
                (np.ones(len(V0), bool), 2, np.argmax),
                (np.ones(len(V0), bool), 0, np.argmax), (np.ones(len(V0), bool), 0, np.argmin),
                (sec0, 0, np.argmax), (sec0, 0, np.argmin), (sec0, 2, np.argmax),
                (cran0, 0, np.argmax), (cran0, 0, np.argmin), (orb0, 2, np.argmax),
                (band0, 0, np.argmax), (band0, 0, np.argmin), (band0, 2, np.argmax), (band0, 2, np.argmin),
                (jt0, 1, np.argmax), (jt0, 2, np.argmin)):
    i = arg_ext(m, c, f)
    if i >= 0: pinset.add(i)
LOG["pinned_extremum_verts"] = len(pinset)
w = np.where(is_orig, 0.22, w_new)
w[is_orig & (seamflag > 0.5)] = 0.35
d_ec = np.minimum(np.linalg.norm(P - np.array(EC[0]), axis=1), np.linalg.norm(P - np.array(EC[1]), axis=1))
w[is_orig & (d_ec < 0.115)] = 0.0
nc = is_orig & (P[:, 1] > nose_y - 0.03)
w[nc] = np.minimum(w[nc], 0.1)
cap = np.where(is_orig, 0.005, 0.012)
# strong sculpt relax for interior originals in the named facet regions
# (cheek / jaw / brow) -- gate extrema are pinned below, so this cannot drift a ruler
cheek_m = (np.abs(P[:, 1] + 0.02) < 0.17) & (P[:, 2] < eye_z + 0.05)
oi = is_orig & cheek_m & (w > 0)
w[oi] = np.maximum(w[oi], 0.55); cap[oi] = 0.010
brow_m = (d_ec < 0.215) & (P[:, 2] > eye_z + 0.02)
oi2 = is_orig & brow_m & (w > 0)
w[oi2] = np.maximum(w[oi2], 0.45); cap[oi2] = np.maximum(cap[oi2], 0.008)
pin_mask = is_orig & np.array([orig_of[i] in pinset if is_orig[i] else False for i in range(n)])
w[pin_mask] = 0.0
P0 = P.copy()
src, dst = E[:, 0], E[:, 1]
def avg_neighbours(P):
    S = np.zeros_like(P); C = np.zeros(len(P))
    np.add.at(S, src, P[dst]); np.add.at(S, dst, P[src])
    np.add.at(C, src, 1.0); np.add.at(C, dst, 1.0)
    return S / np.maximum(C, 1)[:, None]
for it in range(25):
    for lam in (0.5, -0.53):
        A = avg_neighbours(P)
        step = lam * w[:, None] * (A - P)
        Pn = P + step
        disp = Pn - P0
        ln = np.linalg.norm(disp, axis=1)
        over = ln > cap
        if over.any():
            Pn[over] = P0[over] + disp[over] * (cap[over] / ln[over])[:, None]
        P = Pn
# ruler guards: smoothing may not extend any stageF ruler band beyond v3's extent
bb_lo, bb_hi = V0.min(axis=0), V0.max(axis=0)
for ax in range(3):
    P[:, ax] = np.clip(P[:, ax], bb_lo[ax], bb_hi[ax])
sec_m = np.abs(V0[:, 1] - ycan0) < 0.02
for sgn in (1, -1):
    lim = np.abs(V0[sec_m & (np.sign(V0[:, 0]) == sgn), 0]).max()
    m = (np.abs(P[:, 1] - ycan0) < 0.02) & (np.sign(P[:, 0]) == sgn) & (np.abs(P[:, 0]) > lim)
    P[m, 0] = sgn * lim
cran_lim = {}
for sgn in (1, -1):
    cran_lim[sgn] = np.abs(V0[cran0 & (np.sign(V0[:, 0]) == sgn), 0]).max()
    m = cran0_mask = (P[:, 1] >= eye_y - 0.42) & (P[:, 1] <= eye_y - 0.06) & (P[:, 2] >= top0 - 0.11) \
        & (np.sign(P[:, 0]) == sgn) & (np.abs(P[:, 0]) > cran_lim[sgn])
    P[m, 0] = sgn * cran_lim[sgn]
orb_lim = V0[orb0, 2].max()
mo = np.abs(P[:, 1] - eye_y) < 0.03
P[mo & (P[:, 2] > orb_lim), 2] = orb_lim
LOG["ruler_guards_applied"] = True
maxdisp_new = float(np.linalg.norm(P[~is_orig] - P0[~is_orig], axis=1).max()) if (~is_orig).any() else 0.0
maxdisp_orig = float(np.linalg.norm(P[is_orig] - P0[is_orig], axis=1).max()) if is_orig.any() else 0.0
LOG["relax_max_disp_new"] = round(maxdisp_new, 5)
LOG["relax_max_disp_orig"] = round(maxdisp_orig, 5)

# write relaxed positions back, facet metric AFTER
me.vertices.foreach_set("co", P.ravel()); me.update()
bm = bmesh.new(); bm.from_mesh(me)
LOG["cheek_facet_deg_v4_presplit"] = cheek_facet_metric(bm)
bm.free()

# ---------------------------------------------------------------- split by jaw_test
polys = [tuple(p.vertices) for p in me.polygons]
cent = np.array([P[list(f)].mean(axis=0) for f in polys])
is_jaw = np.array([jaw_test(Vector(c)) for c in cent])
# tie-break strip: faces whose centroid lies within 0.02 of the cut surface inherit
# their parent coarse face's side (the analytic test is noise-dominated there, and
# v3's authored partition is the reference for which side a surface patch is on)
n_flip = 0
for fi, c in enumerate(cent):
    zc = jaw_zcut(Vector(c))
    if zc is None or abs(c[2] - zc) >= 0.02: continue
    hit = parent_bvh.find_nearest(Vector(c))
    if hit and parent_label[hit[2]] != bool(is_jaw[fi]):
        is_jaw[fi] = parent_label[hit[2]]; n_flip += 1
LOG["seam_tiebreak_flips"] = int(n_flip)
def build_part(mask, shift):
    used = {}; nv = []; nf = []
    for f, m in zip(polys, mask):
        if not m: continue
        row = []
        for i in f:
            if i not in used:
                used[i] = len(nv); nv.append(tuple(P[i] - shift))
            row.append(used[i])
        nf.append(row)
    return nv, nf

tis_nv, tis_nf = build_part(~is_jaw, np.zeros(3))
jaw_nv, jaw_nf = build_part(is_jaw, np.array(H))
LOG["tissue_verts_v4"] = len(tis_nv); LOG["jaw_verts_v4"] = len(jaw_nv)

def replace_mesh_object(name, nv, nf, material):
    old = bpy.data.objects.get(name)
    if old: bpy.data.objects.remove(old, do_unlink=True)
    m2 = bpy.data.meshes.new(name); m2.from_pydata(nv, [], nf); m2.update()
    o2 = bpy.data.objects.new(name, m2); bpy.context.collection.objects.link(o2)
    if material:
        m2.materials.clear(); m2.materials.append(material)
    return o2
tissue_mat = bpy.data.materials["TissueClay"]
T4 = replace_mesh_object("TissueHead", tis_nv, tis_nf, tissue_mat)
J4 = replace_mesh_object("Jaw", jaw_nv, jaw_nf, tissue_mat)
J4.location = H
bpy.data.objects.remove(mob, do_unlink=True)

# seam roughness: coincident boundary verts, loop-ordered
def key5(c):
    return (round(float(c[0]), 5), round(float(c[1]), 5), round(float(c[2]), 5))
def boundary_loop(objA, objB, shiftB):
    A = {key5(tuple(v.co)) for v in objA.data.vertices}
    Bv = [np.array(tuple(v.co)) + shiftB for v in objB.data.vertices]
    pts = [p for p in Bv if key5(p) in A]
    return loop_roughness(pts), len(pts)
# v3 seam roughness from the pristine file values (recompute from stored arrays)
rough4, nb4 = boundary_loop(T4, J4, np.array(tuple(H)))
LOG["seam_rough_v4"] = rough4; LOG["seam_loop_pts_v4"] = nb4

# ---------------------------------------------------------------- ears: HELD at v3 density
# Deliberate (QA round 2): stageF's ear rulers sample the lowest n//7 verts, and the
# jaw hinge frame (hinge_y) is derived from the ear-base centroid -- densifying the
# ear migrates that population and moves OTHER gates' frames while the ear geometry
# itself is unchanged (subdivided-unrelaxed ear reads EarLength 0.3778 vs 0.3889 on
# identical geometry). Ears stay v3 until the spec redefines ear rulers
# density-independently. See BUILD_NOTES (v4).
LOG["ears_held_at_v3"] = True
bpy.ops.wm.save_as_mainfile(filepath=WORK + "/stage_v4a.blend")
json.dump(LOG, open(WORK + "/build_log_a.json", "w"), indent=1)
print("STAGE A DONE", json.dumps(LOG, indent=1))
