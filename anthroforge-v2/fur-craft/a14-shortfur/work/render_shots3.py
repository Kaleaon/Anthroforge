"""A14 render pass v3 — remaining shots only (t3, t2, grazing, lineup),
thread-capped for the shared 1.5-CPU cell. Same studio as v2."""
import bpy, time
from mathutils import Vector
ROOT = "/home/hatch/workspace/anthroforge-v2/fur-craft/a14-shortfur"
bpy.ops.wm.open_mainfile(filepath=ROOT + "/shortfur_compare.blend")
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.render.use_compositing = False
scene.cycles.use_denoising = True
scene.cycles.transparent_max_bounces = 32
scene.render.image_settings.file_format = 'PNG'
w = bpy.data.worlds.new("A14Studio"); scene.world = w
bg = w.node_tree.nodes["Background"]
bg.inputs[0].default_value = (0.145, 0.145, 0.15, 1.0)

def look_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat('-Z', 'Y').to_euler()

def area(name, pos, energy, size):
    ob = bpy.data.objects.new(name, bpy.data.lights.new(name, 'AREA'))
    ob.data.energy = energy; ob.data.shape = 'DISK'; ob.data.size = size
    ob.location = pos; scene.collection.objects.link(ob); look_at(ob, Vector((0, 0, 0)))
area("A14_Key", Vector((1.8, 3.4, 2.8)), 260, 2.5)
area("A14_Fill", Vector((-3.2, 2.4, 0.3)), 90, 3.0)
rim = bpy.data.objects.get("A14_Rim")
if rim: rim.data.energy = 420

LABELS = {"ctrl": "BASE", "t1": "T1 VELVET", "t2": "T2 SHELLS", "t3": "T3 PELT"}
def show_only(group):
    for ob in bpy.data.objects:
        if ob.type in ('CAMERA', 'LIGHT'):
            continue
        if ob.name == "A14_Floor":
            ob.hide_render = False
        elif group is None:
            ob.hide_render = False
        else:
            ob.hide_render = not (ob.name.startswith(f"A14_{group}_") or
                                  ob.name == "A14_label_" + LABELS[group])
    if group == "t2":
        for ob in bpy.data.objects:
            if "_shell" in ob.name:
                ob.hide_render = False

def shoot(cam_name, out, w_, h, samples):
    t0 = time.time()
    scene.camera = bpy.data.objects[cam_name]
    scene.render.resolution_x = w_; scene.render.resolution_y = h
    scene.cycles.samples = samples
    scene.render.filepath = ROOT + "/renders/" + out
    bpy.ops.render.render(write_still=True)
    print(f"A14 SHOT {out} {time.time()-t0:.0f}s", flush=True)

show_only("t3"); shoot("CamClose_t3", "render_close_t3", 720, 720, 24)
show_only("t2"); shoot("CamClose_t2", "render_close_t2", 720, 720, 24)
show_only("t2"); shoot("CamGrazeT2", "render_grazing_t2", 1000, 700, 24)
show_only(None); shoot("CamLineup", "render_lineup", 1280, 700, 20)
print("A14 RENDERS DONE", flush=True)
