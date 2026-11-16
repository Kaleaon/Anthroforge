"""MuzzleWidth verdict: ruler (vertex-slab) vs surface-true section, v3 vs v4.
Gate replication + surface measures + attaining-vert forensics + subdivided-unrelaxed control.
Measurement only; modifies no delivered file (control subdivision happens in-memory)."""
import bpy, json, math
import numpy as np
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

V3 = "/home/hatch/workspace/anthroforge-v2/base-head-v3/neutral_base_head_v3.blend"
V4A = "/home/hatch/workspace/anthroforge-v2/base-head-v4/work/stage_v4a.blend"
V4 = "/home/hatch/workspace/anthroforge-v2/base-head-v4/neutral_base_head_v4.blend"
OUT = {}

def cent(vs):
    c = Vector((0, 0, 0))
    for v in vs: c += v
    return c / len(vs)

def world_verts(ob):
    return np.array([tuple(ob.matrix_world @ v.co) for v in ob.data.vertices], float)

def polys_of(ob):
    return [tuple(p.vertices) for p in ob.data.polygons]

def slab_ruler(P, ycan):
    m = np.abs(P[:, 1] - ycan) < 0.02
    S = P[m]
    if len(S) == 0: return None
    return {"width": round(float(S[:, 0].max() - S[:, 0].min()), 4),
            "max_x": round(float(S[:, 0].max()), 4), "min_x": round(float(S[:, 0].min()), 4),
            "n_slab": int(len(S)),
            "argmax": [round(float(v), 4) for v in S[int(np.argmax(S[:, 0]))]],
            "argmin": [round(float(v), 4) for v in S[int(np.argmin(S[:, 0]))]]}

def section(P, F, y):
    """Edge-plane intersections at plane y: x-extent + chord-length (section curve length)."""
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

def measure_head(path, tag):
    bpy.ops.wm.open_mainfile(filepath=path)
    O = {o.name: o for o in bpy.data.objects}
    T = world_verts(O["TissueHead"]); J = world_verts(O["Jaw"])
    TF = polys_of(O["TissueHead"]); JF = [tuple(i + len(T) for i in f) for f in polys_of(O["Jaw"])]
    evs = []
    for nm in ("Eyeball_L", "Eyeball_R"):
        evs += [O[nm].matrix_world @ v.co for v in O[nm].data.vertices]
    el = [v for v in evs if v.x < 0]; er = [v for v in evs if v.x >= 0]
    ec = (cent(el) + cent(er)) / 2
    nose = float(T[:, 1].max()); occ = float(T[:, 1].min())
    ycan = float(ec.y + 0.5 * (nose - ec.y))
    M = np.vstack([T, J]); MF = TF + JF
    r = {"tag": tag, "nose": round(nose, 4), "occ": round(occ, 4), "L": round(nose - occ, 4),
         "eye_centre": [round(float(v), 4) for v in ec], "ycan": round(ycan, 5),
         "ruler_tissue": slab_ruler(T, ycan),
         "ruler_merged": slab_ruler(M, ycan),
         "section_tissue_ycan": section(T, TF, ycan),
         "section_merged_ycan": section(M, MF, ycan)}
    prof_t, prof_m = {}, {}
    for k in range(-5, 6):
        y = ycan + 0.004 * k
        st = section(T, TF, y); sm = section(M, MF, y)
        prof_t[round(y, 4)] = st["width"] if st else None
        prof_m[round(y, 4)] = sm["width"] if sm else None
    r["profile_tissue"] = prof_t; r["profile_merged"] = prof_m
    r["profile_merged_max_in_slab"] = max(v for v in prof_m.values() if v is not None)
    r["profile_tissue_max_in_slab"] = max(v for v in prof_t.values() if v is not None)
    OUT[tag] = r
    return T, TF

