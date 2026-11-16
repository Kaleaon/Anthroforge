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
sc.render.engine = 'CYCLES'
sc.cycles.samples = 32
sc.cycles.use_denoising = True
sc.cycles.denoiser = 'OPENIMAGEDENOISE'
sc.cycles.device = 'CPU'
sc.render.image_settings.file_format = 'PNG'

def render(name, res, cam_pos, cam_tgt, lens, systems, cards_visible):
    set_camera(cam, cam_pos, cam_tgt, lens=lens)
    set_system_visibility(ob, systems)
    cards0.hide_render = not cards_visible
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.filepath = f"{BASE}/{name}.png"
    bpy.ops.render.render(write_still=True)
    print("RENDERED", name, flush=True)

# 1 — hero: strands
render("render_strands", (720, 900), (-2.0, -4.1, 1.55), (0, 0, 1.0), 40, GROOM, False)
# 2 — hero: cards
render("render_cards", (720, 900), (-2.0, -4.1, 1.55), (0, 0, 1.0), 40, set(), True)
# 3 — boundary close-up (cheek ruff meeting neck/coat), strands
render("render_boundary_closeup", (800, 800), (0.66, -0.82, 1.66), (0.06, -0.03, 1.50), 70, GROOM, False)
# 4 — body-hair variant: sparse short chest/forearm system only
render("render_bodyhair", (800, 800), (-1.18, -1.60, 1.40), (0.05, -0.05, 1.24), 58, {"FUR_bodyhair"}, False)

# deliverable blend: hero-strand configuration, studio included
set_system_visibility(ob, GROOM)
cards0.hide_render = True
set_camera(cam, (-2.0, -4.1, 1.55), (0, 0, 1.0), lens=40)
bpy.ops.wm.save_as_mainfile(filepath=BASE + "/fur_prototype.blend")
print("SAVED DELIVERABLE BLEND")
