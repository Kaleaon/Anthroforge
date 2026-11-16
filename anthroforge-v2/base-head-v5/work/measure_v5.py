"""Final measurement of the v5 deliverable: v4's stage-F rulers verbatim
(measure_v4.py), MuzzleWidth by the SURFACE-TRUE merged-surface section
(diag_g_muzzle_verdict.py's section(), the governing measure -- the vertex-slab
ruler is superseded, reported for continuity only), surface metrics, and the
teeth-split BVH verify at jaw -10/-20/-30. Measures v4 and v5 side by side;
writes base-head-v5/proportions.json. Modifies no delivered geometry."""
import bpy, json, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

V4D = "/home/hatch/workspace/anthroforge-v2/base-head-v4"
V5D = "/home/hatch/workspace/anthroforge-v2/base-head-v5"

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
    hinge_y = eb.y - 0.02; hinge_z = pal + 0.055
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
    T = bpy.data.objects["TissueHead"]; J = bpy.data.objects["Jaw"]
    H = np.array(tuple(J.location))
    Pv = [tuple(v.co) for v in T.data.vertices] + [tuple(np.array(tuple(v.co)) + H) for v in J.data.vertices]
    off = len(T.data.vertices)
    Pf = [tuple(p.vertices) for p in T.data.polygons] + [tuple(i + off for i in p.vertices) for p in J.data.polygons]
    P = np.array(Pv)
    tris = []
    for f in Pf:
        for t in range(1, len(f) - 1): tris.append((f[0], f[t], f[t + 1]))
    tris = np.array(tris)
    fn = np.cross(P[tris[:, 1]] - P[tris[:, 0]], P[tris[:, 2]] - P[tris[:, 0]])
    fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-12)
    cent_t = P[tris].mean(axis=1)
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
        c = cent_t[fs[0]]
        if abs(c[1] + 0.02) < 0.17 and c[2] < eye_z + 0.05:
            dih.append(math.degrees(math.acos(max(-1, min(1, float(fn[fs[0]] @ fn[fs[1]]))))))
            nstep.append(math.degrees(math.acos(max(-1, min(1, float(vn[a] @ vn[b]))))))
    A = {key5(tuple(v.co)) for v in T.data.vertices}
    Bv = [np.array(tuple(v.co)) + H for v in J.data.vertices]
    pts = [p for p in Bv if key5(p) in A]
    return {"cheek_facet_deg": round(float(np.mean(dih)), 2),
            "cheek_vnormal_step_deg": round(float(np.mean(nstep)), 2),
            "seam_rough": round(loop_roughness(pts), 5), "seam_pts": len(pts)}

def teeth_verify(upper_name, lower_names):
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
        # min clearance between the arcades (vertex-to-surface, both ways sampled on lower verts)
        dmin = 1e9
        for p in lv[::7]:
            _, _, _, dist = tu.find_nearest(Vector(p))
            if dist is not None: dmin = min(dmin, float(dist))
        res[str(deg)] = {"overlap_pairs": len(tu.overlap(tl)), "min_clearance_sampled": round(dmin, 4)}
    return res

# ---- surface-true MuzzleWidth (diag_g's section(), verbatim) ----
def world_verts(ob):
    return np.array([tuple(ob.matrix_world @ v.co) for v in ob.data.vertices], float)

def polys_of(ob):
    return [tuple(p.vertices) for p in ob.data.polygons]

def section(P, F, y):
    xs, chord = [], 0.0
    for f in F:
        pts = P[list(f)]
        hit = []
        for i in range(len(pts)):
            a, b = pts[i], pts[(i + 1) % len(pts)]
            if (a[1] - y) * (b[1] - y) < 0 and a[1] != b[1]:
                t = (y - a[1]) / (b[1] - a[1])
                hit.append(a + t * (b - a))
        if len(hit) == 2:
            xs += [hit[0][0], hit[1][0]]
            chord += float(np.linalg.norm(hit[0] - hit[1]))
        elif len(hit) > 2:
            xs += [h[0] for h in hit]
    if not xs: return None
    return {"width": round(float(max(xs) - min(xs)), 4), "chord_len": round(chord, 4), "n_pts": len(xs)}

def muzzle_surface_true():
    O = {o.name: o for o in bpy.data.objects}
    T = world_verts(O["TissueHead"]); J = world_verts(O["Jaw"])
    TF = polys_of(O["TissueHead"]); JF = [tuple(i + len(T) for i in f) for f in polys_of(O["Jaw"])]
    evs = []
    for nm in ("Eyeball_L", "Eyeball_R"):
        evs += [O[nm].matrix_world @ v.co for v in O[nm].data.vertices]
    el = [v for v in evs if v.x < 0]; er = [v for v in evs if v.x >= 0]
    ec = (cent(el) + cent(er)) / 2
    nose = float(T[:, 1].max())
    ycan = float(ec.y + 0.5 * (nose - ec.y))
    M = np.vstack([T, J]); MF = TF + JF
    sm = section(M, MF, ycan); st = section(T, TF, ycan)
    return {"ycan": round(ycan, 5), "merged": sm, "tissue_only": st}

