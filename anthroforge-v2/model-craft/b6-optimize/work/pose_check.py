#!/usr/bin/env python3
"""B6 deformation sanity check: pose every LOD GLB with the two B17
stress poses and dump rest/posed vertex positions for offline analysis.

Poses (identical construction to B17, so LOD0 numbers cross-check
against RIG_FRIENDLY.md / results.json):
  elbow_flex_L_120   - LeftForeArm bent to exactly 120 deg about its
                       resolved flexion axis (B17 supplement method)
  forearm_twist_L_180- LeftForeArm pose Euler (0, pi, 0) (B17 audit
                       add_twist: rotation about the bone's local Y)

Dumps per input: <tag>_dumps.npz with rest, elbow, twist (world-space
posed verts of the skinned body mesh), faces, dom (dominant bone idx),
bone names. Rigid attachments are excluded (B17 R13 pattern).

  blender -b --python pose_check.py -- <out_dir> <glb...>
"""
import bpy, sys, math, os
import numpy as np
from mathutils import Euler

argv = sys.argv[sys.argv.index("--") + 1:]
OUT = argv[0]
GLBS = argv[1:]
os.makedirs(OUT, exist_ok=True)

def load(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path)

def scene():
    arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    body = None
    for o in bpy.data.objects:
        if o.type == 'MESH' and any(m.type == 'ARMATURE' and m.object == arm
                                    for m in o.modifiers):
            if body is None or len(o.data.vertices) > len(body.data.vertices):
                body = o
    return arm, body

def evaluated_world(obj):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    me = ev.to_mesh()
    pos = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", pos)
    mw = np.array(ev.matrix_world)
    out = pos.reshape(-1, 3) @ mw[:3, :3].T + mw[:3, 3]
    ev.to_mesh_clear()
    return out

def reset_pose(arm):
    for pb in arm.pose.bones:
        pb.rotation_mode = 'XYZ'
        pb.rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()

# ---- FK helpers (B17 supplement, verbatim logic) -------------------------
def build_fk(arm):
    BONES = [b.name for b in arm.data.bones]
    PARENT = {b.name: (b.parent.name if b.parent else None)
              for b in arm.data.bones}
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
        d = fkm[bn][:3, :3] @ np.array([0, 1.0, 0])
        return d / np.linalg.norm(d)
    MW = np.array(arm.matrix_world)
    def to_world(p):
        return p @ MW[:3, :3].T + MW[:3, 3]
    BDIR = {}
    for b in arm.data.bones:
        h = to_world(np.array(b.head_local)); t = to_world(np.array(b.tail_local))
        BDIR[b.name] = (t - h) / np.linalg.norm(t - h)
    UP = BDIR["mixamorig:Spine"] / np.linalg.norm(BDIR["mixamorig:Spine"])
    td = BDIR["mixamorig:LeftToeBase"].copy(); td -= UP * (td @ UP)
    FWD = td / np.linalg.norm(td)
    def resolve_axis(bn, target):
        d0 = fk_dir(fk({}), bn)
        want = math.degrees(math.acos(float(np.clip(d0 @ target, -1, 1))))
        ang = math.radians(max(want, 20.0))
        best = None
        for comp in (0, 2):
            for sgn in (1, -1):
                e = [0, 0, 0]; e[comp] = sgn * ang
                d = fk_dir(fk({bn: tuple(e)}), bn)
                if best is None or float(d @ target) > best[0]:
                    best = (float(d @ target), tuple(e))
        return best[1]
    return resolve_axis, FWD

for path in GLBS:
    tag = os.path.splitext(os.path.basename(path))[0]
    load(path)
    arm, body = scene()
    bones = [b.name for b in arm.data.bones]
    bidx = {n: i for i, n in enumerate(bones)}
    gname = {g.index: g.name for g in body.vertex_groups}
    W = np.zeros((len(body.data.vertices), len(bones)), dtype=np.float32)
    for v in body.data.vertices:
        for g in v.groups:
            nm = gname.get(g.group)
            if nm in bidx:
                W[v.index, bidx[nm]] += g.weight
    dom = W.argmax(axis=1)
    faces = []
    for p in body.data.polygons:
        vs = list(p.vertices)
        for k in range(1, len(vs) - 1):
            faces.append((vs[0], vs[k], vs[k + 1]))
    faces = np.array(faces, dtype=np.int64)
    edges = np.array([(e.vertices[0], e.vertices[1]) for e in body.data.edges],
                     dtype=np.int64)
    resolve_axis, FWD = build_fk(arm)
    reset_pose(arm)
    rest = evaluated_world(body)
    # elbow 120
    bn = "mixamorig:LeftForeArm"
    e = resolve_axis(bn, FWD)
    domc = max(range(3), key=lambda i: abs(e[i]))
    scale = math.radians(120) / e[domc]
    arm.pose.bones[bn].rotation_euler = tuple(x * scale for x in e)
    bpy.context.view_layer.update()
    elbow = evaluated_world(body)
    reset_pose(arm)
    # forearm twist 180 (B17 add_twist: local-Y euler)
    arm.pose.bones[bn].rotation_euler = (0, math.pi, 0)
    bpy.context.view_layer.update()
    twist = evaluated_world(body)
    reset_pose(arm)
    np.savez_compressed(os.path.join(OUT, tag + "_dumps.npz"),
                        rest=rest.astype(np.float32),
                        elbow=elbow.astype(np.float32),
                        twist=twist.astype(np.float32),
                        faces=faces, edges=edges, dom=dom,
                        bones=np.array(bones))
    print("DUMPED", tag, len(rest), "verts", len(faces), "faces")
print("POSE CHECK DONE")
