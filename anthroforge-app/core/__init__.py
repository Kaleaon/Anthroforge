"""AnthroForge Core Service (Python) — the single implementation of
everything that isn't pixels (APP_BLUEPRINT §2.3).

This package is the Phase-1 skeleton: character records, share codes,
and the canonical slider registry. The slider engine, job queue, and
library index join it here as later phases land.
"""

from .anatomy import AnatomyLibrary, AnatomyValidation, validate_character_anatomy, validate_part_manifest
from .character import Character, ValidationReport, new_character_id
from .errors import (
    AnthroForgeError,
    SchemaError,
    ShareCodeError,
    SliderRecordError,
    UnknownSliderError,
    ValidationError,
)
from .sharecode import decode as decode_share_code
from .sharecode import encode as encode_share_code
from .sliders import ClampWarning, SliderRecord, SliderRegistry

__all__ = [
    "AnatomyLibrary",
    "AnatomyValidation",
    "AnthroForgeError",
    "Character",
    "ClampWarning",
    "SchemaError",
    "ShareCodeError",
    "SliderRecord",
    "SliderRecordError",
    "SliderRegistry",
    "UnknownSliderError",
    "ValidationError",
    "ValidationReport",
    "decode_share_code",
    "encode_share_code",
    "new_character_id",
    "validate_character_anatomy",
    "validate_part_manifest",
]

__version__ = "0.1.0"
