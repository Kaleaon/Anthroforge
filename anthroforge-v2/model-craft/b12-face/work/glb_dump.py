from glb_lib import *
gltf, bin_chunk = load_glb("/home/hatch/workspace/anthroforge-v2/base-head-v3/neutral_base_head_v3.glb")
ms = meshes(gltf, bin_chunk)
tot_v = tot_t = 0
for name, prims in ms.items():
    for pi, (pos, idx) in enumerate(prims):
        e = edge_set(idx)
        val = np.zeros(len(pos), int)
        for a, b in e: val[a] += 1; val[b] += 1
        span = pos.max(0) - pos.min(0)
        tot_v += len(pos); tot_t += len(idx)
        print(f"{name}[{pi}]: verts={len(pos)} tris={len(idx)} edges={len(e)} "
              f"valence min/med/max={val.min()}/{int(np.median(val))}/{val.max()} "
              f"poles(v!=6)={int((val!=6).sum())} span={np.round(span,3)} centre={np.round(pos.mean(0),3)}")
print("TOTAL verts", tot_v, "tris", tot_t)
print("scene nodes:", [n.get("name") for n in gltf["nodes"]])
