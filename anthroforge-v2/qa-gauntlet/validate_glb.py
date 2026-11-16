#!/usr/bin/env python3
"""
AnthroForge GLB QA harness — zero-install (stdlib struct/json + numpy).

Validates one GLB (or a directory of them) against the checks AnthroForge's
export gate cares about:

  * parses cleanly (GLB header/chunks, JSON, accessor bounds)
  * skin present: JOINTS_0 + WEIGHTS_0 on skinned primitives, joints list,
    inverse bind matrices
  * joint contract: joint names/count vs the AnthroForge 36-bone rig
  * morph targets: present / total count / max per primitive
  * geometry totals: meshes, primitives, vertices, triangles
  * textures: embedded (bufferView / data-URI) vs external (file URI)
  * degenerate triangles (zero-area), NaN/Inf vertices
  * scale sanity: world-space bounding box (node transforms applied);
    flag max extent < 0.1 m or > 10 m

Usage:
  validate_glb.py FILE.glb [--out DIR]
  validate_glb.py DIR [--out DIR] [--max N]

Writes <name>.qa.json per file into --out (default ./results) and prints a
one-line human summary per file. Exit code 0 unless a file fails to parse.
"""

import argparse
import json
import math
import os
import struct
import sys

import numpy as np

# ---------------------------------------------------------------- contract
# The AnthroForge 36-bone rig, verbatim from anthroforge_3d_pro_v2.html
# (BONE_HIERARCHY). Order matters for the app; the check compares as a set
# and also reports extras.
CONTRACT_BONES = [
    "Root", "Pelvis", "Spine1", "Chest", "Neck", "Head", "Jaw",
    "Ear_L", "Ear_R",
    "Shoulder_L", "Elbow_L", "Wrist_L",
    "Shoulder_R", "Elbow_R", "Wrist_R",
    "Hip_L", "Knee_L", "Ankle_L", "Foot_L",
    "Hip_R", "Knee_R", "Ankle_R", "Foot_R",
    "Wing_L1", "Wing_L2", "Wing_R1", "Wing_R2",
    "Tail_1", "Tail_2", "Tail_3",
    "GenBase", "GenScrot", "Gen01", "Gen02", "Gen03", "Gen04",
]
assert len(CONTRACT_BONES) == 36

# ---------------------------------------------------------------- glTF maps
COMP = {  # componentType -> (numpy dtype, size bytes)
    5120: (np.int8, 1), 5121: (np.uint8, 1),
    5122: (np.int16, 2), 5123: (np.uint16, 2),
    5125: (np.uint32, 4), 5126: (np.float32, 4),
}
NCOMP = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4,
         "MAT2": 4, "MAT3": 9, "MAT4": 16}


class GLBError(Exception):
    pass


def parse_glb(path):
    """Return (gltf_json_dict, bin_bytes). Raises GLBError on bad structure."""
    with open(path, "rb") as f:
        data = f.read()
    if len(data) < 20:
        raise GLBError("file too small for GLB header")
    magic, version, length = struct.unpack_from("<III", data, 0)
    if magic != 0x46546C67:  # 'glTF'
        raise GLBError("bad magic (not a GLB)")
    if version != 2:
        raise GLBError(f"unsupported GLB version {version}")
    if length != len(data):
        # Tolerate trailing padding but note it.
        pass
    off = 12
    gltf = None
    binbuf = b""
    while off + 8 <= len(data):
        clen, ctype = struct.unpack_from("<II", data, off)
        off += 8
        chunk = data[off:off + clen]
        if len(chunk) < clen:
            raise GLBError("chunk overruns file")
        if ctype == 0x4E4F534A:  # JSON
            try:
                gltf = json.loads(chunk.decode("utf-8"))
            except Exception as e:
                raise GLBError(f"JSON chunk undecodable: {e}")
        elif ctype == 0x004E4942:  # BIN\0
            binbuf = chunk
        off += clen
    if gltf is None:
        raise GLBError("no JSON chunk")
    return gltf, binbuf


