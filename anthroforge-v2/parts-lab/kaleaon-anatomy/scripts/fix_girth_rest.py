"""Fix: zero all Girth shape-key values so the saved rest state is Basis.
Build_parts left GirthPlus evaluated at full strength in the saved file
(measured shaft volumes 5.941/6.927 L at open vs canon basis 5.301/6.182 L).
"""
import bpy, bmesh
PATH = "/home/hatch/workspace/anthroforge-v2/parts-lab/kaleaon-anatomy/kaleaon_anatomy_parts.blend"
bpy.ops.wm.open_mainfile(filepath=PATH)
for n in (1, 2, 3, 4):
    ob = bpy.data.objects[f"Part_Shaft_{n}"]
    kb = ob.data.shape_keys.key_blocks
    print(f"Shaft_{n} BEFORE", {k.name: k.value for k in kb})
    for k in kb:
        if k.name != "Basis":
            k.value = 0.0
    print(f"Shaft_{n} AFTER", {k.name: k.value for k in kb})
bpy.context.view_layer.update()
for n in (1, 2, 3, 4):
    ob = bpy.data.objects[f"Part_Shaft_{n}"]
    dg = bpy.context.evaluated_depsgraph_get()
    me = ob.evaluated_get(dg).to_mesh()
    bm = bmesh.new(); bm.from_mesh(me); v = abs(bm.calc_volume()); bm.free()
    print(f"Shaft_{n} evaluated rest volume L = {v*1000:.3f}")
bpy.ops.wm.save_as_mainfile(filepath=PATH)
print("SAVED with girth keys at rest 0")
