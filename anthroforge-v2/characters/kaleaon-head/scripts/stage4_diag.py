#!/usr/bin/env python3
"""Diagnostic 2: locate cage-vs-cage margin crossings and tongue vs
lower-arcade crossings; measure the same margin test on the v5 base
with this script's margin definition (isolates definition vs build)."""
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, str(Path(__file__).parent))
from kaleaon_io import world_co, group_weights

CHAR = Path("/home/hatch/workspace/anthroforge-v2/characters/kaleaon-head")


def mesh_tris(o, W=None):
    if W is None:
        W, _ = world_co(o)
    tris = []
    for p in o.data.polygons:
        idx = list(p.vertices)
        for k in range(1, len(idx) - 1):
            tris.append((idx[0], idx[k], idx[k + 1]))
    return W, tris


def bvh_of(W, tris):
    return BVHTree.FromPolygons([Vector(v) for v in W], tris,
                                all_triangles=True)


def margin_submesh(objs, name):
    o = objs[name]
    other = objs["Jaw"] if name == "TissueHead" else objs["TissueHead"]
    cage = np.where(group_weights(o, "LipCage") > 0)[0]
    ocage = np.where(group_weights(other, "LipCage") > 0)[0]
    W, _ = world_co(o)
    OW, _ = world_co(other)
    P, OP = W[cage], OW[ocage]
    d = np.sqrt(((P[:, None, :] - OP[None, :, :]) ** 2).sum(-1)).min(axis=1)
    rim = set(int(cage[i]) for i in np.where(d < 0.0005)[0])
    keep = set(int(i) for i in cage)
    tris = []
    for p in o.data.polygons:
        idx = list(p.vertices)
        if all(v in keep for v in idx) and not all(v in rim for v in idx):
            for k in range(1, len(idx) - 1):
                tris.append((idx[0], idx[k], idx[k + 1]))
    return W, tris


def cross_centroids(WA, TA, WB, TB):
    TA = np.array(TA)
    ta = bvh_of(WA, TA.tolist())
    tb = bvh_of(WB, np.array(TB).tolist())
    ov = ta.overlap(tb)
    cents = []
    for a, b in ov:
        cents.append(WA[TA[a]].mean(axis=0))
    return np.array(cents) if cents else np.zeros((0, 3))


for tag, path in (("v5base", "/home/hatch/workspace/anthroforge-v2/base-head-v5/neutral_base_head_v5.blend"),
                  ("stage4", str(CHAR / "work" / "stage4.blend"))):
    bpy.ops.wm.open_mainfile(filepath=path)
    objs = {o.name: o for o in bpy.data.objects if o.type == "MESH"}
    TW, TT = margin_submesh(objs, "TissueHead")
    JW, JT = margin_submesh(objs, "Jaw")
    cc = cross_centroids(TW, TT, JW, JT)
    print(f"== {tag}: cage margin crossings = {len(cc)}")
    if len(cc):
        print("   x range", np.round([cc[:, 0].min(), cc[:, 0].max()], 3),
              "y range", np.round([cc[:, 1].min(), cc[:, 1].max()], 3),
              "z range", np.round([cc[:, 2].min(), cc[:, 2].max()], 3))
        hist, _ = np.histogram(cc[:, 1], bins=6,
                               range=(cc[:, 1].min(), cc[:, 1].max()))
        print("   y histogram (posterior->anterior):", hist)
    # tongue vs lower teeth at rest
    GW, GT = mesh_tris(objs["Tongue"])
    LW, LT = mesh_tris(objs["TeethLower"])
    tc = cross_centroids(GW, GT, LW, LT)
    print(f"   tongue vs TeethLower crossings = {len(tc)}")
    if len(tc):
        print("   x |.| mean", round(float(np.abs(tc[:, 0]).mean()), 3),
              " y range", np.round([tc[:, 1].min(), tc[:, 1].max()], 3),
              " z range", np.round([tc[:, 2].min(), tc[:, 2].max()], 3))
        hist, _ = np.histogram(tc[:, 1], bins=6,
                               range=(tc[:, 1].min(), tc[:, 1].max()))
        print("   y histogram (posterior->anterior):", hist)
        hist, _ = np.histogram(np.abs(tc[:, 0]), bins=4,
                               range=(0, float(np.abs(tc[:, 0]).max())))
        print("   |x| histogram (centre->side):", hist)
print("DIAG2 DONE")
