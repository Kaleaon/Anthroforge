"""QA on the shipped kaleaon_anatomy_parts.blend (v2 - crash-hardened):
- rest measurements vs canon
- exact tri-tri intersections among the PARTS (small meshes)
- parts vs Body: KDTree vertex-distance method (the sacdrape report's
  validated approach for the crotch pocket; full-BVH on the 147k-vert Body
  SIGBUS'd under fleet memory pressure)
- articulation suite. JSON written incrementally.
"""
import bpy, bmesh, json, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

BLEND = "/home/hatch/workspace/anthroforge-v2/parts-lab/kaleaon-anatomy/kaleaon_anatomy_parts.blend"
OUTJ = "/home/hatch/workspace/anthroforge-v2/parts-lab/kaleaon-anatomy/work/qa_numbers.json"
bpy.ops.wm.open_mainfile(filepath=BLEND)
arm = bpy.data.objects["KaleaonRig"]
dg = bpy.context.evaluated_depsgraph_get()
R = {}

def save():
    with open(OUTJ, "w") as f: json.dump(R, f, indent=1)

def ev_world(name):
    ob = bpy.data.objects[name]; ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    mw = ev.matrix_world
    V = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("co", V)
    V = V.reshape(-1, 3)
    M = np.array(mw)
    W = (M[:3, :3] @ V.T).T + M[:3, 3]
    me.calc_loop_triangles()
    F = np.empty(len(me.loop_triangles) * 3, dtype=np.int64)
    me.loop_triangles.foreach_get("vertices", F); F = F.reshape(-1, 3)
    ev.to_mesh_clear()
    return W, F

def refresh():
    global dg
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()

def tri_tri(p1, p2, p3, q1, q2, q3):
    def edge_tri(a, b, t1, t2, t3):
        d = b - a; e1 = t2 - t1; e2 = t3 - t1
        n = np.cross(e1, e2); dn = d @ n
        if abs(dn) < 1e-12: return False
        t = ((t1 - a) @ n) / dn
        if t < -1e-9 or t > 1 + 1e-9: return False
        p = a + t * d; u = p - t1
        uu, uv, vv = e1 @ e1, e1 @ e2, e2 @ e2
        wu, wv = u @ e1, u @ e2
        den = uv * uv - uu * vv
        if abs(den) < 1e-14: return False
        s = (uv * wv - vv * wu) / den; tt = (uv * wu - uu * wv) / den
        return s >= -1e-9 and tt >= -1e-9 and s + tt <= 1 + 1e-9
    P = [p1, p2, p3]; Q = [q1, q2, q3]
    for i in range(3):
        for j in range(3):
            if edge_tri(P[i], P[(i + 1) % 3], *Q): return True
            if edge_tri(Q[j], Q[(j + 1) % 3], *P): return True
    return False

def intersections(ca, cb, exclude_near=None, excl_r=0.0):
    (A, FA), (B, FB) = ca, cb
    ta = BVHTree.FromPolygons([Vector(v) for v in A], [tuple(f) for f in FA])
    tb = BVHTree.FromPolygons([Vector(v) for v in B], [tuple(f) for f in FB])
    pairs = ta.overlap(tb)
    hits, excl = 0, 0
    for ia, ib in pairs:
        fa, fb = FA[ia], FB[ib]
        if tri_tri(A[fa[0]], A[fa[1]], A[fa[2]], B[fb[0]], B[fb[1]], B[fb[2]]):
            if exclude_near is not None:
                c = (A[fa].mean(axis=0) + B[fb].mean(axis=0)) / 2
                if np.linalg.norm(c - np.array(exclude_near)) < excl_r:
                    excl += 1; continue
            hits += 1
    return {"candidate_pairs": len(pairs), "intersecting_faces": hits,
            "embed_zone_faces": excl}

refresh()
sacW, sacF = ev_world("Part_SacUdder")
bm = bmesh.new(); bm.from_mesh(bpy.data.objects["Part_SacUdder"].data)
svol = abs(bm.calc_volume()); bm.free()
R["sac"] = {"volume_L": round(svol * 1000, 2), "bottom_z_m": round(float(sacW[:, 2].min()), 4),
            "canon": {"volume_L": 209.46, "bottom_z_m": 0.031}}
tips = {}
for i in (1, 2, 3, 4):
    W, _ = ev_world(f"Part_SacUdder_Teat_{i}")
    tips[f"Teat_{i}"] = round(float(W[:, 2].min()), 4)
R["teat_tip_min_z_m"] = tips
save()

parts = [f"Part_Shaft_{n}" for n in (1, 2, 3, 4)] + ["Part_SacUdder"] + \
        [f"Part_SacUdder_Teat_{i}" for i in (1, 2, 3, 4)]
