#!/usr/bin/env python3
"""Quantised-space fold repair for the neck-fixed body.muscle.target.

The source-level neck fix (build_bara.py: hi_diff("Weight") ->
"Weight 0 to 1") put real mass in the neck band; the build's float
repair gated at dot < 0, so the shipped .target files sat ON the fold
boundary there and the format's 0.1 mm quantisation flipped faces:
muscle solo 1 flip (macro), combined 3 (raw) / 2 (macro), worst
min_dot -0.037.

Repair follows the hyper-range precedent (hyper/scripts/
fix_coupling_defects.py) exactly: attenuation IN QUANTISED SPACE --
the exact numbers that ship -- iterated to 0 flips AND min normalised
dot >= 0.01 on BOTH bases. Because body.bara.strongman.target ships
too, the gate is judged on the muscle solo AND the compositions
(+width, +width+tissue); only the muscle field is attenuated.
bara_fields.npz is updated to the repaired field so the app instance
packs stay identical to the shipped target.
"""
import json
import sys
from pathlib import Path

import numpy as np

V2 = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(V2 / "hyper/scripts"))
from hyper_common import (BP, body_edges, face_dots, fold_stats,
                          load_base, load_macro, load_target, quantise,
                          dequantise, write_target)

MARGIN_FLOOR = 0.01
MARGIN_BAND = 0.02
MAX_ROUNDS = 600

V, F, Fb = load_base()
Vm = load_macro(V)
EDGES = body_edges(Fb)

M_path = BP / "body.muscle.target"
orig = load_target(M_path)
W = load_target(BP / "body.chest.width.target")
T = load_target(BP / "body.tissue.strongman.target")

for nm, D in (("muscle", orig), ("muscle+width", orig + W),
              ("combined", orig + W + T)):
    for base, bn in ((V, "raw"), (Vm, "macro")):
        nf, md = fold_stats(base, Fb, D)
        print(f"  as-shipped {nm:14s} {bn:5s}: {nf} flips, min_dot {md:+.5f}")

q = quantise(orig)
att_total = np.ones(len(V))
rounds = 0
for rounds in range(1, MAX_ROUNDS + 1):
    cur = dequantise(q)
    weak = set()
    ok = True
    for D in (cur, cur + W, cur + W + T):
        for base in (V, Vm):
            dots = face_dots(base, Fb, D)
            if dots.min() < MARGIN_FLOOR:
                ok = False
            weak.update(np.where(dots < MARGIN_BAND)[0].tolist())
    if ok and not weak:
        break
    badv = np.unique(Fb[sorted(weak)].ravel())
    nbr = np.unique(EDGES[np.isin(EDGES[:, 0], badv)
                          | np.isin(EDGES[:, 1], badv)].ravel())
    att = np.ones(len(V))
    att[badv] *= 0.90
    att[np.setdiff1d(nbr, badv)] *= 0.97
    q = np.round(q * att[:, None], 3)
    att_total *= att
else:
    raise SystemExit("repair did not converge")

fixed = dequantise(q)
print(f"repair: {rounds} rounds")
for nm, D in (("muscle", fixed), ("muscle+width", fixed + W),
              ("combined", fixed + W + T)):
    for base, bn in ((V, "raw"), (Vm, "macro")):
        nf, md = fold_stats(base, Fb, D)
        print(f"  repaired {nm:14s} {bn:5s}: {nf} flips, min_dot {md:+.5f}")
        assert nf == 0 and md >= MARGIN_FLOOR, (nm, bn, nf, md)

dev = np.linalg.norm(fixed - orig, axis=1)
sup = np.linalg.norm(orig, axis=1) > 1e-6
changed = dev > 1e-9
print(f"deviation vs pre-repair muscle: max {dev.max()*1000:.2f} mm, "
      f"rms over support {np.sqrt((dev[sup]**2).mean())*1000:.3f} mm, "
      f"{int(changed.sum())} verts changed")

NOTE_M = ("Provenance: omniversal slider body.muscle (bara muscle "
          "vector, core), instance makehuman_hm08. HIMBO granular "
          "vocabulary composed per BARA_LESSONS 6C x Sen 4.2, yoke "
          "first; NeckMass authored from the Weight block gated to "
          "the neck. Chest width ships separately as body.chest.width. "
          "Study-only, internal - not a CC0 MakeHuman asset. "
          "See BARA_PROOF.md. "
          "REPAIRED Nov 12, 2026 (neck-field fix): attenuation repair "
          "in quantised space after the restored neck field put the "
          f"shipped file on the fold boundary; 0 flips, min_dot >= "
          f"{MARGIN_FLOOR} on both bases, solo and composed. Max "
          f"deviation {dev.max()*1000:.2f} mm on "
          f"{int(changed.sum())} verts. See FIX_NECK_FIELD.md.")
n_m = write_target(M_path, fixed, NOTE_M)
print(f"wrote {M_path.name}: {n_m} moved verts")

NOTE_C = ("Provenance: combined bara strongman build at +1/+1/+1 "
          "(body.muscle + body.chest.width + body.tissue.strongman), "
          "instance makehuman_hm08. QA convenience target; the three "
          "component sliders are the deliverable. Study-only, "
          "internal. See BARA_PROOF.md. "
          "Rebuilt Nov 12, 2026 from the repaired body.muscle "
          "(neck-field fix); see FIX_NECK_FIELD.md.")
n_c = write_target(BP / "body.bara.strongman.target", fixed + W + T, NOTE_C)
print(f"wrote body.bara.strongman.target: {n_c} moved verts")

# keep the float work arrays identical to what ships
npz_path = BP / "work/bara_fields.npz"
bf = np.load(npz_path)
np.savez_compressed(
    npz_path,
    muscle_core_canonical_m=fixed,
    chest_width_canonical_m=bf["chest_width_canonical_m"],
    tissue_canonical_m=bf["tissue_canonical_m"],
    region_weights=bf["region_weights"], tau=bf["tau"],
    att_muscle=bf["att_muscle"] * att_total,
    att_width=bf["att_width"], att_tissue=bf["att_tissue"])
print("bara_fields.npz: muscle_core_canonical_m := repaired field, "
      "att_muscle updated by the repair attenuation")

# verify from disk
back = load_target(M_path)
back_c = load_target(BP / "body.bara.strongman.target")
rep = {"rounds": rounds,
       "deviation_max_mm": float(dev.max() * 1000),
       "deviation_rms_mm": float(np.sqrt((dev[sup] ** 2).mean()) * 1000),
       "verts_changed": int(changed.sum()),
       "moved_verts_written": n_m, "combined_moved_verts": n_c}
for nm, D in (("muscle", back), ("combined", back_c)):
    for base, bn in ((V, "raw"), (Vm, "macro")):
        nf, md = fold_stats(base, Fb, D)
        rep[f"reload_{nm}_{bn}"] = [int(nf), float(md)]
        assert nf == 0 and md >= MARGIN_FLOOR
print("reload check:", {k: v for k, v in rep.items()
                        if k.startswith("reload")})
(BP / "work/neckfix_repair.json").write_text(json.dumps(rep, indent=1))
print("wrote work/neckfix_repair.json")
