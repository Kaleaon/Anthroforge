import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.open_mainfile(filepath="/home/hatch/workspace/anthroforge-v2/fur-prototype/work/fur_stage2.blend")
ob = bpy.data.objects["BaraWolfBody"]
psys = ob.particle_systems["FUR_ruff"]
print("particles:", len(psys.particles))
p0 = psys.particles[0]
print("hair keys:", len(p0.hair_keys))
before = tuple(p0.hair_keys[-1].co)
# try direct write
try:
    k = p0.hair_keys[-1]
    k.co = (before[0] + 0.05, before[1], before[2])
    after = tuple(p0.hair_keys[-1].co)
    print("direct write:", before, "->", after, "OK" if abs(after[0]-before[0]-0.05) < 1e-6 else "NO-OP")
except Exception as e:
    print("direct write failed:", e)
# try via particle edit mode
try:
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.particle.particle_edit_toggle()
    k = psys.particles[1].hair_keys[-1]
    b2 = tuple(k.co); k.co = (b2[0]+0.07, b2[1], b2[2])
    a2 = tuple(psys.particles[1].hair_keys[-1].co)
    print("edit-mode write:", b2, "->", a2, "OK" if abs(a2[0]-b2[0]-0.07) < 1e-6 else "NO-OP")
    bpy.ops.particle.particle_edit_toggle()
except Exception as e:
    print("edit-mode write failed:", repr(e))
# object copy independence
ob2 = ob.copy()
bpy.context.scene.collection.objects.link(ob2)
ps2 = ob2.particle_systems["FUR_ruff"]
print("copy shares settings:", ps2.settings == psys.settings)
q0 = ps2.particles[0].hair_keys[-1].co
print("copy key equals edited original:", tuple(q0), "vs orig", tuple(psys.particles[0].hair_keys[-1].co))
# hair material inputs
m = bpy.data.materials["FurHair"]
hair = [n for n in m.node_tree.nodes if n.type == 'BSDF_HAIR_PRINCIPLED'][0]
print("hair inputs:", [i.name for i in hair.inputs])
