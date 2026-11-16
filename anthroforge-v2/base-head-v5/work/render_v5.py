"""Clay renders for base-head-v5: front / three-quarter / profile + jaw-open
three-quarter (-25 deg). Cycles CPU (Workbench/EEVEE need libEGL, absent on
this VM), single clay material override, flat grey world + two sun lights --
flat studio, NO HDRI (v4 shipped no renders at all). Does not save the blend."""
import bpy, math, os
from mathutils import Vector, Matrix
OUT = "/home/hatch/workspace/anthroforge-v2/base-head-v5"
bpy.ops.wm.open_mainfile(filepath=OUT + "/neutral_base_head_v5.blend")
REF = ["Skull", "SkullMandible", "Muscles"]
O = {o.name: o for o in bpy.data.objects}
FINAL = [n for n, o in O.items() if o.type == 'MESH' and n not in REF]
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 32
scene.cycles.use_denoising = True
scene.cycles.device = 'CPU'
scene.render.resolution_x = 950; scene.render.resolution_y = 950
world = bpy.data.worlds.new('W'); scene.world = world
bg = world.node_tree.nodes['Background']
bg.inputs['Color'].default_value = (0.16, 0.16, 0.17, 1.0)
bg.inputs['Strength'].default_value = 1.15
def sun(name, rot, energy, color=(1, 1, 1)):
    d = bpy.data.lights.new(name, 'SUN'); d.energy = energy; d.color = color
    o = bpy.data.objects.new(name, d); o.rotation_euler = rot
    scene.collection.objects.link(o)
sun('KeySun', (math.radians(55), math.radians(10), math.radians(35)), 3.2)
sun('FillSun', (math.radians(70), math.radians(-15), math.radians(-120)), 1.1, (0.9, 0.95, 1.0))
sun('BackSun', (math.radians(100), math.radians(20), math.radians(160)), 1.6, (1.0, 0.98, 0.92))
clay = bpy.data.materials.new("Clay")
bsdf = clay.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.72, 0.70, 0.68, 1)
bsdf.inputs["Roughness"].default_value = 0.6
for n in FINAL:
    o = O[n]
    o.hide_render = False
    o.data.materials.clear(); o.data.materials.append(clay)
for n in REF:
    if n in O: O[n].hide_render = True
cam_data = bpy.data.cameras.new('Cam'); cam_data.lens = 82
cam = bpy.data.objects.new('Cam', cam_data); scene.collection.objects.link(cam); scene.camera = cam
def look_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat('-Z', 'Y').to_euler()
def shoot(name, pos, target):
    cam.location = pos; look_at(cam, target)
    scene.render.filepath = os.path.join(OUT, "renders", name)
    bpy.ops.render.render(write_still=True)
H = Vector(tuple(O["Jaw"].location))
def pose_jaw(deg):
    O["Jaw"].rotation_euler = (math.radians(deg), 0, 0)
    O["TeethLower"].rotation_euler = (math.radians(deg), 0, 0)
    M = Matrix.Translation(H) @ Matrix.Rotation(math.radians(deg), 4, 'X') @ Matrix.Translation(-H)
    O["Tongue"].matrix_world = M @ O["Tongue"].matrix_world
    bpy.context.view_layer.update()
def unpose():
    O["Jaw"].rotation_euler = (0, 0, 0)
    O["TeethLower"].rotation_euler = (0, 0, 0)
    O["Tongue"].matrix_world = Matrix.Identity(4)
    bpy.context.view_layer.update()
shoot('head_v5_front.png', Vector((0, 2.1, 0.10)), Vector((0, -0.01, 0.05)))
shoot('head_v5_threequarter.png', Vector((1.35, 1.45, 0.62)), Vector((0, -0.01, 0.03)))
shoot('head_v5_profile.png', Vector((2.1, 0, 0.06)), Vector((0, -0.01, 0.02)))
pose_jaw(-25)
shoot('head_v5_jawopen_threequarter.png', Vector((1.35, 1.45, 0.62)), Vector((0, -0.01, 0.03)))
unpose()
print("V5 RENDERS DONE", FINAL)
