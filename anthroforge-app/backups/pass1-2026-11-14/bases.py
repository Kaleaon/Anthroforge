"""Base registry — the geometry packages characters are built on.

A base record (``library/bases/<id>.json``, format
``anthroforge.base``) names a package (``.npz`` beside it) holding the
base's vertex positions, triangle list, navel landmark and body-vertex
count, all in frame 1 (base.obj canonical — see
``scripts/build_base_packages.py`` for how the packages are built and
the frame discipline they follow).

Canonical slider records carry per-base instances keyed by base id
(``instances.makehuman_hm08`` …). Targets are per-base by nature: a
field authored on hm08 says nothing about another base until it is
re-derived there (the masculine package's belly instance is exactly
such a re-derivation). The registry therefore never guesses: a slider
with no instance on the character's base is reported, not applied.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np

from .errors import BaseRecordError

# Blueprint §3.1's default body id denotes the hm08 package (recorded
# as an alias in library/bases/makehuman_hm08.json).
BASE_ALIASES = {"af_body_neutral_v1": "makehuman_hm08"}


@dataclass
class BasePackage:
    """A loaded base geometry package."""

    id: str
    record: dict
    positions: np.ndarray      # (n_verts, 3) float64, metres, frame 1
    triangles: np.ndarray      # (n_tris, 3) int64
    navel: int
    body_end: int

    @property
    def n_verts(self) -> int:
        return len(self.positions)

    @property
    def body_face_mask(self) -> np.ndarray:
        """Faces whose three verts are all body verts (the fold gate's
        domain in the proof lineage: helpers/eyes/teeth excluded)."""
        return (self.triangles < self.body_end).all(axis=1)


class BaseRegistry:
    """All base records + packages loaded from one folder."""

    def __init__(self, folder: str | Path):
        self.folder = Path(folder)
        if not self.folder.is_dir():
            raise BaseRecordError(f"base folder not found: {self.folder}")
        self._records: dict[str, dict] = {}
        for path in sorted(self.folder.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise BaseRecordError(f"{path}: unreadable JSON ({exc})") from exc
            if data.get("format") != "anthroforge.base":
                raise BaseRecordError(
                    f"{path}: field 'format': expected 'anthroforge.base', "
                    f"got {data.get('format')!r}"
                )
            if data.get("id") != path.stem:
                raise BaseRecordError(
                    f"{path}: filename stem {path.stem!r} does not match "
                    f"record id {data.get('id')!r}"
                )
            self._records[data["id"]] = data
        self._packages: dict[str, BasePackage] = {}

    def ids(self) -> list[str]:
        return sorted(self._records)

    def __contains__(self, base_id: str) -> bool:
        return self.resolve(base_id) in self._records

    @staticmethod
    def resolve(base_id: str) -> str:
        return BASE_ALIASES.get(base_id, base_id)

    def record(self, base_id: str) -> dict:
        rid = self.resolve(base_id)
        rec = self._records.get(rid)
        if rec is None:
            raise BaseRecordError(
                f"unknown base id: {base_id!r} (registry holds {self.ids()})"
            )
        return rec

    def load(self, base_id: str) -> BasePackage:
        """Load (and cache) the geometry package for a base id."""
        rid = self.resolve(base_id)
        if rid in self._packages:
            return self._packages[rid]
        rec = self.record(base_id)
        pkg_path = self.folder / rec["package"]
        if not pkg_path.is_file():
            raise BaseRecordError(f"base {rid!r}: package not found: {pkg_path}")
        try:
            data = np.load(pkg_path)
            positions = data["positions"].astype(np.float64)
            triangles = data["triangles"].astype(np.int64)
            navel = int(data["navel"])
            body_end = int(data["body_end"])
        except (OSError, KeyError, ValueError) as exc:
            raise BaseRecordError(f"base {rid!r}: unreadable package {pkg_path} ({exc})") from exc
        topo = rec.get("topology", {})
        if "verts" in topo and len(positions) != topo["verts"]:
            raise BaseRecordError(
                f"base {rid!r}: package holds {len(positions)} verts, record "
                f"declares {topo['verts']} — package and record disagree"
            )
        pkg = BasePackage(id=rid, record=rec, positions=positions,
                          triangles=triangles, navel=navel, body_end=body_end)
        self._packages[rid] = pkg
        return pkg
