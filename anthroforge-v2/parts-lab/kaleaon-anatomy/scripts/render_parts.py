import bpy, math, os
from mathutils import Vector

bpy.ops.wm.open_mainfile(filepath="/home/hatch/workspace/anthroforge-v2/parts-lab/kaleaon-anatomy/kaleaon_anatomy_parts.blend")
OUT = "/home/hatch/workspace/anthroforge-v2/parts-lab/kaleaon-anatomy/renders"
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
sc.cycles.samples = 12
sc.cycles.use_denoising = True
sc.render.resolution_x = 512; sc.render.resolution_y = 512
sc.world = bpy.data.worlds.new("W") if not sc.world else sc.world
sc.world.node_tree.nodes["Background"].inputs[0].default_value = (0.25, 0.25, 0.28, 1)
sc.world.node_tree.nodes["Background"].inputs[1].default_value = 0.7

def add_light(name, loc, energy, size=3.0):
    ld = bpy.data.lights.new(name, 'AREA'); ld.energy = energy; ld.shape = 'DISK'; ld.size = size
    lo = bpy.data.objects.new(name, ld); lo.location = loc
    bpy.context.collection.objects.link(lo)
    lo.rotation_euler = (math.radians(50), 0, math.radians(20))
    return lo
add_light("Key", (1.5, -2.0, 2.5), 1200)
add_light("Fill", (-2.0, -0.5, 1.2), 500)

cam_d = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cam_d)
bpy.context.collection.objects.link(cam); sc.camera = cam

def look(cam, loc, target):
    cam.location = loc
    d = Vector(target) - Vector(loc)
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()

TARGET = (0.0, -0.12, 0.52)
views = {
    "groin_front": ((0.0, -2.0, 0.72), TARGET),
    "groin_side": ((2.0, -0.15, 0.66), TARGET),
    "groin_threequarter": ((1.35, -1.45, 0.95), TARGET),
    "full_front": ((0.0, -4.6, 1.15), (0.0, 0.0, 1.05)),
}
for name, (loc, tgt) in views.items():
    if name == "full_front":
        cam.data.lens = 50
    look(cam, loc, tgt)
    sc.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED", name)

# articulation still: shafts fanned, sac swung, teat bent, girth on shaft 1
arm = bpy.data.objects["KaleaonRig"]
def pb(name): 
    b = arm.pose.bones[name]; b.rotation_mode = 'XYZ'; return b
pb("Shaft_2_Base").rotation_euler = (math.radians(28), 0, 0)
pb("Shaft_4_Base").rotation_euler = (math.radians(-24), 0, 0)
pb("Shaft_1_Base").rotation_euler = (math.radians(10), 0, 0)
pb("Sac").rotation_euler = (math.radians(18), 0, 0)
pb("Teat_2").rotation_euler = (math.radians(22), 0, 0)
bpy.data.objects["Part_Shaft_1"].data.shape_keys.key_blocks["GirthPlus"].value = 1.0
bpy.context.view_layer.update()
look(cam, (0.4, -2.0, 0.66), TARGET)
sc.render.filepath = os.path.join(OUT, "articulation.png")
bpy.ops.render.render(write_still=True)
print("RENDERED articulation")
