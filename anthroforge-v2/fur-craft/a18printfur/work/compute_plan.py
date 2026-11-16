#!/usr/bin/env python3
"""A18 fur plan computation: direction field, pile zones, colour zones, pieces.
Base: neutral base head v3 (TissueHead/Jaw/Ear_L/Ear_R/NoseLeather).
Frame: face +Y, up +Z, L (nose->occiput) = 1.0 unit. Plan scale: L = 300 mm.
"""
import json, numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra

W = "/home/hatch/workspace/anthroforge-v2/fur-craft/a18printfur/work/"
G = json.load(open("/home/hatch/workspace/anthroforge-v2/base-head-v3/neutral_base_head_v3.groups.json"))
Z = np.load(W + "head_geom.npz", allow_pickle=True)
SCALE_MM = 300.0  # 1 model unit = 300 mm at fursuit plan scale

def load(name):
    pos = Z[f"{name}_pos"]; faces = [list(f) for f in Z[f"{name}_faces"]]
    tris = []
    for f in faces:  # fan-triangulate
        for k in range(1, len(f) - 1): tris.append([f[0], f[k], f[k + 1]])
    return pos, np.array(tris)

def vnormals(pos, tris):
    n = np.zeros_like(pos)
    for a, b, c in tris:
        cr = np.cross(pos[b] - pos[a], pos[c] - pos[a])
        n[a] += cr; n[b] += cr; n[c] += cr
    l = np.linalg.norm(n, axis=1, keepdims=True); l[l == 0] = 1
    return n / l

def adjacency(pos, tris):
    nv = len(pos); rows, cols, dat = [], [], []
    for a, b, c in tris:
        for i, j in ((a, b), (b, c), (c, a)):
            w = np.linalg.norm(pos[i] - pos[j])
            rows += [i, j]; cols += [j, i]; dat += [w, w]
    return csr_matrix((dat, (rows, cols)), shape=(nv, nv))

def flow_field(pos, tris, nrm, seeds, bias=np.array([0.0, -1.0, -0.45]), bias_w=0.25):
    """Fur direction = uphill of geodesic distance from seed set (fur grows
    away from the face / ear base / chin), tangent-projected, smoothed."""
    A = adjacency(pos, tris)
    phi = dijkstra(A, indices=list(seeds))
    phi = phi.min(axis=0) if phi.ndim == 2 else phi
    nbrs = [[] for _ in range(len(pos))]
    coo = A.tocoo()
    for i, j in zip(coo.row, coo.col): nbrs[i].append(j)
    d = np.zeros_like(pos)
    for i in range(len(pos)):
        acc = np.zeros(3)
        for j in nbrs[i]:
            if phi[j] > phi[i] + 1e-9:
                v = pos[j] - pos[i]; acc += (phi[j] - phi[i]) * v / (np.linalg.norm(v) + 1e-12)
        d[i] = acc
    # blend global back-down bias, project to tangent
    for i in range(len(pos)):
        v = d[i] + bias_w * bias * (np.linalg.norm(d[i]) + 0.05)
        v = v - np.dot(v, nrm[i]) * nrm[i]
        l = np.linalg.norm(v); d[i] = v / l if l > 1e-9 else np.array([0.0, -1.0, 0.0])
    for _ in range(3):  # smooth
        nd = d.copy()
        for i in range(len(pos)):
            if nbrs[i]:
                m = d[nbrs[i]].mean(axis=0)
                v = d[i] + 0.6 * m; v = v - np.dot(v, nrm[i]) * nrm[i]
                l = np.linalg.norm(v); nd[i] = v / l if l > 1e-9 else d[i]
        d = nd
    return d, phi

def smooth_labels(labels, tris, nv, passes=2, codes=None):
    nbrs = [set() for _ in range(nv)]
    for a, b, c in tris:
        nbrs[a] |= {b, c}; nbrs[b] |= {a, c}; nbrs[c] |= {a, b}
    lab = labels.copy()
    for _ in range(passes):
        new = lab.copy()
        for i in range(nv):
            if not nbrs[i]: continue
            vals, cnts = np.unique(lab[list(nbrs[i])], return_counts=True)
            best = vals[np.argmax(cnts)]
            if codes is None or best in codes: new[i] = best
        lab = new
    return lab

def components(labels, tris, nv, want):
    nbrs = [set() for _ in range(nv)]
    for a, b, c in tris:
        nbrs[a] |= {b, c}; nbrs[b] |= {a, c}; nbrs[c] |= {a, b}
    seen = np.zeros(nv, bool); comps = []
    for s in range(nv):
        if seen[s] or labels[s] != want: continue
        stack = [s]; seen[s] = True; comp = []
        while stack:
            i = stack.pop(); comp.append(i)
            for j in nbrs[i]:
                if not seen[j] and labels[j] == want: seen[j] = True; stack.append(j)
        comps.append(comp)
    return comps

out = {}
diag = {}

