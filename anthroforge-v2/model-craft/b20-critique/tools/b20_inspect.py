#!/usr/bin/env python3
"""B20 deep inspector — numeric evidence for CRITIQUE.md reviews.
Stdlib + numpy; reuses the QA gauntlet's GLB reader. Per model reports:
topology proxies (non-manifold/boundary/winding edges, valence poles —
GLB is pre-triangulated, so these are flow *proxies*), UV presence /
coverage / collapsed-UV fraction / per-shell density spread, skin-weight
quality (sums, unweighted %, max influences), morph target count +
accessor-bound displacement, skeleton landmarks + extent, animations.

Usage: b20_inspect.py FILE.glb [FILE.glb ...]  -> prints JSON per file.
NOTE: do not name this file inspect.py (shadows the stdlib module)."""
import json, sys
import numpy as np
sys.path.insert(0, "/home/hatch/workspace/anthroforge-v2/qa-gauntlet")
from validate_glb import parse_glb, read_accessor


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


def world_matrices(g):
    nodes = g.get("nodes", [])
    W = [None] * len(nodes)

    def walk(i, parent):
        W[i] = parent @ node_local(nodes[i])
        for c in nodes[i].get("children", []):
            walk(c, W[i])
    for r in g["scenes"][g.get("scene", 0)]["nodes"]:
        walk(r, np.eye(4))
    return W


def inspect(path):
    g, buf = parse_glb(path)
    W = world_matrices(g)
    topo = {"nonmanifold": 0, "boundary": 0, "bad_winding": 0}
    vals, uvs, wstats, morphs = [], [], [], []
    for ni, node in enumerate(g.get("nodes", [])):
        if "mesh" not in node:
            continue
        M = W[ni]
        for prim in g["meshes"][node["mesh"]]["primitives"]:
            pos = read_accessor(g, buf, prim["attributes"]["POSITION"]).astype(np.float64)
            idx = (read_accessor(g, buf, prim["indices"]).reshape(-1).astype(np.int64)
                   if "indices" in prim else np.arange(len(pos)))
            tris = idx.reshape(-1, 3)
            pw = (M[:3, :3] @ pos.T).T + M[:3, 3]
            edges = {}
            for a, b, c in tris:
                for e in ((a, b), (b, c), (c, a)):
                    edges.setdefault((min(e), max(e)), []).append(e)
            for dirs in edges.values():
                if len(dirs) > 2: topo["nonmanifold"] += 1
                elif len(dirs) == 1: topo["boundary"] += 1
                elif dirs[0] == dirs[1]: topo["bad_winding"] += 1
            val = np.zeros(len(pos), dtype=int)
            for a, b in edges: val[a] += 1; val[b] += 1
            vals.append(val)
            if "TEXCOORD_0" in prim["attributes"]:
                uv = read_accessor(g, buf, prim["attributes"]["TEXCOORD_0"]).astype(np.float64)
                uvt = uv[tris]
                a2 = 0.5 * np.abs((uvt[:, 1, 0]-uvt[:, 0, 0])*(uvt[:, 2, 1]-uvt[:, 0, 1])
                                  - (uvt[:, 2, 0]-uvt[:, 0, 0])*(uvt[:, 1, 1]-uvt[:, 0, 1]))
                p3 = pw[tris]
                a3 = 0.5 * np.linalg.norm(np.cross(p3[:, 1]-p3[:, 0], p3[:, 2]-p3[:, 0]), axis=1)
                uvs.append({"extent": [round(float(x), 2) for x in (uv.max(0)-uv.min(0))],
                            "zero_area_pct": round(float((a2 < 1e-10).mean())*100, 2),
                            "median_uv_per_m2": round(float(np.median(a2/np.maximum(a3, 1e-12))), 4)})
            if "WEIGHTS_0" in prim["attributes"]:
                w = read_accessor(g, buf, prim["attributes"]["WEIGHTS_0"]).astype(np.float64)
                s = w.sum(axis=1)
                wstats.append({"sum_range": [round(float(s.min()), 3), round(float(s.max()), 3)],
                               "unweighted_pct": round(float((s < 0.01).mean())*100, 2),
                               "max_influences": int((w > 0.001).sum(axis=1).max())})
            for t in prim.get("targets", []):
                if "POSITION" in t:
                    acc = g["accessors"][t["POSITION"]]
                    bound = max(max(abs(v) for v in acc.get("max", [0])),
                                max(abs(v) for v in acc.get("min", [0])))
                    morphs.append(round(float(bound), 3))
    val = np.concatenate(vals) if vals else np.array([0])
    joints = {}
    if g.get("skins"):
        for jn in g["skins"][0]["joints"]:
            joints[g["nodes"][jn].get("name", f"node{jn}")] = [round(float(x), 3) for x in W[jn][:3, 3]]
    anims = []
    for a in g.get("animations", []):
        mx = max((float(read_accessor(g, buf, s["input"]).max()) for s in a.get("samplers", [])), default=0.0)
        anims.append({"name": a.get("name", "?"), "channels": len(a.get("channels", [])),
                      "duration_s": round(mx, 2)})
    return {"file": path.split("/")[-1], "topology": {
                **topo, "poles_ge7_pct": round(float((val >= 7).mean())*100, 2),
                "valence3_pct": round(float((val == 3).mean())*100, 2),
                "mean_valence": round(float(val.mean()), 2)},
            "uv_shells": uvs, "weight_shells": wstats,
            "morph_target_bounds": morphs, "joints": joints, "animations": anims}


if __name__ == "__main__":
    for p in sys.argv[1:]:
        print(json.dumps(inspect(p), indent=1))
