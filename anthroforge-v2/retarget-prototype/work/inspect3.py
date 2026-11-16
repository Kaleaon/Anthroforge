import bpy, sys
from collections import defaultdict
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=sys.argv[sys.argv.index("--")+1])
arm = [o for o in bpy.data.objects if o.type=='ARMATURE'][0]
print("armature world matrix:", [round(v,3) for row in arm.matrix_world for v in row])
def fcs(a):
    out=[]
    for layer in getattr(a,"layers",[]):
        for strip in layer.strips:
            for cb in getattr(strip,"channelbags",[]):
                out.extend(cb.fcurves)
    return out
for name in ("Walk","Wave"):
    a = bpy.data.actions[name]
    by = defaultdict(list)
    for fc in fcs(a):
        by[fc.data_path].append(fc)
    print(f"--- {name} ({a.frame_range}) keyed paths: {len(by)}")
    for dp, lst in sorted(by.items()):
        if "Hips" in dp or "location" in dp:
            for fc in lst:
                vals=[kp.co[1] for kp in fc.keyframe_points]
                print(f"   {dp}[{fc.array_index}] n={len(vals)} min={min(vals):.3f} max={max(vals):.3f}")
    # which bones have rotation keys
    bones = sorted({dp.split('"')[1] for dp in by if "pose.bones" in dp})
    print("   bones keyed:", bones)
