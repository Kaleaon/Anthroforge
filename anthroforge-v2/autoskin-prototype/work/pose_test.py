"""Pose tests for both weighting methods (numpy LBS, matplotlib renders).

Bone pose model: each posed bone rotates about its own rest head point around
a world axis; world transform composes down the hierarchy
(A_child = A_parent o R_child). Poses: jaw open 25 deg, head turn 35 deg,
head tilt (Neck 6 + Head 14 deg roll). Metrics per pose: per-mesh
displacement, teeth discipline vs a geometric upper/lower reference split,
edge strain on the bust (collapse / candy-wrapper detector), stray verts.
"""
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components

W = "/home/hatch/workspace/anthroforge-v2/autoskin-prototype/work"
sys.path.insert(0, W)
from geo_weights import BONES, BONE_NAMES

PARENTS = {
    "Root": None, "Pelvis": "Root", "Spine1": "Pelvis", "Chest": "Spine1",
    "Neck": "Chest", "Head": "Neck", "Jaw": "Head", "Ear_L": "Head", "Ear_R": "Head",
    "Shoulder_L": "Chest", "Elbow_L": "Shoulder_L", "Wrist_L": "Elbow_L",
    "Shoulder_R": "Chest", "Elbow_R": "Shoulder_R", "Wrist_R": "Elbow_R",
    "Hip_L": "Pelvis", "Knee_L": "Hip_L", "Ankle_L": "Knee_L", "Foot_L": "Ankle_L",
    "Hip_R": "Pelvis", "Knee_R": "Hip_R", "Ankle_R": "Knee_R", "Foot_R": "Ankle_R",
    "Wing_L1": "Chest", "Wing_L2": "Wing_L1", "Wing_R1": "Chest", "Wing_R2": "Wing_R1",
    "Tail_1": "Pelvis", "Tail_2": "Tail_1", "Tail_3": "Tail_2",
    "GenBase": "Pelvis", "GenScrot": "GenBase", "Gen01": "GenBase",
    "Gen02": "Gen01", "Gen03": "Gen02", "Gen04": "Gen03",
}
AXES = {"X": (1, 0, 0), "Y": (0, 1, 0), "Z": (0, 0, 1)}
POSES = {
    "jaw":  {"Jaw": ("X", 25.0)},
    "turn": {"Head": ("Z", 35.0)},
    "tilt": {"Neck": ("Y", 6.0), "Head": ("Y", 14.0)},
}

def rot_axis(axis, deg):
    a = np.radians(deg)
    x, y, z = AXES[axis]
    K = np.array([[0, -z, y], [z, 0, -x], [-y, x, 0]])
    return np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * (K @ K)

def bone_transforms(pose):
    """Return {bone: (R, t)} world affine per bone for the given pose."""
    A = {}
    for name in BONE_NAMES:  # BONE_NAMES is parent-before-child ordered
        head = np.array(BONES[name][0], float)
        if name in pose:
            axis, deg = pose[name]
            Rb = rot_axis(axis, deg)
            tb = head - Rb @ head
        else:
            Rb, tb = np.eye(3), np.zeros(3)
        p = PARENTS[name]
        if p is None:
            A[name] = (Rb, tb)
        else:
            Rp, tp = A[p]
            A[name] = (Rp @ Rb, Rp @ tb + tp)
    return A

def deform(verts, bi, w4, A):
    out = np.zeros_like(verts)
    for k in range(4):
        idx = bi[:, k]
        wgt = w4[:, k]
        sel = wgt > 0
        if not sel.any():
            continue
        # group verts by bone for the affine apply
        for b in np.unique(idx[sel]):
            m = sel & (idx == b)
            R, t = A[BONE_NAMES[int(b)]]
            out[m] += wgt[m, None] * (verts[m] @ R.T + t)
    return out

