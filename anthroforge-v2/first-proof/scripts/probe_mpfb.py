"""Probe the MPFB2 chain empirically (first-proof step 0 gate):
- install MPFB2 from the local zip, create a human with DEFAULT macros
- verify basis vertex i == base.obj vertex i under the swizzle
  (x_o, -z_o, y_o) * scale_factor, and recover scale_factor
- validate with a KNOWN bundled target (stomach-tone-incr): load at
  weight 1.0 via stock TargetService.load_target, measure a known
  vertex's evaluated displacement vs the file's stated offset.
Run: blender -b --python probe_mpfb.py
"""
import bpy, sys, os, zipfile, gzip, importlib
import numpy as np

ZIP = os.path.expanduser("~/workspace/stick-figure-avatar/photoreal/tools/mpfb2.zip")
TMP = "/tmp/first_proof_probe"
os.makedirs(TMP, exist_ok=True)

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete()
try:
    bpy.ops.extensions.package_install_files(
        filepath=ZIP, enable_on_install=True, repo="user_default")
except Exception as e:
    print("install note:", repr(e))
base = next((m for m in list(sys.modules) if m.endswith(".mpfb") or m == "mpfb"), None)
if not base:
    raise SystemExit("MPFB not loaded")
print("MPFB module base:", base)
HumanService = importlib.import_module(base + ".services.humanservice").HumanService
TargetService = importlib.import_module(base + ".services.targetservice").TargetService

macro = TargetService.get_default_macro_info_dict()
print("DEFAULT MACRO:", macro)
human = HumanService.create_human(macro_detail_dict=macro)
print("human object:", human.name, "verts:", len(human.data.vertices))

# ---- base.obj from the zip
with zipfile.ZipFile(ZIP) as zf:
    obj_text = zf.read("mpfb/data/3dobjs/base.obj").decode()
    tone_gz = zf.read("mpfb/data/targets/stomach/stomach-tone-incr.target.gz")
verts = []
for line in obj_text.splitlines():
    if line.startswith("v "):
        _, x, y, z = line.split()
        verts.append((float(x), float(y), float(z)))
obj = np.array(verts)
print("base.obj verts:", len(obj))

basis = np.array([v.co[:] for v in human.data.vertices])
if human.data.shape_keys and "Basis" in human.data.shape_keys.key_blocks:
    basis = np.array([v.co[:] for v in
                      human.data.shape_keys.key_blocks["Basis"].data])
print("basis verts:", len(basis))

# fit scale factor under the swizzle (x_o, -z_o, y_o)
swz = np.stack([obj[:, 0], -obj[:, 2], obj[:, 1]], axis=1)
n = min(len(basis), len(obj))
ratio = np.linalg.norm(basis[:n], axis=1) / np.maximum(np.linalg.norm(swz[:n], axis=1), 1e-9)
sf = float(np.median(ratio))
print(f"scale_factor (fitted): {sf:.6f}")
pred = swz[:n] * sf
err = np.linalg.norm(basis[:n] - pred, axis=1)
print(f"basis vs swizzled base.obj: max err {err.max():.2e}, "
      f"p95 {np.percentile(err, 95):.2e} (Blender units)")

# facing: front verts in obj frame have z_o > 1; where do they sit in Blender?
front = obj[:, 2] > 1.0
print("front-vert Blender centroid:", basis[:n][front].mean(axis=0).round(3),
      "| overall centroid:", basis[:n].mean(axis=0).round(3))
print("Blender bbox min:", basis.min(axis=0).round(3), "max:", basis.max(axis=0).round(3))

# ---- known bundled target validation
tone_path = os.path.join(TMP, "stomach-tone-incr.target")
with open(tone_path, "wb") as fh:
    fh.write(gzip.decompress(tone_gz))
offs = {}
for line in open(tone_path):
    if line.startswith("#") or not line.strip():
        continue
    p = line.split()
    offs[int(p[0])] = (float(p[1]), float(p[2]), float(p[3]))
print("stomach-tone offsets:", len(offs))
vi = max(offs, key=lambda i: abs(offs[i][1]))
print(f"probe vertex {vi}, file offset (dm): {offs[vi]}")

def evaluated_coords(obj_):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj_.evaluated_get(dg)
    return np.array([v.co[:] for v in ev.data.vertices])

before = evaluated_coords(human)
sk = TargetService.load_target(human, tone_path, weight=1.0, name="probe_tone")
print("load_target returned:", sk)
after = evaluated_coords(human)
d = after[vi] - before[vi]
a, b, c = offs[vi]
expected = np.array([a, -c, b]) * sf
print(f"measured displacement: {d} | expected (a,-c,b)*sf: {expected} "
      f"| err {np.linalg.norm(d - expected):.2e}")
print("PROBE DONE")
