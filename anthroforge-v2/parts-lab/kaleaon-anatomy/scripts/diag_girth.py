import bpy
import numpy as np
bpy.ops.wm.open_mainfile(filepath="/home/hatch/workspace/anthroforge-v2/parts-lab/kaleaon-anatomy/kaleaon_anatomy_parts.blend")
ob = bpy.data.objects["Part_Shaft_1"]
kb = ob.data.shape_keys.key_blocks
base = np.empty(len(ob.data.vertices)*3); kb["Basis"].data.foreach_get("co", base)
plus = np.empty(len(ob.data.vertices)*3); kb["GirthPlus"].data.foreach_get("co", plus)
d = np.linalg.norm(plus.reshape(-1,3)-base.reshape(-1,3), axis=1)
print("girth key disp mm: max", round(float(d.max())*1000,2), "mean", round(float(d.mean())*1000,2))
co = base.reshape(-1,3)
print("local bbox min", co.min(axis=0).round(3), "max", co.max(axis=0).round(3))
print("object matrix_world:", [tuple(round(x,3) for x in r) for r in ob.matrix_world])
arm = bpy.data.objects["KaleaonRig"]
print("arm matrix_world:", [tuple(round(x,3) for x in r) for r in arm.matrix_world])
