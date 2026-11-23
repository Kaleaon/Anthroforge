import bpy

P = "/home/hatch/workspace/anthroforge-v2/fur-prototype/work/fur_stage2.blend"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.open_mainfile(filepath=P)

# --- replace hair shading with a predictable Principled BSDF ---
mat = bpy.data.materials["FurHair"]
nt = mat.node_tree
nt.nodes.clear()
outn = nt.nodes.new("ShaderNodeOutputMaterial")
bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
bsdf.inputs["Base Color"].default_value = (0.105, 0.078, 0.058, 1.0)
bsdf.inputs["Roughness"].default_value = 0.62
bsdf.inputs["Specular IOR Level"].default_value = 0.35
nt.links.new(bsdf.outputs["BSDF"], outn.inputs["Surface"])

ob = bpy.data.objects["BaraWolfBody"]
for psys in ob.particle_systems:
    p = psys.settings
    try:
        p.use_hair_bspline = True
    except Exception as e:
        print("bspline skip", psys.name, e)
    if psys.name == "FUR_coat":
        p.hair_length = 0.058
    print("patched", psys.name)

bpy.ops.wm.save_as_mainfile(filepath=P)
print("PATCHED+SAVED")
