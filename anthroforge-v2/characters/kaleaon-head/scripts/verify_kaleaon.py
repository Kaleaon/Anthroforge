#!/usr/bin/env python3
"""Kaleaon custom stations (spec S-table rows the family rulers don't
cover): S3 canine-station slab, S8 orbit station, S10 tip height,
S11 head height (both definitions), S12/S13 from the shipped GLB,
S14 growth-ray burial, S15 brow projection, S16 hinge, S18 symmetry,
S19 quantised fold gate. Pure python on the two GLBs."""
import argparse
from collections import defaultdict
import json
import struct
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
CHAR = HERE.parent
CHARS = CHAR.parent
V2 = CHARS.parent
if str(CHARS) not in sys.path:
    sys.path.insert(0, str(CHARS))

from common.verify_head import (  # noqa: E402
    ear_base_len,
    glb_meshes,
    rulers,
    run_verify,
)

DEFAULT_BASE = V2 / "base-head-v5" / "neutral_base_head_v5.glb"
DEFAULT_BUILT = CHAR / "kaleaon_head.glb"
DEFAULT_VECTOR = HERE / "kaleaon_vector.json"
DEFAULT_OUT = CHAR / "work" / "verify_kaleaon.json"
DEFAULT_HEAD_VERIFY_OUT = CHAR / "work" / "head_verify.json"


def W(M, name):
    return M[name][0]


def pal(M):
    return float(W(M, "TeethUpper")[:, 2].max())


def nose(M):
    return float(W(M, "TissueHead")[:, 1].max())


def eyec(M):
    e = np.vstack([M["Eyeball_L"], M["Eyeball_R"]])
    return e.mean(axis=0)


def slab_depth(M, R):
    tis = W(M, "TissueHead")
    jaw = W(M, "Jaw")
    yc = R["nose"] - 0.295 * R["L"]
    band = np.vstack([tis[np.abs(tis[:, 1] - yc) < 0.02 * R["L"]],
                      jaw[np.abs(jaw[:, 1] - yc) < 0.02 * R["L"]]])
    return float(band[:, 2].max() - R["pal_z"])


def section_at(M, R, yc):
    tis = W(M, "TissueHead")
    jaw = W(M, "Jaw")
    band = np.vstack([tis[np.abs(tis[:, 1] - yc) < 0.004],
                      jaw[np.abs(jaw[:, 1] - yc) < 0.004]])
    return float(band[:, 0].max() - band[:, 0].min()) if len(band) else None


def ear_tips(M, R, ec):
    res = {}
    tis = W(M, "TissueHead")
    for s in ("L", "R"):
        E = W(M, f"Ear_{s}")
        qb = ear_base_len(E, tis)[0]
        d = np.linalg.norm(E - qb, axis=1)
        tip_tracked = E[int(np.argmax(d))]
        tip_maxz = E[int(np.argmax(E[:, 2]))]
        res[s] = {"tracked_tip": tip_tracked.tolist(),
                  "tracked_height": float((tip_tracked[2] - R["pal_z"]) / R["L"]),
                  "maxz_height": float((tip_maxz[2] - R["pal_z"]) / R["L"])}
    return res


def heights(M, R):
    tis = W(M, "TissueHead")
    jaw = W(M, "Jaw")
    crown = float(tis[:, 2].max())
    return {"palate_to_crown_L": (crown - R["pal_z"]) / R["L"],
            "total_extent_L": float((max(crown, tis[:, 2].max())
                                     - min(jaw[:, 2].min(), tis[:, 2].min()))
                                    / R["L"])}


