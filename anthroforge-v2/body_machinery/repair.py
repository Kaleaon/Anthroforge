"""Pure mesh adjacency, slope limiting, fold repair, and target quantisation.

Zero file I/O, mesh loads, or console output occur at import time.
"""

from __future__ import annotations

import numpy as np


def body_edges(faces: np.ndarray, *, body_end: int | None = None) -> np.ndarray:
    """Sorted unique undirected edges ``(u, v)`` of ``faces``, optionally
    filtered to ``u < body_end and v < body_end``."""
    es = set()
    if body_end is None:
        for a, b, c in faces:
            for u, v in ((a, b), (b, c), (c, a)):
                es.add((min(int(u), int(v)), max(int(u), int(v))))
    else:
        for a, b, c in faces:
            for u, v in ((a, b), (b, c), (c, a)):
                if u < body_end and v < body_end:
                    es.add((min(int(u), int(v)), max(int(u), int(v))))
    return np.array(sorted(es))


def neighbours_of(verts: np.ndarray, edges: np.ndarray) -> np.ndarray:
    """Unique vertices incident to ``verts`` along ``edges``."""
    m = np.isin(edges[:, 0], verts) | np.isin(edges[:, 1], verts)
    return np.unique(edges[m].ravel())


def lap_smooth(
    x: np.ndarray,
    mask: np.ndarray,
    edges: np.ndarray,
    iters: int = 2,
) -> np.ndarray:
    """Self-inclusive uniform graph Laplacian smoothing on ``mask`` vertices."""
    x = x.copy()
    for _ in range(iters):
        acc = x.copy()
        cnt = np.ones(len(x))
        np.add.at(acc, edges[:, 0], x[edges[:, 1]])
        np.add.at(acc, edges[:, 1], x[edges[:, 0]])
        np.add.at(cnt, edges[:, 0], 1)
        np.add.at(cnt, edges[:, 1], 1)
        div = cnt[:, None] if x.ndim == 2 else cnt
        x = np.where(mask[:, None] if x.ndim == 2 else mask, acc / div, x)
    return x


def flipped(
    pos: np.ndarray,
    delta: np.ndarray,
    faces: np.ndarray,
    *,
    tol: float = -1e-12,
) -> np.ndarray:
    """Per-face boolean mask of inverted normals under ``pos + delta``
    (``dot < tol * max(|n0|*|n1|, 1e-30)``, bara/character fold convention)."""
    p = pos + delta
    v0 = p[faces[:, 0]]
    v1 = p[faces[:, 1]]
    v2 = p[faces[:, 2]]
    n0 = np.cross(
        pos[faces[:, 1]] - pos[faces[:, 0]],
        pos[faces[:, 2]] - pos[faces[:, 0]],
    )
    n1 = np.cross(v1 - v0, v2 - v0)
    dot = np.einsum("ij,ij->i", n0, n1)
    ln = np.linalg.norm(n0, axis=1) * np.linalg.norm(n1, axis=1)
    return dot < tol * np.maximum(ln, 1e-30)


def face_dots(
    base_pos: np.ndarray,
    faces: np.ndarray,
    delta: np.ndarray,
) -> np.ndarray:
    """Normalised ``dot(base_normal, deformed_normal)`` per face."""
    p = base_pos + delta
    n0 = np.cross(
        base_pos[faces[:, 1]] - base_pos[faces[:, 0]],
        base_pos[faces[:, 2]] - base_pos[faces[:, 0]],
    )
    n1 = np.cross(p[faces[:, 1]] - p[faces[:, 0]], p[faces[:, 2]] - p[faces[:, 0]])
    ln = np.linalg.norm(n0, axis=1) * np.linalg.norm(n1, axis=1)
    return np.einsum("ij,ij->i", n0, n1) / np.maximum(ln, 1e-30)


