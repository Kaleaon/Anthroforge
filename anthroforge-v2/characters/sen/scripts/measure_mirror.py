#!/usr/bin/env python3
"""L/R mirror quantification for the Sen head rebuild (pure python).

Measures the stations the name-keyed-side bug touched — eyeball
centres (EyeSpacing) and ear bases (EarSpread) — plus tongue extent,
on any head GLB with the house object names, in head-local units
normalised by each file's own tissue length L. GLB parsing imported
from characters/common/verify_head.py (same glTF -> head-frame
conversion, so numbers are directly comparable with the verify
stations and with each other across bases).

    python3 measure_mirror.py LABEL=path.glb [LABEL=path.glb ...] \
        --out work/mirror_measure.json
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
CHARS = HERE.parent.parent
if str(CHARS) not in sys.path:
    sys.path.insert(0, str(CHARS))

from common.verify_head import ear_base_len, glb_meshes  # noqa: E402


def measure(path):
    M = {k: v[0] for k, v in glb_meshes(path).items()}
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
        b, _ = ear_base_len(E, tis)
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


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--out")
    A = ap.parse_args(argv)

    out = {}
    for spec in A.files:
        label, path = spec.split("=", 1)
        out[label] = measure(path)
        print(label, json.dumps(out[label]))
    if A.out:
        Path(A.out).write_text(json.dumps(out, indent=1))
        print("wrote", A.out)
    return out


if __name__ == "__main__":
    main()
