"""Stage B: teeth split (plane scan + BVH verify), layer regen, groups, final save + GLB."""
import bpy, json, math, os
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

OUT = "/home/hatch/workspace/anthroforge-v2/base-head-v4"
WORK = OUT + "/work"
LOG = {}
bpy.ops.wm.open_mainfile(filepath=WORK + "/stage_v4a.blend")
O = {o.name: o for o in bpy.data.objects}
H = Vector(O["Jaw"].location)
Hv = np.array(tuple(H))
eye_x, eye_y, eye_z = 0.13376, 0.08954, -0.00787
ARC = O["TeethArcade"]
pal = max(v.co.z for v in ARC.data.vertices if v.co.y > 0.18)

# ---------------------------------------------------------------- teeth split
V = np.array([tuple(v.co) for v in ARC.data.vertices], float)
FACES = [tuple(p.vertices) for p in ARC.data.polygons]

def clip_poly(pts, gs, keep_pos):
    """Sutherland-Hodgman clip of one polygon against g>=0 (keep_pos) or g<=0."""
    out = []
    m = len(pts)
    for i in range(m):
        a, b = pts[i], pts[(i + 1) % m]
        ga, gb = gs[i], gs[(i + 1) % m]
        ain = ga >= 0 if keep_pos else ga <= 0
        bin_ = gb >= 0 if keep_pos else gb <= 0
        if ain: out.append(a)
        if ain != bin_:
            t = ga / (ga - gb) if ga != gb else 0.0
            out.append(a + t * (b - a))
    return out

def split_arcade(a, b):
    g = V[:, 2] + a * V[:, 1] + b
    parts = {}
    for keep_pos, key in ((True, "up"), (False, "lo")):
        pool = []
        pkey = {}
        tris = []
        def pid(p):
            k = (round(float(p[0]), 6), round(float(p[1]), 6), round(float(p[2]), 6))
            if k not in pkey:
                pkey[k] = len(pool); pool.append(np.array(p))
            return pkey[k]
        for f in FACES:
            pts = [V[i] for i in f]; gs = [g[i] for i in f]
            poly = clip_poly(pts, gs, keep_pos)
            if len(poly) >= 3:
                ids = [pid(p) for p in poly]
                for t in range(1, len(ids) - 1):
                    tris.append((ids[0], ids[t], ids[t + 1]))
        parts[key] = (np.array(pool), tris)
    return parts

def bvh(verts, tris):
    return BVHTree.FromPolygons([Vector(v) for v in verts], tris, all_triangles=True)

def rot_about_H(verts, deg):
    th = math.radians(deg)
    R = np.array([[1, 0, 0], [0, math.cos(th), -math.sin(th)], [0, math.sin(th), math.cos(th)]])
    return (verts - Hv) @ R.T + Hv

def verify(parts):
    up_v, up_t = parts["up"]; lo_v, lo_t = parts["lo"]
    res = {}
    tu = bvh(up_v, up_t)
    for deg in (-10, -20, -30):
        lv = rot_about_H(lo_v, deg)
        tl = bvh(lv, lo_t)
        ov = tu.overlap(tl)
        dmin = 1e9
        for p in lv:
            hit = tu.find_nearest(Vector(p))
            if hit and hit[3] < dmin: dmin = hit[3]
        res[deg] = {"overlap_pairs": len(ov), "min_clearance": round(float(dmin), 5)}
    return res

cands = []
for a in (0.0, 0.05, 0.09, 0.13, 0.18):
    for db in (-0.008, -0.004, 0.0, 0.004, 0.008):
        cands.append((a, 0.2656 + db))
best = None
for a, b in cands:
    parts = split_arcade(a, b)
    if len(parts["up"][1]) == 0 or len(parts["lo"][1]) == 0: continue
    ver = verify(parts)
    ok = all(ver[d]["overlap_pairs"] == 0 for d in ver)
    waist_err = abs((-(a * 0.34 + b)) - (-0.30))
    score = (0 if ok else 1, sum(ver[d]["overlap_pairs"] for d in ver), waist_err)
    if best is None or score < best[0]:
        best = (score, a, b, parts, ver)
    if ok and waist_err < 0.002: break
(score, pa, pb, parts, ver) = best
LOG["teeth_plane"] = {"a": pa, "b": pb, "pass": bool(score[0] == 0), "verify": {str(k): v for k, v in ver.items()},
                      "upper_tris": len(parts["up"][1]), "lower_tris": len(parts["lo"][1]),
                      "upper_verts": len(parts["up"][0]), "lower_verts": len(parts["lo"][0])}
print("TEETH", json.dumps(LOG["teeth_plane"], indent=1))

