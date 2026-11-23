import bpy, random
from mathutils import Vector

IN = "/home/hatch/workspace/anthroforge-v2/fur-prototype/work/fur_stage2.blend"
OUT = "/home/hatch/workspace/anthroforge-v2/fur-prototype/work/fur_stage3.blend"
TEXDIR = "/home/hatch/workspace/anthroforge-v2/fur-prototype"
random.seed(1226)

# ============================================================
# PART A: bake card alpha textures from a real strand render
# ============================================================
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

    # emitter plane (XY, facing +Z)
    bpy.ops.mesh.primitive_plane_add(size=0.30, location=(0, 0, 0))
    em = bpy.context.active_object
    em.name = "CardEmitter"
    mat = bpy.data.materials.new("CardHair")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    outn = nt.nodes.new("ShaderNodeOutputMaterial")
    hair = nt.nodes.new("ShaderNodeBsdfHairPrincipled")
    hair.inputs["Color"].default_value = (0.36, 0.27, 0.19, 1.0)
    hair.inputs["Roughness"].default_value = 0.5
    nt.links.new(hair.outputs["BSDF"], outn.inputs["Surface"])
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
    p.material = 1
    psys.seed = seed

    # tilt emitter so strands sweep downward in frame
    em.rotation_euler = (-1.12, 0, 0)

    cam_data = bpy.data.cameras.new("BakeCam")
    cam_data.type = 'ORTHO'
    cam_data.ortho_scale = 0.36
    cam = bpy.data.objects.new("BakeCam", cam_data)
    sc.collection.objects.link(cam)
    cam.location = (0, -0.02, 0.85)
    cam.rotation_euler = (0, 0, 0)
    # camera looks along -Z by default: it is already facing the plane
    sc.camera = cam

    sun = bpy.data.objects.new("BakeSun", bpy.data.lights.new("BakeSun", 'SUN'))
    sun.data.energy = 4.0
    sc.collection.objects.link(sun)
    sun.rotation_euler = (0.5, 0.2, 0.0)

    bpy.ops.render.render(write_still=True)
    print("BAKED", outpath, flush=True)
    bpy.data.scenes.remove(sc)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.open_mainfile(filepath=IN)
bake_card_texture("BakeA", 800, 11, TEXDIR + "/fur_card_texture_a.png")
bake_card_texture("BakeB", 380, 47, TEXDIR + "/fur_card_texture_b.png")

# back to the main scene
main_sc = bpy.data.scenes[0]
bpy.context.window.scene = main_sc

# ============================================================
# PART B: card geometry sampled from the groom's parent strands
# ============================================================
ob = bpy.data.objects["BaraWolfBody"]
dg = bpy.context.evaluated_depsgraph_get()
ev = ob.evaluated_get(dg)
mw = ob.matrix_world

CARD_W = {"FUR_ruff": 0.030, "FUR_back": 0.024, "FUR_belly": 0.016, "FUR_coat": 0.022}
LOD_TARGETS = {
    "LOD0": {"FUR_ruff": 420, "FUR_back": 380, "FUR_belly": 260, "FUR_coat": 640},
    "LOD1": {"FUR_ruff": 170, "FUR_back": 150, "FUR_belly": 105, "FUR_coat": 255},
    "LOD2": {"FUR_ruff": 65,  "FUR_back": 55,  "FUR_belly": 40,  "FUR_coat": 95},
}
SEGS = 4

