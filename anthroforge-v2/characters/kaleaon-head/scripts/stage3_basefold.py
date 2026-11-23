#!/usr/bin/env python3
"""Base (stage2 = undeformed v5 layers) exterior/cage fold split."""
import sys
from pathlib import Path

import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from kaleaon_io import fold_stats, group_weights

CHAR = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(CHAR / "work" / "stage2.blend"))
objs = {o.name: o for o in bpy.data.objects if o.type == "MESH"}

for name in ("TissueHead", "Jaw"):
    o = objs[name]
    idx = np.where(group_weights(o, "LipCage") > 0)[0]
    print(name, fold_stats(o, idx, include_worst=True))
print("BASE FOLD SPLIT DONE")
