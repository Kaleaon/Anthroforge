#!/usr/bin/env python3
"""B17 supplement: controlled L/R comparison. Bends both elbows and both
knees to the SAME 120 degrees about each side's resolved flexion axis
(scaling the resolved euler), so left/right differences are attributable
to weights/topology, not to different exercised angles. Appends to
results.json and poses_npz/. Run after audit_rig.py.
  blender -b --python supplement.py -- <glb> <out_dir>
"""
import bpy, sys, json, math, os
import numpy as np
from mathutils import Euler

argv = sys.argv[sys.argv.index("--") + 1:]
GLB, OUT = argv[0], argv[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
meshes = [o for o in bpy.data.objects if o.type == 'MESH'
          and any(m.type == 'ARMATURE' and m.object == arm
                  for m in o.modifiers)]
BONES = [b.name for b in arm.data.bones]
BIDX = {n: i for i, n in enumerate(BONES)}
PARENT = {b.name: (b.parent.name if b.parent else None)
          for b in arm.data.bones}
BLEN = {b.name: float(b.length) for b in arm.data.bones}
RESTL = {b.name: np.array(b.matrix_local) for b in arm.data.bones}
OFFSET = {n: (np.linalg.inv(RESTL[PARENT[n]]) @ RESTL[n]) if PARENT[n]
          else RESTL[n] for n in BONES}

def fk(pose):
    out = {}
    for n in BONES:
        base = out[PARENT[n]] @ OFFSET[n] if PARENT[n] else OFFSET[n]
        if n in pose:
            R = np.eye(4)
            R[:3, :3] = np.array(Euler(pose[n], 'XYZ').to_matrix())
            base = base @ R
        out[n] = base
    return out

def fk_dir(fkm, bn):
    M = fkm[bn]
    d = M[:3, :3] @ np.array([0, 1.0, 0])
    return d / np.linalg.norm(d)

MW = np.array(arm.matrix_world)
def to_world(p):
    return p @ MW[:3, :3].T + MW[:3, 3]
BHEAD = {b.name: to_world(np.array(b.head_local)) for b in arm.data.bones}
BTAIL = {b.name: to_world(np.array(b.tail_local)) for b in arm.data.bones}
BDIR = {n: (BTAIL[n] - BHEAD[n]) / np.linalg.norm(BTAIL[n] - BHEAD[n])
        for n in BONES}
UP = BDIR["mixamorig:Spine"]; UP /= np.linalg.norm(UP)
td = BDIR["mixamorig:LeftToeBase"].copy(); td -= UP * (td @ UP)
FWD = td / np.linalg.norm(td)

def resolve_axis(bn, target):
    _, d0 = None, fk_dir(fk({}), bn)
    want = math.degrees(math.acos(float(np.clip(d0 @ target, -1, 1))))
    ang = math.radians(max(want, 20.0))
    best = None
    for comp in (0, 2):
        for sgn in (1, -1):
            e = [0, 0, 0]; e[comp] = sgn * ang
            d = fk_dir(fk({bn: tuple(e)}), bn)
            if best is None or float(d @ target) > best[0]:
                best = (float(d @ target), tuple(e))
    return best[1], math.degrees(ang)

def reset_pose():
    for pb in arm.pose.bones:
        pb.rotation_mode = 'XYZ'
        pb.rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()
reset_pose()

OBJ = []
for obj in meshes:
    me = obj.data
    W = np.zeros((len(me.vertices), len(BONES)), dtype=np.float32)
    for v in me.vertices:
        for g in v.groups:
            nm = obj.vertex_groups[g.group].name
            if nm in BIDX:
                W[v.index, BIDX[nm]] += g.weight
    if (W.sum(axis=1) > 0.5).sum() < 50:
        continue
    edges = np.array([(e.vertices[0], e.vertices[1]) for e in me.edges],
                     dtype=np.int64)
    faces = []
    for p in me.polygons:
        vs = list(p.vertices)
        for k in range(1, len(vs) - 1):
            faces.append((vs[0], vs[k], vs[k + 1]))
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg); m2 = ev.to_mesh()
    pos = np.empty(len(m2.vertices) * 3)
    m2.vertices.foreach_get("co", pos)
    mw = np.array(ev.matrix_world)
    rest = pos.reshape(-1, 3) @ mw[:3, :3].T + mw[:3, 3]
    ev.to_mesh_clear()
    OBJ.append(dict(obj=obj, W=W, edges=edges,
                    faces=np.array(faces, dtype=np.int64), rest=rest,
                    dom=W.argmax(axis=1)))

