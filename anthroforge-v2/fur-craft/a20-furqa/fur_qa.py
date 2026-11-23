#!/usr/bin/env python3
"""
AnthroForge fur QA harness — numpy + stdlib (PIL only for PNG decode).

Scores a fur-card asset (glTF binary, one file per LOD, ordered best->worst)
against the fur quality gates defined in FUR_QA.md:

  density        cards / tris / cards per m^2 of body surface (ellipsoid est.)
  coverage       mean orthographic silhouette coverage vs convex-hull proxy
  grazing        worst-view projected-area retention (skin show-through proxy)
  overdraw       alpha-weighted projected area / silhouette area, per view
  popin          coverage delta between consecutive LODs + est. switch range
  coherence      within-card straightness + neighbour direction coherence
  texture        card-texture alpha coverage, strand fill, root->tip banding

Usage:
  fur_qa.py LOD0.glb [LOD1.glb ...] [--render-strands S.png --render-cards C.png]
            [--out results.json] [--res 256]

Exit code 0 always unless a file fails to parse (scores, not crashes, are
the product). Every gate reports PASS / WARN / FAIL with the measured value.
"""

import argparse
import json
import math
import struct
from io import BytesIO

import numpy as np

# --------------------------------------------------------------------------
# GLB loading (stdlib struct/json + numpy, same approach as validate_glb.py)
# --------------------------------------------------------------------------
COMP = {5120: (np.int8, 1), 5121: (np.uint8, 1), 5122: (np.int16, 2),
        5123: (np.uint16, 2), 5125: (np.uint32, 4), 5126: (np.float32, 4)}
NCOMP = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def load_glb(path):
    data = open(path, "rb").read()
    assert data[:4] == b"glTF", "not a GLB"
    jlen = struct.unpack("<I", data[12:16])[0]
    gltf = json.loads(data[20:20 + jlen])
    off = 20 + jlen
    blen = struct.unpack("<I", data[off:off + 4])[0]
    binbuf = data[off + 8:off + 8 + blen]
    return gltf, binbuf


def read_accessor(gltf, binbuf, idx):
    acc = gltf["accessors"][idx]
    bv = gltf["bufferViews"][acc["bufferView"]]
    dt, _ = COMP[acc["componentType"]]
    n = NCOMP[acc["type"]]
    start = bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
    stride = bv.get("byteStride")
    count = acc["count"]
    if stride and stride != np.dtype(dt).itemsize * n:
        raw = np.lib.stride_tricks.as_strided(
            np.frombuffer(binbuf, dtype=np.uint8, offset=start),
            shape=(count, n), strides=(stride, np.dtype(dt).itemsize))
        return np.array(raw, dtype=dt).astype(np.float64) if dt != np.uint8 else np.array(raw)
    arr = np.frombuffer(binbuf, dtype=dt, count=count * n, offset=start)
    return arr.reshape(count, n) if n > 1 else arr


def node_world_matrices(gltf):
    mats = {}

    def local(node):
        m = np.eye(4)
        if "matrix" in node:
            m = np.array(node["matrix"], dtype=np.float64).reshape(4, 4).T
        else:
            t = node.get("translation", [0, 0, 0])
            r = node.get("rotation", [0, 0, 0, 1])
            s = node.get("scale", [1, 1, 1])
            x, y, z, w = r
            R = np.array([
                [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]],
                dtype=np.float64)
            m[:3, :3] = R @ np.diag(s)
            m[:3, 3] = t
        return m

    def walk(nid, parent):
        node = gltf["nodes"][nid]
        m = parent @ local(node)
        mats[nid] = m
        for c in node.get("children", []):
            walk(c, m)

    for scene in gltf.get("scenes", [{"nodes": []}]):
        for nid in scene.get("nodes", []):
            walk(nid, np.eye(4))
    return mats


