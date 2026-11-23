"""The character record — the one file that *is* a character.

Implements APP_BLUEPRINT §3.1 (`.afchar.json`): base ids + a sparse
slider vector + parts manifest + materials + fur params, with a schema
version field. Everything else in the app is derived from this record.

Validation contract (task spec, blueprint §4.6 spirit):
- Structural problems (wrong ``format``, unsupported ``version``,
  unknown top-level fields, malformed sections) raise :class:`SchemaError`
  naming the field — at load time, never later.
- Semantic validation against a :class:`SliderRegistry` never raises
  silently and never drops data quietly: unknown slider ids are
  collected as named errors on the returned report; out-of-range values
  are clamped with the clamp events returned as warnings.
"""

from __future__ import annotations

import json
import math
import secrets
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .errors import SchemaError, ValidationError
from .sliders import (
    ClampWarning,
    CouplingRegistry,
    EffectiveVector,
    SliderRegistry,
    evaluate_effective_vector,
)

FORMAT = "anthroforge.character"
SCHEMA_VERSION = 1
SUPPORTED_VERSIONS = frozenset({1})

_TOP_LEVEL_FIELDS = frozenset({
    "format", "version", "id", "name", "base", "sliders",
    "species_preset", "parts", "fur", "materials", "identity", "provenance",
})

_DEFAULT_BASE = {"body": "af_body_neutral_v1", "head": "af_head_neutral_v2"}

_CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def new_character_id() -> str:
    """ULID-shaped id: ``chr_`` + 26 Crockford-base32 chars
    (48-bit millisecond time + 80 bits of randomness), as in §3.1."""
    value = (int(time.time() * 1000) << 80) | secrets.randbits(80)
    chars = []
    for _ in range(26):
        chars.append(_CROCKFORD[value & 31])
        value >>= 5
    return "chr_" + "".join(reversed(chars))


@dataclass
class ValidationReport:
    """Result of :meth:`Character.validate`. ``ok`` is True iff no errors."""

    errors: list[str] = field(default_factory=list)
    warnings: list[ClampWarning] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def raise_if_errors(self) -> None:
        if self.errors:
            raise ValidationError(self)


