"""B2 stage 2: deviation measurement in the sculpt's LOCAL frame.
(BVHTree.FromObject is local-space; the sculpt hangs under a rotated
'Geode' parent, so world-space points give garbage distances.)
Also dumps retopo verts/edges for the wireframe plot."""
import bpy, json
import numpy as np
from mathutils.bvhtree import BVHTree

OUT = '/home/hatch/workspace/anthroforge-v2/model-craft/b2-retopo'
bpy.ops.wm.open_mainfile(filepath=f'{OUT}/work/retopo_done.blend')
src = bpy.context.scene.objects['SRC_orc_head_sculpt']
work = bpy.context.scene.objects['RETOPO_orc_head']
print('[b2s2] src matrix_world == retopo matrix_world:',
      src.matrix_world == work.matrix_world)

HEIGHT = 99.15  # from stage 1 src_bounds (world Z span)
bvh = BVHTree.FromObject(src, bpy.context.evaluated_depsgraph_get())

def surf_dist(points):
    return np.array([bvh.find_nearest(p)[3] for p in points])

def dstats(d):
    return dict(mean=round(float(np.mean(d)), 4),
                median=round(float(np.median(d)), 4),
                p95=round(float(np.percentile(d, 95)), 4),
                p99=round(float(np.percentile(d, 99)), 4),
                max=round(float(np.max(d)), 4),
                mean_pct_height=round(float(np.mean(d) / HEIGHT * 100), 3),
                p95_pct_height=round(float(np.percentile(d, 95) / HEIGHT * 100), 3),
                max_pct_height=round(float(np.max(d) / HEIGHT * 100), 3))

wco = [v.co.copy() for v in work.data.vertices]  # local frame == src local frame
d_verts = surf_dist(wco)
centers = [p.center.copy() for p in work.data.polygons]
d_cent = surf_dist(centers)
rng = np.random.default_rng(7)
rand_pts = []
for p in work.data.polygons:
    vs = [work.data.vertices[i].co for i in p.vertices]
    a, b = rng.random(), rng.random()
    if a + b > 1: a, b = 1 - a, 1 - b
    rand_pts.append(vs[0] + a * (vs[1] - vs[0]) + b * (vs[2] - vs[0]))
d_rand = surf_dist(rand_pts)
res = dict(deviation_verts=dstats(d_verts),
           deviation_all_samples=dstats(np.concatenate([d_verts, d_cent, d_rand])),
           deviation_samples_n=int(len(d_verts) + len(d_cent) + len(d_rand)))
print('[b2s2]', json.dumps(res, indent=1))
with open(f'{OUT}/work/stats_stage2.json', 'w') as f:
    json.dump(res, f, indent=1)

# edge dump for the topology plot (local coords; plot will rotate to front)
verts = np.array([tuple(v.co) for v in work.data.vertices], dtype=np.float32)
edges = set()
for p in work.data.polygons:
    vs = list(p.vertices)
    for i in range(len(vs)):
        edges.add(tuple(sorted((vs[i], vs[(i + 1) % len(vs)]))))
edges = np.array(sorted(edges), dtype=np.int32)
sverts = np.array([tuple(v.co) for v in src.data.vertices], dtype=np.float32)
np.savez_compressed(f'{OUT}/work/edges.npz', retopo_verts=verts,
                    retopo_edges=edges, src_verts=sverts)
print('[b2s2] edges dumped:', len(edges))
print('B2_STAGE2_DONE')
