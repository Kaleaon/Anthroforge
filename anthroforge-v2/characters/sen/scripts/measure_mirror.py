#!/usr/bin/env python3
"""L/R mirror quantification for the Sen head rebuild (pure python).

Measures the stations the name-keyed-side bug touched — eyeball
centres (EyeSpacing) and ear bases (EarSpread) — plus tongue extent,
on any head GLB with the house object names, in head-local units
normalised by each file's own tissue length L. GLB parsing copied
from characters/pyn/scripts/verify_head.py (same glTF -> head-frame
conversion, so numbers are directly comparable with the verify
stations and with each other across bases).

    python3 measure_mirror.py LABEL=path.glb [LABEL=path.glb ...] \
        --out work/mirror_measure.json
"""
import argparse
import json
import struct
from pathlib import Path

import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("files", nargs="+")
ap.add_argument("--out")
A = ap.parse_args()

C = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]], float)
C4 = np.eye(4)
C4[:3, :3] = C


def quat_mat(q):
    x, y, z, w = q
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w),
         1 - 2 * (x * x + y * y)]])


def read_accessor(g, buf, idx):
    acc = g["accessors"][idx]
    bv = g["bufferViews"][acc["bufferView"]]
    off = bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
    ncomp = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[acc["type"]]
    dt = {5121: "<u1", 5123: "<u2", 5125: "<u4", 5126: "<f4"}[acc["componentType"]]
    stride = bv.get("byteStride")
    itemsize = np.dtype(dt).itemsize * ncomp
    if stride and stride != itemsize:
        raw = np.empty((acc["count"], ncomp), dtype=np.dtype(dt))
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
        Ps = []
        for prim in mesh["primitives"]:
            P = read_accessor(g, buf, prim["attributes"]["POSITION"])
            P = (C @ P.T).T
            Ps.append(P)
        P = np.concatenate(Ps)
        W = P @ Mh[:3, :3].T + Mh[:3, 3]
        out[node["name"]] = W
    return out


def ear_base(P_ear, P_tis):
    d = np.empty(len(P_ear))
    for i in range(0, len(P_ear), 512):
        chunk = P_ear[i:i + 512]
        dd = np.sqrt(((chunk[:, None, :] - P_tis[None, :, :]) ** 2)
                     .sum(-1)).min(axis=1)
        d[i:i + 512] = dd
    return P_ear[d < np.percentile(d, 25)].mean(axis=0)


def measure(path):
    M = glb_meshes(path)
    tis = M["TissueHead"]
    L = float(np.ptp(tis[:, 1]))
    r = {"L": round(L, 5)}
    eyes = {}
    for s in ("L", "R"):
        c = M[f"Eyeball_{s}"].mean(axis=0)
        eyes[s] = c
        r[f"eye_{s}_centre"] = [round(float(v / L), 4) for v in c]
    r["eye_centre_xdistance"] = round(
        float(abs(eyes["L"][0] - eyes["R"][0]) / L), 4)
    ball = float(np.ptp(M["Eyeball_L"], axis=0).max())
    r["orbit_d"] = round(ball / L, 4)
    r["interorbital_gap"] = round(r["eye_centre_xdistance"] - r["orbit_d"], 4)
    for s in ("L", "R"):
        E = M[f"Ear_{s}"]
        b = ear_base(E, tis)
        tip = E[np.argmax(np.linalg.norm(E - b, axis=1))]
        r[f"ear_{s}_base"] = [round(float(v / L), 4) for v in b]
        r[f"ear_{s}_base_absx"] = round(float(abs(b[0]) / L), 4)
        r[f"ear_{s}_tip"] = [round(float(v / L), 4) for v in tip]
        r[f"ear_{s}_base_tip_len"] = round(
            float(np.linalg.norm(tip - b) / L), 4)
    tg = M["Tongue"]
    jaw = M["Jaw"]
    r["tongue_y_extent"] = round(float(np.ptp(tg[:, 1]) / L), 4)
    r["tongue_max_forward_vs_jaw_front"] = round(
        float((tg[:, 1].max() - jaw[:, 1].max()) / L), 4)
    r["tissue_max_width"] = round(float(np.ptp(tis[:, 0]) / L), 4)
    return r


out = {}
for spec in A.files:
    label, path = spec.split("=", 1)
    out[label] = measure(path)
    print(label, json.dumps(out[label]))
if A.out:
    Path(A.out).write_text(json.dumps(out, indent=1))
    print("wrote", A.out)