mouth_mat = bpy.data.materials["MouthInterior"]
def make_obj(name, verts, tris, shift, loc):
    old = bpy.data.objects.get(name)
    if old: bpy.data.objects.remove(old, do_unlink=True)
    m2 = bpy.data.meshes.new(name)
    m2.from_pydata([tuple(v - shift) for v in verts], [], tris); m2.update()
    o2 = bpy.data.objects.new(name, m2); bpy.context.collection.objects.link(o2)
    o2.location = loc
    m2.materials.clear(); m2.materials.append(mouth_mat)
    return o2
TU = make_obj("TeethUpper", parts["up"][0], parts["up"][1], np.zeros(3), (0, 0, 0))
TL = make_obj("TeethLower", parts["lo"][0], parts["lo"][1], Hv, tuple(H))
bpy.data.objects.remove(ARC, do_unlink=True)
pal4 = max(v.co.z for v in TU.data.vertices if v.co.y > 0.18)
LOG["pal_z_v4"] = round(pal4, 4)

# ---------------------------------------------------------------- layers regen (stageD recipes)
T4 = O["TissueHead"]; J4 = O["Jaw"]
T4.data.update()
top4 = max(v.co.y * 0 + v.co.z for v in T4.data.vertices)
nose_y4 = max(v.co.y for v in T4.data.vertices)
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
def part_from(pos, faces, mask, name, material, push=0.0, nors=None):
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
    old = bpy.data.objects.get(name)
    if old: bpy.data.objects.remove(old, do_unlink=True)
    m2 = bpy.data.meshes.new(name); m2.from_pydata(nv, [], nf); m2.update()
    o2 = bpy.data.objects.new(name, m2); bpy.context.collection.objects.link(o2)
    m2.materials.clear(); m2.materials.append(material)
    return o2
bone_mat = bpy.data.materials["Bone"]; mus_mat = bpy.data.materials["Muscle"]
SK = part_from(skull_pos, tfaces, ~mus_mask, "Skull", bone_mat)
# skull vertex normals at muscle verts: recompute from the full skull surface
tmp = bpy.data.meshes.new("tmp"); tmp.from_pydata([tuple(p) for p in skull_pos], [], tfaces); tmp.update()
sk_nor = np.array([tuple(v.normal) for v in tmp.vertices])
bpy.data.meshes.remove(tmp)
MU = part_from(skull_pos, tfaces, mus_mask, "Muscles", mus_mat, push=0.0045, nors=sk_nor)
J4.data.update()
jpos = np.array([tuple(v.co) for v in J4.data.vertices])
jnor = np.array([tuple(v.normal) for v in J4.data.vertices])
skm_pos = jpos - jnor * 0.008
jfaces = [tuple(p.vertices) for p in J4.data.polygons]
SKM = part_from(skm_pos, jfaces, np.ones(len(jfaces), bool), "SkullMandible", bone_mat)
LOG["skull_verts"] = len(SK.data.vertices); LOG["muscles_verts"] = len(MU.data.vertices); LOG["skullmandible_verts"] = len(SKM.data.vertices)

# ---------------------------------------------------------------- groups (stageD rules)
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
groups = {"TissueHead": gt}
mk_groups(T4, gt)
for ob, tag in ((O["Ear_L"], "L"), (O["Ear_R"], "R")):
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
gj = {"Jaw": list(range(len(J4.data.vertices))),
      "Chin": [v.index for v in J4.data.vertices if (v.co + H).y > nose_y4 - 0.18]}
groups["Jaw"] = gj
mk_groups(J4, gj)
with open(OUT + "/neutral_base_head_v4.groups.json", "w") as f: json.dump(groups, f)
LOG["groups"] = {k: {g: len(v) for g, v in vv.items()} for k, vv in groups.items()}

# ---------------------------------------------------------------- save + export
FINAL = ["TissueHead", "Jaw", "Ear_L", "Ear_R", "Eyeball_L", "Eyeball_R", "Iris_L", "Iris_R", "Pupil_L", "Pupil_R",
         "Eyelid_L", "Eyelid_R", "LidMargin_L", "LidMargin_R", "NoseLeather", "TeethUpper", "TeethLower", "Tongue", "Throat",
         "NeckSocket", "NeckSocketDisc"]
bpy.ops.wm.save_as_mainfile(filepath=OUT + "/neutral_base_head_v4.blend")
bpy.ops.object.select_all(action='DESELECT')
for nm in FINAL: bpy.data.objects[nm].select_set(True)
bpy.context.view_layer.objects.active = T4
bpy.ops.export_scene.gltf(filepath=OUT + "/neutral_base_head_v4.glb", export_format='GLB', use_selection=True)
bpy.ops.object.select_all(action='DESELECT')
LOG["objects_total"] = len(bpy.data.objects)
json.dump(LOG, open(WORK + "/build_log_b.json", "w"), indent=1)
print("STAGE B DONE", json.dumps(LOG, indent=1))
