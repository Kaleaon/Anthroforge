"""A2 test patches: six family patches on identical domes, rendered face-on
and at grazing (~82 deg). Also exports a textured demo GLB + saves .blend.

Run: blender -b --factory-startup -noaudio --threads 2 --python build_patch.py
"""
import bpy, math, os, random, sys
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import card_geo

ROOT = os.path.dirname(HERE)
A8 = os.path.expanduser("~/workspace/anthroforge-v2/fur-craft/a8-cardtextures")
REND = os.path.join(ROOT, "renders")
os.makedirs(REND, exist_ok=True)

R_SPHERE = 0.5
R_PATCH = 0.21


def dome_z(x, y):
    r2 = x * x + y * y
    return math.sqrt(R_SPHERE ** 2 - r2) - math.sqrt(R_SPHERE ** 2 - R_PATCH ** 2)


def dome_n(x, y):
    z = math.sqrt(R_SPHERE ** 2 - x * x - y * y)
    return Vector((x, y, z)).normalized()


def build_dome(mat):
    step = 0.021
    n = int(2 * R_PATCH / step)
    idx, verts = {}, []
    for i in range(n + 1):
        for j in range(n + 1):
            x = -R_PATCH + i * step
            y = -R_PATCH + j * step
            if x * x + y * y <= (R_PATCH + 0.004) ** 2:
                idx[(i, j)] = len(verts)
                verts.append((x, y, dome_z(x, y)))
    faces = []
    for i in range(n):
        for j in range(n):
            q = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
            if all(k in idx for k in q):
                faces.append(tuple(idx[k] for k in q))
    me = bpy.data.meshes.new("dome")
    me.from_pydata(verts, [], faces)
    me.update()
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(mat)
    return me


def fur_material(tex_name, nrm_strength):
    mat = bpy.data.materials.new("Fur_" + tex_name)
    mat.use_nodes = True
    nt = mat.node_tree
    out = nt.nodes.get("Material Output")
    prin = nt.nodes.get("Principled BSDF")
    prin.inputs["Roughness"].default_value = 0.85
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(os.path.join(A8, f"card_{tex_name}_diffuse.png"))
    nrm = nt.nodes.new("ShaderNodeTexImage")
    nrm.image = bpy.data.images.load(os.path.join(A8, f"card_{tex_name}_normal.png"))
    nrm.image.colorspace_settings.name = "Non-Color"
    nmap = nt.nodes.new("ShaderNodeNormalMap")
    nmap.inputs["Strength"].default_value = nrm_strength
    gt = nt.nodes.new("ShaderNodeMath")
    gt.operation = "GREATER_THAN"
    gt.inputs[1].default_value = 0.5
    transp = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(tex.outputs["Color"], prin.inputs["Base Color"])
    nt.links.new(tex.outputs["Alpha"], gt.inputs[0])
    nt.links.new(nrm.outputs["Color"], nmap.inputs["Color"])
    nt.links.new(nmap.outputs["Normal"], prin.inputs["Normal"])
    nt.links.new(gt.outputs["Value"], mix.inputs["Fac"])
    nt.links.new(transp.outputs["BSDF"], mix.inputs[1])
    nt.links.new(prin.outputs["BSDF"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    return mat


def plant_patch(fam_name, spec, centre_x, mat):
    rng = random.Random(hash(fam_name) & 0xFFFF)
    base_verts, base_faces, base_uvs = spec["build"]()
    cluster = fam_name in ("cross_pair", "tri_fan")
    spacing = {"cross_pair": 0.055, "tri_fan": 0.060,
               "quad_shingle": 0.036}.get(fam_name, 0.030)
    # per-family patch scale (normalised GLB size is L=0.10/W=0.030)
    sx = {"quad_shingle": 1.4}.get(fam_name, 1.0)
    sz = {"cross_pair": 1.1, "quad_shingle": 0.7}.get(fam_name, 0.95)
    verts, faces, uvs = [], [], []
    count = 0
    gx = -R_PATCH
    while gx <= R_PATCH:
        gy = -R_PATCH
        while gy <= R_PATCH:
            x = gx + rng.uniform(-0.35, 0.35) * spacing
            y = gy + rng.uniform(-0.35, 0.35) * spacing
            gy += spacing
            if x * x + y * y > 0.20 ** 2:
                continue
            n = dome_n(x, y)
            surf = Vector((x, y, dome_z(x, y)))
            flow = Vector((x + 0.35, y, 0.0))
            flow = flow - n * flow.dot(n)
            flow.normalize()
            tilt = math.radians(26 + rng.uniform(-7, 7))
            g = (n * math.cos(tilt) + flow * math.sin(tilt)).normalized()
            xa = g.cross(flow).normalized()
            ya = g.cross(xa).normalized()
            psi = rng.uniform(0, 2 * math.pi) if cluster else math.radians(rng.uniform(-18, 18))
            xa, ya = (xa * math.cos(psi) + ya * math.sin(psi),
                      -xa * math.sin(psi) + ya * math.cos(psi))
            root = surf - n * 0.004 + Vector((centre_x, 0, 0))
            s1 = rng.uniform(0.85, 1.15)
            s3 = s1 * rng.uniform(0.9, 1.2)
            off = len(verts)
            for (vx, vy, vz), uv in zip(base_verts, base_uvs):
                w = root + xa * (vx * sx * s1) + ya * (vy * s1) + g * (vz * sz * s3)
                verts.append(tuple(w))
                uvs.append(uv)
            for f in base_faces:
                faces.append(tuple(i + off for i in f))
            count += 1
        gx += spacing
    me = bpy.data.meshes.new("patch_" + fam_name)
    me.from_pydata(verts, [], faces)
    me.update()
    uvl = me.uv_layers.new(name="UVMap")
    for loop in me.loops:
        uvl.data[loop.index].uv = uvs[loop.vertex_index]
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(mat)
    ob = bpy.data.objects.new("patch_" + fam_name, me)
    bpy.context.collection.objects.link(ob)
    tris = sum(2 if len(p.vertices) == 4 else 1 for p in me.polygons)
    print(f"PATCH {fam_name}: {count} placements, {tris} tris")
    return ob, count, tris


def look_at(cam, target):
    d = Vector(target) - cam.location
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


# ---------- scene ----------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.samples = 32
scene.cycles.use_denoise = False
scene.render.resolution_x = 640
scene.render.resolution_y = 480
scene.render.image_settings.file_format = "PNG"
world = bpy.data.worlds.new("W")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.45, 0.45, 0.45, 1)
world.node_tree.nodes["Background"].inputs[1].default_value = 0.7
scene.world = world

for loc, energy, size in (((0.3, -0.5, 1.4), 900, 1.2), ((-1.0, 0.9, 0.8), 250, 1.0)):
    ld = bpy.data.lights.new("L", "AREA")
    ld.energy, ld.shape, ld.size = energy, "DISK", size
    lo = bpy.data.objects.new("L", ld)
    lo.location = loc
    lo.rotation_euler = (0.5, 0, 0.3)
    bpy.context.collection.objects.link(lo)

dome_mat = bpy.data.materials.new("Undercoat")
dome_mat.use_nodes = True
dome_mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.02, 0.02, 0.55, 1)
dome_mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 1.0