def fold_stats(
    base_pos: np.ndarray,
    faces: np.ndarray,
    delta: np.ndarray,
    *,
    flip_tol: float = 0.0,
) -> tuple[int, float]:
    """Return ``(n_flips, min_dot)`` of ``base_pos + delta`` against ``base_pos``.

    ``flip_tol=0.0`` matches ``hyper_common.fold_stats`` (``dot < 0``);
    ``flip_tol=-1e-12`` matches ``build_coupling_validation`` /
    ``build_definition`` (``flipped`` tolerance).
    """
    dots = face_dots(base_pos, faces, delta)
    if flip_tol == 0.0:
        n_flips = int((dots < 0).sum())
    else:
        n_flips = int(flipped(base_pos, delta, faces, tol=flip_tol).sum())
    return n_flips, float(dots.min())


def cos_fold_stats(
    pos: np.ndarray,
    delta: np.ndarray,
    faces: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Return ``(cos, ok)`` with ``1e-12`` face-area guard (``build_pyn`` convention)."""
    n0 = np.cross(
        pos[faces[:, 1]] - pos[faces[:, 0]],
        pos[faces[:, 2]] - pos[faces[:, 0]],
    )
    pp = pos + delta
    n1 = np.cross(
        pp[faces[:, 1]] - pp[faces[:, 0]],
        pp[faces[:, 2]] - pp[faces[:, 0]],
    )
    l0 = np.linalg.norm(n0, axis=1)
    l1 = np.linalg.norm(n1, axis=1)
    ok = (l0 > 1e-12) & (l1 > 1e-12)
    cos = np.full(len(faces), np.nan)
    cos[ok] = np.einsum("ij,ij->i", n0[ok], n1[ok]) / (l0[ok] * l1[ok])
    return cos, ok


def slope_limit(
    D: np.ndarray,
    moved: np.ndarray,
    edges: np.ndarray,
    ref_pos: np.ndarray,
    kappa: float = 0.55,
) -> np.ndarray:
    """Bara-style edge-excess mask + 3-iteration Laplacian smoothing."""
    D = D.copy()
    nbr = np.linalg.norm(D[edges[:, 0]] - D[edges[:, 1]], axis=1)
    dist = np.linalg.norm(ref_pos[edges[:, 0]] - ref_pos[edges[:, 1]], axis=1)
    bad = nbr > kappa * dist
    if bad.any():
        mv = moved.copy()
        mv[np.unique(edges[bad].ravel())] = True
        D = lap_smooth(np.where(mv[:, None], D, 0.0), mv, edges, iters=3)
        D = np.where(mv[:, None], D, 0.0)
    return D


def slope_limit_iter(
    Ds: np.ndarray,
    edges: np.ndarray,
    ref_pos: np.ndarray,
    kappa: float = 0.55,
    *,
    max_iters: int = 80,
    supp_mask: np.ndarray | None = None,
) -> tuple[np.ndarray, int]:
    """Iterative pairwise edge-excess projection (first-proof v3-v5.2 convention)."""
    elen = np.linalg.norm(ref_pos[edges[:, 0]] - ref_pos[edges[:, 1]], axis=1)
    Ds = Ds.copy()
    for it in range(max_iters):
        diff = Ds[edges[:, 0]] - Ds[edges[:, 1]]
        dn = np.linalg.norm(diff, axis=1)
        excess = dn - kappa * elen
        if (excess <= 0).all():
            return Ds, it
        corr = np.zeros_like(Ds)
        wgt = np.zeros(len(Ds))
        m = excess > 0
        adj = (0.5 * excess[m] / np.maximum(dn[m], 1e-12))[:, None] * diff[m]
        np.add.at(corr, edges[m, 0], -adj)
        np.add.at(corr, edges[m, 1], adj)
        np.add.at(wgt, edges[m, 0], 1)
        np.add.at(wgt, edges[m, 1], 1)
        Ds += 0.7 * corr / np.maximum(wgt, 1)[:, None]
        if supp_mask is not None:
            Ds[~supp_mask] = 0.0
    return Ds, max_iters


def repair(
    D: np.ndarray,
    checks: list[tuple[np.ndarray, np.ndarray]],
    label: str,
    *,
    faces: np.ndarray,
    edges: np.ndarray,
    ref_pos: np.ndarray,
    kappa: float = 0.55,
    max_rounds: int = 80,
    att_bad: float = 0.78,
    att_nbr: float = 0.93,
    att_floor: float = 0.05,
    verbose: bool = True,
) -> tuple[np.ndarray, np.ndarray, list[int]]:
    """Surgical localised attenuation fold repair across ``(base_pos, base_delta)``
    checks (bara/character convention)."""
    nb = len(D)
    moved = np.linalg.norm(D, axis=1) > 0.0002
    D = slope_limit(D, moved, edges, ref_pos, kappa=kappa)
    att = np.ones(nb)
    traj: list[int] = []
    for it in range(max_rounds):
        badv = np.zeros(nb, bool)
        for pos, base_delta in checks:
            fl = flipped(pos, base_delta + D * att[:, None], faces)
            if fl.any():
                badv[faces[fl].ravel()] = True
        traj.append(int(badv.sum()))
        if not badv.any():
            if verbose:
                print(
                    f" {label}: clean after {it} repair iterations "
                    f"(bad-vert trajectory {traj})"
                )
            break
        nbr = np.zeros(nb, bool)
        nbr[edges[badv[edges].any(axis=1)].ravel()] = True
        att[badv] *= att_bad
        att[nbr & ~badv] *= att_nbr
        att = np.maximum(att, att_floor)
    else:
        if verbose:
            print(
                f" {label}: WARNING flips remain after {max_rounds} iterations "
                f"(trajectory {traj})"
            )
    return D * att[:, None], att, traj


def repair_inc(
    base_delta: np.ndarray,
    inc: np.ndarray,
    label: str,
    *,
    bases: tuple[tuple[np.ndarray, str], ...] | list[tuple[np.ndarray, str]],
    faces: np.ndarray,
    edges: np.ndarray,
    ref_pos: np.ndarray,
    kappa: float = 0.55,
    max_rounds: int = 80,
    att_bad: float = 0.78,
    att_nbr: float = 0.93,
    att_floor: float = 0.0,
    verbose: bool = True,
) -> tuple[np.ndarray, np.ndarray, list[int]]:
    """Staged increment fold repair over an already flip-free ``base_delta``."""
    for pos, nm in bases:
        fb, _ = fold_stats(pos, faces, base_delta, flip_tol=-1e-12)
        assert fb == 0, f"{label}: base delta not flip-free on {nm} ({fb})"
    nb = len(inc)
    moved = np.linalg.norm(inc, axis=1) > 0.0002
    inc = slope_limit(inc, moved, edges, ref_pos, kappa=kappa)
    att = np.ones(nb)
    traj: list[int] = []
    for it in range(max_rounds):
        badv = np.zeros(nb, bool)
        for pos, _nm in bases:
            fl = flipped(pos, base_delta + inc * att[:, None], faces)
            if fl.any():
                badv[faces[fl].ravel()] = True
        traj.append(int(badv.sum()))
        if not badv.any():
            if verbose:
                print(
                    f" {label}: increment clean after {it} iterations "
                    f"(trajectory {traj})"
                )
            break
        nbr = np.zeros(nb, bool)
        nbr[edges[badv[edges].any(axis=1)].ravel()] = True
        att[badv] *= att_bad
        att[nbr & ~badv] *= att_nbr
        att = np.maximum(att, att_floor)
    else:
        if verbose:
            print(f" {label}: WARNING flips remain after {max_rounds} iterations")
    return inc * att[:, None], att, traj


def quantise(delta_m: np.ndarray) -> np.ndarray:
    """Round canonical-frame delta (metres) to ``.target`` 3-decimal dm steps."""
    d_obj = np.stack([delta_m[:, 0], delta_m[:, 2], delta_m[:, 1]], axis=1) / 0.1
    return np.round(d_obj, 3)


def dequantise(d_obj_q: np.ndarray) -> np.ndarray:
    """Convert quantised ``.target``-frame dm deltas back to canonical metres."""
    d = np.stack([d_obj_q[:, 0], d_obj_q[:, 2], d_obj_q[:, 1]], axis=1)
    return d * 0.1
