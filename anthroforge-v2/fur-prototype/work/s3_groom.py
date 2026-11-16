import bpy

IN = "/home/hatch/workspace/anthroforge-v2/fur-prototype/work/fur_stage1.blend"
OUT = "/home/hatch/workspace/anthroforge-v2/fur-prototype/work/fur_stage2.blend"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.open_mainfile(filepath=IN)
ob = bpy.data.objects["BaraWolfBody"]
me = ob.data

# ---------- hair material (Principled Hair BSDF) ----------
hair_mat = bpy.data.materials.get("FurHair") or bpy.data.materials.new("FurHair")
hair_mat.use_nodes = True
nt = hair_mat.node_tree
nt.nodes.clear()
out_node = nt.nodes.new("ShaderNodeOutputMaterial")
hair = nt.nodes.new("ShaderNodeBsdfHairPrincipled")
hair.inputs["Color"].default_value = (0.30, 0.21, 0.14, 1.0)
hair.inputs["Roughness"].default_value = 0.42
hair.inputs["Radial Roughness"].default_value = 0.55
nt.links.new(hair.outputs["BSDF"], out_node.inputs["Surface"])
me.materials.append(hair_mat)
HAIR_SLOT = len(me.materials)  # 1-based index used by ParticleSettings.material
print("hair material slot:", HAIR_SLOT)

bpy.context.view_layer.objects.active = ob
ob.select_set(True)

REGIONS = [
    # name, vgroup, parents, children_render, length, root_r, clump, kink, kink_amp, kink_freq, steps
    ("ruff",     "FUR_ruff",     2400, 6, 0.170, 0.0021, 0.65, 'WAVE', 0.012, 3.0, 6),
    ("back",     "FUR_back",     3400, 6, 0.095, 0.0017, 0.45, 'CURL', 0.006, 2.0, 5),
    ("belly",    "FUR_belly",    2800, 6, 0.042, 0.0014, 0.25, 'NO',   0.0,   0.0, 4),
    ("coat",     "FUR_coat",     5600, 6, 0.066, 0.0016, 0.40, 'CURL', 0.005, 2.0, 5),
    ("bodyhair", "FUR_bodyhair", 1300, 3, 0.018, 0.0009, 0.10, 'NO',   0.0,   0.0, 3),
]

for (name, vg, count, children, length, root_r, clump, kink, kamp, kfreq, steps) in REGIONS:
    bpy.ops.object.particle_system_add()
    psys = ob.particle_systems[-1]
    psys.name = f"FUR_{name}"
    p = psys.settings
    p.name = f"FUR_{name}"
    p.type = 'HAIR'
    p.count = count
    p.hair_length = length
    p.hair_step = steps
    p.display_step = 3
    p.render_step = steps
    p.emit_from = 'FACE'
    p.use_modifier_stack = False
    psys.vertex_group_density = vg
    psys.vertex_group_length = vg
    p.child_type = 'INTERPOLATED'
    p.child_percent = 30
    p.rendered_child_count = children
    p.child_length = 1.0
    p.child_length_threshold = 0.15
    p.clump_factor = clump
    p.clump_shape = -0.4
    if kink != 'NO':
        p.kink = kink
        p.kink_amplitude = kamp
        p.kink_frequency = kfreq
        p.kink_shape = 0.3
    p.roughness_1 = 0.35
    p.roughness_2 = 0.25
    p.root_radius = root_r
    p.tip_radius = 0.0
    p.radius_scale = 1.0
    p.material = HAIR_SLOT
    p.display_percentage = 25
    # name the modifier so the render script can toggle visibility
    mod = ob.modifiers.get(psys.name)
    print("system", psys.name, "modifier:", mod.name if mod else None)

# Cycles hair shape: curves if available
try:
    bpy.context.scene.cycles.hair_shape_type = 'CURVE'
    print("hair_shape_type set to CURVE")
except Exception as e:
    print("hair_shape_type unavailable:", e)

bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SAVED", OUT)
