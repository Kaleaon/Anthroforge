import numpy as np
from collections import defaultdict
from glb_lib import load_glb, meshes

gltf, bin_chunk = load_glb("/home/hatch/workspace/anthroforge-v2/base-head-v3/neutral_base_head_v3.glb")
MS = meshes(gltf, bin_chunk)

def weld(pos, idx, tol=1e-4):
    key = np.round(pos / tol).astype(np.int64)
    _, first, inv = np.unique(key, axis=0, return_index=True, return_inverse=True)
    return pos[first], inv[idx]

tp, ti = weld(*MS["TissueHead"][0])
ap, ai = weld(*MS["Ear_L"][0])
eyeL = np.array([0.131, -0.008, -0.082])
d = np.linalg.norm(tp - eyeL, axis=1)
print("tissue verts by distance-to-eyeball-centre (L eye):")
for lo, hi in [(0.0,0.06),(0.06,0.075),(0.075,0.09),(0.09,0.105),(0.105,0.13),(0.13,0.16),(0.16,0.20)]:
    print(f"  {lo:.3f}-{hi:.3f}: {int(((d>=lo)&(d<hi)).sum())}")
print("min tissue-to-eye-centre dist:", round(float(d.min()),4), "(eyeball radius 0.075)")

# skin rings via BFS from the 12 closest tissue verts to eye centre
adj = defaultdict(set)
for t in ti:
    for a,b in ((0,1),(1,2),(2,0)):
        adj[a].add(b); adj[b].add(a)
seed = np.argsort(d)[:12].tolist()
seen = set(seed); frontier = seed; rings = []
for _ in range(10):
    nxt = []
    for v in frontier:
        for n in adj[v]:
            if n not in seen: seen.add(n); nxt.append(n)
    if not nxt: break
    rings.append((len(nxt), round(float(d[nxt].mean()),3), round(float(d[nxt].max()),3)))
    frontier = nxt
print("BFS layers from eye-station seeds (count, mean dist, max dist):", rings)

# ear grid rows along PCA length axis
c = ap.mean(0); U,S,Vt = np.linalg.svd(ap-c, full_matrices=False)
pc = (ap-c)@Vt.T
ax = pc[:,0]
hist, edges = np.histogram(ax, bins=12)
print("ear vert count by length-axis bin (12 bins):", hist.tolist())
ax2 = pc[:,1]
hist2, _ = np.histogram(ax2, bins=8)
print("ear vert count by width-axis bin (8 bins):", hist2.tolist())
# signed depth sign convention: which side is concave? centre verts vs rim using Vt[2]
depth = pc[:,2]
central = (np.abs(pc[:,0])<0.06)&(np.abs(pc[:,1])<0.03)
print("ear central patch depth mean:", round(float(depth[central].mean()),4), "n=", int(central.sum()),
      "| overall depth range:", round(float(depth.min()),3), round(float(depth.max()),3))