@dataclass
class Character:
    """A character record (blueprint §3.1). Sliders are sparse:
    an absent slider id means the record's default value."""

    name: str = "Unnamed"
    base: dict = field(default_factory=lambda: dict(_DEFAULT_BASE))
    sliders: dict[str, float] = field(default_factory=dict)
    species_preset: dict | None = None
    parts: list[dict] = field(default_factory=list)
    fur: dict = field(default_factory=dict)
    materials: dict = field(default_factory=dict)
    identity: dict = field(default_factory=dict)
    provenance: dict = field(default_factory=dict)
    id: str = field(default_factory=new_character_id)
    version: int = SCHEMA_VERSION

    # -- serialisation ----------------------------------------------------

    def to_dict(self, *, include_provenance: bool = True) -> dict:
        """The record as a plain dict, in blueprint §3.1 key order.
        Share codes use ``include_provenance=False`` (§3.2)."""
        d: dict[str, Any] = {
            "format": FORMAT,
            "version": self.version,
            "id": self.id,
            "name": self.name,
            "base": dict(self.base),
            "sliders": dict(self.sliders),
            "species_preset": self.species_preset,
            "parts": [dict(p) for p in self.parts],
            "fur": self.fur,
            "materials": self.materials,
            "identity": self.identity,
        }
        if include_provenance:
            d["provenance"] = self.provenance
        return d

    @classmethod
    def from_dict(cls, data: Any) -> Character:
        """Build from a parsed dict, structurally validating every
        section. Raises :class:`SchemaError` naming the bad field."""
        if not isinstance(data, dict):
            raise SchemaError("character record must be a JSON object")
        fmt = data.get("format")
        if fmt != FORMAT:
            raise SchemaError(f"field 'format': expected {FORMAT!r}, got {fmt!r}")
        version = data.get("version")
        if not isinstance(version, int) or isinstance(version, bool) \
                or version not in SUPPORTED_VERSIONS:
            raise SchemaError(
                f"field 'version': unsupported version {version!r} "
                f"(supported: {sorted(SUPPORTED_VERSIONS)})"
            )
        unknown = sorted(set(data) - _TOP_LEVEL_FIELDS)
        if unknown:
            raise SchemaError(f"unknown top-level field(s): {', '.join(unknown)}")

        cid = data.get("id")
        if cid is not None and (not isinstance(cid, str) or not cid):
            raise SchemaError("field 'id' must be a non-empty string")
        name = data.get("name", "Unnamed")
        if not isinstance(name, str):
            raise SchemaError("field 'name' must be a string")

        base = dict(_DEFAULT_BASE)
        raw_base = data.get("base")
        if raw_base is not None:
            if not isinstance(raw_base, dict):
                raise SchemaError("field 'base' must be an object with 'body' and 'head'")
            for part in ("body", "head"):
                if part in raw_base:
                    if not isinstance(raw_base[part], str) or not raw_base[part]:
                        raise SchemaError(f"field 'base.{part}' must be a non-empty string")
                    base[part] = raw_base[part]

        sliders: dict[str, float] = {}
        raw_sliders = data.get("sliders", {})
        if not isinstance(raw_sliders, dict):
            raise SchemaError("field 'sliders' must be an object mapping slider id -> number")
        for sid, val in raw_sliders.items():
            if not isinstance(sid, str) or not sid:
                raise SchemaError("field 'sliders': slider ids must be non-empty strings")
            if not isinstance(val, (int, float)) or isinstance(val, bool) \
                    or not math.isfinite(val):
                raise SchemaError(f"field 'sliders.{sid}': value must be a finite number")
            sliders[sid] = float(val)

        species_preset = data.get("species_preset")
        if species_preset is not None and not isinstance(species_preset, dict):
            raise SchemaError("field 'species_preset' must be an object or null")

        parts: list[dict] = []
        raw_parts = data.get("parts", [])
        if not isinstance(raw_parts, list):
            raise SchemaError("field 'parts' must be a list of part entries")
        for i, entry in enumerate(raw_parts):
            if not isinstance(entry, dict):
                raise SchemaError(f"field 'parts[{i}]' must be an object")
            for key in ("slot", "part"):
                if not isinstance(entry.get(key), str) or not entry.get(key):
                    raise SchemaError(f"field 'parts[{i}].{key}' must be a non-empty string")
            parts.append(dict(entry))

        sections: dict[str, dict] = {}
        for key in ("fur", "materials", "identity", "provenance"):
            raw = data.get(key, {})
            if not isinstance(raw, dict):
                raise SchemaError(f"field '{key}' must be an object")
            sections[key] = raw

        return cls(
            name=name,
            base=base,
            sliders=sliders,
            species_preset=species_preset,
            parts=parts,
            fur=sections["fur"],
            materials=sections["materials"],
            identity=sections["identity"],
            provenance=sections["provenance"],
            id=cid if cid is not None else new_character_id(),
            version=version,
        )

    # -- file I/O -----------------------------------------------------------

    def save(self, path: str | Path) -> Path:
        """Write the record as `.afchar.json` (indent 2, §3.1 order)."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_dict(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return path

    @classmethod
    def load(cls, path: str | Path) -> Character:
        path = Path(path)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise SchemaError(f"cannot read character file {path}: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise SchemaError(f"character file {path} is not valid JSON: {exc}") from exc
        return cls.from_dict(data)

    # -- semantic validation --------------------------------------------------

    def validate(
        self,
        registry: SliderRegistry | None = None,
        *,
        apply_clamps: bool = True,
    ) -> ValidationReport:
        """Validate the slider vector against a registry.

        Unknown slider ids become named errors on the report (the ids
        are kept in the record — rejection means the report fails, not
        that data vanishes). Known-but-out-of-range values produce
        clamp warnings; the stored record is never rewritten —
        validation is a read, not an edit. ``apply_clamps`` is kept
        for signature compatibility and no longer writes anything
        back; callers that need clamped values clamp a copy
        (see :meth:`effective_sliders`).
        """
        report = ValidationReport()
        if registry is None:
            return report
        for sid, value in self.sliders.items():
            rec = registry.find(sid)
            if rec is None:
                report.errors.append(
                    f"unknown slider id: {sid!r} (not in the slider registry)"
                )
                continue
            _, warnings = rec.clamp(value)
            report.warnings.extend(warnings)
        return report

    def effective_sliders(
        self,
        registry: SliderRegistry,
        couplings: CouplingRegistry,
    ) -> EffectiveVector:
        """The character's EFFECTIVE slider vector: the raw vector
        passed through the coupling layer (MUSCLE_TISSUE_MODEL.md).
        The stored record keeps the RAW vector — couplings are an
        evaluation, never an edit. The coupling pass clamps a *copy*
        of the vector first, so couplings see the same in-range
        values they saw when validate() clamped the record in place;
        the record itself is left untouched. (Clamp warnings for the
        copy are not re-reported here — validate() is the reporting
        path for them.)"""
        clamped: dict[str, float] = {}
        for sid, value in self.sliders.items():
            rec = registry.find(sid)
            clamped[sid] = rec.clamp(value)[0] if rec is not None else value
        return evaluate_effective_vector(registry, couplings, clamped)
