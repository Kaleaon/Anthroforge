"""MEASUREMENT MACHINERY — extracted verbatim from
bara-proof/scripts/build_bara.py (AST source segments, Nov 12, 2026) so
the Sen build is graded with the identical rulers as BARA_PROOF.md.
Globals (FACES_B, BODY_END, mh_neck, mh_crotch, L_mh, mh_pos_mac,
navel_mh, h_mh) are set by the importing script before use.
"""
import numpy as np

FACES_B = None
BODY_END = 13380
mh_neck = mh_crotch = L_mh = None
mh_pos_mac = None
navel_mh = None
h_mh = None

def compute_axis(pos, gate=None):
    """v4's compute_axis verbatim (incl. the 5-tap axis smoothing)."""
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
            axis[i] = [0.5 * (pos[m, 0].min() + pos[m, 0].max()),
                       0.5 * (pos[m, 1].min() + pos[m, 1].max())]
    ok = ~np.isnan(axis[:, 0])
    for c in range(2):
        axis[:, c] = np.interp(ctr, ctr[ok], axis[ok, c])
    k = np.ones(5) / 5
    for c in range(2):
        axis[:, c] = np.convolve(np.pad(axis[:, c], 2, mode="edge"),
                                 k, "valid")
    return ctr, axis

def axis_at(ctr, axis, hgt):
    return np.stack([np.interp(hgt, ctr, axis[:, 0]),
                     np.interp(hgt, ctr, axis[:, 1])], axis=1)

def torso_params(pos, crotch=None, neck=None, label="mesh"):
    """(h, theta, r, axis_xy, crotch, neck, L) in v4's exact convention:
    theta = atan2(rel_x, rel_y) (0 = front), h = (z-crotch)/(neck-crotch)
    with crotch/neck detected by v4's crotch_of/neck_base when not
    supplied."""
    gate = np.ones(len(pos), bool)
    ctr, axis = compute_axis(pos, gate)
    if crotch is None:
        crotch = crotch_of(pos, gate, 0.030, 0.060)
    if neck is None:
        neck = neck_base(pos, ctr, axis, crotch, label)
    ax = axis_at(ctr, axis, pos[:, 2])
    rel = pos[:, :2] - ax
    r = np.linalg.norm(rel, axis=1)
    theta = np.arctan2(rel[:, 0], rel[:, 1])
    h = (pos[:, 2] - crotch) / (neck - crotch)
    return h, theta, r, ax, crotch, neck, neck - crotch

