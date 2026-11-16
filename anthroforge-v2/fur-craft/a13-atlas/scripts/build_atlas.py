"""A13 fur atlas builder. (The GLB-remap stage at the end of this file is
superseded by scripts/remap_glb.py, which runs standalone off the saved
atlas + layout; this script's atlas/layout outputs are the canonical ones.)

Packs the fur-prototype's two production card bakes (standalone v2 PNGs --
the GLB-embedded copies in fur_cards_lod0.glb are the superseded v1 bake,
see FUR_ATLAS.md) into the AF-FUR-2048 atlas: 4x2 grid of 512x1024 cells,
16 px dilation pad inside every cell, 8 semantic slots. Also emits the
layout JSON and a UV-remapped LOD0 GLB (single material, single texture).
"""
import json, math, struct
from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path("/home/hatch/workspace/anthroforge-v2")
SRC = ROOT / "fur-prototype"
OUT = ROOT / "fur-craft" / "a13-atlas"
OUT.mkdir(parents=True, exist_ok=True)

AW = AH = 2048
CELL_W, CELL_H = 512, 1024
PAD = 16
UW, UH = CELL_W - 2 * PAD, CELL_H - 2 * PAD   # usable 480 x 992

# ---------- alpha renormalisation (ATLAS-ALPHA-1) ----------
# t1 is solved so DENSE (texture A) lands at ~0.15 coverage @ 0.5 cutoff:
# the raw bake's strands are ~1 texel wide, so a textbook curve leaves
# almost nothing above a 0.5 test (measured in FUR_ATLAS.md).
T0 = 0.02
def _solve_t1(a01, target=0.15):
    lo, hi = 0.05, 0.60
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        cov = float((np.clip((a01 - T0) / (mid - T0), 0, 1) >= 0.5).mean())
        if cov < target: hi = mid
        else: lo = mid
    return 0.5 * (lo + hi)
T1 = None  # set after A loads
def renorm_alpha(a01):
    return np.clip((a01 - T0) / (T1 - T0), 0.0, 1.0)

def coverage(a01, t=0.5):
    return float((a01 >= t).mean())

