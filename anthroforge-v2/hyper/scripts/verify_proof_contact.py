#!/usr/bin/env python3
"""Contact-policy verification for the hyper proof (HYPER_RANGES.md s.5).

Reconciliation first: B16's crossing counts (0/19/34/58/69) were
measured on the belly stack + contact corrective, scaled together.
The v5.2 corrective is an envelope-limited field (H5): extrapolated,
IT is the penetration source. Under the schema in HYPER_RANGES.md s.6
the evaluator clamps it at its envelope edge (1.0) inside segment 2,
where a re-solved cap (contact_hyper2) supersedes it. This script:
  1. reproduces B16's crossings on stack+contact (sanity),
  2. gates the POLICY composition at 2x: solved belly 2x + contact@1.0,
  3. if that state is dirty, caps + repairs it and ships the
     difference as body.belly.protrusion_contact_hyper2.target,
  4. fixes the navel tracker (argmax forward displacement in D1).
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from hyper_common import (FP, HYPER, body_edges, crossings, fold_stats, load_base, load_macro, load_target,
                          min_thigh_gap, quantise, dequantise,
                          write_target)
from build_hyper_proof import contact_cap, fold_repair_q  # noqa: E402

V, F, Fb = load_base()
Vm = load_macro(V)
EDGES = body_edges(Fb)

D1 = load_target(FP / "body.belly.protrusion_v5.1.target")
CT = load_target(FP / "body.belly.protrusion_contact_v52.target")
FULL = load_target(HYPER / "body.belly.hyper2_full.target")
SEG = load_target(HYPER / "body.belly.protrusion.hyper2.target")

out = {}
print("== B16 reproduction: stack+contact scaled ==")
rep = {}
for s in (1.0, 1.5, 2.0, 3.0, 4.0):
    rep[str(s)] = crossings(V, (D1 + CT) * s)
print(rep)
out["b16_reproduction_stack_plus_contact_crossings"] = rep

print("== policy composition at 2x: solved belly + contact@1.0 ==")
P2 = FULL + CT
st = {"folds_raw": fold_stats(V, Fb, P2), "folds_macro":
      fold_stats(Vm, Fb, P2), "crossings": crossings(V, P2),
      "min_thigh_gap_mm": float(min_thigh_gap(V, P2) * 1000)}
print(st)
out["policy_2x_before_resolve"] = st

contact_hyper2 = np.zeros_like(P2)
if st["folds_raw"][0] or st["folds_macro"][0] or st["crossings"]:
    q = quantise(P2)
    for attempt in range(1, 9):
        cur = dequantise(q)
        cur, nc = contact_cap(cur, 0.004, margin_extra=0.001 * attempt)
        q = quantise(cur)
        q, rounds, ok = fold_repair_q(q)
        cur = dequantise(q)
        cr = crossings(V, cur)
        fr, fm = fold_stats(V, Fb, cur), fold_stats(Vm, Fb, cur)
        print(f"  resolve attempt {attempt}: capped {nc}, rounds "
              f"{rounds}, folds {fr}/{fm}, crossings {cr}")
        if ok and cr == 0 and fr[0] == 0 and fm[0] == 0:
            break
    contact_hyper2 = cur - FULL
    n = write_target(
        HYPER / "body.belly.protrusion_contact_hyper2.target",
        contact_hyper2,
        "Provenance: segment-2 contact corrective for "
        "body.belly.protrusion (HYPER_RANGES.md s.5). Re-solved at the "
        "2x policy composition (solved hyper belly + v5.2 contact "
        "clamped at its envelope edge 1.0): cap 4 mm + quantised fold "
        "repair. Supersedes contact_v52 inside segment 2 (H5).")
    print(f"  shipped contact_hyper2 ({n} moved verts)")
    P2 = cur
    out["policy_2x_after_resolve"] = {
        "folds_raw": fold_stats(V, Fb, P2),
        "folds_macro": fold_stats(Vm, Fb, P2),
        "crossings": crossings(V, P2),
        "min_thigh_gap_mm": float(min_thigh_gap(V, P2) * 1000)}
else:
    out["policy_2x_after_resolve"] = st
    print("  policy state already clean; cap non-binding")

# segment-2 mid state under policy: 1x stack+contact, then halfway
P15 = (D1 + CT) + 0.5 * SEG + (contact_hyper2 * 0.5
                               if contact_hyper2.any() else 0.0)
out["policy_1.5"] = {"folds_raw": fold_stats(V, Fb, P15),
                     "folds_macro": fold_stats(Vm, Fb, P15),
                     "crossings": crossings(V, P15)}
print("policy 1.5:", out["policy_1.5"])

nav = int(np.argmax(D1[:13380, 1]))
out["navel_tracker"] = {
    "vert": nav,
    "at_1x_fwd_mm": float(D1[nav, 1] * 1000),
    "at_1x_down_mm": float(-D1[nav, 2] * 1000),
    "at_2x_fwd_mm": float(FULL[nav, 1] * 1000),
    "at_2x_down_mm": float(-FULL[nav, 2] * 1000)}
print("navel:", out["navel_tracker"])
(HYPER / "work/proof_contact.json").write_text(json.dumps(out, indent=1))
print("wrote work/proof_contact.json")
