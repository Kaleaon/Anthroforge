"""Render stride frames from the soft-dynamics prototype.

Clay override, Cycles CPU. Picks the lateral-swing extreme frames of the
third walk cycle from the sim data and renders them under BOTH baked
actions (same frames = direct stiffness comparison), plus a settle frame
and the frame-1 hang reference.
Run: blender -b --factory-startup -noaudio prototype_softdynamics.blend \
     --python render_prototype.py
"""
import os
import sys

import bpy
import numpy as np

BASE = os.path.expanduser('~/workspace/anthroforge-v2/dynamics')
rm = np.load(os.path.join(BASE, 'work/root_motion.npz'))
sim = np.load(os.path.join(BASE, 'work/sim_results.npz'))
sys.path.insert(0, os.path.join(BASE, 'scripts'))
from proto_common import PREROLL, REST_OFFSETS

root_pos = rm['root_pos'][PREROLL:]
root_R = rm['root_R'][PREROLL:]
rest_tip = np.sum(np.array(REST_OFFSETS), axis=0)
desired = np.einsum('fij,j->fi', root_R, rest_tip) + root_pos
tip_err = sim['sac_SOFT'][:, -1, :] - desired
side_err = np.einsum('fi,fi->f', tip_err, root_R[:, :, 0])
window = range(64, 96)                       # third cycle, 0-based indices
f_max = max(window, key=lambda i: side_err[i]) + 1
f_min = min(window, key=lambda i: side_err[i]) + 1
print('SWING FRAMES: max side', f_max, 'min side', f_min)

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 24
scene.cycles.use_denoising = False
scene.render.resolution_x = 560
scene.render.resolution_y = 420
clay = bpy.data.materials.new('ClayOverride')
clay.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = \
    (0.55, 0.52, 0.50, 1)
scene.view_layers[0].material_override = clay

arm = bpy.data.objects['Wolf_SRC']
ad = arm.animation_data
outdir = os.path.join(BASE, 'renders')
jobs = [('soft', 'AF_Full_Soft', [f_max, 150, 1]),
        ('firm', 'AF_Full_Firm', [f_max, 150])]
for label, act_name, frames in jobs:
    act = bpy.data.actions[act_name]
    ad.action = act
    if act.slots:
        ad.action_slot = act.slots[0]
    for f in frames:
        scene.frame_set(f)
        scene.render.filepath = os.path.join(outdir, f'{label}_f{f:03d}.png')
        bpy.ops.render.render(write_still=True)
        print('RENDERED', label, f)
print('RENDER_OK swing frames:', f_max, f_min)