backdrop_mat = bpy.data.materials.new("Backdrop")
backdrop_mat.use_nodes = True
bsdf = backdrop_mat.node_tree.nodes.get("Principled BSDF")
emis = backdrop_mat.node_tree.nodes.new("ShaderNodeEmission")
emis.inputs["Color"].default_value = (1.0, 0.0, 1.0, 1)
emis.inputs["Strength"].default_value = 1.0
backdrop_mat.node_tree.links.new(emis.outputs["Emission"],
                                 backdrop_mat.node_tree.nodes["Material Output"].inputs["Surface"])
bpy.ops.mesh.primitive_plane_add(size=8.0, location=(1.5, 0, -0.02))
backdrop = bpy.context.object
backdrop.data.materials.append(backdrop_mat)
backdrop.visible_diffuse = False
backdrop.visible_glossy = False
backdrop.visible_transmission = False
backdrop.visible_volume_scatter = False
backdrop.visible_shadow = False

NRM = {"straight": 1.8, "wavy": 1.8, "clumped": 2.1, "guard_ruff": 2.1,
       "tail_plume": 1.5}
mats = {t: fur_material(t, NRM[t]) for t in NRM}

patch_obs = []
summary = {}
for i, (fam, spec) in enumerate(card_geo.FAMILIES.items()):
    cx = i * 0.60
    dome_ob = bpy.data.objects.new("dome_" + fam, build_dome(dome_mat))
    dome_ob.location = (cx, 0, 0)
    bpy.context.collection.objects.link(dome_ob)
    ob, count, tris = plant_patch(fam, spec, cx, mats[spec["texture"]])
    patch_obs += [dome_ob, ob]
    summary[fam] = dict(placements=count, patch_tris=tris)

    cam_data = bpy.data.cameras.new("cam")
    cam_data.lens = 50
    cam = bpy.data.objects.new("cam_" + fam, cam_data)
    bpy.context.collection.objects.link(cam)
    scene.camera = cam
    cam.location = (cx, 0, 0.60)
    look_at(cam, (cx, 0, 0.02))
    scene.render.filepath = os.path.join(REND, f"patch_{fam}_front.png")
    bpy.ops.render.render(write_still=True)
    cam.location = (cx + 0.55, 0.0, 0.085)
    look_at(cam, (cx, 0, 0.03))
    scene.render.filepath = os.path.join(REND, f"patch_{fam}_grazing.png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED", fam)

import json
json.dump(summary, open(os.path.join(HERE, "patch_summary.json"), "w"), indent=1)

bpy.ops.object.select_all(action="DESELECT")
for ob in patch_obs:
    ob.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT, "cards_patch_demo.glb"),
                          export_format="GLB", use_selection=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "a2_cards_demo.blend"))
print("DONE")
