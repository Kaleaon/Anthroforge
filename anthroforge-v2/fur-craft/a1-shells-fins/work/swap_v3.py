#!/usr/bin/env python3
"""A1 v3 look pass: clump-scale length map, brighter/denser fin texture,
darker shell palette, front fill light. Loads shells_fins.blend, swaps
assets in place, renders front + grazing-fins, saves the blend back."""
import bpy, math, time
import numpy as np
from mathutils import Vector

ROOT = "/home/hatch/workspace/anthroforge-v2/fur-craft/a1-shells-fins"
rng = np.random.default_rng(777)

def make_length_map_clumps(size=512, n_dots=2600):
    img = np.zeros((size, size), dtype=np.float32)
    xs = rng.random(n_dots) * size
    ys = rng.random(n_dots) * size
    lens = 0.25 + 0.75 * rng.beta(2.2, 1.4, n_dots)
    rad = rng.uniform(2.6, 4.4, n_dots)
    for x, y, L, r in zip(xs, ys, lens, rad):
        R = int(math.ceil(r)) + 1
        for dx in range(-R, R + 1):
            for dy in range(-R, R + 1):
                d2 = dx * dx + dy * dy
                if d2 > (r + 0.5) ** 2:
                    continue
                fall = max(0.0, 1.0 - math.sqrt(d2) / (r + 0.5))
                v = L * (0.70 + 0.30 * fall)
                px = int(round(x + dx)) % size
                py = int(round(y + dy)) % size
                if v > img[py, px]:
                    img[py, px] = v
    img += rng.normal(0, 0.012, img.shape).astype(np.float32)
    np.clip(img, 0, 1, out=img)
    cov = {f"{t:.3f}": float((img >= t).mean()) for t in
           (0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875)}
    print("V3 length map coverage:", cov)
    rgba = np.zeros((*img.shape, 4), dtype=np.float32)
    rgba[..., 0] = rgba[..., 1] = rgba[..., 2] = img
    rgba[..., 3] = 1.0
    return rgba

def make_fin_texture_v3(w=256, h=256, n_strands=170):
    rgba = np.zeros((h, w, 4), dtype=np.float32)
    base_col = np.array([0.60, 0.46, 0.30])
    for _ in range(n_strands):
        x0 = rng.random() * w
        wid = rng.uniform(2.0, 4.5)
        top = rng.uniform(0.35, 1.0)
        shade = rng.uniform(0.8, 1.2)
        xi0 = int(max(0, x0 - wid)); xi1 = int(min(w, x0 + wid + 1))
        for xi in range(xi0, xi1):
            prof = max(0.0, 1.0 - abs(xi - x0) / wid) ** 0.7
            for yi in range(h):
                v = yi / (h - 1)
                if v > top:
                    a = 0.0
                elif v > top - 0.18:
                    a = prof * (top - v) / 0.18
                else:
                    a = prof
                if a <= rgba[yi, xi, 3]:
                    continue
                ao = 0.55 + 0.45 * min(1.0, v / 0.35)
                tip = 1.0 + 0.35 * v
                rgba[yi, xi, :3] = base_col * shade * ao * tip
                rgba[yi, xi, 3] = a
    return rgba

def swap_image(substr, rgba):
    for img in bpy.data.images:
        if substr in img.name or substr in img.filepath:
            img.pixels.foreach_set(rgba.reshape(-1).tolist())
            img.update()
            try:
                img.save()
            except Exception as e:
                print("image save skipped:", e)
            print("swapped", img.name)
            return img
    raise RuntimeError(f"image {substr} not found")

bpy.ops.wm.open_mainfile(filepath=f"{ROOT}/shells_fins.blend")
swap_image("strand_length_map", make_length_map_clumps())
swap_image("fin_texture", make_fin_texture_v3())

ROOT2 = (0.15, 0.10, 0.058)
TIP2 = (0.40, 0.285, 0.175)
for mat in bpy.data.materials:
    if mat.name.startswith('Shell_t') and mat.use_nodes:
        t = float(mat.name.split('_t')[1].split('.')[0] + '.' +
                  mat.name.split('_t')[1].split('.')[1][:3])
        col = tuple(ROOT2[i] + (TIP2[i] - ROOT2[i]) * t for i in range(3))
        bsdf = mat.node_tree.nodes['Principled BSDF']
        bsdf.inputs['Base Color'].default_value = (*col, 1)
        print("recolored", mat.name, "t=", round(t, 3))

scene = bpy.context.scene
anchor = Vector((0.3, -0.047, 1.593))
for ob in bpy.data.objects:
    if ob.type == 'LIGHT' and ob.name.startswith('Key'):
        ob.data.energy = 100
    if ob.type == 'LIGHT' and ob.name.startswith('Fill'):
        ob.data.energy = 60
cam_front = bpy.data.objects['CamFront']
ff = bpy.data.lights.new('FrontFill', 'AREA'); ff.energy = 80; ff.size = 2.2
fo = bpy.data.objects.new('FrontFill', ff); scene.collection.objects.link(fo)
fo.location = cam_front.location
fo.rotation_euler = (anchor - fo.location).to_track_quat('-Z', 'Y').to_euler()
if scene.world:
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = (0.09, 0.09, 0.095, 1)

scene.render.engine = 'CYCLES'
scene.cycles.samples = 32
scene.cycles.use_denoising = False
scene.render.resolution_x = 512
scene.render.resolution_y = 512

ALL = ['SH8', 'SH16', 'SH24', 'SH16L60', 'FINS_B', 'FINS_ALL']
def set_vis(visible):
    for name in ALL:
        bpy.data.collections[name].hide_render = name not in visible

def render(name, cam_name, visible):
    scene.camera = bpy.data.objects[cam_name]
    set_vis(visible)
    scene.render.filepath = f"{ROOT}/renders/{name}.png"
    t0 = time.time()
    bpy.ops.render.render(write_still=True)
    print(f"V3 RENDER {name}: {time.time() - t0:.1f}s")

render('render_shells16_front_v3', 'CamFront', ['SH16'])
render('render_shells16_grazing_fins_v3', 'CamGraze', ['SH16', 'FINS_B'])
bpy.ops.wm.save_as_mainfile(filepath=f"{ROOT}/shells_fins.blend")
print("V3 DONE")
