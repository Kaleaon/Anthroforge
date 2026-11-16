"""B2 stage 4: silhouette comparison from render alpha masks +
retopo wireframe plot. Merges all stage stats into work/stats.json."""
import json
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree

OUT = '/home/hatch/workspace/anthroforge-v2/model-craft/b2-retopo'

def mask_of(tag, view):
    im = Image.open(f'{OUT}/renders/{tag}_{view}.png')
    return np.asarray(im)[:, :, 3] > 127

def boundary(mask):
    er = mask.copy()
    er[1:, :] &= mask[:-1, :]; er[:-1, :] &= mask[1:, :]
    er[:, 1:] &= mask[:, :-1]; er[:, :-1] &= mask[:, 1:]
    b = mask & ~er
    ys, xs = np.nonzero(b)
    return np.stack([xs, ys], axis=1).astype(np.float64)

sil = {}
for view in ('front', 'profile', 'top'):
    m1, m2 = mask_of('before', view), mask_of('after', view)
    iou = float(np.logical_and(m1, m2).sum() / np.logical_or(m1, m2).sum())
    b1, b2 = boundary(m1), boundary(m2)
    d12 = cKDTree(b2).query(b1[::5])[0]
    d21 = cKDTree(b1).query(b2[::5])[0]
    d = np.concatenate([d12, d21])
    sil[view] = dict(iou=round(iou, 4),
                     boundary_mean_px=round(float(d.mean()), 2),
                     boundary_p95_px=round(float(np.percentile(d, 95)), 2),
                     boundary_max_px=round(float(d.max()), 2),
                     boundary_mean_pct_diag=round(float(d.mean() / 512 * 100), 3))
    print(view, sil[view])

# wireframe plot: retopo verts are in sculpt-local coords (Y-up-ish frame:
# local x = width, local y = height axis pre-rotation, local z = depth)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

d = np.load(f'{OUT}/work/edges.npz')
V, E = d['retopo_verts'], d['retopo_edges']
rng = np.random.default_rng(3)
sel = E if len(E) <= 20000 else E[rng.choice(len(E), 20000, replace=False)]
fig, axes = plt.subplots(1, 2, figsize=(11, 5.5), facecolor='black')
for ax, (a, b, title) in zip(axes, [(0, 1, 'front (local x/y)'),
                                    (2, 1, 'profile (local z/y)')]):
    segs = np.stack([V[sel[:, 0]][:, [a, b]], V[sel[:, 1]][:, [a, b]]], axis=1)
    ax.add_collection(LineCollection(segs, colors='#7fd4ff', linewidths=0.25))
    ax.set_xlim(V[:, a].min() - 3, V[:, a].max() + 3)
    ax.set_ylim(V[:, b].min() - 3, V[:, b].max() + 3)
    ax.set_aspect('equal'); ax.set_facecolor('black'); ax.set_title(title, color='white')
    ax.tick_params(colors='white')
fig.suptitle('RETOPO_orc_head — 5,811 quads, edge flow (QuadriFlow)', color='white')
fig.tight_layout()
fig.savefig(f'{OUT}/renders/retopo_wireframe.png', facecolor='black', dpi=110)
print('wireframe plot saved')

stats = {}
import os
for s in ('stage1a', 'stage1', 'stage2'):
    p = f'{OUT}/work/stats_{s}.json'
    if os.path.exists(p):
        with open(p) as f:
            stats.update(json.load(f))
stats['silhouette'] = sil
with open(f'{OUT}/work/stats.json', 'w') as f:
    json.dump(stats, f, indent=1, default=str)
print('B2_STAGE4_DONE')
