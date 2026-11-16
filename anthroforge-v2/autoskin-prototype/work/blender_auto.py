"""Method A: Blender automatic weights (bone heat) for the orc bust.

Builds the 36-bone AnthroForge armature (layout from geo_weights.BONES,
hierarchy from anthroforge_3d_pro_v2.html BONE_HIERARCHY), parents each bust
mesh with ARMATURE_AUTO, records per-mesh success/failure, and extracts the
resulting weights to auto_weights.npz (same top-4 format as geo_weights.npz).
Run: blender -b --python blender_auto.py
"""
import bpy, json
import numpy as np

W = "/home/hatch/workspace/anthroforge-v2/autoskin-prototype/work"
BONES = {k: (tuple(v[0]), tuple(v[1])) for k, v in json.load(open(f"{W}/bones.json")).items()}
BONE_NAMES = list(BONES.keys())
PARENTS = {
    "Root": None, "Pelvis": "Root", "Spine1": "Pelvis", "Chest": "Spine1",
    "Neck": "Chest", "Head": "Neck", "Jaw": "Head", "Ear_L": "Head", "Ear_R": "Head",
    "Shoulder_L": "Chest", "Elbow_L": "Shoulder_L", "Wrist_L": "Elbow_L",
    "Shoulder_R": "Chest", "Elbow_R": "Shoulder_R", "Wrist_R": "Elbow_R",
    "Hip_L": "Pelvis", "Knee_L": "Hip_L", "Ankle_L": "Knee_L", "Foot_L": "Ankle_L",
    "Hip_R": "Pelvis", "Knee_R": "Hip_R", "Ankle_R": "Knee_R", "Foot_R": "Ankle_R",
    "Wing_L1": "Chest", "Wing_L2": "Wing_L1", "Wing_R1": "Chest", "Wing_R2": "Wing_R1",
    "Tail_1": "Pelvis", "Tail_2": "Tail_1", "Tail_3": "Tail_2",
    "GenBase": "Pelvis", "GenScrot": "GenBase", "Gen01": "GenBase",
    "Gen02": "Gen01", "Gen03": "Gen02", "Gen04": "Gen03",
}

bpy.ops.wm.read_factory_settings(use_empty=True)

arm_data = bpy.data.armatures.new("AnthroForgeRig")
arm_ob = bpy.data.objects.new("AnthroForgeRig", arm_data)
bpy.context.scene.collection.objects.link(arm_ob)
bpy.context.view_layer.objects.active = arm_ob
bpy.ops.object.mode_set(mode="EDIT")
ebones = {}
for name in BONE_NAMES:
    eb = arm_data.edit_bones.new(name)
    eb.head, eb.tail = BONES[name]
    ebones[name] = eb
for name in BONE_NAMES:
    if PARENTS[name]:
        ebones[name].parent = ebones[PARENTS[name]]
        ebones[name].use_connect = False
bpy.ops.object.mode_set(mode="OBJECT")

bpy.ops.import_scene.gltf(filepath=f"{W}/bust/scene.gltf")
meshes = [ob for ob in bpy.context.scene.objects if ob.type == "MESH"]
print("meshes:", [ob.name for ob in meshes])

log = []
out = {}
for ob in meshes:
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    arm_ob.select_set(True)
    bpy.context.view_layer.objects.active = arm_ob
    err = ""
    try:
        bpy.ops.object.parent_set(type="ARMATURE_AUTO")
    except RuntimeError as e:
        err = str(e)
    # measure coverage: verts with any nonzero group weight
    n = len(ob.data.vertices)
    covered = 0
    Wm = np.zeros((n, 36), np.float32)
    gname = {g.index: g.name for g in ob.vertex_groups}
    for v in ob.data.vertices:
        for ge in v.groups:
            nm = gname.get(ge.group)
            if nm in BONE_NAMES and ge.weight > 0:
                Wm[v.index, BONE_NAMES.index(nm)] = ge.weight
                covered += 1
                break
    frac = covered / max(n, 1)
    status = "OK" if frac > 0.95 else ("PARTIAL" if frac > 0 else "FAILED")
    log.append(f"{ob.name}: {status} covered={covered}/{n} ({frac:.0%}) err={err}")
    print(log[-1])
    s = Wm.sum(axis=1, keepdims=True); s[s == 0] = 1.0; Wm = Wm / s
    idx = np.argsort(-Wm, axis=1)[:, :4]
    w4 = np.take_along_axis(Wm, idx, axis=1)
    s4 = w4.sum(axis=1, keepdims=True); s4[s4 == 0] = 1.0
    key = ob.name.replace(" ", "_")
    out[key + "_bi"] = idx.astype(np.int32)
    out[key + "_w"] = (w4 / s4).astype(np.float32)

np.savez_compressed(f"{W}/auto_weights.npz", **out)
with open(f"{W}/auto_log.txt", "w") as fh:
    fh.write("\n".join(log) + "\n")
print("saved auto_weights.npz")
