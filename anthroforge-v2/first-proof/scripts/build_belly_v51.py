#!/usr/bin/env python3
"""
Belly v5.1 builder: TERMINAL TISSUE CORRECTION.

Joe (Nov 12, 2026): "wrists and hands also need fat, not massive
amounts but that is realistic."

v5 faded the adiposity system to ZERO at the hands/feet (distal
cosine fades across wrist s 0.58-0.82 / ankle s 0.70-0.90). That was
the L1 rule read too absolutely: L1 says hands carry the LEAST fat,
not none. Real heavy bodies carry small but real terminal tissue --
it is one of the tells: dorsal hand pad, thickened finger bases,
softened knuckles, wrist definition lost. v5.1 replaces the zero
fade's endpoint with a low, anatomically shaped TERMINAL field:

    D51 = D5 + TERM        (TERM stacks on v5; v1-v5 files untouched)
    shape(w) = base + w * (LIN5 + TERM) + sign(w)|w|^2.0 * SAG

PRIMARY SOURCE (measured, not guessed): the Fat Males malehands /
malefeet same-topology deltas extracted in the original PoC
(character_assets/learned/fat-males_body_morph.npz -- hands mean
0.150 / max 0.501 Skyrim units, feet mean 0.384 / max 1.520). Their
per-zone perpendicular (radial) magnitudes set the terminal gains,
scaled by the hand/foot length ratio to hm08. Sector shaping
(dorsal > lateral > palmar on the hand; dorsal > side > sole on the
foot) and the knuckle-softening term are anatomical shaping [E]
over those measured magnitudes [S] -- disclosed as such.

Calibration targets (composed v5 + TERM at +1):
  * wrist girth gain total 2.5-3.5 cm (v5 alone: +1.85) -- one
    global scalar CAL is bisected onto 3.0 cm;
  * proximal finger thickness gain 15-20% (per-digit cap at 20% of
    local radius -- the cap binds if the scaled source exceeds it);
  * ankle girth gain total ~3.0-3.5 cm (v5 alone: +2.18); the FM
    ankle/heel zone conflates heel pad + ankle + shin splash, so
    its excess over the ankle-ring cap is routed to the heel/dorsal
    zones, not the ring -- documented, not hidden.

QA: 0 flips at +1 over ALL body faces (raw + macro bases) with
D5 + TERM composed (attenuation repair on TERM if needed);
inter-digit minimum distances base vs deformed (no webbing
collapse); zone gain table.
"""
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import scipy.sparse as sp
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
OUT = HERE.parent
V2 = OUT.parent
APP = V2.parent / "anthroforge-app"
for _p in (str(V2), str(APP)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from body_machinery import (  # noqa: E402
    BODY_END,
    DM_M,
    SK_UNIT_M,
    extract_limbs as _extract_limbs,
    girth_ellipse,
    limb_params,
    load_mpfb_base_obj,
    smoothstep,
)
from core.geometry import face_normals, write_target  # noqa: E402

WORK = OUT / "work"
LEARNED = Path.home() / "workspace/character_assets/learned"
MPFB_ZIP = Path.home() / "workspace/stick-figure-avatar/photoreal/tools/mpfb2.zip"

# ------------------------------------------------------------------ loads
corr = np.load(WORK / "correspondence.npz")
mh_tris = corr["mh_tris"].astype(np.int64)
_v5 = np.load(WORK / "belly_v5.npz")
D5 = _v5["delta_v5_canonical_m"].astype(np.float64)
LIN5 = _v5["lin_v5_canonical_m"].astype(np.float64)
SAG = _v5["sag_v5_canonical_m"].astype(np.float64)
GAMMA = float(_v5["gamma"])

fm = np.load(LEARNED / "fat-males_body_morph.npz")

mh_pos = load_mpfb_base_obj(MPFB_ZIP)
mh_body = np.zeros(len(mh_pos), bool); mh_body[:BODY_END] = True
mh_pos_mac = mh_pos.copy()
_mac = np.load(WORK / "mh_macro_base.npz")["pos_canonical_m"]
mh_pos_mac[:len(_mac)] = _mac

# ------------------------------------------------------- shared machinery
edges_all = np.vstack([mh_tris[:, [0, 1]], mh_tris[:, [1, 2]], mh_tris[:, [2, 0]]])
edges_all = np.unique(np.sort(edges_all, axis=1), axis=0)
A_mat = sp.coo_matrix((np.ones(len(edges_all)),
                       (edges_all[:, 0], edges_all[:, 1])),
                      shape=(len(mh_pos), len(mh_pos)))
A_mat = A_mat + A_mat.T
deg = np.asarray(A_mat.sum(axis=1)).ravel()
Lop = sp.diags(1.0 / np.maximum(deg, 1)) @ A_mat
nbrs = [np.asarray(A_mat[v].nonzero()[1]) for v in range(len(mh_pos))]

mh_limbs = _extract_limbs(
    mh_pos, mh_body, None, neck_log_mode=None, neck_fallback_top=True, verbose=False
)
for k, v in mh_limbs.items():
    print(f"hm08 {k}: length {v['length']*100:.1f} cm")

# ------------------------------------------- FM source zone statistics
# Perpendicular (radial) delta magnitudes per anatomical zone, in
# metres. FM hand frame: fingers point -z (wrist high z), thickness
# along y, lateral along x. FM foot frame: toes +y, up +z, heel -y.
def fm_hand_stats():
    pos = fm["hands_vertices"].astype(np.float64)
    d = fm["hands_delta"].astype(np.float64) * SK_UNIT_M
    out = {}
    for sgn in (1, -1):
        m = pos[:, 0] * sgn > 0
        P, D = pos[m], d[m]
        z = P[:, 2]
        # wrist = top 12% by z; palm band; fingers split by z thirds
        zlo, zhi = z.min(), z.max()
        zones = {"wrist": z > zhi - 0.10 * (zhi - zlo),
                 "palm": (z <= zhi - 0.10 * (zhi - zlo)) & (z > zhi - 0.34 * (zhi - zlo)),
                 "prox_finger": (z <= zhi - 0.34 * (zhi - zlo)) & (z > zhi - 0.62 * (zhi - zlo)),
                 "distal_finger": z <= zhi - 0.62 * (zhi - zlo)}
        for zn, zm in zones.items():
            perp = np.linalg.norm(D[zm][:, :2], axis=1)  # x,y = radial plane
            out.setdefault(zn, []).append(
                {"perp_mean_mm": float(perp.mean() * 1000),
                 "perp_p90_mm": float(np.percentile(perp, 90) * 1000),
                 "n": int(zm.sum())})
        # hand length: wrist centroid (top 15 verts) to tip centroid (bottom 15)
        iw = np.argsort(-z)[:15]; it = np.argsort(z)[:15]
        out.setdefault("length_m", []).append(
            float(np.linalg.norm(P[iw].mean(0) - P[it].mean(0)) * SK_UNIT_M))
    agg = {zn: float(np.mean([e["perp_mean_mm"] for e in v])) if zn != "length_m"
           else float(np.mean(v)) for zn, v in out.items()}
    agg_p90 = {zn: float(np.mean([e["perp_p90_mm"] for e in v]))
               for zn, v in out.items() if zn != "length_m"}
    return agg, agg_p90

def fm_foot_stats():
    pos = fm["feet_vertices"].astype(np.float64)
    d = fm["feet_delta"].astype(np.float64) * SK_UNIT_M
    out = {}
    for sgn in (1, -1):
        m = pos[:, 0] * sgn > 0
        P, D = pos[m], d[m]
        y = P[:, 1]  # heel -8.8 -> toes +10.4
        zones = {"ankle_heel": (y < -2.0) | (P[:, 2] > 8.0),
                 "midfoot": (y >= -2.0) & (y < 4.0) & (P[:, 2] <= 8.0),
                 "toes": y >= 4.0}
        for zn, zm in zones.items():
            # radial plane for a foot ~ (x, z): sideways + up/down
            perp = np.linalg.norm(D[zm][:, [0, 2]], axis=1)
            out.setdefault(zn, []).append(
                {"perp_mean_mm": float(perp.mean() * 1000),
                 "perp_p90_mm": float(np.percentile(perp, 90) * 1000),
                 "n": int(zm.sum())})
        ih = np.argsort(y)[:20]; it = np.argsort(-y)[:20]
        out.setdefault("length_m", []).append(
            float(np.linalg.norm(P[ih].mean(0) - P[it].mean(0)) * SK_UNIT_M))
    agg = {zn: float(np.mean([e["perp_mean_mm"] for e in v])) if zn != "length_m"
           else float(np.mean(v)) for zn, v in out.items()}
    agg_p90 = {zn: float(np.mean([e["perp_p90_mm"] for e in v]))
               for zn, v in out.items() if zn != "length_m"}
    return agg, agg_p90

HS, HS90 = fm_hand_stats()
FS, FS90 = fm_foot_stats()
print("FM hand zones perp mean mm:", {k: round(v, 2) for k, v in HS.items()})
print("FM hand zones perp p90  mm:", {k: round(v, 2) for k, v in HS90.items()})
print("FM foot zones perp mean mm:", {k: round(v, 2) for k, v in FS.items()})
print("FM foot zones perp p90  mm:", {k: round(v, 2) for k, v in FS90.items()})

# ------------------------------------------- target segmentation: hands
def build_hand(side_name):
    """Returns dict of per-vertex data for one hand on hm08."""
    lb = mh_limbs[f"arm_{side_name}"]
    s, dist, phi, er, adir = limb_params(mh_pos, lb)
    pts = lb["pts"]
    # wrist station point: polyline point nearest s=0.72
    segv = np.diff(pts, axis=0); seglen = np.linalg.norm(segv, axis=1)
    cum = np.concatenate([[0], np.cumsum(seglen)]) / seglen.sum()
    i_w = int(np.argmin(np.abs(cum - 0.72)))
    P_wrist = pts[i_w]
    tip_seed = mh_body & (dist < 0.075) & (s > 0.93)
    mid_seed = mh_body & (dist < 0.075) & (s > 0.78) & (s <= 0.88)
    e_long = tip_seed.mean() if False else None
    tip_c = mh_pos[tip_seed].mean(axis=0)
    mid_c = mh_pos[mid_seed].mean(axis=0)
    e_long = tip_c - mid_c; e_long /= np.linalg.norm(e_long)
    # extended axis origin at wrist station
    rel = mh_pos - P_wrist
    a = rel @ e_long                       # along-hand coordinate (m)
    # thickness axis via PCA of hand candidate verts
    cand = mh_body & (dist < 0.085) & (s > 0.66)
    Pc = mh_pos[cand] - mh_pos[cand].mean(axis=0)
    _, _, vt = np.linalg.svd(Pc, full_matrices=False)
    e_dp = vt[2]                            # smallest variance = thickness
    e_dp = e_dp - (e_dp @ e_long) * e_long; e_dp /= np.linalg.norm(e_dp)
    # Dorsal sign, DECISIVE cue: the thumb's first joint sits PALMAR
    # to the plane of the four finger MCP joints (base.obj carries
    # joint helper verts). The fingertip-curl cue used in the first
    # run is NOT reliable -- it flipped the sign and the palmar side
    # received the dorsal weighting (caught on the renders: the
    # "palmar" camera showed fingernails).
    global _JOINTS
    try:
        _JOINTS
    except NameError:
        _JOINTS = {}
        _grp = None
        with zipfile.ZipFile(MPFB_ZIP) as _zf:
            _obj_lines = _zf.read("mpfb/data/3dobjs/base.obj").decode().splitlines()
        for _l in _obj_lines:
            if _l.startswith("g "):
                _grp = _l[2:].strip().strip("\r")
            elif _l.startswith("f ") and _grp and _grp.startswith("joint-"):
                # joint helpers are FACE groups over body verts; the
                # joint position is their verts' centroid
                _JOINTS.setdefault(_grp, []).extend(
                    int(_t.split("/")[0]) - 1 for _t in _l.split()[1:])
    _pre = "joint-l-" if side_name == "R" else "joint-r-"
    _mcp = [mh_pos[_JOINTS[f"{_pre}finger-{k}-1"]].mean(axis=0)
            for k in (2, 3, 4, 5) if f"{_pre}finger-{k}-1" in _JOINTS]
    _thumb = (mh_pos[_JOINTS[f"{_pre}finger-1-1"]].mean(axis=0)
              if f"{_pre}finger-1-1" in _JOINTS else None)
    if _mcp and _thumb is not None:
        _off = float((_thumb - np.mean(_mcp, axis=0)) @ e_dp)
        if _off > 0:    # thumb joint on +e_dp side -> +e_dp is palmar
            e_dp = -e_dp
        print(f"  dorsal sign via thumb-MCP offset {_off*1000:.1f} mm")
    else:
        print("  WARNING: joint helpers not found; dorsal sign unverified")
    e_lat = np.cross(e_dp, e_long); e_lat /= np.linalg.norm(e_lat)
    b = rel @ e_lat
    dp = rel @ e_dp
    hand_len = float(np.percentile(a[cand], 99.5))
    # hand vert set: near extended axis, a beyond blend start
    r_ext = np.linalg.norm(rel - a[:, None] * e_long[None, :], axis=1)
    hset = cand & (a > -0.055) & (r_ext < 0.075)
    a_web = 0.52 * hand_len
    # ---- digit segmentation from the MPFB rig's own skin weights.
    # The hm08 hand is ONE webbed mesh with fingers resting ~1 mm
    # apart, so geometric clustering cannot split it (probed Nov 12,
    # 2026: b-gap split, euclidean linkage and a geodesic fingertip
    # watershed all merged or split fingers). The rig's finger bone
    # weights ARE the authoritative segmentation: digit = finger
    # group (1-5) with the largest summed weight, segment = dominant
    # segment bone (1-3) within the group. MPFB bone side is the
    # CHARACTER's side: its .L bones sit at canonical +x (our R).
    global _MPFB_WEIGHTS
    try:
        _MPFB_WEIGHTS
    except NameError:
        with zipfile.ZipFile(MPFB_ZIP) as z:
            _MPFB_WEIGHTS = json.loads(
                z.read("mpfb/data/rigs/standard/weights.default.json"))["weights"]
    suffix = ".L" if side_name == "R" else ".R"
    group_w = np.zeros((len(mh_pos), 5))
    seg_w = np.zeros((len(mh_pos), 5, 3))
    for gi in range(5):
        for si_ in range(3):
            pairs = _MPFB_WEIGHTS[f"finger{gi+1}-{si_+1}{suffix}"]
            idxw = np.array([p[0] for p in pairs])
            wv = np.array([p[1] for p in pairs])
            group_w[idxw, gi] += wv
            seg_w[idxw, gi, si_] = wv
    digits = []
    for gi in range(5):
        vi = np.where(hset & (group_w.argmax(axis=1) == gi)
                      & (group_w.max(axis=1) > 0.22))[0]
        if len(vi) < 12:
            continue
        C = mh_pos[vi]
        cen = C.mean(axis=0)
        _, _, vtd = np.linalg.svd(C - cen, full_matrices=False)
        dax = vtd[0]
        if dax @ e_long < 0:
            dax = -dax
        rel = C - cen
        t = rel @ dax
        t_n = (t - t.min()) / max(t.max() - t.min(), 1e-9)
        seg = seg_w[vi, gi].argmax(axis=1) + 1
        trans = []
        for k in (1, 2):
            lo_ = t_n[seg == k]; hi_ = t_n[seg == k + 1]
            if len(lo_) and len(hi_):
                trans.append(float(0.5 * (lo_.max() + hi_.min())))
        digits.append({"verts": vi, "centroid": cen, "axis": dax,
                       "b_mean": float(b[vi].mean()),
                       "dp_mean": float(dp[vi].mean()),
                       "t_n": t_n, "seg": seg, "transitions": trans,
                       "group": gi + 1})
    digits.sort(key=lambda d: d["group"])
    print(f"hand {side_name}: {len(digits)} digits (rig weights), sizes "
          f"{[len(d['verts']) for d in digits]}, hand_len {hand_len*100:.1f} cm, "
          f"e_long {np.round(e_long,2)} e_dp(dorsal) {np.round(e_dp,2)}")
    return {"s": s, "dist": dist, "er": er, "a": a, "b": b, "dp": dp,
            "e_long": e_long, "e_dp": e_dp, "e_lat": e_lat,
            "P_wrist": P_wrist, "hset": hset, "cand": cand,
            "a_web": a_web, "hand_len": hand_len, "digits": digits,
            "r_ext": r_ext}

hands = {sn: build_hand(sn) for sn in ("R", "L")}

# ------------------------------------------- target segmentation: feet
def build_foot(side_name):
    lb = mh_limbs[f"leg_{side_name}"]
    s, dist, phi, er, adir = limb_params(mh_pos, lb)
    pts = lb["pts"]
    segv = np.diff(pts, axis=0); seglen = np.linalg.norm(segv, axis=1)
    cum = np.concatenate([[0], np.cumsum(seglen)]) / seglen.sum()
    i_a = int(np.argmin(np.abs(cum - 0.84)))
    P_ankle = pts[i_a]
    z_floor = mh_pos[mh_body, 2].min()
    toe_seed = mh_body & (dist < 0.20) & (s > 0.90)
    toe_c = mh_pos[toe_seed].mean(axis=0)
    e_long = toe_c - P_ankle; e_long[2] = 0.0
    e_long /= np.linalg.norm(e_long)       # horizontal forward
    e_up = np.array([0.0, 0.0, 1.0])
    e_up = e_up - (e_up @ e_long) * e_long; e_up /= np.linalg.norm(e_up)
    e_lat = np.cross(e_up, e_long); e_lat /= np.linalg.norm(e_lat)
    rel = mh_pos - P_ankle
    a = rel @ e_long
    up = rel @ e_up
    lat = rel @ e_lat
    fset = mh_body & (s > 0.80) & (dist < 0.21) & (a > -0.06)
    foot_len = float(np.percentile(a[fset], 99.5)) if fset.sum() else 0.25
    print(f"foot {side_name}: {int(fset.sum())} verts, foot_len "
          f"{foot_len*100:.1f} cm, e_long {np.round(e_long,2)}")
    return {"s": s, "dist": dist, "er": er, "a": a, "up": up, "lat": lat,
            "e_long": e_long, "e_up": e_up, "e_lat": e_lat,
            "P_ankle": P_ankle, "fset": fset, "foot_len": foot_len}

feet = {sn: build_foot(sn) for sn in ("R", "L")}

# ------------------------------------------- gains from source (metres)
hm_hand_len = float(np.mean([hands[s]["hand_len"] for s in hands]))
hm_foot_len = float(np.mean([feet[s]["foot_len"] for s in feet]))
hand_scale = hm_hand_len / HS["length_m"]
foot_scale = hm_foot_len / FS["length_m"]
print(f"length scales: hand {hand_scale:.3f} (hm {hm_hand_len*100:.1f} cm / "
      f"FM {HS['length_m']*100:.1f} cm), foot {foot_scale:.3f}")
G = {  # radial gains (m), pre-CAL, from FM perp means x length scale
    "wrist": HS["wrist"] / 1000 * hand_scale,
    "palm": HS["palm"] / 1000 * hand_scale,
    "prox_finger": HS["prox_finger"] / 1000 * hand_scale,
    "distal_finger": HS["distal_finger"] / 1000 * hand_scale,
    "ankle": FS["ankle_heel"] / 1000 * foot_scale,
    "midfoot": FS["midfoot"] / 1000 * foot_scale,
    "toes": FS["toes"] / 1000 * foot_scale,
}
print("zone gains pre-CAL (mm):", {k: round(v * 1000, 2) for k, v in G.items()})
# ankle ring cap: composed ankle gain target ~3.25 cm total; v5 gave
# +2.18 -> terminal ring delta ~1.7 mm uniform-equivalent.
ANKLE_RING_CAP = 0.0017

# ------------------------------------------- terminal field assembly
def sector_hand(dp_n, lat_n):
    """dp_n: cos angle toward dorsal (+1 dorsal, -1 palmar)."""
    return np.where(dp_n >= 0, 0.55 + 0.75 * dp_n, 0.55 + 0.35 * dp_n)

FBOOST = 1.0   # finger-zone scalar, calibrated after CAL (see below)

def build_terminal(CAL):
    T = np.zeros_like(mh_pos)
    W = np.zeros(len(mh_pos))   # priority weight for overlap resolution
    def add(idx, disp, wgt):
        take = wgt >= W[idx]
        ii = idx[take]
        T[ii] = disp[take]
        W[ii] = wgt[take]
    for sn, H in hands.items():
        s, er = H["s"], H["er"]
        # --- wrist ring (around arm axis), ramp s 0.60 -> 0.74, out by 0.86
        ramp = smoothstep(0.60, 0.74, s) * (1 - smoothstep(0.80, 0.90, s))
        wm = mh_body & (H["dist"] < 0.075) & (ramp > 0.003)
        idx = np.where(wm)[0]
        if len(idx):
            # dorsal-ish bias via radial dir vs dorsal axis
            cosd = er[idx] @ H["e_dp"]
            sec = 0.8 + 0.4 * np.clip(cosd, -1, 1)
            add(idx, (G["wrist"] * CAL * ramp[idx] * sec)[:, None] * er[idx],
                1.0 * ramp[idx])
        # --- palm (around extended hand axis)
        pm = H["hset"] & (H["a"] <= H["a_web"])
        idx = np.where(pm)[0]
        if len(idx):
            rel = mh_pos[idx] - H["P_wrist"]
            rad = rel - (rel @ H["e_long"])[:, None] * H["e_long"][None, :]
            rn = np.linalg.norm(rad, axis=1)
            rdir = rad / np.maximum(rn, 1e-9)[:, None]
            cosd = rdir @ H["e_dp"]
            sec = sector_hand(cosd, None)
            edge = smoothstep(-0.055, -0.01, H["a"][idx])
            add(idx, (G["palm"] * CAL * sec * edge)[:, None] * rdir,
                0.9 * edge)
        # --- digits
        for dg in H["digits"]:
            vi = dg["verts"]
            C = dg["centroid"]; ax = dg["axis"]
            rel = mh_pos[vi] - C
            t = rel @ ax
            rad = rel - t[:, None] * ax[None, :]
            rn = np.linalg.norm(rad, axis=1)
            rdir = rad / np.maximum(rn, 1e-9)[:, None]
            t_n = dg["t_n"]
            prox = dg["seg"] == 1     # dominant segment-1 bone (rig)
            gain = np.where(prox, G["prox_finger"], G["distal_finger"]) * FBOOST
            # per-digit cap: radial gain <= 20% of local radius (prox),
            # 15% mid/distal -- thickness gain target 15-20% at bases
            cap = np.where(prox, 0.20, 0.15) * np.maximum(rn, 0.002)
            gain = np.minimum(gain * CAL, cap)
            cosd = rdir @ H["e_dp"]
            # pudgy fingers are ROUND: dorsal leads, palmar follows
            # closely; only the lateral sectors are contact-capped.
            sec = np.where(cosd >= 0, 0.68 + 0.55 * cosd, 0.78 + 0.22 * cosd)
            # knuckle softening: radius-profile dip at the prox/mid
            # joint band (t_n ~ 0.42) and MCP band (t_n ~ 0.05):
            # extra dorsal+side radial where the base profile dips
            order = np.argsort(t_n)
            r_sorted = rn[order]
            k = max(3, len(r_sorted) // 12)
            trend = np.convolve(np.pad(r_sorted, k, mode="edge"),
                                np.ones(2 * k + 1) / (2 * k + 1), "valid")
            dip = np.zeros(len(rn)); dip[order] = np.clip(trend - r_sorted, 0, None)
            tr = dg["transitions"]
            kb1 = tr[0] if len(tr) > 0 else 0.42
            kb2 = tr[1] if len(tr) > 1 else 0.75
            knuckle_band = np.exp(-0.5 * ((t_n - kb1) / 0.10) ** 2) \
                + 0.7 * np.exp(-0.5 * ((t_n - kb2) / 0.08) ** 2) \
                + 0.5 * np.exp(-0.5 * ((t_n - 0.04) / 0.07) ** 2)
            extra = 0.55 * dip * knuckle_band * np.clip(cosd + 0.6, 0, 1.3)
            tot = gain * sec + extra
            # CONTACT CAP: hm08's fingers rest in contact, so a side-
            # sector vert has no free space to grow into. Cap each
            # vert's gain at 45% of its distance to the nearest vert
            # of a DIFFERENT digit (+0.3 mm) -- thickening is routed
            # into the free sectors (dorsal/palmar), contact faces
            # flatten instead of interpenetrating (the L5 squish
            # principle, one scale down).
            others = (np.concatenate([d2["verts"] for d2 in H["digits"]
                                      if d2 is not dg])
                      if len(H["digits"]) > 1 else np.array([], dtype=int))
            if len(others):
                d_other, _ = cKDTree(mh_pos[others]).query(mh_pos[vi], k=1)
                tot = np.minimum(tot, 0.45 * d_other + 0.0003)
            taper = 1 - 0.45 * smoothstep(0.80, 1.0, t_n)
            add(vi, (tot * taper)[:, None] * rdir, np.full(len(vi), 0.95))
    for sn, F in feet.items():
        s = F["s"]
        # --- ankle ring (around leg axis)
        ramp = smoothstep(0.74, 0.84, s) * (1 - smoothstep(0.90, 0.99, s))
        am = mh_body & (F["dist"] < 0.115) & (ramp > 0.003)
        idx = np.where(am)[0]
        if len(idx):
            g = min(G["ankle"] * CAL, ANKLE_RING_CAP + 0.0008 * CAL)
            add(idx, (g * ramp[idx])[:, None] * F["er"][idx], 1.0 * ramp[idx])
        # --- midfoot + toes (around foot axis): dorsal-weighted
        fm_ = F["fset"] & (F["a"] > -0.01)
        idx = np.where(fm_)[0]
        if len(idx):
            rel = mh_pos[idx] - F["P_ankle"]
            rad = rel - (rel @ F["e_long"])[:, None] * F["e_long"][None, :]
            rn = np.linalg.norm(rad, axis=1)
            rdir = rad / np.maximum(rn, 1e-9)[:, None]
            upn = rdir @ F["e_up"]
            sec = np.where(upn >= 0, 0.45 + 0.85 * upn, 0.45 + 0.22 * upn)
            a_n = F["a"][idx] / max(F["foot_len"], 1e-9)
            gain = np.where(a_n < 0.55, G["midfoot"], G["toes"]) * CAL
            heel_excess = max(G["ankle"] * CAL - ANKLE_RING_CAP, 0.0)
            heel_zone = np.exp(-0.5 * ((F["a"][idx] + 0.02) / 0.035) ** 2)
            gain = gain + heel_excess * 0.8 * heel_zone
            taper = 1 - 0.5 * smoothstep(0.85, 1.02, a_n)
            edge = smoothstep(-0.01, 0.02, F["a"][idx])
            add(idx, (gain * sec * taper * edge)[:, None] * rdir,
                0.9 * edge)
    return T

def graph_smooth_support(V, supp_mask, passes=3, keep=0.35):
    V = V.copy()
    for _ in range(passes):
        sm = Lop @ V
        V = np.where(supp_mask[:, None], (1 - keep) * V + keep * sm, V)
    return V

# wrist girth measurement (v5 method: axis-band ellipse at s=0.72)
def station_girth(P, limb_name, s_t, gate_r):
    lb = mh_limbs[limb_name]
    s, dist, phi, er, adir = limb_params(mh_pos, lb)
    m = mh_body & (dist < gate_r) & (np.abs(s - s_t) < 0.02)
    i0 = np.where(m)[0][np.argmin(np.abs(s[m] - s_t))]
    a_dir = adir[i0]
    eo = np.array([1.0, 0, 0]) * lb["side"]
    eo = eo - (eo @ a_dir) * a_dir; eo /= np.linalg.norm(eo)
    ef = np.cross(a_dir, eo) * lb["side"]
    q = P[m] - P[m].mean(axis=0)
    w = float(np.percentile(q @ eo, 99) - np.percentile(q @ eo, 1))
    d = float(np.percentile(q @ ef, 99) - np.percentile(q @ ef, 1))
    return girth_ellipse(w, d)

base_wrist = station_girth(mh_pos, "arm_R", 0.72, 0.135)
v5_wrist = station_girth(mh_pos + D5, "arm_R", 0.72, 0.135)
print(f"wrist girth: base {base_wrist*100:.1f} cm, v5 {v5_wrist*100:.1f} cm "
      f"(gain {(v5_wrist-base_wrist)*100:.2f})")

CAL = 1.0
for _ in range(8):
    T = build_terminal(CAL)
    supp = np.linalg.norm(T, axis=1) > 0.0002
    T = graph_smooth_support(T, supp)
    g = station_girth(mh_pos + D5 + T, "arm_R", 0.72, 0.135)
    gain = (g - base_wrist) * 100
    print(f"CAL {CAL:.3f}: composed wrist gain {gain:.2f} cm")
    if abs(gain - 3.0) < 0.08:
        break
    CAL *= 3.0 / max(gain - (v5_wrist - base_wrist) * 100, 0.05) \
        if gain > (v5_wrist - base_wrist) * 100 else 1.5
    CAL = float(np.clip(CAL, 0.2, 3.0))
print(f"calibrated CAL = {CAL:.3f}")
TERM = T

# Finger scalar: the FM prox-finger zone sets the SHAPE (sector
# profile, prox:distal ratio); FBOOST is bisected so the mean radial
# thickness gain over fingers 2-5 (rig groups 2-5) lands at 0.150,
# the foot of Joe's specified 15-20% proximal band. The
# 20%-of-radius per-vert cap is the band's ceiling and binds on the
# dorsal sector; lateral sectors sit lower under the contact cap.
# (With the round-finger sector rebalance, FBOOST solved to 1.000 --
# the source magnitude itself, calibrated, not inflated.)
def finger_radial_gain(T_):
    """Mean over fingers 2-5 of mean(|TERM| / local radius) on the
    proximal segment -- the thickness-gain fraction. (A dorsal-palmar
    percentile variant plateaued at 0.115: its extreme verts sit in
    the wrist-ramp overlap and do not track the finger field.)"""
    vals = []
    for sn, H in hands.items():
        for dg in H["digits"]:
            if dg["group"] == 1:
                continue
            vi = dg["verts"]; prox = dg["seg"] == 1
            if prox.sum() < 5:
                continue
            C = dg["centroid"]; ax = dg["axis"]
            rel = mh_pos[vi] - C
            t = rel @ ax
            rn = np.linalg.norm(rel - t[:, None] * ax[None, :], axis=1)
            disp = np.linalg.norm(T_[vi], axis=1)
            vals.append(float((disp[prox] / np.maximum(rn[prox], 1e-6)).mean()))
    return float(np.mean(vals)) if vals else 0.0

for _ in range(4):
    fg = finger_radial_gain(TERM)
    print(f"FBOOST {FBOOST:.3f}: finger prox mean radial thickness gain {fg:.3f}")
    if abs(fg - 0.150) < 0.008:
        break
    FBOOST = float(np.clip(FBOOST * 0.150 / max(fg, 0.01), 0.5, 3.5))
    T = build_terminal(CAL)
    supp_ = np.linalg.norm(T, axis=1) > 0.0002
    TERM = graph_smooth_support(T, supp_)
print(f"calibrated FBOOST = {FBOOST:.3f}")

# ------------------------------------------------------------- fold gate
Fb = mh_tris[np.array([np.all(f < BODY_END) for f in mh_tris])]
BASES = {"raw": mh_pos, "macro": mh_pos_mac}
n0_all = {k: face_normals(p, Fb) for k, p in BASES.items()}
def flips_on(delta, bname):
    nn = face_normals(BASES[bname] + delta, Fb)
    dots = np.einsum("ij,ij->i", n0_all[bname], nn)
    return int((dots < 0).sum()), float(dots.min())

supp = np.linalg.norm(TERM, axis=1) > 0.0002
pre = (flips_on(D5 + TERM, "raw"), flips_on(D5 + TERM, "macro"))
print(f"pre-repair flips (composed +1): raw {pre[0]}, macro {pre[1]}")
if pre[0][0] or pre[1][0]:
    att = np.ones(len(TERM)); Av = TERM.copy()
    for rnd in range(60):
        D = D5 + Av
        if flips_on(D, "raw")[0] == 0 and flips_on(D, "macro")[0] == 0:
            break
        bad = np.zeros(len(Fb), bool)
        for k in BASES:
            nn = face_normals(BASES[k] + D, Fb)
            bad |= np.einsum("ij,ij->i", n0_all[k], nn) < 0.01
        bad_verts = np.unique(Fb[bad])
        ring = np.unique(np.concatenate([nbrs[v] for v in bad_verts]))
        att[bad_verts] *= 0.82; att[ring] *= 0.94
        att = np.where(supp, 0.65 * att + 0.35 * (Lop @ att), att)
        att = np.clip(att, 0.10, 1.0)
        Av = att[:, None] * TERM
    TERM = Av
    print(f"attenuation repair: min att {att.min():.2f}, "
          f"{int((att < 0.99).sum())} verts attenuated")
else:
    att = np.ones(len(TERM))

D51 = D5 + TERM
fold_scan = {}
for name_, D in {"+1 (v5.1 combined)": D51,
                 "+0.5 (coupled)": 0.5 * (LIN5 + TERM) + (0.5 ** GAMMA) * SAG,
                 "+1 (v5 alone)": D5}.items():
    fold_scan[name_] = {b: flips_on(D, b) for b in BASES}
    print(f"fold scan {name_}: raw {fold_scan[name_]['raw']}, "
          f"macro {fold_scan[name_]['macro']}")

# ------------------------------------------------------------- QA metrics
qa = {"cal": CAL, "fboost": FBOOST,
      "fold_scan": {k: {b: {"flips": v[b][0], "min_dot": v[b][1]}
                                for b in BASES} for k, v in fold_scan.items()},
      "terminal_support_verts": int(supp.sum())}
for limb_name, s_t, gate_r, label in (
        ("arm_R", 0.72, 0.135, "wrist"), ("arm_L", 0.72, 0.135, "wrist_L"),
        ("leg_R", 0.84, 0.175, "ankle"), ("leg_L", 0.84, 0.175, "ankle_L")):
    gb = station_girth(mh_pos, limb_name, s_t, gate_r)
    g5 = station_girth(mh_pos + D5, limb_name, s_t, gate_r)
    g51 = station_girth(mh_pos + D51, limb_name, s_t, gate_r)
    qa[label] = {"base_cm": round(gb * 100, 2), "v5_cm": round(g5 * 100, 2),
                 "v51_cm": round(g51 * 100, 2),
                 "gain_v5_cm": round((g5 - gb) * 100, 2),
                 "gain_v51_cm": round((g51 - gb) * 100, 2)}
    print(f"{label}: base {gb*100:.1f} -> v5 {g5*100:.1f} -> v5.1 {g51*100:.1f} cm")

# proximal finger thickness gain (per digit, mean over prox segment)
finger_qa = {}
for sn, H in hands.items():
    for di, dg in enumerate(H["digits"]):
        vi = dg["verts"]; C = dg["centroid"]; ax = dg["axis"]
        rel = mh_pos[vi] - C
        t = rel @ ax
        rad = rel - t[:, None] * ax[None, :]
        rn = np.linalg.norm(rad, axis=1)
        prox = dg["seg"] == 1
        if prox.sum() < 5:
            continue
        disp = np.linalg.norm(TERM[vi][prox], axis=1)
        thick_gain = float((disp / np.maximum(rn[prox], 1e-6)).mean())
        # dorsal-palmar thickness gain over the prox segment: the
        # free direction (lateral growth is contact-capped by the
        # neighbouring fingers, ~1 mm gaps on this base)
        edp = hands[sn]["e_dp"]
        th_b = float(np.percentile(mh_pos[vi][prox] @ edp, 99)
                     - np.percentile(mh_pos[vi][prox] @ edp, 1))
        th_d = float(np.percentile((mh_pos + D51)[vi][prox] @ edp, 99)
                     - np.percentile((mh_pos + D51)[vi][prox] @ edp, 1))
        finger_qa[f"{sn}_digit{di}"] = {
            "n_prox": int(prox.sum()),
            "mean_radial_gain_mm": round(float(disp.mean() * 1000), 2),
            "thickness_gain_frac": round(thick_gain, 3),
            "dorsal_palmar_thickness_base_mm": round(th_b * 1000, 2),
            "dorsal_palmar_thickness_gain_frac": round(th_d / max(th_b, 1e-9) - 1, 3)}
print("finger prox thickness:", json.dumps(finger_qa))

# inter-digit minimum distances (webbing collapse check)
inter = {}
for sn, H in hands.items():
    digs = [dg["verts"] for dg in H["digits"] if len(dg["verts"]) >= 12]
    mins_b, mins_d, close_b, close_d, sep_b, sep_d = [], [], [], [], [], []
    for i in range(len(digs)):
        for j in range(i + 1, len(digs)):
            A_, B_ = digs[i], digs[j]
            tb = cKDTree(mh_pos[B_])
            db, _ = tb.query(mh_pos[A_], k=1)
            td = cKDTree((mh_pos + D51)[B_])
            dd, _ = td.query((mh_pos + D51)[A_], k=1)
            mins_b.append(float(db.min())); mins_d.append(float(dd.min()))
            close_b.append(int((db < 0.0003).sum()))
            close_d.append(int((dd < 0.0003).sum()))
            sep_b.append(float(np.linalg.norm(mh_pos[A_].mean(0) - mh_pos[B_].mean(0))))
            sep_d.append(float(np.linalg.norm((mh_pos + D51)[A_].mean(0)
                                              - (mh_pos + D51)[B_].mean(0))))
    if mins_b:
        # NOTE: hm08 fingers rest IN CONTACT (base pair mins ~0), so
        # the honest criteria are: no new sub-0.3 mm close pairs and
        # digit centroid separations preserved -- not a positive gap.
        inter[sn] = {"pairs": len(mins_b),
                     "base_min_mm": round(min(mins_b) * 1000, 2),
                     "v51_min_mm": round(min(mins_d) * 1000, 2),
                     "base_mean_of_pair_mins_mm": round(float(np.mean(mins_b)) * 1000, 2),
                     "v51_mean_of_pair_mins_mm": round(float(np.mean(mins_d)) * 1000, 2),
                     "close_pairs_lt_0.3mm_base": int(sum(close_b)),
                     "close_pairs_lt_0.3mm_v51": int(sum(close_d)),
                     "centroid_sep_ratio_min": round(min(d / max(b, 1e-9)
                                                         for b, d in zip(sep_b, sep_d)), 3)}
print("inter-digit mins:", json.dumps(inter))
qa["finger_prox_thickness"] = finger_qa
qa["inter_digit_min_dist"] = inter
qa["zone_gains_source"] = {"hand_perp_mean_mm": HS, "hand_perp_p90_mm": HS90,
                           "foot_perp_mean_mm": FS, "foot_perp_p90_mm": FS90,
                           "hand_scale": hand_scale, "foot_scale": foot_scale,
                           "gains_pre_cal_mm": {k: round(v * 1000, 2)
                                                for k, v in G.items()},
                           "ankle_ring_cap_mm": ANKLE_RING_CAP * 1000}

# ---------------------------------------------------------------- targets
NOTET = ("Provenance: TERMINAL component of body.belly.protrusion "
         "v5.1 (= combined v5.1 - combined v5). Stacks on the v5 "
         "combined target. Source: Fat Males malehands/malefeet "
         "measured deltas (learned library), zone-scaled. Study-only, "
         "internal - not a CC0 MakeHuman asset. See GRAVITY_V5.md "
         "v5.1 addendum.")
NOTE51 = ("Provenance: omniversal slider body.belly.protrusion v5.1 "
          "(whole-body adiposity incl. terminal tissue at hands/feet), "
          "instance makehuman_hm08. Combined field at w=+1: v5 system "
          "plus the terminal component. Study-only, internal.")
n_t = write_target(OUT / "body.belly.protrusion_terminal_v51.target", TERM, NOTET)
n_51 = write_target(OUT / "body.belly.protrusion_v5.1.target", D51, NOTE51)
print(f"targets written: terminal {n_t} moved verts, combined v5.1 {n_51}")
qa["moved_verts"] = {"terminal": n_t, "combined_v51": n_51}
np.savez(WORK / "belly_v51.npz", delta_v51_canonical_m=D51,
         terminal_canonical_m=TERM, lin_v51_canonical_m=LIN5 + TERM,
         sag_v5_canonical_m=SAG, gamma=GAMMA, cal=CAL)
(WORK / "qa_numbers_v51.json").write_text(json.dumps(qa, indent=1))
_frames = {sn: {"e_dp": hands[sn]["e_dp"].tolist(),
                "e_long": hands[sn]["e_long"].tolist(),
                "e_dp_foot": feet[sn]["e_up"].tolist()}
           for sn in hands}
(WORK / "hand_frames_v51.json").write_text(json.dumps(_frames, indent=1))
print("QA v5.1 saved")
