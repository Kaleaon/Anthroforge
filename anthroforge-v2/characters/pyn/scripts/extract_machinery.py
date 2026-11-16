#!/usr/bin/env python3
"""Extract the composition machinery from bara-proof/scripts/build_bara.py
into pyn_machinery.py, so Pyn is composed with the identical machinery
as the bara proof and the Sen build — no re-implementation drift.

build_bara.py is a sequential build script, so the extraction is by
verbatim line segments plus AST function segments:

  lines 1-566    imports, constants, loads (correspondence, macro base,
                 HIMBO base + OSD blocks), geometry/label/segment
                 machinery, recipes, compose()
  seam           lines 579 + 584 verbatim (torso_params on the HIMBO
                 base + s_hi) — build_bara computes these inside its
                 strongman section; the label builds below need them
  lines 600-753  label builds (hi_lab / mh_lab), kernel constants,
                 torso_field(), limb_fields()
  AST segments   blend(), flipped(), slope_limit(), repair(), fmt(),
                 write_target()

The region-weights block (lines 764-824) is NOT import-time code: it
needs (h_mh, r_mh) from a torso_field() call first. It is extracted
verbatim to w3_block.txt; build_pyn.py execs it in the machinery
namespace after its torso_field call, exactly where build_bara runs it.
"""
import ast
from pathlib import Path

SRC = Path.home() / "workspace/anthroforge-v2/bara-proof/scripts/build_bara.py"
HERE = Path(__file__).resolve().parent

text = SRC.read_text()
lines = text.splitlines()

def seg(a, b):
    """1-indexed inclusive line range."""
    return "\n".join(lines[a - 1:b])

tree = ast.parse(text)
want_fns = ["blend", "flipped", "slope_limit", "repair", "fmt",
            "write_target"]
found = {}
for node in tree.body:
    if isinstance(node, ast.FunctionDef) and node.name in want_fns:
        found[node.name] = ast.get_source_segment(text, node)
missing = [w for w in want_fns if w not in found]
assert not missing, f"missing functions: {missing}"

header = '''"""COMPOSITION MACHINERY — extracted verbatim from
bara-proof/scripts/build_bara.py (line segments + AST function
segments, Nov 16, 2026) so the Pyn build composes with the identical
machinery as BARA_PROOF.md and the Sen build. Importing this module
executes build_bara's loads and label builds (same prints). The
region-weights block lives in w3_block.txt and is exec'd by the
driver after torso_field() provides (h_mh, r_mh).
"""

'''

seam = ("\n\n# ---- seam (build_bara.py lines 579 + 584 verbatim): HIMBO\n"
        "# torso params + scale ratio, needed by the label builds\n"
        + lines[579 - 1] + "\n" + lines[584 - 1] + "\n")

body = (seg(1, 566) + seam + "\n\n" + seg(600, 753) + "\n\n\n"
        + "\n\n".join(found[w] for w in want_fns) + "\n")
# build_bara derives its roots from __file__ (bara-proof/scripts);
# re-anchor at the real locations — every load in the segments is
# read-only, and the extracted module writes nothing.
body = body.replace(
    'OUT = HERE.parent                      # bara-proof/',
    'OUT = Path.home() / "workspace/anthroforge-v2/bara-proof"  # bara-proof/')
assert 'anthroforge-v2/bara-proof' in body
(HERE / "pyn_machinery.py").write_text(header + body)
(HERE / "w3_block.txt").write_text(seg(764, 824) + "\n")
print("wrote pyn_machinery.py + w3_block.txt; functions:", list(found))
