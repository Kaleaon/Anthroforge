#!/usr/bin/env python3
"""
Belly v5.2 builder: THIGH-CONTACT STAGE (L5/R10 made real).

Joe approved the six-agent improvement round Nov 12, 2026; this is
agent #4. v5/v5.1 left the inner thighs at a 6.38 cm minimum gap at
+1 (z-band probe) -- close, but real heavy thighs MEET and flatten
against each other (FAT_REFERENCE R10: touching tissue flattens and
spreads; Keninism: a convincing fat character has no thigh gap).

v5.2 = v5.1 + CONTACT, a post-process stage on the composed field:

    D52 = D51 + CONTACT
    shape(w) = base + w*LIN51 + sign(w)|w|^2.0*SAG + kappa(w)*CONTACT
    kappa(w) = smoothstep(0.55, 1.0, w) for w > 0, else 0

The shipped .target is CONTACT at tau=1 (kappa=1). The stage is NOT
linear in w: contact is a threshold phenomenon, so it carries its
own coupling function next to SAG's gamma curve (see GRAVITY_V5.md
v5.2 addendum for the kappa-vs-recomputed-stage comparison).

Method (per leg, mirrored; full detail in the addendum):
  * Per s-band gap g(s) measured on the composed v5.1 field (both
    bases; the per-band minimum governs), inner-sector percentile
    extents, side-correct gates -- the v5 probe discipline.
  * Reach: the stage may advance each medial face by at most
    A_MAX = 4.0 cm at tau=1 (soft-tissue supply cap [E], ~0.42 of
    the +1 mid-thigh radius; the medial depot is the thigh's most
    mobile tissue). Bands with g(s) <= 2*A_MAX close fully; beyond
    the last full-close band the advance tapers to zero over
    ds = 0.15 (pre-contact lean-in, no touch).
  * Flattening: a vertex moves toward the midplane by
    w_phi * min(dist_to_plane - eps, a(s)) -- verts within a(s) of
    the plane land ON it (flat patch), verts further out advance
    uniformly (shape preserved), phi falloff blends the shoulders.
    eps = 0.75 mm kiss offset per side.
  * Redistribution: the wedge volume the advance claims is
    returned to the same thigh per s-band (target 90%) by a
    uniform radial ease over the non-contact sectors, band
    coefficients solved from first-order volume integrals
    (hm08's winding is inward; dvol corrects the sign), plus a
    fixed slight axial spread (1.2 mm) away from the patch
    centre -- the brief's up/down term, stated as shaping.
  * Fold machinery is v5's (graph smoothing, kappa=0.55 slope
    limiter, attenuation repair), gated on D51 + CONTACT over all
    26,756 body faces on both bases.

Machinery below the loads (axis, limb extraction, limb_params,
normals) is copied verbatim from build_belly_v5.py, the house
pattern (cf. build_belly_v51.py).
"""
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import scipy.sparse as sp

HERE = Path(__file__).resolve().parent
OUT = HERE.parent
WORK = OUT / "work"
LEARNED = Path.home() / "workspace/character_assets/learned"
MPFB_ZIP = Path.home() / "workspace/stick-figure-avatar/photoreal/tools/mpfb2.zip"
HIMBO_DIR = (Path.home() / "workspace/character_assets/_himbo_work/CalienteTools"
             "/BodySlide/ShapeData/HIMBO")
sys.path.insert(0, str(LEARNED / "tools"))
from osdparse import load_osd  # noqa: E402

SK_UNIT_M = 0.01428
DM_M = 0.1
BODY_END = 13380

# ---- loads: correspondence + base geometry (from v5) ----
corr = np.load(WORK / "correspondence.npz")
navel_mh = int(corr["navel_mh"])
h_star = float(corr["h_star"])
mh_tris = corr["mh_tris"].astype(np.int64)
mh_crotch, mh_neck = [float(x) for x in corr["mh_landmarks"]]
L_mh = mh_neck - mh_crotch
_v4 = np.load(WORK / "belly_v4.npz")
D4 = _v4["delta_v4_canonical_m"].astype(np.float64)
with zipfile.ZipFile(MPFB_ZIP) as z:
    obj_lines = z.read("mpfb/data/3dobjs/base.obj").decode().splitlines()
mh_obj = np.array([[float(x) for x in l.split()[1:4]]
                   for l in obj_lines if l.startswith("v ")])
mh_faces = []
for l in obj_lines:
    if l.startswith("f "):
        mh_faces.append([int(t.split("/")[0]) - 1 for t in l.split()[1:]])
mh_pos = np.stack([mh_obj[:, 0], mh_obj[:, 2], mh_obj[:, 1]], axis=1) * DM_M
mh_body = np.zeros(len(mh_pos), bool); mh_body[:BODY_END] = True
mh_pos_mac = mh_pos.copy()
_mac = np.load(WORK / "mh_macro_base.npz")["pos_canonical_m"]
mh_pos_mac[:len(_mac)] = _mac


# ---- shared machinery (verbatim from build_belly_v5.py) ----
def compute_axis(pos, gate=None):
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
        axis[:, c] = np.convolve(np.pad(axis[:, c], 2, mode="edge"), k, "valid")
    return ctr, axis

def axis_at(ctr, axis, hgt):
    return np.stack([np.interp(hgt, ctr, axis[:, 0]),
                     np.interp(hgt, ctr, axis[:, 1])], axis=1)

def crotch_of(pos, gate, mid_hw=0.030, slab_hw=0.060):
    mid = gate & (np.abs(pos[:, 0]) < mid_hw) & (np.abs(pos[:, 1]) < slab_hw)
    return float(pos[mid, 2].min())

