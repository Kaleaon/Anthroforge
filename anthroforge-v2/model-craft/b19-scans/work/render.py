"""Clay renders for before/after comparison.
Usage: blender -b --python render.py -- <mesh> <prefix>"""
import bpy, sys, math
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
path, prefix = argv[0], argv[1]

bpy.ops.wm.read_factory_settings(use_empty=True)
if path.endswith(('.gltf', '.glb')):
    bpy.ops.import_scene.gltf(filepath=path)
obj = [o for o in bpy.data.objects if o.type == 'MESH'][0]

clay = bpy.data.materials.new('clay')
clay.use_nodes = True
bsdf = clay.node_tree.nodes['Principled BSDF']
bsdf.inputs['Base Color'].default_value = (0.55, 0.53, 0.5, 1)
bsdf.inputs['Roughness'].default_value = 0.85
obj.data.materials.clear()
obj.data.materials.append(clay)

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 24
scene.cycles.device = 'CPU'
scene.render.resolution_x = 512
scene.render.resolution_y = 640
world = bpy.data.worlds.new('w'); scene.world = world
world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (0.12, 0.12, 0.12, 1)
world.node_tree.nodes['Background'].inputs[1].default_value = 0.5

sun_data = bpy.data.lights.new('sun', 'SUN'); sun_data.energy = 3.0
sun = bpy.data.objects.new('sun', sun_data); scene.collection.objects.link(sun)
sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(-30))
fill_data = bpy.data.lights.new('fill', 'AREA'); fill_data.energy = 250; fill_data.shape = 'DISK'; fill_data.size = 1.0
fill = bpy.data.objects.new('fill', fill_data); scene.collection.objects.link(fill)
fill.location = (0.5, 0.4, 0.35)

cam_data = bpy.data.cameras.new('cam'); cam_data.clip_end = 10
cam = bpy.data.objects.new('cam', cam_data); scene.collection.objects.link(cam)
scene.camera = cam

bb = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
cen = sum(bb, Vector()) / 8
rad = max((c - cen).length for c in bb)

def shot(name, direction, up_hint=(0, 0, 1)):
    d = Vector(direction).normalized()
    cam.location = cen + d * rad * 2.6 + Vector((0, 0, rad * 0.1))
    look = cen - cam.location
    cam.rotation_euler = look.to_track_quat('-Z', 'Y').to_euler()
    fill.location = cam.location + Vector((0.2, 0.1, 0.3))
    scene.render.filepath = f'renders/{prefix}_{name}.png'
    bpy.ops.render.render(write_still=True)
    print('RENDERED::', scene.render.filepath, flush=True)

import os
os.makedirs('renders', exist_ok=True)
shot('front', (0, -1, 0.15))       # face front is -Y in this asset
shot('back', (0, 1, 0.25))         # back + shows the ground disc on 'before'
shot('threequarter', (-0.8, -0.75, 0.3))
