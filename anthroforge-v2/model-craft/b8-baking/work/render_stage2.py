# B8 stage 2: apply baked maps to the cage, export baked GLB, render the
# baked cage and the sculpt from one fixed ortho camera for comparison.
# Run: blender -b work/bake_scene.blend --threads 2 -noaudio --python render_stage2.py
import bpy, math, time
from mathutils import Vector

ROOT = "/home/hatch/workspace/anthroforge-v2"
B8 = ROOT + "/model-craft/b8-baking"
t0 = time.time()
def log(*a): print(f"[{time.time()-t0:7.1f}s]", *a, flush=True)

scene = bpy.context.scene
low = bpy.data.objects["Low"]
high = bpy.data.objects["High"]
cage = bpy.data.objects["Cage"]
cage.hide_render = True

# ---------- applied material for the cage ----------
def tex(name, colorspace):
    # NOTE: load from disk - the stage-1 blend only kept the image datablock
    # that still had a user (the last bake target); the rest were purged on
    # save as zero-user datablocks. The PNGs on disk are the source of truth.
    img = bpy.data.images.load(f"{B8}/maps/{name}.png", check_existing=True)
    img.colorspace_settings.name = colorspace
    n = mat.node_tree.nodes.new("ShaderNodeTexImage")
    n.image = img
    return n

mat = bpy.data.materials.new("LowBaked")
nt = mat.node_tree
bsdf = nt.nodes["Principled BSDF"]
bsdf.inputs["Roughness"].default_value = 0.95

t_col = tex("orc_head_color", 'sRGB')
t_ao = tex("orc_head_ao", 'Non-Color')
mix = nt.nodes.new("ShaderNodeMixRGB")
mix.blend_type = 'MULTIPLY'
mix.inputs[0].default_value = 1.0
nt.links.new(t_col.outputs["Color"], mix.inputs[1])
nt.links.new(t_ao.outputs["Color"], mix.inputs[2])
nt.links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])

t_n = tex("orc_head_normal", 'Non-Color')
nmap = nt.nodes.new("ShaderNodeNormalMap")
nmap.inputs["Strength"].default_value = 1.0
nt.links.new(t_n.outputs["Color"], nmap.inputs["Color"])
nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])

t_cv = tex("orc_head_curvature", 'Non-Color')
ramp = nt.nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].position = 0.15
ramp.color_ramp.elements[0].color = (1.0, 1.0, 1.0, 1.0)   # concave -> rough 1.0
ramp.color_ramp.elements[1].position = 0.85
ramp.color_ramp.elements[1].color = (0.72, 0.72, 0.72, 1.0)  # convex -> 0.72
nt.links.new(t_cv.outputs["Color"], ramp.inputs["Fac"])
nt.links.new(ramp.outputs["Color"], bsdf.inputs["Roughness"])

low.data.materials.clear()
low.data.materials.append(mat)
log("LowBaked material applied (color x AO -> base, normal, curvature -> roughness)")

# ---------- export the baked cage ----------
bpy.ops.object.select_all(action='DESELECT')
low.select_set(True)
bpy.context.view_layer.objects.active = low
try:
    bpy.ops.export_scene.gltf(filepath=f"{B8}/orc_head_baked.glb",
                              export_format='GLB', use_selection=True)
    log("exported orc_head_baked.glb")
except Exception as e:
    log(f"GLB export failed (non-fatal): {e}")

# ---------- studio: flat world, one sun, ortho camera ----------
world = bpy.data.worlds.new("Studio")
scene.world = world
bg = world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (0.18, 0.18, 0.18, 1.0)
bg.inputs[1].default_value = 1.0

sun_data = bpy.data.lights.new("Sun", 'SUN')
sun_data.energy = 3.0
sun_data.angle = 0.4
sun = bpy.data.objects.new("Sun", sun_data)
scene.collection.objects.link(sun)
sun.rotation_euler = (math.radians(55), math.radians(-15), math.radians(30))

mn = Vector((1e9, 1e9, 1e9)); mx = -mn
for c in low.bound_box:
    p = low.matrix_world @ Vector(c)
    mn = Vector((min(mn.x, p.x), min(mn.y, p.y), min(mn.z, p.z)))
    mx = Vector((max(mx.x, p.x), max(mx.y, p.y), max(mx.z, p.z)))
cen = (mn + mx) / 2
height = mx.z - mn.z

cam_data = bpy.data.cameras.new("Cam")
cam_data.type = 'ORTHO'
cam_data.ortho_scale = height * 1.15
cam_data.clip_end = 1000.0
cam = bpy.data.objects.new("Cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam
dirv = Vector((0.85, 1.0, 0.38)).normalized()   # face reads toward +Y (B2 view names)
cam.location = cen + dirv * (height * 2.5)
cam.rotation_euler = (cen - cam.location).to_track_quat('-Z', 'Y').to_euler()
log(f"camera ortho_scale={cam_data.ortho_scale:.1f} centre={tuple(round(v,1) for v in cen)}")

scene.render.engine = 'CYCLES'
scene.cycles.samples = 32
scene.cycles.use_denoising = False
scene.render.resolution_x = 768
scene.render.resolution_y = 768
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'

for name, show_low in (("render_high", False), ("render_low_baked", True)):
    low.hide_render = not show_low
    high.hide_render = show_low
    scene.render.filepath = f"{B8}/renders/{name}.png"
    t = time.time()
    bpy.ops.render.render(write_still=True)
    log(f"{name}: {time.time()-t:.1f}s")

log("RENDER_STAGE2_DONE")
