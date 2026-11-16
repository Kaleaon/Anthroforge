#!/usr/bin/env python3
"""
Follow-up measurements for COUPLING_VALIDATION.md -- run AFTER
build_coupling_validation.py (loads its written targets).

Method note: to guarantee identical frames/fields, this script
execs the build script's own setup prefix (everything before its
GACHIDEBU section: data loads, labelling, kernel transfers of the
definition + neck fields, evaluator runs, machinery self-check,
macro map, factor maps). Measurements added here:

  * girth stations by loop PERIMETER (the ellipse fit degenerates
    on pelvis sections -> hip was NaN): base / strongman /
    gachidebu / tissue-only-scaled gachidebu (M4 attribution) /
    pear + bigchest with their distribution-0 controls (unrepaired
    recompositions; the shipped targets' repairs touched <= 98
    verts, sub-mm girth impact);
  * curve-following dip metric for the line features (VLine,
    TrapsValleys, PecsCrease): the (h, theta)-binned profile metric
    smears diagonal lines and sits on unrelated masses (belly
    apron, traps). The curve metric samples the surface along the
    field's own footprint: per slice, dip = flank radius - on-line
    radius; noise = std of the substrate's per-slice dips;
  * wrap audit on the crossfade-weighted ring field TG*(1-B_CORE),
    the fairest post-hoc reconstruction of 'ring tissue'.

Writes work/coupling_measurements.json. Study-only analysis.
"""
import json
import numpy as np
from pathlib import Path

HERE = Path(__file__).resolve().parent
BP = HERE.parent

_src = (HERE / "build_coupling_validation.py").read_text()
_cut = _src.index('print("\\n== GACHIDEBU ==")')
exec(compile(_src[:_cut], "build_coupling_validation.py", "exec"),
     globals())

R = {"note": "follow-up measurements; see COUPLING_VALIDATION.md"}
CM = 100.0

# ------------------------------------------------------------- loop tools
def plane_loops2(points, axis, value):
    """Section loops via a global edge map (robust chaining).
    Body faces only: helper faces share edges with the body and
    poison the chaining (run 3: helper-inclusive sections wandered
    into 400-800 cm 'loops')."""
    tris = mh_tris[np.all(mh_tris < NB, axis=1)]
    P = points[:, axis]
    edge_pts, segs = {}, []
    for fi in range(len(tris)):
        ids = []
        for a, b in ((0, 1), (1, 2), (2, 0)):
            va, vb = tris[fi, a], tris[fi, b]
            da, db = P[va] - value, P[vb] - value
            if da * db < 0:
                key = (min(va, vb), max(va, vb))
                if key not in edge_pts:
                    t = da / (da - db)
                    edge_pts[key] = points[va] + t * (points[vb]
                                                      - points[va])
                ids.append(key)
        if len(ids) == 2:
            segs.append((ids[0], ids[1]))
    if not segs:
        return []
    at = {}
    for i, (a, b) in enumerate(segs):
        at.setdefault(a, []).append((i, b))
        at.setdefault(b, []).append((i, a))
    loops, used = [], np.zeros(len(segs), bool)
    for s in range(len(segs)):
        if used[s]:
            continue
        used[s] = True
        a, b = segs[s]
        chain = [edge_pts[a], edge_pts[b]]
        cur = b
        for _ in range(len(segs) + 2):
            nxt = None
            for (j, end) in at.get(cur, []):
                if not used[j]:
                    nxt = (j, end)
                    break
            if nxt is None:
                break
            j, end = nxt
            used[j] = True
            chain.append(edge_pts[end])
            cur = end
            if cur == a:
                break
        if len(chain) >= 4:
            loops.append(np.array(chain))
    return loops


def loop_perim(L):
    d = np.diff(np.vstack([L, L[:1]]), axis=0)
    return float(np.hypot(d[:, 0], d[:, 1]).sum())


def band_max(P, hlo, hhi, step=0.02):
    cz, nz = mh_crotch, mh_neck
    best = 0.0
    for hh in np.arange(hlo, hhi + 1e-9, step):
        for L in plane_loops2(P, 2, cz + hh * (nz - cz)):
            best = max(best, loop_perim(L))
    return best


def station_table(P):
    cz = mh_crotch
    navel_z = mh_pos_mac[navel_mh, 2]
    waist = 0.0
    for dz in np.arange(-0.012, 0.0121, 0.006):
        for L in plane_loops2(P, 2, navel_z + dz):
            waist = max(waist, loop_perim(L))
    thigh = 0.0
    for L in plane_loops2(P, 2, cz - 0.05):
        thigh = max(thigh, loop_perim(L))
    return {"chest": band_max(P, 0.80, 0.90),
            "waist_navel": waist,
            "waist_min": band_max(P, 0.45, 0.62),
            "hip": band_max(P, 0.0, 0.16),
            "thigh": thigh}


