#!/usr/bin/env python3
"""
Cross-check: how much do the learned morph fields we own actually HANG?

One consistent metric set, applied to each field on its OWN base mesh
(canonical frame: X lateral, Y forward, Z up, metres):

  * belly band: front verts (|theta| < 1.0 rad about the torso axis) whose
    height lies within [z_peak - 0.16*H, z_peak + 0.10*H], where z_peak is
    the height of the band's strongest forward-protrusion vertex and H is
    the base body's height. The band is anchored to each field's own peak
    so different bases/proportions stay comparable.
  * mean_dz_cm: |delta|-weighted mean of the delta's OWN vertical
    component in the band -- how hard the sculptor pushed tissue down.
  * share_down: share of band |delta| mass with dz < -0.5 mm.
  * hang_index_cm: |delta|-weighted centroid height minus z_peak --
    negative means the bulk of the morph's work sits BELOW its peak.
  * fwd_centroid_cm: forward-push-weighted centroid height minus z_peak.

Fields: Fat Males (Skyrim), HIMBO BodyChubby (.osd on the HIMBO base),
Atomic Muscle 'Nuka Bull' (.osd on the AM flaccid base), and our hm08
transfers v1 / v2 / v3 (v3 only if work/belly_v3.npz exists).

Caveat kept honest: the three learned fields are whole-body morphs; only
their belly band is compared here. Our fields are belly-only by design.
"""
import io
import json
import struct
import sys
import zipfile
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
OUT = HERE.parent
WORK = OUT / "work"
LEARNED = Path.home() / "workspace/character_assets/learned"
HIMBO_NIF = (Path.home() / "workspace/character_assets/_himbo_work/CalienteTools"
             "/BodySlide/ShapeData/HIMBO/HIMBO Body - Vanilla.nif")
HIMBO_OSD = HIMBO_NIF.with_suffix(".osd")
AM_ZIP = (Path.home() / "workspace/character_assets/bara-sources"
          "/Atomic-Muscle-Modders-Resource-GitHub.zip")
AM_NIF_NAME = ("Atomic-Muscle---Modders-Resource-main/10 Modder Res - Base Body"
               "/Tools/BodySlide/ShapeData/Atomic Muscle + Hands"
               "/Atomic Muscle + Hands.nif")
AM_OSD_NAME = AM_NIF_NAME.replace(".nif", ".osd")
SK = 0.01428  # Skyrim/FO4 unit -> m (AM decode used the same 1.428 cm/unit)

sys.path.insert(0, str(LEARNED / "tools"))
from osdparse import load_osd  # noqa: E402


def extract_base_positions(data, expect_min_verts):
    """Embedded vertex stream scan, copied from himbo_full_decode.py."""
    best = None
    for phase in range(0, 32, 2):
        n = (len(data) - phase) // 32
        if n < expect_min_verts:
            continue
        rec = np.frombuffer(data[phase:phase + n * 32], dtype="<f4")
        rec = rec.reshape(n, 8).astype(np.float64)
        pos, pad = rec[:, :3], rec[:, 3]
        ok = (np.isfinite(pos).all(axis=1) & (np.abs(pos[:, 0]) < 60) &
              (np.abs(pos[:, 1]) < 45) & (pos[:, 2] > -15) &
              (pos[:, 2] < 160) & (np.abs(pad) < 0.01) &
              (np.abs(pos).max(axis=1) > 0.05))
        ch = np.diff(np.concatenate(([0], ok.view(np.int8), [0])))
        st = np.where(ch == 1)[0]
        en = np.where(ch == -1)[0]
        for s, e in zip(st, en):
            if e - s >= expect_min_verts:
                run = pos[s:e]
                cand = (int(e - s), float(run[:, 2].max() - run[:, 2].min()), run)
                if best is None or cand[:2] > best[:2]:
                    best = cand
    return None if best is None else best[2]


def compute_axis(pos):
    hgt = pos[:, 2]
    lo, hi = hgt.min(), hgt.max()
    edges = np.linspace(lo, hi, 81)
    ctr = 0.5 * (edges[:-1] + edges[1:])
    axis = np.full((len(ctr), 2), np.nan)
    for i, (a, b) in enumerate(zip(edges[:-1], edges[1:])):
        m = (hgt >= a) & (hgt < b) & (np.abs(pos[:, 0]) < 0.23)
        if m.sum() >= 4:
            axis[i] = [0.5 * (pos[m, 0].min() + pos[m, 0].max()),
                       0.5 * (pos[m, 1].min() + pos[m, 1].max())]
    ok = ~np.isnan(axis[:, 0])
    for c in range(2):
        axis[:, c] = np.interp(ctr, ctr[ok], axis[ok, c])
    k = np.ones(5) / 5
    for c in range(2):
        axis[:, c] = np.convolve(np.pad(axis[:, c], 2, mode="edge"), k, "valid")
    return ctr, axis