def load_fur_glb(path):
    """Return dict with world-space verts, tris, uv, per-tri material,
    embedded textures {material_name: PIL.Image or None}."""
    gltf, binbuf = load_glb(path)
    mats = node_world_matrices(gltf)
    verts, uvs, tris, tri_mat = [], [], [], []
    voff = 0
    mesh_nodes = {}
    for nid, node in enumerate(gltf.get("nodes", [])):
        if "mesh" in node:
            mesh_nodes.setdefault(node["mesh"], []).append(nid)
    for mi, mesh in enumerate(gltf["meshes"]):
        world = np.eye(4)
        if mesh_nodes.get(mi):
            world = mats[mesh_nodes[mi][0]]
        for prim in mesh["primitives"]:
            pos = read_accessor(gltf, binbuf, prim["attributes"]["POSITION"]).astype(np.float64)
            pos = (world[:3, :3] @ pos.T).T + world[:3, 3]
            uv = (read_accessor(gltf, binbuf, prim["attributes"]["TEXCOORD_0"]).astype(np.float64)
                  if "TEXCOORD_0" in prim["attributes"] else np.zeros((len(pos), 2)))
            if "indices" in prim:
                idx = read_accessor(gltf, binbuf, prim["indices"]).astype(np.int64).ravel()
            else:
                idx = np.arange(len(pos))
            tris.append(idx.reshape(-1, 3) + voff)
            tri_mat += [prim.get("material", -1)] * (len(idx) // 3)
            verts.append(pos)
            uvs.append(uv)
            voff += len(pos)
    textures = {}
    for mi2, mat in enumerate(gltf.get("materials", [])):
        name = mat.get("name", f"material{mi2}")
        textures[name] = None
        try:
            ti = mat["pbrMetallicRoughness"]["baseColorTexture"]["index"]
            img_idx = gltf["textures"][ti]["source"]
            img = gltf["images"][img_idx]
            bv = gltf["bufferViews"][img["bufferView"]]
            start = bv.get("byteOffset", 0)
            raw = binbuf[start:start + bv["byteLength"]]
            from PIL import Image
            textures[name] = Image.open(BytesIO(raw)).convert("RGBA")
        except Exception:
            pass
    return {"verts": np.vstack(verts), "uv": np.vstack(uvs),
            "tris": np.vstack(tris), "tri_mat": np.array(tri_mat),
            "material_names": [m.get("name", f"material{i}")
                               for i, m in enumerate(gltf.get("materials", []))],
            "textures": textures}


# --------------------------------------------------------------------------
# cards = connected components of the triangle graph
# --------------------------------------------------------------------------
def find_cards(tris, nverts):
    parent = np.arange(nverts)

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for a, b, c in tris:
        ra, rb, rc = find(a), find(b), find(c)
        if ra != rb:
            parent[ra] = rb
        if rb != rc:
            parent[rb] = rc
    roots = np.array([find(i) for i in range(nverts)])
    used_verts = np.unique(tris.ravel())
    cards = {}
    for v in used_verts:
        cards.setdefault(int(roots[v]), []).append(int(v))
    return [np.array(vs) for vs in cards.values()]


def card_geometry(verts, uv, card_verts):
    """Direction (root->tip), straightness, width, length for one card."""
    P = verts[card_verts]
    V = uv[card_verts][:, 1]  # v=1 at root, v=0 at tip (fur-prototype layout)
    root = P[V > 0.75].mean(axis=0) if (V > 0.75).any() else P[np.argmax(V)]
    tip = P[V < 0.25].mean(axis=0) if (V < 0.25).any() else P[np.argmin(V)]
    d = tip - root
    length = np.linalg.norm(d)
    direction = d / length if length > 1e-9 else np.array([0.0, 1.0, 0.0])
    # polyline through v-band centroids -> straightness = chord / path
    bands = []
    for lo in np.linspace(0, 0.8, 5):
        m = (V >= lo) & (V < lo + 0.2 + 1e-6)
        if m.any():
            bands.append(P[m].mean(axis=0))
    bands = np.array(bands[::-1])  # root (high v) first: bands sorted by v desc
    if len(bands) >= 2:
        path = np.linalg.norm(np.diff(bands, axis=0), axis=1).sum()
        straight = float(np.linalg.norm(bands[-1] - bands[0]) / path) if path > 1e-9 else 1.0
    else:
        straight = 1.0
    # width: spread perpendicular to direction at the root band
    perp_spread = P[V > 0.75] - root
    width = float(2 * np.abs(perp_spread @ np.cross(direction, [0, 0, 1])).max()) \
        if len(perp_spread) > 1 else 0.0
    return {"root": root, "tip": tip, "dir": direction,
            "straightness": straight, "length": float(length),
            "width": width}


# --------------------------------------------------------------------------
# orthographic rasterisation (unique-pixel coverage + summed area)
# --------------------------------------------------------------------------
def project(verts, view):
    axes = {"+x": (2, 1, 0), "-x": (2, 1, 0), "+z": (0, 1, 2), "-z": (0, 1, 2),
            "+y": (0, 2, 1), "-y": (0, 2, 1)}
    u, v, _ = axes[view]
    s = -1 if view.startswith("-") else 1
    return verts[:, [u, v]] * np.array([s, 1]), verts[:, axes[view][2]]


def rasterize(pts2d, tris, res, extent):
    """Return (mask, summed_area_m2, mask_area_m2)."""
    lo, hi = extent
    scale = res / (hi - lo)
    P = (pts2d - lo) * scale
    mask = np.zeros((res, res), dtype=bool)
    summed_px = 0.0
    T = P[tris]
    area2 = np.abs((T[:, 1, 0] - T[:, 0, 0]) * (T[:, 2, 1] - T[:, 0, 1])
                   - (T[:, 2, 0] - T[:, 0, 0]) * (T[:, 1, 1] - T[:, 0, 1])) / 2
    summed_px = float(area2.sum())
    for tri in T:
        mn = np.maximum(tri.min(axis=0).astype(int), 0)
        mx = np.minimum(tri.max(axis=0).astype(int) + 1, res)
        if (mx <= mn).any():
            continue
        ys, xs = np.mgrid[mn[1]:mx[1], mn[0]:mx[0]]
        cx, cy = xs + 0.5, ys + 0.5
        (x0, y0), (x1, y1), (x2, y2) = tri
        d = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if abs(d) < 1e-12:
            continue
        a = ((y1 - y2) * (cx - x2) + (x2 - x1) * (cy - y2)) / d
        b = ((y2 - y0) * (cx - x2) + (x0 - x2) * (cy - y2)) / d
        c = 1 - a - b
        inside = (a >= 0) & (b >= 0) & (c >= 0)
        mask[mn[1]:mx[1], mn[0]:mx[0]] |= inside
    px_m2 = ((hi - lo) / res) ** 2
    return mask, summed_px * px_m2, float(mask.sum()) * px_m2


def convex_hull_area(pts):
    pts = np.unique(pts, axis=0)
    if len(pts) < 3:
        return 0.0
    pts = pts[np.lexsort((pts[:, 1], pts[:, 0]))]

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(tuple(p))
    upper = []
    for p in pts[::-1]:
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(tuple(p))
    hull = np.array(lower[:-1] + upper[:-1])
    x, y = hull[:, 0], hull[:, 1]
    return float(0.5 * abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1))))


