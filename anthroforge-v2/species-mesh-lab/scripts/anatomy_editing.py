"""Persistent, editable anatomy state for the Species Mesh Lab.

This module is Blender-independent. The creator UI, preview adapter and exporter
should all consume the same resolved state returned by resolve_anatomy().
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from typing import Any

FORMAT = "anthroforge.anatomy-instance"
VERSION = 1
SCALE_MIN, SCALE_MAX = 0.15, 8.0
COUNT_MIN, COUNT_MAX = 1, 4
DIMENSION_KEYS = ("length", "girth", "sac_width", "sac_height", "member_spacing")


class AnatomyStateError(ValueError):
    """Raised when saved anatomy state cannot be resolved safely."""


@dataclass
class MemberOverride:
    length: float = 1.0
    girth: float = 1.0
    curve: float = 0.0
    offset_x: float = 0.0
    offset_y: float = 0.0
    offset_z: float = 0.0


@dataclass
class AnatomyInstance:
    profile_id: str
    instance_id: str
    enabled: bool = True
    scale: float = 1.0
    axis_scale: dict[str, float] = field(default_factory=dict)
    member_count: int | None = None
    members: dict[str, MemberOverride] = field(default_factory=dict)
    sac_scale: dict[str, float] = field(default_factory=dict)
    socket_offset: dict[str, float] = field(default_factory=lambda: {"x": 0.0, "y": 0.0, "z": 0.0})
    adult_only: bool = True


def load_profiles(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema") != "anthroforge.adult-anatomy-profiles" or data.get("version") != 1:
        raise AnatomyStateError("Unsupported anatomy profile schema")
    return data["profiles"]


def _finite_number(value: Any, label: str, minimum: float | None = None,
                   maximum: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AnatomyStateError(f"{label} must be a number")
    value = float(value)
    if not __import__("math").isfinite(value):
        raise AnatomyStateError(f"{label} must be finite")
    if minimum is not None and value < minimum:
        raise AnatomyStateError(f"{label} must be >= {minimum}")
    if maximum is not None and value > maximum:
        raise AnatomyStateError(f"{label} must be <= {maximum}")
    return value


def new_instance(profile: dict[str, Any], instance_id: str) -> AnatomyInstance:
    if not instance_id or not isinstance(instance_id, str):
        raise AnatomyStateError("instance_id must be a non-empty stable string")
    count = int(profile["default_member_count"])
    return AnatomyInstance(
        profile_id=profile["id"], instance_id=instance_id,
        member_count=count,
        members={f"member-{i+1:02d}": MemberOverride() for i in range(count)},
    )


def resolve_anatomy(instance: AnatomyInstance, profiles: dict[str, Any],
                    body_plan: str, adult_content_enabled: bool = False) -> dict[str, Any]:
    """Return canonical dimensions and stable component records for preview/export.

    The adult-content preference is an app visibility/export gate, not age
    verification. The caller must apply the product's age policy separately.
    """
    if instance.profile_id not in profiles:
        raise AnatomyStateError(f"Unknown anatomy profile: {instance.profile_id}")
    profile = profiles[instance.profile_id]
    if not instance.adult_only or not profile.get("adult_only"):
        raise AnatomyStateError("Adult-only anatomy must remain explicitly gated")
    if not adult_content_enabled:
        raise AnatomyStateError("Adult anatomy is disabled by application settings")
    if body_plan not in profile.get("compatible_plans", []):
        raise AnatomyStateError(f"{instance.profile_id} is incompatible with {body_plan}")

    scale = _finite_number(instance.scale, "scale", SCALE_MIN, SCALE_MAX)
    count = instance.member_count
    if isinstance(count, bool) or not isinstance(count, int) or not COUNT_MIN <= count <= COUNT_MAX:
        raise AnatomyStateError("member_count must be an integer from 1 through 4")

    dimensions = {}
    for key in DIMENSION_KEYS:
        base = float(profile["dimensions_m"].get(key, 0.0))
        axis = _finite_number(instance.axis_scale.get(key, 1.0), f"axis_scale.{key}", 0.05, 20.0)
        dimensions[key] = base * scale * axis

    sac = {}
    for key, base_key in (("width", "sac_width"), ("height", "sac_height"), ("depth", "sac_width")):
        axis = _finite_number(instance.sac_scale.get(key, 1.0), f"sac_scale.{key}", 0.05, 20.0)
        sac[key] = dimensions[base_key] * axis

    resolved_members = []
    for index in range(count):
        component_id = f"{instance.instance_id}:member-{index+1:02d}"
        member_key = f"member-{index+1:02d}"
        override = instance.members.get(member_key, MemberOverride())
        resolved_members.append({
            "component_id": component_id,
            "index": index + 1,
            "length_m": dimensions["length"] * _finite_number(override.length, member_key+".length", 0.05, 20.0),
            "girth_m": dimensions["girth"] * _finite_number(override.girth, member_key+".girth", 0.05, 20.0),
            "curve": _finite_number(override.curve, member_key+".curve", -1.0, 1.0),
            "offset_m": {
                "x": _finite_number(override.offset_x, member_key+".offset_x", -10.0, 10.0) * scale,
                "y": _finite_number(override.offset_y, member_key+".offset_y", -10.0, 10.0) * scale,
                "z": _finite_number(override.offset_z, member_key+".offset_z", -10.0, 10.0) * scale,
            },
        })

    socket = {axis: _finite_number(instance.socket_offset.get(axis, 0.0), f"socket_offset.{axis}", -10.0, 10.0)
              for axis in ("x", "y", "z")}
    return {
        "format": FORMAT, "version": VERSION,
        "instance_id": instance.instance_id, "profile_id": instance.profile_id,
        "body_plan": body_plan, "adult_only": True,
        "scale": scale, "dimensions_m": dimensions, "sac_dimensions_m": sac,
        "socket_offset_m": socket, "members": resolved_members,
        "component_ids": [f"{instance.instance_id}:base", f"{instance.instance_id}:sac"]
                          + [m["component_id"] for m in resolved_members],
        "warnings": ["Extreme-scale intersections require collision/clearance review; requested dimensions are not silently clamped."]
    }


def instance_to_dict(instance: AnatomyInstance) -> dict[str, Any]:
    return {
        "format": FORMAT, "version": VERSION,
        "profile_id": instance.profile_id, "instance_id": instance.instance_id,
        "enabled": instance.enabled, "adult_only": instance.adult_only,
        "scale": instance.scale, "axis_scale": dict(instance.axis_scale),
        "member_count": instance.member_count,
        "members": {key: asdict(value) for key, value in sorted(instance.members.items())},
        "sac_scale": dict(instance.sac_scale), "socket_offset": dict(instance.socket_offset),
    }


def instance_from_dict(data: dict[str, Any]) -> AnatomyInstance:
    if data.get("format") != FORMAT or data.get("version") != VERSION:
        raise AnatomyStateError("Unsupported anatomy instance format")
    members = {key: MemberOverride(**value) for key, value in data.get("members", {}).items()}
    return AnatomyInstance(
        profile_id=data["profile_id"], instance_id=data["instance_id"],
        enabled=bool(data.get("enabled", True)), scale=data.get("scale", 1.0),
        axis_scale=dict(data.get("axis_scale", {})), member_count=data.get("member_count"),
        members=members, sac_scale=dict(data.get("sac_scale", {})),
        socket_offset=dict(data.get("socket_offset", {"x": 0.0, "y": 0.0, "z": 0.0})),
        adult_only=bool(data.get("adult_only", False)),
    )


def save_instance(instance: AnatomyInstance, path: str | Path) -> None:
    Path(path).write_text(json.dumps(instance_to_dict(instance), indent=2, sort_keys=True) + "\n",
                          encoding="utf-8")


def load_instance(path: str | Path) -> AnatomyInstance:
    return instance_from_dict(json.loads(Path(path).read_text(encoding="utf-8")))
