import bpy, sys
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath="/home/hatch/workspace/stick-figure-avatar/furry/bara_wolf_base.blend")
for ob in bpy.data.objects:
    print("OBJ", ob.name, ob.type)
    if ob.type == 'MESH':
        me = ob.data
        print("  verts", len(me.vertices), "polys", len(me.polygons))
        ws = [ob.matrix_world @ v.co for v in me.vertices]
        xs=[w.x for w in ws]; ys=[w.y for w in ws]; zs=[w.z for w in ws]
        print("  bbox X %.3f..%.3f  Y %.3f..%.3f  Z %.3f..%.3f" % (min(xs),max(xs),min(ys),max(ys),min(zs),max(zs)))
        # topmost 1% verts centroid -> head location guess
        zs_sorted = sorted(zs, reverse=True)
        zcut = zs_sorted[int(len(zs)*0.01)]
        top = [w for w in ws if w.z >= zcut]
        cx = sum(w.x for w in top)/len(top); cy = sum(w.y for w in top)/len(top); cz = sum(w.z for w in top)/len(top)
        print("  top1%% centroid %.3f %.3f %.3f  (n=%d, zcut=%.3f)" % (cx,cy,cz,len(top),zcut))
