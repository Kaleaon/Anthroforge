#!/usr/bin/env python3
"""B14 fixup renders: head stage with the skirted ear build, wolf tail
stage (Hips-bone anchor -- the CVRxEarth rig has no tail bones), lineup,
and the combined assembly.blend. Replaces assemble_render.py output."""
import bpy, math, os, json
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
PARTS = os.path.join(ROOT, "parts")
REND = os.path.join(ROOT, "renders")
WORK = os.path.join(ROOT, "work")
FIT = os.path.join(WORK, "fit")
for d in (REND, FIT):
    os.makedirs(d, exist_ok=True)
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
print(f"HEAD bbox {tuple(round(v,3) for v in HS)} centre {tuple(round(v,3) for v in HC)} facing {facing:+.0f}Y", flush=True)
world_stl(tissue, os.path.join(FIT, "base_head.stl"))

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
for tag, roots, side in (("R", earR_roots, 1), ("L", earL_roots, -1)):
    pos = Vector((HC.x + side * HS.x * 0.335, HC.y - facing * HS.y * 0.06,
                  HC.z + HS.z * 0.27))
    rot = (math.radians(-10), side * math.radians(22), side * math.radians(-21))
    for r in roots:
        r.location = pos
        r.rotation_euler = rot
    placements[f"ear.{tag}"] = {"location": [round(v, 4) for v in pos],
                                "rotation_euler_deg": [round(math.degrees(a), 1) for a in rot],
                                "scale": EAR_S}
for r in horn_roots:
    r.location = Vector((HC.x, HC.y - facing * HS.y * 0.10, HC.z + HS.z * 0.44))
    r.rotation_euler = (math.radians(-8), 0, 0)
placements["head.top horns"] = {"location": [round(v, 4) for v in r.location], "scale": HORN_S}
bpy.context.view_layer.update()
for tag, objs, key in (("ear_pair", earR_objs + earL_objs, "ear"), ("horns", horn_objs, "horn")):
    for o in objs:
        if o.type == 'MESH' and key in o.name.lower():
            world_stl(o, os.path.join(FIT, f"{tag}_{o.name}.stl"))

ctr = HC + Vector((0, facing * 0.001, 0.01))
render(add_camera("cam_front", HC + Vector((0, facing * HS.y * 2.6, HS.z * 0.25)), ctr),
       os.path.join(REND, "head_front.png"))
render(add_camera("cam_34", HC + Vector((HS.x * 1.7, facing * HS.y * 2.0, HS.z * 0.55)), ctr),
       os.path.join(REND, "head_threequarter.png"))
render(add_camera("cam_ear", Vector((HC.x + HS.x * 0.75, HC.y + facing * HS.y * 0.85,
                                     HC.z + HS.z * 0.62)),
                  Vector((HC.x + HS.x * 0.33, HC.y, HC.z + HS.z * 0.36))),
       os.path.join(REND, "ear_closeup.png"))

# ================================================================ wolf stage
before = set(bpy.context.scene.objects)
bpy.ops.import_scene.gltf(filepath=WOLF)
wolf_objs = [o for o in bpy.context.scene.objects if o not in before]
for o in wolf_objs:
    if o.parent is None:
        o.location.x += 3.0
bpy.context.view_layer.update()
arm = next(o for o in wolf_objs if o.type == 'ARMATURE')
bones = {b.name: b for b in arm.data.bones}
def bone_world(name):
    b = bones[name]
    return arm.matrix_world @ b.head_local, arm.matrix_world @ b.tail_local
hips_h, hips_t = bone_world('mixamorig:Hips_02')
foot_h, _ = bone_world('mixamorig:LeftFoot_087')
toe_h, _ = bone_world('mixamorig:LeftToeBase_088')
fwd = Vector((toe_h.x - foot_h.x, toe_h.y - foot_h.y, 0))
fwd.normalize()
back = -fwd
up = Vector((0, 0, 1))
wmn, wmx = bbox_of(wolf_objs)
wheight = wmx.z - wmn.z
tpos = hips_h + back * 0.085 + up * 0.015
tdir = (back + Vector((0, 0, -0.22))).normalized()
print("TAIL mount", tuple(round(v, 3) for v in tpos), "dir", tuple(round(v, 3) for v in tdir),
      "wolf height", round(wheight, 2), flush=True)

