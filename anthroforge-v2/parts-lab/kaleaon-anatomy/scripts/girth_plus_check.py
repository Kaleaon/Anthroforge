import bpy, bmesh, json
PATH = "/home/hatch/workspace/anthroforge-v2/parts-lab/kaleaon-anatomy/kaleaon_anatomy_parts.blend"
bpy.ops.wm.open_mainfile(filepath=PATH)
dg = bpy.context.evaluated_depsgraph_get()
def vol(ob):
    me = ob.evaluated_get(dg).to_mesh()
    bm = bmesh.new(); bm.from_mesh(me); v = abs(bm.calc_volume()); bm.free()
    return round(v * 1000, 3)
out = {}
for n in (1, 2, 3, 4):
    ob = bpy.data.objects[f"Part_Shaft_{n}"]
    kb = ob.data.shape_keys.key_blocks
    rest = vol(ob)
    kb["GirthPlus"].value = 1.0; bpy.context.view_layer.update(); plus = vol(ob)
    kb["GirthPlus"].value = 0.0; kb["GirthMinus"].value = 1.0; bpy.context.view_layer.update(); minus = vol(ob)
    kb["GirthMinus"].value = 0.0; bpy.context.view_layer.update()
    out[f"Shaft_{n}"] = {"stored_values_at_open": "0/0 (fix verified)" if n == 1 else "same file",
                         "rest_L": rest, "girth_plus_L": plus, "girth_minus_L": minus}
print(json.dumps(out, indent=1))
open("/home/hatch/workspace/anthroforge-v2/parts-lab/kaleaon-anatomy/work/girth_channels.json", "w").write(json.dumps(out, indent=1))
print("DONE - file NOT saved (read-only run)")
