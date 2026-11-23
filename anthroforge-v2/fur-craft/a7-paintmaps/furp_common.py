"""Shared helpers for the A7 paintable fur-map prototype.

Map set (all POINT domain, on the groom surface mesh):

  vertex groups (Weight-Paint targets, scalar [0,1])
    FURP_density  FURP_length  FURP_clump  FURP_curl
  colour attributes (FLOAT_COLOR, POINT)
    FURP_direction  R,G = flow direction in the UV tangent frame
                    ((d.T, d.B) mapped [-1,1] -> [0,1]); B = lift
                    (0 = strand lies along the flow, 1 = stands on
                    the surface normal); A = 1
    FURP_zone_root  painted root colour of the coat (linear RGB)
    FURP_zone_tip   painted tip colour (linear RGB)
    FURP_viz        editor heat-viz of FURP_density (derived, not data)

Region aggregation uses the fur prototype's analytic region fields,
recomputed identically (FUR_ruff / FUR_back / FUR_belly / FUR_coat /
FUR_bodyhair vertex groups, fur-prototype/work/s2_regions.py).
"""
import numpy as np

FRONT = -1.0  # bara wolf faces -Y (proven in fur prototype s1)
LENGTH_REF_M = 0.20  # FURP_length == 1.0 means 20 cm

REGION_ORDER = ["ruff", "back", "belly", "coat", "bodyhair"]
# prototype groom table (FUR_PROTOTYPE.md SS3): reference length / clump / curl
REGION_REF = {
    "ruff":     dict(length_m=0.170, clump=0.65, curl=0.30, density=0.95),
    "back":     dict(length_m=0.095, clump=0.45, curl=0.50, density=0.90),
    "belly":    dict(length_m=0.042, clump=0.25, curl=0.10, density=0.80),
    "coat":     dict(length_m=0.066, clump=0.40, curl=0.45, density=0.85),
    "bodyhair": dict(length_m=0.018, clump=0.10, curl=0.00, density=0.35),
}
ZONE_SEED = {  # linear RGB root / tip per region (converter seed only)
    "ruff":     dict(root=(0.055, 0.038, 0.022), tip=(0.300, 0.235, 0.150)),
    "back":     dict(root=(0.040, 0.028, 0.018), tip=(0.160, 0.115, 0.070)),
    "belly":    dict(root=(0.100, 0.075, 0.048), tip=(0.240, 0.185, 0.115)),
    "coat":     dict(root=(0.055, 0.038, 0.022), tip=(0.190, 0.140, 0.090)),
    "bodyhair": dict(root=(0.050, 0.036, 0.022), tip=(0.120, 0.090, 0.060)),
}

SCALAR_MAPS = ["FURP_density", "FURP_length", "FURP_clump", "FURP_curl"]


def ss(a, b, x):
    """Smoothstep, edge order significant (matches s2_regions.py)."""
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def clamp01(x):
    return np.clip(x, 0.0, 1.0)