# --------------------------------------------------------------------------
# texture metrics
# --------------------------------------------------------------------------
def texture_metrics(img):
    a = np.asarray(img).astype(np.float64)
    alpha = a[:, :, 3] / 255.0
    rgb = a[:, :, :3] / 255.0
    solid = alpha > 0.5
    coverage = float(solid.mean())
    strand_fill = float(alpha[alpha > 0.03].mean()) if (alpha > 0.03).any() else 0.0
    # root->tip banding: image top row = v=1 = root (fur-prototype bake layout)
    lum = (0.2126 * rgb[:, :, 0] + 0.7152 * rgb[:, :, 1] + 0.0722 * rgb[:, :, 2])
    bands = 10
    profile, occupancy = [], []
    for i in range(bands):
        rows = slice(i * alpha.shape[0] // bands, (i + 1) * alpha.shape[0] // bands)
        w = alpha[rows]
        occupancy.append(float((w > 0.03).mean()))
        profile.append(float((lum[rows] * w).sum() / w.sum()) if w.sum() > 0 else float("nan"))
    profile = np.array(profile)
    occupied = np.array(occupancy) >= 0.01
    dead_uv = float(1.0 - occupied.mean())
    ok = ~np.isnan(profile) & occupied
    if ok.sum() >= 4:
        idx = np.arange(bands)[ok]
        corr = float(np.corrcoef(idx, profile[ok])[0, 1])
        gradient = float((profile[ok].max() - profile[ok].min()) /
                         max(profile[ok].mean(), 1e-6))
    else:
        corr, gradient = 0.0, 0.0
    return {"alpha_coverage": coverage, "strand_fill_alpha": strand_fill,
            "alpha_mean": float(alpha.mean()), "dead_uv_fraction": dead_uv,
            "band_profile_root_to_tip": [round(float(x), 4) for x in profile],
            "band_trend_corr": corr, "band_gradient": gradient}


# --------------------------------------------------------------------------
# gates
# --------------------------------------------------------------------------
def gate(name, value, passed, warned):
    status = "PASS" if value >= passed else ("WARN" if value >= warned else "FAIL")
    return {"gate": name, "value": round(float(value), 4), "status": status,
            "pass_at": passed, "warn_at": warned}


def score_lod(fur, res):
    verts, tris, uv = fur["verts"], fur["tris"], fur["uv"]
    cards = find_cards(tris, len(verts))
    infos = [card_geometry(verts, uv, cv) for cv in cards]
    dirs = np.array([i["dir"] for i in infos])
    roots = np.array([i["root"] for i in infos])
    straight = float(np.mean([i["straightness"] for i in infos]))
    # neighbour coherence: mean resultant length inside 0.15 m root bins
    cell = 0.15
    bins = {}
    for r, d in zip(roots, dirs):
        key = tuple(np.floor(r / cell).astype(int))
        bins.setdefault(key, []).append(d)
    coh, wsum = 0.0, 0
    for ds in bins.values():
        if len(ds) >= 3:
            coh += len(ds) * float(np.linalg.norm(np.mean(ds, axis=0)))
            wsum += len(ds)
    neighbour = coh / wsum if wsum else 0.0
    # body surface estimate: Knud-Thomsen ellipsoid from bbox
    ext = verts.max(axis=0) - verts.min(axis=0)
    a_, b_, c_ = ext / 2
    p = 1.6075
    surf = 4 * math.pi * ((a_ ** p * b_ ** p + a_ ** p * c_ ** p + b_ ** p * c_ ** p) / 3) ** (1 / p)
    # texture alpha per material (for overdraw weighting)
    tex_stats = {}
    mat_alpha = {}
    for name, img in fur["textures"].items():
        if img is not None:
            tex_stats[name] = texture_metrics(img)
            mat_alpha[name] = tex_stats[name]["strand_fill_alpha"]
    def alpha_of(tri_idx):
        m = fur["tri_mat"][tri_idx]
        if m < 0 or m >= len(fur["material_names"]):
            return 0.8
        return mat_alpha.get(fur["material_names"][m], 0.8)
    # views
    views = ["+x", "-x", "+z", "-z", "+y", "-y"]
    diag = []
    covs, overs, areas = {}, {}, {}
    gmin = verts.min(axis=0) - 0.05
    gmax = verts.max(axis=0) + 0.05
    for view in views:
        pts2d, _ = project(verts, view)
        u, v = {"+x": (2, 1), "-x": (2, 1), "+z": (0, 1), "-z": (0, 1),
                "+y": (0, 2), "-y": (0, 2)}[view]
        extent = (min(gmin[u], gmin[v]), max(gmax[u], gmax[v]))
        mask, summed, mask_area = rasterize(pts2d, tris, res, extent)
        hull = convex_hull_area(pts2d)
        covs[view] = mask_area / hull if hull > 0 else 0.0
        areas[view] = mask_area
        # alpha-weighted summed area
        ta = np.array([alpha_of(i) for i in range(len(tris))])
        T = pts2d[tris]
        a2 = np.abs((T[:, 1, 0] - T[:, 0, 0]) * (T[:, 2, 1] - T[:, 0, 1])
                    - (T[:, 2, 0] - T[:, 0, 0]) * (T[:, 1, 1] - T[:, 0, 1])) / 2
        overs[view] = float((a2 * ta).sum() / mask_area) if mask_area > 0 else 0.0
        diag.append(view)
    coverage = float(np.mean(list(covs.values())))
    best = max(areas.values())
    grazing = float(min(areas.values()) / best) if best > 0 else 0.0
    overdraw = float(np.mean(list(overs.values())))
    return {"cards": len(cards), "tris": int(len(tris)),
            "body_surface_m2_est": round(surf, 3),
            "cards_per_m2": round(len(cards) / surf, 1),
            "mean_card_length_m": round(float(np.mean([i["length"] for i in infos])), 4),
            "mean_card_width_m": round(float(np.mean([i["width"] for i in infos])), 4),
            "coverage_by_view": {k: round(v, 3) for k, v in covs.items()},
            "coverage": coverage, "grazing_retention": grazing,
            "overdraw": overdraw,
            "straightness": straight, "neighbour_coherence": neighbour,
            "textures": tex_stats}


def render_silhouette_ratio(strands_path, cards_path):
    from PIL import Image
    def fg(path):
        im = np.asarray(Image.open(path).convert("RGB")).astype(int)
        bg = im[0, 0]
        dist = np.abs(im - bg).sum(axis=2)
        return dist > 40
    s = fg(strands_path)
    c = fg(cards_path)
    return float(c.sum() / s.sum()) if s.sum() else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("glbs", nargs="+", help="card GLBs, best LOD first")
    ap.add_argument("--render-strands")
    ap.add_argument("--render-cards")
    ap.add_argument("--out")
    ap.add_argument("--res", type=int, default=256)
    args = ap.parse_args()

    results = {"lods": [], "gates": []}
    prev = None
    for i, path in enumerate(args.glbs):
        fur = load_fur_glb(path)
        s = score_lod(fur, args.res)
        s["file"] = path
        if prev is not None:
            s["popin_coverage_delta"] = abs(prev["coverage"] - s["coverage"]) / prev["coverage"]
            s["popin_area_delta"] = abs(1 - s["coverage"] / prev["coverage"])
        results["lods"].append(s)
        print(f"LOD{i}: {s['cards']} cards, {s['tris']} tris, "
              f"coverage {s['coverage']:.3f}, grazing {s['grazing_retention']:.3f}, "
              f"overdraw {s['overdraw']:.2f}, coherence n={s['neighbour_coherence']:.3f} "
              f"s={s['straightness']:.3f}")
        prev = s

    lod0 = results["lods"][0]
    g = []
    g.append(gate("density_cards_per_m2", lod0["cards_per_m2"], 4000, 1500))
    g.append(gate("silhouette_coverage", lod0["coverage"], 0.55, 0.35))
    g.append(gate("grazing_retention", lod0["grazing_retention"], 0.55, 0.35))
    over = {"gate": "overdraw", "value": round(lod0["overdraw"], 3),
            "status": "PASS" if lod0["overdraw"] <= 4.0 else
                      ("WARN" if lod0["overdraw"] <= 8.0 else "FAIL"),
            "pass_at": "<=4.0", "warn_at": "<=8.0"}
    g.append(over)
    g.append(gate("direction_coherence_neighbour", lod0["neighbour_coherence"], 0.75, 0.55))
    g.append(gate("direction_straightness", lod0["straightness"], 0.85, 0.70))
    if lod0["textures"]:
        for name, ts in lod0["textures"].items():
            g.append(gate(f"texture_alpha_coverage[{name}]", ts["alpha_coverage"], 0.25, 0.12))
            g.append(gate(f"colour_band_gradient[{name}]", ts["band_gradient"], 0.25, 0.10))
            g.append({"gate": f"dead_uv_fraction[{name}]", "value": round(ts["dead_uv_fraction"], 4),
                      "status": "PASS" if ts["dead_uv_fraction"] <= 0.05 else
                                ("WARN" if ts["dead_uv_fraction"] <= 0.20 else "FAIL"),
                      "pass_at": "<=0.05", "warn_at": "<=0.20"})
    # cross-LOD texture consistency: same-named texture must carry the same
    # alpha strength at every LOD, or the chain fades as it steps down.
    for s in results["lods"][1:]:
        for name, ts in s["textures"].items():
            base = lod0["textures"].get(name)
            if base and base["alpha_mean"] > 0:
                ratio = ts["alpha_mean"] / base["alpha_mean"]
                g.append({"gate": f"lod_texture_alpha_ratio[{name} vs LOD0]",
                          "value": round(ratio, 4),
                          "status": "PASS" if 0.7 <= ratio <= 1.4 else
                                    ("WARN" if 0.4 <= ratio <= 2.0 else "FAIL"),
                          "pass_at": "0.7-1.4", "warn_at": "0.4-2.0"})
    for s in results["lods"][1:]:
        d = s.get("popin_coverage_delta", 0.0)
        g.append({"gate": f"popin_delta[{s['file'].split('/')[-1]}]",
                  "value": round(d, 4),
                  "status": "PASS" if d <= 0.10 else ("WARN" if d <= 0.25 else "FAIL"),
                  "pass_at": "<=0.10", "warn_at": "<=0.25"})
    if args.render_strands and args.render_cards:
        ratio = render_silhouette_ratio(args.render_strands, args.render_cards)
        results["render_silhouette_ratio_cards_vs_strands"] = round(ratio, 4)
        g.append(gate("render_silhouette_ratio", ratio, 0.85, 0.65))
    results["gates"] = g
    for row in g:
        print(f"  {row['status']:4s}  {row['gate']:46s} {row['value']}")
    if args.out:
        with open(args.out, "w") as fh:
            json.dump(results, fh, indent=1)
        print("wrote", args.out)


if __name__ == "__main__":
    main()
