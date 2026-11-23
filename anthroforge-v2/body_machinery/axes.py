"""Pure torso/limb centreline, landmark, and cylindrical parameter helpers.

Zero file I/O, mesh loads, or console output occur at import time.
"""

from __future__ import annotations

import numpy as np


def sstep(x, a: float, b: float):
    """Hermite smoothstep with ``(x, a, b)`` argument order (bara/character convention)."""
    t = np.clip((np.asarray(x, float) - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def smoothstep(a: float, b: float, x):
    """Hermite smoothstep with ``(a, b, x)`` argument order (first-proof v5+ convention)."""
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def cosfade(a: float, b: float, x):
    """Cosine fade from 1 at ``x <= a`` to 0 at ``x >= b``."""
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return 0.5 + 0.5 * np.cos(np.pi * t)


def compute_axis(pos: np.ndarray, gate: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray]:
    """80-slab torso centreline in ``(x, y)`` as a function of height ``z``,
    smoothed with an edge-padded 5-tap moving average."""
    if gate is None:
        gate = np.ones(len(pos), bool)
    hgt = pos[:, 2]
    lo, hi = hgt[gate].min(), hgt[gate].max()
    edges = np.linspace(lo, hi, 81)
    ctr = 0.5 * (edges[:-1] + edges[1:])
    axis = np.full((len(ctr), 2), np.nan)
    for i, (a, b) in enumerate(zip(edges[:-1], edges[1:])):
        m = gate & (hgt >= a) & (hgt < b) & (np.abs(pos[:, 0]) < 0.23)
        if m.sum() >= 4:
            axis[i] = [
                0.5 * (pos[m, 0].min() + pos[m, 0].max()),
                0.5 * (pos[m, 1].min() + pos[m, 1].max()),
            ]
    ok = ~np.isnan(axis[:, 0])
    for c in range(2):
        axis[:, c] = np.interp(ctr, ctr[ok], axis[ok, c])
    k = np.ones(5) / 5
    for c in range(2):
        axis[:, c] = np.convolve(np.pad(axis[:, c], 2, mode="edge"), k, "valid")
    return ctr, axis


def axis_at(ctr: np.ndarray, axis: np.ndarray, hgt: np.ndarray | float) -> np.ndarray:
    """Interpolate ``(x, y)`` torso axis coordinates at height(s) ``hgt``."""
    return np.stack(
        [np.interp(hgt, ctr, axis[:, 0]), np.interp(hgt, ctr, axis[:, 1])],
        axis=1,
    )


def axis_at_3d(zg: np.ndarray, slices: np.ndarray, z: float) -> np.ndarray:
    """Interpolate 3D slice centroid ``(x, y, z)`` at height ``z`` (Blender QA convention)."""
    return np.array(
        [np.interp(z, zg, slices[:, 0]), np.interp(z, zg, slices[:, 1]), z]
    )


def crotch_of(
    pos: np.ndarray,
    gate: np.ndarray | None = None,
    mid_hw: float = 0.030,
    slab_hw: float = 0.060,
) -> float:
    """Perineal roof landmark height inside the midline/depth slab."""
    if gate is None:
        gate = np.ones(len(pos), bool)
    mid = gate & (np.abs(pos[:, 0]) < mid_hw) & (np.abs(pos[:, 1]) < slab_hw)
    return float(pos[mid, 2].min())


def neck_base(
    pos: np.ndarray,
    ctr: np.ndarray,
    axis: np.ndarray,
    crotch: float,
    label: str | None = "mesh",
    *,
    log_mode: str | None = "chest",
    fallback_top: bool = False,
) -> float | None:
    """Detect neck-base height: first run of 3 height bands above the chest
    width peak narrower than 55% of chest width (``r < 0.23`` m gate).

    ``log_mode``:
    - ``"chest"``: prints ``"{label}: chest ... neck base ..."`` (bara/v1-v4 default)
    - ``"neck"``: prints ``"{label}: neck base ..."`` (v5/v5.2)
    - ``None``: silent (coupling validation, definition, neck/forearm, v5.1)
    """
    ax = axis_at(ctr, axis, pos[:, 2])
    r = np.linalg.norm(pos[:, :2] - ax, axis=1)
    gated = r < 0.23
    bands = np.linspace(crotch, pos[:, 2].max(), 160)
    C = 0.5 * (bands[:-1] + bands[1:])
    Wd = np.zeros(len(C))
    for i, (a, b) in enumerate(zip(bands[:-1], bands[1:])):
        m = gated & (pos[:, 2] >= a) & (pos[:, 2] < b)
        if m.sum() >= 4:
            Wd[i] = np.percentile(pos[m, 0], 99) - np.percentile(pos[m, 0], 1)
    above = C > crotch + 0.20 * (C[-1] - crotch)
    chest_i = int(np.argmax(np.where(above, Wd, 0)))
    neck, run = None, 0
    for i in range(chest_i + 1, len(Wd)):
        if 0 < Wd[i] < 0.55 * Wd[chest_i]:
            run += 1
            if run >= 3:
                neck = float(C[i - 2])
                break
        else:
            run = 0
    if neck is None and fallback_top:
        neck = float(C[-1])
    if label is not None and log_mode is not None:
        if log_mode == "chest":
            print(
                f"{label}: chest {C[chest_i]:.3f} m (W={Wd[chest_i]:.3f} m), "
                f"neck base {neck:.4f} m"
            )
        elif log_mode == "neck":
            print(f"{label}: neck base {neck:.4f} m")
        else:
            raise ValueError(f"unknown neck_base log_mode {log_mode!r}")
    return neck


def torso_params(
    pos: np.ndarray,
    crotch: float | None = None,
    neck: float | None = None,
    label: str = "mesh",
    *,
    verbose: bool = True,
):
    """Return ``(h, theta, r, axis_xy, crotch, neck, L)`` in the canonical
    cylindrical torso convention (``theta = atan2(rel_x, rel_y)``, ``0`` = front),
    resolving ``crotch_of`` and ``neck_base`` when ``crotch`` / ``neck`` are
    omitted."""
    gate = np.ones(len(pos), bool)
    ctr, axis = compute_axis(pos, gate)
    if crotch is None:
        crotch = crotch_of(pos, gate, 0.030, 0.060)
    if neck is None:
        neck = neck_base(
            pos,
            ctr,
            axis,
            crotch,
            label,
            log_mode="chest" if verbose else None,
        )
    ax = axis_at(ctr, axis, pos[:, 2])
    rel = pos[:, :2] - ax
    r = np.linalg.norm(rel, axis=1)
    theta = np.arctan2(rel[:, 0], rel[:, 1])
    h = (pos[:, 2] - crotch) / (neck - crotch)
    return h, theta, r, ax, crotch, neck, neck - crotch


def torso_cylindrical(
    pos: np.ndarray,
    ctr: np.ndarray,
    axis: np.ndarray,
    crotch: float,
    neck: float,
):
    """Return ``(h, theta, ax, r)`` from precomputed ``(ctr, axis)``
    (first-proof v1-v4 / masculine-base convention)."""
    ax = axis_at(ctr, axis, pos[:, 2])
    rel = pos[:, :2] - ax
    r = np.linalg.norm(rel, axis=1)
    theta = np.arctan2(rel[:, 0], rel[:, 1])
    h = (pos[:, 2] - crotch) / (neck - crotch)
    return h, theta, ax, r


def smooth_polyline(pts: np.ndarray, passes: int = 3) -> np.ndarray:
    """Binomial interior smoothing with endpoints fixed."""
    pts = pts.copy()
    for _ in range(passes):
        mid = 0.25 * pts[:-2] + 0.5 * pts[1:-1] + 0.25 * pts[2:]
        pts[1:-1] = mid
    return pts


def extract_limbs(
    pos: np.ndarray,
    gate: np.ndarray | None = None,
    label: str | None = "mesh",
    *,
    neck_log_mode: str | None = "neck",
    neck_fallback_top: bool = False,
    verbose: bool = True,
) -> dict[str, dict]:
    """Extract proximal->distal polylines for ``arm_R``, ``arm_L``, ``leg_R``,
    and ``leg_L``."""
    if gate is None:
        gate = np.ones(len(pos), bool)
    ctr, axis = compute_axis(pos, gate)
    ax_x = lambda z: np.interp(z, ctr, axis[:, 0])
    crotch = crotch_of(pos, gate)
    neck = neck_base(
        pos,
        ctr,
        axis,
        crotch,
        label,
        log_mode=neck_log_mode if verbose else None,
        fallback_top=neck_fallback_top,
    )
    zmin = float(pos[gate, 2].min())
    out: dict[str, dict] = {}
    for side, sname in ((1.0, "R"), (-1.0, "L")):
        seeds = (
            gate
            & (np.sign(pos[:, 0] - ax_x(pos[:, 2])) == side)
            & (np.abs(pos[:, 0] - ax_x(pos[:, 2])) > 0.025)
            & (pos[:, 2] < crotch + 0.02)
            & (pos[:, 2] > zmin + 0.09)
        )
        pts = []
        zb = np.arange(zmin + 0.09, crotch + 0.02, 0.025)
        for a in zb:
            m = seeds & (pos[:, 2] >= a) & (pos[:, 2] < a + 0.025)
            if m.sum() >= 4:
                pts.append(pos[m].mean(axis=0))
        pts_arr = np.array(pts)
        d_top = pts_arr[-1] - pts_arr[-2]
        d_top /= np.linalg.norm(d_top)
        d_bot = pts_arr[0] - pts_arr[1]
        d_bot /= np.linalg.norm(d_bot)
        pts_arr = np.vstack(
            [pts_arr[0] + d_bot * 0.05, pts_arr, pts_arr[-1] + d_top * 0.06]
        )
        pts_arr = smooth_polyline(pts_arr[::-1].copy())
        seg = np.linalg.norm(np.diff(pts_arr, axis=0), axis=1)
        out[f"leg_{sname}"] = {
            "pts": pts_arr,
            "length": float(seg.sum()),
            "side": side,
            "kind": "leg",
        }
    for side, sname in ((1.0, "R"), (-1.0, "L")):
        seeds = (
            gate
            & (np.sign(pos[:, 0] - ax_x(pos[:, 2])) == side)
            & (np.abs(pos[:, 0] - ax_x(pos[:, 2])) > 0.17)
            & (pos[:, 2] > crotch + 0.10)
            & (pos[:, 2] < neck + 0.02)
        )
        P = pos[seeds]
        c0 = P.mean(axis=0)
        _, _, vt = np.linalg.svd(P - c0, full_matrices=False)
        d = vt[0]
        if d[0] * side < 0:
            d = -d
        t = (P - c0) @ d
        pts = []
        tb = np.arange(t.min(), t.max(), 0.025)
        for a in tb:
            m = (t >= a) & (t < a + 0.025)
            if m.sum() >= 3:
                pts.append(P[m].mean(axis=0))
        pts_arr = np.array(pts)
        d0 = pts_arr[1] - pts_arr[0]
        d0 /= np.linalg.norm(d0)
        d1 = pts_arr[-1] - pts_arr[-2]
        d1 /= np.linalg.norm(d1)
        pts_arr = np.vstack([pts_arr[0] - d0 * 0.05, pts_arr, pts_arr[-1] + d1 * 0.03])
        pts_arr = smooth_polyline(pts_arr)
        seg = np.linalg.norm(np.diff(pts_arr, axis=0), axis=1)
        out[f"arm_{sname}"] = {
            "pts": pts_arr,
            "length": float(seg.sum()),
            "side": side,
            "kind": "arm",
        }
    if verbose and label is not None:
        for k, v in out.items():
            print(
                f"{label} {k}: {len(v['pts'])} axis pts, length "
                f"{v['length']*100:.1f} cm, prox {np.round(v['pts'][0],3)}, "
                f"dist {np.round(v['pts'][-1],3)}"
            )
    return out


def limb_params(pos: np.ndarray, limb: dict):
    """Return ``(s, dist, phi, er, adir)`` for every vertex relative to one
    limb polyline, with ``phi`` measured in mirrored right-limb space."""
    pts = limb["pts"]
    side = limb["side"]
    segv = np.diff(pts, axis=0)
    seglen = np.linalg.norm(segv, axis=1)
    cum = np.concatenate([[0], np.cumsum(seglen)])
    L = cum[-1]
    best_d2 = np.full(len(pos), np.inf)
    s_out = np.zeros(len(pos))
    pt_out = np.zeros_like(pos)
    dir_out = np.zeros_like(pos)
    for i, (p0, v) in enumerate(zip(pts[:-1], segv)):
        vv = max(float(v @ v), 1e-14)
        tt = np.clip(((pos - p0) @ v) / vv, 0, 1)
        q = p0 + tt[:, None] * v
        d2 = np.einsum("ij,ij->i", pos - q, pos - q)
        m = d2 < best_d2
        best_d2[m] = d2[m]
        s_out[m] = (cum[i] + tt[m] * seglen[i]) / L
        pt_out[m] = q[m]
        dir_out[m] = v / seglen[i]
    dist = np.sqrt(best_d2)
    rel = pos - pt_out
    er = rel / np.maximum(dist, 1e-9)[:, None]
    rel_m = rel.copy()
    rel_m[:, 0] *= side
    adir_m = dir_out.copy()
    adir_m[:, 0] *= side
    a = adir_m
    eo = np.tile(np.array([1.0, 0, 0]), (len(pos), 1))
    eo = eo - np.einsum("ij,ij->i", eo, a)[:, None] * a
    eo /= np.maximum(np.linalg.norm(eo, axis=1, keepdims=True), 1e-12)
    ef = np.tile(np.array([0.0, 1.0, 0]), (len(pos), 1))
    ef = (
        ef
        - np.einsum("ij,ij->i", ef, a)[:, None] * a
        - np.einsum("ij,ij->i", ef, eo)[:, None] * eo
    )
    ef /= np.maximum(np.linalg.norm(ef, axis=1, keepdims=True), 1e-12)
    reln = rel_m / np.maximum(dist, 1e-9)[:, None]
    phi = np.arctan2(
        np.einsum("ij,ij->i", reln, ef),
        np.einsum("ij,ij->i", reln, eo),
    )
    return s_out, dist, phi, er, dir_out
