#!/usr/bin/env python3
"""
fit_score.py — voxel buried-vertex fit scoring for AnthroForge parts.

Method (from the Khajiit Hair Unlock study, LoversLab pass, Nov 12 2026):
that project's Python generator scored 1,733 hairstyles by how their
vertices sat against the Khajiit skull/muzzle/ear volumes. We generalise
it into the PARTS_STANDARD fit gate: voxelise the BASE volume, then test
every PART vertex against it.

Three numbers are reported — never burial alone, because a part floating
in empty space scores a "perfect" 0% buried while fitting nothing:

  buried_pct   % of part vertices inside the base volume.
               Some burial is CORRECT (ear bases, teeth roots, horn
               cores are supposed to seat into the base). Deep burial
               is not — see excess_pct.
  engaged_pct  % of part vertices within the contact band of the base
               surface (outside within `band`, or buried no deeper than
               `band`). This is the coverage term: a fitted part hugs
               the surface it mounts on.
  excess_pct   % of part vertices buried deeper than `max_depth`
               (default 15% of the part's own bounding-box diagonal).
               Deep burial = swallowed, mis-scaled, or wrong-frame part.

  fit_score    engaged * (1 - excess), in [0, 1].
               >= 0.75 fitted · 0.40-0.75 partial · < 0.40 poor.

Cavity caveat: the score measures SURFACE-SEATING fit (the Khajiit hair
use case). A part designed to sit inside a hollow (tongue in a mouth
cavity) will score as deep-buried against a SOLID base mesh. Score
cavity parts against a hollowed base or read buried_pct as their
seating depth instead. See PARTS_STANDARD.md §5.

Loaders: STL (binary + ascii) and OBJ, numpy only for geometry;
scipy.ndimage provides the distance transforms. The solid volume is a
3-axis scanline majority fill (`solidify`), because real bases are
open shells and a flood fill leaks out of them. No trimesh dependency
(not installed on this VM).

Usage:
  python3 fit_score.py --base HEAD.stl [--base JAW.stl ...] \
      --part TEETH.stl [--resolution 128] [--band-voxels 3] [--json]
Multiple --base files are unioned into one volume (e.g. head + jaw).
"""

import argparse
import json
import struct
import sys

import numpy as np
from scipy import ndimage


# ---------------------------------------------------------------- loaders

def load_stl(path):
    with open(path, "rb") as fh:
        data = fh.read()
    if data[:5] == b"solid" and b"facet" in data[:2048]:
        # ascii STL
        verts = []
        for line in data.decode("utf-8", "ignore").splitlines():
            line = line.strip()
            if line.startswith("vertex"):
                verts.append([float(x) for x in line.split()[1:4]])
        v = np.asarray(verts, dtype=np.float64)
        return v, np.arange(len(v)).reshape(-1, 3)
    n = struct.unpack("<I", data[80:84])[0]
    rec = np.frombuffer(data, dtype=np.uint8, offset=84, count=n * 50)
    rec = rec.reshape(n, 50)
    floats = rec[:, :48].copy().view(np.float32).reshape(n, 12)
    tris = floats[:, 3:12].reshape(n, 3, 3)  # skip the normal
    verts = tris.reshape(-1, 3).astype(np.float64)
    return verts, np.arange(len(verts)).reshape(-1, 3)


def load_obj(path):
    verts, faces = [], []
    with open(path, "r", errors="ignore") as fh:
        for line in fh:
            if line.startswith("v "):
                verts.append([float(x) for x in line.split()[1:4]])
            elif line.startswith("f "):
                idx = []
                for tok in line.split()[1:]:
                    i = int(tok.split("/")[0])
                    idx.append(i - 1 if i > 0 else len(verts) + i)
                for k in range(1, len(idx) - 1):
                    faces.append([idx[0], idx[k], idx[k + 1]])
    return (np.asarray(verts, dtype=np.float64),
            np.asarray(faces, dtype=np.int64))


def load_mesh(path):
    if path.lower().endswith(".stl"):
        return load_stl(path)
    if path.lower().endswith(".obj"):
        return load_obj(path)
    raise SystemExit(f"unsupported format (STL/OBJ only): {path}")


# ------------------------------------------------------------ voxelisation

def surface_samples(verts, tris, spacing):
    """Barycentric samples over every triangle, spaced <= spacing apart."""
    a = verts[tris[:, 0]]
    b = verts[tris[:, 1]]
    c = verts[tris[:, 2]]
    longest = np.maximum.reduce([
        np.linalg.norm(b - a, axis=1),
        np.linalg.norm(c - b, axis=1),
        np.linalg.norm(a - c, axis=1)])
    steps = np.maximum(1, np.ceil(longest / spacing).astype(int))
    out = []
    for i in range(len(tris)):
        n = steps[i]
        if n == 1:
            out.append(((a[i] + b[i] + c[i]) / 3.0).reshape(1, 3))
            continue
        u = np.linspace(0, 1, n + 1)
        uu, vv = np.meshgrid(u, u)
        mask = (uu + vv) <= 1.0
        pts = (a[i] + uu[mask, None] * (b[i] - a[i])
               + vv[mask, None] * (c[i] - a[i]))
        out.append(pts)
    return np.concatenate(out) if out else np.empty((0, 3))


