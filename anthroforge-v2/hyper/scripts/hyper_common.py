#!/usr/bin/env python3
"""Shared machinery for the AnthroForge hyper-range work.

Frames/loaders follow B16's audit_hyper.py EXACTLY (so numbers compare
with MORPH_CRAFT.md section 8): base.obj verts (x, z, y) * 0.1 -> metres,
index 0 = lateral, index 1 = depth, index 2 = height. Target files are
MPFB .target (dm, obj axis order); write_target inverts the loader.
Fold gates run on BOTH bases (raw base.obj frame + MPFB macro frame,
range-aligned per build_coupling_validation.py) -- the house standard
since the v1 belly proof.
"""
import sys
from pathlib import Path

import numpy as np

V2 = Path(__file__).resolve().parents[2]
APP = V2.parent / "anthroforge-app"
for _p in (str(V2), str(APP)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from body_machinery.osd import (  # noqa: E402
    BODY_END,
    HM08_N_VERTS as NV,
    align_macro_base,
    load_mpfb_base_obj,
)
from body_machinery.repair import (  # noqa: E402
    body_edges,
    dequantise,
    face_dots,
    fold_stats,
    neighbours_of,
    quantise,
)
from core.geometry import fmt, parse_target, write_target  # noqa: E402

HOME = Path.home()
FP = V2 / "first-proof"
BP = V2 / "bara-proof"
HYPER = V2 / "hyper"
MPFB_ZIP = HOME / "workspace/stick-figure-avatar/photoreal/tools/mpfb2.zip"


def load_base():
    return load_mpfb_base_obj(MPFB_ZIP, with_first_tri_faces=True, body_end=BODY_END)


def load_macro(V):
    """Macro base positions in the same canonical frame (range-aligned
    per axis onto the raw body's bbox, verbatim from
    build_coupling_validation.py)."""
    mac = np.load(FP / "work/mh_macro_base.npz")["pos_canonical_m"]
    return align_macro_base(V, mac, body_end=BODY_END)


def load_target(path):
    return parse_target(path, NV)


def thigh_band(V):
    """B16's interpenetration band, from audit_hyper.py lines 62-65
    (zleg = below the 40th percentile of body height). An earlier copy
    here used the 42nd percentile; corrected Nov 12, 2026 -- on hm08
    the two bands differ by a handful of verts and no gate outcome in
    this pass changes, but B16's is the canonical one."""
    BODY = np.zeros(len(V), bool)
    BODY[:BODY_END] = True
    thigh = BODY & (np.abs(V[:, 0]) > 0.02)
    zleg = V[:, 2] < np.percentile(V[BODY, 2], 40)
    return thigh & zleg & (np.abs(V[:, 0]) < 0.16)


def crossings(V, Fb, delta):
    band = thigh_band(V)
    P = V + delta
    return int(((V[band, 0] > 0) & (P[band, 0] < 0)).sum()
               + ((V[band, 0] < 0) & (P[band, 0] > 0)).sum())


def min_thigh_gap(V, delta):
    """Minimum distance between left and right inner-thigh surfaces in
    the B16 band, via each crossed-side vert's distance to the nearest
    opposite-side vert in the band (brute force on the band subset)."""
    band = np.where(thigh_band(V))[0]
    P = V + delta
    L = band[P[band, 0] < 0]
    R = band[P[band, 0] > 0]
    if len(L) == 0 or len(R) == 0:
        return float("nan")
    best = np.inf
    for s in range(0, len(L), 256):
        d = np.linalg.norm(P[L[s:s + 256], None, :] - P[None, R, :],
                           axis=2)
        best = min(best, float(d.min()))
    return best
