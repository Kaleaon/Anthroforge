"""Geodesic-falloff auto-weighting (method B) for the orc bust prototype.

Weights: per bone, seeds = vertices for which that bone's segment is the
nearest AND clearly so. Weight field = exp(-(geodesic dist to seeds / sigma)^2)
via multi-source Dijkstra on the mesh edge graph. Top-4 influences, normalised.
Disconnected components without seeds fall back to Euclidean segment distance.
Anatomical guards: eyes rigid to Head; teeth jaw-seeds only below jaw pivot.
"""
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra, connected_components

W = "/home/hatch/workspace/anthroforge-v2/autoskin-prototype/work"

# 36-bone AnthroForge layout (names/hierarchy from anthroforge_3d_pro_v2.html),
# positions fitted to the bust (Blender coords: x right, y back, z up, face = -y).
BONES = {
    "Root":       ((0, 0.30, -6.70), (0, 0.30, -3.18)),
    "Pelvis":     ((0, 0.30, -3.18), (0, 0.28, -2.50)),
    "Spine1":     ((0, 0.28, -2.50), (0, 0.15, -1.55)),
    "Chest":      ((0, 0.15, -1.55), (0, 0.08, -0.75)),
    "Neck":       ((0, 0.08, -0.75), (0, -0.02, -0.05)),
    "Head":       ((0, -0.02, -0.05), (0, 0.10, 0.80)),
    "Jaw":        ((0, -0.30, -0.35), (0, -1.02, -1.08)),
    "Ear_L":      ((0.80, -0.05, 0.02), (1.62, 0.02, 0.30)),
    "Ear_R":      ((-0.80, -0.05, 0.02), (-1.62, 0.02, 0.30)),
    "Shoulder_L": ((0.42, 0.02, -1.02), (2.85, 0.22, -1.70)),
    "Elbow_L":    ((2.85, 0.22, -1.70), (3.75, 0.35, -2.45)),
    "Wrist_L":    ((3.75, 0.35, -2.45), (4.15, 0.40, -2.95)),
    "Shoulder_R": ((-0.42, 0.02, -1.02), (-2.85, 0.22, -1.70)),
    "Elbow_R":    ((-2.85, 0.22, -1.70), (-3.75, 0.35, -2.45)),
    "Wrist_R":    ((-3.75, 0.35, -2.45), (-4.15, 0.40, -2.95)),
    "Hip_L":      ((0.48, 0.28, -3.15), (0.55, 0.01, -4.41)),
    "Knee_L":     ((0.55, 0.01, -4.41), (0.55, 0.49, -5.53)),
    "Ankle_L":    ((0.55, 0.49, -5.53), (0.55, 0.01, -6.38)),
    "Foot_L":     ((0.55, 0.01, -6.38), (0.55, -0.45, -6.60)),
    "Hip_R":      ((-0.48, 0.28, -3.15), (-0.55, 0.01, -4.41)),
    "Knee_R":     ((-0.55, 0.01, -4.41), (-0.55, 0.49, -5.53)),
    "Ankle_R":    ((-0.55, 0.49, -5.53), (-0.55, 0.01, -6.38)),
    "Foot_R":     ((-0.55, 0.01, -6.38), (-0.55, -0.45, -6.60)),
    "Wing_L1":    ((0.37, 0.60, -1.10), (1.80, 0.87, -0.42)),
    "Wing_L2":    ((1.80, 0.87, -0.42), (3.10, 1.05, -0.10)),
    "Wing_R1":    ((-0.37, 0.60, -1.10), (-1.80, 0.87, -0.42)),
    "Wing_R2":    ((-1.80, 0.87, -0.42), (-3.10, 1.05, -0.10)),
    "Tail_1":     ((0, 0.78, -3.25), (0, 1.80, -3.39)),
    "Tail_2":     ((0, 1.80, -3.39), (0, 2.89, -3.29)),
    "Tail_3":     ((0, 2.89, -3.29), (0, 3.80, -3.05)),
    "GenBase":    ((0, -0.14, -3.45), (0, -0.28, -3.60)),
    "GenScrot":   ((0, -0.28, -3.60), (0, -0.32, -3.80)),
    "Gen01":      ((0, -0.28, -3.60), (0, -0.45, -3.55)),
    "Gen02":      ((0, -0.45, -3.55), (0, -0.62, -3.52)),
    "Gen03":      ((0, -0.62, -3.52), (0, -0.78, -3.50)),
    "Gen04":      ((0, -0.78, -3.50), (0, -0.92, -3.46)),
}
BONE_NAMES = list(BONES.keys())
JAW_PIVOT_Z = -0.35

def seg_dist(P, A, B):
    AB = B - A
    t = np.clip(((P - A) @ AB) / (AB @ AB), 0, 1)
    return np.linalg.norm(P - (A + t[:, None] * AB), axis=1)

