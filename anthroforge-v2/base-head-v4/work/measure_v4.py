"""Final measurement of the v4 deliverable with v3 stageF's rulers, verbatim,
plus facet/seam/teeth metrics computed identically on the delivered v3 and v4 blends."""
import bpy, json, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

V3D = "/home/hatch/workspace/anthroforge-v2/base-head-v3"
V4D = "/home/hatch/workspace/anthroforge-v2/base-head-v4"

def cent(vs):
    c = Vector((0, 0, 0))
    for v in vs: c += v
    return c / len(vs)

def measure(tissue, ears, eye_objs, pal_obj, jaw_obj=None, ear_excl=None):
    tv = [tissue.matrix_world @ v.co for v in tissue.data.vertices]
    tvx = [v for i, v in enumerate(tv) if not ear_excl or i not in ear_excl]
    nose = max(v.y for v in tv); occ = min(v.y for v in tv); L = nose - occ
    top = max(v.z for v in tv)
    pal = max(v.z for v in [pal_obj.matrix_world @ v.co for v in pal_obj.data.vertices] if v.y > 0.18)
    evs = []
    for eo in eye_objs: evs += [eo.matrix_world @ v.co for v in eo.data.vertices]
    el = [v for v in evs if v.x < 0]; er = [v for v in evs if v.x >= 0]
    cl, cr = cent(el), cent(er); ec = (cl + cr) / 2
    ball = max(max(v.x for v in el) - min(v.x for v in el), max(v.y for v in el) - min(v.y for v in el), max(v.z for v in el) - min(v.z for v in el))
    ycan = ec.y + 0.5 * (nose - ec.y)
    sec = [v for v in tv if abs(v.y - ycan) < 0.02]
    cran = [v for v in tvx if ec.y - 0.42 <= v.y <= ec.y - 0.06 and v.z >= top - 0.11]
    estats = []
    for eo in ears:
        vs = [eo.matrix_world @ v.co for v in eo.data.vertices]
        low = sorted(vs, key=lambda v: v.z)[:max(8, len(vs) // 7)]
        b = cent(low); tip = max(vs, key=lambda v: (v - b).length)
        estats.append((b, tip, (tip - b).length))
    eb = (estats[0][0] + estats[1][0]) / 2 if estats else Vector((0, 0, pal + 0.25))
    r = {"L": round(L, 4),
         "ZB": round(max(v.x for v in tvx) - min(v.x for v in tvx), 4),
         "CraniumWidth_domeShell": round(max(v.x for v in cran) - min(v.x for v in cran), 4) if cran else None,
         "MuzzleWidth": round(max(v.x for v in sec) - min(v.x for v in sec), 4) if sec else None,
         "MuzzleDepth": round((max(v.z for v in sec) - pal), 4) if sec else None,
         "SkullHeight_domeRise": round(top - ec.z, 4),
         "MuzzleFrac_antOrbit": round((nose - (ec.y + ball / 2)) / L, 4),
         "OrbitDiameter": round(ball, 4),
         "Interorbital": round(abs(cl.x - cr.x) - ball, 4),
         "OrbitHeight": round(ec.z - pal, 4),
         "OrbitRise": round((max((v.z for v in tv if abs(v.y - ec.y) < 0.03), default=ec.z) - ec.z), 4),
         "EarLength": round((estats[0][2] + estats[1][2]) / 2, 4) if estats else None,
         "EarBaseHeight_abovePalate": round(eb.z - pal, 4) if estats else None,
         "EarBase_belowSkullTop": round(top - eb.z, 4) if estats else None,
         "EarTip_aboveSkullTop": round(max(estats[0][1].z, estats[1][1].z) - top, 4) if estats else None,
         "eye_centre": [round(v, 4) for v in ec], "pal_z": round(pal, 4)}
    hinge_y = eb.y - 0.02
    r["EarTipHeight_abovePalate"] = round((max(estats[0][1].z, estats[1][1].z) - pal), 4) if estats else None
    if jaw_obj is not None:
        jw = [jaw_obj.matrix_world @ v.co for v in jaw_obj.data.vertices]
        band = [v for v in jw if hinge_y - 0.03 <= v.y <= hinge_y + 0.05]
        r["JawLength"] = round(max(v.y for v in jw) - hinge_y, 4)
        r["JawWidth"] = round(max(v.x for v in band) - min(v.x for v in band), 4) if band else None
        r["RamusDepth"] = round(max(v.z for v in band) - min(v.z for v in band), 4) if band else None
        r["FullHeadHeight"] = round(top - min(v.z for v in jw), 4)
    return r

def key5(c):
    return (round(float(c[0]), 5), round(float(c[1]), 5), round(float(c[2]), 5))

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

def surface_metrics():
    """facet dihedral + vertex-normal step + seam roughness on TissueHead+Jaw."""
    T = bpy.data.objects["TissueHead"]; J = bpy.data.objects["Jaw"]
    H = np.array(tuple(J.location))
    Pv = [tuple(v.co) for v in T.data.vertices] + [tuple(np.array(tuple(v.co)) + H) for v in J.data.vertices]
    off = len(T.data.vertices)
    Pf = [tuple(p.vertices) for p in T.data.polygons] + [tuple(i + off for i in p.vertices) for p in J.data.polygons]
    P = np.array(Pv)
    # face normals (on triangles/fan)
    tris = []
    for f in Pf:
        for t in range(1, len(f) - 1): tris.append((f[0], f[t], f[t + 1]))
    tris = np.array(tris)
    fn = np.cross(P[tris[:, 1]] - P[tris[:, 0]], P[tris[:, 2]] - P[tris[:, 0]])
    fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-12)
    cent = P[tris].mean(axis=1)
    # edge -> faces
    from collections import defaultdict
    ef = defaultdict(list)
    for fi, t in enumerate(tris):
        for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            ef[(min(a, b), max(a, b))].append(fi)
    eye_z = -0.00787
    dih, nstep = [], []
    vn = np.zeros_like(P)
    for fi, t in enumerate(tris):
        for vi in t: vn[vi] += fn[fi]
    vn /= np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-12)
    for (a, b), fs in ef.items():
        if len(fs) != 2: continue
        c = cent[fs[0]]
        if abs(c[1] + 0.02) < 0.17 and c[2] < eye_z + 0.05:
            dih.append(math.degrees(math.acos(max(-1, min(1, float(fn[fs[0]] @ fn[fs[1]]))))))
            nstep.append(math.degrees(math.acos(max(-1, min(1, float(vn[a] @ vn[b]))))))
    # seam roughness
    A = {key5(tuple(v.co)) for v in T.data.vertices}
    Bv = [np.array(tuple(v.co)) + H for v in J.data.vertices]
    pts = [p for p in Bv if key5(p) in A]
    return {"cheek_facet_deg": round(float(np.mean(dih)), 2),
            "cheek_vnormal_step_deg": round(float(np.mean(nstep)), 2),
            "seam_rough": round(loop_roughness(pts), 5), "seam_pts": len(pts)}

