"""B2 stage 3: clay renders for ONE object per process (memory discipline).
Usage: blender -b --python stage3.py -- before|after
'before' renders a render-only decimation (~150k tris) of the sculpt;
the full sculpt OOM-killed a combined render pass at 856k tris.
Deviation numbers are computed against the full sculpt in stage 2."""
import bpy, math, sys
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
MODE = argv[0]
OUT = '/home/hatch/workspace/anthroforge-v2/model-craft/b2-retopo'
bpy.ops.wm.open_mainfile(filepath=f'{OUT}/work/retopo_done.blend')
src = bpy.context.scene.objects['SRC_orc_head_sculpt']
ret = bpy.context.scene.objects['RETOPO_orc_head']

bb = [src.matrix_world @ Vector(c) for c in src.bound_box]
xs = [v.x for v in bb]; ys = [v.y for v in bb]; zs = [v.z for v in bb]
ctr = Vector(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (min(zs) + max(zs)) / 2))
span = max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)) * 1.15

if MODE == 'before':
    rob = src.copy(); rob.data = src.data.copy(); rob.name = 'SRC_render'
    bpy.context.scene.collection.objects.link(rob)
    bpy.data.objects.remove(ret, do_unlink=True)
    bpy.data.objects.remove(src, do_unlink=True)
    bpy.ops.object.select_all(action='DESELECT')
    rob.select_set(True); bpy.context.view_layer.objects.active = rob
    mod = rob.modifiers.new('render_decimate', 'DECIMATE')
    mod.ratio = 150000 / 855696
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.ops.outliner.orphans_purge(do_recursive=True)
    target, tag = rob, 'before'
else:
    bpy.data.objects.remove(src, do_unlink=True)
    bpy.ops.outliner.orphans_purge(do_recursive=True)
    target, tag = ret, 'after'
print(f'[b2s3] {tag}: rendering {target.name} '
      f'({len(target.data.polygons)} polys)')

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 8
scene.cycles.device = 'CPU'
scene.render.film_transparent = True
scene.render.resolution_x = 512
scene.render.resolution_y = 512
scene.render.image_settings.file_format = 'PNG'
world = bpy.data.worlds.get('World') or bpy.data.worlds.new('World')
scene.world = world
world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (0.02, 0.02, 0.02, 1)
clay = bpy.data.materials.new('clay')
clay.use_nodes = True
bsdf = clay.node_tree.nodes['Principled BSDF']
bsdf.inputs['Base Color'].default_value = (0.85, 0.85, 0.85, 1)
bsdf.inputs['Roughness'].default_value = 0.9
target.data.materials.clear()
target.data.materials.append(clay)
sun = bpy.data.lights.new('sun', 'SUN'); sun.energy = 3.0
sun_ob = bpy.data.objects.new('sun', sun); scene.collection.objects.link(sun_ob)
sun_ob.rotation_euler = (math.radians(50), 0, math.radians(35))
cam = bpy.data.cameras.new('cam'); cam.type = 'ORTHO'; cam.ortho_scale = span
cam_ob = bpy.data.objects.new('cam', cam); scene.collection.objects.link(cam_ob)
scene.camera = cam_ob
VIEWS = {'front': (ctr + Vector((0, -span, 0)), (math.radians(90), 0, 0)),
         'profile': (ctr + Vector((span, 0, 0)), (math.radians(90), 0, math.radians(90))),
         'top': (ctr + Vector((0, 0, span)), (0, 0, 0))}
for vname, (loc, rot) in VIEWS.items():
    cam_ob.location = loc; cam_ob.rotation_euler = rot
    scene.render.filepath = f'{OUT}/renders/{tag}_{vname}.png'
    bpy.ops.render.render(write_still=True)
    print(f'[b2s3] wrote {tag}_{vname}.png', flush=True)
print('B2_STAGE3_DONE')
