import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.open_mainfile(filepath="/home/hatch/workspace/anthroforge-v2/fur-prototype/work/fur_stage2.blend")
ob = bpy.data.objects["BaraWolfBody"]
bpy.context.view_layer.objects.active = ob
ob.select_set(True)
psys = ob.particle_systems["FUR_ruff"]
try:
    bpy.ops.object.mode_set(mode='PARTICLE_EDIT')
    print("mode_set PARTICLE_EDIT ok; particles:", len(psys.particles), "is_edited:", psys.is_edited)
    if len(psys.particles):
        k = psys.particles[0].hair_keys[-1]
        b = tuple(k.co); k.co = (b[0]+0.05, b[1], b[2]); a = tuple(psys.particles[0].hair_keys[-1].co)
        print("write:", "OK" if abs(a[0]-b[0]-0.05) < 1e-6 else "NO-OP", b, "->", a)
    bpy.ops.object.mode_set(mode='OBJECT')
except Exception as e:
    print("mode_set failed:", repr(e))
p = psys.settings
props = [a for a in dir(p) if any(s in a for s in ("kink","clump","rough","brown","phase","rotat","veloc","length","radius","child"))]
print("settings props:", props)
print("kink enums:", [i.identifier for i in p.bl_rna.properties['kink'].enum_items] if 'kink' in p.bl_rna.properties else None)
