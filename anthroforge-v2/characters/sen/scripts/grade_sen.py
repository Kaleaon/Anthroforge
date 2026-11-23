#!/usr/bin/env python3
"""SEN — body composition + grading (numpy side).

Composes Sen's body on hm08 from the SHIPPED component targets
(parsed back from the .target files — the ground truth of what ships,
not the pre-repair fields):

    delta_sen = muscle + chest.width + s * tissue.strongman + terminal_v51

s = 1.0 unless the M5 corrective scan moves it (see below). Grades with
the bara machinery verbatim (bara_machinery.py): full BARA_LESSONS
scorecard for context + Sen's own three gates from
presets-titan-batch1.md section 4.2:

    M1  neck width / head width      >= 1.10   (head = bear head, below)
    M5  torso depth index            ~ 1.1, band 1.05-1.20
    M6  trap slope angle             20-26 deg

Head-scale decision (documented in SEN_BUILD.md): bear head length
L = 0.42 m at EXPORT scale (large grizzly head length) -> 0.2414 m at
base scale; bear ZB is measured off the deformed head in the head
build and written to work/head_measure.json; until then M1 is graded
against the bear ZB *predicted* from the spec (ZB/L target 0.60 after
CheekWidth +10) and re-graded in the head script.

M5 corrective rule (pre-registered): scan tissue scale
s in {1.0, .925, .85, .775, .70}; ship the LARGEST s whose M5 lands in
[1.05, 1.20] while M4 stays >= 1.25; if none qualifies, ship s = 1.0
and report the miss. (The gate's named corrective is "belly family
down"; at component level the tissue scale is the available lever —
blunt, and documented as such.)

Output: work/qa_sen_body.json
"""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SEN = HERE.parent
V2 = SEN.parent.parent
APP = V2.parent / "anthroforge-app"
FP = V2 / "first-proof"
TG = SEN / "targets"
sys.path.insert(0, str(V2))
sys.path.insert(0, str(APP))

from body_machinery.axes import torso_params  # noqa: E402
from body_machinery.labels import label_mesh  # noqa: E402
from body_machinery.loops import grade  # noqa: E402
from body_machinery.osd import (  # noqa: E402
    BODY_END,
    align_macro_base,
    load_mpfb_base_obj,
)
from body_machinery.repair import flipped  # noqa: E402
from core.geometry import parse_target  # noqa: E402

MPFB_ZIP = Path.home() / "workspace/stick-figure-avatar/photoreal/tools/mpfb2.zip"

# ------------------------------------------------------------------ loads
corr = np.load(FP / "work/correspondence.npz")
mh_crotch, mh_neck = [float(x) for x in corr["mh_landmarks"]]
navel_mh = int(corr["navel_mh"])
mh_tris = corr["mh_tris"].astype(np.int64)
L_mh = mh_neck - mh_crotch

mh_pos = load_mpfb_base_obj(MPFB_ZIP)
_mac = np.load(FP / "work/mh_macro_base.npz")["pos_canonical_m"]
mh_pos_mac = align_macro_base(mh_pos, _mac, BODY_END)
NB = len(mh_pos)
FACES_B = mh_tris[np.all(mh_tris < BODY_END, axis=1)]

h_mh = torso_params(mh_pos, mh_crotch, mh_neck, "mh")[0]

_mh_body_mask = np.zeros(NB, bool)
_mh_body_mask[:BODY_END] = True
mh_lab = label_mesh(mh_pos_mac, mh_crotch, mh_neck, _mh_body_mask)

D_muscle = parse_target(TG / "body.muscle.target", NB)
D_width = parse_target(TG / "body.chest.width.target", NB)
D_tissue = parse_target(TG / "body.tissue.strongman.target", NB)
D_term = parse_target(TG / "body.belly.protrusion_terminal_v51.target", NB)

# cross-check parsed targets vs the stored fields (sanity, report only)
_bf = np.load(V2 / "bara-proof/work/bara_fields.npz")
for name, D, key in (("muscle", D_muscle, "muscle_core_canonical_m"),
                     ("width", D_width, "chest_width_canonical_m"),
                     ("tissue", D_tissue, "tissue_canonical_m")):
    raw = _bf[key]
    att_key = {"muscle": "att_muscle", "width": "att_width",
               "tissue": "att_tissue"}[name]
    shipped = raw * _bf[att_key][:, None]
    print(f"target parse check {name}: max |parsed - field*att| = "
          f"{np.abs(D - shipped).max()*1000:.2f} mm "
          f"(write threshold 0.1 mm + slope-limit drift expected)")

D_muscle_sys = D_muscle + D_width + D_term


def flips_for(D):
    out = {}
    for nm, base in (("raw", mh_pos), ("macro", mh_pos_mac)):
        out[nm] = int(flipped(base, D, FACES_B).sum())
    return out


def grade_at(D):
    return grade(
        mh_pos_mac + D,
        mh_lab,
        faces_b=FACES_B,
        mh_crotch=mh_crotch,
        mh_neck=mh_neck,
        mh_pos_mac=mh_pos_mac,
        navel_mh=navel_mh,
        h_mh=h_mh,
        body_end=BODY_END,
    )


