import bpy, numpy as np

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath="/home/hatch/workspace/anthroforge-v2/autoskin-prototype/work/bust/scene.gltf")

out = {}
for ob in bpy.context.scene.objects:
    if ob.type != 'MESH':
        continue
    me = ob.data
    me.calc_loop_triangles()
    verts = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get('co', verts)
    verts = verts.reshape(-1, 3)
    # apply world matrix
    M = np.array(ob.matrix_world)
    verts = verts @ M[:3, :3].T + M[:3, 3]
    tris = np.empty(len(me.loop_triangles) * 3, dtype=np.int32)
    me.loop_triangles.foreach_get('vertices', tris)
    tris = tris.reshape(-1, 3)
    key = ob.name.replace(' ', '_')
    out[key + '_v'] = verts.astype(np.float32)
    out[key + '_f'] = tris
    print(key, verts.shape, tris.shape)

np.savez_compressed("/home/hatch/workspace/anthroforge-v2/autoskin-prototype/work/bust_meshes.npz", **out)
print("saved")
