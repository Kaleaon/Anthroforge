"""Stage 2: re-import one exported file into a clean scene and dump metrics.

Run: blender -b --factory-startup --python reimport.py -- <file> <dump.json>
For .blend the file is opened as the mainfile instead of imported.
"""
import bpy
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from inspect_core import inspect_scene, write_dump

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, DUMP = argv[0], argv[1]
ext = os.path.splitext(SRC)[1].lower()

if ext == ".blend":
    bpy.ops.wm.open_mainfile(filepath=SRC)
elif ext == ".dae":
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.collada_import(filepath=SRC, auto_connect=True, find_chains=True)
elif ext == ".fbx":
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(
        filepath=SRC,
        use_custom_normals=True,
        use_custom_props=True,
        ignore_leaf_bones=False,
        force_connect_children=False,
        automatic_bone_orientation=False,
        primary_bone_axis="Y",
        secondary_bone_axis="X",
        use_prepost_rot=True,
        use_anim=True,
    )
else:
    raise SystemExit("unknown ext " + ext)

write_dump(inspect_scene(), DUMP)
print("STAGE2 DONE", SRC)
