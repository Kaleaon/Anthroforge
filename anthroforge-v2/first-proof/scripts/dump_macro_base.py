"""Dump the MPFB2 default-macro human's evaluated vertex positions so the
builder's fold scan can run against the actual test-environment base
(macros change the neutral geometry slightly vs raw base.obj).
Output: work/mh_macro_base.npz with positions in the canonical frame
(x, y-forward, z-up, metres). Blender front is -Y, so y_fwd = -by.
Run: blender -b --python dump_macro_base.py
"""
import bpy, os, importlib, sys
import numpy as np

ROOT = os.path.expanduser("~/workspace/anthroforge-v2/first-proof")
ZIP = os.path.expanduser("~/workspace/stick-figure-avatar/photoreal/tools/mpfb2.zip")

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
dg = bpy.context.evaluated_depsgraph_get()
ev = human.evaluated_get(dg)
B = np.array([v.co[:] for v in ev.data.vertices])
canon = np.stack([B[:, 0], -B[:, 1], B[:, 2]], axis=1)
np.savez(os.path.join(ROOT, "work", "mh_macro_base.npz"), pos_canonical_m=canon)
print(f"dumped macro base: {len(canon)} verts, "
      f"height {canon[:,2].min():.3f}..{canon[:,2].max():.3f} m")
print("DUMP DONE", flush=True)