# ---------------- v4 (reference)
bpy.ops.wm.open_mainfile(filepath=V4D + "/neutral_base_head_v4.blend")
O4 = {o.name: o for o in bpy.data.objects}
m4 = measure(O4["TissueHead"], [O4["Ear_L"], O4["Ear_R"]], [O4["Eyeball_L"], O4["Eyeball_R"]], O4["TeethUpper"], O4["Jaw"])
s4 = surface_metrics()
mw4 = muzzle_surface_true()
print("V4 measure", json.dumps(m4)); print("V4 surface", json.dumps(s4)); print("V4 muzzleST", json.dumps(mw4))

# ---------------- v5
bpy.ops.wm.open_mainfile(filepath=V5D + "/neutral_base_head_v5.blend")
O5 = {o.name: o for o in bpy.data.objects}
m5 = measure(O5["TissueHead"], [O5["Ear_L"], O5["Ear_R"]], [O5["Eyeball_L"], O5["Eyeball_R"]], O5["TeethUpper"], O5["Jaw"])
s5 = surface_metrics()
mw5 = muzzle_surface_true()
tv5 = teeth_verify("TeethUpper", ["TeethLower"])
print("V5 measure", json.dumps(m5)); print("V5 surface", json.dumps(s5)); print("V5 muzzleST", json.dumps(mw5)); print("V5 teeth", json.dumps(tv5))

v4props = json.load(open(V4D + "/proportions.json"))
TARGETS = v4props["result"]
table, deltas, all_ok = {}, {}, True
for k, row in TARGETS.items():
    tgt = row["target"]
    if k == "MuzzleWidth":
        v5m = mw5["merged"]["width"]; v4m = mw4["merged"]["width"]
    else:
        v5m = m5.get(k); v4m = m4.get(k)
    d4 = round(100 * (v4m - tgt) / tgt, 1)
    d5 = round(100 * (v5m - tgt) / tgt, 1) if v5m is not None else None
    ok = (d5 is not None) and abs(d5) <= abs(d4) + 0.05
    all_ok = all_ok and ok
    entry = {"measured": v5m, "target": tgt, "dev_pct": d5, "source": row["source"]}
    if k == "MuzzleWidth":
        entry["measure"] = "surface-true merged-surface section at ycan (governing; vertex-slab superseded)"
        entry["slab_tissue_value"] = m5.get("MuzzleWidth")
        entry["section_chord_len"] = mw5["merged"]["chord_len"]
        entry["ycan"] = mw5["ycan"]
    table[k] = entry
    deltas[k] = {"v4_measured": v4m, "v5_measured": v5m, "v4_dev_pct": d4, "v5_dev_pct": d5, "within_v4_dev": ok}
props = {"meta": {"L_definition": "nose tip to occiput, tissue Y extent, normalised to 1.0",
                  "targets": "species-head-spec.md neutral column (unchanged from v3)",
                  "note": "v5 = v4 + lip-line loop cage (B12 F-M7). Gates must hold |dev| <= v4's |dev|. "
                          "MuzzleWidth is measured SURFACE-TRUE (merged tissue+jaw section at ycan, diag_g method); "
                          "the vertex-slab ruler is superseded (it read 0.2158/0.2332 on v3/v4 where the surface-true "
                          "section reads 0.2413/0.2412 -- the slab scoped TissueHead only and densification moved it). "
                          "Interorbital held at 0.1122 by design (ruling open)."},
         "result": table,
         "result_extra": {k: m5[k] for k in ("EarBaseHeight_abovePalate", "EarBase_belowSkullTop", "EarTip_aboveSkullTop", "FullHeadHeight", "eye_centre", "pal_z")},
         "v4_result": {k: (mw4["merged"]["width"] if k == "MuzzleWidth" else m4.get(k)) for k in TARGETS},
         "gate_deltas_v4_to_v5": deltas,
         "all_gates_within_v4_dev": all_ok,
         "surface_metrics": {"v4": s4, "v5": s5},
         "muzzle_width_surface_true": {"v4": mw4, "v5": mw5},
         "teeth_split_verify_bvh_overlap": tv5}
with open(V5D + "/proportions.json", "w") as f: json.dump(props, f, indent=1)
json.dump({"m4": m4, "s4": s4, "mw4": mw4, "m5": m5, "s5": s5, "mw5": mw5, "teeth": tv5, "all_ok": all_ok},
          open(V5D + "/work/final_measure_v5.json", "w"), indent=1)
print("ALL GATES WITHIN V4 DEV:", all_ok)
print("DELTAS", json.dumps(deltas, indent=1))
