"""Pure mesh-plane slice loops, volumes, girths, and anatomical grading.

Zero file I/O, mesh loads, or console output occur at import time.
"""

from __future__ import annotations

from collections import defaultdict

import numpy as np

from .axes import torso_params


def plane_loops(
    pos: np.ndarray,
    faces: np.ndarray,
    n: np.ndarray,
    p0: np.ndarray,
    *,
    round_decimals: int = 5,
) -> list[np.ndarray]:
    """Intersect triangle mesh ``(pos, faces)`` with plane ``(p - p0) . n = 0``
    and chain crossing segments into closed point loops."""
    n = np.asarray(n, dtype=np.float64)
    n = n / np.linalg.norm(n)
    d = (pos - p0) @ n
    dv = d[faces]
    segs = []
    for e in ((0, 1), (1, 2), (2, 0)):
        a, b = dv[:, e[0]], dv[:, e[1]]
        cross = (a >= 0) != (b >= 0)
        if not cross.any():
            continue
        fa, fb = faces[cross, e[0]], faces[cross, e[1]]
        t = a[cross] / (a[cross] - b[cross])
        pts = pos[fa] + (pos[fb] - pos[fa]) * t[:, None]
        fid = np.where(cross)[0]
        segs.append((fid, pts))
    per_face: dict[int, list[np.ndarray]] = {}
    for fid, pts in segs:
        for i, f in enumerate(fid):
            per_face.setdefault(int(f), []).append(pts[i])
    raw = [np.stack(v) for v in per_face.values() if len(v) == 2]
    if not raw:
        return []
    S = np.stack([s[0] for s in raw])
    E = np.stack([s[1] for s in raw])

    def key(p):
        return (
            round(float(p[0]), round_decimals),
            round(float(p[1]), round_decimals),
            round(float(p[2]), round_decimals),
        )

    at: dict[tuple[float, float, float], list[tuple[int, int]]] = defaultdict(list)
    for i in range(len(raw)):
        at[key(S[i])].append((i, 0))
        at[key(E[i])].append((i, 1))
    used = np.zeros(len(raw), bool)
    loops = []
    for i0 in range(len(raw)):
        if used[i0]:
            continue
        used[i0] = True
        loop = [S[i0], E[i0]]
        cur = key(E[i0])
        for _ in range(len(raw) + 2):
            nxt = None
            for j, end in at.get(cur, []):
                if not used[j]:
                    nxt = (j, end)
                    break
            if nxt is None:
                break
            j, end = nxt
            used[j] = True
            p = E[j] if end == 0 else S[j]
            loop.append(p)
            cur = key(p)
            if cur == key(loop[0]):
                break
        if len(loop) >= 4:
            loops.append(
                np.array(loop[:-1])
                if np.allclose(loop[-1], loop[0])
                else np.array(loop)
            )
    return loops


def loop_perim(lp: np.ndarray) -> float:
    """Closed polyline perimeter."""
    q = np.roll(lp, -1, axis=0)
    return float(np.linalg.norm(q - lp, axis=1).sum())


def best_loop(
    pos: np.ndarray,
    faces: np.ndarray,
    n: np.ndarray,
    p0: np.ndarray,
    near_axis: bool = True,
    max_extent: float | None = None,
    *,
    round_decimals: int = 5,
) -> np.ndarray | None:
    """Largest-perimeter loop passing ``near_axis`` and ``max_extent`` filters."""
    loops = plane_loops(pos, faces, n, p0, round_decimals=round_decimals)
    if not loops:
        return None

    def ok(lp):
        c = lp.mean(axis=0)
        if near_axis and abs(c[0]) > 0.09:
            return False
        if max_extent and (lp[:, 0].max() - lp[:, 0].min()) > max_extent:
            return False
        return True

    cand = [lp for lp in loops if ok(lp)]
    if not cand:
        cand = loops
    return max(cand, key=loop_perim)