# ---------------- TissueHead ----------------
pos, tris = load("TissueHead"); nrm = vnormals(pos, tris)
tg = G["TissueHead"]
S = {k: set(v) for k, v in tg.items()}
nose_y = pos[:, 1].max()
eye_z = np.mean(pos[list(S["EyeSocketL"] | S["EyeSocketR"]), 2])
palate_z = eye_z - 0.172  # OrbitHeight 0.172 L above palatal line (v3 measured)
hinge_y = -0.2167
diag.update(nose_y=float(nose_y), eye_z=float(eye_z), palate_z=float(palate_z))
seeds = sorted(S["MuzzleTip"] | {i for i in S["MuzzleBridge"] if pos[i, 1] > nose_y - 0.10})
d, phi = flow_field(pos, tris, nrm, seeds)
nv = len(pos)
pile = np.full(nv, 3, dtype=int); colour = np.full(nv, 1, dtype=int)
for i in range(nv):
    x, y, z = pos[i]
    # ---- colour ----
    if i in S["MuzzleTip"]: colour[i] = 2
    elif i in S["Muzzle"]:
        # pale = chin/mouth zone + nose-front lower (z-plane alone paints the whole
        # deep muzzle block; cougar-style pale stays low and front)
        colour[i] = 2 if (z < -0.14 or (y > 0.38 and z < -0.05)) else 1
    elif i in S["CheekL"] or i in S["CheekR"]:
        colour[i] = 2 if (z < -0.16 and y > -0.02) else 1  # small jaw-line front blush
    # ---- pile (priority order: specific regions before the big overlapping
    # Brow/EyeSocket groups, which blanket the forehead) ----
    if i in S["MuzzleTip"]: pile[i] = 1
    elif i in S["MuzzleBridge"] and y > 0.30: pile[i] = 1 if abs(x) < 0.10 else 2
    elif i in S["CheekL"] or i in S["CheekR"]:
        pile[i] = 4 if (z < -0.10 or y < -0.02) else 3  # ruff: lower + posterior cheek
    elif i in S["Cranium"]:
        pile[i] = 4 if y < -0.25 else 3  # occiput/neck ruff; dome/sides medium
    elif i in S["Muzzle"]: pile[i] = 2
    elif i in S["EyeSocketL"] or i in S["EyeSocketR"]: pile[i] = 2
    elif i in S["BrowL"] or i in S["BrowR"]: pile[i] = 2
pile = smooth_labels(pile, tris, nv, 2)
colour = smooth_labels(colour, tris, nv, 1)
out["TissueHead"] = dict(pos=pos, tris=tris, nrm=nrm, flow=d, pile=pile, colour=colour)

# ---------------- Jaw ----------------
pos, tris = load("Jaw"); nrm = vnormals(pos, tris)
jg = G["Jaw"]; chin = set(jg["Chin"])
seeds = sorted(i for i in chin if pos[i, 1] > np.percentile(pos[list(chin), 1], 80))
d, _ = flow_field(pos, tris, nrm, seeds, bias=np.array([0.0, -1.0, -0.7]), bias_w=0.3)
nv = len(pos)
# world frame: underside throat fan (z < -0.37) = long; front/chin (y > 0.28) = short; else medium
pile = np.full(nv, 3, dtype=int)
pile[pos[:, 1] > 0.28] = 2
pile[pos[:, 2] < -0.37] = 4
pile = smooth_labels(pile, tris, nv, 2)
colour = np.full(nv, 2, dtype=int)  # cream jaw/throat
out["Jaw"] = dict(pos=pos, tris=tris, nrm=nrm, flow=d, pile=pile, colour=colour)

# ---------------- Ears ----------------
for side in ("Ear_L", "Ear_R"):
    pos, tris = load(side); nrm = vnormals(pos, tris)
    eg = G[side]; base = set(eg[f"EarBase_{side[-1]}"]); tip = set(eg[f"EarTip_{side[-1]}"])
    d, _ = flow_field(pos, tris, nrm, sorted(base), bias=np.array([0.0, -0.2, 1.0]), bias_w=0.2)
    nv = len(pos)
    inner = nrm[:, 1] > 0.15  # faces forward (+Y) = inner ear surface
    pile = np.where(inner, 1, 3).astype(int)
    pile[list(tip)] = np.where(inner[list(tip)], 1, 3)
    colour = np.where(inner, 4, 3).astype(int)
    out[side] = dict(pos=pos, tris=tris, nrm=nrm, flow=d, pile=pile, colour=colour)

# ---------------- NoseLeather (no fur) ----------------
pos, tris = load("NoseLeather"); nrm = vnormals(pos, tris)
nv = len(pos)
out["NoseLeather"] = dict(pos=pos, tris=tris, nrm=nrm,
                          flow=np.zeros_like(pos), pile=np.zeros(nv, int), colour=np.zeros(nv, int))

np.savez(W + "plan_data.npz", **{f"{k}_{kk}": vv for k, v in out.items() for kk, vv in v.items()})
print("diag:", json.dumps(diag, indent=1))
for k, v in out.items():
    pu, pc = np.unique(v["pile"], return_counts=True), np.unique(v["colour"], return_counts=True)
    print(k, "pile", dict(zip(pu[0].tolist(), pu[1].tolist())), "colour", dict(zip(pc[0].tolist(), pc[1].tolist())))
