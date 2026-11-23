#!/usr/bin/env python3
"""B14 assembly: mount parts on library bases, export fit-scoring STLs,
save assembly.blend, render beauty views (Cycles CPU, headless-safe).

Bases: neutral base head v3 (ears+horns, its own ears hidden);
CVRxEarth wolf (tail, mounted at the rig's tail-base bone on a rump crop).
"""
import bpy, math, os, json
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
PARTS = os.path.join(ROOT, "parts")
REND = os.path.join(ROOT, "renders")
WORK = os.path.join(ROOT, "work")
FIT = os.path.join(WORK, "fit")
os.makedirs(REND, exist_ok=True)
os.makedirs(FIT, exist_ok=True)
HEAD_GLB = os.path.expanduser("~/workspace/anthroforge-v2/base-head-v3/neutral_base_head_v3.glb")
WOLF = os.path.expanduser("~/workspace/bodies-3d/parts-library/existing-haul/wolf-rigged-ccby/scene.gltf")
BLENDER = None

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

def add_camera(name, loc, target):
    cd = bpy.data.cameras.new(name)
    co = bpy.data.objects.new(name, cd)
    bpy.context.collection.objects.link(co)
    co.location = loc
    aim(co, target)
    cd.lens = 55
    return co

def render(cam, path):
    scene.camera = cam
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("RENDERED", path)

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

# ================================================================ head base
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
print(f"HEAD bbox size {tuple(round(v,3) for v in HS)} centre {tuple(round(v,3) for v in HC)} facing {facing:+.0f}Y")
world_stl(tissue, os.path.join(FIT, "base_head.stl"))

# ================================================================ ears+horns
def import_part(fname):
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(PARTS, fname))
    new = [o for o in bpy.context.scene.objects if o not in before]
    roots = [o for o in new if o.parent is None]
    return new, roots

earR_objs, earR_roots = import_part("ear_canine_upright_R.glb")
earL_objs, earL_roots = import_part("ear_canine_upright_L.glb")
horn_objs, horn_roots = import_part("horns_curved_pair.glb")

# NOTE: head v3 GLB is authored in L-units (bbox Y = 1.0 = one head length),
# not metres. Parts are true-metre; scale them onto the head by ratio:
# ear 0.115 m -> 0.38 L (wolf band 0.36-0.40) => x3.3; horns x3.0.
EAR_S, HORN_S = 3.3, 3.0
for r in earR_roots + earL_roots:
    r.scale = (EAR_S, EAR_S, EAR_S)
for r in horn_roots:
    r.scale = (HORN_S, HORN_S, HORN_S)

# lights for the head shots (aimed at head centre)
for nm, off, en in (("hkey", (-0.45, 0, 0.35), 240), ("hfill", (0.5, 0, 0.1), 80),
                    ("hrim", (0.1, 0, 0.55), 200)):
    L = add_light(nm, HC + Vector((off[0], facing * (abs(off[0]) * 0.4 - 0.55), off[2])), en, 1.2)
    aim(L, HC)

placements = {}
for tag, roots, side in (("R", earR_roots, 1), ("L", earL_roots, -1)):
    pos = Vector((HC.x + side * HS.x * 0.335, HC.y - facing * HS.y * 0.06,
                  HC.z + HS.z * 0.27))
    rot = (math.radians(-10), side * math.radians(22), side * math.radians(-21))
    if facing < 0:
        rot = (rot[0], rot[1], -rot[2])
    for r in roots:
        r.location = pos
        r.rotation_euler = rot
    placements[f"ear.{tag}"] = {"location": [round(v, 4) for v in pos],
                                "rotation_euler_deg": [round(math.degrees(a), 1) for a in rot]}
for r in horn_roots:
    # pair GLB origin is the midpoint between the horn bases (baked spacing)
    r.location = Vector((HC.x, HC.y - facing * HS.y * 0.10, HC.z + HS.z * 0.44))
    r.rotation_euler = (math.radians(-8), 0, 0)
placements["head.top horns"] = {"location": [round(v, 4) for v in r.location],
                                "note": "pair GLB origin midway between bases; bases at local x +/-0.036"}
bpy.context.view_layer.update()

# placed STL exports for fit scoring (meshes only)
for tag, objs in (("ear_pair", earR_objs + earL_objs), ("horns", horn_objs)):
    for o in objs:
        if o.type == 'MESH':
            world_stl(o, os.path.join(FIT, f"{tag}_{o.name}.stl"))

cams_head = HC + Vector((0, facing * 0.001, 0.01))
front_cam = add_camera("cam_front", HC + Vector((0, facing * HS.y * 2.6, HS.z * 0.25)), cams_head)
tq_cam = add_camera("cam_34", HC + Vector((HS.x * 1.7, facing * HS.y * 2.0, HS.z * 0.55)), cams_head)
ear_cam = add_camera("cam_ear", Vector((HC.x + HS.x * 0.75, HC.y + facing * HS.y * 0.85,
                                        HC.z + HS.z * 0.62)),
                     Vector((HC.x + HS.x * 0.33, HC.y, HC.z + HS.z * 0.36)))
render(front_cam, os.path.join(REND, "head_front.png"))
render(tq_cam, os.path.join(REND, "head_threequarter.png"))
render(ear_cam, os.path.join(REND, "ear_closeup.png"))

# hide head assembly for the tail shot
head_all = head_objs + earR_objs + earL_objs + horn_objs
for o in head_all:
    o.hide_render = True

# ================================================================ wolf + tail
before = set(bpy.context.scene.objects)
bpy.ops.import_scene.gltf(filepath=WOLF)
wolf_objs = [o for o in bpy.context.scene.objects if o not in before]
arm = next((o for o in wolf_objs if o.type == 'ARMATURE'), None)
tail_bone = None
if arm:
    for b in arm.data.bones:
        if 'ail' in b.name:
            tail_bone = b
            break
