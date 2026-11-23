#!/usr/bin/env python3
"""B14 definitive render pass.

Fixes folded in:
- Ears mount at the head v3's REAL ear sites (its hidden Ear_L/R sit at
  (+/-0.314, -0.166, 0.238); the tissue carries an ear-base nub there --
  the 'fin' in earlier closeups). Guessed fractions left the nub exposed.
- Wolf facing from ToeBase-vs-Foot skin-weight clusters (the Foot
  cluster alone points at the ground, not forward).
- Lineup lighting/framing redone (previous pass blew out).
"""
import bpy, math, os, json
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
PARTS = os.path.join(ROOT, "parts")
REND = os.path.join(ROOT, "renders")
WORK = os.path.join(ROOT, "work")
FIT = os.path.join(WORK, "fit")
HEAD_GLB = os.path.expanduser("~/workspace/anthroforge-v2/base-head-v3/neutral_base_head_v3.glb")
WOLF = os.path.expanduser("~/workspace/bodies-3d/parts-library/existing-haul/wolf-rigged-ccby/scene.gltf")

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 24
scene.cycles.device = 'CPU'
scene.render.resolution_x = 680
scene.render.resolution_y = 680
scene.view_settings.view_transform = 'Filmic'
scene.view_settings.look = 'Medium Contrast'
world = bpy.data.worlds.new("W")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.16, 0.16, 0.17, 1)
world.node_tree.nodes["Background"].inputs[1].default_value = 0.45

def add_light(name, loc, energy, size=2.0):
    ld = bpy.data.lights.new(name, 'AREA')
    ld.energy = energy; ld.shape = 'DISK'; ld.size = size
    lo = bpy.data.objects.new(name, ld)
    bpy.context.collection.objects.link(lo)
    lo.location = loc
    return lo

def add_sun(name, rot, energy=3.0):
    ld = bpy.data.lights.new(name, 'SUN')
    ld.energy = energy
    lo = bpy.data.objects.new(name, ld)
    bpy.context.collection.objects.link(lo)
    lo.rotation_euler = rot
    return lo

def aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()

def add_camera(name, loc, target, lens=55):
    cd = bpy.data.cameras.new(name)
    co = bpy.data.objects.new(name, cd)
    bpy.context.collection.objects.link(co)
    co.location = loc
    aim(co, target)
    cd.lens = lens
    return co

def render(cam, path):
    scene.camera = cam
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("RENDERED", path, flush=True)

def world_stl(obj, path):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    me = bpy.data.meshes.new_from_object(ev)
    me.transform(obj.matrix_world)
    tmp = bpy.data.objects.new("tmp_stl", me)
    bpy.context.collection.objects.link(tmp)
    bpy.ops.object.select_all(action='DESELECT')
    tmp.select_set(True)
    bpy.context.view_layer.objects.active = tmp
    bpy.ops.wm.stl_export(filepath=path, export_selected_objects=True)
    bpy.data.objects.remove(tmp, do_unlink=True)
    bpy.data.meshes.remove(me)

def bbox_of(objs):
    mn = Vector((1e9,) * 3); mx = Vector((-1e9,) * 3)
    for o in objs:
        if o.type != 'MESH':
            continue
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            mn = Vector(map(min, mn, w)); mx = Vector(map(max, mx, w))
    return mn, mx

def import_part(fname):
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(PARTS, fname))
    new = [o for o in bpy.context.scene.objects if o not in before]
    roots = [o for o in new if o.parent is None]
    return new, roots

# ================================================================ head stage
bpy.ops.import_scene.gltf(filepath=HEAD_GLB)
head_objs = list(bpy.context.scene.objects)
for o in head_objs:
    if o.name.startswith("Ear_L") or o.name.startswith("Ear_R"):
        o.hide_render = True
        o.hide_viewport = True
tissue = next(o for o in head_objs if o.name == "TissueHead")
nose = next((o for o in head_objs if o.name == "NoseLeather"), None)
hmn, hmx = bbox_of([tissue])
HC = (hmn + hmx) / 2
HS = hmx - hmn
facing = 1.0
if nose:
    nc = nose.matrix_world @ (sum((Vector(c) for c in nose.bound_box), Vector()) / 8)
    facing = 1.0 if nc.y > HC.y else -1.0
