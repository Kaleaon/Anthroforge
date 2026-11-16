import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection

d = np.load("/home/hatch/workspace/anthroforge-v2/autoskin-prototype/work/bust_meshes.npz")
print("keys:", list(d.keys()))
v = d["OrcBust_LP_Main_0_v"]
for ax, name in enumerate("XYZ"):
    h, edges = np.histogram(v[:, ax], bins=10)
    print(name, " ".join(f"{e:.2f}:{c}" for e, c in zip(edges[:-1], h)))

def render(objs, out, az, el, title=""):
    tris, cols = [], []
    palette = [(0.75,0.55,0.45),(0.25,0.22,0.2),(0.9,0.8,0.3),(0.9,0.9,0.95),(0.95,0.93,0.85),(0.85,0.5,0.5)]
    for i, (vv, ff) in enumerate(objs):
        tris.append(vv[ff])
        cols.append(np.tile(palette[i % len(palette)], (len(ff), 1)))
    tris = np.vstack(tris); cols = np.vstack(cols)
    azr, elr = np.radians(az), np.radians(el)
    vd = np.array([np.cos(elr)*np.sin(azr), np.cos(elr)*np.cos(azr), np.sin(elr)])
    up = np.array([0,0,1.0]); right = np.cross(vd, up); right /= np.linalg.norm(right)
    up2 = np.cross(right, vd)
    P = tris.reshape(-1,3); x = P @ right; y = P @ up2; z = P @ vd
    depth = z.reshape(-1,3).mean(1)
    n = np.cross(tris[:,1]-tris[:,0], tris[:,2]-tris[:,0])
    n /= (np.linalg.norm(n, axis=1, keepdims=True) + 1e-9)
    light = np.array([0.4,0.8,0.6]); light /= np.linalg.norm(light)
    shade = np.abs(n @ light)*0.7 + 0.3
    fc = np.clip(cols * shade[:,None], 0, 1)
    order = np.argsort(depth)
    polys = np.stack([x.reshape(-1,3), y.reshape(-1,3)], -1)[order]
    fig, ax = plt.subplots(figsize=(6,7))
    ax.add_collection(PolyCollection(polys, facecolors=fc[order], edgecolors="none"))
    ax.set_xlim(x.min(), x.max()); ax.set_ylim(y.min(), y.max())
    ax.set_aspect("equal"); ax.axis("off"); ax.set_title(title)
    plt.tight_layout(); plt.savefig(out, dpi=90); plt.close()
    print("saved", out)

objs = []
for k in d.keys():
    if k.endswith("_v"):
        objs.append((d[k], d[k[:-2] + "_f"]))
# views: az=180 -> looking from -Y (front, face side). up=+Z
render(objs, "/home/hatch/workspace/anthroforge-v2/autoskin-prototype/work/rest_front.png", 180, 5, "front (from -Y)")
render(objs, "/home/hatch/workspace/anthroforge-v2/autoskin-prototype/work/rest_side.png", 90, 5, "side (from +X)")
render(objs, "/home/hatch/workspace/anthroforge-v2/autoskin-prototype/work/rest_back.png", 0, 5, "back (from +Y)")
render(objs, "/home/hatch/workspace/anthroforge-v2/autoskin-prototype/work/rest_top.png", 180, 80, "top")
