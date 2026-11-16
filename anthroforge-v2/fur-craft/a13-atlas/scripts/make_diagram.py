"""UV-layout diagram for FUR_ATLAS.md: atlas grid + one annotated cell."""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path("/home/hatch/workspace/anthroforge-v2/fur-craft/a13-atlas")
layout = json.loads((OUT / "fur_atlas_layout.json").read_text())
F = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
def font(sz, bold=False): return ImageFont.truetype(FB if bold else F, sz)

atlas = Image.open(OUT / "fur_atlas_2048.png").convert("RGBA")
bg = Image.new("RGBA", atlas.size, (22, 22, 26, 255)); bg.alpha_composite(atlas)
thumb = bg.convert("RGB").resize((980, 980))

W, H = 2060, 1420
cv = Image.new("RGB", (W, H), (16, 16, 20))
d = ImageDraw.Draw(cv)
d.text((40, 26), "AF-FUR-2048 — fur card atlas layout & UV rules", font=font(34, True), fill=(240, 240, 235))
d.text((40, 72), "2048 x 2048 RGBA - 4 x 2 grid of 512 x 1024 cells - usable 480 x 992 (16 px dilation pad inside every cell)", font=font(21), fill=(170, 175, 185))

cv.paste(thumb, (40, 120))
OX, OY, SC = 40, 120, 980 / 2048
for s in layout["slots"]:
    cx, cy, cw, chh = s["cell_px"]; ux, uy, uw, uh = s["usable_px"]
    d.rectangle([OX + cx * SC, OY + cy * SC, OX + (cx + cw) * SC, OY + (cy + chh) * SC], outline=(90, 95, 110), width=2)
    d.rectangle([OX + ux * SC, OY + uy * SC, OX + (ux + uw) * SC, OY + (uy + uh) * SC], outline=(255, 190, 60), width=2)
    d.text((OX + ux * SC + 8, OY + uy * SC + 8), f"{s['slot']} {s['name']}", font=font(19, True), fill=(255, 210, 90))
d.text((40, 1120), "amber = usable rect (card UV domain) - cell border = grey - 16 px pad ring between them is dilated RGB, alpha 0", font=font(19), fill=(170, 175, 185))
d.text((40, 1152), "image row 0 (top) = ROOT for every slot - strands read downward, root -> tip", font=font(19), fill=(170, 175, 185))

# ---- enlarged cell schematic ----
SX, SY, SW, SH = 1120, 120, 560, 1120 // 2 + 380
d.text((SX, SY - 4), "one cell, enlarged", font=font(24, True), fill=(240, 240, 235))
cx0, cy0 = SX, SY + 44
cw2, ch2 = 300, 600
d.rectangle([cx0, cy0, cx0 + cw2, cy0 + ch2], outline=(90, 95, 110), width=3)
pad = int(16 / 512 * cw2)
d.rectangle([cx0 + pad, cy0 + pad, cx0 + cw2 - pad, cy0 + ch2 - pad], outline=(255, 190, 60), width=3)
# card inside usable
kx0, ky0, kx1, ky1 = cx0 + pad + 60, cy0 + pad, cx0 + cw2 - pad - 60, cy0 + ch2 - pad
for i in range(9):
    x = kx0 + (kx1 - kx0) * i / 8
    d.line([x, ky0, x + (6 if i % 2 else -4), ky1], fill=(150, 125, 90), width=3)
d.rectangle([kx0, ky0, kx1, ky1], outline=(120, 200, 255), width=2)
d.text((kx0 - 6, ky0 - 34), "ROOT  s=0", font=font(22, True), fill=(120, 220, 140))
d.text((kx0 - 6, ky1 + 10), "TIP  s=1", font=font(22, True), fill=(255, 140, 120))
d.line([kx1 + 26, ky0, kx1 + 26, ky1], fill=(230, 230, 230), width=3)
d.polygon([(kx1 + 26, ky1), (kx1 + 18, ky1 - 16), (kx1 + 34, ky1 - 16)], fill=(230, 230, 230))
d.text((kx1 + 40, (ky0 + ky1) // 2 - 12), "s", font=font(24, True), fill=(230, 230, 230))
tx = cx0 + cw2 + 24
notes = [
    ("cell 512 x 1024", True),
    ("amber rect = usable 480 x 992", False),
    ("pad ring: RGB dilated from the", False),
    ("usable edge; alpha stays 0", False),
    ("card UV spans the usable rect", False),
    ("exactly: u in [0,1] across,", False),
    ("s in [0,1] root -> tip", False),
    ("mirrored slots give the second", False),
    ("silhouette for free - same", False),
    ("geometry, slot +/- mirror", False),
    ("glTF: v = 1 - row/H, so the root", False),
    ("edge of a rect is its v1 side", False),
]
yy = cy0 + 6
for t, b in notes:
    d.text((tx, yy), t, font=font(20, b), fill=(215, 218, 225) if not b else (255, 210, 90))
    yy += 30

# ---- tier table ----
ty = cy0 + ch2 + 66
d.text((SX, ty), "tiers (same 8 slots, same semantics)", font=font(24, True), fill=(240, 240, 235))
rows = [
    ("AF-FUR-2048", "2048²", "512x1024 cells", "pad 16", "hero / desktop"),
    ("AF-FUR-1024", "1024²", "256x512 cells", "pad 8", "mobile / Mini App WebGL"),
    ("AF-FUR-512", "512²", "128x256 cells", "pad 4", "far LOD / low-end"),
]
yy = ty + 44
for r in rows:
    d.text((SX, yy), "  -  ".join(r), font=font(20), fill=(215, 218, 225)); yy += 32
d.text((SX, yy + 14), "companion maps (normal / ID / flow) reuse this exact grid - a slot means", font=font(20), fill=(170, 175, 185))
d.text((SX, yy + 44), "the same card in every map of the set", font=font(20), fill=(170, 175, 185))

cv.save(OUT / "uv_layout_diagram.png")
print("diagram saved", cv.size)
