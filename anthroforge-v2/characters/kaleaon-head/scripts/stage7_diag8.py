#!/usr/bin/env python3
"""Bisect the mane asymmetry: recompute the stage-7 field stack on
stage6 geometry and check mirrored-nearest symmetry after each step."""
import sys
from collections import defaultdict
from pathlib import Path

import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import kaleaon_fields as F
from kaleaon_io import world_co

CHAR = Path("/home/hatch/workspace/anthroforge-v2/characters/kaleaon-head")
bpy.ops.wm.open_mainfile(filepath=str(CHAR / "work" / "stage6.blend"))
objs = {o.name: o for o in bpy.data.objects if o.type == "MESH"}
tis = objs["TissueHead"]
TW, _ = world_co(tis)
L = float(TW[:, 1].max() - TW[:, 1].min())
pal_z = -0.17988
eye_c = {}
for s in ("L", "R"):
    W0, _ = world_co(objs[f"Eyeball_{s}"])
    eye_c[s] = W0.mean(axis=0)
eye_y = float(np.mean([eye_c["L"][1], eye_c["R"][1]]))
eye_z = float(np.mean([eye_c["L"][2], eye_c["R"][2]]))
top_z = float(TW[:, 2].max())
H_abs = top_z - pal_z

tris = []
for p in tis.data.polygons:
    idx = list(p.vertices)
    for k in range(1, len(idx) - 1):
        tris.append((idx[0], idx[k], idx[k + 1]))
tris = np.array(tris)
adj = defaultdict(set)
for a, b, c in tris:
    adj[a].update((b, c))
    adj[b].update((a, c))
    adj[c].update((a, b))
A, B, C = TW[tris[:, 0]], TW[tris[:, 1]], TW[tris[:, 2]]
fn = np.cross(B - A, C - A)
vn = np.zeros_like(TW)
for i in range(3):
    np.add.at(vn, tris[:, i], fn)
vn = vn / np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-12)


def smooth(field, iters):
    f = field.copy()
    for _ in range(iters):
        g = f.copy()
        for i, ns in adj.items():
            if ns:
                g[i] = 0.5 * f[i] + 0.5 * np.mean([f[j] for j in ns])
        f = g
    return f


def sym(P, mask=None):
    Q = P if mask is None else P[mask]
    src = Q[Q[:, 0] > 0.002]
    mir = src * np.array([-1.0, 1.0, 1.0])
    best = np.full(len(src), 1e9)
    for i in range(0, len(Q), 1024):
        chunk = Q[i:i + 1024]
        d = np.sqrt(((mir[:, None, :] - chunk[None, :, :]) ** 2).sum(-1)).min(axis=1)
        best = np.minimum(best, d)
    return round(float(best.mean()), 5), round(float(best.max()), 4)


print("TW tissue:", sym(TW))
ear_base = {}
for s in ("L", "R"):
    EW, _ = world_co(objs[f"Ear_{s}"])
    d = np.sqrt(((EW[:, None, :] - TW[None, :, :]) ** 2).sum(-1)).min(axis=1)
    ear_base[s] = EW[d < np.percentile(d, 25)].mean(axis=0)
print("ear bases:", {k: np.round(v, 3).tolist() for k, v in ear_base.items()})
face = (TW[:, 1] > eye_y - 0.02 * L) & (TW[:, 2] > pal_z + 0.13 * L) \
    & (np.abs(TW[:, 0]) < 0.30 * L)
face = face | ((TW[:, 2] > eye_z + 0.08 * L)
               & (TW[:, 1] > eye_y - 0.12 * L)
               & (np.abs(TW[:, 0]) < 0.34 * L))


def seg_dist_u(P, a, b):
    ab = b - a
    u = np.clip(((P - a) @ ab) / (ab @ ab), 0, 1)
    return np.linalg.norm(P - (a + np.outer(u, ab)), axis=1), u


corr = np.full(len(TW), 1e9)
corr_u = np.zeros(len(TW))
for s in ("L", "R"):
    dd, uu = seg_dist_u(TW, eye_c[s], ear_base[s])
    take = dd < corr
    corr = np.where(take, dd, corr)
    corr_u = np.where(take, uu, corr_u)
temple = (corr < 0.055 * L) & (corr_u < 0.55) & (TW[:, 2] > eye_z - 0.02 * L)
zone = (~face) & (~temple)
print("zone verts:", sym(TW, zone))
w = np.clip(smooth(zone.astype(float), 5), 0, 1)
print("w asymmetry (max |w - mirror w| via nearest): ")
z_c = pal_z + 0.55 * H_abs
cheek = np.exp(-(((TW[:, 2] - z_c) / (0.15 * L)) ** 2)) \
    * F.sstep(np.abs(TW[:, 0]), 0.05 * L, 0.22 * L)
back = F.sstep(TW[:, 1], eye_y - 0.05 * L, eye_y - 0.35 * L)
crown = F.sstep(TW[:, 2], eye_z + 0.10 * L, eye_z + 0.22 * L)
earcap = np.zeros(len(TW))
for s in ("L", "R"):
    cap_c = ear_base[s] + np.array([0.0, 0.010 * L, 0.045 * L])
    dd = np.linalg.norm(TW - cap_c, axis=1)
    earcap = np.maximum(earcap, np.exp(-((dd / (0.12 * L)) ** 2)))
t = smooth(0.040 + 0.155 * cheek + 0.070 * back + 0.030 * crown
           + 0.036 * earcap, 4)
sweep = 0.05 * L * F.sstep(TW[:, 1], eye_y, eye_y - 0.30 * L)
drape = -0.03 * L * (1.0 - F.sstep(TW[:, 2], pal_z + 0.02 * L,
                                   pal_z + 0.14 * L))
MP0 = TW + vn * (t * w)[:, None]
MP0[:, 1] -= sweep * w
MP0[:, 2] += drape * w
print("MP with raw vn:", sym(MP0, zone))
vn_s = smooth(vn, 3)
vn_s = vn_s / np.maximum(np.linalg.norm(vn_s, axis=1, keepdims=True), 1e-12)
MP1 = TW + vn_s * (t * w)[:, None]
MP1[:, 1] -= sweep * w
MP1[:, 2] += drape * w
print("MP with smoothed vn:", sym(MP1, zone))
for s in ("L", "R"):
    side = 1.0 if ear_base[s][0] >= 0 else -1.0
    dd = np.linalg.norm(TW - ear_base[s], axis=1)
    same_side = (np.sign(TW[:, 0]) == side) & (np.abs(TW[:, 0]) > 0.05 * L)
    bulge = 0.07 * L * np.exp(-((dd / (0.14 * L)) ** 2)) * w * same_side
    MP1[:, 0] = MP1[:, 0] + side * bulge
print("MP + bulge:", sym(MP1, zone))
print("BISECT DONE")
