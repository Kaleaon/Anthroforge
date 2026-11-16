import numpy as np
from PIL import Image
for i, name in enumerate(("a","b")):
    emb = np.asarray(Image.open(f"/tmp/embedded_{i}.png")).astype(float)
    std = np.asarray(Image.open(f"/home/hatch/workspace/anthroforge-v2/fur-prototype/fur_card_texture_{name}.png").convert("RGBA")).astype(float)
    print(f"--- {name}: embedded alpha max {emb[...,3].max():.0f} mean {emb[...,3].mean():.1f} | standalone alpha max {std[...,3].max():.0f} mean {std[...,3].mean():.1f}")
    m = (emb[...,3] > 25) & (std[...,3] > 25)
    print(f"    texels both alpha>25: {m.mean()*100:.1f}%  RGB mean|diff| there: {np.abs(emb[...,:3]-std[...,:3])[m].mean():.2f}  alpha mean|diff| there: {np.abs(emb[...,3]-std[...,3])[m].mean():.2f}")
    m2 = std[...,3] <= 2
    print(f"    standalone-transparent texels: {m2.mean()*100:.1f}%  embedded RGB mean there: {emb[...,:3][m2].mean():.2f}  standalone RGB mean there: {std[...,:3][m2].mean():.2f}")
    # alpha histogram
    a = std[...,3]
    print("    standalone alpha percentiles 50/90/99/99.9:", [round(float(np.percentile(a,p)),1) for p in (50,90,99,99.9)])
