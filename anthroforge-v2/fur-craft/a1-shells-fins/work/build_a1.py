#!/usr/bin/env python3
"""A1 shells+fins prototype: build shell-stack fur + fins on a patch of the
Bara Wolf body, render measured configs, dump stats JSON.

Run: blender -b --factory-startup -noaudio --python build_a1.py
"""
import bpy, math, time, json, sys
import numpy as np
from mathutils import Vector

ROOT = "/home/hatch/workspace/anthroforge-v2/fur-craft/a1-shells-fins"
SRC = "/home/hatch/workspace/stick-figure-avatar/furry/bara_wolf_base.blend"
rng = np.random.default_rng(20261112)

stats = {"source": SRC}

# ---------------------------------------------------------------- textures
def make_length_map(size=512, n_dots=14000):
    """Tileable strand-length map: each pixel = length (0..1) of the longest
    strand disc covering it. Strand survives at shell height t iff v >= t."""
    img = np.zeros((size, size), dtype=np.float32)
    xs = rng.random(n_dots) * size
    ys = rng.random(n_dots) * size
    # length distribution: skew long (most strands reach >0.6), some short
    lens = 0.25 + 0.75 * rng.beta(2.2, 1.4, n_dots)
    rad = rng.uniform(1.1, 2.1, n_dots)
    for x, y, L, r in zip(xs, ys, lens, rad):
        R = int(math.ceil(r)) + 1
        for dx in range(-R, R + 1):
            for dy in range(-R, R + 1):
                d2 = dx * dx + dy * dy
                if d2 > (r + 0.5) ** 2:
                    continue
                fall = max(0.0, 1.0 - math.sqrt(d2) / (r + 0.5))
                v = L * (0.75 + 0.25 * fall)
                px = int(round(x + dx)) % size
                py = int(round(y + dy)) % size
                if v > img[py, px]:
                    img[py, px] = v
    img += rng.normal(0, 0.012, img.shape).astype(np.float32)  # de-band jitter
    np.clip(img, 0, 1, out=img)
    cov = {f"{t:.3f}": float((img >= t).mean()) for t in
           (0.0, 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875, 1.0)}
    return img, cov, n_dots

def make_fin_texture(w=256, h=256, n_strands=110):
    """Side-profile fin texture: vertical strand streaks, each with its own
    max height, root-darkened, tips fade out. RGBA float array."""
    rgba = np.zeros((h, w, 4), dtype=np.float32)
    base_col = np.array([0.42, 0.31, 0.20])
    for _ in range(n_strands):
        x0 = rng.random() * w
        wid = rng.uniform(1.0, 3.2)
        top = rng.uniform(0.35, 1.0)          # strand max height (v)
        shade = rng.uniform(0.8, 1.2)
        xi0 = int(max(0, x0 - wid)); xi1 = int(min(w, x0 + wid + 1))
        for xi in range(xi0, xi1):
            prof = max(0.0, 1.0 - abs(xi - x0) / wid) ** 0.7
            colw = (xi + 0.5) / w
            for yi in range(h):
                v = yi / (h - 1)              # 0 root -> 1 tip
                if v > top:
                    a = 0.0
                elif v > top - 0.18:
                    a = prof * (top - v) / 0.18
                else:
                    a = prof
                if a <= rgba[yi, xi, 3]:
                    continue
                ao = 0.45 + 0.55 * min(1.0, v / 0.35)     # root darkening
                tip = 1.0 + 0.35 * v                       # tips lighten
                rgba[yi, xi, :3] = base_col * shade * ao * tip
                rgba[yi, xi, 3] = a
    # tile horizontally: mirror-wrap the right edge onto the left softly
    return rgba

def save_image(name, arr, colorspace):
    h, w = arr.shape[:2]
    img = bpy.data.images.new(name, w, h, alpha=True, float_buffer=False)
    flat = arr.reshape(-1)
    img.pixels.foreach_set(flat.tolist())
    img.colorspace_settings.name = colorspace
    img.filepath_raw = f"{ROOT}/work/{name}.png"
    img.file_format = 'PNG'
    img.save()
    return img

len_arr, coverage, n_dots = make_length_map()
# to RGBA
len_rgba = np.zeros((*len_arr.shape, 4), dtype=np.float32)
len_rgba[..., 0] = len_rgba[..., 1] = len_rgba[..., 2] = len_arr
len_rgba[..., 3] = 1.0
len_img = save_image("strand_length_map", len_rgba, 'Non-Color')
fin_rgba = make_fin_texture()
fin_img = save_image("fin_texture", fin_rgba, 'sRGB')
stats["length_map"] = {"dots": n_dots, "coverage_by_height": coverage}

