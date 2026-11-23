"""Mouth-open test for base-head-v5 (B12 F-M7 acceptance evidence).

Poses are rigid-object rotations about the hinge H (the v3/v4 jaw mechanism --
no armature exists yet): Jaw and TeethLower carry loc = H and rotate as
objects; Tongue is carried by the same T(H).Rx.T(-H) matrix stageG used.
Measures, at rest and jaw -10/-20/-30 deg:
  (a) rim gap profile between the tissue and jaw lip-line (edge) rows,
      column-matched (the two rows are position duplicates at rest);
  (b) commissure separation (tissue vs jaw commissure-group centroids);
  (c) BVH overlap pairs + sampled min clearances: tissue margin strip vs
      rotated TeethLower, jaw margin strip vs TeethUpper, margin vs margin;
  (d) jaw face sanity under the rigid pose (area / normal drift -- must be ~0).
Plus a synthetic LIP-PART field test: the two edge rows are displaced apart
along their vertex normals (0.01 each at the centre columns, cos^2 falloff),
and the cage strip's strain is measured (max edge stretch, min area ratio,
flipped faces) -- direct evidence the cage can part without tearing.
Margin rows are identified geometrically: cage verts lying OFF the v4 outer
surface (body/support rows were walked on it). Read-only; saves nothing."""
import bpy, json, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

V4 = "/home/hatch/workspace/anthroforge-v2/base-head-v4/neutral_base_head_v4.blend"
V5 = "/home/hatch/workspace/anthroforge-v2/base-head-v5/neutral_base_head_v5.blend"
OUT = {}

def tris_of(obj, vset=None):
    tris = []
    for p in obj.data.polygons:
        vs = tuple(p.vertices)
        if vset is not None and not all(v in vset for v in vs): continue
        for t in range(1, len(vs) - 1): tris.append((vs[0], vs[t], vs[t + 1]))
    return tris

def bvh(pts, tris):
    return BVHTree.FromPolygons([Vector(p) for p in pts], tris, all_triangles=True)

def min_clear(bvh_a, pts_b):
    d = 1e9
    for p in pts_b:
        _, _, _, dist = bvh_a.find_nearest(Vector(p))
        if dist is not None: d = min(d, float(dist))
    return d

# ---- v4 surface (for margin-row discrimination)
bpy.ops.wm.open_mainfile(filepath=V4)
O4 = {o.name: o for o in bpy.data.objects}
H4 = np.array(tuple(O4["Jaw"].location))
P4 = np.vstack([np.array([tuple(v.co) for v in O4["TissueHead"].data.vertices]),
                np.array([tuple(v.co) for v in O4["Jaw"].data.vertices]) + H4])
F4 = tris_of(O4["TissueHead"]) + [tuple(i + len(O4["TissueHead"].data.vertices) for i in t) for t in tris_of(O4["Jaw"])]
bvh4 = bvh(P4, F4)

# ---- v5 scene
bpy.ops.wm.open_mainfile(filepath=V5)
O = {o.name: o for o in bpy.data.objects}
H = np.array(tuple(O["Jaw"].location))
TIS, JAW = O["TissueHead"], O["Jaw"]
tis_w = np.array([tuple(v.co) for v in TIS.data.vertices])                    # identity loc
jaw_w = np.array([tuple(v.co) for v in JAW.data.vertices]) + H
tu_w = np.array([tuple(v.co) for v in O["TeethUpper"].data.vertices])
tl_w = np.array([tuple(O["TeethLower"].matrix_world @ v.co) for v in O["TeethLower"].data.vertices])
tongue_w = np.array([tuple(O["Tongue"].matrix_world @ v.co) for v in O["Tongue"].data.vertices])

def group_idx(obj, name):
    gi = obj.vertex_groups[name].index
    return sorted(v.index for v in obj.data.vertices if any(g.group == gi for g in v.groups))

tis_cage = group_idx(TIS, "LipCage"); jaw_cage = group_idx(JAW, "LipCage")
# candidate edge verts: tissue cage verts with a jaw cage twin within 1e-3
tis_cage_w = tis_w[tis_cage]; jaw_cage_w = jaw_w[jaw_cage]
edge_pairs = []
for ii, a in enumerate(tis_cage):
    d = np.linalg.norm(jaw_cage_w - tis_w[a], axis=1)
    j = int(np.argmin(d))
    if d[j] < 1e-4: edge_pairs.append((a, jaw_cage[j]))   # true rim pairs are exact duplicates (0.0); pinch-cluster near-misses start at 1.7e-4
