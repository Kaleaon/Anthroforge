import bpy, sys
sys.path.append("/home/hatch/workspace/anthroforge-v2/fur-prototype/work")
from studio import build_studio, set_camera, set_system_visibility

BASE = "/home/hatch/workspace/anthroforge-v2/fur-prototype"
GROOM = {"FUR_ruff", "FUR_back", "FUR_belly", "FUR_coat"}

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.open_mainfile(filepath=BASE + "/work/fur_stage3.blend")
sc = bpy.context.scene
ob = bpy.data.objects["BaraWolfBody"]

# ---------- authoritative stats ----------
print("BODY_VERTS", len(ob.data.vertices))
total_rendered = 0
for ps in ob.particle_systems:
    p = ps.settings
    rendered = p.count * p.rendered_child_count
    total_rendered += rendered
    print(f"PSYS {ps.name}: parents={p.count} child_render={p.rendered_child_count} "
          f"length={p.hair_length:.3f} rendered_strands={rendered}")
print("TOTAL_RENDERED_STRANDS", total_rendered)
for lname in ("LOD0", "LOD1", "LOD2"):
    o = bpy.data.objects.get(f"FurCards_{lname}")
    if o:
        m = o.data
        print(f"CARDS {lname}: verts={len(m.vertices)} tris={sum(len(p.vertices)-2 for p in m.polygons)} "
              f"quads={len(m.polygons)} mats={len(m.materials)}")

# ---------- export LOD1 / LOD2 GLBs (LOD0 already exported by s5) ----------
for lname, fname in (("LOD1", "fur_cards_lod1.glb"), ("LOD2", "fur_cards_lod2.glb")):
    o = bpy.data.objects[f"FurCards_{lname}"]
    was_hidden = o.hide_render
    o.hide_render = False
    o.hide_viewport = False
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.export_scene.gltf(filepath=f"{BASE}/{fname}", export_format='GLB',
                              use_selection=True, export_apply=True)
    o.hide_render = was_hidden
    print("EXPORTED", fname, flush=True)

# ---------- the two renders s6 never reached ----------
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

render("render_boundary_closeup", (800, 800), (0.66, -0.82, 1.66), (0.06, -0.03, 1.50), 70, GROOM, False)
render("render_bodyhair", (800, 800), (-1.18, -1.60, 1.40), (0.05, -0.05, 1.24), 58, {"FUR_bodyhair"}, False)

# ---------- deliverable blend (same end-state s6 intended) ----------
set_system_visibility(ob, GROOM)
cards0.hide_render = True
set_camera(cam, (-2.0, -4.1, 1.55), (0, 0, 1.0), lens=40)
bpy.ops.wm.save_as_mainfile(filepath=BASE + "/fur_prototype.blend")
print("SAVED DELIVERABLE BLEND")
