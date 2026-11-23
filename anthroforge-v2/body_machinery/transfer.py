"""Pure Gaussian kernel-transfer and parametric surface correspondence helpers.

Zero file I/O, mesh loads, or console output occur at import time.
"""

from __future__ import annotations

import numpy as np

from .axes import limb_params, sstep, torso_params
from .labels import chain_of, seg_params


def pair_field(
    sa: np.ndarray,
    sb: np.ndarray,
    v1: np.ndarray,
    v2: np.ndarray,
    qa: np.ndarray,
    qb: np.ndarray,
    sig_a: float,
    sig_b: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Chunked 2D Gaussian Nadaraya-Watson kernel evaluation."""
    out1 = np.zeros(len(qa))
    out2 = np.zeros(len(qa))
    for s0 in range(0, len(qa), 800):
        q = slice(s0, s0 + 800)
        da = (sa[:, None] - qa[q][None, :]) / sig_a
        db = (sb[:, None] - qb[q][None, :]) / sig_b
        w = np.exp(-0.5 * (da**2 + db**2))
        ws = w.sum(axis=0) + 1e-12
        out1[q] = (w * v1[:, None]).sum(axis=0) / ws
        out2[q] = (w * v2[:, None]).sum(axis=0) / ws
    return out1, out2


def pair_cv(
    sa: np.ndarray,
    sb: np.ndarray,
    v1: np.ndarray,
    v2: np.ndarray,
    sig_a: float,
    sig_b: float,
    *,
    seed: int = 20261112,
) -> dict | None:
    """5-fold cross-validation over informative samples (``hypot > 0.5 mm``)."""
    inf = np.where(np.hypot(v1, v2) > 0.0005)[0]
    if len(inf) < 40:
        return None
    rng = np.random.default_rng(seed)
    perm = rng.permutation(inf)
    folds = np.array_split(perm, 5)
    errs = np.zeros(len(inf))
    for f in folds:
        tr = np.setdiff1d(perm, f)
        pr, pz = pair_field(
            sa[tr], sb[tr], v1[tr], v2[tr], sa[f], sb[f], sig_a, sig_b
        )
        errs[np.searchsorted(inf, f)] = np.hypot(pr - v1[f], pz - v2[f])
    e = errs * 100.0
    return {
        "n": int(len(e)),
        "median_cm": float(np.median(e)),
        "p95_cm": float(np.percentile(e, 95)),
    }


def torso_field(
    delta: np.ndarray,
    tag: str,
    *,
    hi_lab: dict,
    h_hi: np.ndarray,
    th_hi: np.ndarray,
    r_hi: np.ndarray,
    mh_pos_mac: np.ndarray,
    mh_crotch: float,
    mh_neck: float,
    s_hi: float,
    sig_h: float = 0.05,
    sig_a: float = 0.04,
    cv_report: dict | None = None,
) -> tuple[np.ndarray, tuple[np.ndarray, np.ndarray]]:
    """Signed-theta ``(h, arc)`` kernel transfer from HIMBO torso to ``hm08``."""
    gate_s = hi_lab["torso"] & (
        ((h_hi > -0.02) & (h_hi < 1.06) & (r_hi < 0.30))
        | ((h_hi >= 1.06) & (h_hi < 1.18) & (r_hi < 0.13))
    )
    hh, tt, rr, dd = h_hi[gate_s], th_hi[gate_s], r_hi[gate_s], delta[gate_s]
    er = np.stack([np.sin(tt), np.cos(tt)], axis=1)
    dr_s = dd[:, 0] * er[:, 0] + dd[:, 1] * er[:, 1]
    dz_s = dd[:, 2]
    rb = np.linspace(-0.02, 1.18, 25)
    rmean = np.array(
        [
            rr[(hh >= rb[i]) & (hh < rb[i + 1])].mean()
            if ((hh >= rb[i]) & (hh < rb[i + 1])).sum() > 5
            else 0.17
            for i in range(24)
        ]
    )
    rctr = 0.5 * (rb[:-1] + rb[1:])

    def arc(theta, hv):
        return theta * np.interp(hv, rctr, rmean)

    arc_s = arc(tt, hh)
    h_mh, th_mh, r_mh, _ax_mh, _, _, _ = torso_params(
        mh_pos_mac, mh_crotch, mh_neck, "hm08"
    )
    arc_q = arc(th_mh, h_mh)
    dr, dz = pair_field(hh, arc_s, dr_s, dz_s, h_mh, arc_q, sig_h, sig_a)
    dr, dz = dr * s_hi, dz * s_hi
    cv = pair_cv(hh, arc_s, dr_s, dz_s, sig_h, sig_a)
    if cv and cv_report is not None:
        cv_report[f"torso/{tag}"] = cv
    out = np.zeros((len(mh_pos_mac), 3))
    out[:, 0] = dr * np.sin(th_mh)
    out[:, 1] = dr * np.cos(th_mh)
    out[:, 2] = dz
    return out, (h_mh, r_mh)


def limb_fields(
    delta: np.ndarray,
    tag: str,
    *,
    hi_pos_m: np.ndarray,
    mh_pos_mac: np.ndarray,
    hi_lab: dict,
    mh_lab: dict,
    sig_u: float = 0.045,
    sig_arc: float = 0.04,
    cv_report: dict | None = None,
) -> dict[tuple[str, str], np.ndarray]:
    """Per-(chain, side, segment) ``(t, phi)`` kernel transfer onto ``hm08``."""
    nb = len(mh_pos_mac)
    out: dict[tuple[str, str], np.ndarray] = {}
    for kind in ("arm", "leg"):
        for sname in ("R", "L"):
            ch_s = chain_of(hi_lab, kind, sname)
            ch_t = chain_of(mh_lab, kind, sname)
            if ch_s is None or ch_t is None:
                continue
            segs_s, ref, lm_s = ch_s
            segs_t, _, lm_t = ch_t
            field = np.zeros((nb, 3))
            for si, ((As, Bs), (At, Bt)) in enumerate(zip(segs_s, segs_t)):
                Pv = lm_s["verts"]
                _ts, _ps, _, _, Ls, _ = seg_params(hi_pos_m, As, Bs, ref)
                tt = [seg_params(hi_pos_m, A2, B2, ref)[0][Pv] for (A2, B2) in segs_s]
                tt_arr = np.stack(tt, axis=1)
                cost = np.where(
                    (tt_arr >= -0.15) & (tt_arr <= 1.15), np.abs(tt_arr - 0.5), 1e3
                )
                assign = np.argmin(cost, axis=1) == si
                idx = Pv[assign]
                if len(idx) < 25:
                    continue
                t_s, p_s, rd_s, ah_s, _, rl_s = seg_params(hi_pos_m, As, Bs, ref)
                t_s, p_s = t_s[idx], p_s[idx]
                d = delta[idx]
                dr_s = (d * rd_s[idx]).sum(axis=1)
                ds_s = d @ ah_s
                ok = (t_s > -0.12) & (t_s < 1.18)
                idx, t_s, p_s, dr_s, ds_s = (
                    idx[ok],
                    t_s[ok],
                    p_s[ok],
                    dr_s[ok],
                    ds_s[ok],
                )
                rl_s_all = rl_s[idx]
                tb = np.linspace(-0.1, 1.15, 13)
                rmean = np.array(
                    [
                        rl_s_all[(t_s >= tb[i]) & (t_s < tb[i + 1])].mean()
                        if ((t_s >= tb[i]) & (t_s < tb[i + 1])).sum() > 4
                        else max(rl_s_all.mean(), 0.02)
                        for i in range(12)
                    ]
                )
                tctr = 0.5 * (tb[:-1] + tb[1:])
                arc_s = p_s * np.interp(t_s, tctr, rmean)

                Pv_t = lm_t["verts"]
                tt_t = [
                    seg_params(mh_pos_mac, A2, B2, ref)[0][Pv_t]
                    for (A2, B2) in segs_t
                ]
                tt_t_arr = np.stack(tt_t, axis=1)
                cost_t = np.where(
                    (tt_t_arr >= -0.15) & (tt_t_arr <= 1.15),
                    np.abs(tt_t_arr - 0.5),
                    1e3,
                )
                idx_t = Pv_t[np.argmin(cost_t, axis=1) == si]
                t_t, p_t, rd_t, ah_t, Lt, rl_t = seg_params(mh_pos_mac, At, Bt, ref)
                t_t, p_t, rd_t, rl_t = (
                    t_t[idx_t],
                    p_t[idx_t],
                    rd_t[idx_t],
                    rl_t[idx_t],
                )
                s_seg = Lt / Ls
                s_rad = float(np.mean(rl_t)) / max(float(np.mean(rl_s_all)), 1e-4)
                arc_t = p_t * np.interp(t_t, tctr, rmean)
                dr, ds = pair_field(
                    t_s * Ls, arc_s, dr_s, ds_s, t_t * Lt, arc_t, sig_u, sig_arc
                )
                dr, ds = dr * s_rad, ds * s_seg
                cv = pair_cv(t_s * Ls, arc_s, dr_s, ds_s, sig_u, sig_arc)
                if cv and cv_report is not None:
                    cv_report[f"{kind}{sname}/seg{si}/{tag}"] = cv
                fade = 1.0 - sstep(t_t, 1.00, 1.12)
                field[idx_t] += rd_t * (dr * fade)[:, None] + (
                    ah_t[None, :] * (ds * fade)[:, None]
                )
            out[(kind, sname)] = field
    return out


def limb_field_sphi(
    pos: np.ndarray,
    delta: np.ndarray,
    limbs: dict,
    kind: str,
    label: str,
    *,
    gate_map: dict[str, float] | None = None,
    verbose: bool = True,
):
    """Mirrored ``(s, phi) -> (dr, da)`` kernel field for ``arm`` or ``leg``
    (first-proof v5 convention)."""
    if gate_map is None:
        gate_map = {"arm": 0.135, "leg": 0.175}
    S_, P_, R_, A_ = [], [], [], []
    for name in (f"{kind}_R", f"{kind}_L"):
        lb = limbs[name]
        s, dist, phi, er, adir = limb_params(pos, lb)
        samp = (dist < gate_map[kind]) & (s > -0.04) & (s < 1.05)
        S_.append(s[samp])
        P_.append(phi[samp])
        R_.append(np.einsum("ij,ij->i", delta, er)[samp])
        A_.append(np.einsum("ij,ij->i", delta, adir)[samp])
    S = np.concatenate(S_)
    PH = np.concatenate(P_)
    DR = np.concatenate(R_)
    DA = np.concatenate(A_)
    R_CHAR = 0.055 if kind == "arm" else 0.085
    SIG_S, SIG_A = 0.06, 0.035

    def ev(sq, pq, idx=None):
        if idx is None:
            idx = np.arange(len(S))
        o_r = np.zeros(len(sq))
        o_a = np.zeros(len(sq))
        for s0 in range(0, len(sq), 800):
            q = slice(s0, s0 + 800)
            ds = (S[idx][:, None] - sq[q][None, :]) / SIG_S
            dp = PH[idx][:, None] - pq[q][None, :]
            dp = (dp + np.pi) % (2 * np.pi) - np.pi
            da_ = dp * R_CHAR / SIG_A
            w = np.exp(-0.5 * (ds**2 + da_**2))
            ws = w.sum(axis=0) + 1e-12
            o_r[q] = (w * DR[idx][:, None]).sum(axis=0) / ws
            o_a[q] = (w * DA[idx][:, None]).sum(axis=0) / ws
        return o_r, o_a

    rng = np.random.default_rng(20261112)
    inf = np.where(np.hypot(DR, DA) > 0.0005)[0]
    perm = rng.permutation(inf)
    folds = np.array_split(perm, 5)
    errs = np.zeros(len(inf))
    for f in folds:
        tr = np.setdiff1d(perm, f)
        pos_in_inf = np.searchsorted(inf, f)
        pr, pa = ev(S[f], PH[f], idx=tr)
        errs[pos_in_inf] = np.hypot(pr - DR[f], pa - DA[f])
    cv = {
        k: float(v * 100)
        for k, v in zip(["p50", "p95", "max"], np.percentile(errs, [50, 95, 100]))
    }
    info = {
        "label": label,
        "kind": kind,
        "samples": int(len(S)),
        "informative": int(len(inf)),
        "cv_cm": cv,
    }
    if verbose:
        print(
            f"limb field {label}: {len(S)} samples ({len(inf)} informative), "
            f"CV p50 {cv['p50']:.3f} / p95 {cv['p95']:.3f} / max {cv['max']:.3f} cm"
        )
    return ev, info


def tri_list(faces) -> np.ndarray:
    """Fan-triangulate 3- or 4-vertex polygon index lists into ``(M, 3)``."""
    tris = []
    for f in faces:
        if len(f) == 4:
            tris.append(f[:3])
            tris.append([f[0], f[2], f[3]])
        elif len(f) == 3:
            tris.append(f)
    return np.array(tris)


def tri_closest(
    P: np.ndarray, A: np.ndarray, B: np.ndarray, C: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Vectorised exact closest points on triangles ``(A, B, C)`` (Ericson)."""
    ab, ac, ap = B - A, C - A, P - A
    d1 = np.einsum("ij,ij->i", ab, ap)
    d2 = np.einsum("ij,ij->i", ac, ap)
    d3 = np.einsum("ij,ij->i", ab, ab)
    d4 = np.einsum("ij,ij->i", ab, ac)
    d5 = np.einsum("ij,ij->i", ac, ac)
    den = np.maximum(d3 * d5 - d4 * d4, 1e-14)
    vc = (d3 * d2 - d4 * d1) / den
    vb = (d5 * d1 - d4 * d2) / den
    inside = (vb >= 0) & (vc >= 0) & (vb + vc <= 1)
    plane = A + vb[:, None] * ab + vc[:, None] * ac
    best = plane.copy()
    bestd = np.where(inside, np.linalg.norm(P - plane, axis=1), np.inf)
    for E0, E1 in ((A, B), (B, C), (C, A)):
        seg = E1 - E0
        t = np.einsum("ij,ij->i", P - E0, seg) / np.maximum(
            np.einsum("ij,ij->i", seg, seg), 1e-14
        )
        q = E0 + np.clip(t, 0, 1)[:, None] * seg
        dd = np.linalg.norm(P - q, axis=1)
        m = dd < bestd
        best[m] = q[m]
        bestd[m] = dd[m]
    return best, bestd


class ParamSurface:
    """KD-tree accelerated exact closest-triangle query in parameter space."""

    def __init__(self, P: np.ndarray, F: np.ndarray):
        self.P, self.F = P, F
        try:
            from scipy.spatial import cKDTree

            self.tree = cKDTree(P)
        except ImportError:
            self.tree = None
        vf: dict[int, list[int]] = {}
        for fi, f in enumerate(F):
            for v in f:
                vf.setdefault(int(v), []).append(fi)
        self.vf = vf

    def _knn_indices(self, Q: np.ndarray, k: int) -> np.ndarray:
        k_eff = min(k, len(self.P))
        if self.tree is not None:
            _, nn = self.tree.query(Q, k=k_eff)
            return np.atleast_2d(nn)
        # Pure-numpy fallback when scipy is absent (CI / Blender bundled Python).
        out = np.empty((len(Q), k_eff), dtype=np.int64)
        for s0 in range(0, len(Q), 256):
            q = Q[s0 : s0 + 256]
            d2 = np.sum((q[:, None, :] - self.P[None, :, :]) ** 2, axis=2)
            idx = np.argpartition(d2, k_eff - 1, axis=1)[:, :k_eff]
            row = np.arange(len(q))[:, None]
            order = np.argsort(d2[row, idx], axis=1)
            out[s0 : s0 + 256] = idx[row, order]
        return out

    def closest(self, Q: np.ndarray, k: int = 12) -> tuple[np.ndarray, np.ndarray]:
        nn = self._knn_indices(Q, k)
        out_c = np.empty_like(Q)
        out_d = np.empty(len(Q))
        for i, row in enumerate(nn):
            cand = np.unique(
                np.concatenate([self.vf[int(v)] for v in row if int(v) in self.vf])
            )
            A = self.P[self.F[cand, 0]]
            B = self.P[self.F[cand, 1]]
            C = self.P[self.F[cand, 2]]
            cp, dd = tri_closest(np.repeat(Q[i : i + 1], len(cand), axis=0), A, B, C)
            j = int(np.argmin(dd))
            out_c[i] = cp[j]
            out_d[i] = dd[j]
        return out_c, out_d
