#!/usr/bin/env python3
"""Build the app's hm08 base geometry packages (run once; re-run only
if the source packages change).

Outputs, under ``library/bases/``:

- ``makehuman_hm08.npz`` — the default-macro hm08 base (MPFB defaults:
  gender 0.5) the whole proof lineage (belly v1-v5.2, bara proof,
  definition, coupling validation) was validated on.
- ``makehuman_hm08_masculine.npz`` — the gender-1.0 variant from
  ``anthroforge-v2/masculine-base/``.
- ``<id>.json`` base records describing frame, counts and provenance.

Frame discipline (MASCULINE_BASE.md): everything is stored in
**frame 1** — base.obj canonical, ``(x, z_obj, y_obj) x 0.1 m``, z-up
centred. The MPFB evaluated dumps are grounded (z 0..height); they are
aligned into frame 1 with the documented offset method (x/y: median of
grounded-raw over body rows; z: grounded z-min - raw body z-min;
aligned = grounded - offset). Residual after alignment must reproduce
the documented cross-check (feminine p50 ~3.2 cm / max ~6.2 cm of pure
macro deformation) or the script fails loudly.

Vertex order is base.obj order throughout (19,158 verts; body rows are
the first 13,380). Positions are stored float64 on purpose: the belly
lineage's thinnest fold-gate margin is a face whose normal dot at +1 is
+0.0018 (GRAVITY_V5.md) — float32 storage rounding flips its sign. Faces are the triangulated base.obj face list
(``mh_tris`` from the correspondence packages, 36,972 tris) — the same
topology every .target instance indexes.
"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import numpy as np

WS = Path.home() / "workspace"
APP = WS / "anthroforge-app"
OUT = APP / "library" / "bases"
MPFB_ZIP = WS / "stick-figure-avatar" / "photoreal" / "tools" / "mpfb2.zip"
FP_WORK = WS / "anthroforge-v2" / "first-proof" / "work"
MASC = WS / "anthroforge-v2" / "masculine-base"

BODY_END = 13380
DM_M = 0.1


def load_base_obj() -> tuple[np.ndarray, np.ndarray]:
    with zipfile.ZipFile(MPFB_ZIP) as z:
        lines = z.read("mpfb/data/3dobjs/base.obj").decode().splitlines()
    obj = np.array(
        [[float(x) for x in ln.split()[1:4]] for ln in lines if ln.startswith("v ")],
        dtype=np.float64,
    )
    # frame 1: (x, z_obj, y_obj) * 0.1 m — the builders' canonical frame
    pos = np.stack([obj[:, 0], obj[:, 2], obj[:, 1]], axis=1) * DM_M
    return pos, obj


def align_grounded(grounded: np.ndarray, raw: np.ndarray) -> tuple[np.ndarray, np.ndarray, dict]:
    """Align a grounded evaluated dump into frame 1 (MASCULINE_BASE.md
    method). Returns (aligned_full_array, offset, residual_stats)."""
    body_raw = raw[: len(grounded)]
    off_xy = np.median(grounded - body_raw, axis=0)[:2]
    off_z = grounded[:, 2].min() - body_raw[:, 2].min()
    offset = np.array([off_xy[0], off_xy[1], off_z])
    aligned_body = grounded - offset
    resid = np.linalg.norm(aligned_body - body_raw, axis=1)
    full = raw.copy()
    full[: len(grounded)] = aligned_body
    stats = {
        "p50_cm": float(np.percentile(resid, 50) * 100),
        "p95_cm": float(np.percentile(resid, 95) * 100),
        "max_cm": float(resid.max() * 100),
    }
    return full, offset, stats


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    raw_pos, _ = load_base_obj()
    corr = np.load(FP_WORK / "correspondence.npz")
    tris = corr["mh_tris"].astype(np.int32)
    assert raw_pos.shape == (19158, 3), raw_pos.shape
    assert tris.shape == (36972, 3), tris.shape

    # ---- default macro (gender 0.5) -------------------------------------
    macro = np.load(FP_WORK / "mh_macro_base.npz")["pos_canonical_m"].astype(np.float64)
    assert len(macro) == BODY_END
    fem, fem_off, fem_res = align_grounded(macro, raw_pos)
    print("feminine alignment offset (m):", fem_off, "residual:", fem_res)
    # Documented cross-check: p50 ~3.2 cm, max ~6.2 cm (MASCULINE_BASE.md).
    assert abs(fem_res["p50_cm"] - 3.2) < 1.0, fem_res
    assert abs(fem_res["max_cm"] - 6.2) < 1.5, fem_res
    np.savez_compressed(
        OUT / "makehuman_hm08.npz",
        positions=fem.astype(np.float64),
        triangles=tris,
        navel=np.int64(int(corr["navel_mh"])),
        body_end=np.int64(BODY_END),
    )

    # ---- masculine (gender 1.0) ------------------------------------------
    corrm = np.load(MASC / "work" / "correspondence_masc.npz")
    masc_pos = corrm["pos_neutral_canonical_m"].astype(np.float64)
    assert masc_pos.shape == (19158, 3)
    np.savez_compressed(
        OUT / "makehuman_hm08_masculine.npz",
        positions=masc_pos.astype(np.float64),
        triangles=corrm["mh_tris"].astype(np.int32),
        navel=np.int64(int(corrm["navel_mh"])),
        body_end=np.int64(BODY_END),
    )
    print("masculine package written (pre-aligned by its own pipeline)")

    # ---- base records ------------------------------------------------------
    def record(base_id: str, label: str, package: str, macro_note: str,
               source: str, extra: dict) -> dict:
        return {
            "format": "anthroforge.base",
            "version": 1,
            "id": base_id,
            "label": label,
            "package": package,
            "topology": {
                "verts": 19158,
                "body_verts": BODY_END,
                "triangles": 36972,
                "vertex_order": "MPFB base.obj order; .target instances index this order",
                "frame": "frame 1 (base.obj canonical): (x, z_obj, y_obj) x 0.1 m, "
                         "metres, up = +axis2 in stored array order [width, depth, height] "
                         "as written by the proof builders (pos = [obj.x, obj.z, obj.y])",
            },
            "macro": macro_note,
            "provenance": {"source": source, "licence": "CC0 (MakeHuman system assets via MPFB2)"},
            **extra,
        }

    fem_rec = record(
        "makehuman_hm08", "MakeHuman hm08 — default macro (gender 0.5)",
        "makehuman_hm08.npz",
        "MPFB get_default_macro_info_dict(): gender 0.5, age/muscle/weight/"
        "proportions/height/cupsize/firmness 0.5, race thirds. The base every "
        "v1-v5.2 belly, bara, definition and coupling proof was validated on.",
        "MPFB2 2.0.18 base.obj + evaluated macro dump "
        "(anthroforge-v2/first-proof/work/mh_macro_base.npz), aligned to frame 1 "
        "per anthroforge-v2/masculine-base/MASCULINE_BASE.md",
        {"alignment": {"offset_m": [float(x) for x in fem_off],
                       "residual_cm": fem_res,
                       "cross_check": "documented feminine residual p50 3.2 cm / max 6.2 cm "
                                      "(MASCULINE_BASE.md) — reproduced by this build"},
         "aliases": ["af_body_neutral_v1"],
         "alias_note": "af_body_neutral_v1 is the blueprint §3.1 default body id in "
                       "character records; it denotes this package until a bespoke "
                       "AnthroForge base replaces hm08."},
    )
    (OUT / "makehuman_hm08.json").write_text(json.dumps(fem_rec, indent=2) + "\n")

    masc_rec = record(
        "makehuman_hm08_masculine", "MakeHuman hm08 — masculine macro (gender 1.0)",
        "makehuman_hm08_masculine.npz",
        "Identical default macro dict with exactly one change: gender 0.5 -> 1.0. "
        "Under male weighting the cupsize/firmness macros are inert.",
        "anthroforge-v2/masculine-base/ (correspondence_masc.npz: pos_neutral_canonical_m, "
        "aligned by that package's own pipeline; frame_offset_m "
        "[0.0, 0.00397, 0.81676])",
        {"validation": "belly v1 transfer re-derived on this base: navel achieved "
                       "0.12257 m vs anchor 0.12447 m (error -0.19 cm); anchor deviation "
                       "vs feminine base +0.48 cm (work/qa_numbers_masc.json)"},
    )
    (OUT / "makehuman_hm08_masculine.json").write_text(json.dumps(masc_rec, indent=2) + "\n")
    print("base records written")


if __name__ == "__main__":
    main()
