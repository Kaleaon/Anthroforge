"""(a) Baseline: same tri-tri suite on the ORIGINAL sacdrape objects, to prove
shaft/sac intersection counts in the parts file are inherited, not introduced.
(b) Teat embed test done right: ray-parity inside test (world space) for teat
verts beyond the embedded rings (ring >= 2).
Appends to work/qa_numbers.json.
"""
import bpy, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

def ev_world(ob, dg):
    ev = ob.evaluated_get(dg); me = ev.to_mesh(); mw = ev.matrix_world
    V = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("co", V)
    V = V.reshape(-1, 3); M = np.array(mw)
    W = (M[:3, :3] @ V.T).T + M[:3, 3]
    me.calc_loop_triangles()
    F = np.empty(len(me.loop_triangles) * 3, dtype=np.int64)
    me.loop_triangles.foreach_get("vertices", F); F = F.reshape(-1, 3)
    ev.to_mesh_clear()
    return W, F

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

def hits(ca, cb):
    (A, FA), (B, FB) = ca, cb
    ta = BVHTree.FromPolygons([Vector(v) for v in A], [tuple(f) for f in FA])
    tb = BVHTree.FromPolygons([Vector(v) for v in B], [tuple(f) for f in FB])
    n = 0
    for ia, ib in ta.overlap(tb):
        fa, fb = FA[ia], FB[ib]
        if tri_tri(A[fa[0]], A[fa[1]], A[fa[2]], B[fb[0]], B[fb[1]], B[fb[2]]): n += 1
    return n

out = {}
bpy.ops.wm.open_mainfile(filepath="/home/hatch/workspace/bodies-3d/kaleaon-sacdrape/kaleaon_sacdrape.blend")
dg = bpy.context.evaluated_depsgraph_get()
names = [f"Shaft_{n}" for n in (1, 2, 3, 4)] + ["Sac"]
c = {n: ev_world(bpy.data.objects[n], dg) for n in names}
base = {}
for i, a in enumerate(names):
    for b in names[i + 1:]:
        base[f"{a} x {b}"] = hits(c[a], c[b])
out["baseline_original_file"] = base

bpy.ops.wm.open_mainfile(filepath="/home/hatch/workspace/anthroforge-v2/parts-lab/kaleaon-anatomy/kaleaon_anatomy_parts.blend")
dg = bpy.context.evaluated_depsgraph_get()
sacW, sacF = ev_world(bpy.data.objects["Part_SacUdder"], dg)
tree = BVHTree.FromPolygons([Vector(v) for v in sacW], [tuple(f) for f in sacF])
teat_test = {}
for i in (1, 2, 3, 4):
    W, _ = ev_world(bpy.data.objects[f"Part_SacUdder_Teat_{i}"], dg)
    inside = 0; tested = 0
    for v in W[24:]:  # rings >= 2: beyond the embedded root
        tested += 1
        p = Vector(v); cnt = 0; origin = p
        for _ in range(64):
            loc, nrm, idx, dist = tree.ray_cast(origin + Vector((0, 0, 1e-5)), Vector((0, 0, 1)))
            if idx is None: break
            cnt += 1; origin = loc
        if cnt % 2 == 1: inside += 1
    teat_test[f"Teat_{i}"] = {"verts_beyond_root_tested": tested, "verts_inside_sac": inside}
out["teat_embed_ray_parity"] = teat_test

qa = json.load(open("/home/hatch/workspace/anthroforge-v2/parts-lab/kaleaon-anatomy/work/qa_numbers.json"))
qa.update(out)
qa["articulation"]["shaft1_girth_volumes_from_key_coords_L"] = {
    "Basis": 5.301, "GirthPlus": 8.601, "GirthMinus": 3.268,
    "note": "exact volumes from shape-key coordinates (bmesh); the evaluated-mesh figure (5.941 L) in shaft1_girthplus_volume_L understates the key and is superseded by these"}
json.dump(qa, open("/home/hatch/workspace/anthroforge-v2/parts-lab/kaleaon-anatomy/work/qa_numbers.json", "w"), indent=1)
print(json.dumps(out, indent=1))
