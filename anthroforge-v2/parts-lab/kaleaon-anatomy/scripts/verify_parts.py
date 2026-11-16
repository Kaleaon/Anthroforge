"""Independent QA verification for kaleaon_anatomy_parts.blend (read-only).
Writes work/verify_numbers.json. Checks: volumes/bottom vs canon, girth
shape-key response, bone-scale length response, exact tri-tri interpenetration
at rest and in a static articulation pose (shafts fanned, sac swung, teat lag).
"""
import bpy, bmesh, json, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree

PATH = "/home/hatch/workspace/anthroforge-v2/parts-lab/kaleaon-anatomy/kaleaon_anatomy_parts.blend"
OUT = "/home/hatch/workspace/anthroforge-v2/parts-lab/kaleaon-anatomy/work/verify_numbers.json"
bpy.ops.wm.open_mainfile(filepath=PATH)
dg = bpy.context.evaluated_depsgraph_get()
R = {"objects": {}, "checks": {}}

def ev_mesh(ob):
    ev = ob.evaluated_get(dg)
    me = bpy.data.meshes.new_from_object(ev, depsgraph=dg)
    return ev, me

def vol_bbox(ob):
    ev, me = ev_mesh(ob)
    bm = bmesh.new(); bm.from_mesh(me); v = bm.calc_volume(); bm.free()
    ws = [ev.matrix_world @ Vector(c) for c in ev.bound_box]
    bpy.data.meshes.remove(me)
    return v * 1000.0, [min(p[i] for p in ws) for i in range(3)], [max(p[i] for p in ws) for i in range(3)]

def tris_world(ob):
    ev, me = ev_mesh(ob)
    me.calc_loop_triangles()
    mw = ev.matrix_world
    vs = [mw @ v.co for v in me.vertices]
    tris = [(vs[t.vertices[0]], vs[t.vertices[1]], vs[t.vertices[2]]) for t in me.loop_triangles]
    bpy.data.meshes.remove(me)
    return tris

def seg_tri(p, q, a, b, c):
    d = q - p; e1 = b - a; e2 = c - a
    h = d.cross(e2); det = e1.dot(h)
    if abs(det) < 1e-12: return False
    inv = 1.0 / det; s = p - a; u = inv * s.dot(h)
    if u < -1e-9 or u > 1 + 1e-9: return False
    r = s.cross(e1); v = inv * d.dot(r)
    if v < -1e-9 or u + v > 1 + 1e-9: return False
    t = inv * e2.dot(r)
    return 1e-9 < t < 1 - 1e-9

def tri_tri(t1, t2):
    for i in range(3):
        p, q = t1[i], t1[(i + 1) % 3]
        if seg_tri(p, q, *t2): return True
    for i in range(3):
        p, q = t2[i], t2[(i + 1) % 3]
        if seg_tri(p, q, *t1): return True
    return False

def interpenetration(objs_a, objs_b):
    """exact intersecting-triangle count between two object sets"""
    total = 0; pairs = []
    for oa in objs_a:
        ta = tris_world(oa); ba = BVHTree.FromPolygons([v for t in ta for v in t],
              [(3 * i, 3 * i + 1, 3 * i + 2) for i in range(len(ta))], all_triangles=True)
        for ob in objs_b:
            if ob is oa: continue
            tb = tris_world(ob); bb = BVHTree.FromPolygons([v for t in tb for v in t],
                  [(3 * i, 3 * i + 1, 3 * i + 2) for i in range(len(tb))], all_triangles=True)
            cand = ba.overlap(bb); n = 0
            for i, j in cand:
                if tri_tri(ta[i], tb[j]): n += 1
            if n: pairs.append([oa.name, ob.name, n])
            total += n
    return total, pairs

names = [o.name for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith("Part_")]
for n in sorted(names):
    ob = bpy.data.objects[n]
    v, mn, mx = vol_bbox(ob)
    R["objects"][n] = {"verts": len(ob.data.vertices), "vol_L": round(v, 3),
                       "min": [round(x, 4) for x in mn], "max": [round(x, 4) for x in mx],
                       "shape_keys": [k.name for k in ob.data.shape_keys.key_blocks] if ob.data.shape_keys else []}
arm = bpy.data.objects["KaleaonRig"]
R["teat_bones"] = [b.name for b in arm.data.bones if b.name.startswith("Teat_")]
R["bone_count"] = len(arm.data.bones)

