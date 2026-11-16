"""B2 stage 1b: load joined sculpt -> voxel proxy -> QuadriFlow ->
shrinkwrap pin -> stats -> SAVE + GLB exports."""
import bpy, json, time

T0 = time.time()
LOG = {}
def log(k, v):
    LOG[k] = v
    print(f"[b2s1b] {k}: {v}", flush=True)

OUT = '/home/hatch/workspace/anthroforge-v2/model-craft/b2-retopo'
TARGET_FACES = 6000
HEIGHT = 99.15

bpy.ops.wm.open_mainfile(filepath=f'{OUT}/work/checkpoint_src.blend')
src = bpy.context.scene.objects['SRC_orc_head_sculpt']

def mesh_stats(ob):
    m = ob.data
    quads = sum(1 for p in m.polygons if len(p.vertices) == 4)
    tris = sum(1 for p in m.polygons if len(p.vertices) == 3)
    ngons = sum(1 for p in m.polygons if len(p.vertices) > 4)
    edge_face = {}
    for p in m.polygons:
        vs = p.vertices
        for i in range(len(vs)):
            e = tuple(sorted((vs[i], vs[(i + 1) % len(vs)])))
            edge_face[e] = edge_face.get(e, 0) + 1
    val = {}
    for e in edge_face:
        for v in e:
            val[v] = val.get(v, 0) + 1
    return dict(verts=len(m.vertices), polys=len(m.polygons), quads=quads,
                tris=tris, ngons=ngons,
                nonmanifold_edges=sum(1 for c in edge_face.values() if c != 2),
                boundary_edges=sum(1 for c in edge_face.values() if c == 1),
                poles3=sum(1 for v in val.values() if v == 3),
                poles5=sum(1 for v in val.values() if v == 5),
                poles6plus=sum(1 for v in val.values() if v >= 6))

log('src_stats', mesh_stats(src))
t = time.time()
work = src.copy(); work.data = src.data.copy(); work.name = 'RETOPO_work'
bpy.context.scene.collection.objects.link(work)
bpy.ops.object.select_all(action='DESELECT')
work.select_set(True)
bpy.context.view_layer.objects.active = work
work.data.remesh_voxel_size = HEIGHT / 180.0
work.data.remesh_voxel_adaptivity = 0.0
log('voxel_size', round(HEIGHT / 180.0, 4))
bpy.ops.object.voxel_remesh()
bpy.ops.outliner.orphans_purge(do_recursive=True)
log('voxel_proxy_stats', mesh_stats(work))
log('voxel_s', round(time.time() - t, 1))

t = time.time()
bpy.ops.object.quadriflow_remesh(target_faces=TARGET_FACES,
                                 use_mesh_symmetry=False,
                                 use_preserve_sharp=False,
                                 use_preserve_boundary=False,
                                 smooth_normals=True)
log('retopo_mode', 'voxel_then_quadriflow')
log('quadriflow_s', round(time.time() - t, 1))
log('retopo_raw_stats', mesh_stats(work))

t = time.time()
mod = work.modifiers.new('pin_to_sculpt', 'SHRINKWRAP')
mod.target = src
mod.wrap_method = 'NEAREST_SURFACEPOINT'
bpy.ops.object.modifier_apply(modifier=mod.name)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.remove_doubles(threshold=0.0001)
bpy.ops.object.mode_set(mode='OBJECT')
log('shrinkwrap_s', round(time.time() - t, 1))
work.name = 'RETOPO_orc_head'
log('retopo_stats', mesh_stats(work))

# SAVE FIRST (exports are the fragile step; geometry must not depend on them)
bpy.ops.wm.save_as_mainfile(filepath=f'{OUT}/work/retopo_done.blend')
bpy.ops.wm.save_as_mainfile(filepath=f'{OUT}/orc_head_retopo.blend')
try:
    bpy.ops.object.select_all(action='DESELECT')
    src.select_set(True)
    bpy.ops.export_scene.gltf(filepath=f'{OUT}/orc_head_before.glb',
                              use_selection=True)
    bpy.ops.object.select_all(action='DESELECT')
    work.select_set(True)
    bpy.ops.export_scene.gltf(filepath=f'{OUT}/orc_head_retopo.glb',
                              use_selection=True)
    log('glb_exports', 'ok')
except Exception as e:
    log('glb_exports', f'FAILED: {e}')
log('total_s', round(time.time() - T0, 1))
with open(f'{OUT}/work/stats_stage1.json', 'w') as f:
    json.dump(LOG, f, indent=1, default=str)
print('B2_STAGE1B_DONE')
