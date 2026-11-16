import bpy
import numpy as np
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath="/home/hatch/workspace/anthroforge-v2/base-head-v4/work/stage_v4a.blend")
T4 = bpy.data.objects["TissueHead"]; J4 = bpy.data.objects["Jaw"]
H = Vector(J4.location)
v0 = J4.data.vertices[0]
print("np.array(v.co):", np.array(v0.co), np.array(v0.co).dtype)
print("tuple:", tuple(v0.co))
print("np.array(H):", np.array(H), np.array(H).dtype)
s = np.array(v0.co) + np.array(H)
print("sum:", s, s.dtype)
A1 = {(round(v.co.x,5), round(v.co.y,5), round(v.co.z,5)) for v in T4.data.vertices}
A2 = {tuple(round(float(x),5) for x in tuple(v.co)) for v in T4.data.vertices}
B1 = [np.array(v.co) + np.array(H) for v in J4.data.vertices]
B2 = [np.array(tuple(v.co)) + np.array(tuple(H)) for v in J4.data.vertices]
m11 = sum(1 for p in B1 if (round(p[0],5), round(p[1],5), round(p[2],5)) in A1)
m22 = sum(1 for p in B2 if (round(p[0],5), round(p[1],5), round(p[2],5)) in A2)
m21 = sum(1 for p in B2 if (round(p[0],5), round(p[1],5), round(p[2],5)) in A1)
m12 = sum(1 for p in B1 if (round(p[0],5), round(p[1],5), round(p[2],5)) in A2)
print("matches B1/A1", m11, "B2/A2", m22, "B2/A1", m21, "B1/A2", m12)