earR_objs, earR_roots = import_part("ear_canine_upright_R.glb")
earL_objs, earL_roots = import_part("ear_canine_upright_L.glb")
horn_objs, horn_roots = import_part("horns_curved_pair.glb")
EAR_S, HORN_S = 3.3, 3.0
for r in earR_roots + earL_roots:
    r.scale = (EAR_S, EAR_S, EAR_S)
for r in horn_roots:
    r.scale = (HORN_S, HORN_S, HORN_S)
for nm, off, en in (("hkey", (-0.45, 0, 0.35), 240), ("hfill", (0.5, 0, 0.1), 80),
                    ("hrim", (0.1, 0, 0.55), 200)):
    L = add_light(nm, HC + Vector((off[0], facing * (abs(off[0]) * 0.4 - 0.55), off[2])), en, 1.2)
    aim(L, HC)
placements = {}
# REAL ear sites on this base: v3 Ear_L/R centres (+/-0.314, -0.166, 0.238)
for tag, roots, side in (("R", earR_roots, 1), ("L", earL_roots, -1)):
    pos = Vector((side * 0.295, -0.150, 0.185))
    rot = (math.radians(-10), side * math.radians(22), side * math.radians(-21))
    for r in roots:
        r.location = pos
        r.rotation_euler = rot
    placements[f"ear.{tag}"] = {"location": [round(v, 4) for v in pos],
                                "rotation_euler_deg": [round(math.degrees(a), 1) for a in rot],
                                "scale": EAR_S,
                                "site": "base head v3 native ear site (hidden Ear_L/R centre +/-0.314,-0.166,0.238)"}
for r in horn_roots:
    r.location = Vector((HC.x, HC.y - facing * HS.y * 0.10, HC.z + HS.z * 0.44))
    r.rotation_euler = (math.radians(-8), 0, 0)
placements["head.top horns"] = {"location": [round(v, 4) for v in r.location], "scale": HORN_S}
bpy.context.view_layer.update()
for tag, objs, key in (("ear_pair", earR_objs + earL_objs, "ear"), ("horns", horn_objs, "horn")):
    for o in objs:
        if o.type == 'MESH' and key in o.name.lower():
            world_stl(o, os.path.join(FIT, f"{tag}_{o.name}.stl"))
for o in head_objs + earR_objs + earL_objs + horn_objs:
    o.hide_render = True

# ================================================================ wolf tail stage
before = set(bpy.context.scene.objects)
bpy.ops.import_scene.gltf(filepath=WOLF)
wolf_objs = [o for o in bpy.context.scene.objects if o not in before]
body = max((o for o in wolf_objs if o.type == 'MESH'), key=lambda o: len(o.data.vertices))
dg = bpy.context.evaluated_depsgraph_get()
ev = body.evaluated_get(dg)
me = bpy.data.meshes.new_from_object(ev)
me.transform(body.matrix_world)
verts = [v.co.copy() for v in me.vertices]

def landmark(substrs, min_w=0.4):
    idxs = {g.index for g in body.vertex_groups if any(s in g.name for s in substrs)}
    pts = []
    for v in body.data.vertices:
        w = max((ge.weight for ge in v.groups if ge.group in idxs), default=0.0)
        if w >= min_w:
            pts.append(verts[v.index])
    c = sum(pts, Vector()) / len(pts)
    print("LANDMARK", substrs, len(pts), tuple(round(x, 1) for x in c), flush=True)
    return c

P = landmark(['Hips_02'])
Hd = landmark(['Head_07'])
FT = landmark(['LeftFoot_087', 'RightFoot_092'])
TB = landmark(['LeftToeBase_088', 'RightToeBase_093'])
up = (Hd - P).normalized()
H_units = (Hd - P).length / 0.44
U = H_units / 1.8
fwd_raw = TB - FT
fwd = fwd_raw - up * fwd_raw.dot(up)
fwd.normalize()
back = -fwd
print("FACING fwd", tuple(round(v, 3) for v in fwd), "up", tuple(round(v, 3) for v in up), flush=True)
tpos = P + back * (0.048 * H_units) + up * (0.006 * H_units)
tdir = (back - up * 0.22).normalized()
tscale = U
keep_faces = [tuple(p.vertices) for p in me.polygons
              if max((verts[i] - tpos).length for i in p.vertices) < 0.30 * U]
