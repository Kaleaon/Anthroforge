#!/usr/bin/env python3
"""Build canonical-precision instance packs into library/instances/.

The shipped .target files round deltas to 0.1 mm (3 decimals, dm).
That rounding is fine for MPFB interchange but it moves the belly
lineage's thinnest fold-gate face across zero (canonical min dot
+0.0018 at +1; the rounded field reads -0.0003 — one graze, not a
fold). The app therefore carries its geometry as float64 packs
extracted from the proofs' own canonical work arrays, and the slider
records point at them via the instance's ``arrays`` form (the .target
stays recorded as the interchange form).

Every pack is verified here on the app base package: 0 flipped body
faces at +1, or the script fails. Sources:
- first-proof/work/belly_v51.npz (lin / sag / gamma) + belly_v52.npz
  (contact combined) for body.belly.protrusion;
- bara-proof/work/bara_fields.npz for the body.build.* components
  (the combined strongman pack is their sum);
- bara-proof/work/definition_fields.npz for body.definition.*;
- bara-proof/work/neck_forearm_fields.npz for neck/forearm.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

WS = Path.home() / "workspace"
APP = WS / "anthroforge-app"
sys.path.insert(0, str(APP))

from core.bases import BaseRegistry  # noqa: E402
from core.geometry import count_flips  # noqa: E402

FPW = WS / "anthroforge-v2" / "first-proof" / "work"
BPW = WS / "anthroforge-v2" / "bara-proof" / "work"
OUT = APP / "library" / "instances"
SLIDERS = APP / "library" / "sliders"
REL = "anthroforge-app/library/instances"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    base = BaseRegistry(APP / "library" / "bases").load("makehuman_hm08")
    mask = base.body_face_mask

    def check(name: str, field: np.ndarray) -> None:
        flips = count_flips(base.positions, base.positions + field,
                            base.triangles, mask)
        status = "ok" if flips == 0 else "FAIL"
        print(f"{status}  {name}: flips at +1 = {flips}")
        if flips:
            raise SystemExit(f"instance pack {name} fails the fold gate")

    def pack(slider_id: str, **arrays: np.ndarray) -> str:
        fname = f"{slider_id}__makehuman_hm08.npz"
        np.savez_compressed(OUT / fname, **arrays)
        return f"{REL}/{fname}"

    patches: dict[str, dict] = {}

    # ---- belly: lin + sag (+ contact variant linear) -------------------
    v51 = np.load(FPW / "belly_v51.npz")
    v52 = np.load(FPW / "belly_v52.npz")
    lin = v51["lin_v51_canonical_m"].astype(np.float64)
    sag = v51["sag_v5_canonical_m"].astype(np.float64)
    gamma = float(v51["gamma"])
    contact_lin = v52["delta_v52_canonical_m"].astype(np.float64) - sag
    check("body.belly.protrusion (combined)", lin + sag)
    check("body.belly.protrusion (contact)", contact_lin + sag)
    rel = pack("body.belly.protrusion", linear=lin, sag=sag,
               contact_linear=contact_lin)
    patches["body.belly.protrusion"] = {
        "pack": rel, "linear": "linear", "sag": "sag", "gamma": gamma,
        "variants": {"contact": {"linear": "contact_linear"}},
    }

    # ---- bara components + combined -------------------------------------
    bf = np.load(BPW / "bara_fields.npz")
    comp_keys = {
        "body.build.muscle": "muscle_core_canonical_m",
        "body.build.chest_width": "chest_width_canonical_m",
        "body.build.tissue_strongman": "tissue_canonical_m",
    }
    combined = np.zeros((base.n_verts, 3))
    for sid, key in comp_keys.items():
        field = bf[key].astype(np.float64)
        combined = combined + field
        check(sid, field)
        rel = pack(sid, linear=field)
        patches[sid] = {"pack": rel, "linear": "linear"}
    check("body.build.bara_strongman (sum)", combined)
    rel = pack("body.build.bara_strongman", linear=combined)
    patches["body.build.bara_strongman"] = {"pack": rel, "linear": "linear"}

    # ---- definition reliefs ----------------------------------------------
    df = np.load(BPW / "definition_fields.npz")
    for sid, key in {
        "body.definition.flat_abs": "body_definition_flat_abs",
        "body.definition.traps_valleys": "body_definition_traps_valleys",
        "body.definition.pecs_crease": "body_definition_pecs_crease",
        "body.definition.back": "body_definition_back",
    }.items():
        field = df[key].astype(np.float64)
        check(sid, field)
        rel = pack(sid, linear=field)
        patches[sid] = {"pack": rel, "linear": "linear"}

    # ---- neck / forearm ----------------------------------------------------
    nf = np.load(BPW / "neck_forearm_fields.npz")
    for sid, key in {
        "body.neck.mass": "neck_mass_canonical_m",
        "body.forearm.mass": "forearm_mass_canonical_m",
    }.items():
        field = nf[key].astype(np.float64)
        check(sid, field)
        rel = pack(sid, linear=field)
        patches[sid] = {"pack": rel, "linear": "linear"}

    # ---- patch the records ---------------------------------------------------
    for sid, arrays in patches.items():
        path = SLIDERS / f"{sid}.json"
        rec = json.loads(path.read_text(encoding="utf-8"))
        inst = rec["instances"]["makehuman_hm08"]
        inst["arrays"] = arrays
        inst.setdefault("note", "")
        path.write_text(json.dumps(rec, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")
        print("patched", path.name)
    print("instance packs built and verified")


if __name__ == "__main__":
    main()
