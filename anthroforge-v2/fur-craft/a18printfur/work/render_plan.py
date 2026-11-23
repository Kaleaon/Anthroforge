#!/usr/bin/env python3
"""Render fur-plan zone maps (emission vertex colours, ortho) + arrow projections."""
import bpy, numpy as np, json
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

W = "/home/hatch/workspace/anthroforge-v2/fur-craft/a18printfur/work/"
D = np.load(W + "plan_data.npz")
OBJS = ["TissueHead", "Jaw", "Ear_L", "Ear_R", "NoseLeather"]

PILE_RGB = {0: (0.16, 0.16, 0.16), 1: (0.30, 0.68, 0.95), 2: (0.20, 0.75, 0.40),
            3: (0.98, 0.78, 0.15), 4: (0.92, 0.30, 0.20)}
COL_RGB = {0: (0.13, 0.11, 0.10), 1: (0.58, 0.45, 0.30), 2: (0.96, 0.90, 0.76),
           3: (0.25, 0.22, 0.20), 4: (0.88, 0.62, 0.58)}
NEUTRAL = (0.78, 0.80, 0.83); NEUTRAL_NOSE = (0.35, 0.36, 0.38)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.samples = 16
scene.cycles.use_denoising = False
scene.render.resolution_x = scene.render.resolution_y = 900
scene.view_settings.view_transform = "Standard"
scene.display_settings.display_device = "sRGB"
world = bpy.data.worlds.new("W"); scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (1, 1, 1, 1)
world.node_tree.nodes["Background"].inputs[1].default_value = 1.0

mat = bpy.data.materials.new("planmat"); mat.use_nodes = True
nt = mat.node_tree; nt.nodes.clear()
em = nt.nodes.new("ShaderNodeEmission")
vc = nt.nodes.new("ShaderNodeVertexColor"); vc.layer_name = "plan"
out = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(vc.outputs["Color"], em.inputs["Color"])
nt.links.new(em.outputs["Emission"], out.inputs["Surface"])

meshes = {}
for name in OBJS:
    pos, tris = D[f"{name}_pos"], D[f"{name}_tris"]
    me = bpy.data.meshes.new(name)
    me.from_pydata(pos.tolist(), [], tris.tolist()); me.update()
    attr = me.color_attributes.new(name="plan", type="BYTE_COLOR", domain="POINT")
    ob = bpy.data.objects.new(name, me); ob.data.materials.append(mat)
    bpy.context.collection.objects.link(ob)
    meshes[name] = (ob, attr)

def set_colours(mode):
    for name in OBJS:
        ob, attr = meshes[name]
        if mode == "neutral":
            rgb = NEUTRAL_NOSE if name == "NoseLeather" else NEUTRAL
            cols = [rgb] * len(D[f"{name}_pos"])
        else:
            table = PILE_RGB if mode == "pile" else COL_RGB
            key = "pile" if mode == "pile" else "colour"
            cols = [table[int(c)] for c in D[f"{name}_{key}"]]
        for i, c in enumerate(cols):
            attr.data[i].color = (*c, 1.0)

VIEWS = {  # name: (cam location, ortho scale)
    "front": (Vector((0, 3, 0.02)), 1.25), "side": (Vector((3, 0, 0.02)), 1.25),
    "back": (Vector((0, -3, 0.02)), 1.25), "top": (Vector((0, 0.02, 3)), 1.35)}
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
bpy.context.collection.objects.link(cam); scene.camera = cam
cam.data.type = "ORTHO"
target = Vector((0, 0, 0.0))

def render(mode, view):
    loc, scale = VIEWS[view]
    cam.location = loc; cam.data.ortho_scale = scale
    direction = target - loc
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    bpy.context.view_layer.update()
    scene.render.filepath = f"{W}raw_{mode}_{view}.png"
    bpy.ops.render.render(write_still=True)
    return loc

def arrows_for(loc):
    """Project fur-direction arrows for one view; returns pixel-space list."""
    arr = []
    for name in OBJS:
        if name == "NoseLeather": continue
        pos, nrm, flow = D[f"{name}_pos"], D[f"{name}_nrm"], D[f"{name}_flow"]
        pile = D[f"{name}_pile"]
        to_cam = np.array(loc)[None, :] - pos
        facing = np.einsum("ij,ij->i", nrm, to_cam / (np.linalg.norm(to_cam, axis=1, keepdims=True) + 1e-12))
        idx = np.where(facing > 0.12)[0]
        cap = {"TissueHead": 34, "Jaw": 26, "Ear_L": 20, "Ear_R": 20}.get(name, 30)
        if len(idx) > cap: idx = idx[np.linspace(0, len(idx) - 1, cap).astype(int)]
        for i in idx:
            p = Vector(pos[i]); q = p + Vector(flow[i] * 0.095)
            a = world_to_camera_view(scene, cam, p); b = world_to_camera_view(scene, cam, q)
            arr.append([a.x * 900, (1 - a.y) * 900, b.x * 900, (1 - b.y) * 900, int(pile[i])])
    return arr

arrow_data = {}
for mode, views in (("colour", ["front", "side", "back"]),):
    set_colours(mode)
    for v in views:
        loc = render(mode, v)
        print("rendered", mode, v)
        if mode == "neutral":
            arrow_data[v] = arrows_for(loc)
if arrow_data:
    json.dump(arrow_data, open(W + "arrows.json", "w"))
    print("arrows:", {k: len(v) for k, v in arrow_data.items()})
