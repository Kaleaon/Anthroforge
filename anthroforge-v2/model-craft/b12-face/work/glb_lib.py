import json, struct
import numpy as np

def load_glb(path):
    data = open(path, "rb").read()
    assert data[:4] == b"glTF"
    jlen = struct.unpack("<I", data[12:16])[0]
    gltf = json.loads(data[20:20+jlen])
    c1 = 20 + jlen
    blen = struct.unpack("<I", data[c1:c1+4])[0]
    bin_chunk = data[c1+8:c1+8+blen]
    return gltf, bin_chunk

def acc_data(gltf, bin_chunk, i):
    a = gltf["accessors"][i]; bv = gltf["bufferViews"][a["bufferView"]]
    ncomp = {"SCALAR":1,"VEC2":2,"VEC3":3,"VEC4":4}[a["type"]]
    dt = {5126: np.float32, 5123: np.uint16, 5125: np.uint32}[a["componentType"]]
    stride = bv.get("byteStride")
    start = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    if stride and stride != ncomp * np.dtype(dt).itemsize:
        raw = np.frombuffer(bin_chunk, dtype=np.uint8, count=stride*a["count"], offset=start)
        raw = raw.reshape(a["count"], stride)[:, :ncomp*np.dtype(dt).itemsize]
        arr = raw.copy().view(dt).reshape(a["count"], ncomp)
    else:
        arr = np.frombuffer(bin_chunk, dtype=dt, count=a["count"]*ncomp, offset=start)
        arr = arr.reshape(a["count"], ncomp) if ncomp > 1 else arr
    return arr.reshape(-1) if ncomp == 1 else arr

def meshes(gltf, bin_chunk):
    out = {}
    for node in gltf["nodes"]:
        if "mesh" not in node: continue
        name = node.get("name", "?")
        prims = []
        for prim in gltf["meshes"][node["mesh"]]["primitives"]:
            pos = acc_data(gltf, bin_chunk, prim["attributes"]["POSITION"]).astype(np.float64)
            idx = acc_data(gltf, bin_chunk, prim["indices"]).astype(np.int64).reshape(-1, 3)
            prims.append((pos, idx))
        out[name] = prims
    return out

def edge_set(idx):
    e = set()
    for t in idx:
        for a, b in ((0,1),(1,2),(2,0)):
            e.add((min(t[a],t[b]), max(t[a],t[b])))
    return e