def mesh_volume(pos: np.ndarray, faces: np.ndarray) -> float:
    """Unsigned enclosed mesh volume in cubic metres."""
    v0, v1, v2 = pos[faces[:, 0]], pos[faces[:, 1]], pos[faces[:, 2]]
    return abs(float(np.einsum("ij,ij->i", v0, np.cross(v1, v2)).sum() / 6.0))


def girth_ellipse(width, depth):
    """Ramanujan ellipse circumference approximation from full ``width`` and ``depth``."""
    a, b = width / 2, depth / 2
    return np.pi * (3 * (a + b) - np.sqrt((3 * a + b) * (a + 3 * b)))


def side_mass(D: np.ndarray, h_mh: np.ndarray, th_mh: np.ndarray) -> dict:
    """Front / flank / back mean radial mass profile on chest and belly bands."""
    er = np.stack([np.sin(th_mh), np.cos(th_mh)], axis=1)
    dr = np.abs(D[:, 0] * er[:, 0] + D[:, 1] * er[:, 1])
    out = {}
    for band_name, (h0, h1) in (("chest", (0.78, 0.92)), ("belly", (0.35, 0.55))):
        hb = (h_mh >= h0) & (h_mh < h1)
        fr = hb & (np.abs(th_mh) < 0.5)
        fl = hb & (np.abs(th_mh) > 0.9) & (np.abs(th_mh) < 2.2)
        bk = hb & (np.abs(th_mh) > 2.7)
        f_, l_, b_ = (
            float(dr[m].mean() * 100) if m.sum() else 0.0 for m in (fr, fl, bk)
        )
        out[band_name] = {
            "front_cm": f_,
            "flank_cm": l_,
            "back_cm": b_,
            "flank_front": (l_ / f_) if f_ > 0 else 0.0,
        }
    return out


def girths(
    pos: np.ndarray,
    mh_crotch: float,
    mh_neck: float,
    h_star: float,
    *,
    include_hip: bool = False,
) -> dict[str, float]:
    """Ellipse-approx chest, navel-waist, narrowest-waist (and optional hip) girths."""
    h, _th, _r, ax, _, _, _ = torso_params(pos, mh_crotch, mh_neck, "def")
    edges = np.arange(0.30, 1.001, 0.02)
    out: dict = {}
    for a, b in zip(edges[:-1], edges[1:]):
        m = (h >= a) & (h < b)
        if m.sum() > 20:
            px = pos[m, 0] - ax[m, 0]
            py = pos[m, 1] - ax[m, 1]
            rr = np.hypot(px, py)
            for gate, key in ((0.30, "g30"), (0.215, "g215")):
                mm = rr < gate
                if mm.sum() > 12:
                    A = (px[mm].max() - px[mm].min()) / 2
                    Bv = (py[mm].max() - py[mm].min()) / 2
                    g = np.pi * (
                        3 * (A + Bv) - np.sqrt((3 * A + Bv) * (A + 3 * Bv))
                    )
                    if key == "g30":
                        out.setdefault("bands", []).append((0.5 * (a + b), g, None))
                    elif out.get("bands"):
                        out["bands"][-1] = (
                            out["bands"][-1][0],
                            out["bands"][-1][1],
                            g,
                        )
    bands = out.get("bands", [])
    chest = np.mean([g for hh, g, _ in bands if g and 0.80 <= hh <= 0.90])
    nav = [g2 for hh, _, g2 in bands if g2 and h_star - 0.02 <= hh <= h_star + 0.04]
    waist_navel = float(np.mean(nav)) if nav else float("nan")
    waist_band = [g2 for hh, _, g2 in bands if g2 and 0.45 <= hh <= 0.62]
    waist_min = float(np.min(waist_band)) if waist_band else waist_navel
    res = {
        "chest": float(chest),
        "waist_navel": waist_navel,
        "waist_min": waist_min,
    }
    if include_hip:
        hip_bands = [g2 for hh, _, g2 in bands if g2 and -0.02 <= hh <= 0.14]
        res["hip"] = float(np.max(hip_bands)) if hip_bands else float("nan")
    return res


