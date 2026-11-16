"""Geometry layer — .target instances applied to a base mesh.

The canonical slider record (core/sliders.py) is base-independent
semantics; the *instance* is the per-base vertex field. Instances on
disk are MakeHuman/MPFB ``.target`` files: sparse lines
``<vertex_index> <dx> <dy> <dz>`` under a ``# basemesh hm08`` header.

Units/axes (verified against the proof lineage's own QA numbers —
first-proof GRAVITY_V5.md v5.1 addendum: navel displacement at +1 is
forward 11.14 cm / down 6.99 cm, which only this mapping reproduces):

- .target deltas are in **decimetres**, in base.obj axis order.
- Base packages store positions as ``[obj.x, obj.z, obj.y] * 0.1 m``
  (frame 1, see core/bases.py), so a file delta ``(dx, dy, dz)`` maps
  to stored ``(dx, dz, dy) * 0.1`` metres.

Two instance shapes are supported, declared in the record's
``instances[<base_id>]`` entry:

- ``{"file": ...}`` — one linear field: ``pos = base + w * field``.
- ``{"components": {"combined": ..., "sag": ..., "gamma": g}}`` — a
  gravity-coupled field (the belly lineage): the combined file is
  ``LIN + SAG`` at +1, so ``LIN = combined - sag`` and
  ``pos = base + w * LIN + sign(w) * |w|**gamma * SAG``.
  This reproduces the authored shape function exactly, instead of
  linearly scaling a baked combined field.

A components entry may also carry ``"variants": {"contact": file}``:
an alternate combined field (the belly v5.2 thigh-contact build)
selectable per build; the sag decomposition is retained against the
variant, as the v5.2 record documents it.

An instance may instead (or additionally) declare ``"arrays"``: a
canonical-precision .npz pack under ``library/instances/`` with named
float64 fields (``linear``, optional ``sag``/``gamma``, optional
per-variant ``linear`` keys). When present, the arrays form wins —
the .target files remain the MPFB interchange form, but their 0.1 mm
rounding is coarser than the fold gate's thinnest margin in the
lineage (belly at +1: canonical min normal dot +0.0018).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np

from .errors import GeometryError

DM_M = 0.1  # .target deltas are decimetres


def parse_target(path: str | Path, n_verts: int) -> np.ndarray:
    """Parse a MakeHuman .target file into a dense (n_verts, 3) field
    in stored base axes, metres. Raises GeometryError naming the file
    on any malformed line or out-of-range vertex index."""
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise GeometryError(f"target instance {path}: cannot read ({exc})") from exc
    field = np.zeros((n_verts, 3), dtype=np.float64)
    seen: set[int] = set()
    for lineno, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) != 4:
            raise GeometryError(
                f"target instance {path}:{lineno}: expected '<index> <dx> <dy> <dz>', "
                f"got {line!r}"
            )
        try:
            idx = int(parts[0])
            dx, dy, dz = (float(parts[1]), float(parts[2]), float(parts[3]))
        except ValueError as exc:
            raise GeometryError(
                f"target instance {path}:{lineno}: non-numeric entry {line!r}"
            ) from exc
        if not (0 <= idx < n_verts):
            raise GeometryError(
                f"target instance {path}:{lineno}: vertex index {idx} outside "
                f"[0, {n_verts}) — instance does not belong to this base"
            )
        if idx in seen:
            raise GeometryError(
                f"target instance {path}:{lineno}: duplicate vertex index {idx}"
            )
        seen.add(idx)
        # file (dx, dy, dz) dm -> stored (dx, dz, dy) metres
        field[idx] = (dx * DM_M, dz * DM_M, dy * DM_M)
    if not seen:
        raise GeometryError(f"target instance {path}: no vertex deltas found")
    return field


@dataclass
class InstanceField:
    """A slider's field on one base, ready to evaluate at any value."""

    slider_id: str
    base_id: str
    linear: np.ndarray                       # (n_verts, 3) metres
    sag: Optional[np.ndarray] = None         # gravity component, if coupled
    gamma: float = 2.0

    def at(self, value: float) -> np.ndarray:
        """The displacement field at slider value ``value``."""
        w = float(value)
        disp = w * self.linear
        if self.sag is not None and w != 0.0:
            disp = disp + np.sign(w) * (abs(w) ** self.gamma) * self.sag
        return disp


