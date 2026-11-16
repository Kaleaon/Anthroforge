#!/usr/bin/env python3
"""B17 post-analysis (system python): micro-edge strain filtering,
worst-vertex localisation, pivot-offset decomposition, and matplotlib
captures (front + side orthographic) for the worst stress poses.
Reads results.json / static.json / bones.json / rest.npz / poses_npz/.
"""
import json, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
results = json.load(open(os.path.join(HERE, "results.json")))["poses"]
static = json.load(open(os.path.join(HERE, "static.json")))
bones = json.load(open(os.path.join(HERE, "bones.json")))
rest = np.load(os.path.join(HERE, "rest.npz"))
BODY = "BaraWolfBody"
BONES = [str(x) for x in rest[f"rest|{BODY}|bones"]]
BIDX = {n: i for i, n in enumerate(BONES)}
rpos = rest[f"rest|{BODY}|pos"]
rdom = rest[f"rest|{BODY}|dom"]
redges = rest[f"rest|{BODY}|edges"]

rl = np.linalg.norm(rpos[redges[:, 0]] - rpos[redges[:, 1]], axis=1)
edge_stats = dict(
    rest_edge_len_mm_p1=round(float(np.percentile(rl, 1)) * 1000, 2),
    rest_edge_len_mm_p50=round(float(np.percentile(rl, 50)) * 1000, 2),
    pct_edges_lt_1mm=round(float((rl < 0.001).mean() * 100), 3),
    pct_edges_lt_2mm=round(float((rl < 0.002).mean() * 100), 3))

def filtered_strain(pose):
    d = np.load(os.path.join(HERE, "poses_npz", pose + ".npz"))
    pos = d[f"{BODY}|pos"]
    pl = np.linalg.norm(pos[redges[:, 0]] - pos[redges[:, 1]], axis=1)
    strain = pl / np.maximum(rl, 1e-9)
    keep = rl >= 0.002
    return strain, keep, d[f"{BODY}|vstrain"], pos

analysis = {"edge_stats": edge_stats, "filtered": {}, "worst_verts": {},
            "pivot_decomposition": {}}
for pose, s in results.items():
    strain, keep, _, _ = filtered_strain(pose)
    analysis["filtered"][pose] = dict(
        strain_max_all=round(float(strain.max()), 3),
        strain_max_edges_ge_2mm=round(float(strain[keep].max()), 3),
        strain_p99_edges_ge_2mm=round(
            float(np.percentile(strain[keep], 99)), 3),
        pct_edges_ge_2mm_strain_gt_1_5=round(
            float((strain[keep] > 1.5).mean() * 100), 2))

# worst vertices for the headline poses
for pose in ("upperarm_twist_L_180", "shoulder_overhead_L", "deep_squat",
             "forearm_twist_L_180", "hip_flex_L", "neck_twist_80",
             "elbow_flex_R", "fist_L"):
    d = np.load(os.path.join(HERE, "poses_npz", pose + ".npz"))
    vs = d[f"{BODY}|vstrain"]
    top = np.argsort(vs)[-8:][::-1]
    analysis["worst_verts"][pose] = [
        dict(vert=int(i), vstrain=round(float(vs[i]), 2),
             dom_bone=BONES[int(rdom[i])],
             rest_pos=np.round(rpos[i], 3).tolist()) for i in top]

# pivot decomposition: perpendicular vs along-axis offset
sup = static["__support__"]
for key, v in sup.items():
    if ":pivot:" not in key:
        continue
    bn = key.split(":pivot:", 1)[1].split(":", 1)[1]
    b = bones[bn]
    head = np.array(b["head"]); tail = np.array(b["tail"])
    axis = (tail - head) / np.linalg.norm(tail - head)
    # recompute station centroid exactly as the audit did
    pn = b["parent"]
    pi = BIDX[pn]
    selp = np.where(rdom == pi)[0]
    d = np.linalg.norm(rpos[selp] - head, axis=1)
    plen = np.linalg.norm(np.array(bones[pn]["tail"])
                          - np.array(bones[pn]["head"]))
    near = selp[d < 0.45 * plen]
    cen = rpos[near].mean(axis=0)
    off = cen - head
    along = float(off @ axis)
    perp = float(np.linalg.norm(off - along * axis))
    rad = v["local_radius_m"]
    analysis["pivot_decomposition"][key] = dict(
        joint=bn, perp_offset_m=round(perp, 4),
        along_axis_offset_m=round(along, 4),
        perp_over_radius=round(perp / max(rad, 1e-6), 3))

json.dump(analysis, open(os.path.join(HERE, "analysis.json"), "w"), indent=1)
print(json.dumps(edge_stats, indent=1))
for p in ("upperarm_twist_L_180", "shoulder_overhead_L", "elbow_flex_R"):
    print(p, analysis["filtered"][p])
for k, v in analysis["pivot_decomposition"].items():
    print(v)

# ---------------------------------------------------------------- captures
CAPTURES = ["upperarm_twist_L_180", "forearm_twist_L_180",
            "shoulder_overhead_L", "deep_squat", "elbow_flex_R",
            "neck_twist_80"]
os.makedirs(os.path.join(HERE, "captures"), exist_ok=True)
for pose in CAPTURES:
    region = [BIDX[b] for b in results[pose]["region_bones"] if b in BIDX]
    d = np.load(os.path.join(HERE, "poses_npz", pose + ".npz"))
    pos = d[f"{BODY}|pos"]; vs = d[f"{BODY}|vstrain"]
    mask = np.isin(rdom, region)
    # include a margin of neighbouring verts for context
    fig, axes = plt.subplots(1, 2, figsize=(11, 5.5))
    for ax, (hi, vi, lab) in zip(axes, ((0, 2, "front (x right, z up)"),
                                        (1, 2, "side (y fwd, z up)"))):
        ax.scatter(rpos[mask, hi], rpos[mask, vi], s=1.5, c="0.82",
                   linewidths=0)
        sc = ax.scatter(pos[mask, hi], pos[mask, vi], s=2.5,
                        c=vs[mask], cmap="inferno", vmin=0.8, vmax=2.5,
                        linewidths=0)
        ax.set_aspect("equal")
        ax.set_xlabel(lab)
    fig.colorbar(sc, ax=axes, shrink=0.85, label="per-vertex max edge strain")
    s = results[pose]
    fig.suptitle(f"{pose} — grey: rest, colour: posed | region strain max "
                 f"{s.get('region_strain_max')}, region faces flipped "
                 f"{s.get('region_faces_flipped')}, bend {s.get('bend_deg')}deg")
    fig.savefig(os.path.join(HERE, "captures", pose + ".png"), dpi=90)
    plt.close(fig)
    print("capture", pose)
print("ANALYSIS DONE")
