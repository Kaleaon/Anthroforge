"""Post: labelled lineup crop + close-up montage."""
from PIL import Image, ImageDraw, ImageFont
R = "/home/hatch/workspace/anthroforge-v2/fur-craft/a14-shortfur/renders/"
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)

# --- lineup crop with labels (screen order L->R: T3, T2, T1, BASE) ---
im = Image.open(R + "render_lineup.png").convert("RGB")
crop = im.crop((0, 195, 1280, 505))
bar = 44
out = Image.new("RGB", (1280, crop.height + bar), (24, 24, 26))
out.paste(crop, (0, 0))
d = ImageDraw.Draw(out)
for x, label in [(205, "T3 PELT"), (490, "T2 SHELLS"), (773, "T1 VELVET"), (1058, "BASE")]:
    d.text((x, crop.height + bar // 2), label, fill=(235, 235, 240), font=font, anchor="mm")
out.save(R + "lineup_labelled.png")
print("lineup_labelled", out.size)

# --- close-up montage ---
panels = [("render_close_ctrl.png", "BASE (control)"),
          ("render_close_t1.png", "T1 VELVET SHEEN"),
          ("render_close_t3.png", "T3 PELT TEXTURE"),
          ("render_close_t2.png", "T2 SHELL MICRO")]
ims = [Image.open(R + f).convert("RGB") for f, _ in panels]
w, h = ims[0].size
bar2 = 46
m = Image.new("RGB", (w * 4 + 30, h + bar2), (24, 24, 26))
dm = ImageDraw.Draw(m)
font2 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
for i, (img, (_, label)) in enumerate(zip(ims, panels)):
    x = i * (w + 10)
    m.paste(img, (x, bar2))
    dm.text((x + w // 2, bar2 // 2), label, fill=(235, 235, 240), font=font2, anchor="mm")
m.save(R + "montage_closeups.png")
print("montage", m.size)