def teeth_verify(upper_name, lower_names):
    """lower_names: list of objects that rotate with the jaw (split parts)."""
    U = bpy.data.objects[upper_name]
    H = np.array(tuple(bpy.data.objects["Jaw"].location))
    uv = [tuple(v.co) for v in U.data.vertices]
    ut = []
    for p in U.data.polygons:
        for t in range(1, len(p.vertices) - 1): ut.append((p.vertices[0], p.vertices[t], p.vertices[t + 1]))
    tu = BVHTree.FromPolygons([Vector(v) for v in uv], ut, all_triangles=True)
    lv0, lt = [], []
    for nm in lower_names:
        ob = bpy.data.objects[nm]
        base = len(lv0)
        lv0 += [tuple(ob.matrix_world @ v.co) for v in ob.data.vertices]
        for p in ob.data.polygons:
            for t in range(1, len(p.vertices) - 1): lt.append((p.vertices[0] + base, p.vertices[t] + base, p.vertices[t + 1] + base))
    lv0 = np.array(lv0)
    res = {}
    for deg in (-10, -20, -30):
        th = math.radians(deg)
        R = np.array([[1, 0, 0], [0, math.cos(th), -math.sin(th)], [0, math.sin(th), math.cos(th)]])
        lv = (lv0 - H) @ R.T + H
        tl = BVHTree.FromPolygons([Vector(v) for v in lv], lt, all_triangles=True)
        res[str(deg)] = {"overlap_pairs": len(tu.overlap(tl))}
    return res

