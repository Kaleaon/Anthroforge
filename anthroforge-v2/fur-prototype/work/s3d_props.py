import bpy
ps = bpy.data.particles.new("probe")
props = {p.identifier for p in ps.bl_rna.properties}
want = ['count','hair_step','display_step','render_step','emit_from','use_modifier_stack','roughness_1','roughness_2','material','display_percentage','child_percent','use_hair_bspline','length_random','distribution','particle_factor','jitter_factor']
for w in want: print(w, w in props)
print("STEP-ish:", sorted(x for x in props if 'step' in x))
print("EMIT-ish:", sorted(x for x in props if 'emit' in x or 'distrib' in x or 'jitter' in x))
print("ROUGH:", sorted(x for x in props if 'rough' in x))
