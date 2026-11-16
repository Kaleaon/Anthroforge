"""Final metrics v3 (vectorised): signed point-to-triangle distance.
Candidates: triangles adjacent to 8 nearest vertices, padded to a fixed width.
Closest point on a triangle = min over face projection, 3 edges, 3 vertices."""
import json
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree

OUT = Path.home() / "workspace/anthroforge-v2/model-craft/b15-clothing"
d = np.load(OUT/"scripts/garment_data.npz")
base, faces = d["base"], d["faces"]
g_idx, gq = d["g_idx"], d["g_faces"]
g_faces = np.vstack([gq[:, [0,1,2]], gq[:, [0,2,3]]])  # fan-triangulate quads
BODY_END = 13380
body_mask = np.zeros(len(base), bool); body_mask[:BODY_END] = True
tris = faces[np.all(faces < BODY_END, axis=1)]
src = np.zeros(len(base), bool); src[g_idx] = True
sample_faces = tris[np.all(src[tris], axis=1)]
PAD = 72

def cand_array(nv, F, V, P):
    adj = [[] for _ in range(nv)]
    for ti, f in enumerate(F):
        for v in f:
            adj[v].append(ti)
    tree = cKDTree(V)
    _, nn = tree.query(P, k=8)
    ctree = cKDTree(V[F].mean(axis=1))
    _, nface = ctree.query(P)
    C = np.zeros((len(P), PAD), dtype=int)
    for i, row in enumerate(nn):
        s = sorted(set(t for v in row for t in adj[v]))[:PAD]
        if not s:
            s = [int(nface[i])]
        C[i, :len(s)] = s
        if len(s) < PAD:
            C[i, len(s):] = s[0]
    return C

def seg_closest(P, A, B):
    ab = B - A
    t = np.einsum("ijk,ijk->ij", P - A, ab) / np.maximum(np.einsum("ijk,ijk->ij", ab, ab), 1e-14)
    t = np.clip(t, 0, 1)
    return A + ab * t[..., None]

def signed_dist(P, V, F):
    C = cand_array(len(V), F, V, P)              # (nP, PAD)
    A = V[F[C, 0]]; B = V[F[C, 1]]; Cc = V[F[C, 2]]  # (nP, PAD, 3)
    Pv = P[:, None, :]
    ab, ac = B - A, Cc - A
    ap = Pv - A
    d1 = np.einsum("ijk,ijk->ij", ap, ab); d2 = np.einsum("ijk,ijk->ij", ap, ac)
    d00 = np.einsum("ijk,ijk->ij", ab, ab); d01 = np.einsum("ijk,ijk->ij", ab, ac); d11 = np.einsum("ijk,ijk->ij", ac, ac)
    den = np.maximum(d00 * d11 - d01 * d01, 1e-14)
    vv = (d11 * d1 - d01 * d2) / den; ww = (d00 * d2 - d01 * d1) / den
    inside = (vv >= 0) & (ww >= 0) & (vv + ww <= 1)
    q_face = A + ab * np.clip(vv, 0, 1)[..., None] + ac * np.clip(ww, 0, 1)[..., None]
    cands = [np.where(inside[..., None], q_face, np.inf),
             seg_closest(Pv, A, B), seg_closest(Pv, B, Cc), seg_closest(Pv, Cc, A), A, B, Cc]
    best = np.full(P.shape[:1] + C.shape[1:], np.inf); bestq = None
    for q in cands:
        dist = np.linalg.norm(Pv - q, axis=2)
        upd = dist < best
        best = np.where(upd, dist, best)
        bestq = q if bestq is None else np.where(upd[..., None], q, bestq)
    N = np.cross(ab, ac); N /= np.maximum(np.linalg.norm(N, axis=2, keepdims=True), 1e-14)
    j = np.argmin(best, axis=1)
    diff = P - bestq[np.arange(len(P)), j]
    sgn = np.sign(np.einsum("ij,ij->i", diff, N[np.arange(len(P)), j]))
    return best[np.arange(len(P)), j] * np.where(sgn == 0, 1, sgn)

results = {}
for state in ["neutral", "strongman", "fat_v51", "gachidebu"]:
    delta = d[f"delta_{state}"]
    deformed = base + delta
    samples = np.concatenate([deformed[src], deformed[sample_faces].mean(axis=1)])
    entry = {}
    variants = {"A": d[f"{state}_A"], "B": d[f"{state}_B"]}
    cpath = OUT/f"scripts/garmentC_{state}.npy"
    if cpath.exists():
        variants["C"] = np.load(cpath)
    for m, gpos in variants.items():
        gin = signed_dist(gpos, deformed, tris)
        bout = signed_dist(samples, gpos, g_faces)
        entry[m] = {
            "garment_verts_penetrating_pct": round(float((gin < 0).mean()*100), 2),
            "garment_max_penetration_mm": round(float(-gin.min()*1000), 2) if (gin < 0).any() else 0.0,
            "garment_mean_clearance_mm": round(float(gin.mean()*1000), 2),
            "body_samples_poking_pct": round(float((bout > 0).mean()*100), 2),
            "body_max_poke_mm": round(float(bout.max()*1000), 2) if (bout > 0).any() else 0.0,
        }
    results[state] = entry
    print(state, json.dumps(entry), flush=True)

prev = json.loads((OUT/"metrics.json").read_text())
prev["final_point_to_triangle"] = results
(OUT/"metrics.json").write_text(json.dumps(prev, indent=1))
print("written")
