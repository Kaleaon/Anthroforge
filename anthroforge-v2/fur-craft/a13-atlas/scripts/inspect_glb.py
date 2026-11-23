import json, struct
import numpy as np
from PIL import Image
from io import BytesIO
from pathlib import Path

GLB = Path("/home/hatch/workspace/anthroforge-v2/fur-prototype/fur_cards_lod0.glb")
data = GLB.read_bytes()
assert data[:4] == b"glTF"
jlen = struct.unpack("<I", data[12:16])[0]
gltf = json.loads(data[20:20+jlen])
bin_off = 20 + jlen + 8
binchunk = data[bin_off:]

print("materials:", [m.get("name") for m in gltf.get("materials", [])])
print("images:", [(im.get("name"), im.get("mimeType"), im.get("bufferView")) for im in gltf.get("images", [])])
print("textures:", gltf.get("textures"))
for mi, mesh in enumerate(gltf["meshes"]):
    for pi, prim in enumerate(mesh["primitives"]):
        print(f"mesh{mi} prim{pi}: material={prim.get('material')} attrs={list(prim['attributes'])}")

def bv_bytes(bvi):
    bv = gltf["bufferViews"][bvi]
    off = bv.get("byteOffset", 0)
    return binchunk[off:off+bv["byteLength"]]

# extract embedded images
for i, im in enumerate(gltf.get("images", [])):
    raw = bv_bytes(im["bufferView"])
    img = Image.open(BytesIO(raw)).convert("RGBA")
    img.save(f"/tmp/embedded_{i}.png")
    print(f"embedded image {i}: size={img.size}")

# compare embedded vs standalone (flip test)
for i, name in enumerate(("a", "b")):
    emb = np.asarray(Image.open(f"/tmp/embedded_{i}.png")).astype(int)
    std = np.asarray(Image.open(f"/home/hatch/workspace/anthroforge-v2/fur-prototype/fur_card_texture_{name}.png").convert("RGBA")).astype(int)
    if emb.shape != std.shape:
        print(name, "shape mismatch", emb.shape, std.shape); continue
    d_same = np.abs(emb - std).mean()
    d_flip = np.abs(emb - std[::-1]).mean()
    print(f"texture {name}: mean|diff| vs standalone same={d_same:.3f} flipped={d_flip:.3f}")

# alpha coverage per row band -> which end is the root (roots = densest)
for name in ("a", "b"):
    img = Image.open(f"/home/hatch/workspace/anthroforge-v2/fur-prototype/fur_card_texture_{name}.png").convert("RGBA")
    a = np.asarray(img)[:, :, 3].astype(float) / 255.0
    h = a.shape[0]
    bands = [a[int(h*f):int(h*(f+0.1))].mean() for f in np.arange(0, 1, 0.1)]
    print(f"{name} alpha mean by row decile (top->bottom):", [round(float(b),3) for b in bands])
    cov05 = (a >= 0.5).mean()
    print(f"{name} coverage@0.5 mip0: {cov05:.3f}")
    # naive mip coverage decay
    cur = a
    for lvl in range(1, 5):
        cur = cur.reshape(cur.shape[0]//2, 2, cur.shape[1]//2, 2).mean(axis=(1, 3))
        print(f"   naive mip{lvl} coverage@0.5: {(cur >= 0.5).mean():.3f}")

# UV ranges per primitive
def acc_array(ai):
    acc = gltf["accessors"][ai]
    bv = gltf["bufferViews"][acc["bufferView"]]
    off = bin_off + bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
    ncomp = {"SCALAR":1, "VEC2":2, "VEC3":3, "VEC4":4}[acc["type"]]
    dt = {5126: np.float32, 5123: np.uint16, 5125: np.uint32}[acc["componentType"]]
    arr = np.frombuffer(data, dtype=dt, count=acc["count"]*ncomp, offset=off).reshape(acc["count"], ncomp)
    return arr

for mi, mesh in enumerate(gltf["meshes"]):
    for pi, prim in enumerate(mesh["primitives"]):
        uv = acc_array(prim["attributes"]["TEXCOORD_0"])
        print(f"mesh{mi} prim{pi} mat={prim.get('material')} UV u[{uv[:,0].min():.3f},{uv[:,0].max():.3f}] v[{uv[:,1].min():.3f},{uv[:,1].max():.3f}] nverts={len(uv)}")
