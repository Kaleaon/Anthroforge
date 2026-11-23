#!/usr/bin/env python3
"""AnthroForge Materials Lab — swatch renderer.

Reads materials.json (the record set) and builds one Principled material per
record in Blender, renders each on a UV sphere under the Poly Haven studio
HDRI (CC0), then renders skin_smooth on the v1 neutral base head.
Run: blender -b --python render_swatches.py
"""
import bpy, json, math, os

LAB = os.path.expanduser("~/workspace/anthroforge-v2/materials-lab")
WS = os.path.expanduser("~/workspace")
RECORDS = json.load(open(os.path.join(LAB, "materials.json")))
HDRI = os.path.join(WS, "bodies-3d/parts-library/polyhaven/photo-studio-01-hdri/photo_studio_01_2k.hdr")
HEAD_GLB = os.path.expanduser("~/workspace/anthroforge-v2/base-head/neutral_base_head.glb")
SPHERE_R = 0.06  # 12 cm swatch sphere: subsurface scale_mm stays physically true

# ---------- helpers ----------
def srgb_to_linear(hexstr):
    h = hexstr.lstrip("#")
    vals = [int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4)]
    return tuple(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in vals) + (1.0,)

def rough_of(pbr):
    r = pbr.get("roughness", 0.5)
    return r["default"] if isinstance(r, dict) else r

def new_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    return m, m.node_tree.nodes["Principled BSDF"]

def apply_pbr(mat, bsdf, pbr, base_tex=None):
    nt = mat.node_tree
    if base_tex:
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = base_tex
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    else:
        bc = pbr.get("base_color", {})
        hexv = bc.get("srgb_default")
        if hexv:
            bsdf.inputs["Base Color"].default_value = srgb_to_linear(hexv)
    bsdf.inputs["Metallic"].default_value = pbr.get("metallic", 0.0)
    bsdf.inputs["Roughness"].default_value = rough_of(pbr)
    bsdf.inputs["IOR"].default_value = pbr.get("ior", 1.45)
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = pbr.get("specular_level", 0.5)
    ss = pbr.get("subsurface")
    if ss:
        bsdf.inputs["Subsurface Weight"].default_value = ss["weight"]
        rad = ss["radius_rgb"]
        bsdf.inputs["Subsurface Radius"].default_value = (rad[0], rad[1], rad[2])
        bsdf.inputs["Subsurface Scale"].default_value = ss["scale_mm"] / 1000.0
    coat = pbr.get("coat")
    if coat:
        bsdf.inputs["Coat Weight"].default_value = coat.get("weight", 0.0)
        bsdf.inputs["Coat Roughness"].default_value = coat.get("roughness", 0.3)
    sheen = pbr.get("sheen")
    if sheen and sheen.get("weight", 0) > 0:
        bsdf.inputs["Sheen Weight"].default_value = sheen["weight"]
        bsdf.inputs["Sheen Roughness"].default_value = sheen.get("roughness", 0.5)
    if "anisotropy" in pbr and "Anisotropic" in bsdf.inputs:
        bsdf.inputs["Anisotropic"].default_value = pbr["anisotropy"]
    tr = pbr.get("transmission")
    if tr:
        bsdf.inputs["Transmission Weight"].default_value = tr["weight"]
        if "Thickness" in bsdf.inputs:
            bsdf.inputs["Thickness"].default_value = tr.get("thickness_mm", 0.5) / 1000.0