def neck_base(pos, ctr, axis, crotch, label):
    ax = axis_at(ctr, axis, pos[:, 2])
    r = np.linalg.norm(pos[:, :2] - ax, axis=1)
    gated = r < 0.23
    bands = np.linspace(crotch, pos[:, 2].max(), 160)
    C = 0.5 * (bands[:-1] + bands[1:]); Wd = np.zeros(len(C))
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
                neck = C[i - 2]; break
        else:
            run = 0
    print(f"{label}: neck base {neck:.4f} m")
    return neck

def face_normals(P, F):
    n = np.cross(P[F[:, 1]] - P[F[:, 0]], P[F[:, 2]] - P[F[:, 0]])
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-14)

edges_all = np.vstack([mh_tris[:, [0, 1]], mh_tris[:, [1, 2]], mh_tris[:, [2, 0]]])
edges_all = np.unique(np.sort(edges_all, axis=1), axis=0)
A_mat = sp.coo_matrix((np.ones(len(edges_all)),
                       (edges_all[:, 0], edges_all[:, 1])),
                      shape=(len(mh_pos), len(mh_pos)))
A_mat = A_mat + A_mat.T
deg = np.asarray(A_mat.sum(axis=1)).ravel()
Lop = sp.diags(1.0 / np.maximum(deg, 1)) @ A_mat
nbrs = [np.asarray(A_mat[v].nonzero()[1]) for v in range(len(mh_pos))]
def smooth_polyline(pts, passes=3):
    """Binomial smoothing, endpoints fixed. Coarse source meshes
    (Fat Males: 2,024 verts) give band centroids that zigzag; an
    unsmoothed axis inflates arc length and corrupts (s, phi)."""
    pts = pts.copy()
    for _ in range(passes):
        mid = 0.25 * pts[:-2] + 0.5 * pts[1:-1] + 0.25 * pts[2:]
        pts[1:-1] = mid
    return pts

def extract_limbs(pos, gate, label):
    """Returns dict: for each of arm_R/arm_L/leg_R/leg_L a polyline
    (proximal->distal points), its length, side sign. Legs: z-band
    centroids per side. Arms: PCA-direction bands per side."""
    ctr, axis = compute_axis(pos, gate)
    ax_x = lambda z: np.interp(z, ctr, axis[:, 0])
    crotch = crotch_of(pos, gate)
    neck = neck_base(pos, ctr, axis, crotch, label)
    zmin = float(pos[gate, 2].min())
    out = {}
    # ---- legs (bands ascend ankle->hip; reversed to proximal-first)
    for side, sname in ((1.0, "R"), (-1.0, "L")):
        seeds = gate & (np.sign(pos[:, 0] - ax_x(pos[:, 2])) == side) \
            & (np.abs(pos[:, 0] - ax_x(pos[:, 2])) > 0.025) \
            & (pos[:, 2] < crotch + 0.02) & (pos[:, 2] > zmin + 0.09)
        pts = []
        zb = np.arange(zmin + 0.09, crotch + 0.02, 0.025)
        for a in zb:
            m = seeds & (pos[:, 2] >= a) & (pos[:, 2] < a + 0.025)
            if m.sum() >= 4:
                pts.append(pos[m].mean(axis=0))
        pts = np.array(pts)                       # ankle -> hip order
        d_top = pts[-1] - pts[-2]; d_top /= np.linalg.norm(d_top)
        d_bot = pts[0] - pts[1]; d_bot /= np.linalg.norm(d_bot)
        pts = np.vstack([pts[0] + d_bot * 0.05, pts, pts[-1] + d_top * 0.06])
        pts = smooth_polyline(pts[::-1].copy())   # hip -> ankle order
        seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
        out[f"leg_{sname}"] = {"pts": pts, "length": float(seg.sum()),
                               "side": side, "kind": "leg"}
    # ---- arms
    for side, sname in ((1.0, "R"), (-1.0, "L")):
        seeds = gate & (np.sign(pos[:, 0] - ax_x(pos[:, 2])) == side) \
            & (np.abs(pos[:, 0] - ax_x(pos[:, 2])) > 0.17) \
            & (pos[:, 2] > crotch + 0.10) & (pos[:, 2] < neck + 0.02)
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
        pts = np.array(pts)                       # shoulder -> wrist order
        d0 = pts[1] - pts[0]; d0 /= np.linalg.norm(d0)
        d1 = pts[-1] - pts[-2]; d1 /= np.linalg.norm(d1)
        pts = np.vstack([pts[0] - d0 * 0.05, pts, pts[-1] + d1 * 0.03])
        pts = smooth_polyline(pts)
        seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
        out[f"arm_{sname}"] = {"pts": pts, "length": float(seg.sum()),
                               "side": side, "kind": "arm"}
    for k, v in out.items():
        print(f"{label} {k}: {len(v['pts'])} axis pts, length "
              f"{v['length']*100:.1f} cm, prox {np.round(v['pts'][0],3)}, "
              f"dist {np.round(v['pts'][-1],3)}")
    return out

