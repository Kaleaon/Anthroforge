import bpy, math, os
from mathutils import Matrix, Vector
MODELS = os.path.expanduser("~/workspace/stick-figure-avatar/furry-lineup/threejs-lineup/models")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.render.fps = 30
bpy.ops.import_scene.gltf(filepath=os.path.join(MODELS, "bara_wolf_avatar.glb"))
wolf = bpy.data.objects["BaraWolf"]
SRC = {a.name: a for a in bpy.data.actions}
for a in SRC.values(): a.use_fake_user = True
if wolf.animation_data:
    for t in list(wolf.animation_data.nla_tracks): wolf.animation_data.nla_tracks.remove(t)
    wolf.animation_data.action = None
bpy.ops.import_scene.gltf(filepath=os.path.join(MODELS, "pyn_fennec.glb"))
fen = [o for o in bpy.data.objects if o.type=='ARMATURE' and o != wolf][0]
print("fen rotation_euler before:", tuple(round(math.degrees(v),1) for v in fen.rotation_euler))
fen.rotation_euler = (0,0,0)
bpy.context.view_layer.update()
print("fen hips world after zeroing:", tuple(round(v,3) for v in (fen.matrix_world @ fen.pose.bones["Hips_01"].matrix.translation)))

P = "mixamorig:"
MAP = {P+"Hips":"Hips_01", P+"Spine":"Spine_02", P+"Spine1":"Chest_001_03", P+"Spine2":"Chest_06",
       P+"Neck":"Neck_07", P+"Head":"Head_08", P+"LeftUpLeg":"Left leg_068", P+"LeftLeg":"Middleleg_L_069",
       P+"LeftFoot":"Foot1_L_070", P+"LeftToeBase":"Foot2_L_071",
       P+"RightArm":"Right arm_045", P+"RightForeArm":"Middlearm_R_046", P+"RightHand":"Right wrist_047"}
Rs = {b.name: b.matrix_local.copy() for b in wolf.data.bones}
Rt = {b.name: b.matrix_local.copy() for b in fen.data.bones}
def depth(b):
    d=0
    while b.parent: d+=1; b=b.parent
    return d
order = [b.name for b in sorted(fen.data.bones, key=depth)]
inv = {v:k for k,v in MAP.items()}
F = 10
wolf.animation_data_create(); wolf.animation_data.action = SRC["Walk"]
bpy.context.scene.frame_set(F); bpy.context.view_layer.update()
dQ, dpos = {}, None
for s in MAP:
    Pm = wolf.pose.bones[s].matrix
    dQ[s] = Pm.to_quaternion() @ Rs[s].to_quaternion().inverted()
    if s.endswith("Hips"): dpos = Pm.translation - Rs[s].translation
Rr = (Rt["Hips_01"].translation.z) / (Rs[P+"Hips"].translation.z)
desired = {}
for bn in order:
    bone = fen.data.bones[bn]; R = Rt[bn]; par = bone.parent.name if bone.parent else None
    if par is None: base = R.translation.copy()
    else: base = desired[par] @ (Rt[par].inverted() @ R.translation)
    if bn in inv:
        Q = dQ[inv[bn]] @ R.to_quaternion()
        pos = R.translation + dpos * Rr if bn == "Hips_01" else base
    elif par is None: Q, pos = R.to_quaternion(), base
    else:
        Q = desired[par].to_quaternion() @ (Rt[par].to_quaternion().inverted() @ R.to_quaternion())
        pos = base
    desired[bn] = Matrix.LocRotScale(pos, Q, (1,1,1))
wolf.animation_data.action = None

def basis_of(bn):
    """matrix_basis that yields desired pose matrix, given desired parent matrix."""
    bone = fen.data.bones[bn]; R = Rt[bn]; par = bone.parent.name if bone.parent else None
    if par is None: return R.inverted() @ desired[bn]
    return R.inverted() @ Rt[par] @ desired[par].inverted() @ desired[bn]

def try_method(name, setter):
    if fen.animation_data is None: fen.animation_data_create()
    act = bpy.data.actions.new("PROBE_"+name); act.use_fake_user = True
    fen.animation_data.action = act
    for bn in MAP.values():
        pb = fen.pose.bones[bn]; pb.rotation_mode = 'QUATERNION'
        setter(pb, bn)
        pb.keyframe_insert(data_path="rotation_quaternion", frame=F)
        pb.keyframe_insert(data_path="location", frame=F)
    # reset pose to rest, evaluate from action only
    for pb in fen.pose.bones:
        pb.location = (0,0,0); pb.rotation_quaternion = (1,0,0,0); pb.scale = (1,1,1)
    bpy.context.scene.frame_set(F); bpy.context.view_layer.update()
    wt = wr = 0.0
    for bn in MAP.values():
        E = fen.pose.bones[bn].matrix; M = desired[bn]
        wt = max(wt, (E.translation - M.translation).length)
        dq = E.to_quaternion() @ M.to_quaternion().inverted()
        wr = max(wr, abs(dq.angle))
    print(f"METHOD {name}: max pos dev {wt*1000:.2f} mm, max rot dev {math.degrees(wr):.3f} deg")
    fen.animation_data.action = None
    bpy.data.actions.remove(act)

def m1(pb, bn): pb.matrix = desired[bn]
def m2(pb, bn):
    B = basis_of(bn); pb.matrix_basis = B
def m3(pb, bn):
    B = basis_of(bn); pb.location = B.translation.copy(); pb.rotation_quaternion = B.to_quaternion()
def m4(pb, bn):
    pb.matrix = desired[bn]; bpy.context.view_layer.update()
for nm, fn in (("M1_matrix", m1), ("M2_basis", m2), ("M3_channels", m3), ("M4_matrix_update", m4)):
    try_method(nm, fn)
print("PROBE DONE")