def add_noise_bump(mat, bsdf, scale, strength, stretch=None):
    nt = mat.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = 6.0
    if stretch:
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = stretch
        nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
        nt.links.new(mp.outputs["Vector"], noise.inputs["Vector"])
    else:
        nt.links.new(tc.outputs["Generated"], noise.inputs["Vector"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = strength
    bump.inputs["Distance"].default_value = 0.0012
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

# procedural bump recipes per material id: (noise scale, strength, stretch)
BUMPS = {
    "skin_smooth":      (140.0, 0.15, None),
    "skin_furred_base": (220.0, 0.20, (1.0, 6.0, 1.0)),
    "teeth_enamel":     (300.0, 0.05, None),
    "claw_keratin":     (160.0, 0.25, (6.0, 1.0, 1.0)),
    "tongue_mouth":     (90.0, 0.30, None),
    "scar_tissue":      (120.0, 0.35, (1.0, 5.0, 1.0)),
}

# ---------- scene ----------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = "CYCLES"  # Eevee aborts headless on this VM (no libEGL); Cycles is the proven route in this workspace
scene.cycles.samples = 28
scene.cycles.use_denoising = True
scene.cycles.device = "CPU"
scene.render.resolution_x = 512
scene.render.resolution_y = 512
scene.view_settings.view_transform = "AgX"

world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
wnt = world.node_tree
env = wnt.nodes.new("ShaderNodeTexEnvironment")
env.image = bpy.data.images.load(HDRI)
wnt.links.new(env.outputs["Color"], wnt.nodes["Background"].inputs["Color"])

cam_data = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam
cam.location = (0.0, -0.34, 0.09)
cam.rotation_euler = (math.radians(76), 0, 0)
cam_data.lens = 50

sun_data = bpy.data.lights.new("Sun", "SUN")
sun_data.energy = 2.2
sun_data.angle = 0.35
sun = bpy.data.objects.new("Sun", sun_data)
scene.collection.objects.link(sun)
sun.rotation_euler = (math.radians(48), math.radians(12), math.radians(-30))

ground_mat, g_bsdf = new_mat("Ground")
g_bsdf.inputs["Base Color"].default_value = (0.055, 0.055, 0.058, 1.0)
g_bsdf.inputs["Roughness"].default_value = 0.95
bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 0, -SPHERE_R - 0.004))
ground = bpy.context.active_object
ground.data.materials.append(ground_mat)

bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=64, radius=SPHERE_R, location=(0, 0, 0))
ball = bpy.context.active_object
bpy.ops.object.shade_smooth()

bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=64, radius=SPHERE_R * 1.045, location=(0, 0, 0))
cornea = bpy.context.active_object
bpy.ops.object.shade_smooth()
cornea.hide_render = True

# ---------- build materials from records ----------
by_id = {m["id"]: m for m in RECORDS["materials"]}
built = {}

for mid, rec in by_id.items():
    if mid == "eye":
        # iris ball: iris texture as base colour, rest from the layer record
        layer = rec["layers"][0]["pbr"]
        mat, bsdf = new_mat("eye_iris")
        iris_img = bpy.data.images.load(os.path.join(LAB, "textures/iris_amber.png"))
        apply_pbr(mat, bsdf, layer, base_tex=iris_img)
        built["eye"] = mat
        # cornea shell
        cmat, cbsdf = new_mat("eye_cornea")
        apply_pbr(cmat, cbsdf, rec["layers"][1]["pbr"])
        cornea.data.materials.append(cmat)
        continue
    mat, bsdf = new_mat(mid)
    apply_pbr(mat, bsdf, rec["pbr"])
    if mid == "nose_leather":
        nt = mat.node_tree
        nimg = bpy.data.images.load(os.path.join(WS, rec["normal"]["path"]))
        nimg.colorspace_settings.name = "Non-Color"
        ntex = nt.nodes.new("ShaderNodeTexImage"); ntex.image = nimg
        nmap = nt.nodes.new("ShaderNodeNormalMap")
        nmap.inputs["Strength"].default_value = rec["normal"]["strength"]
        nt.links.new(ntex.outputs["Color"], nmap.inputs["Color"])
        nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
        rimg = bpy.data.images.load(os.path.join(WS, rec["roughness_map"]["path"]))
        rimg.colorspace_settings.name = "Non-Color"
        rtex = nt.nodes.new("ShaderNodeTexImage"); rtex.image = rimg
        rng = nt.nodes.new("ShaderNodeMapRange")
        rng.inputs["To Min"].default_value = rec["pbr"]["roughness"]["low"]
        rng.inputs["To Max"].default_value = rec["pbr"]["roughness"]["high"]
        rng.clamp = True
        nt.links.new(rtex.outputs["Color"], rng.inputs["Value"])
        nt.links.new(rng.outputs["Result"], bsdf.inputs["Roughness"])
    elif mid == "skin_furred_base":
        # sheen colour = coat highlight tint (lightened base colour)
        base_lin = srgb_to_linear(rec["pbr"]["base_color"]["srgb_default"])
        tint = tuple(min(1.0, c * 1.9 + 0.08) for c in base_lin[:3]) + (1.0,)
        if "Sheen Tint" in bsdf.inputs:
            bsdf.inputs["Sheen Tint"].default_value = tint
    if mid in BUMPS:
        s, st, stretch = BUMPS[mid]
        add_noise_bump(mat, bsdf, s, st, stretch)
    built[mid] = mat

