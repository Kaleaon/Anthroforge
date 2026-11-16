#!/usr/bin/env python3
"""
AnthroForge A11 — contact sheet + distance-read test.

Panels:
  1. Shaft atlas, labelled (one row per profile, root left -> tip right)
  2. Single hairs magnified (wolf guard / tabby ground / tabby stripe)
  3. Card textures on a dark pelt backing
  4. Coat-level diffuse (shell tint / texture floor) + driving mask
  5. DISTANCE TEST: cards optically mixed (downscale->upscale) beside
     the flat integral ("distance") colour of the same profile. The
     prediction from FUR_COLOUR.md: banding vanishes, the wolf reads
     as its integral grizzle, and the tabby stripe boundary SURVIVES
     because it is a population difference, not a banding difference.
"""
import json
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TEX = os.path.join(ROOT, "textures")
REN = os.path.join(ROOT, "renders")
BG = (22, 22, 26)
FG = (232, 232, 232)
SUB = (150, 150, 160)
BACKING = (30, 26, 24)

try:
    FONT = ImageFont.load_default(size=21)
    FONT_B = ImageFont.load_default(size=25)
except TypeError:
    FONT = ImageFont.load_default()
    FONT_B = FONT


def load(name):
    return Image.open(os.path.join(TEX, name))


CARD_BACKING = (104, 92, 78)   # mid-tone pelt backing: dark hairs stay readable


def on_backing(rgba, size=None, backing=BACKING):
    im = rgba.convert("RGBA")
    if size:
        im = im.resize(size)
    back = Image.new("RGBA", im.size, backing + (255,))
    back.alpha_composite(im)
    return back.convert("RGB")


def dist_mix(rgba, out_size=(256, 512)):
    """Optical mixing: shrink to a few texels per hair, blow back up."""
    small = rgba.convert("RGBA").resize((20, 40), Image.BILINEAR)
    return on_backing(small.resize(out_size, Image.BILINEAR), backing=CARD_BACKING)


def main():
    with open(os.path.join(TEX, "fur_colour_profiles.json")) as f:
        profiles = json.load(f)["profiles"]

    W = 1680
    sheet = Image.new("RGB", (W, 2760), BG)
    dr = ImageDraw.Draw(sheet)
    dr.text((28, 18), "A11 FUR COLOUR — agouti banding x coat pattern", font=FONT_B, fill=FG)

    # ---- panel 1: shaft atlas
    y = 70
    dr.text((28, y), "1  SHAFT ATLAS — one hair, root (left) to tip (right)", font=FONT, fill=FG)
    atlas = load("shaft_atlas.png").resize((1100, 7 * 44))
    sheet.paste(atlas, (28, y + 34))
    names = list(profiles.keys())
    for i, nm in enumerate(names):
        yy = y + 34 + i * 44
        dr.text((1148, yy + 4), nm, font=FONT, fill=FG)
        dr.text((1148, yy + 26), "distance " + profiles[nm]["distance_colour"],
                font=FONT, fill=SUB)
    y += 34 + 7 * 44 + 26

    # ---- panel 2: magnified single hairs
    dr.text((28, y), "2  SINGLE HAIRS MAGNIFIED — band sequence along the shaft", font=FONT, fill=FG)
    sys_path = os.path.join(HERE, "gen_fur_colour.py")
    import importlib.util
    spec = importlib.util.spec_from_file_location("gfc", sys_path)
    gfc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gfc)
    hairs = [("wolf.guard.dorsal", "wolf guard"), ("tabby.ground", "tabby ground"),
             ("tabby.stripe", "tabby stripe (melanic)")]
    x = 28
    for key, label in hairs:
        bands, mel = gfc.PROFILES[key]
        prof = gfc.profile_from_bands(bands, mel, 640)
        strip = np.repeat(prof[None, :, :], 92, axis=0)          # (92, 640, 3)
        img = Image.fromarray((np.transpose(strip, (1, 0, 2)) * 255).astype(np.uint8))
        # taper: alpha wedge so it reads as a hair silhouette
        wedge = np.repeat(np.linspace(1.0, 0.25, 640)[:, None], 92, axis=1)
        alpha = Image.fromarray((wedge * 255).astype(np.uint8), "L")
        hair = img.convert("RGBA")
        hair.putalpha(alpha.point(lambda v: v))
        back = Image.new("RGBA", hair.size, BACKING + (255,))
        back.alpha_composite(hair)
        sheet.paste(back.convert("RGB"), (x, y + 36))
        dr.text((x, y + 36 + 648), label, font=FONT, fill=FG)
        x += 540
    y += 36 + 640 + 44

    # ---- panel 3: cards
    dr.text((28, y), "3  CARD TEXTURES — population of hairs (baked strand alpha, A11 colour)", font=FONT, fill=FG)
    cards = [("card_wolf_agouti_a.png", "wolf agouti guard"),
             ("card_tabby_ground.png", "tabby ground"),
             ("card_tabby_boundary.png", "tabby stripe boundary ->"),
             ("card_wolf_undercoat.png", "wolf undercoat")]
    x = 28
    for fn, label in cards:
        im = on_backing(load(fn), (392, 392) if "undercoat" in fn else (392, 784),
                        backing=CARD_BACKING)
        sheet.paste(im, (x, y + 36))
        dr.text((x, y + 36 + im.size[1] + 6), label, font=FONT, fill=FG)
        x += 408
    y += 36 + 784 + 44

    # ---- panel 4: coat level + distance test
    dr.text((28, y), "4  COAT LEVEL (shell tint) + DISTANCE TEST (optical mix vs integral colour)", font=FONT, fill=FG)
    coat_w = load("coat_wolf_dorsal.png").resize((392, 392))
    coat_t = load("coat_tabby.png").resize((392, 392))
    sheet.paste(coat_w, (28, y + 36))
    sheet.paste(coat_t, (436, y + 36))
    dr.text((28, y + 36 + 398), "coat: wolf dorsal", font=FONT, fill=FG)
    dr.text((436, y + 36 + 398), "coat: tabby (stripes mask drives fur)", font=FONT, fill=FG)
    # distance test pair
    for i, (fn, key, label) in enumerate([
            ("card_wolf_agouti_a.png", "wolf.guard.dorsal", "wolf at distance"),
            ("card_tabby_boundary.png", None, "tabby boundary at distance")]):
        xx = 844 + i * 408
        sheet.paste(dist_mix(load(fn), (392, 392)), (xx, y + 36))
        dr.text((xx, y + 36 + 398), label, font=FONT, fill=FG)
        if key:
            dc = profiles[key]["distance_colour"]
            rgb = tuple(int(dc.lstrip('#')[j:j + 2], 16) for j in (0, 2, 4))
            sw = Image.new("RGB", (392, 60), rgb)
            sheet.paste(sw, (xx, y + 36 + 434))
            dr.text((xx, y + 36 + 500), "integral colour " + dc, font=FONT, fill=SUB)

    sheet.save(os.path.join(REN, "contact_sheet.png"))
    print("wrote renders/contact_sheet.png", sheet.size)


if __name__ == "__main__":
    main()
