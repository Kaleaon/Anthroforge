#!/usr/bin/env python3
"""Segment-2 midpoint solve for the hyper proof (HYPER_RANGES.md s.5).

Finding from verify_proof_contact.py: correctives do NOT interpolate.
The policy state at slider 1.5 (belly midpoint + contact interpolated
between its 1.0 and 2.0 solves) measured 5 folds / 23 crossings. So
the segment ships a SOLVED MIDPOINT KEY: the 1.5 policy state is
capped + repaired directly, its contact corrective becomes a key, and
the evaluator piecewise-interpolates correctives between solved keys
{1.0: v52, 1.5: hyper15, 2.0: hyper2}. Quarter points (1.25 / 1.75)
are then gated as the honest test of that interpolation.
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from hyper_common import (FP, HYPER, crossings, fold_stats, load_base,
                          load_macro, load_target, min_thigh_gap,
                          quantise, dequantise, write_target)
from build_hyper_proof import contact_cap, fold_repair_q  # noqa: E402

V, F, Fb = load_base()
Vm = load_macro(V)

D1 = load_target(FP / "body.belly.protrusion_v5.1.target")
CT = load_target(FP / "body.belly.protrusion_contact_v52.target")
SEG = load_target(HYPER / "body.belly.protrusion.hyper2.target")
FULL = load_target(HYPER / "body.belly.hyper2_full.target")
CH2 = load_target(HYPER / "body.belly.protrusion_contact_hyper2.target")

out = {}
belly15 = D1 + 0.5 * SEG
P15 = belly15 + CT
print("midpoint before solve:", fold_stats(V, Fb, P15),
      fold_stats(Vm, Fb, P15), "crossings", crossings(V, P15))

q = quantise(P15)
for attempt in range(1, 9):
    cur = dequantise(q)
    cur, nc = contact_cap(cur, 0.004, margin_extra=0.001 * attempt)
    q = quantise(cur)
    q, rounds, ok = fold_repair_q(q)
    cur = dequantise(q)
    cr = crossings(V, cur)
    fr, fm = fold_stats(V, Fb, cur), fold_stats(Vm, Fb, cur)
    print(f"  attempt {attempt}: capped {nc}, rounds {rounds}, "
          f"folds {fr}/{fm}, crossings {cr}")
    if ok and cr == 0 and fr[0] == 0 and fm[0] == 0:
        break
P15s = cur
CH15 = P15s - belly15          # total segment-2 contact at the midpoint
n = write_target(
    HYPER / "body.belly.protrusion_contact_hyper15.target", CH15,
    "Provenance: segment-2 contact corrective KEY at slider 1.5 for "
    "body.belly.protrusion (HYPER_RANGES.md s.5). Correctives do not "
    "interpolate (the naive 1.5 blend measured 5 folds / 23 "
    "crossings), so the midpoint state was capped + repaired "
    "directly; the evaluator interpolates between solved keys "
    "{1.0: contact_v52, 1.5: this, 2.0: contact_hyper2}. This file is "
    "the TOTAL segment-2 contact field at 1.5 (replaces v52's "
    "contribution there), not an increment over v52.")
print(f"shipped contact_hyper15 ({n} moved verts)")
out["midpoint_1.5"] = {
    "folds_raw": fold_stats(V, Fb, P15s),
    "folds_macro": fold_stats(Vm, Fb, P15s),
    "crossings": crossings(V, P15s),
    "min_thigh_gap_mm": float(min_thigh_gap(V, P15s) * 1000)}

# quarter points: belly linear; contact piecewise-linear between keys
def gate(belly, contact):
    d = belly + contact
    return {"folds_raw": fold_stats(V, Fb, d),
            "folds_macro": fold_stats(Vm, Fb, d),
            "crossings": crossings(V, d),
            "min_thigh_gap_mm": float(min_thigh_gap(V, d) * 1000)}

belly125 = D1 + 0.25 * SEG
belly175 = D1 + 0.75 * SEG
ct125 = CT + 0.5 * (CH15 - CT)
ct175 = CH15 + 0.5 * ((CT + CH2) - CH15)
out["quarter_1.25"] = gate(belly125, ct125)
out["quarter_1.75"] = gate(belly175, ct175)
out["endpoint_2.0"] = gate(FULL, CT + CH2)
out["endpoint_1.0"] = gate(D1, CT)
print(json.dumps(out, indent=1))

# navel tracker, windowed: midline front, navel height band.
# v1 anchor: navel forward displacement at +1 = 119.7 mm.
win = (np.abs(V[:13380, 0]) < 0.03) & (V[:13380, 2] > 0.0) \
    & (V[:13380, 2] < 0.14)
cand = np.where(win, D1[:13380, 1], -9)
nav = int(np.argmax(cand))
out["navel_tracker"] = {
    "vert": nav, "base_pos_m": [round(float(x), 4) for x in V[nav]],
    "at_1x_fwd_mm": float(D1[nav, 1] * 1000),
    "at_1x_down_mm": float(-D1[nav, 2] * 1000),
    "at_2x_fwd_mm": float(FULL[nav, 1] * 1000),
    "at_2x_down_mm": float(-FULL[nav, 2] * 1000)}
print("navel:", out["navel_tracker"])
(HYPER / "work/proof_midpoint.json").write_text(json.dumps(out, indent=1))
print("wrote work/proof_midpoint.json")
