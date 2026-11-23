"""author_slider.py — end-to-end procedural slider authoring.

Pipeline (manual §B): semantic definition -> landmark mask (mask_tools)
-> delta field -> QA sweep (folds / anchor / volume) -> canonical record
(MAKEHUMAN_OMNIVERSAL.md §6.1 + APP_BLUEPRINT.md §3.3) + per-base instance
(npz for the Core Service, JSON for the JS runtime) + QA report.

Worked example shipped here: head.brow.projection on the AnthroForge
neutral base head v1, from brow-study.md §5.1:
  * calibration: value = 100 x (P - 12.5 mm) / 11.4 mm (Smith & Ranyard
    midorbit chords via Ahern, Lee & Hawks 2002) [S]
  * scale-free form: chord ~= L x (0.066 + 0.00060 x native_value)
  * canonical normalised value v = native / 100, so at v = +1.0 (Krapina
    Neanderthal anchor) the brow band moves +0.060 L forward at mask = 1.
  * native range -50..+150  ->  normalised range -0.5..+1.5.

The deformation is a landmark-masked forward translation of the brow band
on the SKULL layer. Honest limit (recorded in the record itself): this is
bar *growth by translation*; the post-toral sulcus carve is BrowShelf's
job (brow-study §5.3), a separate slider.

Usage: python3 author_slider.py brow-projection
Outputs land in slider-lab/output/.
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mask_tools import (read_glb, mask_from_landmarks, signed_volume, mask_stats)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output")
HEAD_GLB = os.path.expanduser(
    "~/workspace/anthroforge-v2/base-head/neutral_base_head.glb")
HEAD_GROUPS = os.path.expanduser(
    "~/workspace/anthroforge-v2/base-head/neutral_base_head.groups.json")
BASE_ID = "anthroforge_head_v1"


# ---------------------------------------------------------------------------
# Deformation specs. A spec is data, not code: seed groups, falloff radii,
# direction, magnitude at normalised +1 (in units of head length L).
# Any masked-translation slider is authored by adding a spec dict.
# ---------------------------------------------------------------------------

BROW_PROJECTION_SPEC = {
    "id": "head.brow.projection",
    "label": "Brow Projection",
    "group": "head/eyes-brow",
    "layer": "skull",
    "seed_groups": ["BrowL", "BrowR"],
    # No group-based exclusion: on this base the painted groups overlap
    # wholesale (all 368 Brow verts are also inside "Muzzle"), so zeroing
    # by group carves cliffs into the band (54 folds in the first run).
    # Positional stop guards were also tested — every variant either
    # failed to suppress the glabella weights or introduced folds at +1.
    # The pure geodesic mask is fold-free to +1.0; see record semantics.
    "exclude_groups": [],
    "r_plateau": 0.025,      # geodesic, in L units
    "r_fall": 0.14,
    "direction": (0.0, 0.0, -1.0),   # glTF frame: forward = -Z (verified)
    "magnitude_L_at_plus1": 0.060,   # brow-study §5.1: 0.00060 x 100 x L
    "range_native": (-50.0, 150.0),
    "semantics": (
        "Forward growth of the supraorbital torus (brow band) on the skull "
        "layer. 0 = base; +1.0 = brow-study native +100 (Krapina Neanderthal "
        "anchor, midorbit chord 0.126 L vs 0.066 L baseline); +1.5 = native "
        "+150 (gorilla anchor [E]). Negative values recess the band below "
        "the modern-human zero. v1 form: masked rigid translation of the "
        "band; sulcus carving belongs to head.brow.shelf."),
    "endpoint_anchor": ("at +1.0, the midorbit brow anchor vertices sit "
                        "0.060 L forward of neutral (L = head length)"),
    "provenance": {
        "source": "brow-study.md §5.1 (Smith & Ranyard chords via Ahern, "
                  "Lee & Hawks 2002 [S]; scale-free form [D]; gorilla "
                  "extreme [E])",
        "licence": "ours — build-tier (procedural; no third-party geometry)",
        "method": "procedural authoring (landmark mask + translation)",
    },
}


def build_field(V, F, groups, spec):
    """Delta field at normalised +1 for a masked-translation spec."""
    seeds = sorted({i for g in spec["seed_groups"] for i in groups[g]})
    mask, _ = mask_from_landmarks(V, F, np.array(seeds),
                                  spec["r_plateau"], spec["r_fall"])
    for g in spec.get("exclude_groups", []):
        mask[groups[g]] = 0.0
    L = float(V[:, 2].max() - V[:, 2].min())
    d = np.array(spec["direction"], dtype=np.float64)
    d /= np.linalg.norm(d)
    field = mask[:, None] * (spec["magnitude_L_at_plus1"] * L) * d[None, :]
    return field, mask, L, seeds


def qa_sweep(V, F, field, mask, values):
    """Fold / displacement / volume QA at each slider value."""
    moved_faces = mask[F].max(axis=1) > 0.001
    vol0 = signed_volume(V, F)
    rows = []
    for v in values:
        Vd = V + v * field
        n0 = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
        n1 = np.cross(Vd[F[:, 1]] - Vd[F[:, 0]], Vd[F[:, 2]] - Vd[F[:, 0]])
        flips = np.einsum("ij,ij->i", n0, n1) < 0
        rows.append({
            "value": v,
            "folds_total": int(flips.sum()),
            "folds_in_region": int((flips & moved_faces).sum()),
            "max_displacement_L": float(np.abs(v) *
                                        np.linalg.norm(field, axis=1).max()),
            "delta_volume": float(signed_volume(Vd, F) - vol0),
        })
    return rows


def pick_anchors(V, groups):
    """Midorbit brow anchor vertices: per side, the Brow-group vertex
    nearest the canonical midorbit target point (±0.10, 0.10, -0.26)
    (front-upper brow, above the eye-socket centre at (±0.127, 0.046,
    -0.161) — measured on this base)."""
    anchors = []
    for grp, tx in (("BrowL", 0.10), ("BrowR", -0.10)):
        idx = np.array(groups[grp])
        tgt = np.array([tx, 0.10, -0.26])
        j = idx[np.argmin(np.linalg.norm(V[idx] - tgt, axis=1))]
        anchors.append(int(j))
    return anchors


def author_brow_projection():
    meshes = read_glb(HEAD_GLB)
    V, F = meshes["Head"]
    groups = json.load(open(HEAD_GROUPS))["Head"]
    spec = BROW_PROJECTION_SPEC

    field, mask, L, seeds = build_field(V, F, groups, spec)
    anchors = pick_anchors(V, groups)
    anchor_mask = [float(mask[a]) for a in anchors]
    anchor_disp = [float(np.linalg.norm(field[a])) for a in anchors]

    sweep = qa_sweep(V, F, field, mask, [-0.5, 0.5, 1.0, 1.25, 1.5])
    clean = [r["value"] for r in sweep
             if r["value"] > 0 and r["folds_in_region"] == 0]
    safe_max = max(clean) if clean else 0.0

    os.makedirs(os.path.join(OUT, "instances"), exist_ok=True)
    moved = np.linalg.norm(field, axis=1) > 1e-7
    idx = np.nonzero(moved)[0].astype(np.int32)
    inst_npz = "instances/%s__%s.npz" % (spec["id"], BASE_ID)
    np.savez_compressed(
        os.path.join(OUT, inst_npz),
        indices=idx, delta=field[idx].astype(np.float32),
        base=np.array(BASE_ID), slider=np.array(spec["id"]),
        note=np.array("delta field at normalised value +1.0; "
                      "runtime scales linearly"))
    inst_json = "instances/%s__%s.instance.json" % (spec["id"], BASE_ID)
    with open(os.path.join(OUT, inst_json), "w") as fh:
        json.dump({"slider": spec["id"], "base": BASE_ID,
                   "indices": idx.tolist(),
                   "delta": field[idx].astype(np.float32).ravel().tolist()},
                  fh)

    qa = {
        "slider": spec["id"], "base": BASE_ID,
        "head_length_L": L,
        "mask": mask_stats(mask),
        "seed_count": len(seeds),
        "anchor_vertices": anchors,
        "anchor_mask_weights": anchor_mask,
        "anchor_displacement_at_plus1_L": anchor_disp,
        "anchor_expected_L": spec["magnitude_L_at_plus1"],
        "sweep": sweep,
        "safe_max_from_sweep": safe_max,
    }
    with open(os.path.join(OUT, "%s.qa.json" % spec["id"]), "w") as fh:
        json.dump(qa, fh, indent=2)

    record = {
        "id": spec["id"],
        "label": spec["label"],
        "group": spec["group"],
        "kind": "slider",
        "layer": spec["layer"],
        "semantics": spec["semantics"],
        "region": {
            "landmarks": ["brow_band.L", "brow_band.R"],
            "mask_rule": ("geodesic falloff from BrowL+BrowR vertex groups, "
                          "plateau %.3f L, falloff to %.3f L. No group "
                          "exclusion (base groups overlap wholesale). "
                          "Glabella/medial band moves with the torus "
                          "(anatomically part of it); the low nasal bridge "
                          "carries falloff-tail weights only. A hard stop "
                          "guard per brow-study §5.8 is future work — "
                          "guard prototypes introduced folds (see QA)."
                          % (spec["r_plateau"], spec["r_fall"])),
        },
        "range": {
            "min": spec["range_native"][0] / 100.0,
            "max": spec["range_native"][1] / 100.0,
            "default": 0.0,
            "safe_max": safe_max,
            "units": "normalised (brow-study native units = 100 x value)",
            "endpoint_anchor": spec["endpoint_anchor"],
        },
        "symmetry": "bilateral_x",
        "couplings": [],
        "provenance": spec["provenance"],
        "instances": {
            BASE_ID: {
                "file": inst_npz,
                "qa": {
                    "folds_at_plus1": [r["folds_in_region"] for r in sweep
                                       if r["value"] == 1.0][0],
                    "anchor_displacement_L": max(anchor_disp),
                    "mask_verts_any": mask_stats(mask)["verts_any"],
                },
            }
        },
    }
    rec_path = os.path.join(OUT, "%s.json" % spec["id"])
    with open(rec_path, "w") as fh:
        json.dump(record, fh, indent=2)

    # Fixture for the JS runtime self-test (apply_sliders.js).
    with open(os.path.join(OUT, "fixture_head.json"), "w") as fh:
        json.dump({"base": BASE_ID,
                   "positions": V.ravel().tolist(),
                   "indices": F.ravel().tolist(),
                   "anchor_vertices": anchors,
                   "record": {"id": spec["id"], "range": record["range"]},
                   "instance": {"indices": idx.tolist(),
                                "delta": field[idx].astype(np.float32)
                                .ravel().tolist()}}, fh)

    print("authored:", spec["id"], "on", BASE_ID)
    print("  L =", L, " mask:", mask_stats(mask))
    print("  anchors:", anchors, "mask weights:", anchor_mask,
          " displacement at +1 (L):", anchor_disp)
    for r in sweep:
        print("  v=%+.2f folds(region/total)=%d/%d max|d|=%.4f L dV=%+.5f"
              % (r["value"], r["folds_in_region"], r["folds_total"],
                 r["max_displacement_L"], r["delta_volume"]))
    print("  safe_max =", safe_max)
    print("  wrote:", rec_path)
    return qa


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "brow-projection":
        author_brow_projection()
    else:
        print(__doc__)
