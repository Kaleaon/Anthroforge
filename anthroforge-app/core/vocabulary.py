"""Web ↔ Core vocabulary — the one translation table for the split-brain fix.

The Babylon web apps (desktop v2 + Telegram Mini App) speak a *rendering*
vocabulary: procedural scale factors (``morph.*``), BodySlide ``.osd``
differentials (``bodyslide.*``), SoS genital rig values (``sos.*``) and
pose drivers (``driver.*``), on RuthAndRoth web bodies (``max`` /
``maxwell`` / ``maxine`` / ``bara``) with head ``web_v2``.

The Python Core speaks canonical slider records
(``library/sliders/<id>.json``, e.g. ``body.belly.protrusion``) on base
``af_body_neutral_v1`` / ``af_head_neutral_v2``. ``Character.validate()``
rejects every web slider id as unknown, and ``build_character()`` raises
on the web base ids — so a record saved from either web UI could never
be loaded by the Core. That was the vocabulary split-brain (Hydrogen
plan §(e) item 2; Tallis's read left it unverified from his bundle —
verified here against the real files).

The honest shape of the mapping, established by reading both sides:

* Only the six ``bodyslide.*`` keys have a defensible canonical
  counterpart. The ``.osd`` differentials are 0–100 scales; the
  canonical sliders are mostly 0–1 (``head.brow.projection`` is
  −50…150), so the table carries a scale factor. These are
  *approximate* bridges — an .osd differential is not the same morph
  as a learned Core field — and the table says so on each entry.
* ``morph.*``, ``sos.*`` and ``driver.*`` have NO canonical
  counterpart (there is no height / ears / tail / genital slider in
  the registry). Inventing one would be fabrication. They are
  therefore carried through *losslessly* under ``identity`` (a
  free-form section ``Character.from_dict`` accepts as-is), where the
  web UI can read them back on import. Nothing is silently dropped.
* Web bodies all render the same neutral Core base; the web body id is
  preserved under ``identity.base_body`` (and ``web_v2`` under
  ``identity.base_head``) so the rendering choice survives the trip.
* Slider ids that are already canonical (``body.*`` / ``head.*`` —
  the registry's own ids, as the preset files carry them) pass
  through untouched. Only a *web-prefixed* id the table does not know
  (e.g. a new ``bodyslide.*`` key) is preserved under
  ``identity.unmapped_sliders`` and named in the returned warnings —
  never silently dropped, never passed off as canonical.

The JS twin of this table is ``telegram-miniapp/vocabulary.js``
(``AFVocabulary``). The two are cross-checked by
``tests/test_vocabulary.py``, which parses the JS table and compares
it entry-for-entry with this module. Change one, change both, and let
the test catch drift.
"""

from __future__ import annotations

from typing import Any

VOCABULARY_VERSION = 1

# Web body id -> canonical Core base id. All four web bodies are
# rendering profiles of the neutral base for Core purposes.
BASE_BODY_MAP: dict[str, str] = {
    "max": "af_body_neutral_v1",
    "maxwell": "af_body_neutral_v1",
    "maxine": "af_body_neutral_v1",
    "bara": "af_body_neutral_v1",
}

HEAD_MAP: dict[str, str] = {
    "web_v2": "af_head_neutral_v2",
}

# Web slider id -> (canonical slider id, scale). The web value is
# multiplied by the scale to give the canonical value. Each entry is
# an APPROXIMATE bridge (see module docstring): .osd differentials
# are not the learned Core fields, but they are the closest semantic
# match and the direction/magnitude are preserved.
SLIDER_MAP: dict[str, tuple[str, float]] = {
    # Muscular hypertrophy (.osd) -> bara muscle vector (0..1).
    "bodyslide.samson": ("body.build.muscle", 0.01),
    # Powerbelly / core mass (.osd) -> belly-centred adiposity (-1..1).
    "bodyslide.samuel": ("body.belly.protrusion", 0.01),
    # Lean / waist taper (.osd) -> HIMBO lean (-1..1).
    "bodyslide.samael": ("body.himbo.lean", 0.01),
    # Gluteal shelf & roundness (.osd) -> HIMBO glutes (0..1).
    "bodyslide.glutes": ("body.himbo.legs_glutes", 0.01),
    # Trapezius hump (.osd) -> HIMBO traps (0..1).
    "bodyslide.traps": ("body.himbo.arms_traps", 0.01),
    # Brow scowl & fang snarl (.osd) -> brow projection (-50..150).
    "bodyslide.meaner": ("head.brow.projection", 1.5),
}

