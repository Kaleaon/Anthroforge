#!/usr/bin/env python3
"""Shared Blender IO helpers for the Kaleaon staged build."""
from collections import defaultdict

import numpy as np


def world_co(o):
    M = np.array(o.matrix_world)
    co = np.empty(len(o.data.vertices) * 3)
    o.data.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    return co @ M[:3, :3].T + M[:3, 3], M


def set_world(o, W, M):
    Minv = np.linalg.inv(M)
    local = W @ Minv[:3, :3].T + Minv[:3, 3]
    o.data.vertices.foreach_set("co", local.ravel())
    o.data.update()


def group_weights(o, name):
    """Per-vertex weight of a vertex group (0 where absent)."""
    w = np.zeros(len(o.data.vertices))
    gi = None
    for g in o.vertex_groups:
        if g.name == name:
            gi = g.index
            break
    if gi is None:
        return w
    for i, v in enumerate(o.data.vertices):
        for gr in v.groups:
            if gr.group == gi:
                w[i] = gr.weight
    return w


def fold_stats(o, cage_idx=None, *, include_worst=False):
    """Adjacent-triangle dihedral normal-dot statistics on a Blender mesh object.

    When ``cage_idx`` is provided, splits non-degenerate interior edge pairs into
    exterior vs cage-zone pairs (plus top-6 ``exterior_worst`` if
    ``include_worst=True``). When ``cage_idx`` is ``None``, returns unsplit
    diagnostic statistics over all non-degenerate interior edge pairs.
    """
    W, _ = world_co(o)
    cage_set = set(int(i) for i in cage_idx) if cage_idx is not None else None
    tris = []
    cage_face = [] if cage_set is not None else None
    for p in o.data.polygons:
        idx = list(p.vertices)
        for k in range(1, len(idx) - 1):
            t = (idx[0], idx[k], idx[k + 1])
            tris.append(t)
            if cage_set is not None:
                cage_face.append(all(v in cage_set for v in t))
    tris = np.array(tris)
    A, B, C = W[tris[:, 0]], W[tris[:, 1]], W[tris[:, 2]]
    n = np.cross(B - A, C - A)
    area2 = np.linalg.norm(n, axis=1)
    degen = int((area2 < 1e-10).sum())
    n = n / np.maximum(area2, 1e-12)[:, None]
    edge_faces = defaultdict(list)
    for fi, t in enumerate(tris):
        for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            edge_faces[(min(a, b), max(a, b))].append(fi)

    if cage_set is None:
        dots, cents = [], []
        for (a, b), fs in edge_faces.items():
            if len(fs) == 2 and area2[fs[0]] > 1e-10 and area2[fs[1]] > 1e-10:
                dots.append(float(n[fs[0]] @ n[fs[1]]))
                cents.append(W[[a, b]].mean(axis=0))
        dots = np.array(dots)
        cents = np.array(cents)
        worst = np.argsort(dots)[:8]
        return {
            "pairs": len(dots),
            "degen_faces": degen,
            "min_dot": float(dots.min()),
            "n_below_0.01": int((dots < 0.01).sum()),
            "n_below_0": int((dots < 0).sum()),
            "n_below_-0.5": int((dots < -0.5).sum()),
            "worst": [
                {"dot": round(float(dots[i]), 4), "at": np.round(cents[i], 3).tolist()}
                for i in worst
            ],
        }

    cage_face = np.array(cage_face)
    ext_dots, cage_dots, ext_worst = [], [], []
    for (a, b), fs in edge_faces.items():
        if len(fs) == 2 and area2[fs[0]] > 1e-10 and area2[fs[1]] > 1e-10:
            dot = float(n[fs[0]] @ n[fs[1]])
            if cage_face[fs[0]] or cage_face[fs[1]]:
                cage_dots.append(dot)
            else:
                ext_dots.append(dot)
                if include_worst and dot < 0.01:
                    ext_worst.append((dot, np.round(W[[a, b]].mean(axis=0), 3).tolist()))
    ext_dots = np.array(ext_dots)
    cage_dots = np.array(cage_dots)
    res = {
        "exterior_pairs": len(ext_dots),
        "exterior_min_dot": float(ext_dots.min()) if len(ext_dots) else None,
        "exterior_below_0.01": int((ext_dots < 0.01).sum()),
        "cage_pairs": len(cage_dots),
        "cage_below_0.01": int((cage_dots < 0.01).sum()),
    }
    if include_worst:
        ext_worst.sort()
        res["exterior_worst"] = ext_worst[:6]
    return res