cache = {n: ev_world(n) for n in parts}
R["interpenetration"] = {}
for i, a in enumerate(parts):
    for b in parts[i + 1:]:
        R["interpenetration"][f"{a} x {b}"] = intersections(cache[a], cache[b])
save()
build = json.load(open("/home/hatch/workspace/anthroforge-v2/parts-lab/kaleaon-anatomy/work/build_numbers.json"))
for i in (1, 2, 3, 4):
    root = build["parts"][f"Part_SacUdder_Teat_{i}"]["root_world"]
    R["interpenetration"][f"Teat_{i} x SacUdder (embed-aware)"] = \
        intersections(cache[f"Part_SacUdder_Teat_{i}"], cache["Part_SacUdder"],
                      exclude_near=root, excl_r=0.030)
save()

# parts vs Body - KDTree vertex distance (report method)
bodyW, _ = ev_world("Body")
kd = KDTree(len(bodyW))
for i, v in enumerate(bodyW): kd.insert(Vector(v), i)
kd.balance()
R["body_clearance"] = {}
for n in parts:
    W = cache[n][0]
    ds = np.array([kd.find(Vector(v))[2] for v in W])
    R["body_clearance"][n] = {"min_vert_dist_mm": round(float(ds.min()) * 1000, 2),
                              "verts_within_10mm": int((ds < 0.010).sum())}
save()

def pose_reset():
    for pb in arm.pose.bones:
        pb.rotation_euler = (0, 0, 0); pb.scale = (1, 1, 1); pb.location = (0, 0, 0)
    refresh()

rest = {n: cache[n][0] for n in parts}
def disp(name):
    W, _ = ev_world(name)
    d = np.linalg.norm(W - rest[name], axis=1)
    return {"mean_mm": round(float(d.mean()) * 1000, 3), "max_mm": round(float(d.max()) * 1000, 4)}

ART = {}
pb = arm.pose.bones["Shaft_2_Base"]; pb.rotation_mode = 'XYZ'
pb.rotation_euler = (math.radians(25), 0, 0); refresh()
ART["shaft2_base_+25deg"] = {n: disp(n) for n in parts}
pose_reset()
pb = arm.pose.bones["Sac"]; pb.rotation_mode = 'XYZ'
pb.rotation_euler = (math.radians(20), 0, 0); refresh()
ART["sac_+20deg"] = {n: disp(n) for n in parts[:5]}
sacW2, _ = ev_world("Part_SacUdder")
att = {}
for i in (1, 2, 3, 4):
    W, _ = ev_world(f"Part_SacUdder_Teat_{i}")
    att[f"Teat_{i}"] = round(float(np.linalg.norm(sacW2 - W[:12].mean(axis=0), axis=1).min()) * 1000, 2)
ART["sac_+20deg_teat_root_nearest_sac_mm"] = att
pose_reset()
att0 = {}
for i in (1, 2, 3, 4):
    W, _ = ev_world(f"Part_SacUdder_Teat_{i}")
    att0[f"Teat_{i}"] = round(float(np.linalg.norm(sacW - W[:12].mean(axis=0), axis=1).min()) * 1000, 2)
ART["rest_teat_root_nearest_sac_mm"] = att0
pb = arm.pose.bones["Teat_2"]; pb.rotation_mode = 'XYZ'
pb.rotation_euler = (math.radians(20), 0, 0); refresh()
ART["teat2_+20deg"] = {n: disp(n) for n in parts[5:]}
pose_reset()
pb = arm.pose.bones["Shaft_1_Base"]; pb.scale = (1, 1.3, 1); refresh()
W, _ = ev_world("Part_Shaft_1")
d = np.linalg.norm(W - rest["Part_Shaft_1"], axis=1)
ART["shaft1_bonescale_Y1.3"] = {"mean_disp_mm": round(float(d.mean()) * 1000, 2),
                                "max_disp_mm": round(float(d.max()) * 1000, 2)}
pose_reset()
sk = bpy.data.objects["Part_Shaft_1"].data.shape_keys.key_blocks["GirthPlus"]
sk.value = 1.0; refresh()
ob = bpy.data.objects["Part_Shaft_1"]; ev = ob.evaluated_get(dg); me = ev.to_mesh()
bm = bmesh.new(); bm.from_mesh(me); gv = abs(bm.calc_volume()); bm.free(); ev.to_mesh_clear()
ART["shaft1_girthplus_volume_L"] = round(gv * 1000, 3)
ART["shaft1_rest_volume_L"] = 5.301
sk.value = 0.0; refresh()
R["articulation"] = ART
save()
print(json.dumps(R, indent=1))
