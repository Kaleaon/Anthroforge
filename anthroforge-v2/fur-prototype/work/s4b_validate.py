import bpy, sys
sys.path.append("/home/hatch/workspace/anthroforge-v2/fur-prototype/work")
from studio import build_studio, set_camera, set_system_visibility

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.open_mainfile(filepath="/home/hatch/workspace/anthroforge-v2/fur-prototype/work/fur_stage2.blend")
sc = bpy.context.scene
ob = bpy.data.objects["BaraWolfBody"]

cam = build_studio(sc)
set_camera(cam, (-2.0, -4.1, 1.55), (0, 0, 1.0), lens=40)
set_system_visibility(ob, {"FUR_ruff", "FUR_back", "FUR_belly", "FUR_coat"})

sc.render.engine = 'CYCLES'
sc.cycles.samples = 16
sc.cycles.use_denoising = True
sc.cycles.denoiser = 'OPENIMAGEDENOISE'
sc.cycles.device = 'CPU'
sc.render.resolution_x = 440
sc.render.resolution_y = 550
sc.render.filepath = "/home/hatch/workspace/anthroforge-v2/fur-prototype/work/test_strands2.png"
bpy.ops.render.render(write_still=True)
print("VALIDATE RENDER DONE")
