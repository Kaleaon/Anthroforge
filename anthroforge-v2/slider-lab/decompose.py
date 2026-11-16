"""decompose.py — split one decoded slider into region/side sub-sliders.

Decomposition is the cheapest slider-count multiplier in the manual (§A):
one shipped slider becomes a family of independently-drivable pieces by
multiplying its delta field by partition-of-unity masks (mask_tools).
Because the partition weights sum to exactly 1 per vertex, the pieces sum
back to the original field EXACTLY — decomposition is lossless, and the
pieces can be re-combined in any proportion at runtime (a character can
wear left-chubby at 0.8 and right-chubby at 0.3 — asymmetric bodies that
the source slider could never express).

Worked example: "HIMBO - BodyChubby" decoded from the HIMBO V5 BodySlide
.osd (learned/tools/osdparse.py) on the HIMBO base vertex order
(learned/himbo-to-fatmales_fit.npz, 9,346 verts, Skyrim frame:
x lateral / y forward / z up, 1 unit = 0.01428 m).

Splits: side (soft L/R about x=0, ±2-unit blend) x band (height bands
z<55 lower, 55-88 torso, >88 upper, 8-unit smooth transitions).
Output: 11 canonical records (2 sides + 3 bands + 6 crosses) + parent,
each with a sparse per-base instance npz, in slider-lab/output/.

Usage: python3 decompose.py [slider-name-substring]   (default: Chubby)
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.expanduser(
    "~/workspace/character_assets/learned/tools"))
from mask_tools import lr_partition, band_partition, fold_count, SKYRIM_UNIT_M
import osdparse

OUT = os.path.join(HERE, "output")
OSD = os.path.expanduser(
    "~/workspace/character_assets/_himbo_work/CalienteTools/BodySlide/"
    "ShapeData/HIMBO/HIMBO Body - Vanilla.osd")
FIT = os.path.expanduser(
    "~/workspace/character_assets/learned/himbo-to-fatmales_fit.npz")
BASE_ID = "skyrim_himbo"


def dense_field(block, n):
    field = np.zeros((n, 3))
    field[block["indices"]] = block["diffs"]
    return field


def piece_stats(field):
    mag = np.linalg.norm(field, axis=1)
    nz = mag > 1e-9
    return {
        "diff_verts": int(nz.sum()),
        "mean_disp_units": float(mag[nz].mean()) if nz.any() else 0.0,
        "max_disp_units": float(mag.max()),
        "max_disp_m": float(mag.max() * SKYRIM_UNIT_M),
    }


def write_instance(slider_id, field):
    nz = np.nonzero(np.linalg.norm(field, axis=1) > 1e-9)[0]
    rel = "instances/%s__%s.npz" % (slider_id, BASE_ID)
    np.savez_compressed(os.path.join(OUT, rel),
                        indices=nz.astype(np.int32),
                        delta=field[nz].astype(np.float32),
                        base=np.array(BASE_ID), slider=np.array(slider_id),
                        note=np.array("delta at value +1 (one-pole); "
                                      "decomposition piece — pieces sum "
                                      "exactly to the parent field"))
    return rel, nz


def record(slider_id, label, parent, mask_rule, field, inst_rel):
    st = piece_stats(field)
    return {
        "id": slider_id,
        "label": label,
        "group": "body/torso" if "torso" in slider_id else "body",
        "kind": "slider",
        "semantics": ("Decomposition piece of %s. At +1 applies this "
                      "piece's share of the parent delta field; pieces of "
                      "one partition sum exactly to the parent."
                      % parent),
        "region": {"mask_rule": mask_rule},
        "range": {"min": 0.0, "max": 1.0, "default": 0.0, "safe_max": 1.0,
                  "units": "normalised (BodySlide native 0-100 = 0-1)",
                  "endpoint_anchor": ("max |delta| = %.4f m over %d verts"
                                      % (st["max_disp_m"],
                                         st["diff_verts"]))},
        "symmetry": "bilateral_x" if slider_id.endswith(
            ("lower", "torso", "upper")) or slider_id == parent else "none",
        "couplings": [],
        "provenance": {
            "source": "HIMBO V5 'HIMBO - BodyChubby' (.osd decode), "
                      "decomposed by slider-lab/decompose.py",
            "licence": "study-only (internal) — inherited from source mod",
            "method": "decomposition (partition-of-unity masks)",
            "parent": parent,
        },
        "instances": {BASE_ID: {"file": inst_rel, "qa": st}},
    }


def main():
    want = sys.argv[1] if len(sys.argv) > 1 else "Chubby"
    osd = osdparse.load_osd(OSD)
    blocks = {b["name"]: b for b in osd["blocks"]}
    cands = [n for n in blocks if want.lower() in n.lower()]
    if not cands:
        print("no block matching %r; available: %s" % (want, list(blocks)))
        return
    # Prefer the exact "HIMBO - Body<want>" over longer names that merely
    # contain the substring (BodyChubby vs BodyLegsChubby).
    exact = "HIMBO - Body%s" % want
    cands.sort(key=lambda n: (n != exact, len(n)))
    name = cands[0]
    fit = np.load(FIT, allow_pickle=True)
    V = fit["base_vertices"].astype(np.float64)
    F = fit["base_triangles"].astype(np.int64)
    parent_field = dense_field(blocks[name], len(V))
    parent_id = "body.chubby"
    print("parent: %r -> %s  (%d diff verts on %d-vert base)"
          % (name, parent_id, piece_stats(parent_field)["diff_verts"],
             len(V)))

    w_neg, w_pos = lr_partition(V[:, 0], centre=0.0, halfwidth=2.0)
    sides = {"left": w_pos, "right": w_neg}   # house rule: +x = left
    bands = band_partition(V[:, 2], cuts=[55.0, 88.0], width=8.0)
    band_names = ["lower", "torso", "upper"]

    pieces = {}
    for sname, w in sides.items():
        pieces[sname] = (w, "side partition: soft L/R about x=0, "
                            "+/-2 Skyrim-unit blend")
    for bname, w in zip(band_names, bands):
        pieces[bname] = (w, "height band partition on z (cuts 55/88, "
                            "8-unit smooth transitions)")
    for sname, sw in sides.items():
        for bname, bw in zip(band_names, bands):
            pieces["%s.%s" % (sname, bname)] = (
                sw * bw, "cross of side x band partitions")

    os.makedirs(os.path.join(OUT, "instances"), exist_ok=True)
    records = []
    cross_sum = np.zeros_like(parent_field)
    for pname, (w, rule) in pieces.items():
        field = parent_field * w[:, None]
        sid = "%s.%s" % (parent_id, pname)
        rel, _ = write_instance(sid, field)
        records.append(record(sid, "Chubby — %s" % pname.replace(".", " "),
                              parent_id, rule, field, rel))
        if "." in pname:
            cross_sum += field
        st = piece_stats(field)
        print("  piece %-18s verts=%5d  mean=%.3f u  max=%.3f u (%.3f m)"
              % (sid, st["diff_verts"], st["mean_disp_units"],
                 st["max_disp_units"], st["max_disp_m"]))

    # Exactness proofs (partition of unity -> lossless decomposition).
    err_cross = float(np.abs(cross_sum - parent_field).max())
    side_sum = sum(parent_field * w[:, None] for w in sides.values())
    band_sum = sum(parent_field * w[:, None] for w in bands)
    print("exactness: max |sum(6 crosses) - parent| = %.3e" % err_cross)
    print("exactness: max |L+R - parent|           = %.3e"
          % float(np.abs(side_sum - parent_field).max()))
    print("exactness: max |bands - parent|         = %.3e"
          % float(np.abs(band_sum - parent_field).max()))

    ft, fr, _ = fold_count(V, F, V + parent_field)
    print("parent at +1: folds total=%d in-region=%d" % (ft, fr))

    with open(os.path.join(OUT, "decompose_chubby_records.json"), "w") as fh:
        json.dump({"parent": parent_id, "source_slider": name,
                   "base": BASE_ID,
                   "exactness_max_err": err_cross,
                   "records": records}, fh, indent=2)
    print("wrote %d piece records (+ parent concept) -> "
          "output/decompose_chubby_records.json" % len(records))


if __name__ == "__main__":
    main()