def mesh_arrays(ob):
    """World-space positions, vertex normals, UV tangents, faces."""
    import bpy  # noqa: F401  (ensures we are inside Blender)
    me = ob.data
    mw = np.array(ob.matrix_world)
    n = len(me.vertices)
    co = np.empty(n * 3, dtype=np.float64)
    me.vertices.foreach_get("co", co)
    pos = co.reshape(n, 3)
    pos = pos @ mw[:3, :3].T + mw[:3, 3]
    # vertex normals from polygon accumulation (as s2_regions.py)
    nrm = np.zeros((n, 3))
    me.calc_loop_triangles()
    tris = np.empty(len(me.loop_triangles) * 3, dtype=np.int64)
    me.loop_triangles.foreach_get("vertices", tris)
    tris = tris.reshape(-1, 3)
    p = pos[tris]
    fn = np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0])
    for c in range(3):
        np.add.at(nrm, tris[:, c], fn)
    ln = np.linalg.norm(nrm, axis=1, keepdims=True)
    nrm = nrm / np.maximum(ln, 1e-12)
    # UV tangents, accumulated per face then orthogonalised
    tan = np.zeros((n, 3))
    uv_layer = me.uv_layers.active
    if uv_layer is not None:
        luv = np.empty(len(me.loops) * 2, dtype=np.float64)
        uv_layer.data.foreach_get("uv", luv)
        luv = luv.reshape(-1, 2)
        lt_loops = np.empty(len(me.loop_triangles) * 3, dtype=np.int64)
        me.loop_triangles.foreach_get("loops", lt_loops)
        lt_loops = lt_loops.reshape(-1, 3)
        tuv = luv[lt_loops]                      # (F,3,2)
        tp = pos[tris]                           # (F,3,3)
        e1 = tp[:, 1] - tp[:, 0]
        e2 = tp[:, 2] - tp[:, 0]
        d1 = tuv[:, 1] - tuv[:, 0]
        d2 = tuv[:, 2] - tuv[:, 0]
        det = d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0]
        ok = np.abs(det) > 1e-10
        tf = np.zeros((len(tris), 3))
        r = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)
        tf[ok] = (e1[ok] * d2[ok, 1:2] - e2[ok] * d1[ok, 1:2]) * r[ok, None]
        for c in range(3):
            np.add.at(tan, tris[:, c], tf)
    # orthogonalise T against N; B = N x T
    tan = tan - np.einsum("ij,ij->i", tan, nrm)[:, None] * nrm
    lt = np.linalg.norm(tan, axis=1, keepdims=True)
    bad = (lt[:, 0] < 1e-8)
    if bad.any():  # degenerate UV spots: fall back to any perpendicular
        ref = np.tile(np.array([1.0, 0.0, 0.0]), (n, 1))
        ref[bad & (np.abs(nrm[:, 0]) > 0.9)] = (0.0, 1.0, 0.0)
        tan[bad] = ref[bad] - np.einsum("ij,ij->i", ref[bad], nrm[bad])[:, None] * nrm[bad]
        lt = np.linalg.norm(tan, axis=1, keepdims=True)
    tan = tan / np.maximum(lt, 1e-12)
    bit = np.cross(nrm, tan)
    return pos, nrm, tan, bit, tris


def region_fields(pos, nrm):
    """The fur prototype's five analytic regions, numpy port of s2."""
    x, y, z = pos[:, 0], pos[:, 1], pos[:, 2]
    ax = np.abs(x)
    sy = FRONT * y
    sn = FRONT * nrm[:, 1]
    nz = nrm[:, 2]

    head_band = ss(1.38, 1.46, z) * (1.0 - ss(1.84, 1.92, z))
    cheek = ss(0.05, 0.13, ax) * (1.0 - ss(0.24, 0.34, ax))
    muzzle = ss(0.12, 0.22, sy) * ss(1.56, 1.64, z) * (1.0 - ss(1.74, 1.82, z))
    r_head = head_band * np.maximum(cheek, 0.35 * (1.0 - ss(0.10, 0.20, sy))) * (1.0 - muzzle)
    neck_band = ss(1.24, 1.34, z) * (1.0 - ss(1.46, 1.54, z))
    frontish = ss(-0.10, 0.02, sy)
    narrow = 1.0 - ss(0.26, 0.38, ax)
    r_neck = neck_band * np.maximum(frontish, 0.45) * narrow
    r_jaw = (ss(1.40, 1.48, z) * (1.0 - ss(1.56, 1.64, z))
             * ss(-0.2, -0.6, nz) * (1.0 - ss(0.16, 0.26, ax)))
    ruff = clamp01(np.maximum(np.maximum(r_head, r_neck), r_jaw))

    dorsal = ss(0.05, 0.45, -sn)
    backpos = ss(-0.02, -0.14, sy)
    band = ss(0.45, 0.60, z) * (1.0 - ss(1.60, 1.72, z))
    shoulder = (ss(1.30, 1.44, z) * (1.0 - ss(1.52, 1.62, z))
                * ss(0.15, 0.45, nz) * ss(0.0, 0.12, -sy))
    back = clamp01(np.maximum(dorsal * band * np.maximum(backpos, 0.35),
                              shoulder * 0.9))

    front = ss(0.15, 0.55, sn)
    bband = ss(0.55, 0.70, z) * (1.0 - ss(1.22, 1.36, z))
    bnarrow = 1.0 - ss(0.28, 0.40, ax)
    belly = clamp01(front * bband * bnarrow)

    chest = (ss(0.35, 0.65, sn) * ss(1.02, 1.12, z)
             * (1.0 - ss(1.34, 1.44, z)) * (1.0 - ss(0.22, 0.33, ax)))
    fore = (ss(0.48, 0.62, ax) * (1.0 - ss(0.98, 1.10, ax))
            * ss(1.22, 1.30, z) * (1.0 - ss(1.46, 1.54, z)))
    bodyhair = clamp01(np.maximum(chest, fore))

    coat = np.maximum(clamp01(1.0 - np.maximum(np.maximum(ruff, back), belly)), 0.04)
    return {"ruff": ruff, "back": back, "belly": belly,
            "coat": coat, "bodyhair": bodyhair, "muzzle": muzzle}


