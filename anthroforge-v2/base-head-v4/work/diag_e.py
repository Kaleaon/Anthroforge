import bpy
import numpy as np
from mathutils import Vector
import bmesh

def cent(vs):
    c = Vector((0, 0, 0))
    for v in vs: c += v
    return c / len(vs)

# ---- 1) MuzzleWidth: who attains |x|>0.108 in the ruler slab?
bpy.ops.wm.open_mainfile(filepath="/home/hatch/workspace/anthroforge-v2/base-head-v3/neutral_base_head_v3.blend")
O = {o.name: o for o in bpy.data.objects}
ec = Vector((0.0, 0.0815, -0.0079)); nose = 0.5
ycan = ec.y + 0.5 * (nose - ec.y)
print("ycan", round(ycan, 4))
for nm in ("TissueHead", "Jaw"):
    ob = O[nm]
    W = np.array([tuple(ob.matrix_world @ v.co) for v in ob.data.vertices])
    slab = W[np.abs(W[:, 1] - ycan) < 0.02]
    print(f"v3 {nm}: slab n={len(slab)} max|x|={np.abs(slab[:,0]).max():.4f}")
    big = slab[np.abs(slab[:, 0]) > 0.108]
    for p in big: print("   big vert", np.round(p, 4))
bpy.ops.wm.open_mainfile(filepath="/home/hatch/workspace/anthroforge-v2/base-head-v4/neutral_base_head_v4.blend")
O4 = {o.name: o for o in bpy.data.objects}
W = np.array([tuple(v.co) for v in O4["TissueHead"].data.vertices])
slab = W[np.abs(W[:, 1] - ycan) < 0.02]
big = slab[np.abs(slab[:, 0]) > 0.108]
print(f"v4 TissueHead: slab n={len(slab)} big verts {len(big)}")
for p in big[:10]: print("   v4 big vert", np.round(p, 4))

# ---- 2) Ear ruler: subdivided-unrelaxed ear vs v3 ear
def ear_stats(ob):
    vs = [ob.matrix_world @ v.co for v in ob.data.vertices]
    low = sorted(vs, key=lambda v: v.z)[:max(8, len(vs) // 7)]
    b = cent(low); tip = max(vs, key=lambda v: (v - b).length)
    return b, tip, (tip - b).length
bpy.ops.wm.open_mainfile(filepath="/home/hatch/workspace/anthroforge-v2/base-head-v3/neutral_base_head_v3.blend")
eo = bpy.data.objects["Ear_L"]
b, t, L = ear_stats(eo)
print("v3 ear: base", [round(x, 4) for x in b], "len", round(L, 4), "nverts", len(eo.data.vertices))
bm = bmesh.new(); bm.from_mesh(eo.data)
bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=1, use_grid_fill=True)
bm.to_mesh(eo.data); bm.free(); eo.data.update()
b, t, L = ear_stats(eo)
print("v3 ear SUBDIVIDED-UNRELAXED: base", [round(x, 4) for x in b], "len", round(L, 4), "nverts", len(eo.data.vertices))
