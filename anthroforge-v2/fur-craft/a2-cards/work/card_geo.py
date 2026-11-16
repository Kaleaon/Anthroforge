"""A2 card geometry builders — pure python (no bpy).

Local card space: root at origin, growth along +Z, width along X, thin in Y.
UV convention (matches the A8 standalone bakes, verified empirically):
  v = s (0 at root, 1 at tip) — A8 images carry the root at image-bottom,
  i.e. v=0. NOTE: A13 atlas slots put the root at image-top (glTF v=1 side);
  moving A8 bakes into A13 slots needs a V flip at pack time.
All sizes normalised: L = 0.100 m, W = 0.030 m unless a family says otherwise.
"""
import math

L0, W0 = 0.100, 0.030


def _arc(s, L, bend_rad):
    """Position (y, z) at arc-length fraction s on a circular arc of total
    bend `bend_rad` over length L. Bends toward +Y."""
    if bend_rad < 1e-6:
        return 0.0, s * L
    k = bend_rad / L
    a = s * L
    return (1.0 - math.cos(k * a)) / k, math.sin(k * a) / k


def ribbon(stations, hw_frac, bend_deg=0.0, L=L0, W=W0, u_mode="full",
           u_range=(0.0, 1.0), cx=None):
    """Single ribbon. stations: list of s in [0,1]; hw_frac: halfwidth as a
    fraction of W/2 per station; cx: optional centre-x drift per station
    (in metres). Returns (verts, faces, uvs)."""
    bend = math.radians(bend_deg)
    verts, faces, uvs = [], [], []
    h_root = (W / 2.0) * hw_frac[0]
    for i, s in enumerate(stations):
        y, z = _arc(s, L, bend)
        h = (W / 2.0) * hw_frac[i]
        c = 0.0 if cx is None else cx[i]
        for side in (-1.0, 1.0):
            x = c + side * h
            verts.append((x, y, z))
            if u_mode == "full":
                u = 0.5 + x / (2.0 * h_root)
            else:  # sub-range: map local across [-h..h] into u_range
                u = u_range[0] + (0.5 + (x - c) / (2.0 * h)) * (u_range[1] - u_range[0])
            uvs.append((u, s))
        if i > 0:
            b = 2 * i
            faces.append((b - 2, b - 1, b + 1, b))
    return verts, faces, uvs


def _merge(parts):
    verts, faces, uvs = [], [], []
    for v, f, u in parts:
        off = len(verts)
        verts += v
        uvs += u
        faces += [tuple(i + off for i in face) for face in f]
    return verts, faces, uvs


def _yaw(part, deg):
    v, f, u = part
    t = math.radians(deg)
    c, s = math.cos(t), math.sin(t)
    return ([(x * c - y * s, x * s + y * c, z) for (x, y, z) in v], f, u)


def fam_ribbon_flat():
    return ribbon([0, .25, .5, .75, 1.0], [1, .92, .80, .68, .58])


def fam_ribbon_bent():
    return ribbon([i / 6 for i in range(7)], [1, .95, .87, .78, .68, .58, .48],
                  bend_deg=42.0)


def fam_ribbon_fork():
    # shared base to s=0.58, then two prongs sampling separate strand
    # bundles of the clumped texture (u sub-ranges), gap ~21% of width at tip
    base = ribbon([0, .30, .58], [1, .95, .88], bend_deg=18.0)
    parts = [base]
    h2 = W0 / 2.0
    for sign, ur in ((-1.0, (0.06, 0.46)), (1.0, (0.54, 0.94))):
        cx = [sign * d * h2 for d in (0.0, 0.16, 0.34)]
        parts.append(ribbon([.58, .79, 1.0], [.50, .33, .15], bend_deg=18.0,
                            u_mode="sub", u_range=ur, cx=cx))
    return _merge(parts)


def fam_cross_pair():
    a = fam_ribbon_flat()
    b = _yaw(a, 90.0)
    return _merge([a, b])


def fam_tri_fan():
    one = ribbon([0, .25, .5, .75, 1.0], [1, .93, .83, .70, .55], bend_deg=25.0)
    return _merge([_yaw(one, a) for a in (0.0, 60.0, 120.0)])


def fam_quad_shingle():
    """Wide-short card (L/W = 2.4 at patch scale) with a centre V-fold:
    3 verts across per station, centre lifted toward +Y."""
    L, W = L0, W0
    stations = [0, .34, .67, 1.0]
    hwf = [1, .95, .85, .72]
    bend = math.radians(12.0)
    verts, faces, uvs = [], [], []
    for i, s in enumerate(stations):
        y, z = _arc(s, L, bend)
        h = (W / 2.0) * hwf[i]
        fold = 0.28 * h
        for j, (xf, lift, u) in enumerate(((-1.0, 0.0, 0.0), (0.0, fold, 0.5),
                                          (1.0, 0.0, 1.0))):
            verts.append((xf * h, y + lift, z))
            uvs.append((u, s))
        if i > 0:
            b = 3 * i
            faces.append((b - 3, b - 2, b + 1, b))
            faces.append((b - 2, b - 1, b + 2, b + 1))
    return verts, faces, uvs


FAMILIES = {
    "ribbon_flat":   dict(build=fam_ribbon_flat,   texture="straight",
                          desc="single plane, 4 segments, no baked bend"),
    "ribbon_bent":   dict(build=fam_ribbon_bent,   texture="wavy",
                          desc="single plane, 6 segments, 42 deg baked arc bend"),
    "ribbon_fork":   dict(build=fam_ribbon_fork,   texture="clumped",
                          desc="shared base splitting into 2 prongs at s=0.58"),
    "cross_pair":    dict(build=fam_cross_pair,    texture="guard_ruff",
                          desc="two flat ribbons crossed 90 deg (A5 ruff standard)"),
    "tri_fan":       dict(build=fam_tri_fan,       texture="clumped",
                          desc="three bent ribbons at 60 deg yaw steps"),
    "quad_shingle":  dict(build=fam_quad_shingle,  texture="straight",
                          desc="wide card, 3 across, centre V-fold, 12 deg bend"),
}
