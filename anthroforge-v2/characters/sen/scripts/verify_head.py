#!/usr/bin/env python3
"""SEN head — identical-ruler before/after verification from the GLBs
(pure python; system python has no Blender). Patches head_measure.json
with the corrected M1 (head ZB converted to body metres first)."""
import json
import struct
from pathlib import Path

import numpy as np

SEN = Path(__file__).resolve().parent.parent
V2 = SEN.parent.parent


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
        mesh = g["meshes"][node["mesh"]]
        prim = mesh["primitives"][0]
        acc = g["accessors"][prim["attributes"]["POSITION"]]
        bv = g["bufferViews"][acc["bufferView"]]
        arr = np.frombuffer(buf, dtype="<f4",
                            count=acc["count"] * 3,
                            offset=bv.get("byteOffset", 0)
                            + acc.get("byteOffset", 0))
        P = arr.reshape(-1, 3).astype(np.float64)
        # glTF (x, y-up, z) -> head frame (x, y-forward, z-up):
        P = np.stack([P[:, 0], -P[:, 2], P[:, 1]], axis=1)
        t = node.get("translation")
        if t:
            P = P + np.array([t[0], -t[2], t[1]])
        out[node["name"]] = P
    return out


def rulers(M):
    tis = M["TissueHead"]
    eye_y, eye_z, pal_z = 0.082, -0.008, -0.180
    nose_y = tis[:, 1].max()
    zb_band = tis[(tis[:, 2] > eye_z - 0.06) & (tis[:, 2] < eye_z + 0.10)]
    can_y = eye_y + 0.55 * (nose_y - eye_y)
    muz = tis[(tis[:, 1] > can_y - 0.03) & (tis[:, 1] < can_y + 0.03)
              & (tis[:, 2] < pal_z + 0.10)]
    earlens = []
    for s in ("L", "R"):
        E = M[f"Ear_{s}"]
        d = np.sqrt(((E[:, None, :] - tis[None, :, :]) ** 2).sum(-1)).min(1)
        base = E[d < np.percentile(d, 25)].mean(axis=0)
        earlens.append(np.linalg.norm(E - base, axis=1).max())
    return {
        "tissue_max_width": float(np.ptp(tis[:, 0])),
        "ZB_band_width": float(np.ptp(zb_band[:, 0])),
        "muzzle_band_width": float(np.ptp(muz[:, 0])),
        "jaw_width": float(np.ptp(M["Jaw"][:, 0])),
        "jaw_length": float(np.ptp(M["Jaw"][:, 1])),
        "ear_base_tip_len": float(np.mean(earlens)),
        "orbit_d": float(np.ptp(M["Eyeball_L"][:, 0])),
        "tongue_y_extent": float(np.ptp(M["Tongue"][:, 1])),
        "nose_width": float(np.ptp(M["NoseLeather"][:, 0])),
    }


before = rulers(glb_meshes(V2 / "base-head-v3/neutral_base_head_v3.glb"))
after = rulers(glb_meshes(SEN / "sen_head.glb"))
rep = {"before": before, "after": after,
       "pct_change": {k: round(100.0 * (after[k] / before[k] - 1.0), 1)
                      for k in before}}
# corrected M1: bear head width in BODY metres
scale = 0.42 / 1.74
bear_w = after["tissue_max_width"] * scale
bear_zb = after["ZB_band_width"] * scale
rep["M1_corrected"] = {
    "neck_w_body_m": 0.112,
    "bear_tissue_width_m": bear_w, "bear_ZB_band_m": bear_zb,
    "M1_vs_tissue_width": 0.112 / bear_w,
    "M1_vs_ZB_band": 0.112 / bear_zb,
    "gate": ">= 1.10"}
hm_path = SEN / "work/head_measure.json"
hm = json.loads(hm_path.read_text())
hm["rulers_before_after"] = rep
hm["measured"]["M1_final_neckW_over_bearZB"] = rep["M1_corrected"][
    "M1_vs_tissue_width"]
hm_path.write_text(json.dumps(hm, indent=1))
print(json.dumps(rep, indent=1))