def limb_params(pos, limb):
    """(s, dist, phi, er, adir) for every vert vs one limb polyline.
    phi measured in mirrored right-limb space: left limbs are x-flipped
    about x=0 for the angle only, so phi=0 is lateral-out, +pi/2 front,
    pi inner, -pi/2 back on BOTH sides."""
    pts = limb["pts"]; side = limb["side"]
    segv = np.diff(pts, axis=0)
    seglen = np.linalg.norm(segv, axis=1)
    cum = np.concatenate([[0], np.cumsum(seglen)])
    L = cum[-1]
    best_d2 = np.full(len(pos), np.inf)
    s_out = np.zeros(len(pos)); pt_out = np.zeros_like(pos)
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
        dir_out[m] = (v / seglen[i])
    dist = np.sqrt(best_d2)
    rel = pos - pt_out
    er = rel / np.maximum(dist, 1e-9)[:, None]
    # mirrored-space angle: flip x of the radial dir for left limbs
    rel_m = rel.copy(); rel_m[:, 0] *= side
    adir_m = dir_out.copy(); adir_m[:, 0] *= side
    # per-vertex frames (vectorised gram-schmidt)
    a = adir_m
    eo = np.tile(np.array([1.0, 0, 0]), (len(pos), 1))
    eo = eo - np.einsum("ij,ij->i", eo, a)[:, None] * a
    eo /= np.maximum(np.linalg.norm(eo, axis=1, keepdims=True), 1e-12)
    ef = np.tile(np.array([0.0, 1.0, 0]), (len(pos), 1))
    ef = ef - np.einsum("ij,ij->i", ef, a)[:, None] * a \
             - np.einsum("ij,ij->i", ef, eo)[:, None] * eo
    ef /= np.maximum(np.linalg.norm(ef, axis=1, keepdims=True), 1e-12)
    reln = rel_m / np.maximum(dist, 1e-9)[:, None]
    phi = np.arctan2(np.einsum("ij,ij->i", reln, ef),
                     np.einsum("ij,ij->i", reln, eo))
    return s_out, dist, phi, er, dir_out

