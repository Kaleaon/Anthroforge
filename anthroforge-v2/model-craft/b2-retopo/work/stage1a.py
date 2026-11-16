"""B2 stage 1a: import -> join chunks (NO edit-mode weld: remove_doubles
on 856k tris is the memory spike; the voxel stage doesn't need welded
input and deviation treats the union surface identically) -> save."""
import bpy, json, time
from mathutils import Vector

T0 = time.time()
LOG = {}
def log(k, v):
    LOG[k] = v
    print(f"[b2s1a] {k}: {v}", flush=True)

OUT = '/home/hatch/workspace/anthroforge-v2/model-craft/b2-retopo'
t = time.time()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=OUT + '/work/src/scene.gltf')
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
log('import_s', round(time.time() - t, 1))
log('chunk_objects', len(meshes))
bpy.ops.object.select_all(action='DESELECT')
for o in meshes:
    o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
bpy.ops.object.join()
src = bpy.context.view_layer.objects.active
src.name = 'SRC_orc_head_sculpt'
me = src.data
me.calc_loop_triangles()
log('src_verts_unwelded', len(me.vertices))
log('src_tris', len(me.loop_triangles))
bb = [src.matrix_world @ Vector(c) for c in src.bound_box]
xs = [v.x for v in bb]; ys = [v.y for v in bb]; zs = [v.z for v in bb]
log('src_bounds', dict(x=[round(min(xs), 2), round(max(xs), 2)],
                       y=[round(min(ys), 2), round(max(ys), 2)],
                       z=[round(min(zs), 2), round(max(zs), 2)],
                       height=round(max(zs) - min(zs), 2),
                       x_asym=round(abs(min(xs) + max(xs)), 3)))
bpy.ops.wm.save_as_mainfile(filepath=f'{OUT}/work/checkpoint_src.blend')
log('total_s', round(time.time() - T0, 1))
with open(f'{OUT}/work/stats_stage1a.json', 'w') as f:
    json.dump(LOG, f, indent=1, default=str)
print('B2_STAGE1A_DONE')
