#!/usr/bin/env python3
"""Extract the measurement machinery from bara-proof/scripts/build_bara.py
into bara_machinery.py (verbatim function sources via AST), so Sen is
graded with the identical rulers as the bara proof — no re-implementation
drift. Run once; the extracted module is a build artefact of this folder.
"""
import ast
from pathlib import Path

SRC = Path.home() / "workspace/anthroforge-v2/bara-proof/scripts/build_bara.py"
OUT = Path(__file__).resolve().parent / "bara_machinery.py"
WANT = ["compute_axis", "axis_at", "torso_params", "label_mesh", "plane_loops",
        "loop_perim", "best_loop", "mesh_volume", "grade", "flipped"]

tree = ast.parse(SRC.read_text())
src_lines = SRC.read_text().splitlines()
found = {}
for node in tree.body:
    if isinstance(node, ast.FunctionDef) and node.name in WANT:
        seg = ast.get_source_segment(SRC.read_text(), node)
        found[node.name] = seg
missing = [w for w in WANT if w not in found]
assert not missing, f"missing functions: {missing}"

header = '''"""MEASUREMENT MACHINERY — extracted verbatim from
bara-proof/scripts/build_bara.py (AST source segments, Nov 12, 2026) so
the Sen build is graded with the identical rulers as BARA_PROOF.md.
Globals (FACES_B, BODY_END, mh_neck, mh_crotch, L_mh, mh_pos_mac,
navel_mh, h_mh) are set by the importing script before use.
"""
import numpy as np

FACES_B = None
BODY_END = 13380
mh_neck = mh_crotch = L_mh = None
mh_pos_mac = None
navel_mh = None
h_mh = None

'''
OUT.write_text(header + "\n\n".join(found[w] for w in WANT) + "\n")
print("wrote", OUT, "functions:", list(found))
