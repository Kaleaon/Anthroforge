#!/usr/bin/env python3
"""Species head verification — identical-ruler before/after from GLBs
(pure python; system python3 + numpy, no Blender).

Rulers are the v3 stage-F rulers as re-implemented in
base-head-v4/work/measure_v4.py, plus the merged surface-true section
width for MuzzleWidth (the ruler BUILD_V4.md's appendix recommends:
the tissue-only vertex slab under-reads because the widest surface at
the muzzle station is jaw).

Sanity: run against the v4 base itself, this script reproduces
base-head-v4/proportions.json (ZB .5466, MuzzleWidth .2332, JawLength
.7128, RamusDepth .2697, ...) to ruler precision.

Targets: species target = neutral + (val/100)*span (species-head-spec
anchors). Because sliders are applied PROPORTIONALLY from neutral
(the base carries deliberate deviations), the build-accuracy column is
built-vs-expected, where expected = base_measured * (target/neutral).
built-vs-target is reported too — it includes the base's own deviation,
inherited, not introduced by the build.

    python3 verify_head.py --base BASE.glb --built CHAR_head.glb \
        --vector VECTOR.json --out work/head_verify.json
"""
import argparse
import json
import struct
from pathlib import Path

import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--base", required=True)
ap.add_argument("--built", required=True)
ap.add_argument("--vector", required=True)
ap.add_argument("--out", required=True)
A = ap.parse_args()

V = {k: float(v) for k, v in json.loads(Path(A.vector).read_text()).items()
     if isinstance(v, (int, float))}

C = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]], float)   # glTF -> head frame
C4 = np.eye(4)
C4[:3, :3] = C


def quat_mat(q):
    x, y, z, w = q
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def read_accessor(g, buf, idx):
    acc = g["accessors"][idx]
    bv = g["bufferViews"][acc["bufferView"]]
    off = bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
    ncomp = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[acc["type"]]
    dt = {5121: "<u1", 5123: "<u2", 5125: "<u4", 5126: "<f4"}[acc["componentType"]]
    stride = bv.get("byteStride")
    itemsize = np.dtype(dt).itemsize * ncomp
    if stride and stride != itemsize:
        raw = np.empty((acc["count"], ncomp),
                       dtype=np.dtype(dt))
        for i in range(acc["count"]):
            raw[i] = np.frombuffer(buf, dtype=dt, count=ncomp,
                                   offset=off + i * stride)
        return raw.astype(np.float64)
    return np.frombuffer(buf, dtype=dt, count=acc["count"] * ncomp,
                         offset=off).reshape(acc["count"], ncomp) \
        .astype(np.float64)


def glb_meshes(path):
    data = Path(path).read_bytes()
    ln = struct.unpack("<I", data[12:16])[0]
    g = json.loads(data[20:20 + ln])
    off = 20 + ln
    bln = struct.unpack("<I", data[off:off + 4])[0]
    buf = data[off + 8:off + 8 + bln]
    out = {}
    for node in g["nodes"]:
        if "mesh" not in node:
            continue
        if "matrix" in node:
            Mg = np.array(node["matrix"], float).reshape(4, 4).T
        else:
            Mg = np.eye(4)
            if "scale" in node:
                Mg[:3, :3] = Mg[:3, :3] @ np.diag(node["scale"])
            if "rotation" in node:
                Mg[:3, :3] = Mg[:3, :3] @ quat_mat(node["rotation"])
            if "translation" in node:
                Mg[:3, 3] = node["translation"]
        Mh = C4 @ Mg @ np.linalg.inv(C4)
        mesh = g["meshes"][node["mesh"]]
        Ps, Fs = [], []
        for prim in mesh["primitives"]:
            P = read_accessor(g, buf, prim["attributes"]["POSITION"])
            P = (C @ P.T).T
            base = sum(len(p) for p in Ps)
            if "indices" in prim:
                idx = read_accessor(g, buf, prim["indices"]).ravel() \
                    .astype(np.int64)
                F = idx.reshape(-1, 3) + base
            else:
                F = np.arange(len(P)).reshape(-1, 3) + base
            Ps.append(P)
            Fs.append(F)
        P = np.concatenate(Ps)
        F = np.concatenate(Fs)
        W = P @ Mh[:3, :3].T + Mh[:3, 3]
        out[node["name"]] = (W, F, Mh[:3, 3].copy())
    return out