def slice_ratio(
    pos: np.ndarray,
    faces: np.ndarray,
    mh_crotch: float,
    L_mh: float,
    z_waist: float,
) -> float:
    """Chest / waist slice-loop girth ratio (M4)."""
    Z = np.array([0.0, 0.0, 1.0])
    cl = best_loop(pos, faces, Z, np.array([0.0, 0.0, mh_crotch + 0.85 * L_mh]))
    wl = best_loop(pos, faces, Z, np.array([0.0, 0.0, float(z_waist)]))
    return loop_perim(cl) / loop_perim(wl)


def band(v: float, lo: float, hi: float) -> str:
    """Return ``'PASS'`` when ``lo <= v <= hi`` else ``'miss'``."""
    return "PASS" if lo <= v <= hi else "miss"


def grade(
    pos: np.ndarray,
    lmts: dict,
    *,
    faces_b: np.ndarray,
    mh_crotch: float,
    mh_neck: float,
    mh_pos_mac: np.ndarray,
    navel_mh: int,
    h_mh: np.ndarray | None = None,
    body_end: int = 13380,
) -> dict:
    """Full BARA_LESSONS section-2 anatomical scorecard from true mesh-plane
    slice loops, with explicit mesh context parameters (zero global state)."""
    L_mh = mh_neck - mh_crotch
    Z = np.array([0.0, 0.0, 1.0])
    body = pos[:body_end]
    crown = float(body[:, 2].max())
    sole = float(body[:, 2].min())
    height = crown - sole

    neck_lp = best_loop(pos, faces_b, Z, np.array([0.0, 0.0, mh_neck + 0.045]))
    neck_g = loop_perim(neck_lp)
    neck_w = float(neck_lp[:, 0].max() - neck_lp[:, 0].min())

    widths = []
    for zz in np.arange(mh_neck + 0.06, crown - 0.002, 0.004):
        lp = best_loop(pos, faces_b, Z, np.array([0.0, 0.0, zz]), max_extent=0.30)
        if lp is not None and loop_perim(lp) > 0.04:
            widths.append((zz, float(lp[:, 0].max() - lp[:, 0].min())))
    head_w = max(w for _, w in widths)
    jaw_win = [(zz, w) for zz, w in widths if zz < mh_neck + 0.17]
    jaw_z = min(jaw_win, key=lambda t: t[1])[0]
    chin_z = jaw_z - 0.02
    head_h = crown - chin_z

    z_chest = mh_crotch + 0.85 * L_mh
    chest_lp = best_loop(pos, faces_b, Z, np.array([0.0, 0.0, z_chest]))
    chest_g = loop_perim(chest_lp)
    chest_w = float(chest_lp[:, 0].max() - chest_lp[:, 0].min())
    chest_d = float(chest_lp[:, 1].max() - chest_lp[:, 1].min())

    z_waist = float(mh_pos_mac[navel_mh, 2])
    waist_lp = best_loop(pos, faces_b, Z, np.array([0.0, 0.0, z_waist]))
    waist_g = loop_perim(waist_lp)
    waist_w = float(waist_lp[:, 0].max() - waist_lp[:, 0].min())
    waist_d = float(waist_lp[:, 1].max() - waist_lp[:, 1].min())

    sh_band = (body[:, 2] > mh_neck - 0.17) & (body[:, 2] < mh_neck - 0.02)
    delt_span = float(body[sh_band, 0].max() - body[sh_band, 0].min())

    sil = body[(h_mh[:body_end] <= 1.16)] if h_mh is not None else body
    xs = np.arange(0.0, 0.30, 0.004)
    ztop = np.full(len(xs), np.nan)
    for i, x0 in enumerate(xs):
        m = (sil[:, 0] >= x0) & (sil[:, 0] < x0 + 0.004)
        if m.sum() > 2:
            ztop[i] = sil[m, 2].max()
    ok = ~np.isnan(ztop)
    ztop = np.interp(xs, xs[ok], ztop[ok])
    fx = (xs > 0.10) & (xs < delt_span / 2 - 0.020)
    if fx.sum() > 4:
        fit = np.polyfit(xs[fx], ztop[fx], 1)
        trap_angle = float(np.degrees(np.arctan(abs(fit[0]))))
    else:
        trap_angle = float("nan")

    trap_at_neck = float(np.interp(head_w / 2 + 0.03, xs, ztop))
    visible_neck = chin_z - trap_at_neck

    ua_gs, fa_gs = [], []
    for sname in ("R", "L"):
        lm = lmts["lm"].get(f"arm{sname}")
        if not lm:
            continue
        S, E, W = lm["S"], lm["E"], lm["W"]
        for A, Bv, ts, acc in (
            (S, E, (0.20, 0.35, 0.50, 0.65), ua_gs),
            (E, W, (0.15, 0.30, 0.45, 0.60), fa_gs),
        ):
            n_seg = (Bv - A) / np.linalg.norm(Bv - A)
            best = 0.0
            for t in ts:
                P0 = A + t * (Bv - A)
                loops = [
                    lp for lp in plane_loops(pos, faces_b, n_seg, P0) if loop_perim(lp) > 0.05
                ]
                if loops:
                    lp = min(loops, key=lambda l: np.linalg.norm(l.mean(axis=0) - P0))
                    best = max(best, loop_perim(lp))
            if best > 0:
                acc.append(best)
    ua_g = float(np.mean(ua_gs))
    fa_g = float(np.mean(fa_gs))

    loops = plane_loops(pos, faces_b, Z, np.array([0.0, 0.0, mh_crotch - 0.10]))
    th = [
        loop_perim(lp)
        for lp in loops
        if abs(lp.mean(axis=0)[0]) > 0.03 and loop_perim(lp) > 0.15
    ]
    thigh_g = float(np.mean(th)) if th else float("nan")

    knee_z = min(
        lm["K"][2] for lm in (lmts["lm"].get("legR"), lmts["lm"].get("legL")) if lm
    )
    calf: dict[str, float] = {}
    for zz in np.arange(knee_z - 0.17, knee_z - 0.04, 0.008):
        for lp in plane_loops(pos, faces_b, Z, np.array([0.0, 0.0, zz])):
            cx = lp.mean(axis=0)[0]
            if abs(cx) > 0.03 and loop_perim(lp) > 0.08:
                s = "R" if cx > 0 else "L"
                calf[s] = max(calf.get(s, 0.0), loop_perim(lp))
    calf_g = float(np.mean(list(calf.values()))) if calf else float("nan")

    return {
        "height_m": height,
        "volume_L": mesh_volume(pos, faces_b) * 1000.0,
        "neck_g": neck_g,
        "neck_w": neck_w,
        "head_w": head_w,
        "head_h": head_h,
        "chin_z": chin_z,
        "chest_g": chest_g,
        "chest_w": chest_w,
        "waist_w": waist_w,
        "waist_g": waist_g,
        "chest_d": chest_d,
        "waist_d": waist_d,
        "delt_span": delt_span,
        "trap_angle": trap_angle,
        "visible_neck": visible_neck,
        "ua_g": ua_g,
        "fa_g": fa_g,
        "thigh_g": thigh_g,
        "calf_g": calf_g,
        "M1_neckW_headW": neck_w / head_w,
        "M2_neck_arm": neck_g / ua_g,
        "M2_neck_calf": neck_g / calf_g,
        "M2_arm_calf": ua_g / calf_g,
        "M3_fa_arm": fa_g / ua_g,
        "M4_chest_waist": chest_g / waist_g,
        "M5_depth_ratio": chest_d / waist_d,
        "M6_trap_deg": trap_angle,
        "M7_vis_neck_ratio": visible_neck / head_h,
        "M8_span_headW": delt_span / head_w,
        "M11_thigh_waist": thigh_g / waist_g,
        "M12_heads_tall": height / head_h,
    }
