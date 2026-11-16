import bpy, sys
sys.path.append("/home/hatch/workspace/anthroforge-v2/fur-prototype/work")
from studio import build_studio, set_camera, set_system_visibility

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.open_mainfile(filepath="/home/hatch/workspace/anthroforge-v2/fur-prototype/work/fur_stage2.blend")
sc = bpy.context.scene
ob = bpy.data.objects["BaraWolfBody"]

cam = build_studio(sc)
set_camera(cam, (-1.55, -2.75, 1.42), (0, -0.02, 1.02), lens=50)
set_system_visibility(ob, {"FUR_ruff", "FUR_back", "FUR_belly", "FUR_coat"})

sc.render.engine = 'CYCLES'
sc.cycles.samples = 16
sc.cycles.use_denoising = False
sc.cycles.device = 'CPU'
sc.render.resolution_x = 480
sc.render.resolution_y = 600
sc.render.filepath = "/home/hatch/workspace/anthroforge-v2/fur-prototype/work/test_strands.png"
bpy.ops.render.render(write_still=True)
print("TEST RENDER DONE")
