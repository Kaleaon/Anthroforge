#!/usr/bin/env python3
"""Kaleaon head Phase 2 - Stage 7: mane shell + tufts (spec S8.7).

NEW authored geometry. The mane is a sculpted shell: the deformed
tissue surface inside a mane zone (everything but the face, with a
temple clearance corridor carved out for the future glasses) is
displaced outward along its normals by a band profile - fullest at
cheek level (S12: max width 1.02 +- 0.05 L at ~0.60 of head height),
swept back, draped at the ruff - with the displacement field smoothed
over the surface and faded to skin at the face opening. Cheek tufts
and the chin tuft are separate smaller shells from cheek/jaw patches
(standards v2: distinct masses, not part of the mane shell). The
underside stays open for the later groom + braid root (spec S6).

    blender -b --threads 2 --python stage7_mane.py
In:  work/stage6.blend
Out: work/stage7.blend + work/stage7.json
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, str(Path(__file__).parent))
import kaleaon_fields as F
from kaleaon_io import world_co, group_weights

CHAR = Path("/home/hatch/workspace/anthroforge-v2/characters/kaleaon-head")
bpy.ops.wm.open_mainfile(filepath=str(CHAR / "work" / "stage6.blend"))
objs = {o.name: o for o in bpy.data.objects if o.type == "MESH"}
tis, jaw = objs["TissueHead"], objs["Jaw"]
TW, _ = world_co(tis)
L = float(TW[:, 1].max() - TW[:, 1].min())
pal_z = float(world_co(objs["TeethUpper"])[0][
    world_co(objs["TeethUpper"])[0][:, 1] > 0.18][:, 2].max())
eye_c = {}
for s in ("L", "R"):
    W0, _ = world_co(objs[f"Eyeball_{s}"])
    eye_c[s] = W0.mean(axis=0)
eye_y = float(np.mean([eye_c["L"][1], eye_c["R"][1]]))
eye_z = float(np.mean([eye_c["L"][2], eye_c["R"][2]]))
top_z = float(TW[:, 2].max())
H_abs = top_z - pal_z
report = {"L": L, "pal_z": pal_z, "top_z": top_z, "H_abs": H_abs}

# adjacency + vertex normals (numpy, world frame)
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


def seg_dist_u(P, a, b):
    ab = b - a
    u = np.clip(((P - a) @ ab) / (ab @ ab), 0, 1)
    return np.linalg.norm(P - (a + np.outer(u, ab)), axis=1), u


# ---- mane zone + fade
ear_base = {}
for s in ("L", "R"):
    EW, _ = world_co(objs[f"Ear_{s}"])
    d = np.sqrt(((EW[:, None, :] - TW[None, :, :]) ** 2).sum(-1)).min(axis=1)
    ear_base[s] = EW[d < np.percentile(d, 25)].mean(axis=0)
face = (TW[:, 1] > eye_y - 0.02 * L) & (TW[:, 2] > pal_z + 0.13 * L) \
    & (np.abs(TW[:, 0]) < 0.30 * L)
# Forehead wedge (7b): the first build's shell edge overhung the brow
# as a slab - the face opening now also takes the front-top wedge so
# the shell's edge lands behind the brow line.
face = face | ((TW[:, 2] > eye_z + 0.08 * L)
               & (TW[:, 1] > eye_y - 0.12 * L)
               & (np.abs(TW[:, 0]) < 0.34 * L))
# Temple corridor: the FRONT of the eye->ear line only (u < 0.55,
# radius 0.055 L). The first build carved a 0.075 ball around the
# whole segment INCLUDING its ear-base end, which left the ear
# sitting in a bald patch instead of buried in the mane (measured:
# 160/285 ear verts outside the shell silhouette). The glasses arm
# runs over the temple, not over the ear seat.
corr = np.full(len(TW), 1e9)
corr_u = np.zeros(len(TW))
for s in ("L", "R"):
    dd, uu = seg_dist_u(TW, eye_c[s], ear_base[s])
    take = dd < corr
    corr = np.where(take, dd, corr)
    corr_u = np.where(take, uu, corr_u)
temple = (corr < 0.055 * L) & (corr_u < 0.55) & (TW[:, 2] > eye_z - 0.02 * L)
zone = (~face) & (~temple)
w = smooth(zone.astype(float), 5)
w = np.clip(w, 0, 1)

# ---- thickness profile
z_c = pal_z + 0.55 * H_abs
cheek = np.exp(-(((TW[:, 2] - z_c) / (0.15 * L)) ** 2)) \
    * F.sstep(np.abs(TW[:, 0]), 0.05 * L, 0.22 * L)
back = F.sstep(TW[:, 1], eye_y - 0.05 * L, eye_y - 0.35 * L)
crown = F.sstep(TW[:, 2], eye_z + 0.10 * L, eye_z + 0.22 * L)
# ear cap: the mane is thick over the ear seat (the ear sits IN the
# mass, S14) - extra offset around each ear base, posterior side only
earcap = np.zeros(len(TW))
for s in ("L", "R"):
    # centre shifted up-back toward the tip (7b): with smoothed
    # normals the cap formed forward of the tip, leaving it in a
    # pocket 0.044 from the surface; the shifted, wider cap drapes
    # over the tip itself.
    cap_c = ear_base[s] + np.array([0.0, 0.010 * L, 0.045 * L])
    dd = np.linalg.norm(TW - cap_c, axis=1)
    earcap = np.maximum(earcap, np.exp(-((dd / (0.12 * L)) ** 2)))
t = 0.040 + 0.155 * cheek + 0.070 * back + 0.030 * crown + 0.036 * earcap
t = smooth(t, 4)
sweep = 0.05 * L * F.sstep(TW[:, 1], eye_y, eye_y - 0.30 * L)
drape = -0.03 * L * (1.0 - F.sstep(TW[:, 2], pal_z + 0.02 * L,
                                   pal_z + 0.14 * L))
# Normal-field smoothing (7b): the raw vn field of the low-poly tissue
# varies sharply per vertex; at mane thicknesses (up to ~0.29 L
# stacked) neighbouring verts shot along divergent normals and the
# shell read as crumpled sheet in the first clay renders. The fix
# smooths the DIRECTION field only (diffusion is safe there - the
# thickness profile t*w is already smooth and keeps its amplitude).
# A first attempt smoothed the displacement vector itself (6 iters):
# amplitude collapsed (width 0.98 -> 0.73) - reverted.
vn_s = smooth(vn, 3)
# Symmetrise the smoothed normals (7b fix): iterated neighbourhood
# averaging propagates the tissue graph's small L/R tessellation
# differences into a systematic per-side drift (measured: mirrored
# displacement mean 0.001 with raw vn vs 0.031 after smoothing).
# Pair each vertex with its mirror partner and average the pair
# (x component negated) so the field is mirror-exact by construction.
_mir = TW * np.array([-1.0, 1.0, 1.0])
_pair = np.zeros(len(TW), dtype=int)
for _i in range(0, len(TW), 1024):
    _chunk = _mir[_i:_i + 1024]
    _d = np.sqrt(((_chunk[:, None, :] - TW[None, :, :]) ** 2).sum(-1))
    _pair[_i:_i + 1024] = np.argmin(_d, axis=1)
_vn_m = vn_s[_pair] * np.array([-1.0, 1.0, 1.0])
vn_s = 0.5 * (vn_s + _vn_m)
vn_s = vn_s / np.maximum(np.linalg.norm(vn_s, axis=1, keepdims=True),
                         1e-12)
D = vn_s * (t * w)[:, None]
D[:, 1] = D[:, 1] - sweep * w
D[:, 2] = D[:, 2] + drape * w
MP = TW + D
# Ear bulge: a normal-offset shell follows the skull's curve and
# cannot cover the ear's lateral extreme (the cranium narrows and
# its normals tilt up where the ear rides) - the mane gets a
# deliberate lateral bulge around each ear seat instead.
for s in ("L", "R"):
    side = 1.0 if ear_base[s][0] >= 0 else -1.0
    dd = np.linalg.norm(TW - ear_base[s], axis=1)
    same_side = (np.sign(TW[:, 0]) == side) & (np.abs(TW[:, 0]) > 0.05 * L)
    bulge = 0.07 * L * np.exp(-((dd / (0.14 * L)) ** 2)) * w * same_side
    MP[:, 0] = MP[:, 0] + side * bulge
    # NOTE: a (y,z) profile flare around the ear seat was tried and
    # reverted - it stretched the shell's ear-adjacent triangles and
    # REDUCED raster coverage (84 -> 45 inside). S14 is judged by the
    # growth-ray test + renders in stage 8 instead.

zone_faces = [tuple(t_) for t_ in tris
              if zone[t_[0]] and zone[t_[1]] and zone[t_[2]]]
used = sorted(set(v for f_ in zone_faces for v in f_))
remap = {v: i for i, v in enumerate(used)}
mane_faces = [tuple(remap[v] for v in f_) for f_ in zone_faces]
mane_verts = MP[used]


def add_mesh(name, verts, faces):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([tuple(v) for v in verts], [],
                     [tuple(f) for f in faces])
    mesh.update()
    o = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(o)
    return o


# S13 crown taper: narrow the shell's crown band toward <= 0.80 x S12
kc = 1.0 - 0.07 * F.sstep(mane_verts[:, 2], pal_z + 0.70 * H_abs,
                          pal_z + 0.90 * H_abs)
mane_verts = mane_verts.copy()
mane_verts[:, 0] = mane_verts[:, 0] * kc

mane = add_mesh("ManeShell", mane_verts, mane_faces)
MW, _ = world_co(mane)


def mane_stats(MW):
    width = float(np.ptp(MW[:, 0]))
    imax = int(np.argmax(np.abs(MW[:, 0])))
    z_at = float(MW[imax, 2])
    crown_band = MW[MW[:, 2] > pal_z + 0.85 * H_abs]
    return {"width_L": width / L,
            "z_at_max_frac_of_H": (z_at - pal_z) / H_abs,
            "crown_width_L": (float(np.ptp(crown_band[:, 0])) / L
                              if len(crown_band) else None)}


ms = mane_stats(MW)
report["mane_before_fit"] = ms
# S12 fit: one x-scale correction toward 1.02 L if outside the band
if abs(ms["width_L"] - 1.02) > 0.01:
    k = 1.02 / ms["width_L"]
    MW2 = MW.copy()
    MW2[:, 0] = MW2[:, 0] * k
    mane.data.vertices.foreach_set(
        "co", np.array([tuple(v) for v in MW2]).ravel())
    mane.data.update()
    MW, _ = world_co(mane)
    report["mane_x_fit_factor"] = k
ms2 = mane_stats(MW)
if ms2["crown_width_L"] and ms2["width_L"] \
        and ms2["crown_width_L"] / ms2["width_L"] > 0.80:
    k2 = (0.79 * ms2["width_L"] / ms2["crown_width_L"])
    MW3, MM3 = world_co(mane)
    band = MW3[:, 2] > pal_z + 0.80 * H_abs
    MW3[band, 0] = MW3[band, 0] * k2
    from kaleaon_io import set_world as _sw
    _sw(mane, MW3, MM3)
    MW, _ = world_co(mane)
    report["crown_correction_factor"] = float(k2)
report["mane"] = mane_stats(MW)

# S14: ear burial by (y,z)-grid silhouette test - an ear vertex is
# proud if its |x| exceeds the mane's max |x| in its (y,z) bin by
# more than the 0.005 peek tolerance (spec S14).
from collections import defaultdict as _dd
BIN = 0.02
grid = _dd(float)
for p in MW:
    key = (int(np.floor(p[1] / BIN)), int(np.floor(p[2] / BIN)))
    grid[key] = max(grid[key], abs(p[0]))
burial = {}
for s in ("L", "R"):
    EW, _ = world_co(objs[f"Ear_{s}"])
    proud = []
    for p in EW:
        best = 0.0
        ky, kz = int(np.floor(p[1] / BIN)), int(np.floor(p[2] / BIN))
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                best = max(best, grid.get((ky + dy, kz + dz), 0.0))
        if abs(p[0]) > best + 0.005:
            proud.append((float(abs(p[0]) - best), p))
    proud.sort(key=lambda r: -r[0])
    burial[s] = {"proud_verts": len(proud), "total_verts": len(EW),
                 "max_protrusion_L": (proud[0][0] / L if proud else 0.0),
                 "worst_at": (np.round(proud[0][1], 4).tolist()
                              if proud else None)}
report["ear_burial"] = burial
mane_tree = BVHTree.FromPolygons([Vector(v) for v in MW],
                                 mane_faces, all_triangles=True)
# temple corridor clearance
clr = []
for s in ("L", "R"):
    for u in (0.2, 0.4, 0.6, 0.8):
        p = eye_c[s] + u * (ear_base[s] - eye_c[s])
        hit = mane_tree.find_nearest(Vector(p))
        clr.append(float(hit[3]) if hit else None)
report["temple_corridor_min_dist"] = min(x for x in clr if x is not None)

# ---- cheek tufts (distinct masses flanking the muzzle)
for s in ("L", "R"):
    side = 1.0 if s == "L" else -1.0
    m = (np.sign(TW[:, 0]) == side) & (np.abs(TW[:, 0]) > 0.17 * L) \
        & (TW[:, 1] > eye_y - 0.16 * L) & (TW[:, 1] < eye_y + 0.10 * L) \
        & (TW[:, 2] > pal_z + 0.03 * L) & (TW[:, 2] < pal_z + 0.24 * L)
    wf = smooth(m.astype(float), 4)
    hang = 1.0 - (TW[:, 2] - (pal_z + 0.03 * L)) / (0.21 * L)
    P = TW + vn * (0.035 * L * wf)[:, None]
    P[:, 2] = P[:, 2] - 0.055 * L * np.clip(hang, 0, 1) * wf
    P[:, 1] = P[:, 1] - 0.015 * L * wf
    tf = [tuple(t_) for t_ in tris if m[t_[0]] and m[t_[1]] and m[t_[2]]]
    used = sorted(set(v for f_ in tf for v in f_))
    remap = {v: i for i, v in enumerate(used)}
    add_mesh(f"CheekTuft_{s}", P[used],
             [tuple(remap[v] for v in f_) for f_ in tf])
    report[f"cheek_tuft_{s}"] = {"verts": len(used), "faces": len(tf)}

# ---- chin tuft (under-chin mass from the jaw's Chin patch)
JW, _ = world_co(jaw)
chin_w = group_weights(jaw, "Chin")
jm = (chin_w > 0.35) & (JW[:, 1] > 0.10 * L)
jtris = []
for p in jaw.data.polygons:
    idx = list(p.vertices)
    for k in range(1, len(idx) - 1):
        jtris.append((idx[0], idx[k], idx[k + 1]))
jtris = np.array(jtris)
CP = JW.copy()
CP[:, 2] = CP[:, 2] - 0.050 * L * chin_w
CP[:, 1] = CP[:, 1] + 0.010 * L * chin_w
CP[:, 0] = CP[:, 0] * (1.0 - 0.10 * chin_w)
cf = [tuple(t_) for t_ in jtris if jm[t_[0]] and jm[t_[1]] and jm[t_[2]]]
used = sorted(set(v for f_ in cf for v in f_))
remap = {v: i for i, v in enumerate(used)}
add_mesh("ChinTuft", CP[used], [tuple(remap[v] for v in f_) for f_ in cf])
report["chin_tuft"] = {"verts": len(used), "faces": len(cf)}

bpy.ops.wm.save_as_mainfile(filepath=str(CHAR / "work" / "stage7.blend"))
(CHAR / "work" / "stage7.json").write_text(json.dumps(report, indent=1))
print(json.dumps(report, indent=1))
print("STAGE 7 DONE")
