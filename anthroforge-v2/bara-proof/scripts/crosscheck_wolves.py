"""Cross-check: neck:arm relations on library geometry with real necks.

Two library wolves, measured with mesh-plane slice loops (protocol
diagnosed on the actual geometry -- see NECK_FOREARM.md):

bara wolf (single clean biped T-pose body, 69,190 verts): station-
disciplined measurements. Findings: chest tape 1.82 m (z=1.40, clean
torso loop); arm-station girths along the arm axis (z~1.54): 1.01 at
the shoulder blend falling to 0.69-0.74 through the upper arm, 0.61
forearm max, 0.46 distal forearm, paw beyond. The neck has NO
isolable tape loop: from the chest junction to the skull every
horizontal outline is one merged neck/trap/ruff/head mass (smallest
above-shoulder central outline 1.12 m at z=1.85, skull-dominated;
neck-level outline at z=1.70 is 2.15 m). The sculpt itself embodies
R5/R7 -- the neck cylinder does not exist as a separate tape station.

CVRxEarth wolf: NOT measurable under this protocol. The download is a
fragmented two-scale Sketchfab scene (a posed metre-scale figure in
~9 body fragments plus weapons/props, and a second cm-scale group);
no fragment set forms a closed neck station, and the figure is in a
dynamic pose (arms raised, holding sickles). The automatic biped
pass over the metre-scale fragments returns nonsense stations
(neck 0.164 m at 95% height -- a prop edge), recorded below as
rejected. Reported honestly rather than forced.

Writes work/wolf_crosscheck.json. Geometry dumped to /tmp scratch by
a Blender world-space pass (dump_wolves.py, session scratch).
"""
import json
import sys
from pathlib import Path

import numpy as np

V2 = Path(__file__).resolve().parents[2]
if str(V2) not in sys.path:
    sys.path.insert(0, str(V2))

from body_machinery.loops import loop_perim as perim, plane_loops as _plane_loops  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "work"
SCRATCH = Path("/tmp/nf_work")


def plane_loops(pos, F, n, p0):
    return _plane_loops(pos, F, n, p0, round_decimals=4)


def load_parts(tag):
    d = np.load(SCRATCH / f"wolf_{tag}.npz", allow_pickle=True)
    return [(str(d[f"{i}_name"]), d[f"{i}_V"], d[f"{i}_F"])
            for i in range(int(d["nparts"]))]


def central_loop(V, F, z):
    """Largest near-axis loop at height z (the torso/neck/head
    outline), or None."""
    loops = [lp for lp in plane_loops(V, F, np.array([0.0, 0.0, 1.0]),
                                      np.array([0.0, 0.0, z]))
             if abs(lp.mean(axis=0)[0]) < 0.15 and perim(lp) > 0.2]
    return max(loops, key=perim) if loops else None


def arm_loop(V, F, x):
    """Loop nearest the arm axis (z~1.54, y~0.1) on plane x=const."""
    loops = [lp for lp in plane_loops(V, F, np.array([1.0, 0.0, 0.0]),
                                      np.array([x, 0.0, 0.0]))
             if abs(lp.mean(axis=0)[2] - 1.54) < 0.35
             and abs(lp.mean(axis=0)[1]) < 0.35]
    if not loops:
        return None
    return min(loops, key=lambda lp: abs(lp.mean(axis=0)[2] - 1.54))


out = {}

# ---------------------------------------------------------------- bara
parts = load_parts("bara")
nm, V, F = max(parts, key=lambda p: len(p[1]))
chest = central_loop(V, F, 1.40)
arm_stations = {}
for x in (0.40, 0.50, 0.55, 0.62, 0.70, 0.78):
    lp = arm_loop(V, F, x)
    if lp is not None:
        arm_stations[f"x={x:.2f}"] = float(perim(lp))
neck_outline = {}
for z in (1.65, 1.70, 1.75, 1.85):
    lp = central_loop(V, F, z)
    if lp is not None:
        neck_outline[f"z={z:.2f}"] = float(perim(lp))
ua_clean = arm_stations["x=0.50"]
fa_max = arm_stations["x=0.70"]
out["bara_wolf"] = {
    "model": "BaraWolfBody (Mixamo-rigged bara wolf, T-pose), "
             "height 1.95 m, units m",
    "chest_g_m": float(perim(chest)),
    "arm_station_girths_m": arm_stations,
    "upper_arm_g_clean_m": ua_clean,
    "upper_arm_g_shoulder_blend_m": arm_stations["x=0.40"],
    "forearm_g_max_m": fa_max,
    "fore_over_arm_clean": float(fa_max / ua_clean),
    "neck_tape": "not isolable -- merged neck/trap/ruff/head mass at "
                 "every station above the chest junction",
    "neck_region_outlines_m": neck_outline,
    "neck_region_over_arm_floor": float(
        min(neck_outline.values()) / ua_clean),
    "reading": "the sculpt carries no neck cylinder: the smallest "
               "above-shoulder outline (1.12 m, skull-dominated) is "
               "already 1.5x the clean upper-arm girth, and the "
               "forearm:arm ratio at clean stations is 0.82 -- inside "
               "the study's bara M3 band (0.80-0.88). Real bara "
               "geometry sits at/above the Reeves neck relation, "
               "not below it.",
}
print(json.dumps(out["bara_wolf"], indent=1))

# ---------------------------------------------------------------- cvrx
out["cvrx_wolf"] = {
    "model": "Big Bad Wolf / Death V2 (CVRxEarth), Sketchfab scene",
    "status": "not measurable under the slice-loop protocol",
    "reason": "fragmented two-scale scene: a posed metre-scale figure "
              "in ~9 body fragments (arms raised, holding sickles; "
              "neck segment not present as a closed station) plus a "
              "second cm-scale group and props. An automatic biped "
              "pass over the metre fragments returns a 0.164 m 'neck' "
              "at 95% height (a prop edge) -- rejected as a station "
              "error, not reported as a measurement.",
}
print(json.dumps(out["cvrx_wolf"], indent=1))

OUT.mkdir(exist_ok=True)
(OUT / "wolf_crosscheck.json").write_text(json.dumps(out, indent=1))
print("wrote", OUT / "wolf_crosscheck.json")