def _fill_axis(grid, axis):
    """Fill, along `axis`, every run between the first and last marked
    voxel on each line."""
    g = np.moveaxis(grid, axis, 0)
    fwd = np.maximum.accumulate(g, axis=0)
    bwd = np.maximum.accumulate(g[::-1], axis=0)[::-1]
    return np.moveaxis(fwd & bwd, 0, axis)


def solidify(surface_grid):
    """Majority-vote solid volume from a surface-voxel shell.

    Real bases are open shells (a fursuit head has a neck hole; a game
    head is a thin skin). binary_fill_holes fills nothing when the
    shell leaks. Filling scanlines along each axis and keeping voxels
    claimed by >= 2 of the 3 fills closes open bottoms and pinholes
    while staying honest at silhouettes."""
    votes = (_fill_axis(surface_grid, 0).astype(np.int8)
             + _fill_axis(surface_grid, 1).astype(np.int8)
             + _fill_axis(surface_grid, 2).astype(np.int8))
    return votes >= 2


def voxelise(meshes, resolution):
    """Union voxelisation of one or more (verts, tris) base meshes.

    Grid is sized so the longest bbox axis gets `resolution` voxels.
    Returns (filled_grid, origin, voxel_size)."""
    all_v = np.concatenate([m[0] for m in meshes])
    lo = all_v.min(axis=0)
    hi = all_v.max(axis=0)
    diag = float(np.linalg.norm(hi - lo))
    voxel = diag / resolution
    origin = lo - 2 * voxel
    shape = np.ceil((hi + 2 * voxel - origin) / voxel).astype(int)
    grid = np.zeros(tuple(shape), dtype=bool)
    for verts, tris in meshes:
        pts = surface_samples(verts, tris, spacing=voxel * 0.7)
        idx = np.floor((pts - origin) / voxel).astype(int)
        ok = np.all((idx >= 0) & (idx < shape), axis=1)
        grid[tuple(idx[ok].T)] = True
    filled = solidify(grid)
    return filled, origin, voxel


# ----------------------------------------------------------------- scoring

def score_part(part_verts, filled, origin, voxel, band_voxels=3,
               max_depth_frac=0.15):
    lo = part_verts.min(axis=0)
    hi = part_verts.max(axis=0)
    part_diag = float(np.linalg.norm(hi - lo)) or 1.0
    band = band_voxels * voxel
    max_depth = max_depth_frac * part_diag

    # signed distance (approx): inside depth from EDT of the solid,
    # outside distance from EDT of the complement.
    dist_in = ndimage.distance_transform_edt(filled) * voxel
    dist_out = ndimage.distance_transform_edt(~filled) * voxel

    idx = np.floor((part_verts - origin) / voxel).astype(int)
    shape = np.array(filled.shape)
    in_grid = np.all((idx >= 0) & (idx < shape), axis=1)
    buried = np.zeros(len(part_verts), dtype=bool)
    signed = np.full(len(part_verts), np.inf)  # + outside, - inside
    if in_grid.any():
        ii = tuple(idx[in_grid].T)
        buried[in_grid] = filled[ii]
        signed[in_grid] = np.where(buried[in_grid],
                                   -dist_in[ii], dist_out[ii])
    buried_pct = 100.0 * buried.mean()
    engaged_pct = 100.0 * (np.abs(signed) <= band).mean()
    excess_pct = 100.0 * (signed < -max_depth).mean()
    fit = (engaged_pct / 100.0) * (1.0 - excess_pct / 100.0)
    verdict = "fitted" if fit >= 0.75 else "partial" if fit >= 0.40 else "poor"
    return {
        "part_verts": int(len(part_verts)),
        "buried_pct": round(float(buried_pct), 2),
        "engaged_pct": round(float(engaged_pct), 2),
        "excess_pct": round(float(excess_pct), 2),
        "fit_score": round(float(fit), 3),
        "verdict": verdict,
        "band_world": round(float(band), 4),
        "max_depth_world": round(float(max_depth), 4),
        "out_of_grid_pct": round(100.0 * float((~in_grid).mean()), 2),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--base", action="append", required=True,
                    help="base mesh (repeatable; unioned)")
    ap.add_argument("--part", required=True, help="part mesh to score")
    ap.add_argument("--resolution", type=int, default=128,
                    help="voxels along the base's longest axis")
    ap.add_argument("--band-voxels", type=float, default=3.0,
                    help="contact band width, in voxels")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    bases = [load_mesh(p) for p in args.base]
    part_v, _ = load_mesh(args.part)
    filled, origin, voxel = voxelise(bases, args.resolution)
    res = score_part(part_v, filled, origin, voxel,
                     band_voxels=args.band_voxels)
    res["base"] = args.base
    res["part"] = args.part
    res["voxel_size"] = round(float(voxel), 5)
    res["grid_dims"] = list(filled.shape)
    if args.json:
        print(json.dumps(res, indent=2))
    else:
        print(f"base={args.base} part={args.part}")
        for k, v in res.items():
            if k not in ("base", "part"):
                print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
