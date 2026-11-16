"""Named error types for the AnthroForge Core Service.

Every failure the Core raises is one of these, and every message names
the field / file / slider id that caused it — silent or anonymous
failures are a blueprint violation (APP_BLUEPRINT §4.6 error model,
applied here to the library layer already).
"""


class AnthroForgeError(Exception):
    """Base class for all Core Service errors."""


class SchemaError(AnthroForgeError):
    """A character record (or other schema'd document) is malformed.

    The message always names the offending field.
    """


class ValidationError(AnthroForgeError):
    """A ValidationReport with errors was promoted to an exception.

    Carries the full report on ``.report`` so callers can inspect every
    error and warning, not just the first.
    """

    def __init__(self, report):
        self.report = report
        summary = "; ".join(report.errors) if report.errors else "validation failed"
        super().__init__(summary)


class UnknownSliderError(AnthroForgeError):
    """A slider id was looked up that the registry does not hold."""


class SliderRecordError(AnthroForgeError):
    """A canonical slider record file is malformed or inconsistent.

    The message always names the source file.
    """


class CouplingRecordError(AnthroForgeError):
    """A coupling record file (library/couplings/) is malformed or
    inconsistent. The message always names the source file."""


class BaseRecordError(AnthroForgeError):
    """A base record / geometry package (library/bases/) is malformed,
    missing, or inconsistent. The message always names the base id or
    source file."""


class GeometryError(AnthroForgeError):
    """A geometry operation failed: an unreadable .target instance, a
    base/instance vertex-count mismatch, or a failed build gate. The
    message always names the slider / instance / file involved."""


class FurDataError(AnthroForgeError):
    """A fur data file (library/fur/) is malformed or fails validation.
    The message always names the file and field."""


class ShareCodeError(AnthroForgeError):
    """A share code cannot be decoded: bad prefix, bad checksum, or a
    corrupt payload. The message says which."""
