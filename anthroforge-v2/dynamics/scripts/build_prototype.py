"""Build the soft-dynamics prototype .blend.

Scene: bara wolf (Walk) + a sac stand-in loft hanging from the pelvis,
driven by a 4-bone spring chain (AF_Sac1..4) + two 1-bone teat chains
(AF_TeatL/R), with the AF_softness paintable field on the meshes.
Dynamics are BAKED: two full actions (AF_Full_Soft / AF_Full_Firm) whose
wolf fcurves are the Walk clip looped x3 + held, and whose chain-bone
rotation_quaternions come from the verlet sim (scripts/run_prototype_sim.py)
converted analytically to local bone rotations.
Run: blender -b --factory-startup -noaudio --python build_prototype.py
"""
import json
import os
import sys

import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from proto_common import (N_FRAMES, N_WALK, PREROLL, REST_OFFSETS,
                          SEG_SOFTNESS, TEAT_OFFSET)

BASE = os.path.expanduser('~/workspace/anthroforge-v2/dynamics')
SRC = os.path.expanduser('~/workspace/anthroforge-v2/retarget-prototype/'
                         'retarget_prototype.blend')
OUT = os.path.join(BASE, 'prototype_softdynamics.blend')

rm = np.load(os.path.join(BASE, 'work/root_motion.npz'))
sim = np.load(os.path.join(BASE, 'work/sim_results.npz'))
basis = rm['basis_armature']                 # columns: side, fwd, up (armature)
attach_rest = rm['attach_rest_armature']
hips_rot_all = rm['hips_rot']                # includes preroll offset
MW = rm['MW']

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.fps = 30
scene.frame_start, scene.frame_end = 1, N_FRAMES

with bpy.data.libraries.load(SRC) as (data_from, data_to):
    data_to.objects = ['Wolf_SRC', 'BaraWolfBody']
    data_to.actions = ['Walk']
for ob in data_to.objects:
    scene.collection.objects.link(ob)
arm = bpy.data.objects['Wolf_SRC']
body = bpy.data.objects['BaraWolfBody']
walk = bpy.data.actions['Walk']
if body.parent is not None and body.parent.name not in bpy.data.objects:
    body.parent = None
for mod in body.modifiers:
    if mod.type == 'ARMATURE' and mod.object is None:
        mod.object = arm
print('BODY bbox center:', np.round(np.array(body.matrix_world.translation), 3),
      'dims:', np.round(np.array(body.dimensions), 2))

MWm = Matrix(MW)
MW_inv = MWm.inverted()

# ---------------------------------------------------------------- bones ----
J = [np.array(attach_rest)]
for off in REST_OFFSETS:
    J.append(J[-1] + basis @ np.array(off))
J = np.array(J)                              # 5 joints, armature space

bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.data.edit_bones
hips_eb = eb['mixamorig:Hips']
sac_bones = []
for i in range(4):
    b = eb.new(f'AF_Sac{i + 1}')
    b.head = J[i]
    b.tail = J[i + 1]
    b.parent = hips_eb if i == 0 else sac_bones[-1]
    b.use_connect = False
    sac_bones.append(b)
teat_bones = {}
side_v, fwd_v, up_v = basis[:, 0], basis[:, 1], basis[:, 2]
for label, sgn in [('L', -1.0), ('R', 1.0)]:
    off = np.array(TEAT_OFFSET)
    off[0] = 0.010 * sgn
    head = J[4] + side_v * (0.05 * sgn) + fwd_v * 0.010
    b = eb.new(f'AF_Teat{label}')
    b.head = head
    b.tail = head + basis @ off
    b.parent = sac_bones[-1]
    b.use_connect = False
    teat_bones[label] = b
bpy.ops.object.mode_set(mode='OBJECT')
for name in ['AF_Sac1', 'AF_Sac2', 'AF_Sac3', 'AF_Sac4', 'AF_TeatL', 'AF_TeatR']:
    arm.pose.bones[name].rotation_mode = 'QUATERNION'

# ---------------------------------------------------------------- loft -----
SEG_T = np.concatenate([[0], np.cumsum(
    [np.linalg.norm(o) for o in REST_OFFSETS])])
