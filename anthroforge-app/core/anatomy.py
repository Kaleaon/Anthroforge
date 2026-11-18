"""Plan-aware, rig-validated anatomy part manifests.

The character record remains the source of truth. This module validates
swappable anatomy parts against the canonical socket/body-plan contract;
it does not invent meshes or pretend a metadata-only part is exportable.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path, PureWindowsPath
from typing import Any, Iterable

PART_FORMAT = "anthroforge.part"
PART_VERSION = 1
BODY_PLANS = frozenset({
    "plan.biped",
    "plan.quadruped_taur",
    "plan.quadruped_feral",
    "plan.naga",
})
GENITAL_SOCKET = "pelvis.genital"
GENITAL_CHAIN = ("GenBase", "Gen01", "Gen02", "Gen03", "Gen04")
GENITAL_REQUIRED_BONES = frozenset((*GENITAL_CHAIN, "GenScrot"))
GENITAL_MORPH_CHANNELS = frozenset({
    "length", "girth", "base_volume", "curve", "lift", "scrotal_volume",
})


@dataclass
class AnatomyValidation:
    """Named validation errors and warnings; never silently drops a part."""

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    resolved_parts: list[dict[str, Any]] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def _is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_part_manifest(
    data: Any,
    *,
    source: str = "<memory>",
    require_mesh_files: bool = False,
) -> list[str]:
    """Validate the common part contract and additional genital-module rules.

    Mesh paths are relative to the part manifest. When require_mesh_files is
    true, LOD0 must exist on disk; a manifest alone is never an exportable part.
    """
    errors: list[str] = []
    if not isinstance(data, dict):
        return [f"{source}: manifest must be a JSON object"]
    if data.get("format") != PART_FORMAT:
        errors.append(f"{source}: format must be {PART_FORMAT!r}")
    if data.get("version") != PART_VERSION:
        errors.append(f"{source}: version must be {PART_VERSION}")
    if not _is_nonempty_string(data.get("id")):
        errors.append(f"{source}: id must be a non-empty string")
    if data.get("kind") != "anatomy":
        errors.append(f"{source}: kind must be 'anatomy'")

    sockets = data.get("sockets")
    if not isinstance(sockets, list) or not sockets or any(not _is_nonempty_string(s) for s in sockets):
        errors.append(f"{source}: sockets must be a non-empty list of names")

    meshes = data.get("meshes")
    lod0 = meshes.get("lod0") if isinstance(meshes, dict) else None
    if not _is_nonempty_string(lod0):
        errors.append(f"{source}: meshes.lod0 is required")
    else:
        # Validate both path grammars so manifests behave consistently on
        # Windows and POSIX (where backslashes are otherwise ordinary chars).
        windows_asset = PureWindowsPath(lod0)
        portable_asset = Path(lod0.replace("\\\\", "/"))
        unsafe_path = (
            portable_asset.is_absolute()
            or windows_asset.is_absolute()
            or bool(windows_asset.drive)
            or ".." in portable_asset.parts
            or ".." in windows_asset.parts
            or "\\x00" in lod0
        )
        if unsafe_path:
            errors.append(f"{source}: meshes.lod0 must stay inside the part folder")
        elif require_mesh_files:
            part_root = Path(source).parent.resolve()
            try:
                asset_path = (part_root / portable_asset).resolve()
                contained = asset_path.is_relative_to(part_root)
            except (OSError, RuntimeError, ValueError):
                contained = False
                asset_path = part_root
            # resolve() follows symlinks, preventing a relative asset path
            # from escaping the part folder through a linked file.
            if not contained:
                errors.append(f"{source}: meshes.lod0 resolves outside the part folder")
            elif not asset_path.is_file():
                errors.append(f"{source}: meshes.lod0 asset does not exist: {lod0}")
            elif asset_path.stat().st_size <= 0:
                errors.append(f"{source}: meshes.lod0 asset is empty: {lod0}")

    skin = data.get("skin")
    if not isinstance(skin, dict):
        errors.append(f"{source}: skin must be an object")
        skin = {}
    if skin.get("mode") not in {"own-weights", "inherit", "rigid"}:
        errors.append(f"{source}: skin.mode must be own-weights, inherit, or rigid")
    bones = skin.get("bones")
    if not isinstance(bones, list) or any(not _is_nonempty_string(b) for b in bones):
        errors.append(f"{source}: skin.bones must be a list of bone names")
        bones = []

    plan_fit = data.get("plan_fit")
    if not isinstance(plan_fit, dict):
        errors.append(f"{source}: plan_fit must be an object")
        plan_fit = {}
    plans = plan_fit.get("plans")
    if not isinstance(plans, list) or not plans:
        errors.append(f"{source}: plan_fit.plans must be a non-empty list")
        plans = []
    invalid_plans = [p for p in plans if not _is_nonempty_string(p)]
    if invalid_plans:
        errors.append(f"{source}: plan_fit.plans entries must be non-empty strings")
    else:
        unknown_plans = sorted(set(plans) - BODY_PLANS)
        if unknown_plans:
            errors.append(f"{source}: unknown body plan(s): {unknown_plans}")
    socket_map = plan_fit.get("socket_by_plan", {})
    if not isinstance(socket_map, dict):
        errors.append(f"{source}: plan_fit.socket_by_plan must be an object")
        socket_map = {}
    for plan, socket in socket_map.items():
        if plan not in plans:
            errors.append(f"{source}: socket_by_plan contains undeclared plan {plan!r}")
        if not _is_nonempty_string(socket):
            errors.append(f"{source}: socket_by_plan[{plan!r}] must be a non-empty string")

    if GENITAL_SOCKET in (sockets if isinstance(sockets, list) else []):
        if data.get("adult_only") is not True:
            errors.append(f"{source}: genital modules must declare adult_only=true")
        if skin.get("mode") != "own-weights":
            errors.append(f"{source}: animated genital modules require skin.mode='own-weights'")
        missing = sorted(GENITAL_REQUIRED_BONES - set(bones))
        if missing:
            errors.append(f"{source}: genital rig is missing required bones: {missing}")
        function = data.get("function")
        genital = function.get("genital") if isinstance(function, dict) else None
        if not isinstance(genital, dict):
            errors.append(f"{source}: function.genital is required for pelvis.genital parts")
        else:
            channels = genital.get("morph_channels")
            if not isinstance(channels, list) or not channels:
                errors.append(f"{source}: function.genital.morph_channels must be a non-empty list")
            else:
                unknown = sorted(set(channels) - GENITAL_MORPH_CHANNELS)
                if unknown:
                    errors.append(f"{source}: unsupported genital morph channel(s): {unknown}")
            motion = genital.get("motion")
            if not isinstance(motion, dict):
                errors.append(f"{source}: function.genital.motion must be an object")
            else:
                chain = motion.get("chain")
                if chain != list(GENITAL_CHAIN):
                    errors.append(
                        f"{source}: function.genital.motion.chain must be {list(GENITAL_CHAIN)}"
                    )
                if not _is_nonempty_string(motion.get("collision_profile")):
                    errors.append(f"{source}: function.genital.motion.collision_profile is required")

    return errors


class AnatomyLibrary:
    """Loads anatomy part manifests from library/parts/**/part.json."""

    def __init__(self, parts: dict[str, dict[str, Any]] | None = None):
        self.parts = dict(parts or {})

    @classmethod
    def from_folder(
        cls,
        folder: str | Path,
        *,
        require_mesh_files: bool = True,
    ) -> "AnatomyLibrary":
        root = Path(folder)
        if not root.is_dir():
            raise FileNotFoundError(f"anatomy parts folder not found: {root}")
        loaded: dict[str, dict[str, Any]] = {}
        for manifest_path in sorted(root.rglob("part.json")):
            try:
                data = json.loads(manifest_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise ValueError(f"{manifest_path}: unreadable part manifest: {exc}") from exc
            if not isinstance(data, dict) or data.get("kind") != "anatomy":
                continue
            errors = validate_part_manifest(
                data, source=str(manifest_path), require_mesh_files=require_mesh_files
            )
            if errors:
                raise ValueError("; ".join(errors))
            part_id = data["id"]
            if part_id in loaded:
                raise ValueError(f"duplicate anatomy part id: {part_id!r}")
            loaded[part_id] = data
        return cls(loaded)

    def get(self, part_id: str) -> dict[str, Any] | None:
        return self.parts.get(part_id)


def validate_character_anatomy(
    parts: Iterable[dict[str, Any]],
    library: AnatomyLibrary,
    *,
    body_plan: str = "plan.biped",
    adult_content_enabled: bool = False,
) -> AnatomyValidation:
    """Validate equipped anatomy against plan, socket, and adult-content settings.

    adult_content_enabled is a presentation/export preference, not age
    verification. Applications must apply their own account/age policy.
    """
    result = AnatomyValidation()
    if body_plan not in BODY_PLANS:
        result.errors.append(f"unknown body plan: {body_plan!r}")
        return result

    if not isinstance(adult_content_enabled, bool):
        result.errors.append("adult_content_enabled must be a boolean preference")
        return result

    occupied_genital_socket = False
    for index, entry in enumerate(parts):
        if not isinstance(entry, dict):
            result.errors.append(f"parts[{index}] must be an object")
            continue
        slot = entry.get("slot")
        part_id = entry.get("part")
        if not _is_nonempty_string(slot) or not _is_nonempty_string(part_id):
            result.errors.append(f"parts[{index}] requires non-empty slot and part fields")
            continue
        manifest = library.get(part_id)
        if manifest is None:
            if slot == GENITAL_SOCKET:
                result.errors.append(f"parts[{index}]: unknown anatomy part {part_id!r}")
            continue
        if slot not in manifest.get("sockets", []):
            result.errors.append(
                f"parts[{index}]: {part_id!r} does not provide socket {slot!r}"
            )
            continue

        fit = manifest.get("plan_fit", {})
        plans = fit.get("plans", [])
        if body_plan not in plans:
            result.errors.append(
                f"parts[{index}]: {part_id!r} is not fitted for {body_plan!r}"
            )
            continue
        if body_plan in fit.get("excluded_plans", []):
            result.errors.append(
                f"parts[{index}]: {part_id!r} is excluded on {body_plan!r}"
            )
            continue
        resolved_socket = fit.get("socket_by_plan", {}).get(body_plan, slot)
        if resolved_socket != slot:
            result.errors.append(
                f"parts[{index}]: {part_id!r} expects socket {resolved_socket!r} "
                f"on {body_plan!r}, not {slot!r}"
            )
            continue

        if slot == GENITAL_SOCKET:
            if occupied_genital_socket:
                result.errors.append("only one part may occupy pelvis.genital")
                continue
            occupied_genital_socket = True
            if manifest.get("adult_only") is True and not adult_content_enabled:
                result.errors.append(
                    f"{part_id!r} is adult-only; enable adult anatomy to equip/export it"
                )
                continue

        result.resolved_parts.append({
            "part": part_id,
            "slot": slot,
            "body_plan": body_plan,
            "adult_only": bool(manifest.get("adult_only", False)),
        })
    return result
