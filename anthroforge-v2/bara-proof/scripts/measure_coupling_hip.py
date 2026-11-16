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
import numpy as np
from pathlib import Path

HERE = Path(__file__).resolve().parent
BP = HERE.parent
_src = (HERE / "build_coupling_validation.py").read_text()
_cut = _src.index('print("\\n== GACHIDEBU ==")')
exec(compile(_src[:_cut], "build_coupling_validation.py", "exec"),
     globals())

R = {}


def load_target(tag):
    d = np.zeros((len(mh_pos), 3))
    for line in (BP / f"body.coupling.{tag}.target").read_text().splitlines():
        if not line or line.startswith("#"):
            continue
        p = line.split()
        if len(p) == 4:
            s = [float(p[1]), float(p[2]), float(p[3])]
            d[int(p[0])] = [s[0] * 0.1, s[2] * 0.1, s[1] * 0.1]
    return d


def hip_station(P):
    z = mh_crotch + 0.05
    loops = plane_loops(P, np.array([0.0, 0.0, 1.0]),
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


POS = {"base": mh_pos_mac,
       "strongman": mh_pos_mac + M_F + W_F + T_F,
       "gachidebu": mh_pos_mac + load_target("gachidebu"),
       "pear": mh_pos_mac + load_target("pear"),
       "bigchest": mh_pos_mac + load_target("bigchest")}
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
R["gachidebu_tissue_scaled_only_girths"] = girths(POS_TSO)
R["gachidebu_tissue_scaled_only_hip"] = hip_station(POS_TSO)
print("tissue-scaled-only girths:",
      {k: round(v * 100, 1)
       for k, v in R["gachidebu_tissue_scaled_only_girths"].items()})

for tag in ("pear_control", "bigchest_control"):
    G = grade(POS[tag], mh_lab)
    R[tag + "_grade"] = {"thigh_g_cm": float(G["thigh_g"]) * 100,
                         "chest_g_cm": float(G["chest_g"]) * 100,
                         "waist_g_cm": float(G["waist_g"]) * 100,
                         "ua_g_cm": float(G["ua_g"]) * 100}
    print(tag, R[tag + "_grade"])

(BP / "work" / "coupling_hip.json").write_text(json.dumps(R, indent=1))
print("wrote work/coupling_hip.json")
print("HIP DONE")
