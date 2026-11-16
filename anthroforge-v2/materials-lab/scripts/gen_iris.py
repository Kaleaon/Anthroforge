#!/usr/bin/env python3
"""Generate an equirect iris texture for a UV sphere (pupil at the +Z pole).

Layout by polar angle theta from the pole:
  theta < 0.18 rad        -> pupil (black)
  0.18 .. 0.85 rad        -> iris (amber, radial fibres drawn as vertical streaks)
  theta > 0.85 rad        -> sclera (off-white, slight vein tint at the far edge)
Blender UV spheres map v=1 to the +Z pole, so bands are horizontal in texture space
and fibre streaks are vertical stripes whose brightness is modulated per-column.
"""
import math, random
from PIL import Image

W, H = 1024, 512
random.seed(7)

# per-column fibre phase/brightness so streaks look organic, not printed
cols = []
for x in range(W):
    phase = random.uniform(0, math.tau)
    amp = random.uniform(0.55, 1.0)
    freq = random.choice([46, 61, 83, 109])
    cols.append((phase, amp, freq))

def srgb(c):
    return tuple(max(0, min(255, int(v))) for v in c)

AMBER_DARK = (122, 74, 22)
AMBER_MID = (176, 122, 42)
AMBER_LIGHT = (217, 164, 65)
LIMBAL = (58, 36, 14)
SCLERA = (221, 214, 196)
PUPIL = (5, 4, 4)

img = Image.new("RGB", (W, H))
px = img.load()
for y in range(H):
    v = 1.0 - (y + 0.5) / H          # v=1 at top row -> pole
    theta = (1.0 - v) * math.pi      # polar angle from +Z pole
    for x in range(W):
        u = x / W
        if theta < 0.18:
            col = PUPIL
        elif theta < 0.85:
            t = (theta - 0.18) / (0.85 - 0.18)   # 0 at pupil edge, 1 at limbal ring
            phase, amp, freq = cols[x]
            fibre = 0.72 + 0.28 * amp * math.sin(u * freq * math.tau + phase)
            # radial gradient: light near pupil, mid amber, dark limbal ring
            if t < 0.55:
                base = tuple(AMBER_LIGHT[i] + (AMBER_MID[i] - AMBER_LIGHT[i]) * (t / 0.55) for i in range(3))
            else:
                base = tuple(AMBER_MID[i] + (LIMBAL[i] - AMBER_MID[i]) * ((t - 0.55) / 0.45) for i in range(3))
            col = tuple(base[i] * fibre for i in range(3))
            # collarette ring
            if 0.30 < t < 0.38:
                col = tuple(c * 0.8 for c in col)
        else:
            # sclera with faint reddish veining toward the equator
            vein = 0.94 + 0.06 * math.sin(u * 40 * math.tau + y * 0.11)
            col = tuple(SCLERA[i] * vein for i in range(3))
        px[x, y] = srgb(col)

out = __file__.rsplit("/", 2)[0] + "/textures/iris_amber.png"
img.save(out)
print("wrote", out)