def measure(region_bones):
    rb = [BIDX[b] for b in region_bones]
    agg = dict(flips=0, tris=0, rflips=0)
    strains, rstrains = [], []
    pdump = {}
    for O in OBJ:
        dg = bpy.context.evaluated_depsgraph_get()
        ev = O["obj"].evaluated_get(dg); me = ev.to_mesh()
        pos = np.empty(len(me.vertices) * 3)
        me.vertices.foreach_get("co", pos)
        mw = np.array(ev.matrix_world)
        pos = pos.reshape(-1, 3) @ mw[:3, :3].T + mw[:3, 3]
        ev.to_mesh_clear()
        e, f, rest = O["edges"], O["faces"], O["rest"]
        rl = np.linalg.norm(rest[e[:, 0]] - rest[e[:, 1]], axis=1)
        pl = np.linalg.norm(pos[e[:, 0]] - pos[e[:, 1]], axis=1)
        strain = pl / np.maximum(rl, 1e-9)
        p0, p1, p2 = rest[f[:, 0]], rest[f[:, 1]], rest[f[:, 2]]
        q0, q1, q2 = pos[f[:, 0]], pos[f[:, 1]], pos[f[:, 2]]
        e1 = p1 - p0
        e1n = e1 / np.maximum(np.linalg.norm(e1, axis=1, keepdims=True),
                              1e-12)
        n = np.cross(e1, p2 - p0)
        n = n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
        e2 = np.cross(n, e1n)
        detF = (((q1 - q0) * e1n).sum(1) * ((q2 - q0) * e2).sum(1)
                - ((q1 - q0) * e2).sum(1) * ((q2 - q0) * e1n).sum(1)) / \
            np.maximum(np.linalg.norm(e1, axis=1)
                       * ((p2 - p0) * e2).sum(1), 1e-12)
        vstrain = np.zeros(len(rest))
        np.maximum.at(vstrain, e[:, 0], strain)
        np.maximum.at(vstrain, e[:, 1], strain)
        strains.append(strain)
        emask = np.isin(O["dom"][e], rb).any(axis=1)
        fmask = np.isin(O["dom"][f], rb).any(axis=1)
        rstrains.append(strain[emask])
        agg["flips"] += int((detF < 0).sum()); agg["tris"] += len(detF)
        agg["rflips"] += int((detF[fmask] < 0).sum())
        pdump[f"{O['obj'].name}|pos"] = pos.astype(np.float32)
        pdump[f"{O['obj'].name}|vstrain"] = vstrain.astype(np.float32)
    alls = np.concatenate(strains); rs = np.concatenate(rstrains)
    return dict(edge_strain_max=round(float(alls.max()), 3),
                edge_strain_p99=round(float(np.percentile(alls, 99)), 3),
                faces_flipped=agg["flips"],
                faces_flipped_pct=round(100 * agg["flips"] / agg["tris"], 2),
                region_strain_max=round(float(rs.max()), 3),
                region_strain_p99=round(float(np.percentile(rs, 99)), 3),
                region_faces_flipped=agg["rflips"]), pdump

TESTS = [("elbow_flex_L_120", "mixamorig:LeftForeArm", FWD,
          ["mixamorig:LeftArm", "mixamorig:LeftForeArm"]),
         ("elbow_flex_R_120", "mixamorig:RightForeArm", FWD,
          ["mixamorig:RightArm", "mixamorig:RightForeArm"]),
         ("knee_flex_L_120", "mixamorig:LeftLeg", -FWD,
          ["mixamorig:LeftUpLeg", "mixamorig:LeftLeg"]),
         ("knee_flex_R_120", "mixamorig:RightLeg", -FWD,
          ["mixamorig:RightUpLeg", "mixamorig:RightLeg"])]
rp = os.path.join(OUT, "results.json")
data = json.load(open(rp))
for name, bn, tgt, region in TESTS:
    e, resolved = resolve_axis(bn, tgt)
    dom = max(range(3), key=lambda i: abs(e[i]))
    scale = math.radians(120) / e[dom]
    e120 = tuple(x * scale for x in e)
    reset_pose()
    arm.pose.bones[bn].rotation_euler = e120
    bpy.context.view_layer.update()
    s, pdump = measure(region)
    s["note"] = f"controlled: same 120deg about resolved axis (resolved at {resolved}deg)"
    s["bend_deg"] = 120
    s["region_bones"] = region
    data["poses"][name] = s
    np.savez_compressed(os.path.join(OUT, "poses_npz", name + ".npz"),
                        **pdump)
    print(name, s)
json.dump(data, open(rp, "w"), indent=1, default=str)
print("SUPPLEMENT DONE")
