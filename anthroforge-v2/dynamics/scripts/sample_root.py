"""Sample the root (Hips) motion of the bara wolf Walk clip.

Reads the retarget prototype blend, plays Walk on Wolf_SRC, and records for
every output frame of the prototype timeline (3 walk cycles + frozen settle):
  - the world position of the sac-chain attach point (pelvis front-below)
  - the world rotation of the chain root frame (side / forward / up basis)
  - the Hips pose rotation in armature space (needed for analytic baking)
Output: dynamics/work/root_motion.npz
Run: blender -b --factory-startup -noaudio --python sample_root.py
"""
import bpy
import numpy as np
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from proto_common import FPS, CYCLE, N_WALK, N_FRAMES, PREROLL

SRC = os.path.expanduser('~/workspace/anthroforge-v2/retarget-prototype/'
                         'retarget_prototype.blend')
OUT = os.path.expanduser('~/workspace/anthroforge-v2/dynamics/work/'
                         'root_motion.npz')

bpy.ops.wm.open_mainfile(filepath=SRC)
arm = bpy.data.objects['Wolf_SRC']
scene = bpy.context.scene
scene.render.fps = int(FPS)

walk = bpy.data.actions['Walk']
arm.animation_data_create()
arm.animation_data.action = walk

hips = arm.pose.bones['mixamorig:Hips']
hips_bone = hips.bone

# --- rest-pose character frame (armature space) -----------------------------
foot = np.array(arm.data.bones['mixamorig:LeftFoot'].head_local)
toe = np.array(arm.data.bones['mixamorig:LeftToeBase'].head_local)
fwd = toe - foot
fwd[2] = 0.0
fwd /= np.linalg.norm(fwd)
up = np.array([0.0, 0.0, 1.0])
side = np.cross(up, fwd)
side /= np.linalg.norm(side)
fwd = np.cross(side, up)  # re-orthogonalise
basis = np.column_stack([side, fwd, up])   # root-frame basis, armature space

hips_head = np.array(hips_bone.head_local)
attach_rest = hips_head + fwd * 0.10 - up * 0.03   # groin, front-below pelvis
from mathutils import Matrix, Vector
Minv = hips_bone.matrix_local.inverted()
attach_in_bone = np.array(Minv @ Vector(attach_rest))

MW = np.array(arm.matrix_world)
MW_rot = MW[:3, :3]

n = PREROLL + N_FRAMES
root_pos = np.empty((n, 3))
root_R = np.empty((n, 3, 3))
hips_rot = np.empty((n, 3, 3))
dg = bpy.context.evaluated_depsgraph_get()
for i in range(n):
    f = i - PREROLL
    if f < 0:
        af = 1
    elif f < N_WALK:
        af = 1 + (f % CYCLE)
    else:
        af = CYCLE + 1   # frame 33, the loop-dupe pose, frozen
    scene.frame_set(af)
    bpy.context.view_layer.update()
    pm = np.array(hips.matrix)                       # pose, armature space
    attach_world = MW @ (pm @ np.append(attach_in_bone, 1.0))
    root_pos[i] = attach_world[:3]
    R_delta = pm[:3, :3] @ np.array(hips_bone.matrix_local)[:3, :3].T
    R_arm = R_delta @ basis
    root_R[i] = MW_rot @ R_arm
    hips_rot[i] = pm[:3, :3]

# loop-seam check: hips pose at action frame 1 vs 33
scene.frame_set(1)
bpy.context.view_layer.update()
m1 = np.array(hips.matrix)
scene.frame_set(CYCLE + 1)
bpy.context.view_layer.update()
m33 = np.array(hips.matrix)
seam = float(np.abs(m1 - m33).max())

np.savez(OUT, root_pos=root_pos, root_R=root_R, hips_rot=hips_rot,
         basis_armature=basis, attach_rest_armature=attach_rest,
         hips_head_armature=hips_head, MW=MW, seam_max_delta=seam,
         preroll=PREROLL)
print(f'SAMPLED_OK frames={n} seam_max_delta={seam:.6f}')
print('attach_rest(armature) =', np.round(attach_rest, 4))
print('basis side/fwd =', np.round(side, 3), np.round(fwd, 3))
print('root_pos[30] (first kept) =', np.round(root_pos[PREROLL], 4))
print('root bob range z =', float(root_pos[PREROLL:PREROLL + N_WALK, 2].min()),
      float(root_pos[PREROLL:PREROLL + N_WALK, 2].max()))
