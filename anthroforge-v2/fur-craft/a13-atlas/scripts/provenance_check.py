import json, struct, hashlib
from pathlib import Path
for lod in ("lod0","lod1","lod2"):
    p = Path(f"/home/hatch/workspace/anthroforge-v2/fur-prototype/fur_cards_{lod}.glb")
    data = p.read_bytes()
    jlen = struct.unpack("<I", data[12:16])[0]
    g = json.loads(data[20:20+jlen])
    bin_off = 20 + jlen + 8
    print(lod, "materials:", [(m.get("name"), m.get("alphaMode"), m.get("doubleSided")) for m in g.get("materials",[])])
    for i, im in enumerate(g.get("images", [])):
        bv = g["bufferViews"][im["bufferView"]]
        off = bin_off + bv.get("byteOffset",0)
        raw = data[off:off+bv["byteLength"]]
        print(f"   image{i} {im.get('name')}: {len(raw)} B sha {hashlib.sha256(raw).hexdigest()[:12]}")