assert len(edge_pairs) == 81, f"edge row pairs {len(edge_pairs)}"
edge_pairs.sort(key=lambda pr: -tis_w[pr[0]][0])     # +x commissure -> -x
tis_edge = np.array([tis_w[a] for a, _ in edge_pairs])
jaw_edge = np.array([jaw_w[b] for _, b in edge_pairs])
OUT["edge_row_pairs"] = len(edge_pairs)
OUT["edge_row_max_rest_gap"] = round(float(np.linalg.norm(tis_edge - jaw_edge, axis=1).max()), 6)

# margin rows: cage verts off the v4 surface
def off_surface(pts):
    out = []
    for p in pts:
        _, _, _, dist = bvh4.find_nearest(Vector(p))
        out.append(float(dist) if dist is not None else 0.0)
    return np.array(out)
tis_cage_off = off_surface(tis_cage_w); jaw_cage_off = off_surface(jaw_w[jaw_cage])
tis_edge_set = {a for a, _ in edge_pairs}; jaw_edge_set = {b for _, b in edge_pairs}
tis_margin = sorted(a for a, d in zip(tis_cage, tis_cage_off) if a not in tis_edge_set and d > 0.0035)
jaw_margin = sorted(b for b, d in zip(jaw_cage, jaw_cage_off) if b not in jaw_edge_set and d > 0.0035)
OUT["margin_verts"] = {"tissue": len(tis_margin), "jaw": len(jaw_margin)}
tis_mset = set(tis_margin) | tis_edge_set; jaw_mset = set(jaw_margin) | jaw_edge_set
tis_mtris = tris_of(TIS, tis_mset); jaw_mtris = tris_of(JAW, jaw_mset)
OUT["margin_strip_tris"] = {"tissue": len(tis_mtris), "jaw": len(jaw_mtris)}
tis_cset, jaw_cset = set(tis_cage), set(jaw_cage)
tis_stris = tris_of(TIS, tis_cset); jaw_stris = tris_of(JAW, jaw_cset)

tu_tris = tris_of(O["TeethUpper"]); tl_tris = tris_of(O["TeethLower"])
bvh_tu = bvh(tu_w, tu_tris)
bvh_tis_m = bvh(tis_w, tis_mtris)

def Rx(deg):
    th = math.radians(deg)
    return np.array([[1, 0, 0], [0, math.cos(th), -math.sin(th)], [0, math.sin(th), math.cos(th)]])
def rot(P, deg):
    return (P - H) @ Rx(deg).T + H

comL_t = np.array([tis_w[i] for i in group_idx(TIS, "CommissureL")]).mean(axis=0)
comR_t = np.array([tis_w[i] for i in group_idx(TIS, "CommissureR")]).mean(axis=0)
comL_j = np.array([jaw_w[i] for i in group_idx(JAW, "CommissureL")]).mean(axis=0)
comR_j = np.array([jaw_w[i] for i in group_idx(JAW, "CommissureR")]).mean(axis=0)

cen_col = int(np.argmin(np.abs(tis_edge[:, 0])))
front = np.abs(tis_edge[:, 0]) < 0.10
res = {}
for deg in (0, -10, -20, -30):
    je = rot(jaw_edge, deg)
    gap = np.linalg.norm(tis_edge - je, axis=1)
    tl_r = rot(tl_w, deg)
    bvh_tl = bvh(tl_r, tl_tris)
    jm_r = rot(jaw_w, deg)
    bvh_jm = bvh(jm_r, jaw_mtris)
    bvh_tm = bvh_tis_m
    ov_tm_tl = len(bvh_tm.overlap(bvh_tl))
    bvh_jm_full = bvh_jm
    ov_jm_tu = len(bvh_jm_full.overlap(bvh_tu))
    ov_mm = len(bvh_tm.overlap(bvh_jm))
    tl_static = bvh_tl if deg == 0 else None
    bvh_tl_rest = bvh(tl_w, tl_tris)
    ov_tm_tu = len(bvh_tm.overlap(bvh_tu))
    ov_jm_tl = len(bvh_jm.overlap(bvh_tl_rest if deg == 0 else bvh_tl))
    res[str(deg)] = {
        "rim_gap_centre": round(float(gap[cen_col]), 4),
        "rim_gap_front_mean": round(float(gap[front].mean()), 4),
        "rim_gap_max": round(float(gap.max()), 4),
        "rim_gap_commissure_L": round(float(gap[0]), 4),
        "rim_gap_commissure_R": round(float(gap[-1]), 4),
        "commissure_sep_L": round(float(np.linalg.norm(comL_t - rot(comL_j[None, :], deg)[0])), 4),
        "commissure_sep_R": round(float(np.linalg.norm(comR_t - rot(comR_j[None, :], deg)[0])), 4),
        "overlap_tissueMargin_vs_teethLower": ov_tm_tl,
        "overlap_jawMargin_vs_teethUpper": ov_jm_tu,
        "overlap_tissueMargin_vs_teethUpper": ov_tm_tu,
        "overlap_jawMargin_vs_teethLower_rot": ov_jm_tl,
        "overlap_margin_vs_margin": ov_mm,
        "clear_tissueMargin_teethLower": round(min(min_clear(bvh_tl, tis_w[tis_margin]), min_clear(bvh_tm, tl_r[::5])), 4),
        "clear_jawMargin_teethUpper": round(min(min_clear(bvh_tu, jm_r[jaw_margin]), min_clear(bvh_jm, tu_w[::5])), 4),
    }