def load_target(tag):
    """MakeHuman .target text format: '#' comments, then
    'index dx dy dz' lines (deltas in basemesh units vs base.obj
    rest positions -- the header contract of the proofs' writer)."""
    d = np.zeros((len(mh_pos), 3))
    for line in (BP / f"body.coupling.{tag}.target").read_text().splitlines():
        if not line or line.startswith("#"):
            continue
        p = line.split()
        if len(p) == 4:
            s = [float(p[1]), float(p[2]), float(p[3])]
            # writer stores [dx, dz, dy] / 0.1 (MPFB decimetre frame)
            d[int(p[0])] = [s[0] * 0.1, s[2] * 0.1, s[1] * 0.1]
    return d


TARGETS = {t: load_target(t) for t in ("gachidebu", "pear", "bigchest")}

# --------------------------------------------------------- girth stations
print("station tables (perimeter method)...")
POS = {"base": mh_pos_mac,
       "strongman": mh_pos_mac + M_F + W_F + T_F,
       "gachidebu": mh_pos_mac + TARGETS["gachidebu"],
       "gachidebu_tissue_scaled_only": mh_pos_mac + M_F + W_F
       + T_SCALE * T_F + NECK_EMB}
R["stations"] = {}
for nm, P in POS.items():
    R["stations"][nm] = station_table(P)
    print(" ", nm, {k: round(v * CM, 1)
                    for k, v in R["stations"][nm].items()})

for tag in ("pear", "bigchest"):
    ev = EV[tag]
    w = ev.derived["tissue.level"]
    twin = (M_F + W_F) + d5(w)
    R["stations"][tag] = station_table(mh_pos_mac + TARGETS[tag])
    R["stations"][tag + "_control"] = station_table(mh_pos_mac + twin)
    print(" ", tag, {k: round(v * CM, 1)
                     for k, v in R["stations"][tag].items()},
          "| ctl", {k: round(v * CM, 1)
                    for k, v in R["stations"][tag + "_control"].items()})
    a, b = R["stations"][tag], R["stations"][tag + "_control"]
    R.setdefault("station_ratios", {})[tag] = {
        "chest_waist": a["chest"] / a["waist_navel"],
        "waist_hip": a["waist_navel"] / a["hip"],
        "chest_hip": a["chest"] / a["hip"],
        "control_chest_waist": b["chest"] / b["waist_navel"],
        "control_waist_hip": b["waist_navel"] / b["hip"],
        "control_chest_hip": b["chest"] / b["hip"]}

# ------------------------------------------------------------ curve dips
def core_window(F, frac=0.5):
    mag = np.linalg.norm(F, axis=1)
    return np.where((mag >= frac * mag.max()) & BODY_MASK)[0]


def _radius(P):
    return np.hypot(P[:, 0] - ax_mh[:, 0], P[:, 1] - ax_mh[:, 1])


def dip_curve(P, F, nslices=9):
    """Vertical/diagonal line feature: the footprint is a PAIR of
    lines (left/right of the midline), so the curve is followed per
    side: slice by h; per slice and side, dip = flank radius -
    on-line radius (angles relative to that side's line centre)."""
    core = core_window(F)
    r = _radius(P)
    side_of = np.sign(mh_pos_mac[:, 0] - ax_mh[:, 0])
    dips = []
    for sgn in (1.0, -1.0):
        cs = core[side_of[core] == sgn]
        if len(cs) < 12:
            continue
        phi0 = np.arctan2(np.sin(th_mh[cs]).mean(),
                          np.cos(th_mh[cs]).mean())
        u = (th_mh - phi0 + np.pi) % (2 * np.pi) - np.pi
        edges = np.linspace(h_mh[cs].min(), h_mh[cs].max(),
                            nslices + 1)
        for i in range(nslices):
            msl = (h_mh >= edges[i]) & (h_mh < edges[i + 1]) \
                & (side_of == sgn)
            cc = cs[(h_mh[cs] >= edges[i]) & (h_mh[cs] < edges[i + 1])]
            if len(cc) < 3:
                continue
            u0 = np.arctan2(np.sin(u[cc]).mean(),
                            np.cos(u[cc]).mean())
            uu = (u - u0 + np.pi) % (2 * np.pi) - np.pi
            mc = msl & BODY_MASK & (np.abs(uu) < 0.075)
            mf = msl & BODY_MASK & (np.abs(uu) > 0.11) \
                & (np.abs(uu) < 0.24)
            if mc.sum() >= 2 and mf.sum() >= 4:
                dips.append(float(r[mf].mean() - r[mc].mean()))
    if not dips:
        return float("nan"), []
    return float(np.mean(dips)) * 1000.0, [d * 1000.0 for d in dips]


def dip_curve_h(P, F, nslices=9):
    """Horizontal line feature (crease): slice by theta; per slice,
    dip = above-line radius - on-line radius."""
    core = core_window(F)
    r = _radius(P)
    edges = np.linspace(th_mh[core].min(), th_mh[core].max(),
                        nslices + 1)
    dips = []
    for i in range(nslices):
        msl = (th_mh >= edges[i]) & (th_mh < edges[i + 1])
        cc = core[msl[core]]
        if len(cc) < 2:
            continue
        h0 = h_mh[cc].mean()
        mc = msl & BODY_MASK & (np.abs(h_mh - h0) < 0.03)
        ma = msl & BODY_MASK & (h_mh > h0 + 0.045) & (h_mh < h0 + 0.11)
        if mc.sum() >= 2 and ma.sum() >= 4:
            dips.append(float(r[ma].mean() - r[mc].mean()))
    if not dips:
        return float("nan"), []
    return float(np.mean(dips)) * 1000.0, [d * 1000.0 for d in dips]


