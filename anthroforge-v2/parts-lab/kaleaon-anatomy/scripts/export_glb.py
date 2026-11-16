import bpy
bpy.ops.wm.open_mainfile(filepath="/home/hatch/workspace/anthroforge-v2/parts-lab/kaleaon-anatomy/kaleaon_anatomy_parts.blend")
keep = {"KaleaonRig"} | {f"Part_Shaft_{n}" for n in (1, 2, 3, 4)} | {"Part_SacUdder"} | \
       {f"Part_SacUdder_Teat_{i}" for i in (1, 2, 3, 4)}
bpy.ops.object.select_all(action='DESELECT')
for ob in bpy.data.objects:
    ob.select_set(ob.name in keep)
bpy.ops.export_scene.gltf(
    filepath="/home/hatch/workspace/anthroforge-v2/parts-lab/kaleaon-anatomy/kaleaon_anatomy_parts.glb",
    use_selection=True, export_apply=False, export_skins=True,
    export_morph=True, export_yup=True)
print("GLB EXPORTED")