def compute_weights(verts, faces, mesh_name):
    n = len(verts)
    segs = {b: (np.array(h, float), np.array(t, float)) for b, (h, t) in BONES.items()}
    # only bones whose segment comes near this mesh
    d_all = {}
    for b, (A, B) in segs.items():
        d = seg_dist(verts, A, B)
        if d.min() < 1.0:
            d_all[b] = d
    bones = list(d_all.keys())
    D = np.stack([d_all[b] for b in bones], axis=1)  # n x nb
    order = np.argsort(D, axis=1)
    d1 = np.take_along_axis(D, order[:, :1], axis=1)[:, 0]
    d2 = np.take_along_axis(D, order[:, 1:2], axis=1)[:, 0] if len(bones) > 1 else np.full(n, 9.9)
    nearest = np.array(bones, dtype=object)[order[:, 0]]

    # edge graph
    E = np.vstack([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]])
    E = np.unique(np.sort(E, axis=1), axis=0)
    wlen = np.linalg.norm(verts[E[:, 0]] - verts[E[:, 1]], axis=1)
    G = csr_matrix((wlen, (E[:, 0], E[:, 1])), shape=(n, n))
    G = G + G.T
    ncomp, labels = connected_components(G, directed=False)

    sigma = {b: max(0.16, 0.38 * np.linalg.norm(segs[b][1] - segs[b][0])) for b in bones}
    Wm = np.zeros((n, len(bones)))
    for bi, b in enumerate(bones):
        seeds = np.where((nearest == b) & (d1 < 0.55 * d2 + 0.04))[0]
        if mesh_name.startswith("Teeth") and b == "Jaw":
            seeds = seeds[verts[seeds][:, 2] < JAW_PIVOT_Z - 0.03]
        if mesh_name.startswith("Teeth") and b == "Head":
            seeds = seeds[verts[seeds][:, 2] > JAW_PIVOT_Z - 0.10]
        if len(seeds) == 0:
            continue
        # multi-source Dijkstra via a virtual super-source node (fast):
        # node n connects to every seed with a 0-length edge, so distance
        # from node n == geodesic distance to the nearest seed.
        from scipy.sparse import bmat
        col = csr_matrix((np.zeros(len(seeds)),
                          (seeds.astype(np.int32), np.zeros(len(seeds), dtype=np.int32))),
                         shape=(n, 1))
        Gfull = bmat([[G, col], [col.T, None]], format="csr")
        gd = dijkstra(Gfull, indices=n)[:n]
        # components with no seed for this bone: Euclidean fallback
        seed_comp = set(labels[seeds].tolist())
        missing = ~np.isin(labels, list(seed_comp))
        gd[missing] = D[missing, bi]
        Wm[:, bi] = np.exp(-(gd / sigma[b]) ** 2)
    if mesh_name.startswith("Eyes"):
        Wm[:] = 0.0
        Wm[:, bones.index("Head")] = 1.0
    # top-4 + normalise
    idx = np.argsort(-Wm, axis=1)[:, :4]
    w4 = np.take_along_axis(Wm, idx, axis=1)
    s = w4.sum(axis=1, keepdims=True)
    s[s == 0] = 1.0
    w4 = w4 / s
    bone_idx = np.array([BONE_NAMES.index(bones[i]) for i in range(len(bones))])
    return bone_idx[idx], w4, bones

def main():
    d = np.load(f"{W}/bust_meshes.npz")
    out = {}
    for k in d.keys():
        if not k.endswith("_v"):
            continue
        name = k[:-2]
        verts, faces = d[k], d[name + "_f"]
        bi, w4, bones = compute_weights(verts, faces, name)
        out[name + "_bi"] = bi
        out[name + "_w"] = w4
        counts = {}
        top = bi[:, 0]
        for j, b in enumerate(BONE_NAMES):
            c = int((w4[top == j, 0] > 0).sum())
            if c: counts[b] = c
        print(f"{name}: bones used={bones}")
        print(f"   dominant-vertex counts: {counts}")
        if name.startswith("Teeth"):
            jaw_bone = BONE_NAMES.index("Jaw")
            wj = np.where(bi == jaw_bone, w4, 0).max(axis=1)
            upper = verts[:, 2] > -0.80
            print(f"   TEETH check: upper verts jaw-weight>0.5: {(wj[upper] > 0.5).sum()}/{upper.sum()}; "
                  f"lower verts jaw-weight>0.5: {(wj[~upper] > 0.5).sum()}/{(~upper).sum()}")
    np.savez_compressed(f"{W}/geo_weights.npz", **out)
    print("saved geo_weights.npz")

if __name__ == "__main__":
    main()