def section_width(meshes, ycan):
    """Surface-true section width at y = ycan over merged tissue+jaw:
    x-extent of all triangle-edge / plane intersection points."""
    xs = []
    for name in ("TissueHead", "Jaw"):
        P, F = meshes[name][0], meshes[name][1]
        tris = P[F]
        for t in tris:
            for a, b in ((0, 1), (1, 2), (2, 0)):
                pa, pb = t[a], t[b]
                da, db = pa[1] - ycan, pb[1] - ycan
                if da == 0.0:
                    xs.append(pa[0])
                if da * db < 0:
                    s = da / (da - db)
                    xs.append(pa[0] + s * (pb[0] - pa[0]))
    if not xs:
        return None
    xs = np.array(xs)
    return float(xs.max() - xs.min())


def ear_base_len(P_ear, P_tis):
    """Base = centroid of the ear verts in the nearest quartile to the
    tissue; length = max distance from base (orientation-agnostic —
    works for folded ears, unlike the stage-F lowest-z base)."""
    d = np.empty(len(P_ear))
    for i in range(0, len(P_ear), 512):
        chunk = P_ear[i:i + 512]
        dd = np.sqrt(((chunk[:, None, :] - P_tis[None, :, :]) ** 2)
                     .sum(-1)).min(axis=1)
        d[i:i + 512] = dd
    base = P_ear[d < np.percentile(d, 25)].mean(axis=0)
    return base, float(np.linalg.norm(P_ear - base, axis=1).max())


