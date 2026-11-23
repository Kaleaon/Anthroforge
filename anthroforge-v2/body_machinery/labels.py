"""Pure anatomical mesh labelling, limb segment chains, and region blending.

Zero file I/O, mesh loads, or console output occur at import time.
"""

from __future__ import annotations

import numpy as np

from .axes import compute_axis, sstep
from .repair import body_edges, lap_smooth

REF_ARM = np.array([0.0, 0.0, 1.0])  # "up" projected perpendicular to arm axis
REF_LEG = np.array([0.0, 1.0, 0.0])  # "forward" projected perpendicular to leg axis


def label_mesh(
    pos: np.ndarray,
    crotch: float,
    neck: float,
    body_mask: np.ndarray | None = None,
) -> dict:
    """Geometric region labels (``torso``, ``arm``, ``leg``) and joint
    landmarks (``S``/``E``/``W`` for arms, ``H``/``K``/``A`` for legs)."""
    if body_mask is None:
        body_mask = np.ones(len(pos), bool)
    z = pos[:, 2]
    ctr, axis = compute_axis(pos, np.ones(len(pos), bool))
    ax = np.stack(
        [np.interp(z, ctr, axis[:, 0]), np.interp(z, ctr, axis[:, 1])],
        axis=1,
    )
    rel = pos[:, :2] - ax
    r = np.hypot(rel[:, 0], rel[:, 1])
    edges = np.arange(z.min() - 0.005, z.max() + 0.011, 0.01)
    prof = np.full(len(edges) - 1, np.nan)
    for i, (a, b) in enumerate(zip(edges[:-1], edges[1:])):
        m = (z >= a) & (z < b) & (r < 0.23)
        if m.sum() > 8:
            prof[i] = np.percentile(r[m], 92)
    zc = 0.5 * (edges[:-1] + edges[1:])
    ok = ~np.isnan(prof)
    r92 = np.interp(z, zc[ok], prof[ok])
    side = np.sign(rel[:, 0])
    arm = (
        (r > r92 + 0.010)
        & (z > crotch - 0.02)
        & (z < neck + 0.05)
        & (side != 0)
        & (np.abs(rel[:, 0]) > 0.7 * r)
        & body_mask
    )
    leg = (z < crotch - 0.008) & ~arm & body_mask
    torso = ~arm & ~leg
    lab: dict = {
        "arm": arm,
        "leg": leg,
        "torso": torso,
        "side": side,
        "ax": ax,
        "r": r,
        "rel": rel,
    }
    lm: dict = {}
    for sgn, sname in ((1.0, "R"), (-1.0, "L")):
        am = arm & (side == sgn)
        if am.sum() > 60:
            P = pos[am]
            c = P.mean(axis=0)
            _, _, vt = np.linalg.svd(P - c, full_matrices=False)
            a = vt[0]
            s = (P - c) @ a
            e1 = P[s > np.percentile(s, 92)]
            e0 = P[s < np.percentile(s, 8)]
            d1 = np.mean(np.abs(e1[:, 0] - np.interp(e1[:, 2], ctr, axis[:, 0])))
            d0 = np.mean(np.abs(e0[:, 0] - np.interp(e0[:, 2], ctr, axis[:, 0])))
            if d0 > d1:
                a, s = -a, -s
            u = s - s.min()
            span = u.max()
            nb = 28
            bins = np.linspace(0, span, nb + 1)
            rad = np.full(nb, np.nan)
            for i in range(nb):
                m = (u >= bins[i]) & (u < bins[i + 1])
                if m.sum() > 3:
                    rad[i] = np.mean(
                        np.linalg.norm((P[m] - c) - np.outer(s[m], a), axis=1)
                    )
            okb = ~np.isnan(rad)
            rad = np.interp(np.arange(nb), np.where(okb)[0], rad[okb])
            bc = 0.5 * (bins[:-1] + bins[1:])
            sm_r = np.convolve(rad, np.ones(3) / 3, mode="same")
            loc_min = [
                i
                for i in range(1, nb - 1)
                if sm_r[i] <= sm_r[i - 1]
                and sm_r[i] <= sm_r[i + 1]
                and bc[i] > 0.20 * span
            ]
            if loc_min:
                ei = loc_min[0]
                elb_u = bc[ei]
                cand = [
                    i
                    for i in loc_min
                    if bc[i] > elb_u + 0.18 * span and bc[i] < 0.96 * span
                ]
                wri_u = (
                    bc[min(cand, key=lambda i: sm_r[i])]
                    if cand
                    else bc[min(loc_min[-1], nb - 1)]
                )
            else:
                elo = bc[(bc > 0.32 * span) & (bc < 0.68 * span)]
                elb_u = elo[np.argmin(rad[(bc > 0.32 * span) & (bc < 0.68 * span)])]
                wlo = bc[(bc > 0.74 * span) & (bc < 0.95 * span)]
                wri_u = wlo[np.argmin(rad[(bc > 0.74 * span) & (bc < 0.95 * span)])]

            def cent(uc, hw):
                m = np.abs(u - uc) < hw
                return P[m].mean(axis=0) if m.sum() > 2 else c + a * uc

            lm[f"arm{sname}"] = {
                "S": cent(0.03 * span, 0.05 * span),
                "E": cent(elb_u, 0.04 * span),
                "W": cent(wri_u, 0.035 * span),
                "span": float(span),
                "verts": np.where(am)[0],
            }
        lg = leg & (side == sgn)
        if lg.sum() > 60:
            P = pos[lg]
            top = P[P[:, 2] > crotch - 0.09]
            hip_off = (
                np.median(np.abs(top[:, 0] - np.interp(top[:, 2], ctr, axis[:, 0])))
                if len(top)
                else 0.09
            )
            H = np.array(
                [
                    np.interp(crotch, ctr, axis[:, 0]) + sgn * hip_off,
                    np.interp(crotch, ctr, axis[:, 1]),
                    crotch + 0.005,
                ]
            )
            low = P[P[:, 2] <= np.percentile(P[:, 2], 3)]
            A = low.mean(axis=0)
            hv = A - H
            hl = np.linalg.norm(hv)
            ah = hv / hl
            t = (P - H) @ ah
            rad = np.linalg.norm((P - H) - np.outer(t, ah), axis=1)
            nb = 24
            bins = np.linspace(0, hl, nb + 1)
            prof = np.full(nb, np.nan)
            for i in range(nb):
                m = (t >= bins[i]) & (t < bins[i + 1])
                if m.sum() > 3:
                    prof[i] = np.mean(rad[m])
            okb = ~np.isnan(prof)
            prof = np.interp(np.arange(nb), np.where(okb)[0], prof[okb])
            bc = 0.5 * (bins[:-1] + bins[1:])
            klo = bc[(bc > 0.35 * hl) & (bc < 0.65 * hl)]
            knee_t = klo[np.argmin(prof[(bc > 0.35 * hl) & (bc < 0.65 * hl)])]
            K = P[np.abs(t - knee_t) < 0.04 * hl].mean(axis=0)
            lm[f"leg{sname}"] = {
                "H": H,
                "K": K,
                "A": A,
                "span": float(hl),
                "verts": np.where(lg)[0],
            }
    lab["lm"] = lm
    return lab


