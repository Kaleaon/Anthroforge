import bpy, bmesh
import numpy as np
bpy.ops.wm.open_mainfile(filepath="/home/hatch/workspace/anthroforge-v2/parts-lab/kaleaon-anatomy/kaleaon_anatomy_parts.blend")
ob = bpy.data.objects["Part_Shaft_1"]
def vol_from_coords(co):
    bm = bmesh.new(); bm.from_mesh(ob.data)
    for v, c in zip(bm.verts, co): v.co = c
    bm.verts.index_update()
    v = bm.calc_volume(); bm.free(); return abs(v)*1000
kb = ob.data.shape_keys.key_blocks
n = len(ob.data.vertices)
base = np.empty(n*3); kb["Basis"].data.foreach_get("co", base)
plus = np.empty(n*3); kb["GirthPlus"].data.foreach_get("co", plus)
minus = np.empty(n*3); kb["GirthMinus"].data.foreach_get("co", minus)
print("vol Basis L:", round(vol_from_coords(base.reshape(-1,3)),3))
print("vol GirthPlus L:", round(vol_from_coords(plus.reshape(-1,3)),3))
print("vol GirthMinus L:", round(vol_from_coords(minus.reshape(-1,3)),3))