def mip_coverages(a01):
    out = [coverage(a01)]
    cur = a01
    for _ in range(4):
        cur = cur.reshape(cur.shape[0] // 2, 2, cur.shape[1] // 2, 2).mean(axis=(1, 3))
        out.append(coverage(cur))
    return [round(c, 4) for c in out]

def load_rgba(path):
    return np.asarray(Image.open(path).convert("RGBA")).astype(np.float32) / 255.0

def to_usable(rgba):
    im = Image.fromarray((np.clip(rgba, 0, 1) * 255).astype(np.uint8), "RGBA")
    return np.asarray(im.resize((UW, UH), Image.LANCZOS)).astype(np.float32) / 255.0

A = load_rgba(SRC / "fur_card_texture_a.png")
B = load_rgba(SRC / "fur_card_texture_b.png")
T1 = _solve_t1(A[:, :, 3])
print(f"ATLAS-ALPHA-1: t0={T0} t1={T1:.3f} (solved for A coverage@0.5 ~= 0.15)")
stats = {}
for name, img in (("A", A), ("B", B)):
    raw_a = img[:, :, 3]
    stats[name] = {
        "alpha_max_raw": round(float(raw_a.max()), 3),
        "coverage_raw_mips": mip_coverages(raw_a),
        "coverage_renorm_mips": mip_coverages(renorm_alpha(raw_a)),
    }
    print(name, stats[name])

def with_alpha(img, alpha):
    out = img.copy(); out[:, :, 3] = alpha; return out

Ar = with_alpha(A, renorm_alpha(A[:, :, 3]))
Br = with_alpha(B, renorm_alpha(B[:, :, 3]))

# ---------- slot variants (usable resolution) ----------
def mirror(img): return img[:, ::-1].copy()

CORE = with_alpha(Ar, np.clip(np.power(Ar[:, :, 3], 1.5) * 1.35, 0, 1))

# wide clump: centre half of A stretched to full width
clump_src = Ar[:, Ar.shape[1] // 4: 3 * Ar.shape[1] // 4]
CLUMP = to_usable(clump_src)

# thin/far: erode alpha (3x3 min) then scale
a_img = Image.fromarray((Ar[:, :, 3] * 255).astype(np.uint8))
eroded = np.asarray(a_img.filter(ImageFilter.MinFilter(3))).astype(np.float32) / 255.0
THIN = with_alpha(Ar, np.clip(eroded * 0.8, 0, 1))

# utility cell
util = np.zeros((UH, UW, 4), np.float32)
rows = np.linspace(1.0, 0.0, UH, dtype=np.float32)          # root(top)=1 -> tip=0
util[:, 0:96, 0:3] = rows[:, None, None]                     # gradient LUT strip
util[:, 0:96, 3] = 1.0
A_use = to_usable(Ar)
mean_col = A_use[:, :, :3].reshape(-1, 3).mean(axis=0)
puff_a = np.asarray(Image.fromarray((A_use[:, :, 3] * 255).astype(np.uint8))
                    .filter(ImageFilter.GaussianBlur(18))).astype(np.float32) / 255.0
puff = np.zeros((UH, UW, 4), np.float32)
puff[:, :, :3] = mean_col[None, None, :]
puff[:, :, 3] = renorm_alpha(puff_a)
util[:, 96:240] = puff[:, 96:240]
wisp_src = Br[:, Br.shape[1] // 2 - 32: Br.shape[1] // 2 + 32]
wisp = to_usable(wisp_src)
util[:, 240:336] = wisp[:, 240:336]
util[:, 336:480, 0:3] = Ar[8, 8, :3]                          # reserved: root colour, alpha 0
util[:, 336:480, 3] = 0.0

slots = [
    ("dense",    "DENSE_A",     to_usable(Ar),          "primary full-density card; LOD0/1 workhorse"),
    ("sparse",   "SPARSE_B",    to_usable(Br),          "low-density card; layering + cheap fill"),
    ("dense_mir","DENSE_A_MIR", to_usable(mirror(Ar)),  "U-mirror of dense: free silhouette variant"),
    ("sparse_mir","SPARSE_B_MIR", to_usable(mirror(Br)),"U-mirror of sparse"),
    ("core",     "CORE_A",      to_usable(CORE),        "high-coverage under-layer card (alpha^1.5 x1.35)"),
    ("clump",    "CLUMP_A",     CLUMP,                  "wide-clump card: centre crop of A, fewer thicker clumps"),
    ("thin_far", "THIN_FAR",    to_usable(THIN),        "eroded alpha x0.8: LOD2 / far cards"),
    ("utility",  "UTILITY",     util,                   "strips: gradient LUT | underfur puff | wisp | reserved"),
]

# ---------- compose atlas + dilate RGB into gutters ----------
atlas = np.zeros((AH, AW, 4), np.float32)
known = np.zeros((AH, AW), bool)
layout = []
for i, (key, name, img, role) in enumerate(slots):
    cx, cy = (i % 4) * CELL_W, (i // 4) * CELL_H
    ux, uy = cx + PAD, cy + PAD
    atlas[uy:uy + UH, ux:ux + UW] = img
    known[uy:uy + UH, ux:ux + UW] = True
    layout.append({
        "slot": i, "key": key, "name": name, "role": role,
        "cell_px": [cx, cy, CELL_W, CELL_H],
        "usable_px": [ux, uy, UW, UH],
        "uv_image_space": [ux / AW, uy / AH, (ux + UW) / AW, (uy + UH) / AH],
        # glTF: v = 1 - (row from top)/H  ->  v0 is the rect's BOTTOM in image rows (tip), v1 the top (root)
        "uv_gltf": [ux / AW, 1 - (uy + UH) / AH, (ux + UW) / AW, 1 - uy / AH],
    })

rgb = atlas[:, :, :3].copy()
# Push-pull dilation: fill unknown (gutter) texels with plausible colour.
# Pyramid: weighted-downsample to 64px, fill, upsample back level by level.
def _down(rgbk, mask):
    h, w = mask.shape
    rgb2 = rgbk.reshape(h // 2, 2, w // 2, 2, 3).sum(axis=(1, 3))
    m2 = mask.reshape(h // 2, 2, w // 2, 2).sum(axis=(1, 3))
    return rgb2, m2
pyr = [(rgb * known[:, :, None], known.astype(np.float32))]
while pyr[-1][1].shape[0] > 64:
    pyr.append(_down(*pyr[-1]))
top_rgb, top_m = pyr[-1]
mean_col = (top_rgb.sum(axis=(0, 1)) / max(top_m.sum(), 1e-6))
filled_top = np.where(top_m[:, :, None] > 0, top_rgb / np.maximum(top_m[:, :, None], 1e-6), mean_col[None, None, :])
fill_img = Image.fromarray((np.clip(filled_top, 0, 1) * 255).astype(np.uint8))
for lvl in range(len(pyr) - 2, -1, -1):
    target = pyr[lvl][1].shape
    fill_img = fill_img.resize((target[1], target[0]), Image.BILINEAR)
    up = np.asarray(fill_img).astype(np.float32) / 255.0
    rk, mk = pyr[lvl]
    own = np.where(mk[:, :, None] > 0, rk / np.maximum(mk[:, :, None], 1e-6), 0.0)
    filled = np.where(mk[:, :, None] > 0, own, up)
    fill_img = Image.fromarray((np.clip(filled, 0, 1) * 255).astype(np.uint8))
gutter_rgb = np.asarray(fill_img).astype(np.float32) / 255.0
atlas[:, :, :3] = np.where(known[:, :, None], atlas[:, :, :3], gutter_rgb)
print("push-pull gutter fill done")

atlas_img = Image.fromarray((np.clip(atlas, 0, 1) * 255).astype(np.uint8), "RGBA")
atlas_img.save(OUT / "fur_atlas_2048.png")
print("atlas saved")

meta = {
    "atlas": "AF-FUR-2048", "size_px": [AW, AH], "cell_px": [CELL_W, CELL_H],
    "pad_px": PAD, "gutter_px_between_usable": 2 * PAD,
    "alpha_curve": "ATLAS-ALPHA-1: a' = clamp((a-0.02)/(t1-0.02)) with t1 solved so DENSE coverage@0.5 ~= 0.15; applied to raw Cycles coverage alpha at bake/pack time",
    "v_convention": "image row 0 (top) = ROOT, s increases downward to tip; glTF uv v = 1 - row/H (card root verts carry v at the rect's v1)",
    "source_stats": stats,
    "slots": layout,
    "utility_strips_usable_local_px": {
        "gradient_lut": [0, 96], "underfur_puff": [96, 240], "wisp": [240, 336], "reserved": [336, 480]},
}
(OUT / "fur_atlas_layout.json").write_text(json.dumps(meta, indent=1))
print("layout saved")

# ---------- remap LOD0 GLB to the atlas ----------
src_glb = (SRC / "fur_cards_lod0.glb").read_bytes()
jlen = struct.unpack("<I", src_glb[12:16])[0]
g = json.loads(src_glb[20:20 + jlen])
bin_off = 20 + jlen + 8
old_bin = src_glb[bin_off:]

def view_bytes(bvi):
    bv = g["bufferViews"][bvi]
    off = bv.get("byteOffset", 0)
    return old_bin[off:off + bv["byteLength"]]

# flipped atlas for embedding (glTF v origin): embed the authoring PNG as-is is
# NOT flipped -- glTF v = 1 - row/H is a UV-space statement; the sampler reads
# image rows top-first, so the PNG bytes go in unchanged.
buf = BytesIO(atlas_img.tobytes())  # placeholder, replaced below
atlas_png_bytes = BytesIO()
atlas_img.save(atlas_png_bytes, format="PNG")
atlas_png_bytes = atlas_png_bytes.getvalue()

new_views, new_bin = [], bytearray()
view_map = {}
def add_view(payload, target=None):
    while len(new_bin) % 4:
        new_bin.extend(b"\x00")
    nv = {"buffer": 0, "byteOffset": len(new_bin), "byteLength": len(payload)}
    if target is not None:
        nv["target"] = target
    new_bin.extend(payload)
    new_views.append(nv)
    return len(new_views) - 1

slot_for_mat = {0: 0, 1: 1}   # FurCardA -> slot 0, FurCardB -> slot 1
for mesh in g["meshes"]:
    for prim in mesh["primitives"]:
        slot = slot_for_mat[prim["material"]]
        u0, v0, u1, v1 = layout[slot]["uv_gltf"]   # v0=tip edge, v1=root edge
        ai = prim["attributes"]["TEXCOORD_0"]
        acc = g["accessors"][ai]
        payload = bytearray(view_bytes(acc["bufferView"]))
        aoff = acc.get("byteOffset", 0)
        uv = np.frombuffer(bytes(payload[aoff:aoff + acc["count"] * 8]), dtype="<f4").reshape(-1, 2).copy()
        uv[:, 0] = u0 + uv[:, 0] * (u1 - u0)
        uv[:, 1] = v0 + uv[:, 1] * (v1 - v0)     # orig v=1 (root) -> v1 (root edge) ✓
        payload[aoff:aoff + acc["count"] * 8] = uv.astype("<f4").tobytes()
        view_map[acc["bufferView"]] = (bytes(payload), g["bufferViews"][acc["bufferView"]].get("target"))

# copy every non-image bufferView (with the UV ones replaced), remap indices
img_views = {g["images"][i]["bufferView"] for i in range(len(g["images"]))}
for bvi, bv in enumerate(g["bufferViews"]):
    if bvi in img_views:
        view_map[bvi] = None
        continue
    if bvi not in view_map:
        view_map[bvi] = (view_bytes(bvi), bv.get("target"))
for bvi in range(len(g["bufferViews"])):
    if view_map[bvi] is not None:
        payload, target = view_map[bvi]
        view_map[bvi] = add_view(payload, target)
atlas_view = add_view(atlas_png_bytes)

for acc in g["accessors"]:
    acc["bufferView"] = view_map[acc["bufferView"]]
g["bufferViews"] = new_views
g["buffers"] = [{"byteLength": len(new_bin)}]
g["images"] = [{"bufferView": atlas_view, "mimeType": "image/png", "name": "fur_atlas_2048"}]
g["textures"] = [{"sampler": 0, "source": 0}]
g["materials"] = [{
    "name": "FurCardAtlas", "doubleSided": True, "alphaMode": "BLEND",
    "pbrMetallicRoughness": {"baseColorTexture": {"index": 0}, "metallicFactor": 0.0, "roughnessFactor": 0.85},
}]
for mesh in g["meshes"]:
    for prim in mesh["primitives"]:
        prim["material"] = 0

json_bytes = json.dumps(g).encode()
while len(json_bytes) % 4:
    json_bytes += b" "
while len(new_bin) % 4:
    new_bin.extend(b"\x00")
out = bytearray(b"glTF" + struct.pack("<II", 2, 12 + 8 + len(json_bytes) + 8 + len(new_bin)))
out += struct.pack("<I", len(json_bytes)) + b"JSON" + json_bytes
out += struct.pack("<I", len(new_bin)) + b"BIN\x00" + new_bin
(OUT / "fur_cards_lod0_atlas.glb").write_bytes(bytes(out))
print("remapped GLB saved:", len(out), "bytes (orig", len(src_glb), ")")
