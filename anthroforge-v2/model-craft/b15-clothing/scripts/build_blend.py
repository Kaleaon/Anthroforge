"""Build clothing_fit.blend: hm08 body + tank top (methods A and C) with one
shape key per slider state; render the briefed extremes (front, Cycles).
Run: HOME=/tmp/af_home xvfb-run -a <blender> -b --python build_blend.py
Canonical (x, y_front, z_up) -> Blender (x, -y, z)."""
import bpy, numpy as np, sys
from pathlib import Path

OUT = Path("/home/hatch/workspace/anthroforge-v2/model-craft/b15-clothing")
d = np.load(OUT/"scripts/garment_data.npz")
base, faces = d["base"], d["faces"]
g_idx, gq = d["g_idx"], d["g_faces"]
STATES = ["neutral", "strongman", "fat_v51", "gachidebu"]

def tb(P):
    Q = np.asarray(P, dtype=np.float64).copy()
    Q[:, 1] = -Q[:, 1]
    return [tuple(p) for p in Q]

def make_obj(name, verts, polys, mat):
    me = bpy.data.meshes.new(name)
    me.from_pydata(tb(verts), [], [tuple(int(x) for x in f) for f in polys])
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    if mat:
        me.materials.append(mat)
    return ob

def add_keys(ob, basis_verts, key_verts):
    ob.shape_key_add(name="Basis")
    for name, kv in key_verts.items():
        sk = ob.shape_key_add(name=name)
        for i, p in enumerate(tb(kv)):
            sk.data[i].co = p

bpy.ops.wm.read_factory_settings(use_empty=True)
mat_body = bpy.data.materials.new("Body"); mat_body.diffuse_color = (0.55, 0.53, 0.5, 1)
mat_a = bpy.data.materials.new("TankTop_A"); mat_a.diffuse_color = (0.05, 0.45, 0.5, 1)
mat_c = bpy.data.materials.new("TankTop_C"); mat_c.diffuse_color = (0.85, 0.35, 0.05, 1)
for m in (mat_body, mat_a, mat_c):
    m.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.85

body_idx = np.arange(13380)
body_faces = faces[np.all(faces < 13380, axis=1)]
body_ob = make_obj("Body_hm08", base[body_idx], body_faces - 0, mat_body)
# faces reference global ids 0..13379 == local here
add_keys(body_ob, base[body_idx], {s: (base + d[f"delta_{s}"])[body_idx] for s in STATES[1:]})

gA = {s: d[f"{s}_A"] for s in STATES}
gar_a = make_obj("TankTop_A_delta_transfer", gA["neutral"], gq, mat_a)
add_keys(gar_a, gA["neutral"], {s: gA[s] for s in STATES[1:]})

gC = {s: np.load(OUT/f"scripts/garmentC_{s}.npy") for s in STATES}
gar_c = make_obj("TankTop_C_plus_pushout", gC["neutral"], gq, mat_c)
add_keys(gar_c, gC["neutral"], {s: gC[s] for s in STATES[1:]})
gar_c.hide_render = True

# lights + camera (front view, character front faces -Y in Blender)
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
sun.data.energy = 3.0; sun.rotation_euler = (0.9, 0.2, 0.3)
bpy.context.collection.objects.link(sun)
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
cam.location = (0.0, -2.6, 0.35); cam.rotation_euler = (np.radians(88), 0, 0)
cam.data.lens = 55
bpy.context.collection.objects.link(cam)
bpy.context.scene.camera = cam
w = bpy.data.worlds.new("W"); bpy.context.scene.world = w
w.node_tree.nodes["Background"].inputs[0].default_value = (0.12, 0.12, 0.13, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 0.6

sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.samples = 32
sc.cycles.device = "CPU"
sc.render.resolution_x = 620; sc.render.resolution_y = 780
sc.render.image_settings.file_format = "PNG"

def set_state(objs, state):
    for ob in objs:
        for kb in ob.data.shape_keys.key_blocks:
            kb.value = 1.0 if kb.name == state else 0.0

for state in ["neutral", "strongman", "fat_v51"]:
    set_state([body_ob, gar_a, gar_c], state)
    gar_a.hide_render = False; gar_c.hide_render = True
    sc.render.filepath = str(OUT/f"renders/extreme_{state}_methodA.png")
    bpy.ops.render.render(write_still=True)
# comparison: fat extreme with method C garment
set_state([body_ob, gar_a, gar_c], "fat_v51")
gar_a.hide_render = True; gar_c.hide_render = False
sc.render.filepath = str(OUT/"renders/extreme_fat_v51_methodC.png")
bpy.ops.render.render(write_still=True)
# reset to neutral A for the saved file
set_state([body_ob, gar_a, gar_c], "neutral")
gar_a.hide_render = False; gar_c.hide_render = True
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"clothing_fit.blend"))
print("saved clothing_fit.blend + renders")