def band_metrics(name, base, delta):
    ctr, axis = compute_axis(base)
    ax = np.stack([np.interp(base[:, 2], ctr, axis[:, 0]),
                   np.interp(base[:, 2], ctr, axis[:, 1])], axis=1)
    rel = base[:, :2] - ax
    theta = np.arctan2(rel[:, 0], rel[:, 1])
    er = np.stack([np.sin(theta), np.cos(theta)], axis=1)
    fwd = np.einsum("ij,ij->i", delta[:, :2], er)
    mag = np.linalg.norm(delta, axis=1)
    H = float(base[:, 2].max() - base[:, 2].min())
    front = np.abs(theta) < 1.0
    cand = np.where(front & (mag > 0.002))[0]
    z_peak = float(base[cand[np.argmax(fwd[cand])], 2])
    band = front & (base[:, 2] > z_peak - 0.16 * H) & \
        (base[:, 2] < z_peak + 0.10 * H) & (mag > 0.001)
    idx = np.where(band)[0]
    w = mag[idx]
    dz = delta[idx, 2]
    out = {
        "field": name, "base_verts": int(len(base)), "band_verts": int(len(idx)),
        "body_height_m": round(H, 3), "z_peak_frac_of_height":
            round((z_peak - base[:, 2].min()) / H, 3),
        "mean_dz_cm": round(float((w * dz).sum() / w.sum()) * 100, 2),
        "share_down_pct": round(float(w[dz < -0.0005].sum() / w.sum()) * 100, 1),
        "hang_index_cm": round(float((w * (base[idx, 2] - z_peak)).sum()
                                     / w.sum()) * 100, 2),
        "fwd_centroid_cm": round(float((np.clip(fwd[idx], 0, None)
                                        * (base[idx, 2] - z_peak)).sum()
                                       / max(np.clip(fwd[idx], 0, None).sum(),
                                             1e-12)) * 100, 2),
        "max_fwd_cm": round(float(fwd[idx].max()) * 100, 2),
    }
    print(json.dumps(out))
    return out


def dense_from_osd(osd_bytes, n_verts, block_substr):
    with open("/tmp/_cc.osd", "wb") as fh:
        fh.write(osd_bytes)
    osd = load_osd("/tmp/_cc.osd")
    names = [b["name"] for b in osd["blocks"]]
    blk = next((b for b in osd["blocks"] if block_substr in b["name"]), None)
    assert blk is not None, f"block {block_substr!r} not in {names}"
    D = np.zeros((n_verts, 3))
    D[blk["indices"]] = blk["diffs"]
    return D, blk["name"], names


rows = []

# --- Fat Males (Skyrim base, full delta in the npz)
fm = np.load(LEARNED / "fat-males_body_morph.npz")
rows.append(band_metrics("Fat Males (full morph)",
                         fm["body_vertices"].astype(np.float64) * SK,
                         fm["body_delta"].astype(np.float64) * SK))

# --- HIMBO BodyChubby
pos = extract_base_positions(HIMBO_NIF.read_bytes(), 4000)
assert pos is not None and len(pos) == 9346, None if pos is None else len(pos)
D, bname, _ = dense_from_osd(HIMBO_OSD.read_bytes(), len(pos), "BodyChubby")
rows.append(band_metrics(f"HIMBO '{bname}'", pos * SK, D * SK))

# --- Atomic Muscle Nuka Bull: FIELD-LEVEL only. The FO4 BSTriShape vertex
# buffer in the +Hands NIF is packed in a format our stream scanner cannot
# recover (f32 and f16 scans both fail), so no base positions -> no band
# metrics. What the .osd diffs alone honestly support: the field's own
# vertical push over all its diff verts.
with zipfile.ZipFile(AM_ZIP) as z:
    osd_bytes = z.read(AM_OSD_NAME)
with open("/tmp/_cc.osd", "wb") as fh:
    fh.write(osd_bytes)
_osd = load_osd("/tmp/_cc.osd")
_blk = next(b for b in _osd["blocks"] if "Nuka Bull" in b["name"])
_d = _blk["diffs"] * SK
_m = np.linalg.norm(_d, axis=1)
am_row = {
    "field": f"Atomic Muscle '{_blk['name']}' (field-level only)",
    "base_verts": None, "band_verts": int(len(_d)),
    "body_height_m": None, "z_peak_frac_of_height": None,
    "mean_dz_cm": round(float((_m * _d[:, 2]).sum() / _m.sum()) * 100, 2),
    "share_down_pct": round(float(_m[_d[:, 2] < -0.0005].sum()
                                  / _m.sum()) * 100, 1),
    "hang_index_cm": None, "fwd_centroid_cm": None,
    "max_fwd_cm": None,
    "note": "no base positions recoverable from the FO4 NIF; band metrics "
            "not computable -- field-level dz stats only",
}
print(json.dumps(am_row))
rows.append(am_row)

# --- ours: hm08 v1 / v2 / v3
corr = np.load(WORK / "correspondence.npz")
with zipfile.ZipFile(Path.home() / "workspace/stick-figure-avatar/photoreal"
                     "/tools/mpfb2.zip") as z:
    obj_lines = z.read("mpfb/data/3dobjs/base.obj").decode().splitlines()
mh_obj = np.array([[float(x) for x in l.split()[1:4]]
                   for l in obj_lines if l.startswith("v ")])
mh_pos = np.stack([mh_obj[:, 0], mh_obj[:, 2], mh_obj[:, 1]], axis=1) * 0.1
rows.append(band_metrics("ours v1 (protrusion transfer)",
                         mh_pos, corr["mh_delta_canonical_m"]))
v2 = np.load(WORK / "belly_v2.npz")
rows.append(band_metrics("ours v2 (gravity pass)",
                         mh_pos, v2["delta_v2_canonical_m"]))
if (WORK / "belly_v3.npz").exists():
    v3 = np.load(WORK / "belly_v3.npz")
    rows.append(band_metrics("ours v3 (realistic gravity)",
                             mh_pos, v3["delta_v3_canonical_m"]))

(WORK / "crosscheck_fields.json").write_text(json.dumps(rows, indent=1))
print("saved work/crosscheck_fields.json")
