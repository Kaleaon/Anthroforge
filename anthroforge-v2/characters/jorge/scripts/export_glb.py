#!/usr/bin/env python3
"""Export Jorge's composed body as an unrigged static-bake GLB.

Geometry: MPFB macro base (body verts) + the four shipped
quantised component targets parsed back from disk (muscle +
chest.width + tissue.jorge + belly terminal x0.60), uniformly
scaled by the record export factor x1.39. NO rig, NO skin, NO
morphs, NO head, NO fur -- a body-shape bake for numeric/visual
shape work (Joe, Nov 16, 2026).

Axis mapping: canonical (x lateral, y depth, z height) -> glTF
(x, height, depth); the y/z swap is a reflection, so triangle
winding is reversed and smooth normals are recomputed from the
exported geometry -- the file is self-consistent.
"""
import json
import struct
import sys
from pathlib import Path

import numpy as np

V2 = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(V2 / "hyper/scripts"))
from hyper_common import BODY_END, load_base, load_macro, load_target

OUT = Path(__file__).resolve().parents[1]
TG = OUT / "targets"
SCALE = 1.39

V, F, Fb = load_base()
Vm = load_macro(V)
# Full triangulation from the correspondence file (the same face
# set the build's fold repair used, 26,756 body faces). NOTE:
# hyper_common's Fb keeps only the first triangle of each base.obj
# quad (13,378) -- fine for the fold gate's consistent subset, but
# the exported mesh must be complete.
_corr = np.load(V2 / "first-proof/work/correspondence.npz")
_tris = _corr["mh_tris"].astype(np.int64)
Fb = _tris[np.all(_tris < BODY_END, axis=1)]
print(f"export faces: {len(Fb)} (full triangulation)")
delta = sum(load_target(TG / n) for n in (
    "body.muscle.target", "body.chest.width.target",
    "body.tissue.jorge.target",
    "body.belly.protrusion_terminal_v51.target"))

pos = (Vm[:BODY_END] + delta[:BODY_END]) * SCALE
faces = Fb[:, [0, 2, 1]].copy()          # winding after axis swap
gltf_pos = pos[:, [0, 2, 1]].astype(np.float32)   # (x, height, depth)

# smooth vertex normals from the exported geometry
n = np.zeros_like(gltf_pos, dtype=np.float64)
p = gltf_pos.astype(np.float64)
fn = np.cross(p[faces[:, 1]] - p[faces[:, 0]],
              p[faces[:, 2]] - p[faces[:, 0]])
for c in range(3):
    np.add.at(n, faces[:, c], fn)
ln = np.linalg.norm(n, axis=1)
n = (n / np.maximum(ln, 1e-30)[:, None]).astype(np.float32)

idx = faces.astype(np.uint32)
pos_b = gltf_pos.tobytes()
nrm_b = n.tobytes()
idx_b = idx.tobytes()
bin_blob = pos_b + nrm_b + idx_b
bin_blob += b"\x00" * ((4 - len(bin_blob) % 4) % 4)

gltf = {
    "asset": {"version": "2.0",
              "generator": "anthroforge jorge export_glb.py"},
    "scene": 0,
    "scenes": [{"nodes": [0]}],
    "nodes": [{"mesh": 0,
               "name": "jorge_body — unrigged static bake, "
                       "export x1.39"}],
    "meshes": [{"name": "jorge_body",
                "primitives": [{
                    "attributes": {"POSITION": 0, "NORMAL": 1},
                    "indices": 2, "material": 0}]}],
    "materials": [{"name": "body (unrigged static bake)",
                   "pbrMetallicRoughness": {
                       "baseColorFactor": [0.62, 0.58, 0.55, 1.0],
                       "metallicFactor": 0.0,
                       "roughnessFactor": 0.9},
                   "doubleSided": False}],
    "bufferViews": [
        {"buffer": 0, "byteOffset": 0, "byteLength": len(pos_b),
         "target": 34962},
        {"buffer": 0, "byteOffset": len(pos_b),
         "byteLength": len(nrm_b), "target": 34962},
        {"buffer": 0, "byteOffset": len(pos_b) + len(nrm_b),
         "byteLength": len(idx_b), "target": 34963}],
    "accessors": [
        {"bufferView": 0, "componentType": 5126, "count": len(pos),
         "type": "VEC3",
         "min": gltf_pos.min(axis=0).tolist(),
         "max": gltf_pos.max(axis=0).tolist()},
        {"bufferView": 1, "componentType": 5126, "count": len(pos),
         "type": "VEC3"},
        {"bufferView": 2, "componentType": 5125, "count": idx.size,
         "type": "SCALAR"}],
    "buffers": [{"byteLength": len(bin_blob)}],
}
js = json.dumps(gltf).encode()
js += b" " * ((4 - len(js) % 4) % 4)
total = 12 + 8 + len(js) + 8 + len(bin_blob)
out = OUT / "jorge_body.glb"
with open(out, "wb") as fh:
    fh.write(struct.pack("<III", 0x46546C67, 2, total))
    fh.write(struct.pack("<II", len(js), 0x4E4F534A))
    fh.write(js)
    fh.write(struct.pack("<II", len(bin_blob), 0x004E4942))
    fh.write(bin_blob)
ext = gltf_pos.max(axis=0) - gltf_pos.min(axis=0)
print(f"wrote {out} ({total} bytes): {len(pos)} verts, "
      f"{len(faces)} tris; bbox W {ext[0]:.3f} x H {ext[1]:.3f} x "
      f"D {ext[2]:.3f} m at export scale x{SCALE}")
