#!/usr/bin/env python3
"""
A15 — Hand-painted canine back pelt, painted programmatically by the studied
hand method (see HANDPAINT.md):
  1. value block-in (4 values, big masses: dark saddle over the spine,
     warming flanks)          2. clump shadow pass (dark gaps between tufts)
  3. undercoat pass (short, soft, warm-grey strokes)
  4. guard-hair pass (tapered strokes, AGOUTI banding root->band->dark tip,
     grouped into clumps that share direction + tone)
  5. lit clump tops + sparse pale ticking   6. flyaways / edge breakup
The roughness map is painted from the SAME stroke events (roots rough,
guard tips smoother), never derived by a filter afterwards.
Texture space: u = across the back (flank-spine-flank), v = neck(top)->tail.
Flow: hairs stream toward the tail and spill outward off the spine,
like water off a roof -- the direction discipline every source insists on.
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

rng = np.random.default_rng(20261112)
W = H = 1024
CX = W / 2.0

# ---- palette (sable/agouti canine: GSD / wolf family) -------------------
ROOT_SHADOW = np.array([36, 25, 16], float)
SADDLE_DEEP = np.array([54, 37, 22], float)
MID_BROWN   = np.array([101, 70, 44], float)
TAN         = np.array([152, 112, 70], float)
CREAM       = np.array([206, 173, 122], float)
PALE        = np.array([228, 201, 154], float)
UNDERCOAT   = np.array([141, 119, 93], float)
TIP_BLACK   = np.array([26, 19, 13], float)


def mix(a, b, t):
    if isinstance(t, np.ndarray) and t.ndim == 2:
        t = t[..., None]
    return a + (b - a) * t


def saddle_factor(x):
    """1 at the spine, 0 at the flanks: where the dark blanket sits."""
    d = abs(x - CX) / (W * 0.5)
    return float(np.clip(1.15 - d * 1.25, 0.0, 1.0) ** 1.3)


def flow_dir(x, y):
    """Unit direction of hair growth at a point: toward tail (+y),
    spilling sideways off the spine; slight increase of splay lower down."""
    sx = (x - CX) / (W * 0.5)
    lat = 0.62 * math.tanh(sx * 2.2) * (0.75 + 0.35 * y / H)
    vx, vy = lat, 1.0
    # gentle large-scale waviness (cowlick weather), kept subtle
    vx += 0.10 * math.sin(y * 0.011 + x * 0.004)
    n = math.hypot(vx, vy)
    return vx / n, vy / n


def hair_color(t, sad, pale_tip=False):
    """Agouti banding along one guard hair: dark root -> pale band ->
    dark tip. The dark tip grows longer/ blacker inside the saddle."""
    if t < 0.28:
        c = mix(ROOT_SHADOW, MID_BROWN, t / 0.28)
    elif t < 0.62:
        c = mix(MID_BROWN, mix(TAN, CREAM, sad * 0.35), (t - 0.28) / 0.34)
    else:
        tip_col = mix(MID_BROWN * 0.72, TIP_BLACK, 0.35 + 0.65 * sad)
        c = mix(mix(TAN, CREAM, sad * 0.35), tip_col, (t - 0.62) / 0.38)
    if pale_tip:  # rare frosted/silver guard hair
        c = mix(c, PALE, max(0.0, (t - 0.55) / 0.45) * 0.8)
    return c


# ---- 1. VALUE BLOCK-IN ---------------------------------------------------
img = Image.new("RGB", (W, H), (90, 64, 40))
px = np.zeros((H, W, 3), float)
yy, xx = np.mgrid[0:H, 0:W]
sad = np.clip(1.15 - np.abs(xx - CX) / (W * 0.5) * 1.25, 0, 1) ** 1.3
# big soft value masses: dark saddle spine, warm mid flank, pale lower edge
base = mix(mix(TAN * 0.92, MID_BROWN, 0.35), SADDLE_DEEP, sad * 0.85)
base *= (0.94 + 0.10 * (yy / H))[..., None]               # slightly lighter toward tail
# low-frequency blotches so the masses are not a clean gradient
blotch = np.zeros((H, W))
for _ in range(260):
    bx, by = rng.uniform(0, W), rng.uniform(0, H)
    r = rng.uniform(40, 150)
    amp = rng.uniform(-0.10, 0.10)
    blotch += amp * np.exp(-(((xx - bx) ** 2 + (yy - by) ** 2) / (2 * r * r)))
base *= (1.0 + blotch)[..., None]
# spine part shadow: where the coat splits, the root shadow deepens
part = np.exp(-((xx - CX) ** 2) / (2 * 9.0 ** 2))
base = mix(base, ROOT_SHADOW[None, None, :], (part * 0.45)[..., None])
img = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))
draw = ImageDraw.Draw(img, "RGBA")

# ---- clumps: jittered grid; each owns direction bias + tone -------------
clumps = []
cell = 46
for gy in range(-1, H // cell + 2):
    for gx in range(-1, W // cell + 2):
        cxp = gx * cell + cell / 2 + rng.uniform(-13, 13)
        cyp = gy * cell + cell / 2 + rng.uniform(-13, 13)
        clumps.append({
            "x": cxp, "y": cyp,
            "tone": rng.uniform(-0.13, 0.13),        # value grouping per clump
            "warm": rng.uniform(-0.06, 0.06),
            "dirb": rng.uniform(-0.10, 0.10),        # direction bias, radians
            "lit": rng.uniform(0, 1),                # is this clump top lit?
        })

# ---- 2. CLUMP SHADOW PASS (dark gaps under/between tufts) ----------------
shadow_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sd = ImageDraw.Draw(shadow_layer)
for c in clumps:
    dx, dy = flow_dir(c["x"], c["y"])
    L = rng.uniform(40, 66)
    w0 = rng.uniform(12, 18)
    tipx, tipy = c["x"] + dx * L, c["y"] + dy * L
    px_, py_ = -dy, dx
    poly = [(c["x"] + px_ * w0, c["y"] + py_ * w0),
            (c["x"] - px_ * w0, c["y"] - py_ * w0),
            (tipx, tipy)]
    col = tuple(int(v) for v in ROOT_SHADOW) + (80,)
    sd.polygon(poly, fill=col)
shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(2.2))
img = Image.alpha_composite(img.convert("RGBA"), shadow_layer)
draw = ImageDraw.Draw(img, "RGBA")

# ---- 3. UNDERCOAT PASS (short, soft, warm grey-tan) ----------------------
uc_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ud = ImageDraw.Draw(uc_layer)
for _ in range(14000):
    x, y = rng.uniform(0, W), rng.uniform(0, H)
    dx, dy = flow_dir(x, y)
    a = rng.uniform(-0.14, 0.14)
    ca, sa = math.cos(a), math.sin(a)
    dx, dy = dx * ca - dy * sa, dx * sa + dy * ca
    L = rng.uniform(18, 38)
    tone = rng.uniform(0.82, 1.12)
    col = np.clip(UNDERCOAT * tone * (1 - 0.25 * saddle_factor(x)), 0, 255)
    ud.line([x, y, x + dx * L, y + dy * L],
            fill=tuple(int(v) for v in col) + (58,), width=3)
uc_layer = uc_layer.filter(ImageFilter.GaussianBlur(0.7))
img = Image.alpha_composite(img, uc_layer)
draw = ImageDraw.Draw(img, "RGBA")

# ---- 4+5. GUARD HAIRS in clumps (agouti banded) + lit tops ---------------
guard_events = []   # (points, saddle) replayed into the roughness map

def stroke_points(x, y, dx, dy, L, seg=11):
    pts = []
    ph = rng.uniform(0, math.tau)
    for i in range(seg + 1):
        t = i / seg
        wob = math.sin(ph + t * 2.4) * 1.6 * t
        px_, py_ = -dy, dx
        pts.append((x + dx * L * t + px_ * wob, y + dy * L * t + py_ * wob))
    return pts


def draw_guard(x, y, c, pale_tip=False, lit_boost=0.0):
    dx, dy = flow_dir(x, y)
    a = c["dirb"] + rng.uniform(-0.055, 0.055)   # clump discipline + whisper of jitter
    ca, sa = math.cos(a), math.sin(a)
    dx, dy = dx * ca - dy * sa, dx * sa + dy * ca
    L = rng.uniform(46, 94) * (0.9 + 0.25 * saddle_factor(x))
    sadv = saddle_factor(x)
    pts = stroke_points(x, y, dx, dy, L)
    w0 = rng.uniform(2.4, 3.4)
    tone = 1.0 + c["tone"] + lit_boost
    for i in range(len(pts) - 1):
        t = (i + 0.5) / (len(pts) - 1)
        col = hair_color(t, sadv, pale_tip) * tone
        col[0] *= 1.0 + c["warm"]
        col = np.clip(col, 0, 255)
        wdt = max(0.9, w0 * (1 - t) + 0.9 * t)
        draw.line([pts[i], pts[i + 1]], fill=tuple(int(v) for v in col) + (205,),
                  width=int(round(wdt)))
    guard_events.append((pts, sadv))
    return pts


for c in clumps:
    n = int(rng.integers(20, 30))
    for _ in range(n):
        x = c["x"] + rng.normal(0, 8)
        y = c["y"] + rng.normal(0, 11)
        if -20 <= x < W + 20 and -20 <= y < H + 20:
            draw_guard(x, y, c, pale_tip=(rng.random() < 0.035))
    # lit clump tops: a few shorter, paler strokes riding the top of the tuft
    if c["lit"] > 0.45:
        for _ in range(int(rng.integers(3, 7))):
            x = c["x"] + rng.normal(0, 7)
            y = c["y"] + rng.normal(0, 9)
            pts = draw_guard(x, y, c, lit_boost=0.11 * c["lit"])
            # extra pale kiss along the last third
            for i in range(len(pts) - 3, len(pts) - 1):
                draw.line([pts[i], pts[i + 1]], fill=(232, 208, 164, 52), width=1)

# ---- 5b. UNIFY: slight directional softening blended back (the
# "little blending to unify strokes" step) -------------------------------
_rgb = img.convert("RGB")
soft = _rgb.filter(ImageFilter.GaussianBlur(0.6))
img = Image.blend(_rgb, soft, 0.28).convert("RGBA")
draw = ImageDraw.Draw(img, "RGBA")

# ---- 6. FLYAWAYS + sparse dark accents -----------------------------------
for _ in range(220):
    x, y = rng.uniform(0, W), rng.uniform(0, H)
    dx, dy = flow_dir(x, y)
    L = rng.uniform(16, 42)
    col = PALE * rng.uniform(0.9, 1.05) if rng.random() < 0.6 else ROOT_SHADOW
    draw.line([x, y, x + dx * L, y + dy * L],
              fill=tuple(int(v) for v in np.clip(col, 0, 255)) + (58,), width=1)
# tail-edge tips: break the bottom edge with light strand ends
for _ in range(260):
    x = rng.uniform(0, W)
    dx, dy = flow_dir(x, H - 4)
    L = rng.uniform(8, 26)
    draw.line([x, H - 2, x + dx * L, H - 2 + dy * L],
              fill=(214, 182, 132, 150), width=1)

img = img.convert("RGB")
arr = np.asarray(img).astype(float)
arr *= 1.0 + rng.normal(0, 0.016, arr.shape[:2])[..., None]   # tooth
diffuse = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
diffuse.save("canine_back_diffuse.png")
diffuse.crop((300, 300, 620, 620)).resize((640, 640), Image.LANCZOS).save("detail_crop.png")

# ---- ROUGHNESS, painted from the same stroke events ----------------------
# white = rough. Roots/undercoat roughest; guard tips sleeker; gaps dusty.
rough = Image.new("L", (W, H), 216)                     # base ~0.85
rdraw_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
rl = ImageDraw.Draw(rdraw_layer)
for c in clumps:                                        # clump gaps stay rough
    dx, dy = flow_dir(c["x"], c["y"])
    rl.line([c["x"], c["y"], c["x"] + dx * 52, c["y"] + dy * 52],
            fill=(242, 242, 242, 52), width=11)
for pts, sadv in guard_events:
    n = len(pts) - 1
    for i in range(n):
        t = (i + 0.5) / n
        g = int(232 - 74 * t - 14 * sadv)               # root 232 -> tip ~158, saddle sleeker
        rl.line([pts[i], pts[i + 1]], fill=(g, g, g, 205),
                width=max(1, int(round(2.4 * (1 - t) + 0.8 * t))))
rough = Image.alpha_composite(rough.convert("RGBA"), rdraw_layer).convert("L")
rough = rough.filter(ImageFilter.GaussianBlur(0.8))
rarr = np.asarray(rough).astype(float)
rarr = np.clip(rarr + rng.normal(0, 5, rarr.shape), 118, 248)
Image.fromarray(rarr.astype(np.uint8)).save("canine_back_roughness.png")

print(f"guard strokes replayed: {len(guard_events)}, clumps: {len(clumps)}")
print("diffuse value range:", np.asarray(diffuse).min(), np.asarray(diffuse).max())