SEG_T = SEG_T / SEG_T[-1]
R_PROF = [(0.0, 0.030), (0.12, 0.058), (0.35, 0.095), (0.60, 0.112),
          (0.82, 0.100), (0.95, 0.062), (1.0, 0.028)]


def radius_at(t):
    for (t0, r0), (t1, r1) in zip(R_PROF, R_PROF[1:]):
        if t <= t1:
            return r0 + (r1 - r0) * (t - t0) / (t1 - t0)
    return R_PROF[-1][1]


def point_at(t):
    """Point + tangent on the J polyline at arc parameter t."""
    for j in range(4):
        if t <= SEG_T[j + 1] or j == 3:
            u = (t - SEG_T[j]) / (SEG_T[j + 1] - SEG_T[j])
            u = min(max(u, 0.0), 1.0)
            p = J[j] + (J[j + 1] - J[j]) * u
            tan = J[j + 1] - J[j]
            return p, tan / np.linalg.norm(tan)
    raise RuntimeError


def tent_weights(t):
    """Smooth partition-of-unity weights over AF_Sac1..4 at arc param t."""
    h = 0.5 * float(np.mean(np.diff(SEG_T)))
    w = []
    for b in range(4):
        lo, hi = SEG_T[b], SEG_T[b + 1]
        a = min(max((t - (lo - h)) / (2 * h), 0.0), 1.0)
        c = min(max(((hi + h) - t) / (2 * h), 0.0), 1.0)
        w.append(a * c)
    w = np.array(w)
    return w / w.sum()


N_RING, N_SEG = 13, 16
verts, faces, soft_vals, bone_w = [], [], [], []
for ri in range(N_RING):
    t = ri / (N_RING - 1)
    C, tan = point_at(t)
    S = side_v - tan * np.dot(side_v, tan)
    S /= np.linalg.norm(S)
    B = np.cross(tan, S)
    r = radius_at(t)
    w = tent_weights(t)
    s = 0.15 + 0.85 * t ** 1.25
    for si in range(N_SEG):
        a = 2 * np.pi * si / N_SEG
        verts.append(C + r * (np.cos(a) * S + np.sin(a) * B))
        soft_vals.append(s)
        bone_w.append(w)
pole = J[4] + point_at(1.0)[1] * 0.02
verts.append(pole)
soft_vals.append(1.0)
bone_w.append(tent_weights(1.0))
pole_i = len(verts) - 1
for ri in range(N_RING - 1):
    for si in range(N_SEG):
        a = ri * N_SEG + si
        b_ = ri * N_SEG + (si + 1) % N_SEG
        c = (ri + 1) * N_SEG + si
        d = (ri + 1) * N_SEG + (si + 1) % N_SEG
        faces.append((a, c, d, b_))
last = (N_RING - 1) * N_SEG
for si in range(N_SEG):
    faces.append((last + si, pole_i, last + (si + 1) % N_SEG))

mesh = bpy.data.meshes.new('AF_SacMesh')
mesh.from_pydata([tuple(v) for v in verts], [], faces)
mesh.update()
for poly in mesh.polygons:
    poly.use_smooth = True
sac_obj = bpy.data.objects.new('AF_Sac', mesh)
scene.collection.objects.link(sac_obj)
for i in range(4):
    vg = sac_obj.vertex_groups.new(name=f'AF_Sac{i + 1}')
    for vi, w in enumerate(bone_w):
        if w[i] > 1e-4:
            vg.add([vi], float(w[i]), 'REPLACE')
vg_soft = sac_obj.vertex_groups.new(name='AF_softness')
for vi, s in enumerate(soft_vals):
    vg_soft.add([vi], float(s), 'REPLACE')
mat = bpy.data.materials.new('AF_SacSkin')
bsdf = mat.node_tree.nodes['Principled BSDF']
bsdf.inputs['Base Color'].default_value = (0.45, 0.30, 0.24, 1)
bsdf.inputs['Roughness'].default_value = 0.55
mesh.materials.append(mat)
mod = sac_obj.modifiers.new('Armature', 'ARMATURE')
mod.object = arm
sac_obj.parent = arm
sac_obj.matrix_parent_inverse = MWm.inverted()