def card_materials():
    mats = []
    for suffix, texfile in (("A", "fur_card_texture_a.png"), ("B", "fur_card_texture_b.png")):
        m = bpy.data.materials.get(f"FurCard{suffix}") or bpy.data.materials.new(f"FurCard{suffix}")
        m.use_nodes = True
        nt = m.node_tree
        nt.nodes.clear()
        outn = nt.nodes.new("ShaderNodeOutputMaterial")
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
        bsdf.inputs["Roughness"].default_value = 0.85
        tex = nt.nodes.new("ShaderNodeTexImage")
        img = bpy.data.images.load(TEXDIR + "/" + texfile)
        img.alpha_mode = 'STRAIGHT'
        tex.image = img
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
        nt.links.new(bsdf.outputs["BSDF"], outn.inputs["Surface"])
        m.surface_render_method = 'DITHERED'
        try:
            m.blend_method = 'HASHED'
        except Exception:
            pass
        mats.append(m)
    return mats

MATS = card_materials()

def build_cards(lod_name):
    targets = LOD_TARGETS[lod_name]
    verts, faces, uvs, mat_ids = [], [], [], []
    for psys in ev.particle_systems:
        pname = psys.name
        if pname not in targets:
            continue
        parts = list(psys.particles)
        want = min(targets[pname], len(parts))
        stride = max(1, len(parts) // want)
        chosen = parts[::stride][:want]
        width0 = CARD_W[pname]
        for part in chosen:
            keys = [mw @ k.co for k in part.hair_keys]
            if len(keys) < 3:
                continue
            # resample to SEGS+1 points
            pts = []
            total = len(keys) - 1
            for s in range(SEGS + 1):
                f = s / SEGS * total
                i0 = int(f)
                i1 = min(i0 + 1, total)
                pts.append(keys[i0].lerp(keys[i1], f - i0))
            tan0 = (pts[1] - pts[0])
            if tan0.length < 1e-6:
                continue
            tan0.normalize()
            wdir = tan0.cross(Vector((0, 0, 1)))
            if wdir.length < 0.25:
                wdir = tan0.cross(Vector((1, 0, 0)))
            wdir.normalize()
            # random twist around the strand for natural card orientation variety
            from mathutils import Matrix
            ang = random.uniform(-0.6, 0.6)
            wdir = (Matrix.Rotation(ang, 3, tan0) @ wdir).normalized()
            base = len(verts)
            mid = random.choice((0, 1))
            for s, pt in enumerate(pts):
                t = s / SEGS
                w = width0 * (1.0 - 0.85 * t) * (0.85 + 0.3 * random.random())
                off = wdir * (w * 0.5)
                verts.append(tuple(pt - off))
                verts.append(tuple(pt + off))
                uvs.append((0.0, 1.0 - t))
                uvs.append((1.0, 1.0 - t))
            for s in range(SEGS):
                a = base + 2 * s
                faces.append((a, a + 1, a + 3, a + 2))
                mat_ids.append(mid)
    mesh = bpy.data.meshes.new(f"FurCards_{lod_name}")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    uv_layer = mesh.uv_layers.new(name="UVMap")
    for loop in mesh.loops:
        uv_layer.data[loop.index].uv = uvs[loop.vertex_index]
    for poly, mid in zip(mesh.polygons, mat_ids):
        poly.material_index = mid
    obj = bpy.data.objects.new(f"FurCards_{lod_name}", mesh)
    for m in MATS:
        mesh.materials.append(m)
    bpy.context.scene.collection.objects.link(obj)
    print(f"{lod_name}: cards={len(mat_ids)} tris={len(mesh.polygons)*2} verts={len(verts)}", flush=True)
    return obj

lod_objs = {name: build_cards(name) for name in ("LOD0", "LOD1", "LOD2")}
lod_objs["LOD1"].hide_render = True
lod_objs["LOD2"].hide_render = True

# export LOD0 cards as GLB (cards only)
bpy.ops.object.select_all(action='DESELECT')
lod_objs["LOD0"].select_set(True)
bpy.context.view_layer.objects.active = lod_objs["LOD0"]
bpy.ops.export_scene.gltf(filepath=TEXDIR + "/fur_cards_lod0.glb", export_format='GLB',
                          use_selection=True, export_apply=True)
print("EXPORTED fur_cards_lod0.glb", flush=True)

bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SAVED", OUT)
