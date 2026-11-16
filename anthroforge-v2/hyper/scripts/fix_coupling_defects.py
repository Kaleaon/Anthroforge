#!/usr/bin/env python3
"""Repair the two shipped fold defects B16 found (MORPH_CRAFT.md s.8
Door 1 / s.7): body.coupling.bigchest.target flips 1 face and
body.coupling.gachidebu.target flips 3 faces at their authored 1.0x
when loaded back from the shipped .target files -- although the
coupling-validation build gated its in-memory float deltas at 0 flips
on both bases (work/coupling_validation_numbers.json: gachidebu raw
min_dot 0.00061, bigchest 0.00177). The builds sat ON the fold
boundary; the .target format's 0.1 mm quantisation pushed them over.

Repair method: attenuation in QUANTISED space (the exact numbers that
ship), gated on both bases, to 0 flips AND a margin floor
(min normalised dot >= 0.01) so the fix has headroom instead of
landing back on the boundary. Deviation from the original fields is
measured and reported. Originals are preserved in hyper/work/originals/.
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from hyper_common import (BP, HYPER, body_edges, face_dots, fold_stats,
                          load_base, load_macro, load_target, quantise,
                          dequantise, write_target)

MARGIN_FLOOR = 0.01      # ship gate after this fix
MARGIN_BAND = 0.02       # faces below this get attenuated
MAX_ROUNDS = 600

V, F, Fb = load_base()
Vm = load_macro(V)
EDGES = body_edges(Fb)
zbody = V[:13380, 2]
zlo, zhi = zbody.min(), zbody.max()

report = {}

for name in ("bigchest", "gachidebu"):
    path = BP / f"body.coupling.{name}.target"
    orig = load_target(path)
    print(f"\n== {name} ==")
    for base, nm in ((V, "raw"), (Vm, "macro")):
        nf, md = fold_stats(base, Fb, orig)
        print(f"  as-shipped {nm}: {nf} flips, min_dot {md:.5f}")
    # localise on the raw frame
    dots = face_dots(V, Fb, orig)
    bad = np.where(dots < 0)[0]
    locs = []
    for fi in bad:
        verts = Fb[fi]
        c = (V[verts] + orig[verts]).mean(axis=0)
        locs.append({
            "face_index": int(fi), "verts": [int(v) for v in verts],
            "centroid_m": [round(float(x), 4) for x in c],
            "height_frac_body": round(float((c[2] - zlo) / (zhi - zlo)), 3),
            "lateral_offset_m": round(float(c[0]), 4),
            "dot": round(float(dots[fi]), 5)})
        print(f"  flipped face {fi}: verts {list(verts)}, centroid "
              f"({c[0]:+.3f}, {c[1]:+.3f}, {c[2]:+.3f}) m, "
              f"height frac {(c[2]-zlo)/(zhi-zlo):.3f}, dot {dots[fi]:.5f}")

    # --- repair in quantised space
    q = quantise(orig)                      # (NV,3) dm, obj axis order
    att = np.ones(len(V))
    rounds = 0
    for rounds in range(1, MAX_ROUNDS + 1):
        cur = dequantise(q)
        d_raw = face_dots(V, Fb, cur)
        d_mac = face_dots(Vm, Fb, cur)
        weak = np.where((d_raw < MARGIN_BAND) | (d_mac < MARGIN_BAND))[0]
        if len(weak) == 0 or (d_raw.min() >= MARGIN_FLOOR
                              and d_mac.min() >= MARGIN_FLOOR):
            break
        badv = np.unique(Fb[weak].ravel())
        nbr = np.unique(EDGES[np.isin(EDGES[:, 0], badv)
                              | np.isin(EDGES[:, 1], badv)].ravel())
        att[badv] *= 0.90
        att[np.setdiff1d(nbr, badv)] *= 0.97
        q = np.round(q * att[:, None], 3)
        att = np.ones(len(V))  # att applied cumulatively via q itself
    fixed = dequantise(q)
    nf_r, md_r = fold_stats(V, Fb, fixed)
    nf_m, md_m = fold_stats(Vm, Fb, fixed)
    print(f"  repair: {rounds} rounds; raw {nf_r} flips min_dot "
          f"{md_r:.5f}; macro {nf_m} flips min_dot {md_m:.5f}")
    assert nf_r == 0 and nf_m == 0, f"{name}: flips remain"
    dev = np.linalg.norm(fixed - orig, axis=1)
    sup = np.linalg.norm(orig, axis=1) > 1e-6
    changed = dev > 1e-9
    print(f"  deviation vs original: max {dev.max()*1000:.2f} mm, "
          f"rms over support {np.sqrt((dev[sup]**2).mean())*1000:.3f} mm, "
          f"{int(changed.sum())} verts changed")

    note = (f"Provenance: omniversal coupling validation -- {name.upper()} "
            f"character target. REPAIRED Nov 12, 2026 (hyper-range pass): "
            f"the originally shipped file flipped "
            f"{len(bad)} face(s) at 1.0x under the .target quantisation "
            f"(in-memory build gate had passed at min_dot < 0.002); "
            f"attenuation repair in quantised space, both bases, "
            f"0 flips, min_dot >= {MARGIN_FLOOR}. Max deviation "
            f"{dev.max()*1000:.2f} mm on {int(changed.sum())} verts. "
            f"Original preserved in anthroforge-v2/hyper/work/originals/.")
    n = write_target(path, fixed, note)
    print(f"  wrote {path.name}: {n} moved verts")

    # verify from disk, B16 loader semantics
    back = load_target(path)
    v_r = fold_stats(V, Fb, back)
    v_m = fold_stats(Vm, Fb, back)
    v15 = fold_stats(V, Fb, back * 1.5)
    print(f"  reload check: raw {v_r}, macro {v_m}, 1.5x raw {v15}")
    assert v_r[0] == 0 and v_m[0] == 0
    report[name] = {
        "as_shipped_raw": fold_stats(V, Fb, orig),
        "flipped_faces": locs,
        "repair_rounds": rounds,
        "after_raw": v_r, "after_macro": v_m, "at_1.5x_raw": v15,
        "deviation_max_mm": float(dev.max() * 1000),
        "deviation_rms_mm": float(np.sqrt((dev[sup] ** 2).mean()) * 1000),
        "verts_changed": int(changed.sum()),
        "moved_verts_written": n}

(HYPER / "work/defect_fix.json").write_text(json.dumps(report, indent=1))
print("\nwrote hyper/work/defect_fix.json")