def label_mesh(pos, crotch, neck, body_mask=None):
    """Geometric region labels + limb landmarks. Works on any of our
    bases (metres, z-up, A-pose ~45 deg both). Arms hang lateral of the
    torso radius profile; legs split by side below the crotch.
    body_mask: verts eligible for limb labels/landmarks (hm08 helpers
    excluded); defaults to all."""
    if body_mask is None:
        body_mask = np.ones(len(pos), bool)
    z = pos[:, 2]
    ctr, axis = compute_axis(pos, np.ones(len(pos), bool))
    ax = np.stack([np.interp(z, ctr, axis[:, 0]),
                   np.interp(z, ctr, axis[:, 1])], axis=1)
    rel = pos[:, :2] - ax
    r = np.hypot(rel[:, 0], rel[:, 1])
    # torso radius profile (92nd pct per 1 cm band)
    edges = np.arange(z.min() - 0.005, z.max() + 0.011, 0.01)
    prof = np.full(len(edges) - 1, np.nan)
    for i, (a, b) in enumerate(zip(edges[:-1], edges[1:])):
        m = (z >= a) & (z < b) & (r < 0.23)   # r gate excludes arms/hands
        if m.sum() > 8:
            prof[i] = np.percentile(r[m], 92)
    zc = 0.5 * (edges[:-1] + edges[1:])
    ok = ~np.isnan(prof)
    r92 = np.interp(z, zc[ok], prof[ok])
    side = np.sign(rel[:, 0])
    arm = (r > r92 + 0.010) & (z > crotch - 0.02) & (z < neck + 0.05) \
        & (side != 0) & (np.abs(rel[:, 0]) > 0.7 * r) & body_mask
    leg = (z < crotch - 0.008) & ~arm & body_mask
    torso = ~arm & ~leg
    lab = {"arm": arm, "leg": leg, "torso": torso, "side": side,
           "ax": ax, "r": r, "rel": rel}
    # ---- limb landmarks per side
    lm = {}
    for sgn, sname in ((1.0, "R"), (-1.0, "L")):
        am = arm & (side == sgn)
        if am.sum() > 60:
            P = pos[am]
            c = P.mean(axis=0)
            _, _, vt = np.linalg.svd(P - c, full_matrices=False)
            a = vt[0]
            s = (P - c) @ a
            # orient: the hand end sits farther from the body axis
            for sgn_a in (1.0,):
                e1 = P[s > np.percentile(s, 92)]
                e0 = P[s < np.percentile(s, 8)]
                d1 = np.mean(np.abs(e1[:, 0] - np.interp(
                    e1[:, 2], ctr, axis[:, 0])))
                d0 = np.mean(np.abs(e0[:, 0] - np.interp(
                    e0[:, 2], ctr, axis[:, 0])))
                if d0 > d1:
                    a, s = -a, -s
            u = s - s.min()
            span = u.max()
            # radius profile along the PCA line
            nb = 28
            bins = np.linspace(0, span, nb + 1)
            rad = np.full(nb, np.nan)
            for i in range(nb):
                m = (u >= bins[i]) & (u < bins[i + 1])
                if m.sum() > 3:
                    rad[i] = np.mean(np.linalg.norm(
                        (P[m] - c) - np.outer(s[m], a), axis=1))
            okb = ~np.isnan(rad)
            rad = np.interp(np.arange(nb), np.where(okb)[0], rad[okb])
            bc = 0.5 * (bins[:-1] + bins[1:])
            # elbow = FIRST local minimum of the smoothed radius
            # profile (scanning from the shoulder); wrist = thinnest
            # local minimum after it. A plain argmin over a wide
            # window picks the WRIST as the "elbow" (it is thinner)
            # and a finger web as the "wrist" -- caught in QA when
            # the forearm station read 13 cm on the base mesh.
            sm_r = np.convolve(rad, np.ones(3) / 3, mode="same")
            loc_min = [i for i in range(1, nb - 1)
                       if sm_r[i] <= sm_r[i - 1] and sm_r[i] <= sm_r[i + 1]
                       and bc[i] > 0.20 * span]
            if loc_min:
                ei = loc_min[0]
                elb_u = bc[ei]
                cand = [i for i in loc_min
                        if bc[i] > elb_u + 0.18 * span
                        and bc[i] < 0.96 * span]
                wri_u = bc[min(cand, key=lambda i: sm_r[i])] \
                    if cand else bc[min(loc_min[-1], nb - 1)]
            else:
                elo = bc[(bc > 0.32 * span) & (bc < 0.68 * span)]
                elb_u = elo[np.argmin(rad[(bc > 0.32 * span)
                                          & (bc < 0.68 * span)])]
                wlo = bc[(bc > 0.74 * span) & (bc < 0.95 * span)]
                wri_u = wlo[np.argmin(rad[(bc > 0.74 * span)
                                          & (bc < 0.95 * span)])]

            def cent(uc, hw):
                m = np.abs(u - uc) < hw
                return P[m].mean(axis=0) if m.sum() > 2 else c + a * uc
            lm[f"arm{sname}"] = {
                "S": cent(0.03 * span, 0.05 * span),
                "E": cent(elb_u, 0.04 * span),
                "W": cent(wri_u, 0.035 * span),
                "span": float(span), "verts": np.where(am)[0]}
        lg = leg & (side == sgn)
        if lg.sum() > 60:
            P = pos[lg]
            top = P[P[:, 2] > crotch - 0.09]
            hip_off = np.median(np.abs(top[:, 0] - np.interp(
                top[:, 2], ctr, axis[:, 0]))) if len(top) else 0.09
            H = np.array([np.interp(crotch, ctr, axis[:, 0]) + sgn * hip_off,
                          np.interp(crotch, ctr, axis[:, 1]), crotch + 0.005])
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
            knee_t = klo[np.argmin(prof[(bc > 0.35 * hl)
                                        & (bc < 0.65 * hl)])]
            K = P[np.abs(t - knee_t) < 0.04 * hl].mean(axis=0)
            lm[f"leg{sname}"] = {"H": H, "K": K, "A": A,
                                 "span": float(hl), "verts": np.where(lg)[0]}
    lab["lm"] = lm
    return lab

