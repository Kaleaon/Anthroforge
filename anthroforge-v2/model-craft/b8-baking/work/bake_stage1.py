# B8 bake stage 1: import B2 orc pair -> UV unwrap cage -> cage build ->
# selected-to-active bakes (normal / AO / vertex-colour diffuse / pointiness curvature).
# Run: blender -b --factory-startup --threads 2 -noaudio --python bake_stage1.py
import bpy, time, json
import numpy as np
from mathutils import Vector

ROOT = "/home/hatch/workspace/anthroforge-v2"
B2 = ROOT + "/model-craft/b2-retopo"
B8 = ROOT + "/model-craft/b8-baking"
RES_MAIN = 2048
RES_AO = 1024
CAGE_EXTRUDE = 2.0      # units; head height 99.15 u -> ~2.0% of height
MARGIN = 16             # px dilation on every bake

t0 = time.time()
stats = {"settings": {"res_main": RES_MAIN, "res_ao": RES_AO,
                      "cage_extrude": CAGE_EXTRUDE, "margin": MARGIN},
         "passes": {}}

def log(*a):
    print(f"[{time.time()-t0:7.1f}s]", *a, flush=True)

def names():
    return set(o.name for o in bpy.data.objects)

def import_glb(path):
    before = names()
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o.name not in before]
    assert len(new) == 1 and new[0].type == 'MESH', f"unexpected import: {new}"
    return new[0]

def world_bbox(ob):
    pts = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return mn, mx

# ---------- scene ----------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'

log("importing high sculpt ...")
high = import_glb(B2 + "/orc_head_before.glb")
high.name = "High"
log("importing retopo cage ...")
low = import_glb(B2 + "/orc_head_retopo.glb")
low.name = "Low"

hmn, hmx = world_bbox(high)
lmn, lmx = world_bbox(low)
hsize, lsize = hmx - hmn, lmx - lmn
hcen, lcen = (hmn + hmx) / 2, (lmn + lmx) / 2
log(f"high size={tuple(round(v,2) for v in hsize)} low size={tuple(round(v,2) for v in lsize)}")
log(f"centre offset high->low = {tuple(round(v,3) for v in (lcen-hcen))}")
assert (lcen - hcen).length < 1.0, "high/low frames do not line up"
stats["head_height"] = float(hsize.z)
stats["low_verts"] = len(low.data.vertices)
stats["high_tris"] = len(high.data.loop_triangles) if high.data.loop_triangles else len(high.data.polygons)
log(f"low: {len(low.data.vertices)} verts / {len(low.data.polygons)} polys; "
    f"high polys={len(high.data.polygons)}; low UV layers: {[l.name for l in low.data.uv_layers]}")

# ---------- UV unwrap the cage (it ships with none) ----------
bpy.ops.object.select_all(action='DESELECT')
low.select_set(True)
bpy.context.view_layer.objects.active = low
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=1.1519, island_margin=0.003,
                         correct_aspect=True, scale_to_bounds=False)
bpy.ops.object.mode_set(mode='OBJECT')
assert len(low.data.uv_layers) == 1, "unwrap produced no UV layer"
log(f"unwrap done: UV layer '{low.data.uv_layers[0].name}'")

# ---------- cage = cage copy pushed out along averaged vertex normals ----------
cage = low.copy()
cage.data = low.data.copy()
cage.name = "Cage"
scene.collection.objects.link(cage)
me = cage.data
nv = len(me.vertices)
acc = np.zeros((nv, 3))
for poly in me.polygons:
    n = np.array(poly.normal, dtype=np.float64) * poly.area
    for vi in poly.vertices:
        acc[vi] += n
lens = np.linalg.norm(acc, axis=1, keepdims=True)
lens[lens == 0] = 1.0
acc /= lens
co = np.empty(nv * 3)
me.vertices.foreach_get("co", co)
co = co.reshape(nv, 3) + acc * CAGE_EXTRUDE
me.vertices.foreach_set("co", co.ravel())
me.update()
log(f"cage built: {nv} verts extruded {CAGE_EXTRUDE} u along averaged normals")

# ---------- high materials ----------
vc_names = [a.name for a in high.data.color_attributes]
log(f"high vertex-colour attributes: {vc_names}")
assert vc_names, "high has no vertex colours - colour bake impossible"
vc_name = high.data.color_attributes.active_color.name if high.data.color_attributes.active_color else vc_names[0]
log(f"using vertex-colour layer '{vc_name}'")