def ray_burial(M, R, ec):
    """For each ear: ray from the quartile base through the tracked
    tip; buried if the mane surface along the ray lies at or beyond
    the tip (- 0.005 tolerance). Vectorised Moller-Trumbore."""
    MWl, tris = M["ManeShell"][0], M["ManeShell"][1]
    A = MWl[tris[:, 0]]
    B = MWl[tris[:, 1]]
    C = MWl[tris[:, 2]]
    e1 = B - A
    e2 = C - A

    def first_hit(origin, direction, max_t):
        pvec = np.cross(direction, e2)
        det = np.einsum("ij,ij->i", e1, pvec)
        ok = np.abs(det) > 1e-10
        inv = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)
        tvec = origin - A
        u = np.einsum("ij,ij->i", tvec, pvec) * inv
        qvec = np.cross(tvec, e1)
        v = np.einsum("j,ij->i", direction, qvec) * inv
        t = np.einsum("ij,ij->i", e2, qvec) * inv
        hit = ok & (u >= -1e-6) & (v >= -1e-6) & (u + v <= 1 + 1e-6) \
            & (t > 1e-6) & (t <= max_t)
        return float(t[hit].min()) if hit.any() else None

    tis = W(M, "TissueHead")
    res = {}
    for s in ("L", "R"):
        E = W(M, f"Ear_{s}")
        qb = ear_base_len(E, tis)[0]
        d = np.linalg.norm(E - qb, axis=1)
        tip = E[int(np.argmax(d))]
        direction = tip - qb
        dist_tip = float(np.linalg.norm(direction))
        surf = first_hit(qb, direction / dist_tip, dist_tip * 3)
        res[s] = {"tip_dist": dist_tip, "mane_surface_dist": surf,
                  "buried": bool(surf is not None and surf >= dist_tip - 0.005)}
    return res


def brow_proj(M, R, ec):
    tis = W(M, "TissueHead")
    ez = ec[2]
    brow = tis[(tis[:, 2] > ez + 0.03 * R["L"]) & (tis[:, 2] < ez + 0.13 * R["L"])
               & (np.abs(tis[:, 0]) < 0.12 * R["L"])]
    bridge = tis[(tis[:, 2] > ez - 0.02 * R["L"]) & (tis[:, 2] < ez + 0.03 * R["L"])
                 & (np.abs(tis[:, 0]) < 0.12 * R["L"])]
    return float(brow[:, 1].max() - bridge[:, 1].max())


def node_trans(path):
    data = Path(path).read_bytes()
    jlen = struct.unpack("<I", data[12:16])[0]
    g = json.loads(data[20:20 + jlen])
    return {n["name"]: n.get("translation", [0, 0, 0])
            for n in g["nodes"] if "mesh" in n}


def symmetry(M, name):
    from scipy.spatial import cKDTree
    V = W(M, name)
    tree = cKDTree(V)
    src = V[V[:, 0] > 0.002]
    mir = src * np.array([-1.0, 1.0, 1.0])
    d, _ = tree.query(mir)
    return {"n": int(len(src)), "max": float(d.max()), "mean": float(d.mean())}


def fold_gate(M, name, R):
    V, tris = M[name][0], M[name][1]
    Vq = np.round(V, 4)
    A, B, C = Vq[tris[:, 0]], Vq[tris[:, 1]], Vq[tris[:, 2]]
    n1 = np.cross(B - A, C - A)
    cents = (A + B + C) / 3
    dots = []
    edge = defaultdict(list)
    for fi, t in enumerate(tris):
        for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            edge[(min(a, b), max(a, b))].append(fi)
    nrm = np.linalg.norm(n1, axis=1)
    n1 = n1 / np.maximum(nrm, 1e-12)[:, None]
    for fl in edge.values():
        if len(fl) == 2:
            dots.append(float(n1[fl[0]] @ n1[fl[1]]))
    dots = np.array(dots)
    mouth = np.array([np.abs(cents[f][0]) < 0.30 and cents[f][2] < R["pal_z"] + 0.06
                      and cents[f][1] > R["eye_centre"][1] - 0.14 for f in range(len(tris))])
    pair_mouth = []
    for fl in edge.values():
        if len(fl) == 2:
            pair_mouth.append(bool(mouth[fl[0]] and mouth[fl[1]]))
    pair_mouth = np.array(pair_mouth)
    return {"min_all": float(dots.min()),
            "min_exterior": float(dots[~pair_mouth].min()) if (~pair_mouth).any() else None,
            "n_below_0.01_all": int((dots < 0.01).sum()),
            "n_below_0.01_exterior": int(((dots < 0.01) & ~pair_mouth).sum())}