# ---------------- v3 + subdivided-unrelaxed control + jaw-slab forensics
T3, TF3 = measure_head(V3, "v3")
bpy.ops.wm.open_mainfile(filepath=V3)
O = {o.name: o for o in bpy.data.objects}
ycan3 = OUT["v3"]["ycan"]
J3 = world_verts(O["Jaw"])
slabJ = J3[np.abs(J3[:, 1] - ycan3) < 0.02]
order = np.argsort(-np.abs(slabJ[:, 0]))
OUT["v3_jaw_slab_top"] = [[round(float(v), 4) for v in slabJ[i]] for i in order[:6]]
OUT["v3_jaw_slab_max_absx"] = round(float(np.abs(slabJ[:, 0]).max()), 4) if len(slabJ) else None
# control: subdivide v3 tissue in-memory, NO relax, re-run tissue slab ruler
eo = O["TissueHead"]
bm = bmesh.new(); bm.from_mesh(eo.data)
bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=1, use_grid_fill=True)
bm.verts.ensure_lookup_table()
TS = np.array([tuple(eo.matrix_world @ v.co) for v in bm.verts], float)
bm.free()
OUT["v3_tissue_subdiv_unrelaxed_ruler"] = slab_ruler(TS, ycan3)
OUT["v3_tissue_subdiv_unrelaxed_section"] = section(TS, None, ycan3) if False else None

# ---------------- stage A output (attribution: A vs B)
T4a, _ = measure_head(V4A, "v4_stageA")
# ---------------- v4 final
T4, TF4 = measure_head(V4, "v4")
OUT["stageA_vs_final_tissue_maxdiff"] = round(float(np.abs(T4a - T4).max()), 6) if T4a.shape == T4.shape else "shape differs"

# ---------------- attaining-vert forensics on v4 tissue
ycan4 = OUT["v4"]["ycan"]
r4 = OUT["v4"]["ruler_tissue"]
set3 = {}
for i, p in enumerate(T3):
    set3[(round(float(p[0]), 4), round(float(p[1]), 4), round(float(p[2]), 4))] = i
mids = {}
for f in TF3:
    for i in range(len(f)):
        a, b = T3[f[i]], T3[f[(i + 1) % len(f)]]
        m = tuple(round(float(v), 4) for v in (a + b) / 2)
        mids[m] = True
def classify(p):
    k = (round(float(p[0]), 4), round(float(p[1]), 4), round(float(p[2]), 4))
    if k in set3: return "original_v3_vert_exact"
    if k in mids: return "subdivision_midpoint_of_v3_edge"
    # nearest v3 vert distance
    d = np.linalg.norm(T3 - np.array(p), axis=1)
    return f"other (nearest v3 vert {d.min():.4f})"
OUT["v4_attaining_argmax_class"] = classify(r4["argmax"])
OUT["v4_attaining_argmin_class"] = classify(r4["argmin"])

# ---------------- BVH: v4 tissue verts vs v3 tissue surface (signed, muzzle band + global)
bpy.ops.wm.open_mainfile(filepath=V3)
O = {o.name: o for o in bpy.data.objects}
tree = BVHTree.FromPolygons([Vector(tuple(v)) for v in T3], TF3)
def signed_dists(P):
    out = np.zeros(len(P))
    for i, p in enumerate(P):
        loc, nrm, idx, dist = tree.find_nearest(Vector(tuple(p)))
        if loc is None: out[i] = np.nan; continue
        s = float(np.dot(np.array(p) - np.array(loc), np.array(nrm)))
        out[i] = dist if s >= 0 else -dist
    return out
sd = signed_dists(T4)
band = np.abs(T4[:, 1] - ycan4) < 0.05
OUT["bvh_v4_vs_v3_tissue"] = {
    "band_n": int(band.sum()),
    "band_max_outward": round(float(np.nanmax(sd[band])), 4),
    "band_mean_signed": round(float(np.nanmean(sd[band])), 4),
    "band_p99_outward": round(float(np.nanpercentile(sd[band], 99)), 4),
    "global_max_outward": round(float(np.nanmax(sd)), 4)}

print("MUZZLE_DIAG_JSON_BEGIN")
print(json.dumps(OUT, indent=1))
print("MUZZLE_DIAG_JSON_END")
