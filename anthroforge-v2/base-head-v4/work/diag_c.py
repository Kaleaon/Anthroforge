import bpy
import numpy as np
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath="/home/hatch/workspace/anthroforge-v2/base-head-v4/work/stage_v4a.blend")
T4 = bpy.data.objects["TissueHead"]; J4 = bpy.data.objects["Jaw"]
H = np.array(J4.location)
Aarr = np.array([tuple(v.co) for v in T4.data.vertices])
Barr = np.array([tuple(v.co) for v in J4.data.vertices]) + H
best = np.full(len(Barr), 1e9); bj = np.zeros(len(Barr), int)
for i in range(0, len(Aarr), 512):
    d = np.sqrt(((Barr[:, None, :] - Aarr[None, i:i+512, :]) ** 2).sum(-1))
    m = d.argmin(axis=1); mv = d[np.arange(len(Barr)), m]
    upd = mv < best
    best[upd] = mv[upd]; bj[upd] = m[upd] + i
j = int(np.argmin(best)); i = bj[j]
print("closest dist", best[j])
print("B", Barr[j], "A", Aarr[i])
print("B key", tuple(round(float(x), 5) for x in Barr[j]))
print("A key", tuple(round(float(x), 5) for x in Aarr[i]))
print("B raw floats", [float(x) for x in Barr[j]])
print("A raw floats", [float(x) for x in Aarr[i]])
