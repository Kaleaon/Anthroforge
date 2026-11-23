#!/usr/bin/env python3
"""
Hip-station addendum for COUPLING_VALIDATION.md.

girth_simple's ellipse fit degenerated on pelvis sections in the
build script (hip = NaN). Here the hip is measured at ONE fixed
station (z = crotch + 0.05, the grade() hip-width station) on the
widest section loop: width, depth, ellipse girth (same ellipse
convention as girths()) and raw loop perimeter. Also: girths() for
the tissue-scaled-only gachidebu variant (M4 attribution) and
grade() thigh girths for the two distribution controls.

Execs the build script's setup prefix for identical frames/fields.
Writes work/coupling_hip.json.
"""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
BP = HERE.parent
V2 = BP.parent
APP = V2.parent / "anthroforge-app"
for _p in (str(HERE), str(V2), str(APP)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from body_machinery.loops import girths, grade, plane_loops  # noqa: E402
from build_coupling_validation import load_coupling_validation_context  # noqa: E402
from core.geometry import parse_target  # noqa: E402

_ctx = load_coupling_validation_context()
mh_pos = _ctx["mh_pos"]
mh_pos_mac = _ctx["mh_pos_mac"]
mh_crotch = _ctx["mh_crotch"]
mh_neck = _ctx["mh_neck"]
h_star = _ctx["h_star"]
FACES_B = _ctx["FACES_B"]
M_F, W_F, T_F = _ctx["M_F"], _ctx["W_F"], _ctx["T_F"]
EV = _ctx["EV"]
d5 = _ctx["d5"]
T_SCALE = _ctx["T_SCALE"]
NECK_EMB = _ctx["NECK_EMB"]
mh_lab = _ctx["mh_lab"]
grade_kw = _ctx["grade_kw"]

R = {}


def hip_station(P):
    z = mh_crotch + 0.05
    loops = plane_loops(P, FACES_B, np.array([0.0, 0.0, 1.0]),
                        np.array([0.0, 0.0, z]))
    if not loops:
        return None
    L = max(loops, key=lambda Q: Q[:, 0].max() - Q[:, 0].min())
    w = float(L[:, 0].max() - L[:, 0].min())
    dep = float(L[:, 1].max() - L[:, 1].min())
    a, b = w / 2, dep / 2
    ellipse = float(2 * np.pi * np.sqrt((a * a + b * b) / 2))
    dd = np.diff(np.vstack([L, L[:1]]), axis=0)
    perim = float(np.hypot(dd[:, 0], dd[:, 1]).sum())
    return {"width_m": w, "depth_m": dep, "ellipse_girth_m": ellipse,
            "perimeter_m": perim, "loop_points": int(len(L))}


POS = {
    "base": mh_pos_mac,
    "strongman": mh_pos_mac + M_F + W_F + T_F,
    "gachidebu": mh_pos_mac + parse_target(BP / "body.coupling.gachidebu.target", len(mh_pos)),
    "pear": mh_pos_mac + parse_target(BP / "body.coupling.pear.target", len(mh_pos)),
    "bigchest": mh_pos_mac + parse_target(BP / "body.coupling.bigchest.target", len(mh_pos)),
}
for tag in ("pear", "bigchest"):
    w = EV[tag].derived["tissue.level"]
    POS[tag + "_control"] = mh_pos_mac + (M_F + W_F) + d5(w)

R["hip_station"] = {}
for nm, P in POS.items():
    R["hip_station"][nm] = hip_station(P)
    h = R["hip_station"][nm]
    print(f"hip {nm}: width {h['width_m']*100:.1f} depth "
          f"{h['depth_m']*100:.1f} ellipse {h['ellipse_girth_m']*100:.1f} "
          f"perim {h['perimeter_m']*100:.1f} cm")

POS_TSO = mh_pos_mac + M_F + W_F + T_SCALE * T_F + NECK_EMB
R["gachidebu_tissue_scaled_only_girths"] = girths(
    POS_TSO, mh_crotch, mh_neck, h_star, include_hip=True
)
R["gachidebu_tissue_scaled_only_hip"] = hip_station(POS_TSO)
print("tissue-scaled-only girths:",
      {k: round(v * 100, 1)
       for k, v in R["gachidebu_tissue_scaled_only_girths"].items()})

for tag in ("pear_control", "bigchest_control"):
    G = grade(POS[tag], mh_lab, **grade_kw)
    R[tag + "_grade"] = {"thigh_g_cm": float(G["thigh_g"]) * 100,
                         "chest_g_cm": float(G["chest_g"]) * 100,
                         "waist_g_cm": float(G["waist_g"]) * 100,
                         "ua_g_cm": float(G["ua_g"]) * 100}
    print(tag, R[tag + "_grade"])

(BP / "work" / "coupling_hip.json").write_text(json.dumps(R, indent=1))
print("wrote work/coupling_hip.json")
print("HIP DONE")
