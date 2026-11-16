"""Alpha-aware projected-area measurement (system python3, PIL + numpy).

For each family: projected visible area toward view directions rotated from
face-on (+Y toward the card) toward along-growth (+Z), alpha-weighted by
sampling the family's A8 diffuse at tri UVs (visible = alpha > 0.5, the
A13 cutoff contract). Reports retention R(theta) = A(theta)/A(0).
"""
import json, math, os
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
A8 = os.path.expanduser("~/workspace/anthroforge-v2/fur-craft/a8-cardtextures")

stats = json.load(open(os.path.join(HERE, "card_stats.json")))
alphas = {}
for name, st in stats.items():
    if st["texture"] not in alphas:
        im = Image.open(os.path.join(
            A8, f"card_{st['texture']}_diffuse.png"))
        alphas[st["texture"]] = np.asarray(im)[:, :, 3].astype(float) / 255.0


def tri_samples(uv_tri, n=4):
    pts = []
    for i in range(n):
        for j in range(n - i):
            a = i / n; b = j / n; c = 1 - a - b
            pts.append(a * uv_tri[0] + b * uv_tri[1] + c * uv_tri[2])
    return pts


def proj_area(st, view, tex_alpha):
    V = np.array(st["geo_verts"]); F = st["geo_faces"]; UV = np.array(st["geo_uvs"])
    H, W = tex_alpha.shape
    total = 0.0
    for f in F:
        tris = [(f[0], f[1], f[2]), (f[0], f[2], f[3])] if len(f) == 4 else [tuple(f)]
        for t in tris:
            p = V[list(t)]
            n = np.cross(p[1] - p[0], p[2] - p[0])
            area = 0.5 * np.linalg.norm(n)
            facing = abs(np.dot(n / (np.linalg.norm(n) + 1e-12), view))
            if facing <= 0 or area == 0:
                continue
            vis = 0.0
            pts = tri_samples(UV[list(t)])
            for (u, v) in pts:
                px = min(max(int(u * W), 0), W - 1)
                py = min(max(int((1.0 - v) * H), 0), H - 1)
                vis += 1.0 if tex_alpha[py, px] > 0.5 else 0.0
            total += area * facing * (vis / len(pts))
    return total


ANGLES = [0, 30, 60, 75, 85]
out = {}
for name, st in stats.items():
    row = {}
    base = None
    for th in ANGLES:
        t = math.radians(th)
        view = np.array([0.0, math.cos(t), math.sin(t)])
        a = proj_area(st, view, alphas[st["texture"]])
        if base is None:
            base = a
        row[str(th)] = dict(area_m2=round(a, 6),
                            retention=round(a / base, 3) if base else 0)
    out[name] = row
    print(name, {k: v["retention"] for k, v in row.items()},
          "A0 =", row["0"]["area_m2"], "m2")

json.dump(out, open(os.path.join(HERE, "projected_area.json"), "w"), indent=1)
print("WROTE projected_area.json")