# ---------------------------------------------------------------- teats ----
for label in ['L', 'R']:
    bone = arm.data.bones[f'AF_Teat{label}']
    head = np.array(bone.head_local)
    tail = np.array(bone.tail_local)
    d = tail - head
    d /= np.linalg.norm(d)
    center = head + d * 0.024
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.0165,
                                          location=tuple(center))
    tob = bpy.context.active_object
    tob.name = f'AF_Teat{label}'
    # verts are edited in ARMATURE space (absolute), so the object itself
    # must sit at the origin -- reset the primitive's location, otherwise
    # the centre offset is applied twice (caught in mesh diagnostics).
    tob.location = (0.0, 0.0, 0.0)
    tob.rotation_euler = (0.0, 0.0, 0.0)
    tob.scale = (1.0, 1.0, 1.0)
    # elongate along the bone direction. NOTE: primitive verts are LOCAL
    # (centred on origin); the armature-space position is centre + local'.
    R = np.column_stack([side_v, fwd_v, d])
    for v in tob.data.vertices:
        local = np.array(v.co)
        v.co = Vector(center + R @ (np.array([1.0, 1.0, 1.35]) *
                                    (R.T @ local)))
    tob.data.materials.append(mat)
    vg = tob.vertex_groups.new(name=f'AF_Teat{label}')
    vg.add(list(range(len(tob.data.vertices))), 1.0, 'REPLACE')
    vgs = tob.vertex_groups.new(name='AF_softness')
    vgs.add(list(range(len(tob.data.vertices))), 1.0, 'REPLACE')
    m2 = tob.modifiers.new('Armature', 'ARMATURE')
    m2.object = arm
    tob.parent = arm
    tob.matrix_parent_inverse = MWm.inverted()

# ------------------------------------------------------- action baking -----
def bone_rest_data(name):
    b = arm.data.bones[name]
    return (b.matrix_local.to_3x3(),
            (Vector(b.tail_local) - Vector(b.head_local)).normalized(),
            b.parent.name if b.parent else None)


def chain_quaternions(pos_world, parent0_rot, chain_names):
    """Analytic local rotation quaternions from sim particle positions."""
    n = len(pos_world)
    quats = {name: np.empty((n, 4)) for name in chain_names}
    rest = {name: bone_rest_data(name) for name in chain_names}
    parent_world_R = [None] * n
    for i in range(n):
        P = [MW_inv @ Vector(p) for p in pos_world[i]]
        Rpar = Matrix(parent0_rot[i]).to_3x3()
        for bi, name in enumerate(chain_names):
            Rrest, rest_dir, pname = rest[name]
            cur_dir = (P[bi + 1] - P[bi]).normalized()
            A = rest_dir.rotation_difference(cur_dir).to_matrix()
            W = A @ Rrest
            Lrest = (arm.data.bones[pname].matrix_local.to_3x3().inverted()
                     @ Rrest)
            q = (Lrest.inverted() @ Rpar.inverted() @ W).to_quaternion()
            quats[name][i] = (q.w, q.x, q.y, q.z)
            Rpar = W
        parent_world_R[i] = Rpar
    return quats, parent_world_R


hips_rot_kept = hips_rot_all[PREROLL:]       # (186,3,3) armature space
sac_names = ['AF_Sac1', 'AF_Sac2', 'AF_Sac3', 'AF_Sac4']


def extend_action(setting):
    sac_pos = sim[f'sac_{setting}']
    quats, tip_R = chain_quaternions(sac_pos, hips_rot_kept, sac_names)
    all_quats = dict(quats)
    for label in ['L', 'R']:
        tpos = sim[f'teat{label}_{setting}']
        tq, _ = chain_quaternions(tpos, tip_R, [f'AF_Teat{label}'])
        all_quats.update(tq)
    act = walk.copy()
    act.name = f'AF_Full_{setting.title()}'
    act.use_fake_user = True
    cb = act.layers[0].strips[0].channelbags[0]
    for fc in cb.fcurves:
        vals = [fc.evaluate(fr) for fr in range(1, 34)]
        kps = fc.keyframe_points
        while len(kps):
            kps.remove(kps[0])
        co = []
        for f in range(1, N_FRAMES + 1):
            v = vals[(f - 1) % 32] if f <= N_WALK else vals[32]
            co += [float(f), float(v)]
        kps.add(N_FRAMES)
        kps.foreach_set('co', co)
        for kp in kps:
            kp.interpolation = 'LINEAR'
        fc.update()
    for bname, arr in all_quats.items():
        for idx in range(4):
            fc = cb.fcurves.new(
                data_path=f'pose.bones["{bname}"].rotation_quaternion',
                index=idx, group_name='AF_Dynamics')
            co = []
            for f in range(1, N_FRAMES + 1):
                co += [float(f), float(arr[f - 1][idx])]
            fc.keyframe_points.add(N_FRAMES)
            fc.keyframe_points.foreach_set('co', co)
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'
            fc.update()
    return act