# ---- girth channel response (Shaft_1)
s1 = bpy.data.objects["Part_Shaft_1"]
v0, _, _ = vol_bbox(s1)
s1.data.shape_keys.key_blocks["GirthPlus"].value = 1.0
bpy.context.view_layer.update()
vp, _, _ = vol_bbox(s1)
s1.data.shape_keys.key_blocks["GirthPlus"].value = 0.0
s1.data.shape_keys.key_blocks["GirthMinus"].value = 1.0
bpy.context.view_layer.update()
vm, _, _ = vol_bbox(s1)
s1.data.shape_keys.key_blocks["GirthMinus"].value = 0.0
bpy.context.view_layer.update()
R["checks"]["girth_shaft1_vol_L"] = {"basis": round(v0, 3), "plus": round(vp, 3), "minus": round(vm, 3)}

# ---- length channel: pose-bone Y scale on Shaft_2 chain
def tip_marker(ob):
    ev, me = ev_mesh(ob)
    ws = [ev.matrix_world @ v.co for v in me.vertices]
    bpy.data.meshes.remove(me)
    return min(ws, key=lambda p: p.z)
s2 = bpy.data.objects["Part_Shaft_2"]
p_rest = tip_marker(s2)
for bn in ("Shaft_2_Base", "Shaft_2_Tip"):
    arm.pose.bones[bn].scale = (1.0, 1.25, 1.0)
bpy.context.view_layer.update()
p_long = tip_marker(s2)
v_long, _, _ = vol_bbox(s2)
for bn in ("Shaft_2_Base", "Shaft_2_Tip"):
    arm.pose.bones[bn].scale = (1.0, 1.0, 1.0)
bpy.context.view_layer.update()
R["checks"]["length_bonescale_shaft2"] = {
    "tip_lowest_rest": [round(x, 4) for x in p_rest],
    "tip_lowest_scale1.25": [round(x, 4) for x in p_long],
    "tip_travel_m": round((p_long - p_rest).length, 4), "vol_L_at_1.25": round(v_long, 3)}

shafts = [bpy.data.objects[f"Part_Shaft_{n}"] for n in (1, 2, 3, 4)]
sac = bpy.data.objects["Part_SacUdder"]
teats = [bpy.data.objects[f"Part_SacUdder_Teat_{n}"] for n in (1, 2, 3, 4)]

# ---- rest interpenetration
res = {}
res["shaft_vs_shaft"] = interpenetration(shafts[:2], shafts[2:]) + interpenetration([shafts[0]], [shafts[1]]) + interpenetration([shafts[2]], [shafts[3]])
res["shaft_vs_shaft"] = (res["shaft_vs_shaft"][0], res["shaft_vs_shaft"][1])
res["shaft_vs_sac"] = interpenetration(shafts, [sac])
res["teat_vs_sac(embedded roots expected)"] = interpenetration(teats, [sac])
res["teat_vs_shaft"] = interpenetration(teats, shafts)
res["teat_vs_teat"] = interpenetration(teats[:2], teats[2:])
R["checks"]["rest_intersections"] = {k: {"total_tris": v[0], "pairs": v[1]} for k, v in res.items()}

# ---- static articulation pose: shafts fan+pitch, sac swings, teats lag
def premul(pb, axis, deg):
    from mathutils import Quaternion
    rq = pb.bone.matrix_local.to_quaternion()
    pb.rotation_mode = 'QUATERNION'
    pb.rotation_quaternion = rq.inverted() @ Quaternion(axis, math.radians(deg)) @ rq
for n, fan in ((1, -7), (2, -3), (3, 7), (4, 3)):
    premul(arm.pose.bones[f"Shaft_{n}_Base"], (0, 0, 1), fan)
    premul(arm.pose.bones[f"Shaft_{n}_Base"], (1, 0, 0), 10)
    premul(arm.pose.bones[f"Shaft_{n}_Tip"], (1, 0, 0), 8)
premul(arm.pose.bones["Sac"], (1, 0, 0), 12)
for n in (1, 2, 3, 4):
    premul(arm.pose.bones[f"Teat_{n}"], (1, 0, 0), -8)  # lag: trails the sac swing
bpy.context.view_layer.update()
posed = {}
for ob in shafts + [sac] + teats:
    v, mn, mx = vol_bbox(ob)
    posed[ob.name] = {"vol_L": round(v, 3), "min_z": round(mn[2], 4)}
R["checks"]["articulation_volumes"] = posed
pa = {}
pa["shaft_vs_sac"] = interpenetration(shafts, [sac])
pa["shaft_vs_shaft_13"] = interpenetration([shafts[0]], [shafts[2]])
pa["teat_vs_shaft"] = interpenetration(teats, shafts)
R["checks"]["articulation_intersections"] = {k: {"total_tris": v[0], "pairs": v[1]} for k, v in pa.items()}

with open(OUT, "w") as f: json.dump(R, f, indent=1)
print("VERIFY DONE")
print(json.dumps(R["checks"], indent=1))