def plane_loops(pos, n, p0):
    """Intersect the body mesh with a plane; chain segments into loops.
    Returns list of (M,3) point arrays (closed loops, not repeated)."""
    n = n / np.linalg.norm(n)
    d = (pos - p0) @ n
    F = FACES_B
    dv = d[F]                                    # (nf, 3)
    segs = []
    for e in ((0, 1), (1, 2), (2, 0)):
        a, b = dv[:, e[0]], dv[:, e[1]]
        cross = (a >= 0) != (b >= 0)
        if not cross.any():
            continue
        fa, fb = F[cross, e[0]], F[cross, e[1]]
        t = a[cross] / (a[cross] - b[cross])
        pts = pos[fa] + (pos[fb] - pos[fa]) * t[:, None]
        fid = np.where(cross)[0]
        for k in range(2):
            pass
        segs.append((fid, pts))
    # each crossing face yields exactly 2 points -> pair them per face
    per_face = {}
    for fid, pts in segs:
        for i, f in enumerate(fid):
            per_face.setdefault(int(f), []).append(pts[i])
    raw = [np.stack(v) for v in per_face.values() if len(v) == 2]
    if not raw:
        return []
    S = np.stack([s[0] for s in raw])
    E = np.stack([s[1] for s in raw])

    def key(p):
        return (round(float(p[0]), 5), round(float(p[1]), 5),
                round(float(p[2]), 5))
    from collections import defaultdict
    at = defaultdict(list)
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
            for (j, end) in at.get(cur, []):
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
            loops.append(np.array(loop[:-1]) if
                         np.allclose(loop[-1], loop[0]) else
                         np.array(loop))
    return loops

def loop_perim(lp):
    q = np.roll(lp, -1, axis=0)
    return float(np.linalg.norm(q - lp, axis=1).sum())

def best_loop(pos, n, p0, near_axis=True, max_extent=None):
    loops = plane_loops(pos, n, p0)
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

def mesh_volume(pos):
    F = FACES_B
    v0, v1, v2 = pos[F[:, 0]], pos[F[:, 1]], pos[F[:, 2]]
    return abs(float(np.einsum("ij,ij->i", v0,
                                np.cross(v1, v2)).sum() / 6.0))

