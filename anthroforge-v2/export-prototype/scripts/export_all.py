"""Stage 1: import the source GLB, dump baseline, export BLEND / DAE / FBX.

Run: blender -b --factory-startup --python export_all.py -- <src.glb> <outdir> <dumpdir>
Profiles:
  DAE  -> Second Life profile (Blender Collada is natively Z-up, which is what
          SL's importer expects; shape keys + animation on, no triangulation,
          no modifier application so weights/shape keys survive).
  FBX  -> Unity profile (Y-up / -Z forward, no leaf bones, FACE smoothing,
          bake all actions).
  BLEND-> native save of the imported scene.
"""
import bpy
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from inspect_core import inspect_scene, write_dump

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, OUTDIR, DUMPDIR = argv[0], argv[1], argv[2]

STEM = "border_collie"

# clean factory scene
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)

write_dump(inspect_scene(), os.path.join(DUMPDIR, "baseline_from_glb.json"))

# ---- BLEND (native) ----
blend_path = os.path.join(OUTDIR, STEM + ".blend")
bpy.ops.wm.save_as_mainfile(filepath=blend_path)
print("SAVED BLEND", blend_path)

# ---- DAE ----
# Blender 5.2 REMOVED the built-in Collada exporter (bpy.ops.wm.collada_export
# no longer exists). The DAE is therefore produced by the standalone writer:
#   scripts/dump_interchange.py  (Blender -> scene interchange JSON/NPZ)
#   scripts/write_dae.py         (pycollada -> SL-profile .dae)
# See SURVIVAL.md. The DAE operator call that older Blenders used was:
#   bpy.ops.wm.collada_export(filepath, apply_modifiers=False,
#       export_animation=True, include_animations=True, include_armatures=True,
#       include_shapekeys=True, deform_bones_only=False, triangulate=False,
#       keep_bind_info=True)
print("DAE: deferred to write_dae.py (no Collada op in Blender 5.2)")

# ---- FBX (Unity profile) ----
fbx_path = os.path.join(OUTDIR, STEM + "_Unity.fbx")
bpy.ops.export_scene.fbx(
    filepath=fbx_path,
    check_existing=False,
    use_selection=False,
    global_scale=1.0,
    apply_unit_scale=True,
    apply_scale_options="FBX_SCALE_UNITS",
    use_space_transform=True,
    bake_space_transform=False,
    object_types={"ARMATURE", "MESH", "EMPTY"},
    use_mesh_modifiers=True,
    mesh_smooth_type="FACE",
    use_tspace=True,
    add_leaf_bones=False,        # Unity: leaf bones create junk end bones
    primary_bone_axis="Y",
    secondary_bone_axis="X",
    use_armature_deform_only=False,
    armature_nodetype="NULL",
    bake_anim=True,
    bake_anim_use_all_bones=True,
    bake_anim_use_nla_strips=True,
    bake_anim_use_all_actions=True,
    bake_anim_force_startend_keying=True,
    bake_anim_step=1.0,
    bake_anim_simplify_factor=0.0,
    path_mode="AUTO",
    embed_textures=False,
    axis_forward="-Z",           # Unity convention
    axis_up="Y",
)
print("EXPORTED FBX", fbx_path)
print("STAGE1 DONE")
