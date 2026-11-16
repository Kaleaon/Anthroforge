"""Share codes — a character as one portable string.

The decoder applies strict size limits before and during decompression.
Share codes are untrusted input, so a tiny compressed payload must not
be able to allocate unbounded memory.
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
MAX_CODE_CHARS = 1_000_000
MAX_DECOMPRESSED_BYTES = 4 * 1024 * 1024


def encode(character: Character) -> str:
    """Encode a character record to its AF1 share code."""
    payload = character.to_dict(include_provenance=False)
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    if len(raw) > MAX_DECOMPRESSED_BYTES:
        raise ShareCodeError(
            f"character record is too large to share ({len(raw)} bytes; limit {MAX_DECOMPRESSED_BYTES})"
        )
    comp = zlib.compress(raw, level=9)
    frame = comp + _CRC.pack(zlib.crc32(comp) & 0xFFFFFFFF)
    code = PREFIX + base64.urlsafe_b64encode(frame).decode("ascii").rstrip("=")
    if len(code) > MAX_CODE_CHARS:
        raise ShareCodeError(f"encoded share code is too large ({len(code)} characters; limit {MAX_CODE_CHARS})")
    return code


def decode(code: str) -> Character:
    """Decode an AF1 share code with bounded resource usage."""
    if not isinstance(code, str):
        raise ShareCodeError("share code must be a string")
    code = code.strip()
    if len(code) > MAX_CODE_CHARS:
        raise ShareCodeError(f"share code exceeds the {MAX_CODE_CHARS}-character size limit")
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
            f"share code checksum mismatch (expected {expected_crc:#010x}, computed {actual_crc:#010x}): the code is corrupted"
        )
    try:
        inflater = zlib.decompressobj()
        raw = inflater.decompress(comp, MAX_DECOMPRESSED_BYTES + 1)
        if len(raw) > MAX_DECOMPRESSED_BYTES or inflater.unconsumed_tail:
            raise ShareCodeError(
                f"share code expands beyond the {MAX_DECOMPRESSED_BYTES}-byte limit"
            )
        if not inflater.eof:
            raise ShareCodeError("share code contains an incomplete compressed stream")
        if inflater.unused_data:
            raise ShareCodeError("share code contains trailing compressed data")
    except zlib.error as exc:
        raise ShareCodeError(f"share code payload does not decompress: {exc}") from exc
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ShareCodeError(f"share code payload is not valid JSON: {exc}") from exc
    return Character.from_dict(data)
