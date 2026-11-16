"""A14 T3: procedural directional pelt textures (tileable).
Strokes = short tapered fur strands along a flow direction (image Y),
root dark -> tip light. Albedo + height; normal derived from height (Sobel).
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

S = 1024
rng = np.random.default_rng(1414)
OUT = "/home/hatch/workspace/anthroforge-v2/fur-craft/a14-shortfur/work/"

alb = Image.new("RGB", (S, S), (122, 99, 74))
hei = Image.new("L", (S, S), 30)
da, dh = ImageDraw.Draw(alb), ImageDraw.Draw(hei)

ROOT = np.array([70, 54, 38]); TIP = np.array([178, 150, 112])
GUARD = np.array([205, 186, 152]); DARK = np.array([50, 38, 28])

def draw_stroke(draw_a, draw_h, x, y, ang, ln, wdt, c0, c1, hv0, hv1):
    dx, dy = np.sin(ang), np.cos(ang)  # flow ~ +y (down image)
    steps = 6
    pts = [(x + dx * ln * i / steps, y + dy * ln * i / steps) for i in range(steps + 1)]
    for i in range(steps):
        t = i / steps
        col = tuple(int(v) for v in (c0 * (1 - t) + c1 * t))
        draw_a.line([pts[i], pts[i + 1]], fill=col, width=wdt)
        hv = int(hv0 * (1 - t) + hv1 * t)
        draw_h.line([pts[i], pts[i + 1]], fill=hv, width=wdt)

N = 11000
for _ in range(N):
    x, y = rng.uniform(0, S, 2)
    ang = rng.normal(0, 0.16) + rng.normal(0, 0.05)  # flow jitter
    ln = rng.uniform(15, 46)
    wdt = 1 if rng.random() < 0.7 else 2
    r = rng.random()
    if r < 0.11:   c0, c1 = ROOT * 0.9, GUARD          # pale guard hairs
    elif r < 0.27: c0, c1 = DARK, ROOT * 1.15          # dark underfur
    else:          c0, c1 = ROOT, TIP * rng.uniform(0.85, 1.05)
    # draw with wrap copies only when near an edge (tiling)
    xs = [x] + ([x - S] if x < 60 else []) + ([x + S] if x > S - 60 else [])
    ys = [y] + ([y - S] if y < 60 else []) + ([y + S] if y > S - 60 else [])
    for xx in xs:
        for yy in ys:
            draw_stroke(da, dh, xx, yy, ang, ln, wdt, c0, c1, 40, 235)

hei = hei.filter(ImageFilter.GaussianBlur(0.8))
h = np.asarray(hei).astype(np.float32) / 255.0
# albedo: bake height as soft AO so strand roots sit in shade
a = np.asarray(alb).astype(np.float32)
a *= (0.80 + 0.28 * h)[..., None]
alb = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
# roughness: tips slightly rougher/brighter
rou = Image.fromarray(np.clip(205 + (h - 0.5) * 55, 150, 245).astype(np.uint8))
# normal map from height (Sobel), OpenGL convention, Y flipped for image space
gx = np.zeros_like(h); gy = np.zeros_like(h)
gx[:, 1:-1] = (h[:, 2:] - h[:, :-2]); gx[:, 0] = h[:, 1] - h[:, -1]; gx[:, -1] = h[:, 0] - h[:, -2]
gy[1:-1, :] = (h[2:, :] - h[:-2, :]); gy[0, :] = h[1, :] - h[-1, :]; gy[-1, :] = h[0, :] - h[-2, :]
st = 2.4
n = np.stack([-gx * st, gy * st, np.ones_like(h)], -1)
n /= np.linalg.norm(n, axis=-1, keepdims=True)
nrm = Image.fromarray(((n * 0.5 + 0.5) * 255).astype(np.uint8))

alb.save(OUT + "tex_pelt_albedo.png"); hei.save(OUT + "tex_pelt_height.png")
rou.save(OUT + "tex_pelt_rough.png");  nrm.save(OUT + "tex_pelt_normal.png")
print("textures written")
