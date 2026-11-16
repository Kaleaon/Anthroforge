#!/usr/bin/env python3
"""Export the masculine neutral as a Wavefront OBJ (canonical frame).

Positions come from work/correspondence_masc.npz (pos_neutral_canonical_m:
masculine-macro body rows aligned into the base.obj frame, helper rows =
raw base.obj). Faces are copied from MPFB2's base.obj so the OBJ is a
drop-in visual reference. Units: metres (base.obj is decimetres; this
export is canonical metres, x right / y forward / z up).
"""
import zipfile
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
OUT = HERE.parent
MPFB_ZIP = Path.home() / "workspace/stick-figure-avatar/photoreal/tools/mpfb2.zip"

z = np.load(OUT / "work" / "correspondence_masc.npz")
pos = z["pos_neutral_canonical_m"]
with zipfile.ZipFile(MPFB_ZIP) as zz:
    lines = zz.read("mpfb/data/3dobjs/base.obj").decode().splitlines()
faces = [l for l in lines if l.startswith("f ")]
out_path = OUT / "masculine_base.obj"
with open(out_path, "w") as fh:
    fh.write("# hm08 MASCULINE base (MPFB macro gender 1.0, else default)\n")
    fh.write("# vertex layout follows base.obj: (x right, up, depth=fwd), metres\n")
    for v in pos:
        # base.obj layout is (x, up, depth) with canonical fwd = +depth:
        # file line = (canon_x, canon_z_up, canon_y_fwd)
        fh.write(f"v {v[0]:.6f} {v[2]:.6f} {v[1]:.6f}\n")
    for l in faces:
        fh.write(l + "\n")
print(f"wrote {out_path}: {len(pos)} verts, {len(faces)} faces")