def read_accessor(gltf, binbuf, idx):
    """Read an accessor into a numpy array shaped (count, ncomp)."""
    acc = gltf["accessors"][idx]
    if "sparse" in acc:
        raise GLBError(f"accessor {idx}: sparse accessors unsupported")
    bv_idx = acc.get("bufferView")
    if bv_idx is None:
        # Draco-compressed or all-zeros accessor.
        raise GLBError(f"accessor {idx}: no bufferView (draco?)")
    bv = gltf["bufferViews"][bv_idx]
    if bv.get("buffer", 0) != 0:
        raise GLBError(f"accessor {idx}: external buffer (not a self-contained GLB)")
    dtype, dsize = COMP[acc["componentType"]]
    ncomp = NCOMP[acc["type"]]
    count = acc["count"]
    start = bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
    stride = bv.get("byteStride")
    elem = dsize * ncomp
    raw = np.frombuffer(binbuf, dtype=np.uint8)
    if stride is None or stride == elem:
        end = start + elem * count
        if end > len(binbuf):
            raise GLBError(f"accessor {idx}: overruns BIN chunk")
        arr = np.frombuffer(binbuf, dtype=dtype, count=count * ncomp,
                            offset=start)
    else:
        # Interleaved: gather element by element via strided view.
        need = start + stride * (count - 1) + elem
        if need > len(binbuf):
            raise GLBError(f"accessor {idx}: overruns BIN chunk (strided)")
        base = np.frombuffer(binbuf, dtype=np.uint8,
                             count=stride * count, offset=start)
        arr = np.lib.stride_tricks.as_strided(
            base, shape=(count, stride), strides=(stride, 1))
        arr = arr[:, :elem].copy().view(dtype).reshape(count * ncomp)
    arr = arr.reshape(count, ncomp)
    if acc.get("normalized"):
        info = np.iinfo(dtype) if np.issubdtype(dtype, np.integer) else None
        if info is not None:
            arr = arr.astype(np.float32) / float(info.max)
    return arr


# ------------------------------------------------------------ node matrices
def quat_to_mat(q):
    x, y, z, w = q
    m = np.eye(4)
    m[0, 0] = 1 - 2 * (y * y + z * z); m[0, 1] = 2 * (x * y - z * w); m[0, 2] = 2 * (x * z + y * w)
    m[1, 0] = 2 * (x * y + z * w);     m[1, 1] = 1 - 2 * (x * x + z * z); m[1, 2] = 2 * (y * z - x * w)
    m[2, 0] = 2 * (x * z - y * w);     m[2, 1] = 2 * (y * z + x * w);     m[2, 2] = 1 - 2 * (x * x + y * y)
    return m


def node_local_matrix(node):
    if "matrix" in node:
        return np.array(node["matrix"], dtype=np.float64).reshape(4, 4).T
    m = np.eye(4)
    t = node.get("translation", [0, 0, 0])
    r = node.get("rotation", [0, 0, 0, 1])
    s = node.get("scale", [1, 1, 1])
    rot = quat_to_mat([float(v) for v in r])
    rot[:3, :3] *= np.array(s, dtype=np.float64)
    m[:3, :3] = rot[:3, :3]
    m[:3, 3] = t
    return m


def world_matrices(gltf):
    """node index -> 4x4 world matrix, via scene roots + children walk."""
    nodes = gltf.get("nodes", [])
    world = {}

    def walk(idx, parent):
        if idx in world:
            return
        m = parent @ node_local_matrix(nodes[idx])
        world[idx] = m
        for c in nodes[idx].get("children", []):
            walk(c, m)

    scenes = gltf.get("scenes", [])
    roots = []
    if scenes:
        roots = scenes[gltf.get("scene", 0)].get("nodes", [])
    for r in roots:
        walk(r, np.eye(4))
    # Any node unreachable from the scene still gets its local matrix.
    for i in range(len(nodes)):
        if i not in world:
            world[i] = node_local_matrix(nodes[i])
    return world