def curve_increment(sub_pos, F, v, kind):
    fn = dip_curve if kind == "v" else dip_curve_h
    d1, _ = fn(sub_pos + v * F, F)
    d0, slices0 = fn(sub_pos, F)
    noise = float(np.std(slices0)) if len(slices0) >= 4 else float("nan")
    return {"inc_mm": d1 - d0, "abs_dip_mm": d1,
            "substrate_slice_std_mm": noise,
            "snr_inc": (d1 - d0) / noise if noise else None,
            "snr_abs": d1 / noise if noise else None}


S0 = mh_pos_mac + M_F + W_F
S1 = mh_pos_mac + TARGETS["gachidebu"]
CUR = {}
for nm, F, raw_v, eff_v in (
        ("vline", F_VLINE, 0.85, float(EV["gachidebu"]
                                       .sliders["body.definition.vline"])),
        ("valleys", F_VALLEYS, 0.40,
         float(EV["gachidebu"].sliders["body.definition.traps_valleys"]))):
    CUR[nm] = {"raw": raw_v, "effective": eff_v,
               "low": curve_increment(S0, F, raw_v, "v"),
               "naive": curve_increment(S1, F, raw_v, "v"),
               "coupled": curve_increment(S1, F, eff_v, "v")}
    c = CUR[nm]
    print(f"curve {nm}: low inc {c['low']['inc_mm']:+.2f} (abs "
          f"{c['low']['abs_dip_mm']:+.2f}, noise "
          f"{c['low']['substrate_slice_std_mm']:.2f}); naive inc "
          f"{c['naive']['inc_mm']:+.2f}; coupled inc "
          f"{c['coupled']['inc_mm']:+.2f} (abs "
          f"{c['coupled']['abs_dip_mm']:+.2f}, SNR_inc "
          f"{c['coupled']['snr_inc']:.2f})")
R["curve_dips_gachidebu"] = CUR

CR2 = {}
for tag, dist, eff in (("pear", -1.0, 0.77088),
                       ("bigchest", 1.0, 0.5664)):
    evc = evaluate_effective_vector(
        reg, coup,
        {"body.muscle": 1.0, "body.tissue.level": 0.6,
         "body.distribution": dist,
         "body.definition.pecs_crease": 0.80})
    tfac = factor_map(evc.derived, "tissue")
    mfac = factor_map(evc.derived, "muscle")
    sub = mh_pos_mac + M_F * mfac[:, None] \
        + W_F * evc.derived["distribution.muscle.chest"] \
        + d5(0.6) * tfac[:, None]
    CR2[tag] = {"effective": eff,
                "coupled": curve_increment(sub, F_CREASE, eff, "h"),
                "raw": curve_increment(sub, F_CREASE, 0.80, "h")}
    print(f"curve crease {tag}: coupled inc "
          f"{CR2[tag]['coupled']['inc_mm']:+.2f} (abs "
          f"{CR2[tag]['coupled']['abs_dip_mm']:+.2f}, noise "
          f"{CR2[tag]['coupled']['substrate_slice_std_mm']:.2f}); "
          f"raw inc {CR2[tag]['raw']['inc_mm']:+.2f}")
R["curve_crease"] = CR2

# ------------------------------------------------------------- wrap audit
TG = T_SCALE * T_F
TG_X = TG * (1.0 - B_CORE)[:, None]


def sector(F, hlo, hhi):
    m = BODY_MASK & (h_mh >= hlo) & (h_mh <= hhi)
    dr = F[:, 0] * np.cos(th_mh) + F[:, 1] * np.sin(th_mh)
    out = {}
    for nm, mm in (("front", m & (np.abs(th_mh) < 0.6)),
                   ("flank", m & (np.abs(th_mh) >= 0.6)
                    & (np.abs(th_mh) <= 2.2)),
                   ("back", m & (np.abs(th_mh) > 2.2))):
        out[nm + "_cm"] = float(np.abs(dr[mm]).mean() * CM) \
            if mm.any() else float("nan")
    out["flank_front"] = out["flank_cm"] / out["front_cm"] \
        if out["front_cm"] else float("nan")
    return out


R["wrap_crossfade_weighted"] = {
    "chest": sector(TG_X, 0.78, 0.92),
    "waist": sector(TG_X, h_star - 0.06, h_star + 0.06),
    "belly_apron": sector(TG_X, 0.35, 0.55)}
for b, v in R["wrap_crossfade_weighted"].items():
    print(f"wrap[xfade] {b}: flank/front {v['flank_front']:.3f} "
          f"front {v['front_cm']:.2f} flank {v['flank_cm']:.2f} cm")

(BP / "work" / "coupling_measurements.json").write_text(
    json.dumps(R, indent=1, default=float))
print("wrote work/coupling_measurements.json")
print("MEASURE DONE")