body = max((o for o in wolf_objs if o.type == 'MESH'), key=lambda o: len(o.data.vertices))
wmn, wmx = bbox_of(wolf_objs)
wheight = wmx.z - wmn.z
if tail_bone:
    tpos = arm.matrix_world @ tail_bone.head_local
    tdir = (arm.matrix_world @ tail_bone.tail_local) - tpos
    tdir.normalize()
else:
    tpos = Vector((wmn.x + wmx.x) / 2, wmn.y, wmn.z + wheight * 0.52)
    tdir = Vector((0, -1, 0))
print("TAIL mount at", tuple(round(v, 3) for v in tpos), "dir", tuple(round(v, 3) for v in tdir),
      "wolf height", round(wheight, 2))

# rump crop from wolf body mesh
dg = bpy.context.evaluated_depsgraph_get()
ev = body.evaluated_get(dg)
me = bpy.data.meshes.new_from_object(ev)
me.transform(body.matrix_world)
verts = [v.co.copy() for v in me.vertices]
keep_faces = []
R_IN, R_OUT = 0.30, 0.36
for p in me.polygons:
    ds = [ (verts[i] - tpos).length for i in p.vertices]
    if max(ds) < R_OUT:
        keep_faces.append(tuple(p.vertices))
crop_verts = verts
crop = bpy.data.meshes.new("rump_crop")
crop.from_pydata([tuple(v) for v in crop_verts], [], keep_faces)
crop.update()
rump = bpy.data.objects.new("rump_crop", crop)
bpy.context.collection.objects.link(rump)
grey = bpy.data.materials.new("rump_grey")
grey.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.42, 0.40, 0.38, 1)
grey.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.95
rump.data.materials.append(grey)
for o in wolf_objs:
    o.hide_render = True
world_stl(rump, os.path.join(FIT, "base_rump.stl"))
bpy.data.meshes.remove(me)

# tail placement: local -Y along bone dir, +Z toward world up
tail_objs, tail_roots = import_part("tail_canine_bushy.glb")
back = tdir
up_hint = Vector((0, 0, 1))
side_v = back.cross(up_hint)
if side_v.length < 1e-5:
    side_v = Vector((1, 0, 0))
side_v.normalize()
up_v = side_v.cross(back).normalized()
# local axes: X->side_v, Y->(-back) so that local -Y == back dir, Z->up_v
from mathutils import Matrix
M = Matrix((side_v, -back, up_v)).transposed()
q = M.to_quaternion()
tscale = max(wheight / 1.8, 0.85)
for r in tail_roots:
    r.location = tpos
    r.rotation_mode = 'QUATERNION'
    r.rotation_quaternion = q
    r.scale = (tscale, tscale, tscale)
placements["tail.base"] = {"location": [round(v, 4) for v in tpos], "scale": round(tscale, 3)}
bpy.context.view_layer.update()
for o in tail_objs:
    if o.type == 'MESH' and 'volume' in o.name:
        world_stl(o, os.path.join(FIT, "tail_placed.stl"))
    if o.type == 'MESH':
        o.hide_render = False
rump.hide_render = False

tail_target = tpos + back * 0.22 + Vector((0, 0, 0.05))
tcam = add_camera("cam_tail", tpos + Vector((0.55, 0, 0.18)) + back * 0.35, tail_target)
render(tcam, os.path.join(REND, "tail_on_wolf_rump.png"))

# ================================================================ lineup shot
for o in head_all:
    o.hide_render = True
rump.hide_render = True
for o in tail_objs:
    o.hide_render = True
lup = {}
ear2, ear2_roots = import_part("ear_canine_upright_R.glb")
horn2, horn2_roots = import_part("horns_curved_pair.glb")
tail2, tail2_roots = import_part("tail_canine_bushy.glb")
for r in ear2_roots:
    r.location = Vector((-0.42, 0, 0)); r.rotation_euler = (0, 0, 0)
for r in horn2_roots:
    r.location = Vector((0.0, 0, 0)); r.rotation_euler = (math.radians(90), 0, 0)
for r in tail2_roots:
    r.location = Vector((0.42, 0.16, 0)); r.rotation_euler = (math.radians(-90), 0, 0)
for objs in (tail2,):
    for o in objs:
        if o.type == 'MESH':
            o.hide_render = ('core' in o.name)
plane = bpy.data.meshes.new("ground")
plane.from_pydata([(-1.2, -0.7, 0), (1.2, -0.7, 0), (1.2, 0.7, 0), (-1.2, 0.7, 0)], [],
                  [(0, 1, 2, 3)])
po = bpy.data.objects.new("ground", plane)
bpy.context.collection.objects.link(po)
gm = bpy.data.materials.new("ground_mat")
gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.23, 0.23, 0.24, 1)
po.data.materials.append(gm)
for nm, loc, en in (("key", (-0.8, -1.2, 1.6), 900), ("fill", (1.2, -0.6, 0.8), 350),
                    ("rim", (0.3, 1.2, 1.0), 500)):
    L = add_light(nm, loc, en, 1.5)
    aim(L, (0, 0, 0.15))
scene.render.resolution_x = 960
scene.render.resolution_y = 640
lcam = add_camera("cam_lineup", (0, -1.35, 0.42), (0.02, 0, 0.16))
render(lcam, os.path.join(REND, "parts_lineup.png"))

json.dump(placements, open(os.path.join(WORK, "placements.json"), "w"), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "assembly.blend"))
print("B14 ASSEMBLY DONE", placements)
