#!/usr/bin/env python3
"""Quantised ship-gate check for bara-proof targets (neck-field fix).

Loads the SHIPPED .target files (0.1 mm quantised numbers, exactly what
ships) and reports flips + min normalised face dot on both bases, for
each slider solo and for the composed sums. House rule (hyper pass):
the ship gate runs on the shipped quantised numbers with a margin
floor of min_dot >= 0.01.

Usage: gate_check_neckfix.py [label]
"""
import sys
from pathlib import Path


sys.path.insert(0, str(Path.home() / "workspace/anthroforge-v2/hyper/scripts"))
from hyper_common import BP, face_dots, load_base, load_macro, load_target

label = sys.argv[1] if len(sys.argv) > 1 else "run"
V, F, Fb = load_base()
Vm = load_macro(V)

M = load_target(BP / "body.muscle.target")
W = load_target(BP / "body.chest.width.target")
T = load_target(BP / "body.tissue.strongman.target")
C = load_target(BP / "body.bara.strongman.target")

combos = {
    "muscle": M,
    "width": W,
    "tissue": T,
    "muscle+width": M + W,
    "muscle+width+tissue": M + W + T,
    "combined_file": C,
}
print(f"== quantised gate [{label}] ==")
worst = 1.0
for name, D in combos.items():
    for base, bn in ((V, "raw"), (Vm, "macro")):
        dots = face_dots(base, Fb, D)
        nf = int((dots < 0).sum())
        md = float(dots.min())
        worst = min(worst, md)
        flag = "OK " if (nf == 0 and md >= 0.01) else "BELOW-MARGIN"
        print(f"  {name:22s} {bn:5s}: flips {nf}, min_dot {md:+.5f}  {flag}")
print(f"worst min_dot: {worst:+.5f} (floor 0.01)")
