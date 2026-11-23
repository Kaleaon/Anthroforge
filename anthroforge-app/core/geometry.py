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
    if not isinstance(n_verts, int) or isinstance(n_verts, bool) or n_verts <= 0:
        raise GeometryError(f"target instance {path}: n_verts must be a positive integer")
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
        if not np.isfinite((dx, dy, dz)).all():
            raise GeometryError(
                f"target instance {path}:{lineno}: vertex deltas must be finite numbers"
            )
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


def fmt(v: float) -> str:
    """Format one MakeHuman ``.target`` coordinate in decimetres (3-decimal
    precision with trailing zeros stripped, preserving ``.0`` on whole
    floats and zeros)."""
    s = f"{abs(v):.3f}".rstrip("0")
    if s.endswith("."):
        s += "0"
    if s in ("", "0."):
        s = "0"
    return ("-" + s) if v < 0 else s


def write_target(path: str | Path, delta: np.ndarray, note: str) -> int:
    """Write a canonical-frame ``(N, 3)`` vertex delta (metres, ``(x, y, z)``)
    as a sparse MakeHuman ``.target`` file (decimetres, ``(x, z, y)``),
    emitting vertices with ``max(|d_obj|) > 0.001`` dm. Returns the count of
    moved vertices written."""
    path = Path(path)
    arr = np.asarray(delta, dtype=np.float64)
    if arr.ndim != 2 or arr.shape[1:] != (3,) or arr.shape[0] == 0:
        raise GeometryError(
            f"target output {path}: delta must have shape (N, 3) with N > 0, got {arr.shape}"
        )
    if not np.isfinite(arr).all():
        raise GeometryError(f"target output {path}: delta contains non-finite values")
    d_obj = np.stack([arr[:, 0], arr[:, 2], arr[:, 1]], axis=1) / DM_M
    moved = np.where(np.abs(d_obj).max(axis=1) > 0.001)[0]
    raw_lines = str(note).splitlines() or [""]
    note_block = "\n".join(
        line if line.startswith("#") else f"# {line}" for line in raw_lines
    )
    header = (
        "# This is a target file for MakeHuman\n#\n"
        "# It was written by the MakeTarget submodule of MPFB\n#\n"
        "# For more information, see MakeHuman's home page at "
        "http://www.makehumancommunity.org\n#\n# basemesh hm08\n"
        f"{note_block}\n"
    )
    try:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(header)
            for i in moved:
                fh.write(
                    f"{i} {fmt(d_obj[i, 0])} {fmt(d_obj[i, 1])} {fmt(d_obj[i, 2])}\n"
                )
    except OSError as exc:
        raise GeometryError(f"target output {path}: cannot write ({exc})") from exc
    return int(len(moved))


@dataclass
class InstanceField:
    """A slider's field on one base, ready to evaluate at any value."""

    slider_id: str
    base_id: str
    linear: np.ndarray                       # (n_verts, 3) metres
    sag: Optional[np.ndarray] = None         # gravity component, if coupled
    gamma: float = 2.0

    def __post_init__(self) -> None:
        self.linear = np.asarray(self.linear, dtype=np.float64)
        if self.linear.ndim != 2 or self.linear.shape[1:] != (3,):
            raise GeometryError(
                f"slider {self.slider_id!r}: linear field must have shape (N, 3), "
                f"got {self.linear.shape}"
            )
        if not np.isfinite(self.linear).all():
            raise GeometryError(f"slider {self.slider_id!r}: linear field contains non-finite values")
        if self.sag is not None:
            self.sag = np.asarray(self.sag, dtype=np.float64)
            if self.sag.shape != self.linear.shape:
                raise GeometryError(
                    f"slider {self.slider_id!r}: sag field shape {self.sag.shape} "
                    f"does not match linear field {self.linear.shape}"
                )
            if not np.isfinite(self.sag).all():
                raise GeometryError(f"slider {self.slider_id!r}: sag field contains non-finite values")
        try:
            self.gamma = float(self.gamma)
        except (TypeError, ValueError) as exc:
            raise GeometryError(f"slider {self.slider_id!r}: gamma must be a finite positive number") from exc
        if not np.isfinite(self.gamma) or self.gamma <= 0:
            raise GeometryError(f"slider {self.slider_id!r}: gamma must be a finite positive number")

    def at(self, value: float) -> np.ndarray:
        """The displacement field at slider value ``value``."""
        try:
            w = float(value)
        except (TypeError, ValueError) as exc:
            raise GeometryError(f"slider {self.slider_id!r}: slider value must be finite") from exc
        if not np.isfinite(w):
            raise GeometryError(f"slider {self.slider_id!r}: slider value must be finite")
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


