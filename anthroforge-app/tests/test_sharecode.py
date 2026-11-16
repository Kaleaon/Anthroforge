"""Share codes: lossless round-trip + corruption detection."""

import pytest

from core.character import Character
from core.errors import ShareCodeError
from core.sharecode import decode, encode


def sample_character() -> Character:
    return Character(
        name="Code Orc",
        sliders={
            "body.belly.protrusion": 0.62,
            "body.chubby": 0.30000000000000004,   # not a tidy double
            "head.brow.projection": 135.0,
            "head.muzzle.length": -0.35,
            "body.weight": 1e-09,
        },
        parts=[{"slot": "ear.L", "part": "ear_point_v1", "variant": None,
                "transform": {"offset": [0, 0, 0], "rotate_deg": [0, 0, 0],
                              "scale": 1.0}}],
        materials={"skin": {"palette": "orc.classic_green", "base": "#6B8E3D"}},
        provenance={"created_by": "pytest", "secret_note": "must not travel"},
        id="chr_00000000000000000000000002",
    )


def test_round_trip_is_lossless_for_sliders():
    char = sample_character()
    code = encode(char)
    assert code.startswith("AF1-")
    back = decode(code)
    # Exact float equality: the vector must survive bit-for-bit.
    assert back.sliders == char.sliders
    assert back.to_dict(include_provenance=False) == \
        char.to_dict(include_provenance=False)


def test_provenance_is_stripped_by_the_code():
    back = decode(encode(sample_character()))
    assert back.provenance == {}


def test_encoding_is_deterministic():
    char = sample_character()
    assert encode(char) == encode(char)


def test_flipped_character_fails_checksum():
    code = encode(sample_character())
    mid = len(code) // 2
    replacement = "A" if code[mid] != "A" else "B"
    corrupted = code[:mid] + replacement + code[mid + 1:]
    assert corrupted != code
    with pytest.raises(ShareCodeError, match="checksum"):
        decode(corrupted)


def test_wrong_prefix_rejected():
    with pytest.raises(ShareCodeError, match="AF1-"):
        decode("XXXX-abcdef")


def test_future_version_prefix_rejected_by_name():
    with pytest.raises(ShareCodeError, match="AF2"):
        decode("AF2-abcdef")


def test_garbage_payload_rejected():
    with pytest.raises(ShareCodeError):
        decode("AF1-!!!not-base64!!!")