# ---------------------------------------------------------------- patch
bpy.ops.wm.open_mainfile(filepath=SRC)
# opening the source file wiped the generated images from memory; reload
# them from the PNGs saved above
len_img = bpy.data.images.load(f"{ROOT}/work/strand_length_map.png")
len_img.colorspace_settings.name = 'Non-Color'
fin_img = bpy.data.images.load(f"{ROOT}/work/fin_texture.png")
fin_img.colorspace_settings.name = 'sRGB'
src_ob = bpy.data.objects['BaraWolfBody']
me = src_ob.data
me.calc_loop_triangles()
V = np.empty(len(me.vertices) * 3)
me.vertices.foreach_get('co', V); V = V.reshape(-1, 3)
N = np.array([tuple(v.normal) for v in me.vertices], dtype=np.float64)
tris = np.empty(len(me.loop_triangles) * 3, dtype=np.int32)
me.loop_triangles.foreach_get('vertices', tris); T = tris.reshape(-1, 3)
# per-vertex UV from first loop that uses it
uv_layer = me.uv_layers[0]
loop_v = np.empty(len(me.loops), dtype=np.int32)
me.loops.foreach_get('vertex_index', loop_v)
UV = np.zeros((len(me.vertices), 2))
seen = np.zeros(len(me.vertices), bool)
for li, vi in enumerate(loop_v):
    if not seen[vi]:
        UV[vi] = uv_layer.data[li].uv
        seen[vi] = True

target = np.array([0.30, -0.05, 1.60])
ai = int(np.argmin(np.linalg.norm(V - target, axis=1)))
anchor = V[ai]
C = V[T].mean(1)
RAD = 0.17
sel = np.linalg.norm(C - anchor, axis=1) < RAD
pT = T[sel]
used = np.unique(pT)
remap = {int(v): i for i, v in enumerate(used)}
pV = V[used]; pN = N[used]; pUV = UV[used]
pF = [[remap[int(a)] for a in f] for f in pT]
patch_area = 0.0
for f in pF:
    a, b, c = pV[f[0]], pV[f[1]], pV[f[2]]
    patch_area += 0.5 * np.linalg.norm(np.cross(b - a, c - a))
avg_n = pN.mean(0); avg_n /= np.linalg.norm(avg_n)
# PLANAR patch UVs (v2): the source Tripo UVs are heavily islanded and the
# v1 per-vertex UVs streaked black seams across the shells (see
# renders/evidence_uv_seams_overexposed.png). For a small patch, project
# onto the patch tangent plane instead: seam-free, uniform texel density,
# UV in metres so the mapping scale is exactly 1/TILE_M.
_t1 = np.cross(avg_n, [0.0, 0.0, 1.0])
if np.linalg.norm(_t1) < 0.1:
    _t1 = np.cross(avg_n, [1.0, 0.0, 0.0])
_t1 /= np.linalg.norm(_t1)
_t2 = np.cross(avg_n, _t1)
rel = pV - anchor
pUV = np.stack([rel @ _t1, rel @ _t2], axis=1)
stats["patch"] = {"anchor_src_vertex": ai, "anchor": anchor.round(3).tolist(),
                  "radius_m": RAD, "verts": int(len(pV)), "tris": int(len(pF)),
                  "area_m2": round(float(patch_area), 4),
                  "avg_normal": avg_n.round(3).tolist(),
                  "uv_mode": "planar projection on patch tangent plane (metres)"}
print("PATCH", stats["patch"])

# texture tiling: one length-map tile covers TILE_M x TILE_M of surface
TILE_M = 0.068
tiles_across = (2 * RAD) / TILE_M
scale_uv = np.array([1.0 / TILE_M, 1.0 / TILE_M])
dots_per_cm2 = n_dots / (TILE_M * 100) ** 2
stats["tiling"] = {"tile_world_m": TILE_M, "tiles_across_patch": round(float(tiles_across), 2),
                   "uv_scale": scale_uv.round(2).tolist(),
                   "strand_dots_per_cm2": round(float(dots_per_cm2), 1)}
print("TILING", stats["tiling"])

# ---------------------------------------------------------------- scene reset
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
for coll in list(bpy.data.collections):
    if coll.name != 'Master Collection':
        bpy.data.collections.remove(coll)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 24
