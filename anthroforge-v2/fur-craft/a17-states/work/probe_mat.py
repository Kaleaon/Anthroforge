import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.open_mainfile(filepath="/home/hatch/workspace/anthroforge-v2/fur-prototype/work/fur_stage2.blend")
ob = bpy.data.objects["BaraWolfBody"]
print("OBJECT", ob.name)
print("PSYSTEMS", [ps.name for ps in ob.particle_systems])
for ps in ob.particle_systems:
    p = ps.settings
    print("PS", ps.name, "type", p.type, "count", p.count, "hair_length", p.hair_length,
          "clump_factor", p.clump_factor, "kink", p.kink, "material_slot", p.material)
print("MATERIALS", [m.name if m else None for m in bpy.data.materials])
for m in bpy.data.materials:
    if not m or not m.node_tree:
        print("MAT", m.name if m else None, "no node tree")
        continue
    print("MAT", m.name, "nodes:")
    for n in m.node_tree.nodes:
        print("   ", repr(n.type), n.bl_idname, repr(n.name))
        if 'HAIR' in n.type or 'Principled' in n.name:
            print("      inputs:", [i.name for i in n.inputs])
print("OBJ MAT SLOTS", [m.name if m else None for m in ob.data.materials])