def _resolve(workspace_root: Path, rel: str, slider_id: str) -> Path:
    # Confine the resolved path to the workspace: instance records
    # are library data, and a crafted "file"/"pack" entry must not be
    # able to walk out of the library (e.g. "../../etc/passwd").
    root = Path(workspace_root).resolve()
    p = (root / rel).resolve()
    if not p.is_relative_to(root):
        raise GeometryError(
            f"slider {slider_id!r}: instance path escapes the workspace: {rel} "
            f"(resolved to {p})"
        )
    if not p.is_file():
        raise GeometryError(
            f"slider {slider_id!r}: instance file not found: {rel} "
            f"(resolved to {p})"
        )
    return p


def load_instance(
    slider_id: str,
    instance: dict,
    base_id: str,
    n_verts: int,
    workspace_root: str | Path,
    *,
    variant: Optional[str] = None,
) -> InstanceField:
    """Load one record instance entry as an :class:`InstanceField`.

    ``instance`` is the record's ``instances[base_id]`` dict. File
    paths inside it are workspace-relative (the library convention:
    instances live with their proof, e.g.
    ``anthroforge-v2/bara-proof/body.muscle.target``)."""
    root = Path(workspace_root)
    if not isinstance(instance, dict):
        raise GeometryError(f"slider {slider_id!r}: instance for base {base_id!r} "
                            "must be an object with 'file' or 'components'")
    arrays = instance.get("arrays")
    if arrays is not None:
        # Canonical-precision form (library/instances/*.npz): the
        # .target interchange files round deltas to 0.1 mm, which moves
        # the belly lineage's thinnest fold-gate face across zero — the
        # app builds from the proofs' full-precision fields instead.
        pack_path = _resolve(root, arrays["pack"], slider_id)
        try:
            # Read inside the context manager: the extracted arrays
            # are .astype(np.float64) copies, so they outlive the file.
            # (np.load without `with` leaked the NpzFile handle.)
            with np.load(pack_path) as data:
                linear_key = arrays["linear"]
                if variant is not None:
                    variants = arrays.get("variants", {})
                    if variant not in variants:
                        raise GeometryError(
                            f"slider {slider_id!r}: unknown instance variant "
                            f"{variant!r} (declared: {sorted(variants) or 'none'})"
                        )
                    linear_key = variants[variant]["linear"]
                linear = data[linear_key].astype(np.float64)
                sag = (data[arrays["sag"]].astype(np.float64)
                       if arrays.get("sag") else None)
        except GeometryError:
            raise
        except (OSError, KeyError, ValueError) as exc:
            raise GeometryError(
                f"slider {slider_id!r}: unreadable instance pack {pack_path} ({exc})"
            ) from exc
        if linear.shape != (n_verts, 3):
            raise GeometryError(
                f"slider {slider_id!r}: instance pack field shape {linear.shape} "
                f"does not match base vertex count {n_verts}"
            )
        return InstanceField(
            slider_id=slider_id, base_id=base_id, linear=linear, sag=sag,
            gamma=float(arrays.get("gamma", 2.0)),
        )
    comps = instance.get("components")
    if comps is not None:
        combined_rel = comps.get("combined")
        if variant is not None:
            variants = comps.get("variants", {})
            if variant not in variants:
                raise GeometryError(
                    f"slider {slider_id!r}: unknown instance variant {variant!r} "
                    f"(declared: {sorted(variants) or 'none'})"
                )
            combined_rel = variants[variant]
        if not combined_rel or "sag" not in comps:
            raise GeometryError(
                f"slider {slider_id!r}: components instance needs 'combined' and 'sag'"
            )
        combined = parse_target(_resolve(root, combined_rel, slider_id), n_verts)
        sag = parse_target(_resolve(root, comps["sag"], slider_id), n_verts)
        return InstanceField(
            slider_id=slider_id, base_id=base_id,
            linear=combined - sag, sag=sag,
            gamma=float(comps.get("gamma", 2.0)),
        )
    rel = instance.get("file")
    if not rel:
        raise GeometryError(
            f"slider {slider_id!r}: instance for base {base_id!r} declares "
            "neither 'file' nor 'components'"
        )
    return InstanceField(
        slider_id=slider_id, base_id=base_id,
        linear=parse_target(_resolve(root, rel, slider_id), n_verts),
    )