mat_vc = bpy.data.materials.new("HighMat")
mat_vc.use_nodes = True
nt = mat_vc.node_tree
bsdf = nt.nodes["Principled BSDF"]
vcn = nt.nodes.new("ShaderNodeVertexColor")
vcn.layer_name = vc_name
nt.links.new(vcn.outputs["Color"], bsdf.inputs["Base Color"])
bsdf.inputs["Roughness"].default_value = 1.0

mat_pt = bpy.data.materials.new("HighPointiness")
mat_pt.use_nodes = True
nt2 = mat_pt.node_tree
nt2.nodes.remove(nt2.nodes["Principled BSDF"])
out = nt2.nodes["Material Output"]
geo = nt2.nodes.new("ShaderNodeNewGeometry")
ramp = nt2.nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].position = 0.35
ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
ramp.color_ramp.elements[1].position = 0.65
ramp.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)
emit = nt2.nodes.new("ShaderNodeEmission")
nt2.links.new(geo.outputs["Pointiness"], ramp.inputs["Fac"])
nt2.links.new(ramp.outputs["Color"], emit.inputs["Color"])
nt2.links.new(emit.outputs["Emission"], out.inputs["Surface"])

# ---------- low bake material (active image node is the bake target) ----------
mat_bake = bpy.data.materials.new("LowBakeMat")
mat_bake.use_nodes = True
tex_node = mat_bake.node_tree.nodes.new("ShaderNodeTexImage")
low.data.materials.clear()
low.data.materials.append(mat_bake)

rb = scene.render.bake
rb.use_selected_to_active = True
rb.use_cage = True
rb.cage_object = cage
rb.max_ray_distance = 0.0
rb.margin = MARGIN
rb.use_clear = True

def bake_pass(key, image_name, res, bake_type, samples, pass_filter=None,
              colorspace='Non-Color'):
    t = time.time()
    img = bpy.data.images.new(image_name, res, res, alpha=True)
    img.colorspace_settings.name = colorspace
    tex_node.image = img
    mat_bake.node_tree.nodes.active = tex_node
    scene.cycles.samples = samples
    kw = {"type": bake_type}
    if pass_filter:
        kw["pass_filter"] = pass_filter
    bpy.ops.object.select_all(action='DESELECT')
    high.select_set(True)
    low.select_set(True)
    bpy.context.view_layer.objects.active = low
    bpy.ops.object.bake(**kw)
    path = f"{B8}/maps/{image_name}.png"
    img.filepath_raw = path
    img.save()
    # stats from the baked pixels
    px = np.empty(res * res * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    px = px.reshape(-1, 4)
    filled = px[:, 3] > 0.0
    rgb = px[filled][:, :3]
    entry = {"file": f"maps/{image_name}.png", "res": res,
             "bake_seconds": round(time.time() - t, 1),
             "fill_fraction": round(float(filled.mean()), 4),
             "rgb_mean": [round(float(v), 4) for v in rgb.mean(axis=0)],
             "rgb_std": [round(float(v), 4) for v in rgb.std(axis=0)]}
    stats["passes"][key] = entry
    log(f"{key}: {entry['bake_seconds']}s fill={entry['fill_fraction']} "
        f"mean={entry['rgb_mean']} std={entry['rgb_std']}")
    return img

log("bake: normal (tangent) ...")
bake_pass("normal", "orc_head_normal", RES_MAIN, 'NORMAL', 1)

log("bake: diffuse colour from vertex colours ...")
bake_pass("color", "orc_head_color", RES_MAIN, 'DIFFUSE', 1,
          pass_filter={'COLOR'}, colorspace='sRGB')

log("bake: AO ...")
bake_pass("ao", "orc_head_ao", RES_AO, 'AO', 32)

log("bake: curvature (pointiness -> emit) ...")
high.data.materials.clear()
high.data.materials.append(mat_pt)
bake_pass("curvature", "orc_head_curvature", RES_MAIN, 'EMIT', 1)
high.data.materials.clear()
high.data.materials.append(mat_vc)

bpy.ops.wm.save_as_mainfile(filepath=f"{B8}/work/bake_scene.blend")
with open(f"{B8}/work/bake_stats.json", "w") as f:
    json.dump(stats, f, indent=2)
log("BAKE_STAGE1_DONE")
