import bpy

TEXDIR = "/home/hatch/workspace/anthroforge-v2/fur-prototype"

def bake_card_texture(name, count, seed, outpath):
    sc = bpy.data.scenes.new(name)
    bpy.context.window.scene = sc
    sc.render.engine = 'CYCLES'
    sc.cycles.samples = 24
    sc.cycles.use_denoising = True
    sc.render.resolution_x = 512
    sc.render.resolution_y = 1024
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = 'PNG'
    sc.render.filepath = outpath

    bpy.ops.mesh.primitive_plane_add(size=0.30, location=(0, 0.11, 0))
    em = bpy.context.active_object
    em.name = "CardEmitter"
    # slot 0: transparent (hides the emitter sheet itself)
    ghost = bpy.data.materials.new("Ghost")
    ghost.use_nodes = True
    gnt = ghost.node_tree
    gnt.nodes.clear()
    go = gnt.nodes.new("ShaderNodeOutputMaterial")
    gt = gnt.nodes.new("ShaderNodeBsdfTransparent")
    gnt.links.new(gt.outputs["BSDF"], go.inputs["Surface"])
    em.data.materials.append(ghost)
    # slot 1: the hair shading the particles will use
    mat = bpy.data.materials.new("CardHair")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    outn = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (0.30, 0.23, 0.17, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.7
    nt.links.new(bsdf.outputs["BSDF"], outn.inputs["Surface"])
    em.data.materials.append(mat)

    bpy.ops.object.particle_system_add()
    psys = em.particle_systems[-1]
    p = psys.settings
    p.type = 'HAIR'
    p.count = count
    p.hair_length = 0.27
    p.hair_step = 6
    p.render_step = 6
    p.emit_from = 'FACE'
    p.child_type = 'INTERPOLATED'
    p.child_percent = 100
    p.rendered_child_count = 4
    p.clump_factor = 0.38
    p.clump_shape = -0.3
    p.kink = 'WAVE'
    p.kink_amplitude = 0.006
    p.kink_frequency = 2.0
    p.root_radius = 0.0016
    p.tip_radius = 0.0
    p.material = 2
    psys.seed = seed

    # hang the curtain: hair direction rotates from +Z to -Y (down in frame)
    em.rotation_euler = (1.48, 0, 0)

    cam_data = bpy.data.cameras.new("BakeCam")
    cam_data.type = 'ORTHO'
    cam_data.ortho_scale = 0.34
    cam = bpy.data.objects.new("BakeCam", cam_data)
    sc.collection.objects.link(cam)
    cam.location = (0, -0.03, 0.85)
    sc.camera = cam

    sun = bpy.data.objects.new("BakeSun", bpy.data.lights.new("BakeSun", 'SUN'))
    sun.data.energy = 3.2
    sc.collection.objects.link(sun)
    sun.rotation_euler = (0.5, 0.2, 0.0)

    bpy.ops.render.render(write_still=True)
    print("BAKED", outpath, flush=True)
    bpy.data.scenes.remove(sc)

bpy.ops.wm.read_factory_settings(use_empty=True)
bake_card_texture("BakeA", 800, 11, TEXDIR + "/fur_card_texture_a.png")
bake_card_texture("BakeB", 380, 47, TEXDIR + "/fur_card_texture_b.png")
print("BAKEFIX DONE")