def verify_kaleaon(base=DEFAULT_BASE, built=DEFAULT_BUILT,
                   vector=DEFAULT_VECTOR, out=DEFAULT_OUT,
                   head_verify_out=DEFAULT_HEAD_VERIFY_OUT):
    run_verify(base, built, vector, head_verify_out)

    Mb = glb_meshes(base)
    Mk = glb_meshes(built)
    Rb = rulers(Mb)
    Rk = rulers(Mk)
    res = {}

    Cb = {n: Mb[n][0] for n in ("Eyeball_L", "Eyeball_R")}
    Ck = {n: Mk[n][0] for n in ("Eyeball_L", "Eyeball_R")}
    ecb, eck = eyec(Cb), eyec(Ck)
    Rb["nose"] = nose(Mb)
    Rk["nose"] = nose(Mk)
    Lb = Rb["L"]
    Lk = Rk["L"]
    res["L"] = {"base": Lb, "built": Lk}

    # --- S3 canine-station muzzle depth (slab at the canine band) -------
    res["S3_canine_slab"] = {"base": slab_depth(Mb, Rb),
                             "built": slab_depth(Mk, Rk)}

    # --- S2 canine-station muzzle width ---------------------------------
    res["S2_canine_section"] = {
        "base": section_at(Mb, Rb, Rb["nose"] - 0.295 * Lb),
        "built": section_at(Mk, Rk, Rk["nose"] - 0.295 * Lk)}

    # --- S8 orbit station u = (nose - eye_y)/L ---------------------------
    res["S8_orbit_station_u"] = {
        "base": (Rb["nose"] - ecb[1]) / Lb,
        "built": (Rk["nose"] - eck[1]) / Lk}

    # --- S10 ear tip height (above palate, built-L units) ----------------
    res["S10_ear_tip_height"] = {"base": ear_tips(Mb, Rb, ecb),
                                 "built": ear_tips(Mk, Rk, eck)}

    # --- S11 head height: palate->crown and total extent -----------------
    res["S11_head_height"] = {"base": heights(Mb, Rb),
                              "built": heights(Mk, Rk)}

    # --- S12/S13 from the shipped mane -----------------------------------
    MW = W(Mk, "ManeShell")
    H_abs = float(W(Mk, "TissueHead")[:, 2].max()) - Rk["pal_z"]
    zmax_i = int(np.argmax(np.abs(MW[:, 0])))
    crown_band = MW[MW[:, 2] > Rk["pal_z"] + 0.85 * H_abs]
    res["S12_S13_mane"] = {
        "width_L": float((MW[:, 0].max() - MW[:, 0].min()) / Lk),
        "z_at_max_frac": float((MW[zmax_i, 2] - Rk["pal_z"]) / H_abs),
        "crown_width_L": float((crown_band[:, 0].max() - crown_band[:, 0].min()) / Lk),
    }

    # --- S14 growth-ray burial -------------------------------------------
    res["S14_growth_ray"] = ray_burial(Mk, Rk, eck)

    # --- S15 brow projection ----------------------------------------------
    res["S15_brow_projection"] = {"base": brow_proj(Mb, Rb, ecb),
                                  "built": brow_proj(Mk, Rk, eck)}

    # --- S16 hinge (GLB node translations) --------------------------------
    ntb, ntk = node_trans(base), node_trans(built)
    res["S16_hinge_nodes"] = {"base_TeethLower": ntb["TeethLower"],
                              "built_TeethLower": ntk["TeethLower"],
                              "built_Jaw": ntk["Jaw"],
                              "built_Tongue": ntk["Tongue"]}

    # --- S18 symmetry (mirrored nearest-vertex) ---------------------------
    res["S18_symmetry"] = {n: symmetry(Mk, n)
                           for n in ("TissueHead", "Jaw", "ManeShell")}

    # --- S19 quantised fold gate ------------------------------------------
    res["S19_fold_gate"] = {
        "base": {n: fold_gate(Mb, n, Rb) for n in ("TissueHead", "Jaw")},
        "built": {n: fold_gate(Mk, n, Rk) for n in ("TissueHead", "Jaw")},
    }

    print(json.dumps(res, indent=1, default=str))
    if out is not None:
        out_path = Path(out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(res, indent=1, default=str))
    print("KALEAON VERIFY DONE")
    return res


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=str(DEFAULT_BASE))
    ap.add_argument("--built", default=str(DEFAULT_BUILT))
    ap.add_argument("--vector", default=str(DEFAULT_VECTOR))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--head-verify-out", default=str(DEFAULT_HEAD_VERIFY_OUT))
    A = ap.parse_args(argv)
    return verify_kaleaon(
        base=A.base,
        built=A.built,
        vector=A.vector,
        out=A.out,
        head_verify_out=A.head_verify_out,
    )


if __name__ == "__main__":
    main()
