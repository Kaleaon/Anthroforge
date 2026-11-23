#!/usr/bin/env python3
"""
AnthroForge GLB QA harness v2 — EXTENDED checks (model-craft wave, agent B3).

Companion to ../qa-gauntlet/validate_glb.py (v1: parse / skin / contract /
morphs / scale / degenerate / NaN). v1 is untouched and still the export
gate; v2 adds the checks a modelling pro runs before calling an asset
"good", all parsed straight out of the GLB with stdlib + numpy:

  topology   non-manifold edges (face count > 2), boundary (open) edges,
             duplicate faces, unused vertices, T-junction proxy via
             split vertices (same position, distinct index)
  winding    directed-edge conflicts (two faces traversing a shared edge
             in the SAME direction = one of them is flipped), vertex-
             normal vs face-normal agreement, signed-volume sign on
             closed meshes (negative = inside-out)
  uv         textured primitive with no TEXCOORD_0, UV range (tiling),
             UV-overlap estimate (multi-sample rasterisation into a
             128x128 grid: fraction of covered cells claimed by >1 tri —
             catches gross self-overlap; UV mirroring also trips it, so
             it is reported as an estimate, severity warn-only),
             UV seam edges (position edge whose two faces disagree in
             UV space) and seam ratio
  texel      texel density per textured primitive (texels/metre, from
             image pixel dims x UV area / world area) and its
             coefficient of variation across a file's primitives —
             pros keep texel density CONSISTENT; CV is the smell
  materials  materials defined but never used by any primitive,
             primitives with no material in a file that defines some,
             duplicate material names
  weights    per-vertex influence counts, vertices with ZERO total
             weight on a skinned primitive, unnormalised weight sums
             (|sum-1| > 0.01), joint indices outside the skin's joint
             list, skin joints no vertex actually uses (orphan groups),
             WEIGHTS_1 without JOINTS_1
  animation  channel targets exist, sampler time keys monotonic,
             NaN/Inf in channel outputs, zero-duration clips,
             duplicate (node, path) channels

Usage:
  validate_glb2.py FILE.glb [--out DIR]
  validate_glb2.py DIR [--out DIR] [--max N]
  validate_glb2.py LIST.txt --list [--out DIR]   # one path per line

Per-file <name>.qa2.json + _summary2.json in --out. Exit 0 unless a file
fails to parse.
"""

import argparse
import json
import math
import os
import struct
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "qa-gauntlet"))
from validate_glb import parse_glb, read_accessor, world_matrices, GLBError

EPS_AREA = 1e-14


# ------------------------------------------------------------------ images
def image_dims(gltf, binbuf, img):
    """(w, h) from PNG/JPEG headers inside the embedded image, else None."""
    data = None
    if "bufferView" in img:
        bv = gltf["bufferViews"][img["bufferView"]]
        off = bv.get("byteOffset", 0)
        data = binbuf[off:off + bv["byteLength"]]
    if not data:
        return None
    if data[:8] == b"\x89PNG\r\n\x1a\n" and len(data) > 24:
        w, h = struct.unpack_from(">II", data, 16)
        return int(w), int(h)
    if data[:2] == b"\xff\xd8":  # JPEG: scan for SOF0/SOF2
        i = 2
        while i + 9 < len(data):
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            if marker in (0xC0, 0xC1, 0xC2):
                h, w = struct.unpack_from(">HH", data, i + 5)
                return int(w), int(h)
            if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
                i += 2
                continue
            seglen = struct.unpack_from(">H", data, i + 2)[0]
            i += 2 + seglen
    return None


# -------------------------------------------------------------- primitives
def prim_tris(gltf, binbuf, prim, pos_count):
    """Index array (n,3) for a primitive, or None if not triangle-based."""
    mode = prim.get("mode", 4)
    if mode != 4:
        return None
    if "indices" in prim:
        idx = read_accessor(gltf, binbuf, prim["indices"]).reshape(-1).astype(np.int64)
        n = len(idx) // 3
        return idx[:n * 3].reshape(-1, 3)
    n = pos_count // 3
    return np.arange(n * 3, dtype=np.int64).reshape(-1, 3)