# ---------- render swatches ----------
def render_to(path):
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("RENDERED", path)

os.makedirs(os.path.join(LAB, "renders"), exist_ok=True)
for mid in ["skin_smooth", "skin_furred_base", "nose_leather", "teeth_enamel",
            "claw_keratin", "eye", "tongue_mouth", "scar_tissue"]:
    ball.data.materials.clear()
    ball.data.materials.append(built[mid])
    if mid == "eye":
        ball.rotation_euler = (math.radians(90), 0, 0)  # +Z pole (pupil) toward camera
        cornea.hide_render = False
    else:
        ball.rotation_euler = (0, 0, 0)
        cornea.hide_render = True
    out = os.path.join(LAB, "renders", f"swatch_{mid}.png")
    if os.path.exists(out) and os.path.getsize(out) > 10000:
        print("SKIP existing", out)
        continue
    render_to(out)

# ---------- head render ----------
ball.hide_render = True
cornea.hide_render = True
bpy.ops.import_scene.gltf(filepath=HEAD_GLB)
head_objs = [o for o in bpy.context.scene.objects if o.type == "MESH" and o not in (ball, cornea, ground)]
print("HEAD OBJECTS:", [(o.name, tuple(round(d, 3) for d in o.dimensions)) for o in head_objs])
eye_gloss, e_bsdf = new_mat("eyeball_gloss")
e_bsdf.inputs["Base Color"].default_value = srgb_to_linear("#2a1c11")
e_bsdf.inputs["Roughness"].default_value = 0.06
e_bsdf.inputs["Coat Weight"].default_value = 1.0
e_bsdf.inputs["Coat Roughness"].default_value = 0.06
for o in head_objs:
    if "eyeball" in o.name.lower() or "eye" in o.name.lower():
        o.data.materials.clear(); o.data.materials.append(eye_gloss)
    else:
        o.data.materials.clear(); o.data.materials.append(built["skin_smooth"])

# frame the head: bbox centre + size
import mathutils
mins = mathutils.Vector((1e9, 1e9, 1e9)); maxs = mathutils.Vector((-1e9, -1e9, -1e9))
for o in head_objs:
    for c in o.bound_box:
        w = o.matrix_world @ mathutils.Vector(c)
        mins = mathutils.Vector(map(min, mins, w)); maxs = mathutils.Vector(map(max, maxs, w))
centre = (mins + maxs) / 2
size = max((maxs - mins).x, (maxs - mins).y, (maxs - mins).z)
print("HEAD BBOX centre", tuple(centre), "size", size)
scene.render.resolution_x = 640; scene.render.resolution_y = 640
cam.location = centre + mathutils.Vector((size * 0.85, -size * 1.9, size * 0.38))
# aim camera at centre
direction = centre - mathutils.Vector(cam.location)
cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
sun.location = centre + mathutils.Vector((1, -1, 2))
render_to(os.path.join(LAB, "renders", "head_skin_smooth.png"))

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(LAB, "swatch_scene.blend"))
print("DONE")
