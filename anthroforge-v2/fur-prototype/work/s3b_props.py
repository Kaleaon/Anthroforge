import bpy
ps = bpy.data.particles.new("probe")
props = [p.identifier for p in ps.bl_rna.properties]
print("VERTEX/GROUP:", [x for x in props if 'vertex' in x or 'group' in x])
print("CLUMP/KINK:", [x for x in props if 'clump' in x or 'kink' in x])
print("CHILD:", [x for x in props if 'child' in x])
print("RADIUS:", [x for x in props if 'radius' in x or 'root' in x or 'tip' in x])