def seg_params(pos: np.ndarray, A: np.ndarray, B: np.ndarray, ref: np.ndarray):
    """Return ``(t, phi, radial_dir, axis_dir, seg_len, radial_len)`` of
    vertices relative to segment ``A -> B``."""
    ab = B - A
    L = np.linalg.norm(ab)
    ah = ab / L
    t = ((pos - A) @ ah) / L
    rv = (pos - A) - np.outer((pos - A) @ ah, ah)
    rl = np.linalg.norm(rv, axis=1)
    e1 = ref - (ref @ ah) * ah
    e1 = e1 / np.linalg.norm(e1)
    e2 = np.cross(ah, e1)
    phi = np.arctan2(rv @ e2, rv @ e1)
    rdir = np.where(
        rl[:, None] > 1e-9,
        rv / np.maximum(rl, 1e-9)[:, None],
        e1[None, :],
    )
    return t, phi, rdir, ah, L, rl


def chain_of(lab: dict, kind: str, sname: str):
    """Return ``(segments, ref_vec, landmarks)`` for ``(kind, sname)`` or ``None``."""
    lm = lab["lm"].get(f"{kind}{sname}")
    if lm is None:
        return None
    if kind == "arm":
        return [(lm["S"], lm["E"]), (lm["E"], lm["W"])], REF_ARM, lm
    return [(lm["H"], lm["K"]), (lm["K"], lm["A"])], REF_LEG, lm


def region_weights_w3(
    mh_pos_mac: np.ndarray,
    mh_lab: dict,
    h_mh: np.ndarray,
    r_mh: np.ndarray,
    w_torso_v4: np.ndarray,
    mh_tris: np.ndarray,
    *,
    body_end: int = 13380,
    edges: np.ndarray | None = None,
    verbose: bool = True,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute smoothed 3-way ``(torso, arm, leg)`` partition-of-unity weights
    ``W3`` on ``hm08`` (replaces ``w3_block.txt`` and inline copies).
    Returns ``(W3, body_edges_array)``."""
    nb = len(mh_pos_mac)
    w_neck = (
        sstep(h_mh, 1.00, 1.05)
        * (1 - sstep(h_mh, 1.07, 1.15))
        * (1 - sstep(r_mh, 0.11, 0.15))
    )
    w_t = np.maximum(w_torso_v4, w_neck)
    if edges is None:
        edges = body_edges(mh_tris, body_end=body_end)
    w_arm = np.zeros(nb)
    w_leg = np.zeros(nb)
    for kind, warr in (("arm", w_arm), ("leg", w_leg)):
        for sname in ("R", "L"):
            ch = chain_of(mh_lab, kind, sname)
            if ch is None:
                continue
            segs, _ref, lm = ch
            idx = lm["verts"]
            root = segs[0][0]
            d = np.linalg.norm(mh_pos_mac[idx] - root, axis=1)
            warr[idx] = np.maximum(warr[idx], sstep(d, 0.005, 0.055))
    W3 = np.stack([w_t, w_arm, w_leg], axis=1)
    sup = W3.sum(axis=1) > 0
    for j in range(3):
        W3[:, j] = lap_smooth(W3[:, j], sup, edges, iters=2)
    W3 = W3 / np.maximum(W3.sum(axis=1, keepdims=True), 1e-9)
    W3[~sup] = 0.0
    if verbose:
        print(
            f"region weights: torso-dominant {int((W3[:,0]>0.5).sum())}, "
            f"arm {int((W3[:,1]>0.5).sum())}, leg {int((W3[:,2]>0.5).sum())}, "
            f"uncovered body verts {int((sup[:body_end]==0).sum())}"
        )
    return W3, edges


def blend_regions(torso_f: np.ndarray, limb_f: dict, W3: np.ndarray) -> np.ndarray:
    """Blend transferred ``torso_f`` and ``limb_f`` using ``W3`` weights."""
    out = W3[:, 0:1] * torso_f
    for (kind, _sname), f in limb_f.items():
        j = 1 if kind == "arm" else 2
        out = out + W3[:, j : j + 1] * f
    return out / np.maximum(1.0, W3.sum(axis=1, keepdims=True))