# Web slider prefix -> identity section the values are carried under.
# These have no canonical counterpart and are preserved, not mapped.
CARRIED_PREFIXES: dict[str, str] = {
    "morph.": "morphs",
    "sos.": "sos",
    "driver.": "drivers",
}

_CANONICAL_TO_WEB: dict[str, tuple[str, float]] = {
    canonical: (web, 1.0 / scale)
    for web, (canonical, scale) in SLIDER_MAP.items()
}


def canonical_to_web_slider(canonical_id: str) -> tuple[str, float] | None:
    """Inverse of :data:`SLIDER_MAP`: canonical id -> (web id, scale).

    Returns ``None`` when the canonical slider has no web counterpart
    (most Core sliders — e.g. every ``body.himbo.*`` preset slider —
    are carried in the web UI's ``coreSliders`` bag instead).
    """
    return _CANONICAL_TO_WEB.get(canonical_id)


def translate_record(record: dict) -> tuple[dict, list[str]]:
    """Translate a web-vocabulary character record to canonical Core form.

    Takes the record as the web UIs build it (web slider ids, web base
    ids) and returns ``(canonical_record, warnings)``. The input is
    never mutated. A record that is already canonical passes through
    unchanged (and un-warned).
    """
    warnings: list[str] = []
    out: dict[str, Any] = dict(record)
    sliders_in: dict = dict(record.get("sliders") or {})
    identity_in: dict = dict(record.get("identity") or {})

    # -- bases ------------------------------------------------------------
    base_in: dict = dict(record.get("base") or {})
    base_out: dict[str, str] = dict(base_in)
    web_body = base_in.get("body")
    if isinstance(web_body, str) and web_body in BASE_BODY_MAP:
        base_out["body"] = BASE_BODY_MAP[web_body]
        identity_in.setdefault("base_body", web_body)
    web_head = base_in.get("head")
    if isinstance(web_head, str) and web_head in HEAD_MAP:
        base_out["head"] = HEAD_MAP[web_head]
        identity_in.setdefault("base_head", web_head)
    out["base"] = base_out

    # -- sliders ----------------------------------------------------------
    sliders_out: dict[str, float] = {}
    carried: dict[str, dict[str, float]] = {}
    unmapped: dict[str, float] = {}
    for sid, value in sliders_in.items():
        if sid in SLIDER_MAP:
            canonical_id, scale = SLIDER_MAP[sid]
            sliders_out[canonical_id] = float(value) * scale
        elif sid.startswith(("morph.", "bodyslide.", "sos.", "driver.")):
            # Web-prefixed id the table does not map.
            placed = False
            for prefix, section in CARRIED_PREFIXES.items():
                if sid.startswith(prefix):
                    carried.setdefault(section, {})[sid[len(prefix):]] = value
                    placed = True
                    break
            if not placed:
                unmapped[sid] = value
                warnings.append(
                    f"slider {sid!r} has no canonical mapping; "
                    "preserved under identity.unmapped_sliders"
                )
        else:
            # Already canonical (body.* / head.* registry ids): pass through.
            sliders_out[sid] = value
    out["sliders"] = sliders_out

    # -- carried values live under identity (free-form, preserved) --------
    identity_out: dict = dict(identity_in)
    for section, values in carried.items():
        merged = dict(identity_out.get(section) or {})
        merged.update(values)
        identity_out[section] = merged
    if unmapped:
        merged_unmapped = dict(identity_out.get("unmapped_sliders") or {})
        merged_unmapped.update(unmapped)
        identity_out["unmapped_sliders"] = merged_unmapped
    out["identity"] = identity_out
    return out, warnings
