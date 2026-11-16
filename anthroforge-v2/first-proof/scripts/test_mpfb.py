"""First-proof acceptance test in stock MPFB2 / Blender (headless).

- creates a human with DEFAULT macros (macro-neutral base)
- loads body.belly.protrusion.target via stock TargetService.load_target
  (no code changes anywhere)
- measures the navel landmark's forward displacement at -1 / 0 / +0.5 / +1
  against the canonical anchor from work/qa_numbers.json
- cross-checks belly-face flips at +1 from the evaluated mesh
- renders the four states (profile) + a front view at +1 (Workbench)
Run: blender -b --python test_mpfb.py
"""
import bpy, os, json, importlib, sys
import numpy as np

ROOT = os.path.expanduser("~/workspace/anthroforge-v2/first-proof")
ZIP = os.path.expanduser("~/workspace/stick-figure-avatar/photoreal/tools/mpfb2.zip")
TARGET = os.path.join(ROOT, "body.belly.protrusion.target")
RENDERS = os.path.join(ROOT, "renders")
os.makedirs(RENDERS, exist_ok=True)

qa = json.load(open(os.path.join(ROOT, "work", "qa_numbers.json")))
ANCHOR = qa["anchor_m"]
z = np.load(os.path.join(ROOT, "work", "correspondence.npz"))
NAVEL = int(z["navel_mh"])
MH_TRIS = z["mh_tris"]
BELLY = z["belly_face_mask"].astype(bool)

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete()
try:
    bpy.ops.extensions.package_install_files(
        filepath=ZIP, enable_on_install=True, repo="user_default")
except Exception as e:
    print("install note:", repr(e))
base = next((m for m in list(sys.modules) if m.endswith(".mpfb") or m == "mpfb"), None)
HumanService = importlib.import_module(base + ".services.humanservice").HumanService
TargetService = importlib.import_module(base + ".services.targetservice").TargetService

macro = TargetService.get_default_macro_info_dict()
human = HumanService.create_human(macro_detail_dict=macro)
print("human created, verts:", len(human.data.vertices))

def evaluated_coords(obj_):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj_.evaluated_get(dg)
    return np.array([v.co[:] for v in ev.data.vertices])

pre = evaluated_coords(human)
sk = TargetService.load_target(human, TARGET, weight=0.0,
                               name="body.belly.protrusion")
print("TARGET LOADED via stock load_target ->", sk)
print(f"shape key slider range as loaded: [{sk.slider_min}, {sk.slider_max}]")
# MPFB/Blender shape keys default to [0, 1]; MakeHuman targets are
# one-sided files. Extending slider_min is a property tweak on the key
# (no code change) and is required to exercise the -1 state at all.
sk.slider_min = -1.0
print(f"slider_min extended to {sk.slider_min} for the -1 test state")

states = {}
for w in (-1.0, 0.0, 0.5, 1.0):
    sk.value = w
    states[w] = evaluated_coords(human)
    print(f"evaluated weight {w:+.1f}")

base_coords = states[0.0]
print("weight 0 == pre-load state:", bool(np.allclose(base_coords, pre, atol=1e-7)),
      "| max |diff|:", float(np.abs(base_coords - pre).max()))

# forward axis at navel height: navel vs centroid of the same height band
nav0 = base_coords[NAVEL]
band = np.abs(base_coords[:, 2] - nav0[2]) < 0.03
centre = base_coords[band].mean(axis=0)
fwd = nav0 - centre
fwd[2] = 0.0
fwd = fwd / np.linalg.norm(fwd)
print(f"navel vert {NAVEL} neutral pos {nav0.round(3)}, forward axis {fwd.round(3)}")

results = {}
for w, coords in states.items():
    d = coords[NAVEL] - nav0
    results[w] = {"navel_forward_m": float(d @ fwd),
                  "navel_disp_vec": d.round(4).tolist(),
                  "max_abs_disp_m": float(np.abs(coords - base_coords).max())}
    print(f"w={w:+.1f}: navel forward displacement "
          f"{results[w]['navel_forward_m']*100:+.2f} cm "
          f"(max |disp| anywhere {results[w]['max_abs_disp_m']*100:.1f} cm)")

err_mm = abs(results[1.0]["navel_forward_m"] - ANCHOR) * 1000
print(f"CRITERION 1: anchor {ANCHOR*100:.2f} cm, measured "
      f"{results[1.0]['navel_forward_m']*100:.2f} cm, error {err_mm:.1f} mm "
      f"-> {'PASS' if err_mm <= 5.0 else 'FAIL'} (tolerance 5 mm)")

# belly flip cross-check at +1 from evaluated coords
def face_normals(P, F):
    n = np.cross(P[F[:, 1]] - P[F[:, 0]], P[F[:, 2]] - P[F[:, 0]])
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-14)
Fb = MH_TRIS[BELLY]
n0 = face_normals(base_coords, Fb)
for w in (0.5, 1.0, -1.0):
    nn = face_normals(states[w], Fb)
    dots = np.einsum("ij,ij->i", n0, nn)
    print(f"Blender flip check w={w:+.1f}: flips={int((dots < 0).sum())} "
          f"min_dot={dots.min():.3f} over {len(Fb)} belly faces")

out = {"anchor_m": ANCHOR, "navel_vertex": NAVEL,
       "criterion1_error_mm": err_mm, "states": {str(k): v for k, v in results.items()}}
json.dump(out, open(os.path.join(ROOT, "work", "blender_test.json"), "w"), indent=1)
print("measurements saved to work/blender_test.json", flush=True)

# ---------------------------------------------------------------- renders
scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "SINGLE"
scene.display.shading.single_color = (0.75, 0.72, 0.70)
scene.display.shading.show_cavity = True
scene.display.shading.cavity_type = "BOTH"
scene.render.resolution_x = 640
scene.render.resolution_y = 800
scene.render.film_transparent = False
scene.world = bpy.data.worlds.new("W") if not scene.world else scene.world
scene.world.color = (0.12, 0.12, 0.13)

cam_data = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam
sun_data = bpy.data.lights.new("Sun", "SUN")
sun = bpy.data.objects.new("Sun", sun_data)
scene.collection.objects.link(sun)
sun.rotation_euler = (0.9, 0.2, 0.6)

from mathutils import Vector
def aim(cam_obj, loc, target):
    cam_obj.location = loc
    d = Vector(target) - Vector(loc)
    cam_obj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()

for w, tag, loc, tgt in [
        (-1.0, "w-1.0_profile", (-2.1, -0.35, 1.02), (0, 0, 0.95)),
        (0.0,  "w+0.0_profile", (-2.1, -0.35, 1.02), (0, 0, 0.95)),
        (0.5,  "w+0.5_profile", (-2.1, -0.35, 1.02), (0, 0, 0.95)),
        (1.0,  "w+1.0_profile", (-2.1, -0.35, 1.02), (0, 0, 0.95)),
        (1.0,  "w+1.0_front",   (0.25, -2.3, 1.02), (0, 0, 0.95))]:
    sk.value = w
    aim(cam, loc, tgt)
    scene.render.filepath = os.path.join(RENDERS, f"belly_{tag}.png")
    bpy.ops.render.render(write_still=True)
    print("rendered", scene.render.filepath)

print("TEST DONE", flush=True)