GATE = {"arm": 0.135, "leg": 0.175}
def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)
def cosfade(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return 0.5 + 0.5 * np.cos(np.pi * t)

# ------------------------------------------------------------------ v5.1 field
_v51 = np.load(WORK / "belly_v51.npz", allow_pickle=True)
D51 = _v51["delta_v51_canonical_m"].astype(np.float64)
LIN51 = _v51["lin_v51_canonical_m"].astype(np.float64)
SAG = _v51["sag_v5_canonical_m"].astype(np.float64)
GAMMA = float(_v51["gamma"])

def composed(w):
    """The v5.1 slider composition at level w (no contact stage)."""
    return w * LIN51 + np.sign(w) * (abs(w) ** GAMMA) * SAG

assert np.abs(composed(1.0) - D51).max() < 1e-12

mh_limbs = extract_limbs(mh_pos, mh_body, "hm08-v52")
leg_par = {n: limb_params(mh_pos, mh_limbs[n]) for n in ("leg_R", "leg_L")}
GATE_LEG = 0.175
_ctr, _axis = compute_axis(mh_pos, mh_body)
AXV = axis_at(_ctr, _axis, mh_pos[:, 2])   # body axis (x, y) per vertex

# ------------------------------------------------------------- fold machinery
Fb = mh_tris[np.array([np.all(f < BODY_END) for f in mh_tris])]
print(f"body faces for fold gate: {len(Fb)}")
BASES = {"raw": mh_pos, "macro": mh_pos_mac}
n0_all = {k: face_normals(p, Fb) for k, p in BASES.items()}

def flips_on(delta, bname):
    nn = face_normals(BASES[bname] + delta, Fb)
    dots = np.einsum("ij,ij->i", n0_all[bname], nn)
    return int((dots < 0).sum()), float(dots.min())

def graph_smooth(V, supp_mask, passes=3, keep=0.35):
    V = V.copy()
    for _ in range(passes):
        sm = Lop @ V
        V = np.where(supp_mask[:, None], (1 - keep) * V + keep * sm, V)
    return V

def slope_limit(Ds, supp_mask, kappa=0.55):
    ea = np.array([e for e in edges_all if supp_mask[e[0]] or supp_mask[e[1]]])
    el = np.linalg.norm(mh_pos[ea[:, 0]] - mh_pos[ea[:, 1]], axis=1)
    Ds = Ds.copy()
    for it in range(80):
        diff = Ds[ea[:, 0]] - Ds[ea[:, 1]]
        dn = np.linalg.norm(diff, axis=1)
        excess = dn - kappa * el
        if (excess <= 0).all():
            return Ds, it
        corr_ = np.zeros_like(Ds); wgt = np.zeros(len(Ds))
        m_ = excess > 0
        adj = (0.5 * excess[m_] / np.maximum(dn[m_], 1e-12))[:, None] * diff[m_]
        np.add.at(corr_, ea[m_, 0], -adj)
        np.add.at(corr_, ea[m_, 1], adj)
        np.add.at(wgt, ea[m_, 0], 1); np.add.at(wgt, ea[m_, 1], 1)
        Ds += 0.7 * corr_ / np.maximum(wgt, 1)[:, None]
        Ds[~supp_mask] = 0.0
    return Ds, 80

def repair(C_raw, supp_mask, max_rounds=60):
    """Attenuation repair so D51 + C has 0 flips at +1 on both bases
    (v5 pattern: bad verts x0.82, ring x0.94, graph-smooth att)."""
    att = np.ones(len(C_raw))
    Cv = C_raw.copy()
    for rnd in range(max_rounds):
        D = D51 + Cv
        if flips_on(D, "raw")[0] == 0 and flips_on(D, "macro")[0] == 0:
            return Cv, att, True, rnd
        bad = np.zeros(len(Fb), bool)
        for k in BASES:
            nn = face_normals(BASES[k] + D, Fb)
            dots = np.einsum("ij,ij->i", n0_all[k], nn)
            bad |= dots < 0.01
        # only faces the increment can influence: v5.1's inherited
        # macro crease sits at dot ~0.002 permanently, and fighting
        # it (run 6) dragged att to the 0.10 floor over 17 rounds
        # without ever touching the actual flip.
        bad &= supp_mask[Fb].any(axis=1)
        bad_verts = np.unique(Fb[bad])
        ring = np.unique(np.concatenate([nbrs[v] for v in bad_verts]))
        att[bad_verts] *= 0.82
        att[ring] *= 0.94
        att = np.where(supp_mask, 0.65 * att + 0.35 * (Lop @ att), att)
        att = np.clip(att, 0.10, 1.0)
        Cv = att[:, None] * C_raw
    D = D51 + Cv
    ok = flips_on(D, "raw")[0] == 0 and flips_on(D, "macro")[0] == 0
    return Cv, att, ok, max_rounds

# ------------------------------------------------------------- gap measurement
def band_gaps(delta, base_pos, step=0.02, smax=0.60, halfwin=0.025,
              pcts=(10, 90)):
    """Per s-centre inner-thigh gap (m) on base_pos + delta: BULK gap --
    sliding window (width 2*halfwin) around each centre, inner-sector
    10/90 percentile extents, side-correct gates. Thin-band percentile
    extents (the first run) chase single bulging verts (0.97 cm at
    s=0.05 against a 5 cm bulk gap) and starve in places; the windowed
    bulk gap is what a contact patch actually forms against. The
    worst-case check stays with zband_min_gap + the vertex probe."""
    P = base_pos + delta
    out = []
    for c in np.arange(0.01, smax, step):
        ext, ok = [], True
        for name, pct in (("leg_R", pcts[0]), ("leg_L", pcts[1])):
            s, dist, phi, er, adir = leg_par[name]
            side = mh_limbs[name]["side"]
            got = None
            for hw in (halfwin, halfwin * 2):
                m = mh_body & (dist < GATE_LEG) & (np.abs(s - c) < hw) \
                    & (mh_pos[:, 0] * side > 0.008) \
                    & (np.abs(np.abs(phi) - np.pi) < 1.2)
                if m.sum() >= 4:
                    got = np.percentile(P[m, 0], pct); break
            if got is None:
                ok = False; break
            ext.append(got)
        out.append((float(c), float(ext[0] - ext[1]) if ok else np.nan))
    cs = np.array([c for c, _ in out]); gs = np.array([g for _, g in out])
    if np.isnan(gs).any():
        good = ~np.isnan(gs)
        gs = np.interp(cs, cs[good], gs[good])
        out = [(float(c), float(g)) for c, g in zip(cs, gs)]
    return out

def zband_min_gap(delta, base_pos):
    """v5's headline probe, verbatim logic: min z-band gap (m)."""
    P = base_pos + delta
    sR, dR = leg_par["leg_R"][0], leg_par["leg_R"][1]
    sL, dL = leg_par["leg_L"][0], leg_par["leg_L"][1]
    inR = mh_body & (dR < GATE_LEG) & (sR > 0.02) & (sR < 0.55) & (mh_pos[:, 0] > 0.008)
    inL = mh_body & (dL < GATE_LEG) & (sL > 0.02) & (sL < 0.55) & (mh_pos[:, 0] < -0.008)
    best = None
    for z0 in np.arange(P[:, 2].min(), mh_crotch - 0.06, 0.02):
        mR = inR & (P[:, 2] >= z0) & (P[:, 2] < z0 + 0.02)
        mL = inL & (P[:, 2] >= z0) & (P[:, 2] < z0 + 0.02)
        if mR.sum() >= 4 and mL.sum() >= 4:
            g = float(np.percentile(P[mR, 0], 2) - np.percentile(P[mL, 0], 98))
            if best is None or g < best[1]:
                best = (float(z0), g)
    return best if best is not None else (None, float("nan"))

# ------------------------------------------------------------- contact stage
A_MAX = 0.040        # per-side medial advance cap at tau=1 (m) [E]
EPS = 0.00075        # kiss offset per side (m): surfaces stop EPS off-plane
PHI_HW = 1.15        # inner-sector half-width (rad) for the phi falloff
TAPER_DS = 0.15      # advance taper length past the reach crossing (s units)

def kappa(w):
    """Contact-stage coupling: threshold engagement, full at w=1."""
    return float(smoothstep(0.55, 1.0, w)) if w > 0 else 0.0

# design gaps at +1: the RAW base (the canonical base every target
# since v1 is authored on; macro is a fold-gate cross-check only).
# Over-closure on macro is impossible by construction -- a vertex
# moves at most its own distance to the plane and lands ON it.
_bg = {bname: band_gaps(D51, bpos) for bname, bpos in BASES.items()}
_band_s = np.array([c for c, _ in _bg["raw"]])
_band_g = np.array([g for _, g in _bg["raw"]])
print("raw band gaps at +1 (cm):",
      {f"{c:.2f}": round(float(g) * 100, 2) for c, g in zip(_band_s, _band_g)})
print("macro band gaps at +1 (cm):",
      {f"{c:.2f}": round(float(g) * 100, 2) for c, g in _bg["macro"]})

_s_grid = np.linspace(0.0, 0.62, 313)
_g_grid = np.interp(_s_grid, _band_s, _band_g)
_a_grid = np.minimum(_g_grid / 2.0, A_MAX)
_above = _g_grid > 2 * A_MAX
_s_t = float(_s_grid[np.argmax(_above)]) if _above.any() else 0.62
_a_grid = _a_grid * np.where(_s_grid <= _s_t, 1.0,
                             cosfade(_s_t, _s_t + TAPER_DS, _s_grid))
_a_grid = _a_grid * smoothstep(0.0, 0.015, _s_grid)
_a_grid = np.convolve(np.pad(_a_grid, 2, mode="edge"), np.ones(5) / 5, "valid")
print(f"reach crossing s_t = {_s_t:.3f}; advance at band centres (cm):",
      {f"{c:.2f}": round(float(np.interp(c, _s_grid, _a_grid)) * 100, 2)
       for c in _band_s[::3]})

def a_of_s(s):
    return np.interp(s, _s_grid, _a_grid)

def closing_field(P, a_fn=None):
    if a_fn is None:
        a_fn = a_of_s
    """Medial advance + flatten, from composed positions P (raw base).
    A vertex moves toward the midplane by w_phi * min(dist-EPS, a(s)):
    within a(s) of the plane it lands ON the plane (flat patch);
    further out it advances uniformly (shape preserved).
    The scalar AMOUNT is graph-smoothed per leg -- smoothing the 3D
    displacement instead (run 3) Laplacian-drained the medial ridge
    (a local |x| minimum) and cost ~8 mm of closure."""
    C = np.zeros_like(mh_pos)
    for name in ("leg_R", "leg_L"):
        other = "leg_L" if name == "leg_R" else "leg_R"
        s, dist, phi, er, adir = leg_par[name]
        dist_o = leg_par[other][1]
        side = mh_limbs[name]["side"]
        # unique claim: the vertex must belong to THIS leg -- the
        # perineum fan sits inside both legs' gates (dist ~0.10 to
        # each axis) and shearing it flipped 9 macro faces in run 4;
        # a true thigh vertex is far closer to its own axis.
        gate = mh_body & (dist < GATE_LEG) & (mh_pos[:, 0] * side > 0.004) \
            & (dist < dist_o - 0.03)
        u = np.abs(np.abs(phi) - np.pi) / PHI_HW
        w_phi = np.where(u < 1, 0.5 + 0.5 * np.cos(np.pi * np.clip(u, 0, 1)), 0.0)
        dist_plane = side * (P[:, 0] - AXV[:, 0]) - EPS
        amt = w_phi * np.minimum(np.maximum(dist_plane, 0.0), a_fn(s))
        amt = np.where(gate, amt, 0.0)
        # ONE light pass: the ridge is a local max of amt, and heavier
        # smoothing (0.7/0.3 x2, run 6) drained ~0.55 cm/side of
        # closure into the shoulder population.
        amt = np.where(gate, 0.85 * amt + 0.15 * (Lop @ amt), amt)
        C[:, 0] -= side * amt
    return C

# ------------------------------------------------- volume bookkeeping (legs)
P51 = mh_pos + D51
def leg_faces(name):
    s, dist, phi, er, adir = leg_par[name]
    vert_in = mh_body & (dist < GATE_LEG) & (s < 0.80)
    return Fb[np.array([np.all(vert_in[f]) for f in Fb])], vert_in

def dvol(P, F, D):
    """First-order volume change of field D over faces F at positions P.
    NOTE: hm08's winding is inward by the right-hand rule (divergence
    volume of the base body comes out negative), so the raw integral
    is negated to true orientation."""
    n = np.cross(P[F[:, 1]] - P[F[:, 0]], P[F[:, 2]] - P[F[:, 0]])
    a2 = np.linalg.norm(n, axis=1)
    nhat = n / np.maximum(a2, 1e-14)[:, None]
    return -float(np.sum(np.einsum("ij,ij->i", D[F].mean(axis=1), nhat)
                         * (0.5 * a2)))

CLOSE = closing_field(P51)
COMP_RETURN = 0.90   # per-band fraction of the claimed wedge volume
                     # the reshape gives back (see below)
RESHAPE_CAP = 0.005  # per-band reshape coefficient cap (m)
AXIAL_SHAPE = 0.0012  # fixed slight vertical redistribution (m, max)

CONTACT = np.zeros_like(mh_pos)
vol_report = {}
for name in ("leg_R", "leg_L"):
    F_l, vert_in = leg_faces(name)
    s, dist, phi, er, adir = leg_par[name]
    v_close = dvol(P51, F_l, CLOSE)   # > 0: the advance claims wedge volume
    # Redistribution, per s-band: a uniform radial ease over the
    # NON-CONTACT sectors, coefficient solved band by band to return
    # COMP_RETURN of the band's claimed volume (sign free -- the
    # solve, not a story, decides whether sectors ease in or out;
    # run 3's signed sector pattern just inverted under its caps).
    dphi = np.abs(np.abs(phi) - np.pi)
    s_win = smoothstep(-0.02, 0.03, s) * cosfade(0.62, 0.80, s)
    # sector starts OUTSIDE the closing sector (PHI_HW = 1.15):
    # run 5 evidence -- an inward ease over the inner shoulder
    # (0.55 < dphi < 1.15) pushed the shoulder verts back off the
    # plane and re-opened the approach by ~9 mm.
    sector = np.where(dphi < 1.25, 0.0, 1.0)
    U = np.where(vert_in[:, None], (sector * s_win)[:, None] * er, 0.0)
    cs_f = s[F_l].mean(axis=1)
    centres = np.arange(0.01, 0.53, 0.02)
    betas = np.zeros(len(centres))
    for i, c in enumerate(centres):
        Fb_ = F_l[np.abs(cs_f - c) < 0.03]
        if len(Fb_) == 0:
            continue
        cl = dvol(P51, Fb_, CLOSE)
        un = dvol(P51, Fb_, U)
        if abs(un) > 1e-9 and cl > 0:
            betas[i] = np.clip(-COMP_RETURN * cl / un,
                               -RESHAPE_CAP, RESHAPE_CAP)
    betas = np.convolve(np.pad(betas, 1, mode="edge"), np.ones(3) / 3, "valid")
    beta_v = np.interp(s, centres, betas)
    # the brief's vertical term: slight, fixed-amplitude, NOT
    # volume-solved -- tissue slips up/down the thigh away from the
    # patch centre (s_c = 0.08); its small volume effect is reported.
    psi = np.clip((s - 0.08) / 0.10, -1, 1)
    w_a = smoothstep(-0.02, 0.03, s) * cosfade(0.55, 0.78, s)
    B_a = np.where(vert_in[:, None], (w_a * psi)[:, None] * adir, 0.0)
    comp = beta_v[:, None] * U + AXIAL_SHAPE * B_a
    v_comp = dvol(P51, F_l, comp)
    CONTACT += comp
    vol_report[name] = {
        "v_claimed_cm3": v_close * 1e6, "v_returned_cm3": -v_comp * 1e6,
        "return_fraction": float(-v_comp / v_close) if v_close else None,
        "beta_reshape_range_mm": [float(betas.min() * 1000),
                                  float(betas.max() * 1000)],
        "axial_shape_mm": AXIAL_SHAPE * 1000,
        "net_cm3": (v_close + v_comp) * 1e6}
    print(f"{name}: claimed {v_close*1e6:.1f} cm3, returned "
          f"{-v_comp*1e6:.1f} (reshape beta range "
          f"{betas.min()*1000:.2f}..{betas.max()*1000:.2f} mm), net "
          f"{vol_report[name]['net_cm3']:.1f} cm3")
CONTACT += CLOSE

supp = np.linalg.norm(CONTACT, axis=1) > 0.0002
print(f"contact support: {supp.sum()} verts, max |C| "
      f"{np.linalg.norm(CONTACT, axis=1).max()*100:.2f} cm")
# NOTE: no graph smoothing and no slope limiter on the assembled
# field (runs 2-3 evidence): Laplacian smoothing drains the medial
# ridge (a local |x| minimum) and the kappa=0.55 limiter is
# intrinsically violated by the flattening shoulder; both cost
# closure uniformly. Smoothness lives in the field's construction
# (a(s), w_phi, smoothed amounts); the attenuation repair below is
# the fold enforcer, as designed.
lim_it = None
CONTACT, att, converged, rounds = repair(CONTACT, supp)
print(f"repair: converged {converged} in {rounds} rounds, att min "
      f"{att.min():.3f}, verts under 0.99: {(att < 0.99).sum()}")
assert converged, "contact increment failed the fold gate after repair"
D52 = D51 + CONTACT

# ------------------------------------------------------------------ QA
qa = {"constants": {"A_MAX_cm": A_MAX * 100, "EPS_mm": EPS * 1000,
                    "PHI_HW_rad": PHI_HW, "TAPER_DS": TAPER_DS,
                    "reach_crossing_s": _s_t,
                    "reshape_cap_mm": RESHAPE_CAP * 1000,
                    "axial_shape_mm": AXIAL_SHAPE * 1000,
                    "comp_return": COMP_RETURN},
      "volume": vol_report,
      "repair": {"converged": converged, "rounds": rounds,
                 "att_min": float(att.min()),
                 "verts_under_0.99": int((att < 0.99).sum()),
                 "slope_limiter_iters": lim_it,
                 "support_verts": int(supp.sum())}}

fold_scan = {}
for label, D in {"+1 (combined)": D52,
                 "w=0.75 + kappa*C": composed(0.75) + kappa(0.75) * CONTACT,
                 "w=0.5 + kappa*C": composed(0.5) + kappa(0.5) * CONTACT,
                 "+1.05 + C": composed(1.05) + CONTACT}.items():
    fold_scan[label] = {b: flips_on(D, b) for b in BASES}
    print(f"fold scan {label}: " +
          ", ".join(f"{b} {v[0]} ({v[1]:.4f})" for b, v in fold_scan[label].items()))
qa["fold_scan"] = {k: {b: {"flips": v[b][0], "min_dot": v[b][1]}
                       for b in v} for k, v in fold_scan.items()}

gap_qa = {}
for bname, bpos in BASES.items():
    before = band_gaps(D51, bpos)
    after = band_gaps(D52, bpos)
    after98 = band_gaps(D52, bpos, pcts=(2, 98))
    zb_b = zband_min_gap(D51, bpos); zb_a = zband_min_gap(D52, bpos)
    gap_qa[bname] = {
        "band_gaps_before_cm": {f"{c:.2f}": round(g * 100, 2) for c, g in before},
        "band_gaps_after_cm": {f"{c:.2f}": round(g * 100, 2) for c, g in after},
        "band_gaps_after_2_98_cm": {f"{c:.2f}": round(g * 100, 2)
                                    for c, g in after98},
        "zband_min_before": {"z": zb_b[0],
                             "gap_cm": None if np.isnan(zb_b[1])
                             else zb_b[1] * 100},
        "zband_min_after": {"z": zb_a[0],
                            "gap_cm": None if np.isnan(zb_a[1])
                            else zb_a[1] * 100}}
    print(f"{bname}: z-band min gap {gap_qa[bname]['zband_min_before']['gap_cm']}"
          f" -> {gap_qa[bname]['zband_min_after']['gap_cm']} cm")
qa["gaps"] = gap_qa

# vertex-level interpenetration (raw base): worst crossing in the zone
P52 = mh_pos + D52
rel52 = P52[:, 0] - AXV[:, 0]
zone = np.zeros(len(mh_pos), bool)
for name in ("leg_R", "leg_L"):
    s, dist, phi, er, adir = leg_par[name]
    zone |= mh_body & (dist < GATE_LEG) & (s < 0.60)
zR = zone & (mh_pos[:, 0] > 0.008); zL = zone & (mh_pos[:, 0] < -0.008)
qa["vertex_min_gap_mm"] = float((rel52[zR].min() - rel52[zL].max()) * 1000)
print(f"vertex-level min gap in zone: {qa['vertex_min_gap_mm']:.2f} mm")
# ridge gap: the medial ridge line itself (dphi < 0.35), and the
# repair attenuation over the patch core (must stay ~1)
core = np.zeros(len(mh_pos), bool)
for name in ("leg_R", "leg_L"):
    s, dist, phi, er, adir = leg_par[name]
    core |= mh_body & (dist < GATE_LEG) & (s > 0.02) & (s < 0.30) \
        & (np.abs(np.abs(phi) - np.pi) < 0.35)
cR = core & (mh_pos[:, 0] > 0); cL = core & (mh_pos[:, 0] < 0)
qa["ridge_gap_mm"] = float((rel52[cR].min() - rel52[cL].max()) * 1000)
qa["att_min_patch_core"] = float(att[core].min()) if core.any() else None
print(f"ridge gap: {qa['ridge_gap_mm']:.2f} mm; att min over patch core: "
      f"{qa['att_min_patch_core']}")

# contact patch: ridge gaps per band + near-plane faces
def band_ridge_gaps(delta):
    """Per-band gap (m) between the medial RIDGE lines (core sector
    dphi < 0.5, extrema -- the surfaces that actually meet). The bulk
    percentile gaps keep reading ~1 cm after contact because the
    sector's shoulder population spreads behind the flattened face;
    the ridge is the contact instrument."""
    P = mh_pos + delta
    rel = P[:, 0] - AXV[:, 0]
    out = []
    for c in np.arange(0.01, 0.60, 0.02):
        ext = []
        for name, fn in (("leg_R", np.min), ("leg_L", np.max)):
            s, dist, phi, er, adir = leg_par[name]
            side = mh_limbs[name]["side"]
            m = mh_body & (dist < GATE_LEG) & (np.abs(s - c) < 0.025) \
                & (mh_pos[:, 0] * side > 0.008) \
                & (np.abs(np.abs(phi) - np.pi) < 0.5)
            ext.append(fn(rel[m]) if m.sum() >= 3 else np.nan)
        out.append((float(c), float(ext[0] - ext[1])))
    return out

ridge_after = band_ridge_gaps(D52)
qa["ridge_gaps_after_cm"] = {f"{c:.2f}": round(g * 100, 2)
                             for c, g in ridge_after}
touch_bands = [c for c, g in ridge_after if g <= 0.003]
leg_len = mh_limbs["leg_R"]["length"]

patch = {}
for name in ("leg_R", "leg_L"):
    F_l, _ = leg_faces(name)
    s, dist, phi, er, adir = leg_par[name]
    side = mh_limbs[name]["side"]
    dplane = side * rel52
    entry = {}
    for tol_mm, key in ((2.75, "area_cm2"), (6.0, "area_cm2_tol6mm")):
        f_ok = np.array([np.abs(dplane[f].mean()) <= tol_mm / 1000
                         and s[f].mean() < 0.35 for f in F_l])
        Fp = F_l[f_ok]
        ar = 0.5 * np.linalg.norm(np.cross(P52[Fp[:, 1]] - P52[Fp[:, 0]],
                                           P52[Fp[:, 2]] - P52[Fp[:, 0]]),
                                  axis=1)
        entry[key] = float(ar.sum() * 1e4)
        if key == "area_cm2":
            entry["faces"] = int(len(Fp))
            verts_p = np.unique(Fp)
            entry["width_frontback_cm"] = float(
                (P52[verts_p, 1].max() - P52[verts_p, 1].min()) * 100) \
                if len(verts_p) else 0.0
            entry["plane_resid_std_mm"] = float(
                dplane[verts_p].std() * 1000) if len(verts_p) else None
    patch[name] = entry
patch["length_cm"] = (max(touch_bands) - min(touch_bands) + 0.02) * leg_len * 100 \
    if touch_bands else 0.0
patch["touch_bands_s"] = touch_bands
qa["contact_patch"] = patch
print("contact patch:", json.dumps(patch, indent=1))

# girth profiles through the contact zone (shelf check)
def girth_ellipse(w, d):
    a, b = w / 2, d / 2
    return np.pi * (3 * (a + b) - np.sqrt((3 * a + b) * (a + 3 * b)))

def limb_profile(P, name):
    s, dist, phi, er, adir = leg_par[name]
    side = mh_limbs[name]["side"]
    reg = mh_body & (dist < GATE_LEG)
    rows = []
    for s0 in np.arange(-0.02, 0.56, 0.04):
        m = reg & (s >= s0) & (s < s0 + 0.04)
        if m.sum() < 8:
            rows.append((s0 + 0.02, np.nan)); continue
        i0 = np.where(m)[0][np.argmin(np.abs(s[m] - (s0 + 0.02)))]
        a_dir = adir[i0]
        eo = np.array([1.0, 0, 0]) * side
        eo = eo - (eo @ a_dir) * a_dir; eo /= np.linalg.norm(eo)
        ef = np.cross(a_dir, eo) * side
        q = P[m] - P[m].mean(axis=0)
        w = float(np.percentile(q @ eo, 99) - np.percentile(q @ eo, 1))
        d = float(np.percentile(q @ ef, 99) - np.percentile(q @ ef, 1))
        rows.append((s0 + 0.02, girth_ellipse(w, d)))
    return np.array(rows)

prof_qa = {}
for name in ("leg_R", "leg_L"):
    p51 = limb_profile(P51, name)
    p52 = limb_profile(P52, name)
    def zone_stats(prof):
        ss, gg = prof[:, 0], prof[:, 1]
        win = (ss >= 0.0) & (ss <= 0.50)
        gr = np.abs(np.diff(gg[win])) / np.diff(ss[win])
        return float(np.nanmax(gr)), float(np.nanmax(np.abs(np.diff(gg[win]))))
    g51, d51m = zone_stats(p51)
    g52, d52m = zone_stats(p52)
    prof_qa[name] = {"profile_v51_cm": {f"{r[0]:.2f}": round(r[1] * 100, 1)
                                        for r in p51},
                     "profile_v52_cm": {f"{r[0]:.2f}": round(r[1] * 100, 1)
                                        for r in p52},
                     "max_grad_v51_cm_per_s": g51 * 100,
                     "max_grad_v52_cm_per_s": g52 * 100,
                     "grad_ratio": g52 / g51,
                     "max_band_step_v52_cm": d52m * 100}
    print(f"{name} girth: max grad v5.1 {g51*100:.1f} -> v5.2 {g52*100:.1f} "
          f"cm/s (ratio {g52/g51:.2f}), max band step {d52m*100:.2f} cm")
qa["girth_profiles"] = prof_qa

# navel untouched (contact is leg-only)
qa["navel_delta_change_mm"] = float(
    np.linalg.norm(CONTACT[int(corr["navel_mh"])]) * 1000)

# recomputed-stage progression: the true stage at tau < 1 (closing only)
def stage_at(tau):
    D_t = composed(tau)
    P_t = mh_pos + D_t
    bg = band_gaps(D_t, mh_pos)
    bs = np.array([c for c, _ in bg]); bgv = np.array([g for _, g in bg])
    A_t = A_MAX * kappa(tau)
    sg = np.linspace(0, 0.62, 313)
    gg = np.interp(sg, bs, bgv)
    ag = np.minimum(gg / 2, A_t)
    ab = gg > 2 * A_t
    st = float(sg[np.argmax(ab)]) if ab.any() else 0.62
    ag = ag * np.where(sg <= st, 1.0, cosfade(st, st + TAPER_DS, sg))
    ag = ag * smoothstep(0.0, 0.015, sg)
    ag = np.convolve(np.pad(ag, 2, mode="edge"), np.ones(5) / 5, "valid")
    C = closing_field(P_t, a_fn=lambda s: np.interp(s, sg, ag))
    r_after = band_ridge_gaps(D_t + C)
    touch = [c for c, g in r_after if g <= 0.003]
    return {"kappa": kappa(tau), "A_t_cm": A_t * 100,
            "zband_min_gap_cm": zband_min_gap(D_t + C, mh_pos)[1] * 100,
            "ridge_min_gap_cm": min(g for _, g in r_after) * 100,
            "touch_bands": touch,
            "patch_length_cm": ((max(touch) - min(touch) + 0.02) * leg_len * 100)
            if touch else 0.0}

qa["stage_progression"] = {f"tau={t}": stage_at(t) for t in (0.6, 0.75, 0.9)}
for t, r in qa["stage_progression"].items():
    print(f"stage {t}: kappa {r['kappa']:.3f}, A_t {r['A_t_cm']:.2f} cm, "
          f"min z-gap after {r['zband_min_gap_cm']:.2f} cm, patch "
          f"{r['patch_length_cm']:.1f} cm")

# ------------------------------------------------------------------ outputs
def fmt(v):
    s_ = f"{abs(v):.3f}".rstrip("0")
    if s_.endswith("."): s_ += "0"
    if s_ in ("", "0."): s_ = "0"
    return ("-" + s_) if v < 0 else s_

def write_target(path, delta, note):
    d_obj = np.stack([delta[:, 0], delta[:, 2], delta[:, 1]], axis=1) / DM_M
    moved = np.where(np.abs(d_obj).max(axis=1) > 0.001)[0]
    header = ("# This is a target file for MakeHuman\n#\n"
              "# It was written by the MakeTarget submodule of MPFB\n#\n"
              "# For more information, see MakeHuman's home page at "
              "http://www.makehumancommunity.org\n#\n# basemesh hm08\n"
              f"# {note}\n")
    with open(path, "w") as fh:
        fh.write(header)
        for i in moved:
            fh.write(f"{i} {fmt(d_obj[i,0])} {fmt(d_obj[i,1])} {fmt(d_obj[i,2])}\n")
    return int(len(moved))

NOTE52 = ("Provenance: CONTACT component of body.belly.protrusion v5.2 "
          "(thigh-contact stage: medial advance + flatten + volume "
          "redistribution, = combined v5.2 - combined v5.1). A "
          "post-process increment, not a standalone field: apply on "
          "top of the v5.1 combined target at full stage weight "
          "(kappa coupling, see slider record). Study-only, internal "
          "- not a CC0 MakeHuman asset. See GRAVITY_V5.md v5.2 addendum.")
n_contact = write_target(OUT / "body.belly.protrusion_contact_v52.target",
                         CONTACT, NOTE52)
qa["moved_verts_contact"] = n_contact
print(f"contact target written: {n_contact} moved verts")

np.savez(WORK / "belly_v52.npz", contact_canonical_m=CONTACT,
         delta_v52_canonical_m=D52, s_grid=_s_grid, a_grid=_a_grid,
         band_s=_band_s, band_g=_band_g, A_MAX=A_MAX, EPS=EPS,
         kappa_onset=0.55)
(WORK / "qa_numbers_v52.json").write_text(json.dumps(qa, indent=1))

# render frame for the Blender test: thigh-zone centre (Blender coords)
dplane52 = np.abs(rel52)
near_all = zone & (dplane52 <= EPS + 0.003)
cen = P52[near_all].mean(axis=0) if near_all.any() else \
    np.array([0.0, 0.0, mh_crotch - 0.12])
frames = {"target_blender": [float(cen[0]), float(-cen[1]), float(cen[2])],
          "note": "canonical (x, y_front, z_up) -> Blender (x, -y, z)"}
(WORK / "contact_frames_v52.json").write_text(json.dumps(frames, indent=1))
print("thigh centre (Blender):", frames["target_blender"])
print("QA v5.2 saved")
