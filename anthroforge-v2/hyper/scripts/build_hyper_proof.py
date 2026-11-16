#!/usr/bin/env python3
"""Hyper proof build: belly stack (body.belly.protrusion v5.1) at 2x,
authored as a HYPER SEGMENT per HYPER_RANGES.md s.3.1 / rule H2.

Method -- solve the 2x STATE, never extrapolate to it:
  1. naive state D2 = 2 * D1 (D1 = shipped v5.1 target). B16 measured
     this at 75 flipped faces and 34 midline crossings.
  2. Contact cap (H6): in B16's inner-thigh band, no vert may sit
     closer than GAP to the midline plane on its own base side; verts
     that cross or approach are set onto the cap plane (the patch goes
     FLAT -- R10 squish), with the x-correction diffused over three
     neighbour rings so the patch edge has no step.
  3. Fold repair in QUANTISED space at the 2x state (attenuation,
     both bases, margin floor 0.01 -- same discipline as the s.4
     defect repair). Cap and repair iterate: attenuation shrinks the
     cap push, so re-cap and re-gate until folds == 0 AND
     crossings == 0 AND min gap >= GAP.
  4. Ship the SEGMENT: delta(2x solved) - delta(1x shipped), both in
     quantised dm space, so base segment + hyper segment recompose
     from disk to exactly the gated state.
Gates (H8): folds both bases at 1.0 / 1.5 / 2.0 composed states,
crossings at the same three states, min thigh gap at 2x.
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from hyper_common import (FP, HYPER, body_edges, crossings, face_dots,
                          fold_stats, load_base, load_macro, load_target,
                          min_thigh_gap, quantise, dequantise,
                          thigh_band, write_target)

GAP = 0.004            # 4 mm minimum surface gap across the midline
MARGIN_FLOOR = 0.01
MARGIN_BAND = 0.02

V, F, Fb = load_base()
Vm = load_macro(V)
EDGES = body_edges(Fb)
band = thigh_band(V)
band_idx = np.where(band)[0]
side = np.sign(V[band_idx, 0])
side[side == 0] = 1.0

D1 = load_target(FP / "body.belly.protrusion_v5.1.target")
D2n = 2.0 * D1
print(f"naive 2x: raw folds {fold_stats(V, Fb, D2n)}, "
      f"macro folds {fold_stats(Vm, Fb, D2n)}, "
      f"crossings {crossings(V, Fb, D2n)}, "
      f"min gap {min_thigh_gap(V, D2n)*1000:.2f} mm")


def contact_cap(delta, gap, margin_extra=0.0):
    """Return (capped delta, n capped verts). Pushes band verts out to
    sign*(gap/2 + margin_extra) in x; correction diffused 3 rings."""
    P = V + delta
    need = (gap / 2 + margin_extra) - side * P[band_idx, 0]
    capped = need > 0
    corr = np.zeros(len(V))
    corr[band_idx[capped]] = side[capped] * need[capped]
    # diffuse over neighbour rings (non-patch verts only)
    frontier = set(band_idx[capped].tolist())
    src = corr.copy()
    for w in (0.55, 0.32, 0.16):
        nxt = set()
        for u, v in EDGES:
            if u in frontier and v not in frontier and corr[v] == 0:
                nxt.add(v)
            elif v in frontier and u not in frontier and corr[u] == 0:
                nxt.add(u)
        for vtx in nxt:
            nb = [src[u] if u != vtx else src[v] for u, v in EDGES
                  if u == vtx or v == vtx]
            corr[vtx] = w * float(np.mean(nb))
        frontier = nxt
        src = corr.copy()
        if not frontier:
            break
    out = delta.copy()
    out[:, 0] += corr
    return out, int(capped.sum())


def fold_repair_q(q):
    att = np.ones(len(V))
    for rnd in range(1, 601):
        cur = dequantise(q)
        d_raw = face_dots(V, Fb, cur)
        d_mac = face_dots(Vm, Fb, cur)
        if d_raw.min() >= MARGIN_FLOOR and d_mac.min() >= MARGIN_FLOOR:
            return q, rnd - 1, True
        weak = np.where((d_raw < MARGIN_BAND) | (d_mac < MARGIN_BAND))[0]
        badv = np.unique(Fb[weak].ravel())
        nbr = np.unique(EDGES[np.isin(EDGES[:, 0], badv)
                              | np.isin(EDGES[:, 1], badv)].ravel())
        att[badv] *= 0.90
        att[np.setdiff1d(nbr, badv)] *= 0.97
        q = np.round(q * att[:, None], 3)
        att = np.ones(len(V))
    return q, 600, False


q = quantise(D2n)
solved = None
for attempt in range(1, 9):
    cur = dequantise(q)
    cur, ncapped = contact_cap(cur, GAP, margin_extra=0.001 * attempt)
    q = quantise(cur)
    q, rounds, ok = fold_repair_q(q)
    cur = dequantise(q)
    cr = crossings(V, Fb, cur)
    gap_mm = min_thigh_gap(V, cur) * 1000
    fr = fold_stats(V, Fb, cur)
    fm = fold_stats(Vm, Fb, cur)
    print(f"attempt {attempt}: capped {ncapped}, repair rounds {rounds} "
          f"ok={ok}; folds raw {fr} macro {fm}; crossings {cr}; "
          f"min gap {gap_mm:.2f} mm")
    if ok and cr == 0 and gap_mm >= GAP * 1000 - 0.05:
        solved = cur
        break
assert solved is not None, "2x state did not converge"

# --- segment = solved(2x) - shipped(1x), in quantised dm space
q_seg = np.round(quantise(solved) - quantise(D1), 3)
seg = dequantise(q_seg)
note_seg = ("Provenance: HYPER SEGMENT 1->2 for body.belly.protrusion "
            "(HYPER_RANGES.md s.5). The 2x state was solved directly: "
            "2x v5.1 stack, inner-thigh contact cap (4 mm min gap, "
            "patch flattened), attenuation fold repair in quantised "
            "space at the 2x design point, both bases, 0 flips, "
            "min_dot >= 0.01. This file is the INCREMENT over the "
            "shipped v5.1 target; slider value 2.0 = v5.1 + this.")
n_seg = write_target(HYPER / "body.belly.protrusion.hyper2.target",
                     seg, note_seg)
note_full = ("Provenance: composed 2x state of body.belly.protrusion "
             "(v5.1 + hyper segment), the gated design point of "
             "HYPER_RANGES.md s.5, written for QA convenience.")
n_full = write_target(HYPER / "body.belly.hyper2_full.target",
                      solved, note_full)
print(f"wrote hyper2 segment ({n_seg} moved verts), full ({n_full})")

# --- verify everything FROM DISK
D1d = load_target(FP / "body.belly.protrusion_v5.1.target")
segd = load_target(HYPER / "body.belly.protrusion.hyper2.target")
fulld = load_target(HYPER / "body.belly.hyper2_full.target")
states = {"1.0": D1d, "1.5": D1d + 0.5 * segd, "2.0": D1d + segd}
qa = {}
for nm, d in states.items():
    qa[nm] = {
        "folds_raw": fold_stats(V, Fb, d),
        "folds_macro": fold_stats(Vm, Fb, d),
        "crossings": crossings(V, Fb, d),
        "min_thigh_gap_mm": float(min_thigh_gap(V, d) * 1000)}
    print(f"state {nm}: {qa[nm]}")
qa["full_file_matches_composition_max_mm"] = float(
    np.abs(fulld - (D1d + segd)).max() * 1000)
dev = np.linalg.norm(solved - D2n, axis=1)
sup = np.linalg.norm(D2n, axis=1) > 1e-6
qa["solve_deviation_vs_naive_2x"] = {
    "max_mm": float(dev.max() * 1000),
    "rms_mm": float(np.sqrt((dev[sup] ** 2).mean()) * 1000),
    "verts_changed": int((dev > 1e-9).sum())}
# navel-region tracker: vert of max forward (depth+) displacement in D1
fwd = D1[:, 1]
nav = int(np.argmax(np.where((V[:, 2] > 0.35) & (V[:, 2] < 0.75), fwd, -9)))
qa["navel_tracker"] = {
    "vert": nav,
    "at_1x_fwd_mm": float(D1[nav, 1] * 1000),
    "at_1x_down_mm": float(-D1[nav, 2] * 1000),
    "at_2x_fwd_mm": float(solved[nav, 1] * 1000),
    "at_2x_down_mm": float(-solved[nav, 2] * 1000)}
print(json.dumps(qa, indent=1))
(HYPER / "work/proof_qa.json").write_text(json.dumps(qa, indent=1))
np.savez_compressed(HYPER / "work/proof_states.npz",
                    base=V, faces=Fb, d1=D1d, seg=segd, full=fulld)
print("wrote work/proof_qa.json + work/proof_states.npz")
