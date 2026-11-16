import bpy
import numpy as np
bpy.ops.wm.open_mainfile(filepath="/home/hatch/workspace/anthroforge-v2/base-head-v4/work/stage_v4a.blend")
T = bpy.data.objects["TissueHead"]; J = bpy.data.objects["Jaw"]
A = np.array([tuple(v.co) for v in T.data.vertices])
B = np.array([tuple(v.co) for v in J.data.vertices]) + np.array(J.location)
print("T", A.shape, "J(world)", B.shape, "Jloc", tuple(J.location))
# chunked min distance from B points to A
best = np.full(len(B), 1e9)
for i in range(0, len(A), 512):
    d = np.sqrt(((B[:, None, :] - A[None, i:i+512, :]) ** 2).sum(-1)).min(axis=1)
    best = np.minimum(best, d)
for tol in (1e-7, 1e-6, 1e-5, 1e-4, 1e-3):
    print(f"J verts within {tol} of a T vert: {(best < tol).sum()}")
print("min dist overall", best.min())
