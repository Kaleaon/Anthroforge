import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

bpy.ops.wm.open_mainfile(filepath="/home/hatch/workspace/anthroforge-v2/parts-lab/kaleaon-anatomy/kaleaon_anatomy_parts.blend")
dg = bpy.context.evaluated_depsgraph_get()

for name, inside_pt, outside_pt in [
    ("Part_SacUdder", Vector((0.03, -0.05, 0.5)), Vector((0.03, -0.05, -1.0))),
    ("Part_Shaft_1", Vector((-0.07, -0.25, 0.85)), Vector((-0.07, -0.25, -1.0))),
]:
    ob = bpy.data.objects[name]
    tree = BVHTree.FromObject(ob, dg)
    for label, p in (("inside_pt", inside_pt), ("outside_pt", outside_pt)):
        loc, nrm, idx, dist = tree.find_nearest(p)
        s = (p - loc) @ nrm
        print(name, label, "signed=", round(s, 4), "dist=", round(dist, 4))
    # winding check: signed volume of raw mesh
    import bmesh
    bm = bmesh.new(); bm.from_mesh(ob.data); print(name, "raw signed vol L:", round(bm.calc_volume() * 1000, 3)); bm.free()
