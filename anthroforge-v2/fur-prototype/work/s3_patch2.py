import bpy
P = "/home/hatch/workspace/anthroforge-v2/fur-prototype/work/fur_stage2.blend"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.open_mainfile(filepath=P)
bsdf = bpy.data.materials["FurHair"].node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.072, 0.054, 0.041, 1.0)
bpy.ops.wm.save_as_mainfile(filepath=P)
print("ALBEDO PATCHED")
