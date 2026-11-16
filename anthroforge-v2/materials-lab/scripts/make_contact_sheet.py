#!/usr/bin/env python3
"""Stitch the 8 material swatches + head render into one labelled 3x3 contact sheet."""
import os
from PIL import Image, ImageDraw

LAB = os.path.expanduser("~/workspace/anthroforge-v2/materials-lab")
TILES = [
    ("swatch_skin_smooth.png", "skin_smooth - bare skin"),
    ("swatch_skin_furred_base.png", "skin_furred_base - undercoat floor"),
    ("swatch_nose_leather.png", "nose_leather - Poly Haven grain"),
    ("swatch_teeth_enamel.png", "teeth_enamel - warm SSS"),
    ("swatch_claw_keratin.png", "claw_keratin - anisotropic streaks"),
    ("swatch_eye.png", "eye - iris ball + cornea shell"),
    ("swatch_tongue_mouth.png", "tongue_mouth - saliva coat"),
    ("swatch_scar_tissue.png", "scar_tissue - derived pale"),
    ("head_skin_smooth.png", "HEAD - skin_smooth on neutral base head v1"),
]
TILE = 512
LABEL = 34
cols, rows = 3, 3
sheet = Image.new("RGB", (cols * TILE, rows * (TILE + LABEL)), (24, 24, 26))
d = ImageDraw.Draw(sheet)
for i, (fn, label) in enumerate(TILES):
    p = os.path.join(LAB, "renders", fn)
    img = Image.open(p).convert("RGB")
    img.thumbnail((TILE, TILE))
    x = (i % cols) * TILE + (TILE - img.width) // 2
    y = (i // cols) * (TILE + LABEL)
    sheet.paste(img, (x, y))
    d.text(((i % cols) * TILE + 10, y + TILE + 9), label, fill=(235, 230, 220))
out = os.path.join(LAB, "swatch_sheet.png")
sheet.save(out)
print("wrote", out, sheet.size)
