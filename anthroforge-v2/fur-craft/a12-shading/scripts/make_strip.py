"""Comparison strip v2: A/B/C full frames, left-rim silhouette crops,
and the rim-mix failure mode as its own footer cell."""
from PIL import Image, ImageDraw, ImageFont

B = "/home/hatch/workspace/anthroforge-v2/fur-craft/a12-shading/renders/"
F = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
Fb = lambda s: ImageFont.truetype(F, s)

panels = [("a_plain.png", "A - plain alpha-card PBR"),
          ("b_sheen.png", "B - + sheen (KHR_materials_sheen)"),
          ("c_aniso_rim.png", "C - + aniso GGX + additive rim")]
PW, BAR = 512, 40
W = PW * 3 + 16
CROP_H = 352
FOOT = 208
strip = Image.new("RGB", (W, BAR + PW + 26 + CROP_H + 12 + FOOT), (18, 18, 20))
d = ImageDraw.Draw(strip)
for i, (fn, label) in enumerate(panels):
    x = i * (PW + 4)
    im = Image.open(B + fn).convert("RGB")
    strip.paste(im, (x, BAR))
    d.rectangle([x, 0, x + PW, BAR - 4], fill=(38, 38, 44))
    d.text((x + 10, 10), label, font=Fb(19), fill=(235, 230, 220))
    crop = im.crop((48, 176, 168, 336)).resize((264, CROP_H), Image.LANCZOS)
    strip.paste(crop, (x + 8, BAR + PW + 26))
    d.text((x + 10, BAR + PW + 4), "left silhouette x2.2", font=Fb(15), fill=(200, 195, 185))
fy = BAR + PW + 26 + CROP_H + 12
fail = Image.open(B + "c_rim_mix_failure.png").convert("RGB").resize((176, 176), Image.LANCZOS)
strip.paste(fail, (W - 188, fy))
d.rectangle([W - 188, fy + 178, W - 12, fy + 204], fill=(60, 30, 26))
d.text((W - 180, fy + 183), "Mix-Shader rim: FAILURE", font=Fb(12), fill=(255, 210, 190))
d.text((10, fy + 8), "Identical card geometry in A/B/C (same seed, 1,150 cards on a spherical-cap pelt).",
       font=Fb(16), fill=(200, 195, 185))
d.text((10, fy + 34), "Undercoat = materials-lab skin_furred_base in all three. C's rim is ADDITIVE (v2); the",
       font=Fb(16), fill=(200, 195, 185))
d.text((10, fy + 60), "Mix-Shader rim (right) replaces shading at grazing angles - flat patches, capped",
       font=Fb(16), fill=(200, 195, 185))
d.text((10, fy + 86), "highlights. Measured numbers and the full study: FUR_SHADING.md S4-S5.",
       font=Fb(16), fill=(200, 195, 185))
strip.save(B + "comparison_strip.png")
print("strip saved", strip.size)