scene.cycles.device = 'CPU'
scene.cycles.use_denoising = False
scene.cycles.transparent_max_bounces = 30
scene.cycles.max_bounces = 12
scene.render.resolution_x = 448
scene.render.resolution_y = 448
scene.render.film_transparent = False
world = bpy.data.worlds.new('W'); scene.world = world
world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (0.055, 0.055, 0.06, 1)
world.node_tree.nodes['Background'].inputs[1].default_value = 1.0
light = bpy.data.lights.new('Key', 'AREA'); light.energy = 160; light.size = 1.6
lo = bpy.data.objects.new('Key', light); scene.collection.objects.link(lo)
lo.location = anchor + avg_n * 1.1 + Vector((0.35, -0.3, 0.45))
lo.rotation_euler = (Vector(anchor) - lo.location).to_track_quat('-Z', 'Y').to_euler()
fill = bpy.data.lights.new('Fill', 'AREA'); fill.energy = 45; fill.size = 2.0
fo = bpy.data.objects.new('Fill', fill); scene.collection.objects.link(fo)
fo.location = anchor - avg_n * 0.6 + Vector((-0.5, 0.3, 0.1))
fo.rotation_euler = (Vector(anchor) - fo.location).to_track_quat('-Z', 'Y').to_euler()

def get_coll(name):
    c = bpy.data.collections.new(name)
    scene.collection.children.link(c)
    return c

def mesh_obj(name, verts, faces, uvs, coll, material=None):
    m = bpy.data.meshes.new(name)
    m.from_pydata([tuple(v) for v in verts], [], faces)
    m.update()
    uvl = m.uv_layers.new(name='UVMap')
    for loop in m.loops:
        uvl.data[loop.index].uv = tuple(uvs[loop.vertex_index])
    ob = bpy.data.objects.new(name, m)
    coll.objects.link(ob)
    if material:
        m.materials.append(material)
    return ob

ROOT_COL = (0.30, 0.205, 0.125)
TIP_COL = (0.56, 0.43, 0.29)

def skin_material():
    mat = bpy.data.materials.new('SkinUndercoat')
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = (0.16, 0.11, 0.075, 1)
    bsdf.inputs['Roughness'].default_value = 1.0
    return mat

def shell_material(t):
    mat = bpy.data.materials.new(f'Shell_t{t:.3f}')
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes['Principled BSDF']
    bsdf.inputs['Roughness'].default_value = 0.92
    col = tuple(ROOT_COL[i] + (TIP_COL[i] - ROOT_COL[i]) * t for i in range(3))
    bsdf.inputs['Base Color'].default_value = (*col, 1)
    tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = len_img
    tex.interpolation = 'Linear'
    mapping = nt.nodes.new('ShaderNodeMapping')
    mapping.inputs['Scale'].default_value = (scale_uv[0], scale_uv[1], 1.0)
    coord = nt.nodes.new('ShaderNodeTexCoord')
    gt = nt.nodes.new('ShaderNodeMath'); gt.operation = 'GREATER_THAN'
    gt.inputs[1].default_value = t + 1e-4
    transp = nt.nodes.new('ShaderNodeBsdfTransparent')
    mix = nt.nodes.new('ShaderNodeMixShader')
    out = nt.nodes['Material Output']
    nt.links.new(coord.outputs['UV'], mapping.inputs['Vector'])
    nt.links.new(mapping.outputs['Vector'], tex.inputs['Vector'])
    nt.links.new(tex.outputs['Color'], gt.inputs[0])
    nt.links.new(gt.outputs['Value'], mix.inputs['Fac'])
    nt.links.new(transp.outputs['BSDF'], mix.inputs[1])
    nt.links.new(bsdf.outputs['BSDF'], mix.inputs[2])
    nt.links.new(mix.outputs['Shader'], out.inputs['Surface'])
    return mat

def fin_material():
    mat = bpy.data.materials.new('FinMat')
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes['Principled BSDF']
    bsdf.inputs['Roughness'].default_value = 0.95
    tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = fin_img
    transp = nt.nodes.new('ShaderNodeBsdfTransparent')
    mix = nt.nodes.new('ShaderNodeMixShader')
    out = nt.nodes['Material Output']
    nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    nt.links.new(tex.outputs['Alpha'], mix.inputs['Fac'])
    nt.links.new(transp.outputs['BSDF'], mix.inputs[1])
    nt.links.new(bsdf.outputs['BSDF'], mix.inputs[2])
    nt.links.new(mix.outputs['Shader'], out.inputs['Surface'])
    return mat

# base patch
base_coll = get_coll('BASE')
mesh_obj('PatchSkin', pV, pF, pUV, base_coll, skin_material())

