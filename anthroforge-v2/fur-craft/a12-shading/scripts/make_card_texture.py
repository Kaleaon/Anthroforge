"""Procedural fur-card texture for the A12 shading testbed.
512x1024 RGBA: strands drawn root (v=0, bottom of image = v0 in Blender UV
with flip_y handled by drawing roots at image bottom) -> tip.
Root: opaque, dark. Tip: tapered, alpha -> 0. Warm brown guard-hair palette
(root #4a3421 -> tip #b98d5f) with per-strand jitter."""
import random
from PIL import Image, ImageDraw

random.seed(1212)
W, H = 512, 1024
img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
dr = ImageDraw.Draw(img)

def lerp(a, b, t): return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))
ROOT = (29, 19, 10); MID = (94, 65, 37); TIP = (178, 130, 82)

N = 300
for _ in range(N):
    x0 = random.uniform(-6, W + 6)
    sway = random.uniform(-16, 16)          # tip lean
    wob = random.uniform(2, 7)              # waviness amplitude
    phase = random.uniform(0, 6.28)
    length = random.uniform(0.82, 1.0)      # fraction of height
    w_root = random.uniform(1.6, 3.0)
    j = random.uniform(-26, 26)             # per-strand colour jitter
    segs = 26
    pts = []
    for s in range(segs + 1):
        t = s / segs
        y = H - 1 - t * length * (H - 8)
        x = x0 + sway * t * t + wob * (1 - t) * __import__("math").sin(phase + t * 5.0)
        pts.append((x, y, t))
    for s in range(segs):
        x1, y1, t1 = pts[s]; x2, y2, t2 = pts[s + 1]
        tm = (t1 + t2) / 2
        base = lerp(ROOT, MID, tm * 1.6) if tm < 0.62 else lerp(MID, TIP, (tm - 0.62) / 0.38)
        col = tuple(max(0, min(255, c + int(j))) for c in base)
        alpha = int(255 * min(1.0, tm * 6 + 0.55) * (1.0 - max(0.0, (tm - 0.86) / 0.14) ** 1.5))
        wdt = w_root * (1.0 - tm * 0.82)
        dr.line([x1, y1, x2, y2], fill=col + (alpha,), width=max(1, int(round(wdt))))
# underfur wash: faint broad strokes so card interiors are not hollow
img.save("/home/hatch/workspace/anthroforge-v2/fur-craft/a12-shading/textures/fur_card_a12.png")
a = img.getchannel("A")
print("saved; alpha extrema", a.getextrema(), "mean alpha", sum(a.getdata()) / (W * H))
