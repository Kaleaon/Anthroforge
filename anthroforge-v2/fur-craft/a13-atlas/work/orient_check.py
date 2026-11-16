import numpy as np
from PIL import Image
for i, name in enumerate(("a","b")):
    emb = np.asarray(Image.open(f"/tmp/embedded_{i}.png")).astype(float)
    std = np.asarray(Image.open(f"/home/hatch/workspace/anthroforge-v2/fur-prototype/fur_card_texture_{name}.png").convert("RGBA")).astype(float)
    ea, sa = emb[...,3], std[...,3]
    def corr(x, y):
        x = x.ravel(); y = y.ravel()
        return float(np.corrcoef(x, y)[0,1])
    print(f"{name}: alpha corr embedded-vs-standalone same={corr(ea,sa):.3f} flipped={corr(ea,sa[::-1]):.3f}")
    h = ea.shape[0]
    bands = [ea[int(h*f):int(h*(f+0.1))].mean()/255 for f in np.arange(0,1,0.1)]
    print(f"    embedded alpha mean by row decile (top->bottom):", [round(float(b),3) for b in bands])
    a01 = ea/255.0
    print(f"    embedded coverage@0.5 mip0: {(a01>=0.5).mean():.3f}  coverage@0.35: {(a01>=0.35).mean():.3f}")
    cur = a01
    for lvl in range(1,5):
        cur = cur.reshape(cur.shape[0]//2,2,cur.shape[1]//2,2).mean(axis=(1,3))
        print(f"    naive mip{lvl} coverage@0.5: {(cur>=0.5).mean():.3f}")
