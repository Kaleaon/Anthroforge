"""Dump the MPFB2 MASCULINE-macro human's evaluated vertex positions.

Mirror of first-proof/scripts/dump_macro_base.py, with ONE change: the
macro dict is TargetService.get_default_macro_info_dict() with
gender overridden 0.5 -> 1.0 (male). Every other macro value stays at
the exact default the existing proofs used (age/muscle/weight/
proportions/height/cupsize/firmness 0.5, race thirds).

Output: work/mh_macro_base_masculine.npz
  pos_canonical_m : evaluated positions, canonical frame
                    (x right, y forward = -blender_y, z up), metres.
                    NOTE: Blender grounds the human, so z spans
                    ~0..height here; the numpy builder re-aligns this
                    into the base.obj canonical frame (see
                    MASCULINE_BASE.md, frame trap).
  basis_canonical_m : the created human's basis (raw base.obj) vertex
                    positions in the same canonical frame, for the
                    vertex-order correspondence check.
  macro_dict_json : the exact macro dict used.
Run: HOME=/tmp/af_home xvfb-run blender -b --python dump_masculine_base.py
"""
import bpy, os, importlib, sys, json
import numpy as np

ROOT = os.path.expanduser("~/workspace/anthroforge-v2/masculine-base")
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
print("default macro dict:", json.dumps(macro))
macro["gender"] = 1.0
print("masculine macro dict:", json.dumps(macro))

human = HumanService.create_human(macro_detail_dict=macro)
try:
    readback = TargetService.get_macro_info_dict_from_basemesh(human)
    print("readback macro from basemesh:", json.dumps(readback))
except Exception as e:
    print("readback failed:", repr(e))

dg = bpy.context.evaluated_depsgraph_get()
ev = human.evaluated_get(dg)
B = np.array([v.co[:] for v in ev.data.vertices])
canon = np.stack([B[:, 0], -B[:, 1], B[:, 2]], axis=1)
Bb = np.array([v.co[:] for v in human.data.vertices])
basis = np.stack([Bb[:, 0], -Bb[:, 1], Bb[:, 2]], axis=1)
np.savez(os.path.join(ROOT, "work", "mh_macro_base_masculine.npz"),
         pos_canonical_m=canon, basis_canonical_m=basis,
         macro_dict_json=json.dumps(macro))
print(f"dumped masculine macro base: {len(canon)} evaluated verts, "
      f"height {canon[:,2].min():.4f}..{canon[:,2].max():.4f} m, "
      f"x {canon[:,0].min():.3f}..{canon[:,0].max():.3f}, "
      f"y {canon[:,1].min():.3f}..{canon[:,1].max():.3f}")
print(f"basis verts: {len(basis)}, height {basis[:,2].min():.4f}.."
      f"{basis[:,2].max():.4f} m")
print("DUMP DONE", flush=True)