def edge_stats(tris, nverts):
    """Undirected/directed edge census for one triangle soup."""
    a, b, c = tris[:, 0], tris[:, 1], tris[:, 2]
    directed = np.stack([np.concatenate([a, b, c]),
                         np.concatenate([b, c, a])], axis=1)
    und = np.sort(directed, axis=1)
    ukey = und[:, 0] * nverts + und[:, 1]
    dkey = directed[:, 0] * nverts + directed[:, 1]
    uq, ucounts = np.unique(ukey, return_counts=True)
    dq, dcounts = np.unique(dkey, return_counts=True)
    return {
        "edges_total": int(len(uq)),
        "boundary_edges": int((ucounts == 1).sum()),
        "nonmanifold_edges": int((ucounts > 2).sum()),
        "winding_conflicts": int((dcounts >= 2).sum()),
    }


def uv_overlap_estimate(uv, tris, grid=256):
    """Estimated overlapped fraction of a primitive's UV area.

    Area-conservation method: sum the triangles' UV areas, and compare
    with the actually-covered UV area (dense-sample occupancy on a
    512x512 grid). If triangles tile cleanly, covered ~= summed; every
    overlapped region is counted twice in the sum but once in coverage,
    so overlap ~= 1 - covered/summed. Deliberate UV mirroring (halves
    sharing an atlas) counts as overlap here BY DESIGN — the number says
    "this much UV area is double-claimed", the human decides whether
    that was intent. Only computed when UVs sit inside [0,1] (tiled
    textures defeat the area argument); returns None otherwise.
    """
    if len(tris) == 0:
        return None
    if ((uv < -1e-6) | (uv > 1 + 1e-6)).any():
        return None
    t = uv[tris]  # (n,3,2)
    ua, ub, uc = t[:, 0], t[:, 1], t[:, 2]
    areas = abs(0.5 * ((ub[:, 0] - ua[:, 0]) * (uc[:, 1] - ua[:, 1])
                       - (uc[:, 0] - ua[:, 0]) * (ub[:, 1] - ua[:, 1])))
    total = float(areas.sum())
    if total < 1e-9:
        return None
    # (caller unpacks estimate only; total kept for weighted aggregation
    # via the module-level stash below)
    # Occupancy by SUBDIVIDE-THEN-SAMPLE, fully vectorised. Two
    # earlier attempts failed calibration and are documented so nobody
    # re-tries them: (a) fixed samples-per-triangle under-fills big
    # triangles (Poisson 1-e^-lambda with lambda ~0.5 read 0.7 fake
    # "overlap" on clean atlases); (b) exact per-triangle cell-centre
    # rasterisation is correct but its Python loop over 30k triangles
    # with per-tri meshgrid allocation took >5 min on a 1.2M-vert
    # sculpt. Here: midpoint-subdivide (vectorised) until every
    # sub-triangle is <= ~4 grid cells, then ONE fixed 9-point
    # barycentric lattice over all sub-triangles at once gives
    # lambda >= ~6 samples/cell -> occupancy bias < 0.5%.
    thresh = 4.0 / float(grid * grid)
    sub = t
    sub_areas = areas.copy()
    for _ in range(10):
        big = sub_areas > thresh
        if not big.any():
            break
        keep = sub[~big]
        bt = sub[big]
        a, b, c = bt[:, 0], bt[:, 1], bt[:, 2]
        ab, bc, ca = (a + b) / 2, (b + c) / 2, (c + a) / 2
        kids = np.stack([
            np.stack([a, ab, ca], axis=1), np.stack([ab, b, bc], axis=1),
            np.stack([ca, bc, c], axis=1), np.stack([ab, bc, ca], axis=1),
        ], axis=1).reshape(-1, 3, 2)
        sub = np.concatenate([keep, kids], axis=0) if len(keep) else kids
        sub_areas = np.concatenate([
            sub_areas[~big], np.repeat(sub_areas[big] / 4.0, 4)])
    bary = np.array([[1 / 3, 1 / 3, 1 / 3],
                     [0.5, 0.25, 0.25], [0.25, 0.5, 0.25], [0.25, 0.25, 0.5],
                     [0.6, 0.2, 0.2], [0.2, 0.6, 0.2], [0.2, 0.2, 0.6],
                     [0.45, 0.45, 0.1], [0.1, 0.45, 0.45]])
    pts = np.einsum("sb,tbu->tsu", bary, sub).reshape(-1, 2)
    cell = (np.clip(pts, 0.0, 0.999999) * grid).astype(np.int64)
    ckey = cell[:, 0].astype(np.int64) * grid + cell[:, 1]
    covered = len(np.unique(ckey)) / float(grid * grid)
    # occupancy underestimates true covered area for thin triangles;
    # clamp into [0,1] and treat <3% as noise floor.
    est = 1.0 - covered / total
    return round(float(min(max(est, 0.0), 1.0)), 4), total


