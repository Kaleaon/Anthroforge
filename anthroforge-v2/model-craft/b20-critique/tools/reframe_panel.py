#!/usr/bin/env python3
"""Re-frame one model's annotation panel in its anatomical (PCA) frame.
For GLBs that store the character lying (Sketchfab exports): PC1 = body
axis (head end toward -Z by that pipeline's convention). Stdlib+numpy+
matplotlib; reuses the QA gauntlet's GLB reader for world triangles."""
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection

sys.path.insert(0, "/home/hatch/workspace/anthroforge-v2/qa-gauntlet")
from validate_glb import parse_glb, read_accessor  # noqa: E402


def quat_mat(q):
    x, y, z, w = q
    return np.array([
        [1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
        [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
        [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]], dtype=np.float64)


def node_local(n):
    if "matrix" in n:
        return np.array(n["matrix"], dtype=np.float64).reshape(4, 4).T
    M = np.eye(4)
    M[:3, :3] = quat_mat(n.get("rotation", [0, 0, 0, 1])) @ np.diag(n.get("scale", [1, 1, 1]))
    M[:3, 3] = n.get("translation", [0, 0, 0])
    return M


def world_tris(path):
    g, buf = parse_glb(path)
    nodes = g.get("nodes", [])
    W = [None] * len(nodes)

    def walk(i, parent):
        W[i] = parent @ node_local(nodes[i])
        for c in nodes[i].get("children", []):
            walk(c, W[i])
    for r in g["scenes"][g.get("scene", 0)]["nodes"]:
        walk(r, np.eye(4))
    out = []
    for ni, node in enumerate(nodes):
        if "mesh" not in node:
            continue
        M = W[ni]
        for prim in g["meshes"][node["mesh"]]["primitives"]:
            pos = read_accessor(g, buf, prim["attributes"]["POSITION"]).astype(np.float64)
            idx = (read_accessor(g, buf, prim["indices"]).reshape(-1).astype(np.int64)
                   if "indices" in prim else np.arange(len(pos)))
            pw = (M[:3, :3] @ pos.T).T + M[:3, 3]
            out.append(pw[idx.reshape(-1, 3)])
    return np.concatenate(out)


def main(path, out_png, title):
    T = world_tris(path)
    V = T.reshape(-1, 3)
    c = V.mean(axis=0)
    _, _, vt = np.linalg.svd(V - c, full_matrices=False)
    up = vt[0]
    if up @ np.array([0, 0, -1.0]) < 0:
        up = -up
    lat = vt[1]
    dep = np.cross(up, lat)
    P = np.stack([V @ lat, V @ up, V @ dep], axis=1).reshape(-1, 3, 3)
    # dominant-cluster crop: composites may instance the character twice
    cen = P[:, :, 1].mean(axis=1)
    hist, edges = np.histogram(cen, bins=100)
    occ = hist > 0
    best, run, start = (0, 0), 0, 0
    for i, o in enumerate(occ):
        if o:
            if run == 0: start = i
            run += 1
            if run > best[1] - best[0]: best = (start, i)
        else:
            run = 0
    lo = edges[max(best[0] - 1, 0)]; hi = edges[min(best[1] + 1, 99)]
    keep = (cen >= lo) & (cen <= hi)
    if keep.mean() < 0.98:
        print(f"cluster crop: kept {keep.mean()*100:.0f}% of tris")
        P = P[keep]
    # orient: head end = terminal 10% with more surface area (ears/head vs feet)
    cu = P[:, :, 1].mean(axis=1)
    a = np.linalg.norm(np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]), axis=1)
    span = cu.max() - cu.min()
    top = a[cu > cu.max() - 0.1 * span].sum(); bot = a[cu < cu.min() + 0.1 * span].sum()
    if bot > top:
        P[:, :, 1] *= -1
        print("flipped up: head end was at the bottom")
    front, side = P[:, :, [0, 1]], P[:, :, [2, 1]]
    order = np.argsort(P[:, :, 2].mean(axis=1))
    n = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0])
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    L = np.array([0.3, 0.5, 0.8]); L /= np.linalg.norm(L)
    d = np.abs(n @ L)
    cols = np.stack([d * 0.85 + 0.1] * 3, axis=1)
    black = np.zeros((len(front), 3))
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 4.6))
    for ax, polys, cc, t in [
            (axes[0], front, black, "silhouette front"),
            (axes[1], side, black, "silhouette side"),
            (axes[2], front, cols, "shaded front")]:
        ax.add_collection(PolyCollection(polys[order], facecolors=cc[order], edgecolors="none"))
        ax.autoscale_view(); ax.set_aspect("equal")
        ax.set_title(t, fontsize=9); ax.tick_params(labelsize=7)
    fig.suptitle(title, fontsize=8.5)
    fig.tight_layout()
    fig.savefig(out_png, dpi=110)
    print("wrote", out_png,
          "| up-extent", round(float((V @ up).max() - (V @ up).min()), 3),
          "| lat-extent", round(float((V @ lat).max() - (V @ lat).min()), 3))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
