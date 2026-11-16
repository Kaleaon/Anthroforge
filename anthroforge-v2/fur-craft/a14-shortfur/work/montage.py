"""Side-by-side close-up montage with labels (BASE / T1 / T2 / T3)."""
from PIL import Image, ImageDraw, ImageFont
R = "/home/hatch/workspace/anthroforge-v2/fur-craft/a14-shortfur/renders/"
panels = [("render_close_ctrl.png", "BASE (control)"),
          ("render_close_t1.png", "T1 VELVET SHEEN"),
          ("render_close_t3.png", "T3 PELT TEXTURE"),
          ("render_close_t2.png", "T2 SHELL MICRO")]
ims = [Image.open(R + f).convert("RGB") for f, _ in panels]
w, h = ims[0].size
bar = 46
out = Image.new("RGB", (w * 4 + 30, h + bar), (24, 24, 26))
d = ImageDraw.Draw(out)
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
except Exception:
    font = ImageFont.load_default()
for i, (im, (_, label)) in enumerate(zip(ims, panels)):
    x = i * (w + 10)
    out.paste(im, (x, bar))
    d.text((x + w // 2, bar // 2), label, fill=(235, 235, 240), font=font, anchor="mm")
out.save(R + "montage_closeups.png")
print("montage written", out.size)
