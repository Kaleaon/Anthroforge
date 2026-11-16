import bpy, sys, time
sys.path.insert(0, "/home/hatch/workspace/anthroforge-v2/fur-craft/a3-geonodes/work")
import importlib.util
spec = importlib.util.spec_from_file_location("bld", "/home/hatch/workspace/anthroforge-v2/fur-craft/a3-geonodes/work/build_geonodes_fur.py")
bld = importlib.util.module_from_spec(spec)
sys.argv = ["blender"]
spec.loader.exec_module(bld)  # defines helpers; __main__ guard prevents build

OUT = "/home/hatch/workspace/anthroforge-v2/fur-craft/a3-geonodes"
bpy.ops.wm.open_mainfile(filepath=f"{OUT}/geonodes_fur.blend")

# --- 1. radius taper patch on the five region objects (idempotent) ---
rg = bld.make_radius_group()
for name in ("AF_Fur_ruff", "AF_Fur_back", "AF_Fur_belly", "AF_Fur_coat", "AF_Fur_bodyhair"):
    ob = bpy.data.objects[name]
    if not any(m.name == "AF Radius" for m in ob.modifiers):
        bld.add_mod(ob, "AF Radius", rg)
        print(f"PATCHED {name}", flush=True)
    else:
        print(f"already patched {name}", flush=True)
bpy.ops.wm.save_as_mainfile(filepath=f"{OUT}/geonodes_fur.blend")
print("PATCH_SAVED", flush=True)

sc = bpy.context.scene
# --- 2. curtain bake (deliverable gap) ---
bld.render_curtain_only_bake()
print("BAKE_DONE", flush=True)

# --- 3. re-render closeup + hero with radius fix ---
for o in bpy.data.objects:
    o.hide_render = False
cam = bld.build_studio(sc)
sc.render.engine = "CYCLES"
sc.cycles.samples = 32
sc.cycles.use_denoising = True
sc.render.film_transparent = False
cam.data.type = "PERSP"
bld.set_camera(cam, (-0.95, -1.35, 1.75), (0.02, 0.05, 1.38), lens=55)
sc.render.resolution_x, sc.render.resolution_y = 800, 800
sc.render.filepath = f"{OUT}/render_geonodes_closeup.png"
t0 = time.time(); bpy.ops.render.render(write_still=True)
print(f"CLOSEUP2_DONE s={time.time()-t0:.1f}", flush=True)
bld.set_camera(cam, (-2.0, -4.1, 1.55), (0, 0, 1.0), lens=40)
sc.render.resolution_x, sc.render.resolution_y = 720, 900
sc.render.filepath = f"{OUT}/render_geonodes_strands.png"
t0 = time.time(); bpy.ops.render.render(write_still=True)
print(f"HERO2_DONE s={time.time()-t0:.1f}", flush=True)
print("FINISH_ALL_DONE", flush=True)
