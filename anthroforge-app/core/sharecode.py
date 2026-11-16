"""Share codes — a character as one portable string.

Blueprint §3.2 + CREATOR_LESSONS rule 2 ("a character is a serialisable
vector; codes are nearly free — ship the share code with the creator").

Wire format::

    AF1-<base64url(frame)>
    frame = zlib(JSON) || CRC32(zlib(JSON)) as 4 big-endian bytes

- The payload is the character record *minus provenance* (§3.2),
  serialised as canonical JSON (sorted keys, compact separators), so
  encoding is deterministic and the round-trip is lossless — slider
  floats survive exactly (JSON repr round-trips IEEE-754 doubles).
- ``AF1-`` is the version prefix; a future format change is ``AF2-``
  and old codes keep decoding.
- The trailing CRC32 is the corruption gate: any flipped character in
  the code changes the decoded bytes and fails the checksum before a
  single byte is trusted (and zlib + JSON + schema validation stand
  behind it as further gates).
- Base64 padding is stripped on encode and restored on decode.
"""

from __future__ import annotations

import base64
import binascii
import json
import struct
import zlib

from .character import Character
from .errors import ShareCodeError

PREFIX = "AF1-"
_CRC = struct.Struct(">I")


def encode(character: Character) -> str:
    """Encode a character record to its ``AF1-…`` share code."""
    payload = character.to_dict(include_provenance=False)
    raw = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    comp = zlib.compress(raw, level=9)
    frame = comp + _CRC.pack(zlib.crc32(comp) & 0xFFFFFFFF)
    return PREFIX + base64.urlsafe_b64encode(frame).decode("ascii").rstrip("=")


def decode(code: str) -> Character:
    """Decode an ``AF1-…`` share code back to a :class:`Character`.

    Raises :class:`ShareCodeError` naming the failure: unsupported
    prefix, invalid base64, checksum mismatch, or corrupt payload.
    """
    if not isinstance(code, str):
        raise ShareCodeError("share code must be a string")
    code = code.strip()
    if not code.startswith(PREFIX):
        head = code.split("-", 1)[0]
        if head.startswith("AF") and head[2:].isdigit():
            raise ShareCodeError(
                f"unsupported share-code version {head!r}: this build decodes 'AF1-' codes"
            )
        raise ShareCodeError(f"share code must start with {PREFIX!r}")
    body = code[len(PREFIX):]
    if not body:
        raise ShareCodeError("share code has an empty payload")
    padded = body + "=" * (-len(body) % 4)
    try:
        frame = base64.b64decode(padded.encode("ascii"), altchars=b"-_", validate=True)
    except (binascii.Error, ValueError, UnicodeEncodeError) as exc:
        raise ShareCodeError(f"share code is not valid base64url: {exc}") from exc
    if len(frame) <= _CRC.size:
        raise ShareCodeError("share code payload is too short to contain a checksum")
    comp, crc_bytes = frame[:-_CRC.size], frame[-_CRC.size:]
    (expected_crc,) = _CRC.unpack(crc_bytes)
    actual_crc = zlib.crc32(comp) & 0xFFFFFFFF
    if actual_crc != expected_crc:
        raise ShareCodeError(
            f"share code checksum mismatch (expected {expected_crc:#010x}, "
            f"computed {actual_crc:#010x}): the code is corrupted"
        )
    try:
        raw = zlib.decompress(comp)
    except zlib.error as exc:
        raise ShareCodeError(f"share code payload does not decompress: {exc}") from exc
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ShareCodeError(f"share code payload is not valid JSON: {exc}") from exc
    # Structural validation (format/version/fields) happens in from_dict;
    # its SchemaError propagates as the named failure.
    return Character.from_dict(data)
