"""mask_tools.py — region-mask construction for AnthroForge slider authoring.

A slider's *region mask* is a per-vertex weight field w in [0,1] over a base
mesh. Masks are how a semantic slider ("brow projection", "belly") knows
which vertices it owns. This module builds masks from:

  * landmark vertex sets  (annotator picks, stored once per base)
  * geodesic falloff      (Dijkstra over the edge graph — the standard
                           graph approximation of true surface geodesics)
  * soft partitions       (L/R splits and anatomical bands whose weights
                           sum to exactly 1 per vertex — the basis of
                           slider decomposition, see decompose.py)

Mesh IO covers the two formats the lab works with:
  * learned/*.npz  (keys: <name>_vertices / <name>_triangles [/ <name>_delta])
  * .glb           (pure-python reader; positions + indices per named mesh)

House convention (verified against base-head groups.json): +x = left.
Skyrim-frame bases: z = up, x = lateral, y = forward, units = Skyrim units
(1 unit = 0.01428 m). glTF-frame bases: y = up, z = -forward, units = metres
(head length L = 1.0 on the neutral base head).

Run `python3 mask_tools.py demo` for the self-check used in the README.
"""
import json
import struct
import sys

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra

SKYRIM_UNIT_M = 0.01428  # [L] MAKEHUMAN_OMNIVERSAL.md §6.1


# --------------------------------------------------------------------------
# Mesh IO
# --------------------------------------------------------------------------

def load_npz_mesh(path, key="body"):
    """Load a learned-format npz: <key>_vertices, <key>_triangles, optional
    <key>_delta. Returns (V float64 [n,3], F int64 [m,3], delta|None)."""
    d = np.load(path, allow_pickle=True)
    V = d[key + "_vertices"].astype(np.float64)
    F = d[key + "_triangles"].astype(np.int64)
    delta = d[key + "_delta"].astype(np.float64) if key + "_delta" in d.files else None
    return V, F, delta


def read_glb(path):
    """Minimal glTF-binary reader (positions + indices only).

    Returns {mesh_name: (V float64 [n,3], F int64 [m,3])} keyed by NODE name
    when present (nodes name the logical part: Head, Jaw, ...), else mesh name.
    """
    raw = open(path, "rb").read()
    if raw[:4] != b"glTF":
        raise ValueError("not a GLB: %s" % path)
    jlen, = struct.unpack_from("<I", raw, 12)
    js = json.loads(raw[20:20 + jlen])
    off = 20 + jlen
    blen, = struct.unpack_from("<I", raw, off)
    bin_ = raw[off + 8:off + 8 + blen]

    def accessor(ai):
        a = js["accessors"][ai]
        bv = js["bufferViews"][a["bufferView"]]
        o = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
        n = a["count"]
        ct, ty = a["componentType"], a["type"]
        if ty == "VEC3" and ct == 5126:
            return np.frombuffer(bin_, "<f4", n * 3, o).reshape(n, 3).astype(np.float64)
        if ty == "SCALAR" and ct == 5125:
            return np.frombuffer(bin_, "<u4", n, o).astype(np.int64)
        if ty == "SCALAR" and ct == 5123:
            return np.frombuffer(bin_, "<u2", n, o).astype(np.int64)
        raise ValueError("unsupported accessor %s/%s" % (ty, ct))

    node_mesh = {}
    for node in js.get("nodes", []):
        if "mesh" in node and node.get("name"):
            node_mesh[node["mesh"]] = node["name"]
    out = {}
    for mi, m in enumerate(js["meshes"]):
        pr = m["primitives"][0]
        V = accessor(pr["attributes"]["POSITION"])
        F = accessor(pr["indices"]).reshape(-1, 3)
        out[node_mesh.get(mi, m.get("name", "mesh%d" % mi))] = (V, F)
    return out


# --------------------------------------------------------------------------
# Graph / geodesic machinery
# --------------------------------------------------------------------------

def edge_graph(V, F):
    """Weighted undirected edge graph (CSR) with euclidean edge lengths."""
    e = np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
    e = np.unique(np.sort(e, axis=1), axis=0)
    w = np.linalg.norm(V[e[:, 0]] - V[e[:, 1]], axis=1)
    n = len(V)
    g = csr_matrix((w, (e[:, 0], e[:, 1])), shape=(n, n))
    return g + g.T


def geodesic_distances(V, F, seeds):
    """Multi-source geodesic distance (graph approximation) from seed verts.
    scipy returns one distance row per source index — take the min."""
    g = edge_graph(V, F)
    d = dijkstra(g, indices=np.asarray(seeds, dtype=np.int64))
    return d.min(axis=0) if d.ndim == 2 else d


def smoothstep(x):
    """C1 smoothstep of clipped x in [0,1]."""
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)


def falloff_mask(dist, r_plateau, r_fall):
    """Weight 1 inside r_plateau, smoothstep down to 0 at r_fall."""
    if r_fall <= r_plateau:
        raise ValueError("r_fall must exceed r_plateau")
    w = np.ones_like(dist)
    mid = (dist > r_plateau) & (dist < r_fall)
    w[mid] = 1.0 - smoothstep((dist[mid] - r_plateau) / (r_fall - r_plateau))
    w[dist >= r_fall] = 0.0
    return w