def face_normals(positions: np.ndarray, triangles: np.ndarray) -> np.ndarray:
    """Unit face normals; degenerate faces get a zero normal."""
    tris = positions[triangles]
    n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    ln = np.linalg.norm(n, axis=1, keepdims=True)
    return np.divide(n, ln, out=np.zeros_like(n), where=ln > 0)


def count_flips(
    base_positions: np.ndarray,
    positions: np.ndarray,
    triangles: np.ndarray,
    face_mask: Optional[np.ndarray] = None,
) -> int:
    """Fold gate: faces whose normal flipped vs the base pose — the
    hard QA gate every proof in the lineage ships against (0 flips at
    +1). ``face_mask`` restricts the count (e.g. body faces only)."""
    nb = face_normals(base_positions, triangles)
    nn = face_normals(positions, triangles)
    dots = np.einsum("ij,ij->i", nb, nn)
    if face_mask is not None:
        dots = dots[face_mask]
    return int((dots < 0).sum())


def write_glb(path: str | Path, positions: np.ndarray, triangles: np.ndarray) -> Path:
    """Write a minimal, valid GLB (one mesh, positions + computed
    normals + uint32 indices, no skin/materials — a geometry-proof
    export). The QA gauntlet parses GLB directly, so this file is the
    artefact the gate runs on."""
    import json as _json
    import struct

    pos = np.ascontiguousarray(positions, dtype=np.float32)
    # A non-finite vertex would serialise as an invalid NaN/Infinity
    # token in the glTF JSON chunk (accessor min/max) — refuse the
    # export instead of writing a file no strict parser accepts.
    if not np.isfinite(pos).all():
        raise GeometryError(
            "write_glb: vertex positions contain NaN or infinite values — "
            "refusing to write an invalid GLB"
        )
    nrm = np.ascontiguousarray(face_normals(positions, triangles), dtype=np.float32)
    # per-vertex normals: average of adjacent face normals
    vn = np.zeros_like(pos)
    flat = triangles.ravel()
    np.add.at(vn, flat, np.repeat(nrm, 3, axis=0))
    ln = np.linalg.norm(vn, axis=1, keepdims=True)
    vn = np.divide(vn, ln, out=np.zeros_like(vn), where=ln > 0).astype(np.float32)
    idx = np.ascontiguousarray(triangles, dtype=np.uint32)

    def pad4(b: bytes) -> bytes:
        return b + b"\x00" * (-len(b) % 4)

    bin_parts: list[bytes] = []
    views: list[dict] = []
    offset = 0
    for arr, target in ((pos, 34962), (vn, 34962), (idx, 34963)):
        raw = pad4(arr.tobytes())
        views.append({
            "buffer": 0, "byteOffset": offset, "byteLength": len(arr.tobytes()),
            "target": target,
        })
        bin_parts.append(raw)
        offset += len(raw)
    bin_blob = b"".join(bin_parts)
    gltf = {
        "asset": {"version": "2.0", "generator": "AnthroForge core.geometry"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0, "name": "body"}],
        "meshes": [{
            "name": "body",
            "primitives": [{
                "attributes": {"POSITION": 0, "NORMAL": 1},
                "indices": 2, "mode": 4,
            }],
        }],
        "buffers": [{"byteLength": len(bin_blob)}],
        "bufferViews": views,
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": len(pos),
             "type": "VEC3", "min": pos.min(axis=0).tolist(),
             "max": pos.max(axis=0).tolist()},
            {"bufferView": 1, "componentType": 5126, "count": len(vn), "type": "VEC3"},
            {"bufferView": 2, "componentType": 5125, "count": idx.size,
             "type": "SCALAR"},
        ],
    }
    # glTF: the JSON chunk is padded with spaces (0x20), the BIN chunk
    # with zeros — strict parsers reject NUL-padded JSON.
    raw_json = _json.dumps(gltf, separators=(",", ":")).encode("utf-8")
    json_blob = raw_json + b" " * (-len(raw_json) % 4)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as fh:
        fh.write(struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(json_blob) + 8 + len(bin_blob)))
        fh.write(struct.pack("<I4s", len(json_blob), b"JSON"))
        fh.write(json_blob)
        fh.write(struct.pack("<I4s", len(bin_blob), b"BIN\x00"))
        fh.write(bin_blob)
    return path
