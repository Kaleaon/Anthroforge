"""Fur data — species coat profiles + platform budgets as app data.

Loads and validates ``library/fur/species_profiles.json`` (the
SPECIES_FUR.md section 9 profiles: per-region density / length /
colour / layer structure, in that document's canonical region
vocabulary) and ``library/fur/budgets.json`` (FUR_BUDGETS.md platform
caps, zone budgets and the LOD switching spec).

A character record's ``fur`` block names a profile
(``{"profile": "species.bear.coat"}``); :func:`profile_for` resolves
it. These are data only — the groom/card builders consume them; no
geometry lives here.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from .errors import FurDataError

# SPECIES_FUR.md section 0.1 canonical region vocabulary.
REGIONS = frozenset({
    "scalp", "muzzle", "cheeks", "ruff", "ears.inner", "ears.back",
    "torso.front", "torso.back", "arms", "legs", "pelvis", "tail",
    "hands", "feet",
})

_REGION_NUMERIC = ("density", "length_m", "length_variation", "curl", "clump", "frizz")
_PATTERNS = frozenset({"agouti", "banded", "tipped", "solid"})


def _load(path: Path, expected_format: str) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FurDataError(f"{path}: unreadable JSON ({exc})") from exc
    if data.get("format") != expected_format:
        raise FurDataError(
            f"{path}: field 'format': expected {expected_format!r}, "
            f"got {data.get('format')!r}"
        )
    if data.get("version") != 1:
        raise FurDataError(f"{path}: unsupported version {data.get('version')!r} (supported: 1)")
    return data


def _validate_profile(profile_id: str, profile: dict, source: str) -> None:
    def fail(msg: str) -> FurDataError:
        return FurDataError(f"{source}: profile {profile_id!r}: {msg}")

    if profile.get("profile") != profile_id:
        raise fail(f"embedded 'profile' field is {profile.get('profile')!r}")
    regions = profile.get("regions")
    if not isinstance(regions, dict) or not regions:
        raise fail("missing or empty 'regions'")
    unknown = sorted(set(regions) - REGIONS)
    if unknown:
        raise fail(f"regions outside the canonical vocabulary: {unknown}")
    for region, params in regions.items():
        if not isinstance(params, dict):
            raise fail(f"region {region!r} must be an object")
        for key in _REGION_NUMERIC:
            val = params.get(key)
            if not isinstance(val, (int, float)) or isinstance(val, bool):
                raise fail(f"region {region!r}: field {key!r} must be a number")
        if not (0.0 <= params["density"] <= 1.0):
            raise fail(f"region {region!r}: density {params['density']} outside [0, 1]")
        if params["length_m"] <= 0:
            raise fail(f"region {region!r}: length_m must be positive")
        colour = params.get("colour", {})
        pattern = colour.get("pattern")
        if pattern is not None and pattern not in _PATTERNS:
            raise fail(f"region {region!r}: unknown colour pattern {pattern!r}")


class FurLibrary:
    """Species profiles + budgets loaded from library/fur/."""

    def __init__(self, folder: str | Path):
        folder = Path(folder)
        if not folder.is_dir():
            raise FurDataError(f"fur folder not found: {folder}")
        profiles_doc = _load(folder / "species_profiles.json", "anthroforge.fur_profiles")
        self._profiles: dict[str, dict] = profiles_doc["profiles"]
        for pid, profile in self._profiles.items():
            _validate_profile(pid, profile, str(folder / "species_profiles.json"))
        self._budgets_doc = _load(folder / "budgets.json", "anthroforge.fur_budgets")

    def profile_ids(self) -> list[str]:
        return sorted(self._profiles)

    def profile(self, profile_id: str) -> dict:
        prof = self._profiles.get(profile_id)
        if prof is None:
            raise FurDataError(
                f"unknown fur profile: {profile_id!r} (library holds {self.profile_ids()})"
            )
        return prof

    def profile_for(self, character_fur: dict) -> Optional[dict]:
        """Resolve a character record's ``fur`` block to its profile,
        or None when the character names no profile."""
        pid = character_fur.get("profile")
        if pid is None:
            return None
        return self.profile(pid)

    @property
    def budgets(self) -> dict:
        return self._budgets_doc

    def platform_budget(self, platform: str) -> dict:
        platforms = self._budgets_doc.get("platforms", {})
        if platform not in platforms:
            raise FurDataError(
                f"unknown fur budget platform: {platform!r} (holds {sorted(platforms)})"
            )
        return platforms[platform]