# ------------------------------------------------------------------ scan
print("\n== tissue-scale scan (M5 corrective) ==")
scan = []
for s in (1.0, 0.925, 0.85, 0.775, 0.70):
    D = D_muscle_sys + s * D_tissue
    G = grade_at(D)
    scan.append({"s": s, "M5": G["M5_depth_ratio"],
                 "M4": G["M4_chest_waist"], "M6": G["M6_trap_deg"],
                 "neck_w": G["neck_w"], "head_w_hm08": G["head_w"],
                 "M1_hm08head": G["M1_neckW_headW"],
                 "chest_g": G["chest_g"], "waist_g": G["waist_g"],
                 "chest_d": G["chest_d"], "waist_d": G["waist_d"]})
    print(f" s={s:.3f}: M5 {G['M5_depth_ratio']:.3f}  M4 "
          f"{G['M4_chest_waist']:.3f}  M6 {G['M6_trap_deg']:.1f}  "
          f"neck_w {G['neck_w']*100:.1f} cm")

ship_s, rule = 1.0, "s=1.0 already in band"
if not (1.05 <= scan[0]["M5"] <= 1.20):
    rule = "no s in scan puts M5 in band with M4 >= 1.25; shipping 1.0"
    for row in scan:
        if 1.05 <= row["M5"] <= 1.20 and row["M4"] >= 1.25:
            ship_s = row["s"]
            rule = (f"largest s with M5 in [1.05,1.20] and M4>=1.25: "
                    f"s={ship_s}")
            break
print("corrective:", rule)

D_sen = D_muscle_sys + ship_s * D_tissue
G_base = grade_at(np.zeros_like(D_sen))
G_musc = grade_at(D_muscle_sys)
G_sen = grade_at(D_sen)
fl = flips_for(D_sen)
fl_m = flips_for(D_muscle_sys)
print(f"\nflips composed: {fl}  muscle-system: {fl_m}")
print(f"Sen: M5 {G_sen['M5_depth_ratio']:.3f}  M4 "
      f"{G_sen['M4_chest_waist']:.3f}  M6 {G_sen['M6_trap_deg']:.1f} deg  "
      f"neck_w {G_sen['neck_w']*100:.1f} cm  volume "
      f"{G_sen['volume_L']:.1f} L (base {G_base['volume_L']:.1f})")

# M1 against the bear head: predicted ZB from the spec target
HEAD_L_BASE = 0.42 / 1.74        # 0.42 m at export / export scale 1.74
BEAR_ZB_RATIO = 0.60             # spec ZB/L after CheekWidth +10
bear_zb = HEAD_L_BASE * BEAR_ZB_RATIO
m1_bear = G_sen["neck_w"] / bear_zb
print(f"M1 (bear head, predicted ZB {bear_zb*100:.1f} cm): {m1_bear:.3f}")

qa = {
    "composition": {
        "formula": "muscle + chest.width + s*tissue.strongman + "
                   "terminal_v51 (all parsed from shipped .target files)",
        "tissue_scale_shipped": ship_s,
        "corrective_rule": rule,
        "scan": scan,
    },
    "head_scale": {"L_base_m": HEAD_L_BASE, "L_export_m": 0.42,
                   "export_scale": 1.74,
                   "bear_ZB_ratio_spec": BEAR_ZB_RATIO,
                   "bear_ZB_pred_m": bear_zb},
    "gates_sen_4_2": {
        "M1_neckW_headW_bear_predicted": m1_bear,
        "M1_gate": ">= 1.10",
        "M5_depth_ratio": G_sen["M5_depth_ratio"],
        "M5_gate": "1.05-1.20 (centre 1.1)",
        "M6_trap_deg": G_sen["M6_trap_deg"],
        "M6_gate": "20-26",
    },
    "scorecard_context": {
        "base": {k: G_base[k] for k in
                 ("neck_w", "head_w", "chest_g", "waist_g", "volume_L",
                  "height_m")},
        "muscle_system": {k: G_musc[k] for k in
                          ("M1_neckW_headW", "M4_chest_waist",
                           "M5_depth_ratio", "M6_trap_deg", "neck_w",
                           "chest_g", "waist_g", "volume_L")},
        "sen": {k: G_sen[k] for k in
                ("M1_neckW_headW", "M2_neck_arm", "M2_neck_calf",
                 "M3_fa_arm", "M4_chest_waist", "M5_depth_ratio",
                 "M6_trap_deg", "M7_vis_neck_ratio", "M8_span_headW",
                 "M11_thigh_waist", "M12_heads_tall", "neck_w", "neck_g",
                 "head_w", "head_h", "chest_g", "chest_w", "waist_g",
                 "waist_w", "chest_d", "waist_d", "delt_span", "ua_g",
                 "fa_g", "thigh_g", "calf_g", "volume_L", "height_m",
                 "visible_neck")},
    },
    "flips": {"sen_composed": fl, "muscle_system": fl_m,
              "body_faces": int(len(FACES_B))},
}
(SEN / "work/qa_sen_body.json").write_text(json.dumps(qa, indent=1))
np.savez(SEN / "work/sen_body_delta.npz",
         delta_sen_canonical_m=D_sen, tissue_scale=ship_s,
         delta_muscle_sys_canonical_m=D_muscle_sys)
print("\nwrote work/qa_sen_body.json + work/sen_body_delta.npz")
