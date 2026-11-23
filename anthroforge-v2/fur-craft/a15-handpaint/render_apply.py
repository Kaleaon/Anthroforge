#!/usr/bin/env python3
"""Apply the painted pelt to a 'back region' proxy: a subdivided sheet
domed across its width (the ridge of a canine back, spine along the
centre, coat spilling to both flanks), textured with the A15 diffuse +
roughness pair, and rendered in Cycles from two distances."""
import bpy
import math
from mathutils import Vector

DIR = "/home/hatch/workspace/anthroforge-v2/fur-craft/a15-handpaint"

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.samples = 16
scene.cycles.use_denoising = False
scene.cycles.device = "CPU"
scene.render.resolution_x = 768
scene.render.resolution_y = 576
scene.view_settings.view_transform = "AgX"
scene.view_settings.exposure = -0.7

# ---- back-region sheet ---------------------------------------------------
N = 128
SIZE = 2.2
verts, uvs, faces = [], [], []
for j in range(N + 1):
    for i in range(N + 1):
        x = -SIZE / 2 + SIZE * i / N
        y = -SIZE / 2 + SIZE * j / N
        ridge = math.cos(max(-1, min(1, x / (SIZE / 2))) * math.pi / 2) ** 1.1
        taper = 0.93 + 0.07 * math.cos(y / (SIZE / 2) * math.pi / 2)
        z = 0.34 * ridge * taper - 0.03 * (y / (SIZE / 2)) ** 2
        verts.append((x, y, z))
        uvs.append((i / N, j / N))
for j in range(N):
    for i in range(N):
        a = j * (N + 1) + i
        b = a + 1
        c = a + N + 1
        d = c + 1
        faces.append((a, c, b))
        faces.append((b, c, d))
mesh = bpy.data.meshes.new("BackRegion")
mesh.from_pydata(verts, [], faces)
mesh.update()
uvlayer = mesh.uv_layers.new(name="UVMap")
for loop in mesh.loops:
    uvlayer.data[loop.index].uv = uvs[loop.vertex_index]
obj = bpy.data.objects.new("BackRegion", mesh)
bpy.context.collection.objects.link(obj)
for poly in mesh.polygons:
    poly.use_smooth = True

# ---- material: painted diffuse + painted roughness + bump from diffuse ---
mat = bpy.data.materials.new("CanineBackPelt")
nt = mat.node_tree
bsdf = nt.nodes["Principled BSDF"]
tex_d = nt.nodes.new("ShaderNodeTexImage")
tex_d.image = bpy.data.images.load(f"{DIR}/canine_back_diffuse.png")
tex_d.image.colorspace_settings.name = "sRGB"
tex_r = nt.nodes.new("ShaderNodeTexImage")
tex_r.image = bpy.data.images.load(f"{DIR}/canine_back_roughness.png")
tex_r.image.colorspace_settings.name = "Non-Color"
tex_b = nt.nodes.new("ShaderNodeTexImage")
tex_b.image = bpy.data.images.load(f"{DIR}/canine_back_diffuse.png")
tex_b.image.colorspace_settings.name = "Non-Color"
bump = nt.nodes.new("ShaderNodeBump")
bump.inputs["Strength"].default_value = 0.25
bump.inputs["Distance"].default_value = 0.012
nt.links.new(tex_d.outputs["Color"], bsdf.inputs["Base Color"])
nt.links.new(tex_r.outputs["Color"], bsdf.inputs["Roughness"])
nt.links.new(tex_b.outputs["Color"], bump.inputs["Height"])
nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
def set_in(node, name, value):
    if name in node.inputs:
        node.inputs[name].default_value = value

set_in(bsdf, "Specular IOR Level", 0.35)
set_in(bsdf, "Sheen Weight", 0.18)
set_in(bsdf, "Sheen Roughness", 0.55)
set_in(bsdf, "Sheen Color", (0.55, 0.42, 0.28, 1.0))
set_in(bsdf, "Sheen Tint", (0.55, 0.42, 0.28, 1.0))
obj.data.materials.append(mat)

# ---- ground shadow catcher ----------------------------------------------
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, -0.42))
ground = bpy.context.active_object
gmat = bpy.data.materials.new("Ground")
gmat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.16, 0.15, 0.14, 1)
gmat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 1.0
ground.data.materials.append(gmat)

# ---- lights ---------------------------------------------------------------
def area(name, loc, rot, size, energy, color):
    ld = bpy.data.lights.new(name, "AREA")
    ld.shape = "RECTANGLE"
    ld.size = size
    ld.energy = energy
    ld.color = color
    o = bpy.data.objects.new(name, ld)
    o.location = loc
    o.rotation_euler = rot
    bpy.context.collection.objects.link(o)

area("Key", (-1.6, -1.2, 2.4), (math.radians(38), math.radians(-18), math.radians(-32)), 2.6, 330, (1.0, 0.93, 0.82))
area("Fill", (2.0, -0.4, 1.0), (math.radians(62), math.radians(20), math.radians(55)), 3.2, 85, (0.82, 0.88, 1.0))
world = bpy.data.worlds.new("W")
scene.world = world
world.node_tree.nodes["Background"].inputs[0].default_value = (0.03, 0.03, 0.035, 1)
world.node_tree.nodes["Background"].inputs[1].default_value = 1.0

# ---- cameras ---------------------------------------------------------------
cam_data = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_data)
bpy.context.collection.objects.link(cam)
scene.camera = cam

def aim(cam_obj, loc, target):
    cam_obj.location = loc
    d = Vector(target) - Vector(loc)
    cam_obj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()

aim(cam, (1.45, -1.85, 1.30), (0, 0.05, 0.10))
cam_data.lens = 42
scene.render.filepath = f"{DIR}/render_back_region.png"
bpy.ops.render.render(write_still=True)

aim(cam, (0.62, -0.95, 0.72), (0.05, 0.10, 0.26))
cam_data.lens = 55
scene.render.filepath = f"{DIR}/render_back_closeup.png"
bpy.ops.render.render(write_still=True)
print("RENDERS DONE")
