"""Pure OSD/NIF vertex-stream extraction and base-mesh alignment helpers.

Zero file I/O, mesh loads, or console output occur at import time.
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path
from typing import Callable

import numpy as np

SK_UNIT_M = 0.01428   # Skyrim / HIMBO unit -> metres
DM_M = 0.1            # MakeHuman decimetre -> metres
BODY_END = 13380      # hm08 body vertex count (helpers start at 13380)
HM08_N_VERTS = 19158  # hm08 total vertex count


def extract_base_positions(
    data: bytes,
    expect_min_verts: int = 4000,
) -> np.ndarray | None:
    """Scan a raw NIF byte buffer for the embedded 32-byte f32 vertex stream."""
    best = None
    for phase in range(0, 32, 2):
        n = (len(data) - phase) // 32
        if n < expect_min_verts:
            continue
        rec = np.frombuffer(data[phase : phase + n * 32], dtype="<f4")
        rec = rec.reshape(n, 8).astype(np.float64)
        pos, pad = rec[:, :3], rec[:, 3]
        ok = (
            np.isfinite(pos).all(axis=1)
            & (np.abs(pos[:, 0]) < 60)
            & (np.abs(pos[:, 1]) < 45)
            & (pos[:, 2] > -15)
            & (pos[:, 2] < 160)
            & (np.abs(pad) < 0.01)
            & (np.abs(pos).max(axis=1) > 0.05)
        )
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


def hi_diff(
    hi_blocks: dict,
    n_verts: int,
    name: str,
    *,
    prefix: str = "HIMBO - Body",
    warn_missing: bool = True,
    missed: set[str] | None = None,
) -> np.ndarray:
    """Return dense ``(n_verts, 3)`` OSD block diff for ``{prefix}{name}``.

    When ``warn_missing=True`` (``FIX_NECK_FIELD.md`` discipline), emits a
    one-time warning to ``sys.stderr`` when the block is absent from
    ``hi_blocks``; when ``warn_missing=False``, returns silent zeros.
    """
    full_name = f"{prefix}{name}"
    blk = hi_blocks.get(full_name)
    if blk is None:
        if warn_missing:
            already = missed is not None and name in missed
            if not already:
                if missed is not None:
                    missed.add(name)
                print(
                    f"WARNING: hi_diff({name!r}) -- block "
                    f"{full_name!r} not in the Vanilla OSD; "
                    "composing ZEROS for this slider",
                    file=sys.stderr,
                )
        return np.zeros((n_verts, 3))
    d = np.zeros((n_verts, 3))
    d[blk["indices"]] = blk["diffs"]
    return d


def compose_osd(
    hi_blocks: dict,
    n_verts: int,
    recipe: dict[str, float],
    *,
    scale: float = SK_UNIT_M,
    prefix: str = "HIMBO - Body",
    warn_missing: bool = True,
    missed: set[str] | None = None,
) -> np.ndarray:
    """Compose a weighted sum of OSD block diffs scaled to canonical units."""
    out = np.zeros((n_verts, 3))
    for name, val in recipe.items():
        out += hi_diff(
            hi_blocks,
            n_verts,
            name,
            prefix=prefix,
            warn_missing=warn_missing,
            missed=missed,
        ) * (val * scale)
    return out


def dense_from_osd(
    osd_bytes: bytes,
    n_verts: int,
    block_substr: str,
    load_osd_fn: Callable[[str], dict],
    *,
    tmp_path: str = "/tmp/_cc.osd",
) -> tuple[np.ndarray, str, list[str]]:
    """Decode one OSD block matching ``block_substr`` from raw bytes."""
    with open(tmp_path, "wb") as fh:
        fh.write(osd_bytes)
    osd = load_osd_fn(tmp_path)
    names = [b["name"] for b in osd["blocks"]]
    blk = next((b for b in osd["blocks"] if block_substr in b["name"]), None)
    assert blk is not None, f"block {block_substr!r} not in {names}"
    D = np.zeros((n_verts, 3))
    D[blk["indices"]] = blk["diffs"]
    return D, blk["name"], names


def align_macro_base(
    raw_pos: np.ndarray,
    mac_body_pos: np.ndarray,
    body_end: int = BODY_END,
) -> np.ndarray:
    """Range-align evaluated macro body positions onto ``raw_pos[:body_end]``
    per axis, preserving helper vertices past ``len(mac_body_pos)``."""
    out = raw_pos.copy()
    mb = mac_body_pos.copy()
    for ax in range(3):
        r0, r1 = raw_pos[:body_end, ax].min(), raw_pos[:body_end, ax].max()
        m0, m1 = mb[:, ax].min(), mb[:, ax].max()
        mb[:, ax] = r0 + (mb[:, ax] - m0) * (r1 - r0) / (m1 - m0)
    out[: len(mb)] = mb
    return out


def load_mpfb_base_obj(
    mpfb_zip_path: str | Path,
    *,
    with_first_tri_faces: bool = False,
    with_poly_faces: bool = False,
    body_end: int = BODY_END,
):
    """Read ``mpfb/data/3dobjs/base.obj`` from ``mpfb2.zip`` into canonical
    ``(x, z, y) * 0.1`` metre positions, plus optional face arrays."""
    with zipfile.ZipFile(mpfb_zip_path) as zf:
        lines = zf.read("mpfb/data/3dobjs/base.obj").decode().splitlines()
    verts = []
    first_tris = []
    polys = []
    for line in lines:
        if line.startswith("v "):
            p = line.split()
            verts.append([float(p[1]), float(p[3]), float(p[2])])
        elif line.startswith("f "):
            if with_first_tri_faces:
                first_tris.append([int(t.split("/")[0]) - 1 for t in line.split()[1:4]])
            if with_poly_faces:
                polys.append([int(t.split("/")[0]) - 1 for t in line.split()[1:]])
    V = np.array(verts, dtype=np.float64) * DM_M
    if with_first_tri_faces:
        F = np.array(first_tris)
        body = np.zeros(len(V), bool)
        body[:body_end] = True
        Fb = F[np.array([body[f].all() for f in F])]
        return V, F, Fb
    if with_poly_faces:
        return V, polys
    return V
