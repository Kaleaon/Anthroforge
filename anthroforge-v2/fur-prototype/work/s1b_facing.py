import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.open_mainfile(filepath="/home/hatch/workspace/stick-figure-avatar/furry/bara_wolf_base.blend")
ob = bpy.data.objects["BaraWolfBody"]
mw = ob.matrix_world
ws = [mw @ v.co for v in ob.data.vertices]

def report(label, sel):
    print(f"--- {label}: n={len(sel)}")
    if not sel: return
    for axis, ai in (("x",0),("y",1),("z",2)):
        vals = [v[ai] for v in sel]
        print(f"   {axis}: [{min(vals):.3f}, {max(vals):.3f}]")

# centerline head column
col = [v for v in ws if abs(v.x) < 0.06 and 1.45 <= v.z <= 1.95]
report("centerline |x|<0.06, z 1.45-1.95", col)
plus = [v for v in col if v.y > 0.15]
minus = [v for v in col if v.y < -0.15]
report("centerline y>+0.15", plus)
report("centerline y<-0.15", minus)

# ears: top band, off-center
ears_p = [v for v in ws if v.z > 1.86 and v.y > 0.05]
ears_m = [v for v in ws if v.z > 1.86 and v.y < -0.05]
report("top z>1.86 y>0.05", ears_p)
report("top z>1.86 y<-0.05", ears_m)

# chest vs back at sternum height: which side has more surface area proxy (vert count) at z 1.15-1.30, |x|<0.2
fr = [v for v in ws if abs(v.x) < 0.2 and 1.15 <= v.z <= 1.30 and v.y > 0.10]
bk = [v for v in ws if abs(v.x) < 0.2 and 1.15 <= v.z <= 1.30 and v.y < -0.10]
print("sternum front(+Y) verts:", len(fr), " max y:", max((v.y for v in fr), default=None))
print("sternum back (-Y) verts:", len(bk), " min y:", min((v.y for v in bk), default=None))