act_soft = extend_action('SOFT')
act_firm = extend_action('FIRM')

# ------------------------------------------------------ ground / camera ----
bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
ground = bpy.context.active_object
ground.name = 'Ground'
gmat = bpy.data.materials.new('Clay')
gmat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = \
    (0.32, 0.32, 0.34, 1)
ground.data.materials.append(gmat)

cam_data = bpy.data.cameras.new('Cam')
cam = bpy.data.objects.new('Cam', cam_data)
scene.collection.objects.link(cam)
target = Vector(MWm @ Vector(attach_rest + np.array([0, 0, -0.22])))
side_w = Vector(MW[:3, :3] @ basis[:, 0])
fwd_w = Vector(MW[:3, :3] @ basis[:, 1])
cam.location = target + side_w * 1.05 + fwd_w * 1.05 + Vector((0, 0, 0.06))
direction = target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
cam_data.lens = 55
scene.camera = cam

sun_data = bpy.data.lights.new('Sun', 'SUN')
sun_data.energy = 2.5
sun = bpy.data.objects.new('Sun', sun_data)
scene.collection.objects.link(sun)
sun.rotation_euler = (0.9, 0.2, 0.6)
world = bpy.data.worlds.new('W')
scene.world = world
world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.5

scene['af_dynamics'] = json.dumps({
    'format': 'anthroforge.dynamics.prototype',
    'actions': {'soft': act_soft.name, 'firm': act_firm.name},
    'chain_bones': sac_names + ['AF_TeatL', 'AF_TeatR'],
    'softness_field': 'AF_softness',
    'timeline': 'frames 1-96 walk (Walk x3), 97-186 settle (root frozen)',
})

# ------------------------------------------------------------ verify -------
ad = arm.animation_data_create()
ad.action = act_soft
if act_soft.slots:
    ad.action_slot = act_soft.slots[0]
report = {}
for f_check in (40, 150):
    scene.frame_set(f_check)
    bpy.context.view_layer.update()
    tip = np.array(arm.matrix_world @ arm.pose.bones['AF_Sac4'].tail)
    want = sim['sac_SOFT'][f_check - 1][-1]
    report[f_check] = float(np.linalg.norm(tip - want))
    print(f'VERIFY frame {f_check}: sac tip error '
          f'{report[f_check] * 1000:.1f} mm (sim {np.round(want, 3)} '
          f'got {np.round(tip, 3)})')
# teat MESH placement check (bone tips were fine in run 1 while the meshes
# were displaced by a local-vs-armature-space bug -- verify meshes directly)
scene.frame_set(1)
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
for label in ('L', 'R'):
    ob = bpy.data.objects[f'AF_Teat{label}']
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    vs = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get('co', vs)
    vs = vs.reshape(-1, 3)
    W = np.array(ev.matrix_world)
    vs = vs @ W[:3, :3].T + W[:3, 3]
    centroid = vs.mean(axis=0)
    expect = sim[f'teat{label}_SOFT'][0].mean(axis=0)
    err = float(np.linalg.norm(centroid - expect))
    print(f'VERIFY teat{label} mesh centroid error {err * 1000:.1f} mm '
          f'(expect {np.round(expect, 3)} got {np.round(centroid, 3)})')
    assert err < 0.015, f'teat{label} mesh misplaced'
    ev.to_mesh_clear()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('BUILD_OK', OUT, 'tip_errors_mm:',
      {k: round(v * 1000, 1) for k, v in report.items()})