# ------------------------------------------------------------------ checks
def validate(path):
    rep = {
        "file": os.path.basename(path),
        "path": os.path.abspath(path),
        "size_bytes": os.path.getsize(path),
        "parses": False,
        "error": None,
    }
    try:
        gltf, binbuf = parse_glb(path)
    except GLBError as e:
        rep["error"] = str(e)
        return rep
    except Exception as e:  # unreadable file etc.
        rep["error"] = f"{type(e).__name__}: {e}"
        return rep
    rep["parses"] = True
    rep["generator"] = gltf.get("asset", {}).get("generator")
    rep["extensions_used"] = gltf.get("extensionsUsed", [])

    nodes = gltf.get("nodes", [])
    node_names = [n.get("name") for n in nodes]
    meshes = gltf.get("meshes", [])
    skins = gltf.get("skins", [])

    # ---- geometry totals, degenerate tris, NaN, world bbox
    total_verts = 0
    total_tris = 0
    degen = 0
    nan_verts = 0
    prim_count = 0
    morph_total = 0
    morph_max = 0
    prims_with_joints = 0
    prims_with_weights = 0
    bbox_min = np.array([np.inf] * 3)
    bbox_max = np.array([-np.inf] * 3)
    draco = "KHR_draco_mesh_compression" in rep["extensions_used"]
    accessor_errors = []

    world = world_matrices(gltf)
    node_mesh = {}  # mesh index -> first node world matrix using it
    for ni, n in enumerate(nodes):
        if "mesh" in n and n["mesh"] not in node_mesh:
            node_mesh[n["mesh"]] = world.get(ni, np.eye(4))

    for mi, mesh in enumerate(meshes):
        mat = node_mesh.get(mi, np.eye(4))
        for prim in mesh.get("primitives", []):
            prim_count += 1
            attrs = prim.get("attributes", {})
            targets = prim.get("targets", [])
            morph_total += len(targets)
            morph_max = max(morph_max, len(targets))
            if "JOINTS_0" in attrs:
                prims_with_joints += 1
            if "WEIGHTS_0" in attrs:
                prims_with_weights += 1
            if "POSITION" not in attrs:
                continue
            try:
                pos = read_accessor(gltf, binbuf, attrs["POSITION"]).astype(np.float64)
            except GLBError as e:
                accessor_errors.append(str(e))
                continue
            total_verts += len(pos)
            finite = np.isfinite(pos).all(axis=1)
            nan_verts += int((~finite).sum())
            if len(pos):
                wp = pos @ mat[:3, :3].T + mat[:3, 3]
                bbox_min = np.minimum(bbox_min, np.nanmin(wp, axis=0))
                bbox_max = np.maximum(bbox_max, np.nanmax(wp, axis=0))
            # triangles
            if "indices" in prim:
                try:
                    idx = read_accessor(gltf, binbuf, prim["indices"]).reshape(-1).astype(np.int64)
                except GLBError as e:
                    accessor_errors.append(str(e))
                    continue
                n_tri = len(idx) // 3
                total_tris += n_tri
                if n_tri:
                    tris = idx[:n_tri * 3].reshape(-1, 3)
                    a, b, c = pos[tris[:, 0]], pos[tris[:, 1]], pos[tris[:, 2]]
                    cross = np.cross(b - a, c - a)
                    area2 = np.einsum("ij,ij->i", cross, cross)
                    degen += int((area2 == 0).sum())
            else:
                n_tri = len(pos) // 3
                total_tris += n_tri
                if n_tri:
                    tris = pos[:n_tri * 3].reshape(-1, 3)
                    cross = np.cross(tris[:, 1] - tris[:, 0],
                                     tris[:, 2] - tris[:, 0])
                    area2 = np.einsum("ij,ij->i", cross, cross)
                    degen += int((area2 == 0).sum())

    rep["meshes"] = len(meshes)
    rep["primitives"] = prim_count
    rep["vertices"] = int(total_verts)
    rep["triangles"] = int(total_tris)
    rep["degenerate_triangles"] = int(degen)
    rep["nan_vertices"] = int(nan_verts)
    rep["morph_targets_total"] = int(morph_total)
    rep["morph_targets_max_per_primitive"] = int(morph_max)
    if accessor_errors:
        rep["accessor_errors"] = accessor_errors[:5]
    if draco:
        rep["draco"] = True

    if np.isfinite(bbox_min).all():
        dims = (bbox_max - bbox_min).tolist()
        rep["bbox_min"] = [round(v, 4) for v in bbox_min.tolist()]
        rep["bbox_max"] = [round(v, 4) for v in bbox_max.tolist()]
        rep["bbox_dims_m"] = [round(v, 4) for v in dims]
        rep["max_extent_m"] = round(float(max(dims)), 4)
        rep["scale_flag"] = ("too_small" if max(dims) < 0.1 else
                             "too_large" if max(dims) > 10 else None)
    else:
        rep["bbox_dims_m"] = None
        rep["max_extent_m"] = None
        rep["scale_flag"] = "no_geometry"

    # ---- textures
    images = gltf.get("images", [])
    emb = ext = 0
    for im in images:
        if "bufferView" in im:
            emb += 1
        elif str(im.get("uri", "")).startswith("data:"):
            emb += 1
        else:
            ext += 1
    rep["textures"] = {"total": len(images), "embedded": emb, "external": ext}
    rep["materials"] = len(gltf.get("materials", []))
    rep["animations"] = len(gltf.get("animations", []))

    # ---- skin + contract
    skin_rep = {"present": bool(skins), "count": len(skins)}
    best = None  # skin with the most contract matches
    for si, sk in enumerate(skins):
        joints = sk.get("joints", [])
        jnames = [node_names[j] if j < len(node_names) else None for j in joints]
        entry = {
            "index": si,
            "joint_count": len(joints),
            "joint_names": jnames,
            "has_inverse_bind_matrices": "inverseBindMatrices" in sk,
        }
        matches = [n for n in CONTRACT_BONES if n in jnames]
        entry["contract_matched"] = len(matches)
        entry["contract_missing"] = [n for n in CONTRACT_BONES if n not in jnames]
        entry["contract_extra"] = [n for n in jnames if n not in CONTRACT_BONES]
        if best is None or len(matches) > best["contract_matched"]:
            best = entry
    if best is not None:
        skin_rep.update(best)
        skin_rep["contract_full_match"] = (
            best["contract_matched"] == 36 and best["joint_count"] == 36)
    rep["skin"] = skin_rep
    rep["primitives_with_joints"] = prims_with_joints
    rep["primitives_with_weights"] = prims_with_weights

    # ---- status classification
    st = {}
    st["parse"] = "ok" if rep["parses"] else "fail"
    if not skins:
        st["skin"] = "warn"  # static assets legitimately have no skin
    elif not skin_rep.get("has_inverse_bind_matrices"):
        st["skin"] = "fail"
    elif prims_with_joints == 0 or prims_with_weights == 0:
        st["skin"] = "fail"  # skin declared but geometry carries no weights
    else:
        st["skin"] = "ok"
    if not skins:
        st["contract"] = "n/a"
    elif skin_rep.get("contract_full_match"):
        st["contract"] = "ok"
    elif skin_rep.get("contract_matched", 0) >= 30:
        st["contract"] = "warn"
    else:
        st["contract"] = "fail"
    st["morphs"] = "ok" if morph_total > 0 else "warn"
    st["textures"] = "fail" if ext > 0 else "ok"
    st["geometry"] = "fail" if (degen > 0 or nan_verts > 0) else "ok"
    st["scale"] = "ok" if rep["scale_flag"] is None else "warn"
    rep["status"] = st
    return rep