def rulers(M):
    tis = M["TissueHead"][0]
    nose = float(tis[:, 1].max())
    occ = float(tis[:, 1].min())
    L = nose - occ
    top = float(tis[:, 2].max())
    balls = np.concatenate([M["Eyeball_L"][0], M["Eyeball_R"][0]])
    el = balls[balls[:, 0] < 0]
    er = balls[balls[:, 0] >= 0]
    cl, cr = el.mean(axis=0), er.mean(axis=0)
    ec = 0.5 * (cl + cr)
    ball = float(np.ptp(el, axis=0).max())
    tu = M["TeethUpper"][0]
    ant = tu[tu[:, 1] > ec[1] + 0.10 * L]
    pal = float(ant[:, 2].max())
    ycan = ec[1] + 0.5 * (nose - ec[1])
    slab = tis[np.abs(tis[:, 1] - ycan) < 0.02 * L]
    cran = tis[(tis[:, 1] >= ec[1] - 0.42 * L) & (tis[:, 1] <= ec[1] - 0.06 * L)
               & (tis[:, 2] >= top - 0.11 * L)]
    eb_list, ear_lens, ear_lens_f = [], [], []
    for s in ("L", "R"):
        E = M[f"Ear_{s}"][0]
        b, ln = ear_base_len(E, tis)
        ear_lens.append(ln)
        low = E[np.argsort(E[:, 2])[:max(8, len(E) // 7)]]
        bf = low.mean(axis=0)
        eb_list.append(bf)   # stage-F ear base (measure_v4's eb)
        ear_lens_f.append(float(np.linalg.norm(E - bf, axis=1).max()))
    eb = 0.5 * (eb_list[0] + eb_list[1])
    hinge_y = eb[1] - 0.02 * L
    hinge_node_y = float(M["TeethLower"][2][1])   # jaw pivot, from the GLB node
    jaw = M["Jaw"][0]
    band = jaw[(jaw[:, 1] >= hinge_y - 0.03 * L)
               & (jaw[:, 1] <= hinge_y + 0.05 * L)]
    fh = tis[(np.abs(tis[:, 1] - (ec[1] + 0.01 * L)) < 0.035 * L)
             & (tis[:, 2] >= ec[2]) & (tis[:, 2] <= ec[2] + 0.10 * L)]
    ruff = tis[(tis[:, 2] < pal + 0.10 * L) & (tis[:, 1] < ec[1] - 0.02 * L)]
    stop_probe = tis[np.argmin(((tis[:, 0]) ** 2
                                + (tis[:, 1] - (ec[1] - 0.01 * L)) ** 2
                                + (tis[:, 2] - (ec[2] + 0.095 * L)) ** 2))]
    return {
        "L": L,
        "ZB": float(np.ptp(tis[:, 0])),
        "CraniumWidth_domeShell": float(np.ptp(cran[:, 0])) if len(cran) else None,
        "MuzzleWidth_slab": float(np.ptp(slab[:, 0])) if len(slab) else None,
        "MuzzleWidth_section": section_width(M, ycan),
        "MuzzleDepth": float(slab[:, 2].max() - pal) if len(slab) else None,
        "SkullHeight_domeRise": float(top - ec[2]),
        "MuzzleFrac_antOrbit": float((nose - (ec[1] + ball / 2)) / L),
        "OrbitDiameter": ball,
        "Interorbital": float(abs(cl[0] - cr[0]) - ball),
        "OrbitHeight": float(ec[2] - pal),
        "OrbitRise": float(tis[np.abs(tis[:, 1] - ec[1]) < 0.03 * L][:, 2].max() - ec[2]),
        "EarLength_baseTip": float(np.mean(ear_lens)),
        "EarLength_stageF": float(np.mean(ear_lens_f)),
        "JawLength": float(jaw[:, 1].max() - hinge_y),
        "JawLength_nodeHinge": float(jaw[:, 1].max() - hinge_node_y),
        "JawWidth": float(np.ptp(band[:, 0])) if len(band) else None,
        "RamusDepth": float(np.ptp(band[:, 2])) if len(band) else None,
        "NoseWidth": float(np.ptp(M["NoseLeather"][0][:, 0])),
        "ForeheadWidth_probe": float(np.ptp(fh[:, 0])) if len(fh) else None,
        "RuffZoneWidth_probe": float(np.ptp(ruff[:, 0])) if len(ruff) else None,
        "StopBandZ_probe": float(stop_probe[2]),
        "OcciputY": occ,
        "eye_centre": ec.tolist(), "pal_z": pal,
    }


B = rulers(glb_meshes(A.base))
N = rulers(glb_meshes(A.built))


def rf(neutral, span, val):
    return (neutral + (val / 100.0) * span) / neutral


# station: (label, ruler key, neutral, span, slider)
STATIONS = [
    ("ZB (CheekWidth)", "ZB", 0.58, 0.20, "CheekWidth"),
    ("MuzzleWidth — vertex slab (legacy ruler)", "MuzzleWidth_slab", 0.17, 0.08, "MuzzleWidth"),
    ("MuzzleWidth — merged section (v4-verdict ruler)", "MuzzleWidth_section", 0.17, 0.08, "MuzzleWidth"),
    ("MuzzleDepth", "MuzzleDepth", 0.20, 0.10, "MuzzleDepth"),
    ("MuzzleFrac (MuzzleLength)", "MuzzleFrac_antOrbit", 0.33, 0.20, "MuzzleLength"),
    ("CraniumWidth (dome shell)", "CraniumWidth_domeShell", 0.36, 0.16, "CraniumWidth"),
    ("SkullHeight (CraniumHeight)", "SkullHeight_domeRise", 0.31, 0.12, "CraniumHeight"),
    ("OrbitDiameter (EyeSize)", "OrbitDiameter", 0.15, 0.10, "EyeSize"),
    ("EarLength base->tip (EarHeight)", "EarLength_baseTip", 0.40, 0.65, "EarHeight"),
    ("EarLength stage-F ruler (EarHeight)", "EarLength_stageF", 0.40, 0.65, "EarHeight"),
    ("JawLength", "JawLength", 0.74, 0.10, "JawLength"),
    ("JawWidth", "JawWidth", 0.40, 0.14, "JawWidth"),
    ("RamusDepth (JawDepth)", "RamusDepth", 0.28, 0.12, "JawDepth"),
]
rows = []
for label, key, neutral, span, slider in STATIONS:
    val = V[slider]
    target = neutral + (val / 100.0) * span
    b, n = B[key], N[key]
    exp = b * rf(neutral, span, val) if b else None
    rows.append({
        "station": label, "slider": slider, "value": val,
        "base": round(b, 4) if b else None,
        "built": round(n, 4) if n else None,
        "species_target": round(target, 4),
        "built_vs_target_pct": round(100 * (n / target - 1), 1) if n else None,
        "expected_proportional": round(exp, 4) if exp else None,
        "built_vs_expected_pct": round(100 * (n / exp - 1), 1) if (n and exp) else None,
    })

extra = []
# Interorbital — delta station (EyeSpacing moves centres, not a ratio)
val = V["EyeSpacing"]
exp_d = (val / 100.0) * 0.08
extra.append({"station": "Interorbital (EyeSpacing, delta)",
              "base": round(B["Interorbital"], 4),
              "built": round(N["Interorbital"], 4),
              "delta_measured": round(N["Interorbital"] - B["Interorbital"], 4),
              "delta_expected": round(exp_d, 4)})
# NoseWidth — factor station
val = V["NoseSize"]
extra.append({"station": "NoseWidth (NoseSize, factor)",
              "base": round(B["NoseWidth"], 4),
              "built": round(N["NoseWidth"], 4),
              "ratio_measured": round(N["NoseWidth"] / B["NoseWidth"], 3),
              "ratio_expected": round(rf(0.55, 0.30, val), 3)})
# ForeheadWidth probe — factor station
val = V["ForeheadWidth"]
extra.append({"station": "ForeheadWidth probe (factor)",
              "base": round(B["ForeheadWidth_probe"], 4),
              "built": round(N["ForeheadWidth_probe"], 4),
              "ratio_measured": round(N["ForeheadWidth_probe"] / B["ForeheadWidth_probe"], 3),
              "ratio_expected": round(rf(0.24, 0.12, val), 3)})
# RuffZone probe — swell evidence (no closed-form expectation)
extra.append({"station": "RuffZoneWidth probe (RuffVolume evidence)",
              "base": round(B["RuffZoneWidth_probe"], 4),
              "built": round(N["RuffZoneWidth_probe"], 4),
              "pct_change": round(100 * (N["RuffZoneWidth_probe"] / B["RuffZoneWidth_probe"] - 1), 1)})
# Stop band probe — dip evidence
extra.append({"station": "StopBandZ probe (StopAngle evidence)",
              "base": round(B["StopBandZ_probe"], 4),
              "built": round(N["StopBandZ_probe"], 4),
              "delta": round(N["StopBandZ_probe"] - B["StopBandZ_probe"], 4)})
# Occiput — CraniumLength evidence
val = V["CraniumLength"]
extra.append({"station": "OcciputY (CraniumLength evidence)",
              "base": round(B["OcciputY"], 4),
              "built": round(N["OcciputY"], 4),
              "delta": round(N["OcciputY"] - B["OcciputY"], 4),
              "factor": round(rf(0.62, 0.20, val), 3)})
# JawLength about the node hinge — the stage-F origin (ear-base-derived
# hinge_y) migrates when the ears change shape (population migration,
# the v4 EarLength artefact family); the node-hinge measure is immune.
val = V["JawLength"]
extra.append({"station": "JawLength about node hinge (supplementary)",
              "base": round(B["JawLength_nodeHinge"], 4),
              "built": round(N["JawLength_nodeHinge"], 4),
              "ratio_measured": round(N["JawLength_nodeHinge"] / B["JawLength_nodeHinge"], 4),
              "ratio_expected": round(rf(0.74, 0.10, val), 4)})
# unchanged-check stations
for k in ("OrbitHeight", "OrbitRise"):
    extra.append({"station": f"{k} (no slider — drift check)",
                  "base": round(B[k], 4), "built": round(N[k], 4),
                  "delta": round(N[k] - B[k], 4)})

rep = {"base_rulers": {k: (round(v, 4) if isinstance(v, float) else v)
                       for k, v in B.items()},
       "built_rulers": {k: (round(v, 4) if isinstance(v, float) else v)
                        for k, v in N.items()},
       "stations": rows, "extra": extra}
Path(A.out).write_text(json.dumps(rep, indent=1))

print("| Station | Slider | Base | Built | Species target | Built vs target | Expected (proportional) | Built vs expected |")
print("|---|---|---|---|---|---|---|---|")
for r in rows:
    print(f"| {r['station']} | {r['slider']} {r['value']:+.0f} | {r['base']} | "
          f"{r['built']} | {r['species_target']} | {r['built_vs_target_pct']:+}% | "
          f"{r['expected_proportional']} | {r['built_vs_expected_pct']:+}% |")
print()
for e in extra:
    print(e)