def grade(pos, lmts):
    """The BARA_LESSONS section-2 scorecard, measured. Stations are
    base-mesh anatomical heights (documented protocol); circumferences
    are true mesh-plane loop perimeters."""
    Z = np.array([0.0, 0.0, 1.0])
    body = pos[:BODY_END]
    crown = body[:, 2].max()
    sole = body[:, 2].min()
    height = crown - sole
    # neck + head
    neck_lp = best_loop(pos, Z, np.array([0, 0, mh_neck + 0.045]))
    neck_g = loop_perim(neck_lp)
    neck_w = float(neck_lp[:, 0].max() - neck_lp[:, 0].min())
    widths = []
    for zz in np.arange(mh_neck + 0.06, crown - 0.002, 0.004):
        lp = best_loop(pos, Z, np.array([0, 0, zz]), max_extent=0.30)
        if lp is not None and loop_perim(lp) > 0.04:
            widths.append((zz, float(lp[:, 0].max() - lp[:, 0].min())))
    head_w = max(w for _, w in widths)
    jaw_win = [(zz, w) for zz, w in widths if zz < mh_neck + 0.17]
    jaw_z = min(jaw_win, key=lambda t: t[1])[0]
    chin_z = jaw_z - 0.02                      # [E] protocol constant
    head_h = crown - chin_z
    # chest / waist stations
    z_chest = mh_crotch + 0.85 * L_mh
    chest_lp = best_loop(pos, Z, np.array([0, 0, z_chest]))
    chest_g = loop_perim(chest_lp)
    chest_w = float(chest_lp[:, 0].max() - chest_lp[:, 0].min())
    chest_d = float(chest_lp[:, 1].max() - chest_lp[:, 1].min())
    z_waist = float(mh_pos_mac[navel_mh, 2])
    waist_lp = best_loop(pos, Z, np.array([0, 0, z_waist]))
    waist_g = loop_perim(waist_lp)
    waist_w = float(waist_lp[:, 0].max() - waist_lp[:, 0].min())
    waist_d = float(waist_lp[:, 1].max() - waist_lp[:, 1].min())
    # deltoid span (vert extents in the shoulder band)
    band = (body[:, 2] > mh_neck - 0.17) & (body[:, 2] < mh_neck - 0.02)
    delt_span = float(body[band, 0].max() - body[band, 0].min())
    # trap slope from the (x, z) silhouette, right side. Head verts
    # (base-mesh h > 1.16) are EXCLUDED: the skull's silhouette stays
    # high at small |x| and poisons both the fit and the neck-edge
    # read (first grade measured the base human as neck-buried).
    # Fit window starts lateral of the neck cylinder; the trap line
    # at the neck edge is the fit extrapolated to neck_half.
    _h = globals().get("h_mh")
    sil = body[(_h[:BODY_END] <= 1.16)] if _h is not None else body
    xs = np.arange(0.0, 0.30, 0.004)
    ztop = np.full(len(xs), np.nan)
    for i, x0 in enumerate(xs):
        m = (sil[:, 0] >= x0) & (sil[:, 0] < x0 + 0.004)
        if m.sum() > 2:
            ztop[i] = sil[m, 2].max()
    ok = ~np.isnan(ztop)
    ztop = np.interp(xs, xs[ok], ztop[ok])
    neck_half = neck_w / 2
    fx = (xs > 0.10) & (xs < delt_span / 2 - 0.020)
    if fx.sum() > 4:
        fit = np.polyfit(xs[fx], ztop[fx], 1)
        trap_angle = float(np.degrees(np.arctan(abs(fit[0]))))
    else:
        trap_angle = float("nan")
    # visible neck: DIRECT read -- silhouette height just lateral of
    # the head (head_w/2 + 0.03), no extrapolation (a steep trap fit
    # extrapolated to the neck edge overshoots past the chin even on
    # the base mesh; the eye reads the shoulder mass beside the head)
    trap_at_neck = float(np.interp(head_w / 2 + 0.03, xs, ztop))
    visible_neck = chin_z - trap_at_neck
    # limbs: largest-loop tape convention (the field data's own
    # convention -- Hall's forearm 45 cm is a max girth), stations
    # swept along each segment, nearest-centroid loop per station
    ua_gs, fa_gs = [], []
    for sname in ("R", "L"):
        lm = lmts["lm"].get(f"arm{sname}")
        if not lm:
            continue
        S, E, W = lm["S"], lm["E"], lm["W"]
        for A, Bv, ts, acc in ((S, E, (0.20, 0.35, 0.50, 0.65), ua_gs),
                               (E, W, (0.15, 0.30, 0.45, 0.60), fa_gs)):
            n = (Bv - A) / np.linalg.norm(Bv - A)
            best = 0.0
            for t in ts:
                P0 = A + t * (Bv - A)
                loops = [lp for lp in plane_loops(pos, n, P0)
                         if loop_perim(lp) > 0.05]
                if loops:
                    lp = min(loops, key=lambda l:
                             np.linalg.norm(l.mean(axis=0) - P0))
                    best = max(best, loop_perim(lp))
            if best > 0:
                acc.append(best)
    ua_g = float(np.mean(ua_gs))
    fa_g = float(np.mean(fa_gs))
    # thigh loops at crotch - 0.10 (two loops, one per leg)
    loops = plane_loops(pos, Z, np.array([0, 0, mh_crotch - 0.10]))
    th = [loop_perim(lp) for lp in loops
          if abs(lp.mean(axis=0)[0]) > 0.03 and loop_perim(lp) > 0.15]
    thigh_g = float(np.mean(th)) if th else float("nan")
    # calf: max loop per side in the anatomical calf zone (4-17 cm
    # below the knee line; sweeping to the knee measures the knee /
    # lower-thigh junction and calls it calf)
    knee_z = min(lm["K"][2] for lm in
                 (lmts["lm"].get("legR"), lmts["lm"].get("legL")) if lm)
    calf = {}
    for zz in np.arange(knee_z - 0.17, knee_z - 0.04, 0.008):
        for lp in plane_loops(pos, Z, np.array([0, 0, zz])):
            cx = lp.mean(axis=0)[0]
            if abs(cx) > 0.03 and loop_perim(lp) > 0.08:
                s = "R" if cx > 0 else "L"
                calf[s] = max(calf.get(s, 0.0), loop_perim(lp))
    calf_g = float(np.mean(list(calf.values()))) if calf else float("nan")
    return {
        "height_m": height, "volume_L": mesh_volume(pos) * 1000.0,
        "neck_g": neck_g, "neck_w": neck_w, "head_w": head_w,
        "head_h": head_h, "chin_z": chin_z, "chest_g": chest_g,
        "chest_w": chest_w, "waist_w": waist_w,
        "waist_g": waist_g, "chest_d": chest_d, "waist_d": waist_d,
        "delt_span": delt_span, "trap_angle": trap_angle,
        "visible_neck": visible_neck, "ua_g": ua_g, "fa_g": fa_g,
        "thigh_g": thigh_g, "calf_g": calf_g,
        "M1_neckW_headW": neck_w / head_w,
        "M2_neck_arm": neck_g / ua_g, "M2_neck_calf": neck_g / calf_g,
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

def flipped(pos, D):
    p = pos + D
    v0 = p[FACES_B[:, 0]]
    v1 = p[FACES_B[:, 1]]
    v2 = p[FACES_B[:, 2]]
    n0 = np.cross(pos[FACES_B[:, 1]] - pos[FACES_B[:, 0]],
                  pos[FACES_B[:, 2]] - pos[FACES_B[:, 0]])
    n1 = np.cross(v1 - v0, v2 - v0)
    dot = np.einsum("ij,ij->i", n0, n1)
    ln = np.linalg.norm(n0, axis=1) * np.linalg.norm(n1, axis=1)
    return dot < -1e-12 * np.maximum(ln, 1e-30)
