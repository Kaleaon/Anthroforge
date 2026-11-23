#!/usr/bin/env python3
"""Independent ship-gate re-check for the Jorge body targets,
parsed back from disk (mirror of bara-proof/work/
gate_check_neckfix.py). House rule: 0 flips AND min normalised
face dot >= 0.01 on BOTH bases (raw base.obj frame + MPFB macro
frame), every component solo and composed."""
import sys
from pathlib import Path

import numpy as np

V2 = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(V2 / "hyper/scripts"))
from hyper_common import (fold_stats, load_base, load_macro,
                          load_target)

TG = Path(__file__).resolve().parents[1] / "targets"
V, F, Fb = load_base()
Vm = load_macro(V)
M = load_target(TG / "body.muscle.target")
W = load_target(TG / "body.chest.width.target")
T = load_target(TG / "body.tissue.jorge.target")
E = load_target(TG / "body.belly.protrusion_terminal_v51.target")
C = load_target(TG / "body.jorge.target")

combos = [("muscle", M), ("width", W), ("tissue", T),
          ("terminal", E), ("muscle+width", M + W),
          ("full (components)", M + W + T + E),
          ("combined file", C)]
worst = 1.0
bad = 0
for nm, D in combos:
    for base, bn in ((V, "raw"), (Vm, "macro")):
        nf, md = fold_stats(base, Fb, D)
        worst = min(worst, md)
        bad += nf
        print(f"  {nm:20s} {bn:5s}: {nf} flips, min_dot {md:+.5f}")
print(f" WORST min_dot {worst:+.5f}; total flips {bad}")
assert bad == 0 and worst >= 0.01, "SHIP GATE FAIL"
print(" SHIP GATE PASS (0 flips, min_dot >= 0.01, both bases)")
