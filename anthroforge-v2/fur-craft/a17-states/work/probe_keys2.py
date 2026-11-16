import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.open_mainfile(filepath="/home/hatch/workspace/anthroforge-v2/fur-prototype/work/fur_stage2.blend")
ob = bpy.data.objects["BaraWolfBody"]
bpy.context.view_layer.objects.active = ob
ob.select_set(True)
bpy.context.view_layer.update()
psys = ob.particle_systems["FUR_ruff"]
print("after update:", len(psys.particles))
if len(psys.particles) == 0:
    bpy.ops.particle.particle_edit_toggle()
    print("after edit toggle on:", len(psys.particles))
    bpy.ops.particle.particle_edit_toggle()
    print("after edit toggle off:", len(psys.particles))
if len(psys.particles):
    p0 = psys.particles[0]
    print("hair keys:", len(p0.hair_keys))
    k = p0.hair_keys[-1]
    b = tuple(k.co); k.co = (b[0] + 0.05, b[1], b[2]); a = tuple(p0.hair_keys[-1].co)
    print("write:", b, "->", a, "OK" if abs(a[0]-b[0]-0.05) < 1e-6 else "NO-OP")
    m = bpy.data.materials["FurHair"]
    hair = [n for n in m.node_tree.nodes if n.type == 'BSDF_HAIR_PRINCIPLED'][0]
    print("hair inputs:", [i.name for i in hair.inputs])
