"""Remap fur_cards_lod0.glb onto fur_atlas_2048.png (single image/texture/
material; TEXCOORD_0 rewritten into the DENSE/SPARSE usable rects).
Loads the saved atlas + layout, so it can rerun without rebuilding the atlas.
"""
import json, struct
from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path("/home/hatch/workspace/anthroforge-v2")
SRC = ROOT / "fur-prototype"
OUT = ROOT / "fur-craft" / "a13-atlas"

layout = json.loads((OUT / "fur_atlas_layout.json").read_text())["slots"]
atlas_img = Image.open(OUT / "fur_atlas_2048.png")
atlas_png = BytesIO(); atlas_img.save(atlas_png, format="PNG"); atlas_png = atlas_png.getvalue()

src = (SRC / "fur_cards_lod0.glb").read_bytes()
jlen = struct.unpack("<I", src[12:16])[0]
g = json.loads(src[20:20 + jlen])
bin_off = 20 + jlen + 8
old_bin = src[bin_off:]

def view_bytes(bvi):
    bv = g["bufferViews"][bvi]
    off = bv.get("byteOffset", 0)
    return old_bin[off:off + bv["byteLength"]]

slot_for_mat = {0: 0, 1: 1}
uv_payloads = {}
for mesh in g["meshes"]:
    for prim in mesh["primitives"]:
        u0, v0, u1, v1 = layout[slot_for_mat[prim["material"]]]["uv_gltf"]
        ai = prim["attributes"]["TEXCOORD_0"]
        acc = g["accessors"][ai]
        payload = bytearray(view_bytes(acc["bufferView"]))
        aoff = acc.get("byteOffset", 0)
        n = acc["count"] * 8
        uv = np.frombuffer(bytes(payload[aoff:aoff + n]), dtype="<f4").reshape(-1, 2).copy()
        uv[:, 0] = u0 + uv[:, 0] * (u1 - u0)
        uv[:, 1] = v0 + uv[:, 1] * (v1 - v0)
        payload[aoff:aoff + n] = uv.astype("<f4").tobytes()
        uv_payloads[acc["bufferView"]] = bytes(payload)

img_views = {im["bufferView"] for im in g["images"]}
new_views, new_bin = [], bytearray()
def add_view(payload, target=None):
    while len(new_bin) % 4:
        new_bin.extend(b"\x00")
    nv = {"buffer": 0, "byteOffset": len(new_bin), "byteLength": len(payload)}
    if target is not None:
        nv["target"] = target
    new_bin.extend(payload)
    new_views.append(nv)
    return len(new_views) - 1

view_map = {}
for bvi, bv in enumerate(g["bufferViews"]):
    if bvi in img_views:
        view_map[bvi] = None
        continue
    payload = uv_payloads.get(bvi, view_bytes(bvi))
    view_map[bvi] = add_view(payload, bv.get("target"))
atlas_view = add_view(atlas_png)

for acc in g["accessors"]:
    acc["bufferView"] = view_map[acc["bufferView"]]
g["bufferViews"] = new_views
g["buffers"] = [{"byteLength": len(new_bin)}]
g["images"] = [{"bufferView": atlas_view, "mimeType": "image/png", "name": "fur_atlas_2048"}]
g["textures"] = [{"sampler": 0, "source": 0}]
g["materials"] = [{
    "name": "FurCardAtlas", "doubleSided": True, "alphaMode": "BLEND",
    "pbrMetallicRoughness": {"baseColorTexture": {"index": 0},
                             "metallicFactor": 0.0, "roughnessFactor": 0.85},
}]
for mesh in g["meshes"]:
    for prim in mesh["primitives"]:
        prim["material"] = 0

jb = json.dumps(g).encode()
while len(jb) % 4:
    jb += b" "
while len(new_bin) % 4:
    new_bin.extend(b"\x00")
outb = bytearray(b"glTF" + struct.pack("<II", 2, 12 + 8 + len(jb) + 8 + len(new_bin)))
outb += struct.pack("<I", len(jb)) + b"JSON" + jb
outb += struct.pack("<I", len(new_bin)) + b"BIN\x00" + new_bin
(OUT / "fur_cards_lod0_atlas.glb").write_bytes(bytes(outb))
print("remapped GLB:", len(outb), "bytes (orig", len(src), ")")

# self-check: re-read and confirm UV ranges sit inside the right rects
d2 = bytes(outb)
jl2 = struct.unpack("<I", d2[12:16])[0]
g2 = json.loads(d2[20:20 + jl2])
bo2 = 20 + jl2 + 8
for pi, prim in enumerate(g2["meshes"][0]["primitives"]):
    acc = g2["accessors"][prim["attributes"]["TEXCOORD_0"]]
    bv = g2["bufferViews"][acc["bufferView"]]
    off = bo2 + bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
    uv = np.frombuffer(d2, dtype="<f4", count=acc["count"] * 2, offset=off).reshape(-1, 2)
    u0, v0, u1, v1 = layout[pi]["uv_gltf"]
    print(f"prim{pi}: u[{uv[:,0].min():.4f},{uv[:,0].max():.4f}] in [{u0:.4f},{u1:.4f}] | "
          f"v[{uv[:,1].min():.4f},{uv[:,1].max():.4f}] in [{v0:.4f},{v1:.4f}] | n={acc['count']}")
