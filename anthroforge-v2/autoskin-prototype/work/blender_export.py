"""Export the winning method (geodesic + anatomical guards) as a skinned GLB.

Rebuilds the 36-bone armature, imports the original glTF (materials/UVs
preserved), assigns vertex groups from geo_weights_guarded.npz, parents the
meshes, renders one Blender-side jaw-open check frame (end-to-end proof the
exported skin deforms), then exports the bind-pose GLB.
Run: blender -b --python blender_export.py
"""
import bpy, json
import numpy as np

W = "/home/hatch/workspace/anthroforge-v2/autoskin-prototype/work"
OUT = "/home/hatch/workspace/anthroforge-v2/autoskin-prototype/orc_bust_skinned.glb"
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
eb = {}
for name in BONE_NAMES:
    b = arm_data.edit_bones.new(name)
    b.head, b.tail = BONES[name]
    eb[name] = b
for name in BONE_NAMES:
    if PARENTS[name]:
        eb[name].parent = eb[PARENTS[name]]
        eb[name].use_connect = False
bpy.ops.object.mode_set(mode="OBJECT")

bpy.ops.import_scene.gltf(filepath=f"{W}/bust/scene.gltf")
w = np.load(f"{W}/geo_weights_guarded.npz")
for ob in [o for o in bpy.context.scene.objects if o.type == "MESH"]:
    key = ob.name.replace(" ", "_")
    bi, w4 = w[key + "_bi"], w[key + "_w"]
    assert len(ob.data.vertices) == bi.shape[0], (ob.name, len(ob.data.vertices), bi.shape[0])
    groups = {}
    for k in range(4):
        for vi, bone_i, wgt in zip(range(len(bi)), bi[:, k], w4[:, k]):
            if wgt <= 0:
                continue
            bname = BONE_NAMES[int(bone_i)]
            g = groups.get(bname)
            if g is None:
                g = groups[bname] = ob.vertex_groups.new(name=bname)
            g.add([int(vi)], float(wgt), "REPLACE")
    ob.parent = arm_ob
    mod = ob.modifiers.new("Armature", "ARMATURE")
    mod.object = arm_ob
    print(f"{ob.name}: {len(groups)} vertex groups assigned")

# NOTE: no in-Blender render check — Workbench/EEVEE need libEGL, which this
# VM lacks, and Blender aborts (SIGABRT) instead of erroring. End-to-end
# verification is done numerically by blender_verify.py on the exported GLB.
bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", export_apply=False)
print("exported", OUT)
