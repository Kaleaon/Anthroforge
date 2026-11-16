import bpy
import numpy as np
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath="/home/hatch/workspace/anthroforge-v2/base-head-v4/work/stage_v4a.blend")
T4 = bpy.data.objects["TissueHead"]; J4 = bpy.data.objects["Jaw"]
H = Vector(J4.location)
A = {(round(v.co.x, 5), round(v.co.y, 5), round(v.co.z, 5)): np.array(v.co) for v in T4.data.vertices}
Bv = [np.array(v.co) + np.array(H) for v in J4.data.vertices]
print("A size", len(A), "Bv", len(Bv))
pts = [p for p in Bv if (round(p[0], 5), round(p[1], 5), round(p[2], 5)) in A]
print("matched", len(pts))
# inspect one known coincident pair manually
Aarr = np.array([tuple(v.co) for v in T4.data.vertices])
Barr = np.array(Bv)
d = np.sqrt(((Barr[:, None, :] - Aarr[None, :, :]) ** 2).sum(-1))
i, j = np.unravel_index(np.argmin(d), d.shape)
print("closest pair dist", d[i, j], "B", Barr[j], "A", Aarr[i])
print("B key", (round(Barr[j][0], 5), round(Barr[j][1], 5), round(Barr[j][2], 5)))
print("A key", (round(Aarr[i][0], 5), round(Aarr[i][1], 5), round(Aarr[i][2], 5)))
print("types", type(Barr[j][0]), type(Aarr[i][0]))
