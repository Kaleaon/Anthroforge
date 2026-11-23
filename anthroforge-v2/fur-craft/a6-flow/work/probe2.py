import bpy
bpy.ops.wm.open_mainfile(filepath="/home/hatch/workspace/stick-figure-avatar/furry/bara_wolf_base.blend")
arm = bpy.data.objects["BaraWolf"]
for b in arm.data.bones:
    n = b.name.lower()
    if any(k in n for k in ("head","neck","ear","jaw","nose","snout","muzzle","eye")):
        print("BONE", b.name, "head", tuple(round(v,3) for v in b.head_local), "tail", tuple(round(v,3) for v in b.tail_local))
ob = bpy.data.objects["BaraWolfBody"]
ws = [ob.matrix_world @ v.co for v in ob.data.vertices]
for zlo in (1.50,1.60,1.70,1.80):
    band = [w for w in ws if zlo <= w.z < zlo+0.10 and abs(w.x) < 0.45]
    if band:
        print("BAND z %.2f n=%d  X %.2f..%.2f  Y %.2f..%.2f" % (zlo, len(band), min(w.x for w in band), max(w.x for w in band), min(w.y for w in band), max(w.y for w in band)))
# head cluster: z>1.55, |x|<0.45
head = [w for w in ws if w.z > 1.55 and abs(w.x) < 0.45]
print("HEAD n=%d Ymin %.3f Ymax %.3f Zmax %.3f" % (len(head), min(w.y for w in head), max(w.y for w in head), max(w.z for w in head)))
# muzzle guess: lowest-front verts
front = sorted(head, key=lambda w: w.y)
print("most -Y:", [tuple(round(v,2) for v in w) for w in front[:3]])
print("most +Y:", [tuple(round(v,2) for v in w) for w in front[-3:]])
