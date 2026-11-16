import bpy, sys
sys.path.append("/home/hatch/workspace/anthroforge-v2/fur-prototype/work")
from studio import build_studio, set_camera, set_system_visibility

BASE = "/home/hatch/workspace/anthroforge-v2/fur-prototype"
GROOM = {"FUR_ruff", "FUR_back", "FUR_belly", "FUR_coat"}

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.open_mainfile(filepath=BASE + "/work/fur_stage3.blend")
sc = bpy.context.scene
ob = bpy.data.objects["BaraWolfBody"]
cards0 = bpy.data.objects["FurCards_LOD0"]

cam = build_studio(sc)
set_system_visibility(ob, GROOM)
cards0.hide_render = True
set_camera(cam, (-2.0, -4.1, 1.55), (0, 0, 1.0), lens=40)
bpy.ops.wm.save_as_mainfile(filepath=BASE + "/fur_prototype.blend")
print("SAVED DELIVERABLE BLEND")
