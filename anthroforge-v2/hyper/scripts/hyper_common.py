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
import zipfile
from pathlib import Path

import numpy as np

HOME = Path.home()
V2 = HOME / "workspace/anthroforge-v2"
FP = V2 / "first-proof"
BP = V2 / "bara-proof"
HYPER = V2 / "hyper"
MPFB_ZIP = HOME / "workspace/stick-figure-avatar/photoreal/tools/mpfb2.zip"
BODY_END = 13380
NV = 19158


def load_base():
    z = zipfile.ZipFile(MPFB_ZIP)
    obj = z.read("mpfb/data/3dobjs/base.obj").decode().splitlines()
    z.close()
    V, F = [], []
    for l in obj:
        if l.startswith("v "):
            p = l.split()
            V.append([float(p[1]), float(p[3]), float(p[2])])
        elif l.startswith("f "):
            F.append([int(t.split("/")[0]) - 1 for t in l.split()[1:4]])
    V = np.array(V) * 0.1
    F = np.array(F)
    BODY = np.zeros(len(V), bool)
    BODY[:BODY_END] = True
    Fb = F[np.array([BODY[f].all() for f in F])]
    return V, F, Fb


def load_macro(V):
    """Macro base positions in the same canonical frame (range-aligned
    per axis onto the raw body's bbox, verbatim from
    build_coupling_validation.py)."""
    mac = np.load(FP / "work/mh_macro_base.npz")["pos_canonical_m"]
    out = V.copy()
    mb = mac.copy()
    for ax in range(3):
        r0, r1 = V[:BODY_END, ax].min(), V[:BODY_END, ax].max()
        m0, m1 = mb[:, ax].min(), mb[:, ax].max()
        mb[:, ax] = r0 + (mb[:, ax] - m0) * (r1 - r0) / (m1 - m0)
    out[:len(mb)] = mb
    return out


def load_target(path):
    d = np.zeros((NV, 3))
    for line in Path(path).read_text().splitlines():
        if not line or line.startswith("#"):
            continue
        p = line.split()
        d[int(p[0])] = [float(p[1]), float(p[3]), float(p[2])]
    return d * 0.1


def fmt(v):
    s = f"{abs(v):.3f}".rstrip("0")
    if s.endswith("."):
        s += "0"
    if s in ("", "0."):
        s = "0"
    return ("-" + s) if v < 0 else s


def quantise(delta_m):
    """Round a canonical-frame delta (metres) to the .target format's
    quantisation: 3-decimal dm = 0.1 mm steps."""
    d_obj = np.stack([delta_m[:, 0], delta_m[:, 2], delta_m[:, 1]],
                     axis=1) / 0.1
    return np.round(d_obj, 3)


def dequantise(d_obj_q):
    d = np.stack([d_obj_q[:, 0], d_obj_q[:, 2], d_obj_q[:, 1]], axis=1)
    return d * 0.1


def write_target(path, delta_m, note):
    d_obj = np.stack([delta_m[:, 0], delta_m[:, 2], delta_m[:, 1]],
                     axis=1) / 0.1
    moved = np.where(np.abs(d_obj).max(axis=1) > 0.001)[0]
    header = ("# This is a target file for MakeHuman\n#\n"
              "# It was written by the MakeTarget submodule of MPFB\n#\n"
              "# For more information, see MakeHuman's home page at "
              "http://www.makehumancommunity.org\n#\n# basemesh hm08\n"
              f"# {note}\n")
    with open(path, "w") as fh:
        fh.write(header)
        for i in moved:
            fh.write(f"{i} {fmt(d_obj[i, 0])} {fmt(d_obj[i, 1])} "
                     f"{fmt(d_obj[i, 2])}\n")
    return int(len(moved))


def face_dots(base_pos, Fb, delta):
    """Normalised dot(base normal, deformed normal) per body face."""
    P = base_pos + delta
    n0 = np.cross(base_pos[Fb[:, 1]] - base_pos[Fb[:, 0]],
                  base_pos[Fb[:, 2]] - base_pos[Fb[:, 0]])
    n1 = np.cross(P[Fb[:, 1]] - P[Fb[:, 0]], P[Fb[:, 2]] - P[Fb[:, 0]])
    ln = np.linalg.norm(n0, axis=1) * np.linalg.norm(n1, axis=1)
    return np.einsum("ij,ij->i", n0, n1) / np.maximum(ln, 1e-30)


def fold_stats(base_pos, Fb, delta):
    d = face_dots(base_pos, Fb, delta)
    return int((d < 0).sum()), float(d.min())


def body_edges(Fb):
    es = set()
    for a, b, c in Fb:
        for u, v in ((a, b), (b, c), (c, a)):
            es.add((min(u, v), max(u, v)))
    return np.array(sorted(es))


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


def crossings(V, delta):
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
