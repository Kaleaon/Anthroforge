import bpy, json
import numpy as np
from collections import defaultdict, deque

bpy.ops.wm.open_mainfile(filepath="/home/hatch/workspace/anthroforge-v2/base-head-v3/neutral_base_head_v3.blend")
ob = bpy.data.objects["TeethArcade"]
me = ob.data
V = np.array([tuple(v.co) for v in me.vertices])
print("arcade verts", len(V), "polys", len(me.polygons))

# connected components via edges
parent = list(range(len(V)))
def find(a):
    while parent[a]!=a: parent[a]=parent[parent[a]]; a=parent[a]
    return a
def union(a,b):
    ra,rb=find(a),find(b)
    if ra!=rb: parent[ra]=rb
for e in me.edges: union(e.vertices[0], e.vertices[1])
comps = defaultdict(list)
for i in range(len(V)): comps[find(i)].append(i)
print("components:", len(comps))
for k,idxs in sorted(comps.items(), key=lambda kv:-len(kv[1])):
    P = V[idxs]
    print(f" comp root={k} n={len(idxs)} x[{P[:,0].min():.3f},{P[:,0].max():.3f}] y[{P[:,1].min():.3f},{P[:,1].max():.3f}] z[{P[:,2].min():.3f},{P[:,2].max():.3f}]")

# z histogram of verts
hist, edges = np.histogram(V[:,2], bins=20)
for h,e in zip(hist, edges): print(f" z {e:+.3f}: {h}")

# palate line as stageF: max z of verts with y>0.18
pal = V[V[:,1]>0.18][:,2].max()
print("pal_z", round(float(pal),4))

# how many polys are quads/tris
from collections import Counter
print("poly sizes", Counter(len(p.vertices) for p in me.polygons))

# distance of arcade verts to Jaw and TissueHead surfaces (rough: nearest vert)
for name in ("Jaw","TissueHead","Tongue"):
    o2 = bpy.data.objects[name]
    W = np.array([tuple(o2.matrix_world @ v.co) for v in o2.data.vertices])
    d = np.sqrt(((V[:,None,:]-W[None,:,:])**2).sum(-1)).min(axis=1)
    print(f"arcade->{name}: min {d.min():.4f} mean {d.mean():.4f} frac<0.005 {(d<0.005).mean():.2f}")
