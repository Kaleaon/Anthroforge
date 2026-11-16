import bpy
from mathutils import Vector

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.open_mainfile(filepath="/home/hatch/workspace/stick-figure-avatar/furry/bara_wolf_base.blend")

ob = bpy.data.objects["BaraWolfBody"]
me = ob.data
print("UV layers:", [uv.name for uv in me.uv_layers])
print("Materials:", len(me.materials))
print("Armature parent:", ob.parent.name if ob.parent else None)
print("Modifiers:", [(m.type, m.name) for m in ob.modifiers])

mw = ob.matrix_world
ws = [mw @ v.co for v in me.vertices]
zs = [v.z for v in ws]
print(f"World Z range: {min(zs):.3f} .. {max(zs):.3f}")

import statistics
def band(lo, hi, label):
    sel = [v for v in ws if lo <= v.z <= hi]
    if not sel: 
        print(label, "empty"); return
    ys = [v.y for v in sel]; xs = [v.x for v in sel]
    print(f"{label}: n={len(sel)} x[{min(xs):.3f},{max(xs):.3f}] y[{min(ys):.3f},{max(ys):.3f}] y_mean={statistics.mean(ys):.3f}")

band(1.80, 2.05, "crown/ears (z 1.80-2.05)")
band(1.62, 1.80, "face/muzzle (z 1.62-1.80)")
band(1.45, 1.62, "neck/jaw   (z 1.45-1.62)")
band(1.05, 1.45, "torso      (z 1.05-1.45)")
band(0.75, 1.05, "belly/hips (z 0.75-1.05)")

# normals: average normal Y in torso band tells front/back if mesh axis-aligned
n_front = n_back = 0
for p in me.polygons:
    c = mw @ p.center
    if 1.05 <= c.z <= 1.45:
        n = p.normal
        if n.y > 0.5: n_front += 1
        if n.y < -0.5: n_back += 1
print("torso polys normal +Y:", n_front, " -Y:", n_back)