# ------------------------------------------------------------ layer I/O

def write_group(ob, name, w, thresh=0.003):
    g = ob.vertex_groups.get(name) or ob.vertex_groups.new(name=name)
    idx = np.where(w > thresh)[0]
    for i in idx:
        g.add([int(i)], float(w[i]), "REPLACE")
    return g


def read_group(ob, name, n):
    g = ob.vertex_groups.get(name)
    w = np.zeros(n)
    if g is None:
        return w
    for i in range(n):
        try:
            w[i] = g.weight(i)
        except RuntimeError:
            pass
    return w


def write_color_attr(me, name, rgba):
    if name in me.color_attributes:
        me.color_attributes.remove(me.color_attributes[name])
    ca = me.color_attributes.new(name=name, type="FLOAT_COLOR", domain="POINT")
    ca.data.foreach_set("color", rgba.astype(np.float32).ravel().tolist())
    return ca


def read_color_attr(me, name, n):
    ca = me.color_attributes.get(name)
    if ca is None:
        return None
    arr = np.empty(n * 4, dtype=np.float32)
    ca.data.foreach_get("color", arr)
    return arr.reshape(n, 4).astype(np.float64)


# ------------------------------------------------------- direction codec

def encode_direction(d, lift, tan, bit):
    """d: (N,3) unit flow in the tangent plane. Returns RGBA float."""
    c = np.einsum("ij,ij->i", d, tan)
    s = np.einsum("ij,ij->i", d, bit)
    rgba = np.ones((len(d), 4))
    rgba[:, 0] = c * 0.5 + 0.5
    rgba[:, 1] = s * 0.5 + 0.5
    rgba[:, 2] = lift
    return rgba


def decode_direction(rgba, tan, bit):
    c = rgba[:, 0] * 2.0 - 1.0
    s = rgba[:, 1] * 2.0 - 1.0
    d = c[:, None] * tan + s[:, None] * bit
    ln = np.linalg.norm(d, axis=1, keepdims=True)
    d = d / np.maximum(ln, 1e-12)
    return d, rgba[:, 2].copy()


def flow_seed(nrm):
    """Canonical slick flow: backward (+Y, away from the face) and down,
    projected onto the tangent plane; lift seeded by nothing (flat 0.32,
    raised on the ruff by the caller)."""
    f = np.array([0.0, 0.5, -1.0])
    f = f / np.linalg.norm(f)
    d = f[None, :] - np.einsum("ij,j->i", nrm, f)[:, None] * nrm
    ln = np.linalg.norm(d, axis=1, keepdims=True)
    d = d / np.maximum(ln, 1e-12)
    return d