def summary_line(rep):
    if not rep["parses"]:
        return f"FAIL-PARSE  {rep['file']}: {rep['error']}"
    sk = rep["skin"]
    if sk["present"]:
        skin_s = (f"skin {sk['joint_count']}j "
                  f"contract {sk.get('contract_matched', 0)}/36")
    else:
        skin_s = "no skin"
    return (f"{rep['file']}: {rep['meshes']} meshes, "
            f"{rep['vertices']:,} v / {rep['triangles']:,} t, {skin_s}, "
            f"morphs {rep['morph_targets_total']}, "
            f"tex {rep['textures']['embedded']}emb/{rep['textures']['external']}ext, "
            f"degen {rep['degenerate_triangles']}, NaN {rep['nan_vertices']}, "
            f"extent {rep['max_extent_m']} m"
            + (f" [{rep['scale_flag']}]" if rep.get("scale_flag") else ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target", help="GLB file or directory")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(
        os.path.abspath(__file__)), "results"))
    ap.add_argument("--max", type=int, default=0, help="cap files (0 = all)")
    args = ap.parse_args()

    base = None
    if os.path.isdir(args.target):
        base = os.path.abspath(args.target)
        files = []
        for root, _dirs, names in os.walk(args.target):
            for n in sorted(names):
                if n.lower().endswith(".glb"):
                    files.append(os.path.join(root, n))
        files.sort()
    else:
        files = [args.target]
    if args.max:
        files = files[:args.max]

    os.makedirs(args.out, exist_ok=True)
    reports = []
    for f in files:
        rep = validate(f)
        reports.append(rep)
        if base:
            slug = os.path.relpath(f, base).replace(os.sep, "__")
        else:
            slug = os.path.basename(f)
        out_name = os.path.splitext(slug)[0] + ".qa.json"
        with open(os.path.join(args.out, out_name), "w") as fh:
            json.dump(rep, fh, indent=1)
        print(summary_line(rep))
    with open(os.path.join(args.out, "_summary.json"), "w") as fh:
        json.dump(reports, fh, indent=1)
    nfail = sum(1 for r in reports if not r["parses"])
    print(f"\n{len(reports)} file(s) validated, {nfail} parse failure(s). "
          f"Per-file JSON in {args.out}")
    return 1 if nfail else 0


if __name__ == "__main__":
    sys.exit(main())