def render(objs, out, az, el, title=""):
    tris, cols = [], []
    palette = [(0.75,0.55,0.45),(0.25,0.22,0.2),(0.9,0.8,0.3),(0.9,0.9,0.95),(0.95,0.93,0.85),(0.85,0.5,0.5)]
    for i, (vv, ff) in enumerate(objs):
        tris.append(vv[ff]); cols.append(np.tile(palette[i % len(palette)], (len(ff), 1)))
    tris = np.vstack(tris); cols = np.vstack(cols)
    azr, elr = np.radians(az), np.radians(el)
    vd = np.array([np.cos(elr)*np.sin(azr), np.cos(elr)*np.cos(azr), np.sin(elr)])
    up = np.array([0, 0, 1.0]); right = np.cross(vd, up); right /= np.linalg.norm(right)
    up2 = np.cross(right, vd)
    P = tris.reshape(-1, 3); x = P @ right; y = P @ up2; z = P @ vd
    depth = z.reshape(-1, 3).mean(1)
    n = np.cross(tris[:, 1]-tris[:, 0], tris[:, 2]-tris[:, 0])
    n /= (np.linalg.norm(n, axis=1, keepdims=True) + 1e-9)
    light = np.array([0.4, 0.8, 0.6]); light /= np.linalg.norm(light)
    shade = np.abs(n @ light) * 0.7 + 0.3
    fc = np.clip(cols * shade[:, None], 0, 1)
    order = np.argsort(depth)
    polys = np.stack([x.reshape(-1, 3), y.reshape(-1, 3)], -1)[order]
    fig, ax = plt.subplots(figsize=(6, 7))
    ax.add_collection(PolyCollection(polys, facecolors=fc[order], edgecolors="none"))
    ax.set_xlim(-4, 4); ax.set_ylim(-3.4, 2.2); ax.set_aspect("equal"); ax.axis("off"); ax.set_title(title)
    plt.tight_layout(); plt.savefig(out, dpi=90); plt.close()

def teeth_reference(verts, faces):
    E = np.vstack([faces[:, [0,1]], faces[:, [1,2]], faces[:, [2,0]]])
    E = np.unique(np.sort(E, axis=1), axis=0)
    G = csr_matrix((np.ones(len(E)), (E[:,0], E[:,1])), shape=(len(verts), len(verts)))
    lab = connected_components(G + G.T, directed=False)[1]
    upper = np.zeros(len(verts), bool)
    for c in range(lab.max() + 1):
        sel = lab == c
        vv = verts[sel]
        is_upper = vv[:, 2].mean() > -0.97
        span = vv[:, 2].max() - vv[:, 2].min()  # same tusk rule as the guards
        if span >= 0.30 and vv[:, 1].mean() < -0.95:
            zc = (vv[:, 2] - vv[:, 2].min()) / span
            def spread(s):
                cxy = s[:, :2].mean(0)
                return np.linalg.norm(s[:, :2] - cxy, axis=1).mean()
            if spread(vv[zc > 0.8]) < 0.6 * spread(vv[zc < 0.2]):
                is_upper = False
        upper[sel] = is_upper
    return upper

def main():
    d = np.load(f"{W}/bust_meshes.npz")
    names = [k[:-2] for k in d.keys() if k.endswith("_v")]
    upper = teeth_reference(d["Teeth_LP_Main_0_v"], d["Teeth_LP_Main_0_f"])
    methods = {"geo": "geo_weights_guarded.npz", "auto": "auto_weights.npz"}
    report = []
    for mname, fn in methods.items():
        w = np.load(f"{W}/{fn}")
        for pname, pose in POSES.items():
            A = bone_transforms(pose)
            objs, lines = [], []
            for name in names:
                v, f = d[name + "_v"], d[name + "_f"]
                dv = deform(v, w[name + "_bi"], w[name + "_w"], A)
                objs.append((dv, f))
                disp = np.linalg.norm(dv - v, axis=1)
                line = f"  {name}: disp mean {disp.mean():.3f} max {disp.max():.3f}"
                if name.startswith("Teeth") and pname == "jaw":
                    line += (f" | UPPER teeth mean disp {disp[upper].mean():.4f} (want ~0)"
                             f" | LOWER teeth mean disp {disp[~upper].mean():.3f} (want ~0.45 rigid)")
                if name.startswith("OrcBust"):
                    E = np.vstack([f[:, [0,1]], f[:, [1,2]], f[:, [2,0]]])
                    E = np.unique(np.sort(E, axis=1), axis=0)
                    l0 = np.linalg.norm(v[E[:,0]] - v[E[:,1]], axis=1)
                    l1 = np.linalg.norm(dv[E[:,0]] - dv[E[:,1]], axis=1)
                    strain = np.abs(l1 / np.maximum(l0, 1e-9) - 1)
                    chin = (v[:, 1] < -0.95) & (v[:, 2] < -1.15)
                    line += (f" | strain p50 {np.percentile(strain,50):.3f} p99 {np.percentile(strain,99):.3f}"
                             f" max {strain.max():.3f} | chin disp {disp[chin].mean():.3f} (n={chin.sum()})")
                lines.append(line)
            hdr = f"[{mname} / {pname}]"
            report.append(hdr); report.extend(lines)
            print(hdr); print("\n".join(lines))
            render(objs, f"{W}/pose_{mname}_{pname}_front.png", 180, 5, f"{mname} {pname} front")
            render(objs, f"{W}/pose_{mname}_{pname}_side.png", 90, 5, f"{mname} {pname} side")
    with open(f"{W}/pose_metrics.txt", "w") as fh:
        fh.write("\n".join(report) + "\n")
    print("saved pose_metrics.txt + renders")

if __name__ == "__main__":
    main()
