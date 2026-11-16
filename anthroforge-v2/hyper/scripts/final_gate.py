#!/usr/bin/env python3
"""Final gate for the hyper proof, composed ONLY from shipped files
under the evaluator semantics of HYPER_RANGES.md s.6:

  belly(s)   = D1 + clamp(s-1, 0, 1) * SEG            (piecewise morph)
  contact(s) = total-field keys, piecewise-linear:
               s<=1: CT * s   |   1.0: CT   1.5: CH15   2.0: CH2
               (CH15 / CH2 are TOTAL segment-2 contact fields at
               their key values -- they replace, not add to, v52)
  state(s)   = belly(s) + contact(s)

Gates at s = 1.0 / 1.25 / 1.5 / 1.75 / 2.0, both bases: folds,
midline crossings (B16 band), min thigh gap. Navel = vert 4075
(first-proof canonical anchor vert).
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from hyper_common import (FP, HYPER, crossings, fold_stats, load_base,
                          load_macro, load_target, min_thigh_gap)

V, F, Fb = load_base()
Vm = load_macro(V)
D1 = load_target(FP / "body.belly.protrusion_v5.1.target")
CT = load_target(FP / "body.belly.protrusion_contact_v52.target")
SEG = load_target(HYPER / "body.belly.protrusion.hyper2.target")
CH15 = load_target(HYPER / "body.belly.protrusion_contact_hyper15.target")
CH2 = load_target(HYPER / "body.belly.protrusion_contact_hyper2.target")


def contact(s):
    if s <= 1.0:
        return CT * s
    if s <= 1.5:
        return CT + (CH15 - CT) * (s - 1.0) / 0.5
    return CH15 + (CH2 - CH15) * (s - 1.5) / 0.5


def state(s):
    return D1 + max(0.0, min(1.0, s - 1.0)) * SEG + contact(s) \
        if s > 1.0 else (D1 * s + CT * s) * 0 + (D1 + CT) * s


out = {}
for s in (1.0, 1.25, 1.5, 1.75, 2.0):
    d = state(s)
    out[str(s)] = {
        "folds_raw": fold_stats(V, Fb, d),
        "folds_macro": fold_stats(Vm, Fb, d),
        "crossings": crossings(V, Fb, d),
        "min_thigh_gap_mm": float(min_thigh_gap(V, d) * 1000)}
    print(s, out[str(s)])

nav = 4075
d2 = state(2.0)
out["navel_vert_4075"] = {
    "at_1x_fwd_mm": float(D1[nav, 1] * 1000 + 0 * CT[nav, 1] * 1000),
    "belly_only_1x_fwd_mm": float(D1[nav, 1] * 1000),
    "belly_only_1x_down_mm": float(-D1[nav, 2] * 1000),
    "at_2x_total_fwd_mm": float(d2[nav, 1] * 1000),
    "at_2x_total_down_mm": float(-d2[nav, 2] * 1000)}
print("navel 4075:", out["navel_vert_4075"])
(HYPER / "work/final_gate.json").write_text(json.dumps(out, indent=1))
print("wrote work/final_gate.json")