body = max((o for o in wolf_objs if o.type == 'MESH'), key=lambda o: len(o.data.vertices))
dg = bpy.context.evaluated_depsgraph_get()
ev = body.evaluated_get(dg)
me = bpy.data.meshes.new_from_object(ev)
me.transform(body.matrix_world)
verts = [v.co.copy() for v in me.vertices]
keep_faces = [tuple(p.vertices) for p in me.polygons
              if max((verts[i] - tpos).length for i in p.vertices) < 0.36]
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
q = M.to_quaternion()
tscale = max(wheight / 1.8, 0.85)
for r in tail_roots:
    r.location = tpos
    r.rotation_mode = 'QUATERNION'
    r.rotation_quaternion = q
    r.scale = (tscale, tscale, tscale)
placements["tail.base"] = {"location": [round(v, 4) for v in tpos], "scale": round(tscale, 3),
                           "anchor": "mixamorig:Hips_02 head + back*0.085 + up*0.015 (rig has no tail bones)"}
bpy.context.view_layer.update()
for o in tail_objs:
    if o.type == 'MESH' and 'volume' in o.name:
        world_stl(o, os.path.join(FIT, "tail_placed.stl"))

json.dump(placements, open(os.path.join(WORK, "placements.json"), "w"), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "assembly.blend"))
print("ASSEMBLY SAVED", flush=True)

for o in head_objs + earR_objs + earL_objs + horn_objs:
    o.hide_render = True
for o in wolf_objs:
    o.hide_render = True
rump.hide_render = False
for o in tail_objs:
    o.hide_render = ('core' in o.name)
ttarget = tpos + tdir * 0.22 + Vector((0, 0, 0.05))
render(add_camera("cam_tail", tpos + side_v * 0.55 + up * 0.18 + tdir * 0.30, ttarget),
       os.path.join(REND, "tail_on_wolf_rump.png"))

# ================================================================ lineup
for o in tail_objs:
    o.hide_render = True
rump.hide_render = True
ear2, ear2_roots = import_part("ear_canine_upright_R.glb")
horn2, horn2_roots = import_part("horns_curved_pair.glb")
tail2, tail2_roots = import_part("tail_canine_bushy.glb")
for r in ear2_roots:
    r.location = Vector((-0.42, 0, 0)); r.rotation_euler = (0, 0, 0)
for r in horn2_roots:
    r.location = Vector((0.0, 0, 0)); r.rotation_euler = (math.radians(90), 0, 0)
for r in tail2_roots:
    r.location = Vector((0.42, 0.16, 0)); r.rotation_euler = (math.radians(-90), 0, 0)
for o in tail2:
    if o.type == 'MESH':
        o.hide_render = ('core' in o.name)
plane = bpy.data.meshes.new("ground")
plane.from_pydata([(-1.2, -0.7, 0), (1.2, -0.7, 0), (1.2, 0.7, 0), (-1.2, 0.7, 0)], [],
                  [(0, 1, 2, 3)])
po = bpy.data.objects.new("ground", plane)
bpy.context.collection.objects.link(po)
gm = bpy.data.materials.new("ground_mat")
gm.use_nodes = True
gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.23, 0.23, 0.24, 1)
po.data.materials.append(gm)
for nm, loc, en in (("key2", (-0.8, -1.2, 1.6), 500), ("fill2", (1.2, -0.6, 0.8), 200),
                    ("rim2", (0.3, 1.2, 1.0), 300)):
    L = add_light(nm, loc, en, 1.5)
    aim(L, (0, 0, 0.15))
scene.render.resolution_x = 960
scene.render.resolution_y = 640
render(add_camera("cam_lineup", (0, -1.35, 0.42), (0.02, 0, 0.16)),
       os.path.join(REND, "parts_lineup.png"))
print("B14 FIXUP DONE", flush=True)
