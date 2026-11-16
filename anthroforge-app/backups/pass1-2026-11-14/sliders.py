"""Canonical slider records + registry.

Implements the canonical slider definition from
``MAKEHUMAN_OMNIVERSAL.md`` §6.1: a slider is a *semantic record*
(id, label, group, region mask rule, range + safe range, endpoint
anchor in metres, symmetry, provenance/licence, per-base instances
with QA). Vertex data lives in the instances, never in the record.

The registry loads a folder of ``<id>.json`` records (blueprint §3.6:
``library/sliders/<id>.json``) and is the one place that knows how a
raw slider value is clamped: hard clamp to the declared range, and a
non-destructive warning when a value sits outside the *safe* range
(the fold-risk band the record ships with, §6.1 design rules).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Optional

from .errors import SliderRecordError, UnknownSliderError


@dataclass(frozen=True)
class ClampWarning:
    """One clamping event. Returned, never printed, never silent."""

    slider_id: str
    requested: float
    applied: float
    kind: str  # "range" (value was changed) | "safe" (value kept, outside safe band)
    message: str


@dataclass(frozen=True)
class SliderRecord:
    """One canonical slider definition (§6.1), base-independent."""

    id: str
    label: str
    group: str
    semantics: str = ""
    region: dict = field(default_factory=dict)
    range_min: float = -1.0
    range_max: float = 1.0
    default: float = 0.0
    safe_min: Optional[float] = None
    safe_max: Optional[float] = None
    units: str = "normalised"
    endpoint_anchor: str = ""
    symmetry: Optional[str] = None
    provenance: dict = field(default_factory=dict)
    instances: dict = field(default_factory=dict)
    raw: dict = field(default_factory=dict, repr=False)

    # -- construction -----------------------------------------------------

    @classmethod
    def from_dict(cls, data: Any, *, source: str = "<record>") -> "SliderRecord":
        def fail(msg: str) -> SliderRecordError:
            return SliderRecordError(f"{source}: {msg}")

        if not isinstance(data, dict):
            raise fail("slider record must be a JSON object")
        for key in ("id", "label", "group", "range"):
            if key not in data:
                raise fail(f"missing required field {key!r}")
        if not isinstance(data["id"], str) or not data["id"]:
            raise fail("field 'id' must be a non-empty string")
        rng = data["range"]
        if not isinstance(rng, dict):
            raise fail("field 'range' must be an object")
        for key in ("min", "max", "default"):
            if key not in rng:
                raise fail(f"missing required field 'range.{key}'")
            if not isinstance(rng[key], (int, float)) or isinstance(rng[key], bool):
                raise fail(f"field 'range.{key}' must be a number")
        if not rng["max"] > rng["min"]:
            raise fail(
                f"field 'range.max' ({rng['max']}) must be greater than 'range.min' ({rng['min']})"
            )
        if not (rng["min"] <= rng["default"] <= rng["max"]):
            raise fail(
                f"field 'range.default' ({rng['default']}) lies outside "
                f"[{rng['min']}, {rng['max']}]"
            )
        for opt in ("safe_min", "safe_max"):
            if opt in rng and rng[opt] is not None and not isinstance(rng[opt], (int, float)):
                raise fail(f"field 'range.{opt}' must be a number or null")
        return cls(
            id=data["id"],
            label=data["label"],
            group=data["group"],
            semantics=data.get("semantics", ""),
            region=data.get("region", {}) or {},
            range_min=float(rng["min"]),
            range_max=float(rng["max"]),
            default=float(rng["default"]),
            safe_min=None if rng.get("safe_min") is None else float(rng["safe_min"]),
            safe_max=None if rng.get("safe_max") is None else float(rng["safe_max"]),
            units=rng.get("units", "normalised"),
            endpoint_anchor=rng.get("endpoint_anchor", ""),
            symmetry=data.get("symmetry"),
            provenance=data.get("provenance", {}) or {},
            instances=data.get("instances", {}) or {},
            raw=data,
        )

    # -- behaviour --------------------------------------------------------

    def clamp(self, value: float) -> tuple[float, list[ClampWarning]]:
        """Clamp ``value`` to this record's range.

        Returns ``(applied_value, warnings)``. Out-of-range values are
        hard-clamped to [min, max] with a ``"range"`` warning. Values
        inside the range but outside the safe band are kept as-is with
        a ``"safe"`` warning (the record's fold-risk disclosure, §6.1).
        """
        v = float(value)
        if v < self.range_min:
            return self.range_min, [
                ClampWarning(
                    self.id, v, self.range_min, "range",
                    f"{self.id}: requested {v} is below range min {self.range_min}; "
                    f"clamped to {self.range_min}",
                )
            ]
        if v > self.range_max:
            return self.range_max, [
                ClampWarning(
                    self.id, v, self.range_max, "range",
                    f"{self.id}: requested {v} is above range max {self.range_max}; "
                    f"clamped to {self.range_max}",
                )
            ]
        lo = self.range_min if self.safe_min is None else self.safe_min
        hi = self.range_max if self.safe_max is None else self.safe_max
        if v < lo or v > hi:
            return v, [
                ClampWarning(
                    self.id, v, v, "safe",
                    f"{self.id}: requested {v} is outside the safe range "
                    f"[{lo}, {hi}]; kept as-is (fold risk per record QA)",
                )
            ]
        return v, []

    @property
    def licence_tier(self) -> Optional[str]:
        """Provenance licence string, e.g. 'study-only (internal)'."""
        lic = self.provenance.get("licence")
        return lic if isinstance(lic, str) else None


class SliderRegistry:
    """All canonical slider records loaded from one folder."""

    def __init__(self, records: Iterable[SliderRecord] = ()):
        self._records: dict[str, SliderRecord] = {}
        for rec in records:
            if rec.id in self._records:
                raise SliderRecordError(f"duplicate slider id {rec.id!r}")
            self._records[rec.id] = rec

    @classmethod
    def from_folder(cls, folder: str | Path) -> "SliderRegistry":
        folder = Path(folder)
        if not folder.is_dir():
            raise SliderRecordError(f"slider folder not found: {folder}")
        records: list[SliderRecord] = []
        seen: dict[str, Path] = {}
        for path in sorted(folder.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise SliderRecordError(f"{path}: unreadable JSON ({exc})") from exc
            rec = SliderRecord.from_dict(data, source=str(path))
            if path.stem != rec.id:
                raise SliderRecordError(
                    f"{path}: filename stem {path.stem!r} does not match "
                    f"record id {rec.id!r} (blueprint §3.6 names records <id>.json)"
                )
            if rec.id in seen:
                raise SliderRecordError(
                    f"{path}: duplicate slider id {rec.id!r} (first seen in {seen[rec.id]})"
                )
            seen[rec.id] = path
            records.append(rec)
        return cls(records)

    # -- lookup -----------------------------------------------------------

    def __contains__(self, slider_id: str) -> bool:
        return slider_id in self._records

    def __len__(self) -> int:
        return len(self._records)

    def ids(self) -> list[str]:
        return sorted(self._records)

    def find(self, slider_id: str) -> Optional[SliderRecord]:
        return self._records.get(slider_id)

    def get(self, slider_id: str) -> SliderRecord:
        rec = self._records.get(slider_id)
        if rec is None:
            raise UnknownSliderError(
                f"unknown slider id: {slider_id!r} (registry holds {len(self)} records)"
            )
        return rec

    def clamp_value(self, slider_id: str, value: float) -> tuple[float, list[ClampWarning]]:
        """Clamp ``value`` against the named record (raises on unknown id)."""
        return self.get(slider_id).clamp(value)


# ---------------------------------------------------------------------------
# Couplings — the Muscle x Tissue interaction layer (MUSCLE_TISSUE_MODEL.md)
#
# A coupling record (library/couplings/<id>.json) declares how slider
# values modify EACH OTHER. Evaluation turns a character's RAW slider
# vector into its EFFECTIVE vector:
#
#     effective = evaluate_effective_vector(registry, couplings, raw)
#
# Stages run in PIPELINE_STAGES order, mirroring the geometry
# composition doctrine (base -> muscle field -> tissue field -> drape):
# the muscle stage passes muscle values through untouched; every
# interaction lives in the tissue stage, where tissue is resolved
# regionally and then attenuates definition, boosts show-through
# forms, and re-characterises the belly. The raw vector is never
# mutated; derived quantities (regional tissue, core share, ...)
# ride along on the result for the geometry layer.
# ---------------------------------------------------------------------------

from .errors import CouplingRecordError  # noqa: E402  (section import)

PIPELINE_STAGES = ("authoring", "distribution", "muscle", "tissue")

_COUPLING_KINDS = frozenset({
    "composition_order", "dial_expand", "mass_distribution",
    "regional_tissue", "definition_attenuation", "show_through",
    "power_belly", "tissue_wrap",
})

# Within the tissue stage, regional tissue must resolve before the
# couplings that consume it; the wrap audit runs last, over the final
# resolved tissue state.
_TISSUE_KIND_ORDER = ("regional_tissue", "definition_attenuation",
                      "show_through", "power_belly", "tissue_wrap")


def _interp(anchors: list, x: float) -> float:
    """Piecewise-linear interpolation over sorted [x, y] anchors,
    clamped flat outside the anchor span."""
    pts = sorted((float(a[0]), float(a[1])) for a in anchors)
    if x <= pts[0][0]:
        return pts[0][1]
    if x >= pts[-1][0]:
        return pts[-1][1]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 <= x <= x1:
            if x1 == x0:
                return y1
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return pts[-1][1]  # unreachable; keeps type-checkers calm


@dataclass(frozen=True)
class CouplingRecord:
    """One declarative coupling definition (library/couplings/)."""

    id: str
    kind: str
    stage: str
    label: str = ""
    semantics: str = ""
    params: dict = field(default_factory=dict)
    provenance: dict = field(default_factory=dict)
    raw: dict = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: Any, *, source: str = "<record>") -> "CouplingRecord":
        def fail(msg: str) -> CouplingRecordError:
            return CouplingRecordError(f"{source}: {msg}")

        if not isinstance(data, dict):
            raise fail("coupling record must be a JSON object")
        if data.get("format") != "anthroforge.coupling":
            raise fail(f"field 'format': expected 'anthroforge.coupling', got {data.get('format')!r}")
        if data.get("version") != 1:
            raise fail(f"field 'version': unsupported version {data.get('version')!r} (supported: 1)")
        for key in ("id", "kind", "stage", "params"):
            if key not in data:
                raise fail(f"missing required field {key!r}")
        if data["kind"] not in _COUPLING_KINDS:
            raise fail(f"field 'kind': unknown coupling kind {data['kind']!r}")
        if data["stage"] not in PIPELINE_STAGES and data["stage"] != "meta":
            raise fail(f"field 'stage': unknown stage {data['stage']!r}")
        if not isinstance(data["params"], dict):
            raise fail("field 'params' must be an object")
        return cls(
            id=data["id"], kind=data["kind"], stage=data["stage"],
            label=data.get("label", ""), semantics=data.get("semantics", ""),
            params=data["params"], provenance=data.get("provenance", {}) or {},
            raw=data,
        )


class CouplingRegistry:
    """All coupling records loaded from one folder (library/couplings/)."""

    def __init__(self, records: Iterable[CouplingRecord] = ()):
        self._records: dict[str, CouplingRecord] = {}
        for rec in records:
            if rec.id in self._records:
                raise CouplingRecordError(f"duplicate coupling id {rec.id!r}")
            self._records[rec.id] = rec

    @classmethod
    def from_folder(cls, folder: str | Path) -> "CouplingRegistry":
        folder = Path(folder)
        if not folder.is_dir():
            raise CouplingRecordError(f"coupling folder not found: {folder}")
        records: list[CouplingRecord] = []
        for path in sorted(folder.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise CouplingRecordError(f"{path}: unreadable JSON ({exc})") from exc
            rec = CouplingRecord.from_dict(data, source=str(path))
            if path.stem != rec.id:
                raise CouplingRecordError(
                    f"{path}: filename stem {path.stem!r} does not match "
                    f"record id {rec.id!r}"
                )
            records.append(rec)
        return cls(records)

    def __len__(self) -> int:
        return len(self._records)

    def ids(self) -> list[str]:
        return sorted(self._records)

    def by_stage(self, stage: str) -> list[CouplingRecord]:
        return [r for r in self._records.values() if r.stage == stage]

    def find_kind(self, kind: str) -> Optional[CouplingRecord]:
        for rec in self._records.values():
            if rec.kind == kind:
                return rec
        return None


@dataclass
class EffectiveVector:
    """Result of coupling evaluation: the effective slider vector,
    the derived quantities the geometry layer consumes, and every
    warning raised on the way (clamps + coupling advisories)."""

    sliders: dict[str, float]
    derived: dict[str, float] = field(default_factory=dict)
    warnings: list[ClampWarning] = field(default_factory=list)


class _Eval:
    """Mutable evaluation context passed between coupling handlers."""

    def __init__(self, registry: SliderRegistry, raw: dict[str, float]):
        self.registry = registry
        self.sliders: dict[str, float] = dict(raw)
        self.derived: dict[str, float] = {}
        self.warnings: list[ClampWarning] = []
        self.dist_tissue: dict[str, float] = {}
        self.dist_muscle: dict[str, float] = {}
        self.region_to_macro: dict[str, str] = {}
        self.tissue: dict[str, float] = {}
        self.tissue_level: float = 0.0

    def value(self, slider_id: str) -> float:
        """Current working value, falling back to the record default."""
        if slider_id in self.sliders:
            return self.sliders[slider_id]
        rec = self.registry.find(slider_id)
        return rec.default if rec is not None else 0.0

    def tissue_at(self, region: str) -> float:
        return self.tissue.get(region, 0.0)


def _apply_dial_expand(ctx: _Eval, rec: CouplingRecord) -> None:
    p = rec.params
    driver = p["driver"]
    if driver not in ctx.sliders:
        return
    d = ctx.sliders[driver]
    for sid, spec in p["targets"].items():
        if sid in ctx.sliders:
            continue  # explicit values always win over the dial
        ctx.sliders[sid] = spec["at_driver_0"] + (spec["at_driver_1"] - spec["at_driver_0"]) * d


def _apply_mass_distribution(ctx: _Eval, rec: CouplingRecord) -> None:
    p = rec.params
    d = ctx.value(p["driver"])
    anchors = p["anchors"]
    ctx.region_to_macro = dict(p.get("region_to_macro", {}))
    for macro in p["macro_regions"]:
        w = _interp([[a["at"], a["weights"][macro]] for a in anchors], d)
        ctx.dist_tissue[macro] = 1.0 + (w - 1.0) * float(p.get("strength_tissue", 1.0))
        ctx.dist_muscle[macro] = 1.0 + (w - 1.0) * float(p.get("strength_muscle", 0.6))
        ctx.derived[f"distribution.weight.{macro}"] = w
        ctx.derived[f"distribution.tissue.{macro}"] = ctx.dist_tissue[macro]
        ctx.derived[f"distribution.muscle.{macro}"] = ctx.dist_muscle[macro]


def _apply_regional_tissue(ctx: _Eval, rec: CouplingRecord) -> None:
    p = rec.params
    level_id = p["level_slider"]
    if level_id in ctx.sliders:
        level = ctx.sliders[level_id]
    else:
        num = den = 0.0
        for sid, w in p["level_from"].items():
            if sid in ctx.sliders:
                num += float(w) * ctx.sliders[sid]
                den += float(w)
        level = num / den if den else 0.0
    ctx.tissue_level = level
    ctx.derived["tissue.level"] = level
    profile = p["profiles"][p.get("default_profile", "lifter")]
    for region, weight in profile.items():
        macro = ctx.region_to_macro.get(region)
        factor = ctx.dist_tissue.get(macro, 1.0) if macro else 1.0
        t = min(1.0, max(0.0, level * float(weight) * factor))
        ctx.tissue[region] = t
        ctx.derived[f"tissue.{region}"] = t


def _apply_definition_attenuation(ctx: _Eval, rec: CouplingRecord) -> None:
    p = rec.params
    gate = p.get("muscle_gate", {"floor": 1.0, "full_at": 1.0})
    muscle = ctx.value(p["muscle_slider"])
    g = float(gate["floor"]) + (1.0 - float(gate["floor"])) * min(1.0, max(0.0, muscle) / float(gate["full_at"]))
    class_region = p["class_region"]
    for sid, cls in p["targets"].items():
        if sid not in ctx.sliders:
            continue
        a = _interp(p["curves"][cls], ctx.tissue_at(class_region[cls]))
        ctx.derived[f"attenuation.{sid}"] = a * g
        ctx.sliders[sid] = ctx.sliders[sid] * a * g


def _apply_show_through(ctx: _Eval, rec: CouplingRecord) -> None:
    factor = float(rec.params["factor"])
    for sid, region in rec.params["targets"].items():
        if sid not in ctx.sliders:
            continue
        ctx.sliders[sid] = ctx.sliders[sid] * (1.0 + factor * ctx.tissue_at(region))


def _apply_power_belly(ctx: _Eval, rec: CouplingRecord) -> None:
    p = rec.params
    num = den = 0.0
    for sid, w in p["belly_sliders"].items():
        if sid in ctx.sliders:
            num += float(w) * ctx.sliders[sid]
            den += float(w)
    if not den:
        return
    composite = num / den
    muscle = ctx.value(p["muscle_slider"])
    core_share = muscle * composite
    ctx.derived["power_belly.composite"] = composite
    ctx.derived["power_belly.core_share"] = core_share
    ctx.derived["power_belly.drape_share"] = 1.0 - core_share
    ctx.derived["power_belly.tilt_deg"] = float(p["tilt_anchor_deg"]) * core_share
    ctx.derived["power_belly.index"] = composite * (0.5 + 0.5 * muscle)
    chest = ctx.value(p["chest_slider"])
    if muscle >= 0.5 and composite - chest > float(p["chest_gap_advisory"]):
        ctx.warnings.append(ClampWarning(
            "power_belly", composite, composite, "coupling",
            "power belly: belly composite exceeds the chest slider by more "
            "than the advisory gap at lifter muscle levels - verify M4 "
            "(chest:waist >= 1.28) on the mesh; the chest ring must stay "
            "dominant (BARA_LESSONS R17)"))
    if muscle < float(p["bare_belly_muscle_floor"]) and composite > float(p["bare_belly_advisory"]):
        ctx.warnings.append(ClampWarning(
            "power_belly", composite, composite, "coupling",
            "power belly: large belly with little muscle under it reads as "
            "tissue-only (the Fat Males failure, BARA_LESSONS R18) - if a "
            "carried gut is intended, raise the Muscle vector, not the belly"))


def _apply_tissue_wrap(ctx: _Eval, rec: CouplingRecord) -> None:
    """Circumferential wrap audit (MUSCLE_TISSUE_MODEL.md section 4).

    Fat is a ring, not a front patch: per band, emit the wrap factor
    (side-sector radial gain the geometry kernel must deliver, as a
    fraction of the front-sector gain, rising with the band's front
    tissue) and, where the band has a resolved side region, the
    side/front tissue ratio. A ratio below the floor while the front
    carries real tissue is the 'stiff sides' failure — an advisory
    here (it guards the regional profile); on a mesh it fails QA.
    This handler never rewrites slider values."""
    p = rec.params
    floor_ratio = float(p["floor_ratio"])
    min_front = float(p.get("min_front_tissue", 0.3))
    for band, spec in p["bands"].items():
        front = ctx.tissue_at(spec["front"])
        ctx.derived[f"wrap.factor.{band}"] = _interp(p["factor_anchors"], front)
        side_region = spec.get("side")
        if not side_region or front <= 1e-9:
            continue
        ratio = ctx.tissue_at(side_region) / front
        ctx.derived[f"wrap.ratio.{band}"] = ratio
        if front >= min_front and ratio < floor_ratio:
            ctx.warnings.append(ClampWarning(
                "tissue_wrap", ratio, ratio, "coupling",
                f"tissue wrap: stiff sides in the {band} band - side/front "
                f"tissue ratio {ratio:.2f} is below the floor {floor_ratio} "
                f"while front tissue is {front:.2f}; fat wraps "
                "circumferentially, so the flanks must carry their share of "
                "the ring (MUSCLE_TISSUE_MODEL.md section 4)"))


_HANDLERS = {
    "dial_expand": _apply_dial_expand,
    "mass_distribution": _apply_mass_distribution,
    "regional_tissue": _apply_regional_tissue,
    "definition_attenuation": _apply_definition_attenuation,
    "show_through": _apply_show_through,
    "power_belly": _apply_power_belly,
    "tissue_wrap": _apply_tissue_wrap,
}


def evaluate_effective_vector(
    registry: SliderRegistry,
    couplings: CouplingRegistry,
    raw_sliders: dict[str, float],
) -> EffectiveVector:
    """Pass a raw slider vector through every coupling, in pipeline
    stage order, and return the effective vector + derived quantities
    + warnings. The input dict is never mutated. A final registry
    clamp pass guarantees every known slider lands inside its record
    range (clamps surface as warnings, as everywhere in the Core)."""
    comp = couplings.find_kind("composition_order")
    if comp is not None:
        declared = list(comp.params.get("evaluation_stages", []))
        if declared != list(PIPELINE_STAGES):
            raise CouplingRecordError(
                f"{comp.id}: composition record declares evaluation stages "
                f"{declared}, code pipeline is {list(PIPELINE_STAGES)} - "
                "the doctrine and the engine disagree; fix one of them"
            )
    ctx = _Eval(registry, raw_sliders)
    for stage in PIPELINE_STAGES:
        records = couplings.by_stage(stage)
        if stage == "tissue":
            records.sort(key=lambda r: _TISSUE_KIND_ORDER.index(r.kind)
                           if r.kind in _TISSUE_KIND_ORDER else len(_TISSUE_KIND_ORDER))
        for rec in records:
            handler = _HANDLERS.get(rec.kind)
            if handler is not None:
                handler(ctx, rec)
    # Final clamp pass against the registry (unknown ids pass through;
    # Character.validate is responsible for flagging those).
    for sid, value in list(ctx.sliders.items()):
        rec = registry.find(sid)
        if rec is None:
            continue
        applied, warnings = rec.clamp(value)
        ctx.sliders[sid] = applied
        ctx.warnings.extend(warnings)
    return EffectiveVector(sliders=ctx.sliders, derived=ctx.derived, warnings=ctx.warnings)