def degenerate_face_mask(positions: np.ndarray, triangles: np.ndarray, *, area_epsilon: float = 1e-12) -> np.ndarray:
    """Return a per-face mask for collapsed or non-finite triangles."""
    if positions.ndim != 2 or positions.shape[1] != 3:
        raise GeometryError(f"positions must have shape (N, 3), got {positions.shape}")
    if triangles.ndim != 2 or triangles.shape[1] != 3:
        raise GeometryError(f"triangles must have shape (M, 3), got {triangles.shape}")
    if triangles.size and (triangles.min() < 0 or triangles.max() >= len(positions)):
        raise GeometryError("triangle index is outside the vertex array")
    tri = positions[triangles]
    cross = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    magnitude = np.linalg.norm(cross, axis=1)
    return ~np.isfinite(magnitude) | (magnitude <= area_epsilon)


def count_degenerate_faces(positions: np.ndarray, triangles: np.ndarray, *, area_epsilon: float = 1e-12) -> int:
    """Count faces with cross-product magnitude at or below epsilon (m^2)."""
    return int(degenerate_face_mask(positions, triangles, area_epsilon=area_epsilon).sum())

def write_glb(path: str | Path, positions: np.ndarray, triangles: np.ndarray) -> Path:
    """Write a minimal, valid GLB (one mesh, positions + computed
    normals + uint32 indices, no skin/materials — a geometry-proof
    export). The QA gauntlet parses GLB directly, so this file is the
    artefact the gate runs on."""
    import json as _json
    import struct

    source_positions = np.asarray(positions)
    source_triangles = np.asarray(triangles)
    if source_positions.ndim != 2 or source_positions.shape[1:] != (3,) or not len(source_positions):
        raise GeometryError(
            f"write_glb: positions must have non-empty shape (N, 3), got {source_positions.shape}"
        )
    if source_triangles.ndim != 2 or source_triangles.shape[1:] != (3,) or not len(source_triangles):
        raise GeometryError(
            f"write_glb: triangles must have non-empty shape (M, 3), got {source_triangles.shape}"
        )
    if not np.issubdtype(source_triangles.dtype, np.integer):
        raise GeometryError("write_glb: triangle indices must be integers")
    if source_triangles.min() < 0 or source_triangles.max() >= len(source_positions):
        raise GeometryError("write_glb: triangle index is outside the vertex array")
    pos = np.ascontiguousarray(source_positions, dtype=np.float32)
    triangles = np.ascontiguousarray(source_triangles, dtype=np.uint32)
    # A non-finite vertex would serialise as an invalid NaN/Infinity
    # token in the glTF JSON chunk (accessor min/max) — refuse the
    # export instead of writing a file no strict parser accepts.
    if not np.isfinite(pos).all():
        raise GeometryError(
            "write_glb: vertex positions contain non-finite values (NaN or infinity) — "
            "refusing to write an invalid GLB"
        )
    nrm = np.ascontiguousarray(face_normals(pos, triangles), dtype=np.float32)
    if not np.isfinite(nrm).all():
        raise GeometryError("write_glb: computed normals contain non-finite values")
    # per-vertex normals: average of adjacent face normals
    vn = np.zeros_like(pos)
    flat = triangles.ravel()
    np.add.at(vn, flat, np.repeat(nrm, 3, axis=0))
    ln = np.linalg.norm(vn, axis=1, keepdims=True)
    vn = np.divide(vn, ln, out=np.zeros_like(vn), where=ln > 0).astype(np.float32)
    idx = triangles

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
