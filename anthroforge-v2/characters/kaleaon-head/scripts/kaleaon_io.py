#!/usr/bin/env python3
"""Shared Blender IO helpers for the Kaleaon staged build."""
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
