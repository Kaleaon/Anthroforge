"""The build service — a character, evaluated end to end.

Pipeline (the composition doctrine, MUSCLE_TISSUE_MODEL.md):

    character record
      -> validate against the slider registry (unknown ids are errors)
      -> couplings: raw vector -> effective vector + derived quantities
      -> geometry: every effective slider with an instance on the
         character's base contributes its field at its effective value
         (sliders without an instance are reported, never faked)
      -> fold gate over body faces (0 flips is the lineage's hard gate;
         flips are reported, and ``strict`` turns them into an error)
      -> GLB export (core.geometry.write_glb)
      -> QA gauntlet (anthroforge-v2/qa-gauntlet/validate_glb.py) when
         available: parse / NaN / degenerate / scale verdicts ride back
         on the report.

This module is the Core Service the MCP tools wrap (APP_BLUEPRINT §4:
the MCP server contains no implementation; it calls this).
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np

from .bases import BaseRegistry
from .character import Character
from .errors import GeometryError
from .geometry import count_degenerate_faces, count_flips, degenerate_face_mask, load_instance, write_glb
from .sliders import CouplingRegistry, SliderRegistry

APP_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = APP_ROOT.parent
DEFAULT_LIBRARY = APP_ROOT / "library"
QA_GAUNTLET = WORKSPACE_ROOT / "anthroforge-v2" / "qa-gauntlet" / "validate_glb.py"


@dataclass
class Library:
    """The three registries a build needs, loaded from one library."""

    sliders: SliderRegistry
    couplings: CouplingRegistry
    bases: BaseRegistry

    @classmethod
    def load(cls, library: str | Path = DEFAULT_LIBRARY) -> "Library":
        library = Path(library)
        return cls(
            sliders=SliderRegistry.from_folder(library / "sliders"),
            couplings=CouplingRegistry.from_folder(library / "couplings"),
            bases=BaseRegistry(library / "bases"),
        )


@dataclass
class BuildReport:
    """Everything a build established, in one inspectable object."""

    character_id: str
    base_id: str
    effective_sliders: dict[str, float]
    derived: dict[str, float] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    applied: list[str] = field(default_factory=list)       # slider ids with geometry
    unapplied: list[str] = field(default_factory=list)     # effective, no instance on base
    flips_body: Optional[int] = None
    flips_all: Optional[int] = None
    min_body_dot: Optional[float] = None   # thinnest body fold-gate margin
    min_all_dot: Optional[float] = None    # thinnest full-mesh fold-gate margin
    base_degenerate_faces: Optional[int] = None
    degenerate_faces: Optional[int] = None
    new_degenerate_faces: Optional[int] = None
    nonfinite_vertices: int = 0
    glb_path: Optional[str] = None
    qa: Optional[dict] = None                              # qa-gauntlet verdicts

    @property
    def ok(self) -> bool:
        return (
            self.flips_body in (0, None)
            and self.flips_all in (0, None)
            and self.new_degenerate_faces in (0, None)
            and self.nonfinite_vertices == 0
            and not (self.qa and self.qa.get("blocked"))
        )


def evaluate_character(character: Character, library: Library):
    """Vector half of the pipeline: validate + couple. Returns
    (ValidationReport, EffectiveVector)."""
    report = character.validate(library.sliders)
    effective = character.effective_sliders(library.sliders, library.couplings)
    return report, effective


def run_qa_gauntlet(glb_path: str | Path) -> Optional[dict]:
    """Run the QA gauntlet on one GLB and return its verdict summary,
    or None when the gauntlet is not available on this machine."""
    if not QA_GAUNTLET.is_file():
        return None
    import tempfile

    glb_path = Path(glb_path)
    with tempfile.TemporaryDirectory() as td:
        out_dir = Path(td) / "results"
        proc = subprocess.run(
            [sys.executable, str(QA_GAUNTLET), str(glb_path), "--out", str(out_dir)],
            capture_output=True, text=True, timeout=300,
        )
        results = sorted(out_dir.glob("*.qa.json")) if out_dir.is_dir() else []
        if not results:
            # QA never ran, so nothing about this GLB was verified:
            # the report must block, not silently pass (BuildReport.ok
            # keys off qa["blocked"]).
            return {"error": (proc.stderr or proc.stdout or "gauntlet produced no result")[-500:],
                    "blocked": True}
        data = json.loads(results[0].read_text(encoding="utf-8"))
    # Gauntlet report shape: flat fields + a `status` dict whose values
    # are ok / warn / fail per gate (parse, skin, contract, morphs,
    # textures, geometry, scale). The block list (qa-gauntlet REPORT.md):
    # parse failure, NaN/Inf verts, external texture URIs, degenerate
    # tris > 0.1% — a `fail` status or any of those raw signals blocks.
    status = data.get("status", {}) if isinstance(data, dict) else {}
    textures = data.get("textures", {}) if isinstance(data, dict) else {}
    blocked = (
        any(v == "fail" for v in status.values())
        or data.get("parses") is False
        or (data.get("nan_vertices") or 0) > 0
        or (textures.get("external") or 0) > 0
    )
    return {
        "file": glb_path.name,
        "status": status,
        "parses": data.get("parses"),
        "nan_vertices": data.get("nan_vertices"),
        "degenerate_triangles": data.get("degenerate_triangles"),
        "max_extent_m": data.get("max_extent_m"),
        "scale_flag": data.get("scale_flag"),
        "blocked": blocked,
    }


def build_character(
    character: Character,
    library: Library,
    *,
    out_path: str | Path,
    belly_variant: Optional[str] = None,
    strict: bool = False,
    run_qa: bool = True,
) -> BuildReport:
    """Evaluate a character onto its base and export a GLB.

    Raises ValidationError (via the report) when the character names
    sliders the registry does not hold; GeometryError when an instance
    is malformed or (with ``strict``) when the fold gate fails.
    """
    report, effective = evaluate_character(character, library)
    report.raise_if_errors()

    base_id = BaseRegistry.resolve(character.base.get("body", ""))
    base = library.bases.load(base_id)
    positions = base.positions.copy()
    applied: list[str] = []
    unapplied: list[str] = []
    for sid in sorted(effective.sliders):
        value = effective.sliders[sid]
        if abs(value) < 1e-12:
            continue
        rec = library.sliders.find(sid)
        instance = (rec.instances or {}).get(base.id) if rec else None
        if instance is None:
            unapplied.append(sid)
            continue
        variant = belly_variant if sid == "body.belly.protrusion" else None
        fld = load_instance(sid, instance, base.id, base.n_verts,
                            WORKSPACE_ROOT, variant=variant)
        positions = positions + fld.at(value)
        applied.append(sid)

    nonfinite_vertices = int((~np.isfinite(positions).all(axis=1)).sum())
    if nonfinite_vertices:
        raise GeometryError(
            f"build of character {character.id!r} on base {base.id!r}: "
            f"{nonfinite_vertices} vertices contain NaN or infinity"
        )
    flips_body = count_flips(base.positions, positions, base.triangles,
                             base.body_face_mask)
    flips_all = count_flips(base.positions, positions, base.triangles)
    base_degenerate_faces = count_degenerate_faces(base.positions, base.triangles)
    degenerate_faces = count_degenerate_faces(positions, base.triangles)
    from .geometry import face_normals

    dots = np.einsum(
        "ij,ij->i",
        face_normals(base.positions, base.triangles),
        face_normals(positions, base.triangles),
    )
    min_body_dot = (float(dots[base.body_face_mask].min())
                    if np.any(base.body_face_mask) else None)
    min_all_dot = float(dots.min()) if len(dots) else None
    new_degenerate_faces = int((degenerate_face_mask(positions, base.triangles) &\n                                ~degenerate_face_mask(base.positions, base.triangles)).sum())
    if strict and (flips_all or new_degenerate_faces):
        raise GeometryError(
            f"build of character {character.id!r} on base {base.id!r}: "
            f"geometry gate failed — {flips_all} flipped faces across the full mesh, "
            f"{new_degenerate_faces} newly degenerate faces"
        )
    glb = write_glb(out_path, positions, base.triangles)
    qa = run_qa_gauntlet(glb) if run_qa else None
    warnings = [w.message for w in report.warnings] + \
               [w.message for w in effective.warnings]
    if unapplied:
        warnings.append(
            f"{len(unapplied)} active slider(s) have no geometry instance on "
            f"base {base.id!r}; they were not applied"
        )
    if flips_all:
        warnings.append(f"Full-mesh fold gate: {flips_all} face(s) flipped")
    if new_degenerate_faces:
        warnings.append(f"Geometry gate: {new_degenerate_faces} newly degenerate face(s)")
    return BuildReport(
        character_id=character.id,
        base_id=base.id,
        effective_sliders=dict(effective.sliders),
        derived=dict(effective.derived),
        warnings=warnings,
        applied=applied,
        unapplied=unapplied,
        flips_body=flips_body,
        flips_all=flips_all,
        min_body_dot=min_body_dot,
        min_all_dot=min_all_dot,
        base_degenerate_faces=base_degenerate_faces,
        degenerate_faces=degenerate_faces,
        new_degenerate_faces=new_degenerate_faces,
        nonfinite_vertices=nonfinite_vertices,
        glb_path=str(glb),
        qa=qa,
    )
