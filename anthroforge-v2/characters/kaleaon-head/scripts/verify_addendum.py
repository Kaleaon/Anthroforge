#!/usr/bin/env python3
"""Addendum measures: S2 station migration, S15 profile brow
projection, S18 base comparison, S19 offender locations.
Pure python on the GLBs."""
import argparse
from collections import defaultdict
import json
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
CHAR = HERE.parent
CHARS = CHAR.parent
V2 = CHARS.parent
if str(CHARS) not in sys.path:
    sys.path.insert(0, str(CHARS))

from common.verify_head import glb_meshes, rulers  # noqa: E402

DEFAULT_BASE = V2 / "base-head-v5" / "neutral_base_head_v5.glb"
DEFAULT_BUILT = CHAR / "kaleaon_head.glb"
DEFAULT_OUT = CHAR / "work" / "verify_addendum.json"


def W(M, n):
    return M[n][0]


# --- S2 station migration ---------------------------------------------
def section(M, yc, half=0.004):
    tis = W(M, "TissueHead")
    jaw = W(M, "Jaw")
    band = np.vstack([tis[np.abs(tis[:, 1] - yc) < half],
                      jaw[np.abs(jaw[:, 1] - yc) < half]])
    return float(band[:, 0].max() - band[:, 0].min()) if len(band) else None


# --- S15 profile brow projection ---------------------------------------
def brow_profile(M, R):
    tis = W(M, "TissueHead")
    ec = np.array(R["eye_centre"])
    ez = ec[2]
    prof = tis[np.abs(tis[:, 0]) < 0.03]
    bins = {}
    for z0 in np.arange(-0.30, 0.45, 0.01):
        row = prof[np.abs(prof[:, 2] - z0) < 0.005]
        if len(row):
            bins[round(float(z0), 2)] = float(row[:, 1].max())

    def yprof(z):
        ks = sorted(bins)
        return float(np.interp(z, ks, [bins[k] for k in ks]))

    z_stop, z_nose = ez - 0.01, ez - 0.09
    y_stop, y_nose = yprof(z_stop), yprof(z_nose)
    worst = 0.0
    for z in np.arange(ez + 0.03, ez + 0.115, 0.005):
        line = y_stop + (y_nose - y_stop) * (z - z_stop) / (z_nose - z_stop)
        worst = max(worst, yprof(z) - line)
    return worst


# --- S18 base comparison -------------------------------------------------
def symmetry(M, name):
    V = W(M, name)
    tree = cKDTree(V)
    src = V[V[:, 0] > 0.002]
    d, _ = tree.query(src * np.array([-1.0, 1.0, 1.0]))
    i = int(np.argmax(d))
    return {"max": float(d.max()), "mean": float(d.mean()),
            "worst_at": src[i].tolist()}


# --- S19 offender locations ----------------------------------------------
def offenders(M, name, R):
    V, tris = M[name][0], M[name][1]
    Vq = np.round(V, 4)
    A, B, C = Vq[tris[:, 0]], Vq[tris[:, 1]], Vq[tris[:, 2]]
    n1 = np.cross(B - A, C - A)
    n1 = n1 / np.maximum(np.linalg.norm(n1, axis=1), 1e-12)[:, None]
    cents = (A + B + C) / 3
    edge = defaultdict(list)
    for fi, t in enumerate(tris):
        for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            edge[(min(a, b), max(a, b))].append(fi)
    ec = np.array(R["eye_centre"])
    pal = R["pal_z"]
    res = []
    for fl in edge.values():
        if len(fl) == 2:
            d = float(n1[fl[0]] @ n1[fl[1]])
            if d < 0.01:
                c = cents[fl].mean(axis=0)
                in_mouth = bool(np.abs(c[0]) < 0.30 and c[2] < pal + 0.06
                                and c[1] > ec[1] - 0.14)
                res.append({"dot": d, "centroid": c.tolist(),
                            "in_mouth_zone_stage3_def": in_mouth})
    return res


def verify_addendum(base=DEFAULT_BASE, built=DEFAULT_BUILT, out=DEFAULT_OUT):
    Mb = glb_meshes(base)
    Mk = glb_meshes(built)
    Rb = rulers(Mb)
    Rk = rulers(Mk)
    res = {}

    nose_b = float(W(Mb, "TissueHead")[:, 1].max())
    nose_k = float(W(Mk, "TissueHead")[:, 1].max())
    res["S2_migration"] = {
        "base_at_own_station": section(Mb, nose_b - 0.295 * Rb["L"]),
        "built_at_own_station": section(Mk, nose_k - 0.295 * Rk["L"]),
        "built_at_base_absolute_station": section(Mk, nose_b - 0.295 * Rb["L"]),
        "base_at_built_absolute_station": section(Mb, nose_k - 0.295 * Rk["L"]),
    }

    res["S15_profile"] = {"base": brow_profile(Mb, Rb),
                          "built": brow_profile(Mk, Rk)}

    res["S18_base"] = {n: symmetry(Mb, n) for n in ("TissueHead", "Jaw")}
    res["S18_built_worst"] = {n: symmetry(Mk, n) for n in ("TissueHead", "Jaw")}

    res["S19_offenders"] = {
        "base": {n: offenders(Mb, n, Rb) for n in ("TissueHead", "Jaw")},
        "built": {n: offenders(Mk, n, Rk) for n in ("TissueHead", "Jaw")},
    }
    print(json.dumps(res, indent=1, default=str))
    if out is not None:
        out_path = Path(out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(res, indent=1, default=str))
    print("ADDENDUM DONE")
    return res


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=str(DEFAULT_BASE))
    ap.add_argument("--built", default=str(DEFAULT_BUILT))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    A = ap.parse_args(argv)
    return verify_addendum(base=A.base, built=A.built, out=A.out)


if __name__ == "__main__":
    main()
