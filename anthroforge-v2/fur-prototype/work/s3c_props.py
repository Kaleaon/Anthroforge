import bpy
ps = bpy.data.particles.new("probe")
props = [p.identifier for p in ps.bl_rna.properties]
print("DENSITY/LENGTH/etc:", [x for x in props if 'dens' in x or 'length' in x or 'invert' in x])
print("ALL COUNT:", len(props))
# check ParticleSystem RNA via a temp object
bpy.ops.mesh.primitive_cube_add()
ob = bpy.context.active_object
bpy.ops.object.particle_system_add()
psys = ob.particle_systems[0]
sprops = [p.identifier for p in psys.bl_rna.properties]
print("PSYS VERTEX/GROUP:", [x for x in sprops if 'vertex' in x or 'group' in x])
print("PSYS ALL:", sprops)