def build_shells(coll_name, n_layers, fur_len):
    coll = get_coll(coll_name)
    tris = 0
    for i in range(1, n_layers):
        t = i / (n_layers - 1)
        off = pV + pN * (fur_len * t)
        ob = mesh_obj(f'{coll_name}_s{i:02d}', off, pF, pUV, coll, shell_material(t))
        tris += len(pF)
    return {"layers_total_incl_base": n_layers, "shells_above_base": n_layers - 1,
            "fur_length_mm": fur_len * 1000, "step_mm": fur_len / (n_layers - 1) * 1000,
            "shell_tris": tris, "total_tris_incl_base": tris + len(pF)}

config_stats = {}
config_stats['SH8'] = build_shells('SH8', 8, 0.025)
config_stats['SH16'] = build_shells('SH16', 16, 0.025)
config_stats['SH24'] = build_shells('SH24', 24, 0.025)
config_stats['SH16L60'] = build_shells('SH16L60', 16, 0.060)
stats["configs"] = config_stats

# ---------------------------------------------------------------- fins
edge_count = {}
for f in pF:
    for a, b in ((f[0], f[1]), (f[1], f[2]), (f[2], f[0])):
        key = (min(a, b), max(a, b))
        edge_count[key] = edge_count.get(key, 0) + 1
boundary = [e for e, c in edge_count.items() if c == 1]
all_edges = list(edge_count.keys())

def build_fins(name, edges, fur_len):
    coll = get_coll(name)
    verts, faces, uvs = [], [], []
    for (a, b) in edges:
        i0 = len(verts)
        verts += [tuple(pV[a]), tuple(pV[b]),
                  tuple(pV[b] + pN[b] * fur_len), tuple(pV[a] + pN[a] * fur_len)]
        faces.append([i0, i0 + 1, i0 + 2, i0 + 3])
        uvs += [(0, 0), (1, 0), (1, 1), (0, 1)]
    ob = mesh_obj(name, np.array(verts), faces, np.array(uvs), coll, fin_material())
    return {"fins": len(edges), "tris": len(edges) * 2, "fur_length_mm": fur_len * 1000}

stats["fins_boundary"] = build_fins('FINS_B', boundary, 0.025)
stats["fins_all"] = build_fins('FINS_ALL', all_edges, 0.025)
print("FINS", stats["fins_boundary"], stats["fins_all"])

# ---------------------------------------------------------------- cameras
def make_cam(name, loc, target_pt):
    cam = bpy.data.cameras.new(name); cam.lens = 55
    ob = bpy.data.objects.new(name, cam); scene.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = (Vector(target_pt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    return ob

A = Vector(anchor); Nv = Vector(avg_n)
tangent = Vector((0, 0, 1)).cross(Nv)
if tangent.length < 0.1:
    tangent = Vector((1, 0, 0)).cross(Nv)
tangent.normalize()
cam_front = make_cam('CamFront', A + Nv * 0.52, A + Nv * 0.01)
cam_graze = make_cam('CamGraze', A + tangent * 0.46 + Nv * 0.085, A + Nv * 0.012)

ALL_COLLS = ['SH8', 'SH16', 'SH24', 'SH16L60', 'FINS_B', 'FINS_ALL']
def set_vis(visible):
    for name in ALL_COLLS:
        bpy.data.collections[name].hide_render = name not in visible

def render(name, cam, visible):
    scene.camera = cam
    set_vis(visible)
    scene.render.filepath = f"{ROOT}/renders/{name}.png"
    t0 = time.time()
    bpy.ops.render.render(write_still=True)
    dt = time.time() - t0
    print(f"RENDER {name}: {dt:.1f}s visible={visible}")
    return round(dt, 1)

render_stats = {}
render_stats['shells16_front'] = render('render_shells16_front', cam_front, ['SH16'])
render_stats['shells8_front'] = render('render_shells8_front', cam_front, ['SH8'])
render_stats['shells16_grazing_nofins'] = render('render_shells16_grazing_nofins', cam_graze, ['SH16'])
render_stats['shells16_grazing_fins'] = render('render_shells16_grazing_fins', cam_graze, ['SH16', 'FINS_B'])
render_stats['shells16_ruff60_front'] = render('render_shells16_ruff60_front', cam_front, ['SH16L60'])
stats["render_seconds_448x448_24spp"] = render_stats
stats["note_render_configs"] = ("SH24 and FINS_ALL are built in the .blend "
    "but were not rendered in this pass (shared-VM CPU contention); their "
    "costs follow from the measured per-shell figures.")

# leave the hero config visible, save
set_vis(['SH16', 'FINS_B'])
scene.camera = cam_front
bpy.ops.wm.save_as_mainfile(filepath=f"{ROOT}/shells_fins.blend")
print("STATS_JSON_BEGIN")
print(json.dumps(stats, indent=1, default=str))
print("STATS_JSON_END")