def mask_from_landmarks(V, F, seeds, r_plateau, r_fall):
    """Geodesic-falloff mask around a landmark vertex set."""
    d = geodesic_distances(V, F, seeds)
    return falloff_mask(d, r_plateau, r_fall), d


def laplacian_smooth_mask(V, F, mask, iterations=3, lam=0.5):
    """Graph-Laplacian smoothing — cleans up hand-painted masks.
    Boundary vertices (mask exactly 0 or 1 far from the front) drift least;
    this is a cleanup pass, not a mask generator."""
    g = edge_graph(V, F)
    deg = np.asarray(g.sum(axis=1)).ravel()
    deg[deg == 0] = 1.0
    m = mask.astype(np.float64).copy()
    for _ in range(iterations):
        avg = g.dot(m) / deg
        m = m + lam * (avg - m)
    return np.clip(m, 0.0, 1.0)


# --------------------------------------------------------------------------
# Soft partitions (weights sum to 1 per vertex — decomposition-safe)
# --------------------------------------------------------------------------

def lr_partition(coord, centre=0.0, halfwidth=0.05):
    """Soft left/right partition of unity along one axis.
    Returns (w_neg, w_pos) with w_neg + w_pos == 1 everywhere.
    House rule: the + side is labelled 'left' (base-head groups put
    BrowL at +x)."""
    t = smoothstep((coord - (centre - halfwidth)) / (2.0 * halfwidth))
    return 1.0 - t, t


def band_partition(values, cuts, width):
    """Partition of unity into len(cuts)+1 bands along a scalar field
    (e.g. height z). Band i weight = s_i - s_{i+1} of cumulative smoothsteps,
    so the weights telescope to exactly 1 per vertex."""
    s = [smoothstep((values - c) / width) for c in cuts]  # fraction ABOVE cut i
    bands = [1.0 - s[0]]                                  # below first cut
    for i in range(len(s) - 1):
        bands.append(s[i] - s[i + 1])                     # between cuts
    bands.append(s[-1])                                   # above last cut
    return bands


# --------------------------------------------------------------------------
# QA helpers shared by author_slider.py / decompose.py
# --------------------------------------------------------------------------

def face_normals(V, F):
    n = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    ln = np.linalg.norm(n, axis=1)
    ln[ln == 0] = 1.0
    return n / ln[:, None], ln  # unit normals, 2x areas


def fold_count(V, F, Vd):
    """Fold-over = face whose deformed normal opposes its bind normal
    (dot < 0). Returns (total_folds, folds_among_faces_touching_moved_verts,
    moved_vertex_mask)."""
    n0, _ = face_normals(V, F)
    n1, _ = face_normals(Vd, F)
    flips = np.einsum("ij,ij->i", n0, n1) < 0
    moved = np.linalg.norm(Vd - V, axis=1) > 1e-9
    touched = moved[F].any(axis=1)
    return int(flips.sum()), int((flips & touched).sum()), moved


def signed_volume(V, F):
    """Divergence-theorem volume. Meaningful for closed meshes; on open
    meshes (neck-cut heads) treat DELTAS as indicative only."""
    return float(np.einsum("ij,ij->i", V[F[:, 0]],
                            np.cross(V[F[:, 1]], V[F[:, 2]])).sum() / 6.0)


def mask_stats(mask):
    return {
        "verts_full": int((mask >= 0.999).sum()),
        "verts_partial": int(((mask > 0.001) & (mask < 0.999)).sum()),
        "verts_any": int((mask > 0.001).sum()),
        "weight_sum": float(mask.sum()),
    }


# --------------------------------------------------------------------------
# Demo / self-check
# --------------------------------------------------------------------------

def demo():
    base = "~/workspace/anthroforge-v2/base-head/neutral_base_head.glb"
    import os
    meshes = read_glb(os.path.expanduser(base))
    V, F = meshes["Head"]
    groups = json.load(open(os.path.expanduser(
        "~/workspace/anthroforge-v2/base-head/neutral_base_head.groups.json")))["Head"]
    seeds = np.array(groups["BrowL"] + groups["BrowR"])
    mask, dist = mask_from_landmarks(V, F, seeds, r_plateau=0.025, r_fall=0.14)
    print("head verts:", len(V), " brow seeds:", len(seeds))
    print("brow mask:", mask_stats(mask))
    # partition sanity on the same mesh (x = lateral, +x = left)
    wn, wp = lr_partition(V[:, 0], centre=0.0, halfwidth=0.02)
    print("lr partition max |sum-1|:", float(np.abs(wn + wp - 1).max()))
    bands = band_partition(V[:, 2], cuts=[-0.25, 0.1], width=0.08)
    tot = sum(bands)
    print("band partition max |sum-1|:", float(np.abs(tot - 1).max()),
          " band weight sums:", [round(float(b.sum()), 1) for b in bands])


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo()
    else:
        print(__doc__)