# ---------------- v3 (fused arcade: verify not applicable; measure with TeethArcade as pal)
bpy.ops.wm.open_mainfile(filepath=V3D + "/neutral_base_head_v3.blend")
O3 = {o.name: o for o in bpy.data.objects}
m3 = measure(O3["TissueHead"], [O3["Ear_L"], O3["Ear_R"]], [O3["Eyeball_L"], O3["Eyeball_R"]], O3["TeethArcade"], O3["Jaw"])
s3 = surface_metrics()
print("V3 measure", json.dumps(m3)); print("V3 surface", json.dumps(s3))

# ---------------- v4
bpy.ops.wm.open_mainfile(filepath=V4D + "/neutral_base_head_v4.blend")
O4 = {o.name: o for o in bpy.data.objects}
m4 = measure(O4["TissueHead"], [O4["Ear_L"], O4["Ear_R"]], [O4["Eyeball_L"], O4["Eyeball_R"]], O4["TeethUpper"], O4["Jaw"])
s4 = surface_metrics()
tv4 = teeth_verify("TeethUpper", ["TeethLower"])
print("V4 measure", json.dumps(m4)); print("V4 surface", json.dumps(s4)); print("V4 teeth", json.dumps(tv4))

v3props = json.load(open(V3D + "/proportions.json"))
TARGETS = v3props["result"]
table, deltas, all_ok = {}, {}, True
for k, row in TARGETS.items():
    v3m = row["measured"]; v4m = m4.get(k)
    d3 = row["dev_pct"]; d4 = round(100 * (v4m - row["target"]) / row["target"], 1) if v4m is not None else None
    ok = (d4 is not None) and abs(d4) <= abs(d3) + 0.05
    all_ok = all_ok and ok
    table[k] = {"measured": v4m, "target": row["target"], "dev_pct": d4, "source": row["source"]}
    deltas[k] = {"v3_measured": v3m, "v4_measured": v4m, "v3_dev_pct": d3, "v4_dev_pct": d4, "within_v3_dev": ok}
props = {"meta": {"L_definition": "nose tip to occiput, tissue Y extent, normalised to 1.0",
                  "targets": "species-head-spec.md neutral column (unchanged from v3)",
                  "note": "v4 = v3 geometry subdivided + sculpt-smoothed, jaw seam re-cut, teeth split. Gates must hold |dev| <= v3's |dev|."},
         "result": table,
         "result_extra": {k: m4[k] for k in ("EarBaseHeight_abovePalate", "EarBase_belowSkullTop", "EarTip_aboveSkullTop", "FullHeadHeight", "eye_centre", "pal_z")},
         "v3_result": {k: v["measured"] for k, v in TARGETS.items()},
         "gate_deltas_v3_to_v4": deltas,
         "all_gates_within_v3_dev": all_ok,
         "surface_metrics": {"v3": s3, "v4": s4},
         "teeth_split_verify_bvh_overlap": tv4}
with open(V4D + "/proportions.json", "w") as f: json.dump(props, f, indent=1)
json.dump({"m3": m3, "s3": s3, "m4": m4, "s4": s4, "teeth": tv4, "all_ok": all_ok},
          open(V4D + "/work/final_measure_v4.json", "w"), indent=1)
print("ALL GATES WITHIN V3 DEV:", all_ok)
print("DELTAS", json.dumps(deltas, indent=1))