OUT["jaw_pose"] = res

# jaw face sanity under rigid pose (areas/normals must be invariant)
jaw_tris = tris_of(JAW)
def tri_stats(P, tris):
    T = P[np.array(tris)]
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    a = np.linalg.norm(n, axis=1) / 2
    return a, n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
a0, n0 = tri_stats(jaw_w, jaw_tris)
a1, n1 = tri_stats(rot(jaw_w, -30), jaw_tris)
n1_back = n1 @ Rx(-30)
OUT["jaw_rigid_pose_check"] = {"min_area_rest": round(float(a0.min()), 6),
                               "max_area_drift": round(float(np.abs(a1 - a0).max()), 8),
                               "max_normal_drift_deg": round(float(np.degrees(np.arccos(np.clip(np.einsum('ij,ij->i', n0, n1_back), -1, 1))).max()), 6)}

# ---- synthetic lip-part field test
cols = np.arange(81)
fall = np.cos(np.clip((np.abs(cols - cen_col)) / 20.0, 0, 1) * math.pi / 2) ** 2
# parting direction per column = the jaw rim's actual travel direction at -20 deg
trav = rot(jaw_edge, -20) - jaw_edge
trav /= np.maximum(np.linalg.norm(trav, axis=1, keepdims=True), 1e-12)
# graded weights across the strip: rim 1.0, margin1 0.6, margin2 0.35, body/support 0.35
def row_weights(cage_ids, offs, rim_set):
    w = {}
    for i, d in zip(cage_ids, offs):
        if i in rim_set: w[i] = 1.0
        elif d > 0.0135: w[i] = 0.35
        elif d > 0.0035: w[i] = 0.6
        else: w[i] = 0.35
    return w
tis_wts = row_weights(tis_cage, tis_cage_off, tis_edge_set)
jaw_wts = row_weights(jaw_cage, jaw_cage_off, jaw_edge_set)
# column of a cage vert = nearest rim column (by rest position)
def col_of(P, i):
    return int(np.argmin(np.linalg.norm(tis_edge - P[i], axis=1)))
tis_w2 = tis_w.copy(); jaw_w2 = jaw_w.copy()
for i, w in tis_wts.items():
    k = col_of(tis_w, i)
    tis_w2[i] -= trav[k] * 0.01 * fall[k] * w
for i, w in jaw_wts.items():
    k = col_of(jaw_w, i)
    jaw_w2[i] += trav[k] * 0.01 * fall[k] * w
def strip_strain(P0, P1, tris):
    T0 = P0[np.array(tris)]; T1 = P1[np.array(tris)]
    def edges(T):
        return np.stack([np.linalg.norm(T[:, 1] - T[:, 0], axis=1),
                         np.linalg.norm(T[:, 2] - T[:, 1], axis=1),
                         np.linalg.norm(T[:, 0] - T[:, 2], axis=1)], axis=1)
    e0, e1 = edges(T0), edges(T1)
    stretch = (e1 / np.maximum(e0, 1e-12)).max()
    n0 = np.cross(T0[:, 1] - T0[:, 0], T0[:, 2] - T0[:, 0]); n1 = np.cross(T1[:, 1] - T1[:, 0], T1[:, 2] - T1[:, 0])
    a0 = np.linalg.norm(n0, axis=1); a1 = np.linalg.norm(n1, axis=1)
    flips = int((np.einsum('ij,ij->i', n0, n1) < 0).sum())
    return {"max_edge_stretch": round(float(stretch), 4), "min_area_ratio": round(float((a1 / np.maximum(a0, 1e-12)).min()), 4),
            "flipped": flips, "tris": len(tris)}
part_gap = float(np.linalg.norm(tis_w2[edge_pairs[cen_col][0]] - jaw_w2[edge_pairs[cen_col][1]]))
OUT["lip_part_field_test"] = {"centre_parting_achieved": round(part_gap, 4),
                              "tissue_strip": strip_strain(tis_w, tis_w2, tis_stris),
                              "jaw_strip": strip_strain(jaw_w, jaw_w2, jaw_stris)}
print(json.dumps(OUT, indent=1))
json.dump(OUT, open("/home/hatch/workspace/anthroforge-v2/base-head-v5/work/mouth_open_v5.json", "w"), indent=1)