# ------------------------------------------------------------------- main
LITE = False  # set by --lite: skip the memory-hungry UV-overlap and
               # seam passes (mega-files on a loaded machine)


def validate2(path):
    rep = {"file": os.path.basename(path), "path": os.path.abspath(path),
           "parses": False, "error": None}
    try:
        gltf, binbuf = parse_glb(path)
    except Exception as e:
        rep["error"] = f"{type(e).__name__}: {e}"
        return rep
    rep["parses"] = True
    rep["lite"] = bool(LITE)

    nodes = gltf.get("nodes", [])
    meshes = gltf.get("meshes", [])
    skins = gltf.get("skins", [])
    materials = gltf.get("materials", [])
    textures = gltf.get("textures", [])
    images = gltf.get("images", [])
    world = world_matrices(gltf)
    node_mesh = {}
    for ni, n in enumerate(nodes):
        if "mesh" in n and n["mesh"] not in node_mesh:
            node_mesh[n["mesh"]] = world.get(ni, np.eye(4))

    # skin joint-count lookup for weight validation: node -> skin joints
    node_skin_joints = {}
    for ni, n in enumerate(nodes):
        if "skin" in n and n["skin"] < len(skins):
            node_skin_joints[ni] = len(skins[n["skin"]].get("joints", []))
    mesh_skin_joints = {}
    for ni, n in enumerate(nodes):
        if "mesh" in n and ni in node_skin_joints:
            mesh_skin_joints.setdefault(n["mesh"], node_skin_joints[ni])

    topo = {"boundary_edges": 0, "nonmanifold_edges": 0, "edges_total": 0,
            "duplicate_faces": 0, "unused_vertices": 0, "vertices_total": 0,
            "split_vertex_ratio": None}
    winding = {"conflicts": 0, "faces_checked": 0, "faces_inverted": 0,
               "closed_meshes": 0, "negative_volume_meshes": 0}
    uvrep = {"prims_textured_no_uv": 0, "prims_with_uv": 0,
             "uv_out_of_range_frac_max": 0.0, "overlap_estimate_max": None,
             "seam_edges": 0, "shared_edges": 0}
    texel = {"per_prim": []}
    weights = {"prims_checked": 0, "verts": 0, "zero_weight_verts": 0,
               "unnormalised_verts": 0, "max_influences": 0,
               "mean_influences": None, "joint_index_out_of_range": 0,
               "skins_joint_total": 0, "skins_joints_unused": 0,
               "weights1_without_joints1": 0}
    used_materials = set()
    prims_no_material = 0
    acc_errors = []
    _infl = []
    _used_joints = set()

    for mi, mesh in enumerate(meshes):
        mat4 = node_mesh.get(mi, np.eye(4))
        skin_jc = mesh_skin_joints.get(mi)
        for prim in mesh.get("primitives", []):
            attrs = prim.get("attributes", {})
            if "material" in prim:
                used_materials.add(prim["material"])
            elif materials:
                prims_no_material += 1
            if "POSITION" not in attrs:
                continue
            try:
                pos = read_accessor(gltf, binbuf, attrs["POSITION"]).astype(np.float64)
                tris = prim_tris(gltf, binbuf, prim, len(pos))
            except GLBError as e:
                acc_errors.append(str(e))
                continue
            if tris is None or len(tris) == 0:
                continue
            n = len(pos)
            topo["vertices_total"] += n
            wpos = pos @ mat4[:3, :3].T + mat4[:3, 3]

            # --- topology
            es = edge_stats(tris, n)
            for k in ("boundary_edges", "nonmanifold_edges", "edges_total"):
                topo[k] += es[k]
            winding["conflicts"] += es["winding_conflicts"]
            tf = np.sort(tris, axis=1)
            tkey = (tf[:, 0] * n + tf[:, 1]) * n + tf[:, 2]
            topo["duplicate_faces"] += int(len(tkey) - len(np.unique(tkey)))
            used_verts = np.zeros(n, dtype=bool)
            used_verts[np.unique(tris)] = True
            topo["unused_vertices"] += int((~used_verts).sum())
            # split vertices: distinct indices sharing a position.
            # Hash-quantised count (np.unique(axis=0) is O(n log n) with
            # a huge constant — it was the sweep's bottleneck at 1M+
            # verts; a 64-bit mix hash has the same answer up to
            # negligible collision probability).
            if n <= 2000000:
                q = np.round(pos * 1e5).astype(np.int64)
                h = (q[:, 0] * 1000003) ^ (q[:, 1] * 1000033) ^ (q[:, 2] * 1000037)
                nuniq = len(np.unique(h))
                topo.setdefault("split_extra", 0)
                topo["split_extra"] += int(n - nuniq)
            # closed mesh + signed volume (world space)
            if es["boundary_edges"] == 0 and es["nonmanifold_edges"] == 0:
                winding["closed_meshes"] += 1
                a, b, c = wpos[tris[:, 0]], wpos[tris[:, 1]], wpos[tris[:, 2]]
                vol = float(np.einsum("ij,ij->i", a, np.cross(b, c)).sum() / 6.0)
                if vol < 0:
                    winding["negative_volume_meshes"] += 1

            # --- winding vs vertex normals (sample big meshes)
            if "NORMAL" in attrs:
                try:
                    nrm = read_accessor(gltf, binbuf, attrs["NORMAL"]).astype(np.float64)
                    step = max(1, len(tris) // 20000)
                    t = tris[::step]
                    # LOCAL positions: vertex normals are local too; mixing
                    # world face normals with local vertex normals garbage-
                    # dots any rotated mesh.
                    fn = np.cross(pos[t[:, 1]] - pos[t[:, 0]],
                                  pos[t[:, 2]] - pos[t[:, 0]])
                    vn = nrm[t].mean(axis=1)
                    fl = np.linalg.norm(fn, axis=1) > 0
                    vl = np.linalg.norm(vn, axis=1) > 0
                    ok = fl & vl
                    if ok.any():
                        dots = np.einsum("ij,ij->i", fn[ok], vn[ok])
                        winding["faces_checked"] += int(ok.sum())
                        winding["faces_inverted"] += int((dots < 0).sum())
                except GLBError as e:
                    acc_errors.append(str(e))

            # --- UV checks + texel density
            mat_i = prim.get("material")
            mat = materials[mat_i] if (mat_i is not None and mat_i < len(materials)) else {}
            bct = (mat.get("pbrMetallicRoughness", {}) or {}).get("baseColorTexture")
            has_uv = "TEXCOORD_0" in attrs
            if bct is not None and not has_uv:
                uvrep["prims_textured_no_uv"] += 1
            if has_uv:
                try:
                    uv = read_accessor(gltf, binbuf, attrs["TEXCOORD_0"]).astype(np.float64)
                    uvrep["prims_with_uv"] += 1
                    oor = float(((uv < 0) | (uv > 1)).any(axis=1).mean())
                    uvrep["uv_out_of_range_frac_max"] = max(
                        uvrep["uv_out_of_range_frac_max"], oor)
                    ov = None if LITE else uv_overlap_estimate(uv, tris)
                    if ov is not None:
                        est, tarea = ov
                        uvrep.setdefault("_ovl", []).append((est, tarea))
                        cur = uvrep["overlap_estimate_max"]
                        uvrep["overlap_estimate_max"] = est if cur is None else max(cur, est)
                    # seam edges: position edges shared by 2 faces whose
                    # UV assignments disagree
                    if len(tris) <= 300000 and not LITE:
                        se, sh = uv_seam_edges(tris, uv, n)
                        uvrep["seam_edges"] += se
                        uvrep["shared_edges"] += sh
                    # texel density
                    if bct is not None:
                        tex_i = bct.get("index")
                        tex = textures[tex_i] if tex_i is not None and tex_i < len(textures) else {}
                        img_i = tex.get("source")
                        dims = None
                        if img_i is not None and img_i < len(images):
                            dims = image_dims(gltf, binbuf, images[img_i])
                        a3, b3, c3 = wpos[tris[:, 0]], wpos[tris[:, 1]], wpos[tris[:, 2]]
                        warea = 0.5 * np.linalg.norm(np.cross(b3 - a3, c3 - a3), axis=1).sum()
                        ua, ub, uc = uv[tris[:, 0]], uv[tris[:, 1]], uv[tris[:, 2]]
                        uarea = abs(0.5 * ((ub[:, 0] - ua[:, 0]) * (uc[:, 1] - ua[:, 1])
                                           - (uc[:, 0] - ua[:, 0]) * (ub[:, 1] - ua[:, 1]))).sum()
                        if warea > EPS_AREA and uarea > 1e-12:
                            if dims:
                                dens = math.sqrt(uarea * dims[0] * dims[1] / warea)
                                texel["per_prim"].append(round(float(dens), 1))
                            else:
                                texel.setdefault("per_prim_relative", []).append(
                                    round(float(math.sqrt(uarea / warea)), 4))
                except GLBError as e:
                    acc_errors.append(str(e))

            # --- skin weights
            if "JOINTS_0" in attrs and "WEIGHTS_0" in attrs:
                try:
                    j0 = read_accessor(gltf, binbuf, attrs["JOINTS_0"]).astype(np.int64)
                    w0 = read_accessor(gltf, binbuf, attrs["WEIGHTS_0"]).astype(np.float64)
                    weights["prims_checked"] += 1
                    weights["verts"] += len(w0)
                    sums = w0.sum(axis=1)
                    weights["zero_weight_verts"] += int((sums <= 0).sum())
                    nz = sums > 0
                    weights["unnormalised_verts"] += int(
                        (np.abs(sums[nz] - 1.0) > 0.01).sum())
                    infl = (w0 > 0).sum(axis=1)
                    _infl.append(infl)
                    if len(j0):
                        _used_joints |= set(np.unique(j0[w0 > 0]).tolist())
                    if skin_jc is not None and len(j0):
                        weights["joint_index_out_of_range"] += int(
                            (j0.max() >= skin_jc) if j0.size else 0)
                    if "WEIGHTS_1" in attrs and "JOINTS_1" not in attrs:
                        weights["weights1_without_joints1"] += 1
                except GLBError as e:
                    acc_errors.append(str(e))

    if _infl:
        all_infl = np.concatenate(_infl)
        weights["max_influences"] = int(all_infl.max())
        weights["mean_influences"] = round(float(all_infl.mean()), 2)
    if topo.get("split_extra") is not None and topo["vertices_total"]:
        topo["split_vertex_ratio"] = round(
            topo.get("split_extra", 0) / max(topo["vertices_total"], 1), 4)
    topo.pop("split_extra", None)

    # skin joints unused (orphan groups): joints no vertex weights onto
    # (accumulated during the main weight pass — no second read)
    if skins and weights["prims_checked"]:
        used_joints = _used_joints
        total_j = sum(len(s.get("joints", [])) for s in skins)
        weights["skins_joint_total"] = int(total_j)
        # joint indices are skin-local; unused counted per first skin only
        # when a single skin exists (the common case) — else report total.
        if len(skins) == 1:
            weights["skins_joints_unused"] = int(
                len(set(range(total_j)) - used_joints))
        else:
            weights["skins_joints_unused"] = None

    if uvrep.get("_ovl"):
        pairs = uvrep.pop("_ovl")
        tot = sum(a for _e, a in pairs)
        uvrep["overlap_estimate_area_weighted"] = round(
            sum(e * a for e, a in pairs) / tot, 4) if tot else None
    else:
        uvrep.pop("_ovl", None)
        uvrep["overlap_estimate_area_weighted"] = None

    # texel summary
    pp = texel["per_prim"]
    if len(pp) >= 2:
        arr = np.array(pp, dtype=np.float64)
        texel["mean_texel_per_m"] = round(float(arr.mean()), 1)
        texel["cv"] = round(float(arr.std() / arr.mean()), 3) if arr.mean() else None
    elif len(pp) == 1:
        texel["mean_texel_per_m"] = pp[0]
        texel["cv"] = 0.0
    else:
        texel["mean_texel_per_m"] = None
        texel["cv"] = None
    texel["prims_measured"] = len(pp)

    # --- materials summary
    mat_names = [m.get("name") for m in materials]
    rep["materials_check"] = {
        "defined": len(materials),
        "used": len(used_materials),
        "unused": int(len(materials) - len(used_materials)),
        "prims_without_material": int(prims_no_material),
        "duplicate_names": int(len(mat_names) - len(set(x for x in mat_names if x))),
    }

    # --- animation sanity
    anim = {"count": len(gltf.get("animations", [])), "channels": 0,
            "nonmonotonic_samplers": 0, "nan_outputs": 0,
            "zero_duration": 0, "bad_targets": 0, "duplicate_channels": 0,
            "max_duration_s": 0.0}
    for a in gltf.get("animations", []):
        seen = set()
        for ch in a.get("channels", []):
            anim["channels"] += 1
            tgt = ch.get("target", {})
            node_i = tgt.get("node")
            if node_i is None or node_i >= len(nodes):
                anim["bad_targets"] += 1
            key = (node_i, tgt.get("path"))
            if key in seen:
                anim["duplicate_channels"] += 1
            seen.add(key)
        for s in a.get("samplers", []):
            try:
                times = read_accessor(gltf, binbuf, s["input"]).reshape(-1).astype(np.float64)
                out = read_accessor(gltf, binbuf, s["output"]).astype(np.float64)
            except (GLBError, KeyError) as e:
                acc_errors.append(str(e))
                continue
            if len(times):
                if np.any(np.diff(times) < 0):
                    anim["nonmonotonic_samplers"] += 1
                dur = float(times.max() - times.min())
                anim["max_duration_s"] = max(anim["max_duration_s"], dur)
                if dur == 0:
                    anim["zero_duration"] += 1
            if not np.isfinite(out).all():
                anim["nan_outputs"] += 1
    anim["max_duration_s"] = round(anim["max_duration_s"], 3)
    rep["animation_check"] = anim

    rep["topology"] = topo
    rep["winding"] = winding
    rep["uv"] = uvrep
    rep["texel"] = texel
    rep["weights"] = weights
    if acc_errors:
        rep["accessor_errors"] = acc_errors[:5]

    # --- status
    st = {}
    st["topology"] = ("fail" if topo["nonmanifold_edges"] > 0 else
                      "warn" if (topo["boundary_edges"] > 0 or
                                 topo["duplicate_faces"] > 0) else "ok")
    inv_frac = (winding["faces_inverted"] / winding["faces_checked"]
                if winding["faces_checked"] else 0)
    winding["inverted_face_frac"] = round(float(inv_frac), 4)
    st["winding"] = ("fail" if inv_frac > 0.05 or winding["negative_volume_meshes"] > 0
                     else "warn" if (inv_frac > 0.005 or winding["conflicts"] > 0)
                     else "ok")
    st["uv"] = ("fail" if uvrep["prims_textured_no_uv"] > 0 else
                "warn" if (uvrep["overlap_estimate_area_weighted"] or 0) > 0.20
                else "ok")
    st["texel"] = ("warn" if (texel["cv"] is not None and texel["cv"] > 0.5)
                   else "ok" if texel["cv"] is not None else "n/a")
    st["materials"] = "warn" if rep["materials_check"]["unused"] > 0 else "ok"
    wv = weights["verts"]
    unnorm_frac = weights["unnormalised_verts"] / wv if wv else 0
    st["weights"] = ("fail" if weights["joint_index_out_of_range"] > 0 or
                     (wv and unnorm_frac > 0.02) else
                     "warn" if (weights["zero_weight_verts"] > 0 or
                                unnorm_frac > 0.001 or
                                (weights["skins_joints_unused"] or 0) > 0)
                     else "ok" if wv else "n/a")
    st["animation"] = ("fail" if (anim["nan_outputs"] > 0 or
                                  anim["nonmonotonic_samplers"] > 0 or
                                  anim["bad_targets"] > 0) else
                       "warn" if (anim["zero_duration"] > 0 or
                                  anim["duplicate_channels"] > 0) else
                       "ok" if anim["count"] else "n/a")
    rep["status2"] = st
    return rep


def uv_seam_edges(tris, uv, nverts):
    """Position edges shared by exactly 2 faces whose UVs disagree.

    Fully vectorised: sort directed corner edges by undirected key,
    take the adjacent pairs of the exactly-2 groups, orient each
    pair's UVs by position order, compare.
    """
    a, b, c = tris[:, 0], tris[:, 1], tris[:, 2]
    src = np.concatenate([a, b, c])
    dst = np.concatenate([b, c, a])
    key = np.minimum(src, dst) * nverts + np.maximum(src, dst)
    order = np.argsort(key, kind="stable")
    key_s = key[order]
    src_s, dst_s = src[order], dst[order]
    starts = np.where(np.concatenate([[True], key_s[1:] != key_s[:-1]]))[0]
    ends = np.concatenate([starts[1:], [len(key_s)]])
    counts = ends - starts
    two = np.where(counts == 2)[0]
    if len(two) == 0:
        return 0, 0
    rows = starts[two]  # first row of each 2-group; partner is rows+1
    i0, i1 = rows, rows + 1
    uvq = np.round(uv, 5)

    def oriented(idx):
        s, d = src_s[idx], dst_s[idx]
        us, ud = uvq[s], uvq[d]
        flip = (s > d)[:, None]
        return np.where(flip, ud, us), np.where(flip, us, ud)

    a0, b0 = oriented(i0)
    a1, b1 = oriented(i1)
    seam = int(((a0 != a1) | (b0 != b1)).any(axis=1).sum())
    return seam, int(len(two))


def summary_line(rep):
    if not rep["parses"]:
        return f"FAIL-PARSE  {rep['file']}: {rep['error']}"
    t, w, u, x, wt, an = (rep["topology"], rep["winding"], rep["uv"],
                          rep["texel"], rep["weights"], rep["animation_check"])
    return (f"{rep['file']}: nm {t['nonmanifold_edges']} bnd {t['boundary_edges']} "
            f"dup {t['duplicate_faces']} | wind-conf {w['conflicts']} "
            f"inv {w['inverted_face_frac']:.3f} | uv-ovl "
            f"{(u['overlap_estimate_max'] if u['overlap_estimate_max'] is not None else -1):.2f} "
            f"| texelCV {x['cv']} | wt zero {wt['zero_weight_verts']} "
            f"unnorm {wt['unnormalised_verts']} orphanJ {wt['skins_joints_unused']} "
            f"| anim {an['count']} bad {an['bad_targets']+an['nan_outputs']} "
            f"| {rep['status2']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target")
    ap.add_argument("--list", action="store_true",
                    help="target is a text file with one GLB path per line")
    ap.add_argument("--out", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "results"))
    ap.add_argument("--max", type=int, default=0)
    ap.add_argument("--lite", action="store_true",
                    help="skip UV-overlap + seam passes (mega-files)")
    args = ap.parse_args()
    if args.lite:
        global LITE
        LITE = True

    base = None
    if args.list:
        files = [l.strip() for l in open(args.target) if l.strip()]
    elif os.path.isdir(args.target):
        base = os.path.abspath(args.target)
        files = []
        for root, _d, names in os.walk(args.target):
            for nm in sorted(names):
                if nm.lower().endswith(".glb"):
                    files.append(os.path.join(root, nm))
        files.sort()
    else:
        files = [args.target]
    if args.max:
        files = files[:args.max]

    os.makedirs(args.out, exist_ok=True)
    reports = []
    for f in files:
        if base:
            slug = os.path.relpath(f, base).replace(os.sep, "__")
        elif args.list:
            slug = os.path.basename(os.path.dirname(f)) + "__" + os.path.basename(f)
        else:
            slug = os.path.basename(f)
        out_name = os.path.splitext(slug)[0] + ".qa2.json"
        out_path = os.path.join(args.out, out_name)
        if args.list and os.path.exists(out_path):
            with open(out_path) as fh:
                reports.append(json.load(fh))
            print(f"skip (done) {os.path.basename(f)}", flush=True)
            continue
        rep = validate2(f)
        reports.append(rep)
        with open(os.path.join(args.out, out_name), "w") as fh:
            json.dump(rep, fh, indent=1)
        print(summary_line(rep), flush=True)
    with open(os.path.join(args.out, "_summary2.json"), "w") as fh:
        json.dump(reports, fh, indent=1)
    nfail = sum(1 for r in reports if not r["parses"])
    print(f"\n{len(reports)} file(s) validated (v2), {nfail} parse failure(s).")
    return 1 if nfail else 0


if __name__ == "__main__":
    sys.exit(main())