crop = bpy.data.meshes.new("rump_crop")
crop.from_pydata([tuple(v) for v in verts], [], keep_faces)
crop.update()
rump = bpy.data.objects.new("rump_crop", crop)
bpy.context.collection.objects.link(rump)
grey = bpy.data.materials.new("rump_grey")
grey.use_nodes = True
grey.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.42, 0.40, 0.38, 1)
grey.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.95
rump.data.materials.append(grey)
bpy.data.meshes.remove(me)
world_stl(rump, os.path.join(FIT, "base_rump.stl"))
tail_objs, tail_roots = import_part("tail_canine_bushy.glb")
side_v = tdir.cross(up)
if side_v.length < 1e-5:
    side_v = Vector((1, 0, 0))
side_v.normalize()
up_v = side_v.cross(tdir).normalized()
M = Matrix((side_v, -tdir, up_v)).transposed()
for r in tail_roots:
    r.location = tpos
    r.rotation_mode = 'QUATERNION'
    r.rotation_quaternion = M.to_quaternion()
    r.scale = (tscale, tscale, tscale)
placements["tail.base"] = {"anchor": "skin-weight Hips_02 cluster, mesh world frame",
                           "H_units": round(H_units, 1), "scale": round(tscale, 2)}
bpy.context.view_layer.update()
for o in tail_objs:
    if o.type == 'MESH' and 'volume' in o.name:
        world_stl(o, os.path.join(FIT, "tail_placed.stl"))
json.dump(placements, open(os.path.join(WORK, "placements.json"), "w"), indent=1)
for o in wolf_objs:
    o.hide_render = True
rump.hide_render = False
for o in tail_objs:
    o.hide_render = ('core' in o.name)
add_sun("tsun1", (0.9, 0.3, 0.5), 3.5)
add_sun("tsun2", (-0.6, -0.8, 0.9), 1.2)
ttarget = tpos + tdir * 0.13 * U + up * 0.02 * U
_tv = [o for o in tail_objs if o.type == 'MESH' and 'volume' in o.name][0]
_tv.data = _tv.data.copy()
_tv.data.materials.clear()
_hi = bpy.data.materials.new('TailHighlight'); _hi.use_nodes = True
_hi.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.62, 0.42, 0.24, 1)
_hi.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.9
_tv.data.materials.append(_hi)
render(add_camera("cam_tail", ttarget + side_v * 1.05 * U + back * 0.95 * U + up * 0.45 * U,
                  ttarget), os.path.join(REND, "tail_on_wolf_rump.png"))
# park the wolf group aside for the saved assembly
for o in wolf_objs + tail_objs + [rump]:
    if o.parent is None:
        o.location.x += 3.0 * U
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "assembly.blend"))
print("ASSEMBLY SAVED", flush=True)

# ================================================================ lineup
for o in tail_objs:
    o.hide_render = True
rump.hide_render = True
ear2, ear2_roots = import_part("ear_canine_upright_R.glb")
horn2, horn2_roots = import_part("horns_curved_pair.glb")
tail2, tail2_roots = import_part("tail_canine_bushy.glb")
for r in ear2_roots:
    r.location = Vector((-0.55, 0, 0)); r.rotation_euler = (0, 0, 0)
for r in horn2_roots:
    r.location = Vector((0.0, 0, 0)); r.rotation_euler = (math.radians(90), 0, 0)
for r in tail2_roots:
    r.location = Vector((0.55, 0.16, 0)); r.rotation_euler = (math.radians(-90), 0, 0)
for o in tail2:
    if o.type == 'MESH':
        o.hide_render = ('core' in o.name)
plane = bpy.data.meshes.new("ground")
plane.from_pydata([(-1.4, -0.8, 0), (1.4, -0.8, 0), (1.4, 0.8, 0), (-1.4, 0.8, 0)], [],
                  [(0, 1, 2, 3)])
po = bpy.data.objects.new("ground", plane)
bpy.context.collection.objects.link(po)
gm = bpy.data.materials.new("ground_mat")
gm.use_nodes = True
gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.23, 0.23, 0.24, 1)
po.data.materials.append(gm)
add_sun("lsun1", (0.7, 0.4, 0.6), 3.0)
add_sun("lsun2", (-0.5, -0.6, 0.8), 1.0)
L = add_light("larea", (-0.7, -1.1, 1.3), 60, 1.2)
aim(L, (0, 0, 0.15))
scene.render.resolution_x = 960
scene.render.resolution_y = 640
print("B14 RENDERS_FIX DONE", flush=True)
